from asyncio import Queue, Task
import json
from typing import Awaitable

from loguru import logger

from easymcp.client.iobuffers import reader, writer
from easymcp.client.requestmap import RequestMap
from easymcp.client.transports.generic import GenericTransport

from easymcp.client.utils import CreateJsonRPCRequest
from easymcp.vendored import types


class ClientSession:
    """ClientSession class"""

    incoming_messages: Queue[types.JSONRPCMessage]
    outgoing_messages: Queue[types.JSONRPCMessage]

    reader_task: Task[None]
    writer_task: Task[None]

    request_map: RequestMap

    roots_callback: Awaitable | None = None
    sampling_callback: Awaitable | None = None

    _tools: types.ListToolsResult | None = None
    _prompts: types.ListPromptsResult | None = None
    _resources: types.ListResourcesResult | None = None

    def __init__(self, transport: GenericTransport):
        self.transport = transport

        # define message queues
        self.incoming_messages = Queue()
        self.outgoing_messages = Queue()

        self._tools = None

    async def init(self):
        """initialize the client session"""
        await self.transport.init()
        self.request_map = RequestMap(self.outgoing_messages)

    async def register_roots_callback(self, callback: Awaitable):
        """register a callback for roots"""
        self.roots_callback = callback

    async def register_sampling_callback(self, callback: Awaitable):
        """register a callback for sampling"""
        self.sampling_callback = callback

    def start_reading_messages(self):
        async def _start_reading_messages():
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

                    await self.handle_request(request)

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

        Task(_start_reading_messages())

    async def start(self) -> types.InitializeResult:
        """start the client session"""
        await self.transport.start()
        self.reader_task = await reader(self.transport, self.incoming_messages)
        self.writer_task = await writer(self.transport, self.outgoing_messages)

        self.start_reading_messages()

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
                        experimental=None,
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
        await self.transport.stop()

    async def list_tools(self, force: bool = False):
        """list available tools"""

        if not force and self._tools is not None:
            return self._tools

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

        self._tools = result

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
            return self._resources

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

        self._resources = result

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
            return self._prompts

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

        self._prompts = result

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

        elif isinstance(notification.root, types.PromptListChangedNotification):
            self._prompts = None
            logger.debug("cleared prompts cache")

        elif isinstance(notification.root, types.ResourceListChangedNotification):
            self._resources = None
            logger.debug("cleared resources cache")

    async def handle_request(self, request: types.ServerRequest):
        """handle a request"""
        
        logger.debug(f"Handling request: {request}")