from asyncio import Queue, Task, create_task
import asyncio
from inspect import iscoroutinefunction
import json
from typing import Awaitable, Callable

from loguru import logger

from easymcp.client.iobuffers import reader, writer
from easymcp.client.requestmap import RequestMap
from easymcp.client.transports.generic import TransportProtocol

from easymcp.client.utils import CreateJsonRPCRequest
from mcp import types

from easymcp.client.sessions.GenericSession import BaseSessionProtocol

class MCPClientSession(BaseSessionProtocol):
    """ClientSession class"""

    incoming_messages: Queue[types.JSONRPCMessage]
    outgoing_messages: Queue[types.JSONRPCMessage]

    reader_task: Task[None]
    writer_task: Task[None]

    _start_reading_messages_task: Task[None]

    request_map: RequestMap

    roots_callback: Callable[[types.ListRootsRequest], Awaitable[types.ListRootsResult]] | None = None
    sampling_callback: Callable[[types.CreateMessageRequest], Awaitable[types.CreateMessageResult]] | None = None

    tools_changed_callback: Callable[[], Awaitable[None]] | None = None
    prompts_changed_callback: Callable[[], Awaitable[None]] | None = None
    resources_changed_callback: Callable[[], Awaitable[None]] | None = None

    _tools: types.ListToolsResult | None = None
    _prompts: types.ListPromptsResult | None = None
    _resources: types.ListResourcesResult | None = None

    def __init__(self, transport: TransportProtocol):
        self.transport = transport

        # define message queues
        self.incoming_messages = Queue()
        self.outgoing_messages = Queue()

        self._tools = None

    async def init(self):
        """initialize the client session"""
        await self.transport.init()
        self.request_map = RequestMap(self.outgoing_messages)

    @staticmethod
    def _validate_async_callback(callback: Callable, name: str):
        assert callable(callback), f"{name} must be callable"
        assert iscoroutinefunction(callback), f"{name} must be an async function"

    async def register_roots_callback(self, callback: Callable[[types.ListRootsRequest], Awaitable[types.ListRootsResult]]):
        """register a callback for roots"""
        self._validate_async_callback(callback, "roots_callback")
        self.roots_callback = callback

    async def register_sampling_callback(self, callback: Callable[[types.CreateMessageRequest], Awaitable[types.CreateMessageResult]]):
        """register a callback for sampling"""
        self._validate_async_callback(callback, "sampling_callback")
        self.sampling_callback = callback

    async def register_tools_changed_callback(self, callback: Callable[[], Awaitable[None]]):
        """register a callback for tools changed"""
        self._validate_async_callback(callback, "tools_changed_callback")
        self.tools_changed_callback = callback

    async def register_prompts_changed_callback(self, callback: Callable[[], Awaitable[None]]):
        """register a callback for prompts changed"""
        self._validate_async_callback(callback, "prompts_changed_callback")
        self.prompts_changed_callback = callback

    async def register_resources_changed_callback(self, callback: Callable[[], Awaitable[None]]):
        """register a callback for resources changed"""
        self._validate_async_callback(callback, "resources_changed_callback")
        self.resources_changed_callback = callback

    def _start_reading_messages(self):
        async def __start_reading_messages():
            while self.transport.state == "started":
                message = await self.incoming_messages.get()
                if message is None:
                    continue

                # handle responses
                if isinstance(message.root, types.JSONRPCResponse):
                    self.request_map.resolve_request(message.root)

                # handle notifications
                elif isinstance(message.root, types.JSONRPCNotification):
                    if message.root.params is None:
                        logger.error(f"Received notification with no params: {message}")
                        continue

                    notification = types.ServerNotification.model_validate(message.root)

                    await self.handle_notification(notification)

                # handle requests
                elif isinstance(message.root, types.JSONRPCRequest):
                    if message.root.params is None:
                        logger.error(f"Received request with no params: {message}")
                        continue

                    request = types.ServerRequest.model_validate(message.root)

                    response = await self.handle_request(request)
                    if response is not None:
                        response_message = types.JSONRPCResponse(
                            jsonrpc="2.0",
                            id=message.root.id,
                            result=response,
                        )
                        await self.transport.send(response_message.model_dump_json())

                # handle errors
                elif isinstance(message.root, types.JSONRPCError):
                    data = message.model_dump()
                    try:
                        data["error"]["message"] = json.loads(
                            data.get("error").get("message", "{}")
                        )
                        data = json.dumps(data, indent=4)
                        logger.error(f"Received error:\n{data}")
                    except Exception:
                        pass

                    if message.root.id is not None:
                        self.request_map.resolve_error(message.root)

                else:
                    logger.error(f"Unknown message type: {message.root}")

        self._start_reading_messages_task = create_task(__start_reading_messages())

    async def start(self) -> types.InitializeResult:
        """start the client session"""
        await self.transport.start()
        self.reader_task = await reader(self.transport, self.incoming_messages)
        self.writer_task = await writer(self.transport, self.outgoing_messages)

        self._start_reading_messages()

        sampling = types.SamplingCapability()
        roots = types.RootsCapability(listChanged=True)

        # send initialize request
        request = types.ClientRequest(
            types.InitializeRequest(
                method="initialize",
                params=types.InitializeRequestParams(
                    protocolVersion=types.LATEST_PROTOCOL_VERSION,
                    capabilities=types.ClientCapabilities(
                        sampling=sampling,
                        experimental={},
                        roots=roots,
                    ),
                    clientInfo=types.Implementation(name="easymcp", version="0.1.0"),
                ),
            )
        )

        response = await self.request_map.send_request(CreateJsonRPCRequest(request))  # type: ignore
        if response is None:
            raise RuntimeError("Failed to initialize client session")

        # send initialized notification
        notification = types.ClientNotification(
            types.InitializedNotification(method="notifications/initialized")
        )

        self.outgoing_messages.put_nowait(
            types.JSONRPCNotification(
                jsonrpc="2.0",
                **notification.model_dump(
                    by_alias=True, mode="json", exclude_none=True
                ),
            )  # type: ignore
        )

        result = types.InitializeResult.model_validate(response.result)
        return result

    async def stop(self):
        """stop the client session"""
        self.reader_task.cancel()
        self.writer_task.cancel()
        try:
            await self.reader_task
        except asyncio.CancelledError:
            pass

        try:
            self.writer_task
        except asyncio.CancelledError:
            pass

        self._start_reading_messages_task.cancel()
        try:
            await self._start_reading_messages_task
        except asyncio.CancelledError:
            pass

        await self.transport.stop()
        await asyncio.sleep(0)

    async def list_tools(self, force: bool = False):
        """list available tools"""

        if not force and self._tools is not None:
            return self._tools.model_copy(deep=True)

        request = types.ClientRequest(
            types.ListToolsRequest(
                method="tools/list",
            )
        )

        response = await self.request_map.send_request(CreateJsonRPCRequest(request))

        if response is None:
            result = types.ListToolsResult(tools=[])
        else:
            result = types.ListToolsResult.model_validate(response.result)

        self._tools = result.model_copy(deep=True)

        return result

    async def call_tool(self, tool_name: str, args: dict):
        """call a tool"""
        request = types.ClientRequest(
            types.CallToolRequest(
                method="tools/call",
                params=types.CallToolRequestParams(
                    name=tool_name,
                    arguments=args,
                ),
            )
        )

        response = await self.request_map.send_request(CreateJsonRPCRequest(request))
        
        if response is None:
            raise RuntimeError("Failed to call tool")

        result = types.CallToolResult.model_validate(response.result)

        return result

    async def list_resources(self, force: bool = False):
        """list available resources"""

        if not force and self._resources is not None:
            return self._resources.model_copy(deep=True)

        request = types.ClientRequest(
            types.ListResourcesRequest(
                method="resources/list",
            )
        )

        response = await self.request_map.send_request(CreateJsonRPCRequest(request))

        if response is None:
            result = types.ListResourcesResult(resources=[])
        else:
            result = types.ListResourcesResult.model_validate(response.result)

        self._resources = result.model_copy(deep=True)

        return result

    async def read_resource(self, resource_name: str):
        """read a resource"""

        request = types.ClientRequest(
            types.ReadResourceRequest(
                method="resources/read",
                params=types.ReadResourceRequestParams(
                    # TODO: validate uri
                    uri=resource_name,  # type: ignore
                ),
            )
        )

        response = await self.request_map.send_request(CreateJsonRPCRequest(request))
        
        if response is None:
            raise RuntimeError("Failed to read resource")
        
        result = types.ReadResourceResult.model_validate(response.result)

        return result

    async def list_prompts(self, force: bool = False):
        """list available prompts"""

        if not force and self._prompts is not None:
            return self._prompts.model_copy(deep=True)

        request = types.ClientRequest(
            types.ListPromptsRequest(
                method="prompts/list",
            )
        )

        response = await self.request_map.send_request(CreateJsonRPCRequest(request))

        if response is None:
            result = types.ListPromptsResult(prompts=[])
        else:
            result = types.ListPromptsResult.model_validate(response.result)

        self._prompts = result.model_copy(deep=True)

        return result
    
    async def read_prompt(self, prompt_name: str, args: dict):
        """read a prompt"""

        request = types.ClientRequest(
            types.GetPromptRequest(
                method="prompts/get",
                params=types.GetPromptRequestParams(
                    name=prompt_name,
                    arguments=args,
                ),
            )
        )

        response = await self.request_map.send_request(CreateJsonRPCRequest(request))
        result = types.GetPromptResult.model_validate(response.result)

        return result
    
    async def handle_notification(self, notification: types.ServerNotification):
        """handle a notification"""

        logger.debug(f"Handling notification: {notification}")

        if isinstance(notification.root, types.ToolListChangedNotification):
            self._tools = None
            logger.debug("cleared tools cache")
            if self.tools_changed_callback is not None:
                await self.tools_changed_callback()

        elif isinstance(notification.root, types.PromptListChangedNotification):
            self._prompts = None
            logger.debug("cleared prompts cache")
            if self.prompts_changed_callback is not None:
                await self.prompts_changed_callback()

        elif isinstance(notification.root, types.ResourceListChangedNotification):
            self._resources = None
            logger.debug("cleared resources cache")
            if self.resources_changed_callback is not None:
                await self.resources_changed_callback()

    async def handle_request(self, request: types.ServerRequest):
        """handle a request"""
        
        logger.debug(f"Handling request: {request}")

        # handle ping
        if isinstance(request.root, types.PingRequest):
            return {}

        # handle sampling
        elif isinstance(request.root, types.CreateMessageRequest):
            if self.sampling_callback is None:
                logger.error("Sampling callback not set but received sampling request")
                return
            
            sampling_result = await self.sampling_callback(request.root)

            assert isinstance(sampling_result, types.CreateMessageResult), "Sampling callback must return a CreateMessageResult"
            
            return sampling_result.model_dump()

        # handle list roots
        elif isinstance(request.root, types.ListRootsRequest):
            if self.roots_callback is None:
                logger.error("Roots callback not set but received roots request")
                return

            roots_result = await self.roots_callback(request.root)

            assert isinstance(roots_result, types.ListRootsResult), "Roots callback must return a ListRootsResult"

            return roots_result.model_dump()

        # throw error for unknown request
        else:
            logger.error(f"Unknown request type: {request.root}")
            return
