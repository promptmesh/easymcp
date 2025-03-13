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

    def __init__(self, transport: GenericTransport):
        self.transport = transport

        # define message queues
        self.incoming_messages = Queue()
        self.outgoing_messages = Queue()

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

                if isinstance(message.root, types.JSONRPCResponse):
                    self.request_map.resolve_request(message.root)

                elif isinstance(message.root, types.JSONRPCNotification):
                    pass

                elif isinstance(message.root, types.JSONRPCRequest):
                    pass

                elif isinstance(message.root, types.JSONRPCError):
                    data = message.model_dump()
                    data["error"]["message"] = json.loads(data.get("error").get("message", "{}"))
                    data = json.dumps(data, indent=4)
                    logger.error(f"Received error:\n{data}")

                else:
                    logger.error(f"Unknown message type: {message.root}")

        Task(_start_reading_messages())

    async def start(self) -> types.InitializeResult:
        """start the client session"""
        await self.transport.start()
        self.reader_task = await reader(self.transport, self.incoming_messages)
        self.writer_task = await writer(self.transport, self.outgoing_messages)

        self.start_reading_messages()

        sampling = (
            types.SamplingCapability() if self.sampling_callback is not None else {}
        )
        roots = (
            types.RootsCapability(listChanged=True)
            if self.roots_callback is not None
            else {}
        )

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

        # send initialized notification
        notification = types.ClientNotification(
            types.InitializedNotification(method="notifications/initialized")
        )

        self.outgoing_messages.put_nowait(
            types.JSONRPCNotification(
                jsonrpc="2.0",
                **notification.model_dump(by_alias=True, mode="json", exclude_none=True),
            )
        )  # type: ignore

        return response

    async def stop(self):
        """stop the client session"""
        await self.transport.stop()

    async def list_tools(self):
        """list available tools"""
        request = types.ClientRequest(
            types.ListToolsRequest(
                method="tools/list",
            )
        )

        response = self.request_map.send_request(CreateJsonRPCRequest(request))

        return await response

    async def call_tool(self, tool_name: str, args: dict):
        """call a tool"""
        raise NotImplementedError

    async def list_resources(self):
        """list available resources"""

        request = types.ClientRequest(
            types.ListResourcesRequest(
                method="resources/list",
            )
        )

        response = self.request_map.send_request(CreateJsonRPCRequest(request))

        return await response

    async def read_resource(self, resource_name: str):
        """read a resource"""
        raise NotImplementedError
