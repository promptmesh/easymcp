from asyncio import Queue, Task
from easymcp.client.transports.generic import GenericTransport

async def reader(transport: GenericTransport, queue: Queue):
    """Read data from the transport and put it in the queue"""

    async def _reader():
        while transport.state == "started":
            data = await transport.receive()
            queue.put_nowait(data)

    task = Task(_reader())
    return task

async def writer(transport: GenericTransport, queue: Queue):
    """Write data from the queue to the transport"""

    async def _writer():
        while transport.state == "started":
            data = await queue.get()
            await transport.send(data)

    task = Task(_writer())
    return task

