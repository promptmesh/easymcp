from pydantic import BaseModel
from easymcp.client.transports.generic import TransportProtocol
from mcp.client.sse import sse_client
from mcp import types

class SseServerParameters(BaseModel):
    """SseServerParameters class"""

    url: str
    """url to connect to"""

    headers: dict[str, str] = {}
    """headers to send"""

    timeout: int = 60
    """timeout in seconds"""


class SseTransport(TransportProtocol):
    """SseTransport class"""

    args: SseServerParameters
    connection = None

    readstream = None
    writestream = None

    def __init__(self, arguments: SseServerParameters):
        self.state = "constructed"
        self.args = arguments.model_copy(deep=True)

    async def init(self):
        """Perform init logic"""
        self.state = "initialized"
        self.client = sse_client(self.args.url, headers=self.args.headers, timeout=self.args.timeout)

    async def start(self):
        """Start the transport"""
        self.state = "started"

        self.readstream, self.writestream = await self.client.__aenter__()


    async def send(self, message: str):
        """Send data to the transport"""
        assert self.writestream, "Transport not started"

        msg = types.JSONRPCMessage.model_validate_json(message)
        await self.writestream.send(msg)

    async def receive(self) -> str:
        """Receive data from the transport"""
        assert self.readstream, "Transport not started"

        msg = await self.readstream.receive()
        
        if isinstance(msg, Exception):
            await self.stop()
            raise msg
        
        return msg.model_dump_json()

    async def stop(self):
        """Stop the transport"""
        self.state = "stopped"
