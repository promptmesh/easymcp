from asyncio import Queue, Task
from typing import Awaitable

from easymcp.client.iobuffers import reader, writer
from easymcp.client.transports.generic import GenericTransport


class ClientSession:
    """ClientSession class"""

    incoming_messages: Queue
    outgoing_messages: Queue

    reader_task: Task[None]
    writer_task: Task[None]

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

    async def register_roots_callback(self, callback: Awaitable):
        """register a callback for roots"""
        self.roots_callback = callback

    async def register_sampling_callback(self, callback: Awaitable):
        """register a callback for sampling"""
        self.sampling_callback = callback

    async def start(self):
        """start the client session"""
        await self.transport.start()
        self.reader_task = await reader(self.transport, self.incoming_messages)
        self.writer_task = await writer(self.transport, self.outgoing_messages)

    async def stop(self):
        """stop the client session"""
        await self.transport.stop()

    async def list_tools(self):
        """list available tools"""
        raise NotImplementedError

    async def call_tool(self, tool_name: str, args: dict):
        """call a tool"""
        raise NotImplementedError
    
    async def list_resources(self):
        """list available resources"""
        raise NotImplementedError
    
    async def read_resource(self, resource_name: str):
        """read a resource"""
        raise NotImplementedError