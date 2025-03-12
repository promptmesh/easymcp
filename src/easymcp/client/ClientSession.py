from asyncio import Queue, Task

from easymcp.client.iobuffers import reader, writer
from easymcp.client.transports.generic import GenericTransport


class ClientSession:
    """ClientSession class"""

    incoming_messages: Queue
    outgoing_messages: Queue

    reader_task: Task[None]
    writer_task: Task[None]

    def __init__(self, transport: GenericTransport):
        self.transport = transport

        # define message queues
        self.incoming_messages = Queue()
        self.outgoing_messages = Queue()

    async def init(self):
        """initialize the client session"""
        await self.transport.init()

    async def start(self):
        """start the client session"""
        await self.transport.start()
        reader_task = await reader(self.transport, self.incoming_messages)
        writer_task = await writer(self.transport, self.outgoing_messages)

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