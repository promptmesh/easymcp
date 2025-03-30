from asyncio import Queue, Task

from loguru import logger
import pydantic
from easymcp.client.transports.generic import TransportProtocol
from mcp import types


async def reader(transport: TransportProtocol, queue: Queue[types.JSONRPCMessage]):
    """Read data from the transport and put it in the queue"""

    async def _reader():
        while transport.state == "started":
            data = await transport.receive()

            try:
                parsed = types.JSONRPCMessage.model_validate_json(data)
            except pydantic.ValidationError:
                logger.error(f"Error parsing JSON: {data}")
                parsed = None

            if parsed is None:
                continue

            queue.put_nowait(parsed)

    task = Task(_reader())
    return task


async def writer(transport: TransportProtocol, queue: Queue[types.JSONRPCMessage]):
    """Write data from the queue to the transport"""

    async def _writer():
        while transport.state == "started":
            data = await queue.get()
            await transport.send(data.model_dump_json())

    task = Task(_writer())
    return task
