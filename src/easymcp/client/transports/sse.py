import httpx
from pydantic import BaseModel
from easymcp.client.transports.generic import TransportProtocol


class SseServerParameters(BaseModel):
    """SseServerParameters class"""

    url: str
    """url to connect to"""

    headers: dict[str, str] = {}
    """headers to send"""


class SseTransport(TransportProtocol):
    """SseTransport class"""

    args: SseServerParameters
    client: httpx.AsyncClient
    connection = None

    def __init__(self, arguments: SseServerParameters):
        self.state = "constructed"
        self.args = arguments.model_copy(deep=True)

    async def init(self):
        """Perform init logic"""
        self.state = "initialized"

        raise NotImplementedError

    async def start(self):
        """Start the transport"""
        self.state = "started"

        raise NotImplementedError

    async def send(self, message: str):
        """Send data to the transport"""
        raise NotImplementedError

    async def receive(self) -> str:
        """Receive data from the transport"""
        raise NotImplementedError

    async def stop(self):
        """Stop the transport"""
        self.state = "stopped"
