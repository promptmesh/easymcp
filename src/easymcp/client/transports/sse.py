import httpx
from easymcp.client.transports.generic import GenericTransport
from pydantic import BaseModel


class SseServerParameters(BaseModel):
    """SseServerParameters class"""

    url: str
    """url to connect to"""

    headers: dict[str, str] = {}
    """headers to send"""


class SseTransport(GenericTransport):
    """SseTransport class"""

    args: SseServerParameters
    client: httpx.AsyncClient
    connection = None

    def __init__(self, arguments: SseServerParameters):
        super().__init__(arguments)
        self.state = "constructed"
        self.args = arguments.model_copy(deep=True)

    async def init(self):
        """Perform init logic"""
        self.state = "initialized"

        self.client = httpx.AsyncClient(
            base_url=self.args.url,
            headers=self.args.headers,
        )

    async def start(self):
        """Start the transport"""
        self.state = "started"

        self.connection = self.client.get()

    async def send(self, message: str):
        """Send data to the transport"""
        raise NotImplementedError

    async def receive(self) -> str:
        """Receive data from the transport"""
        raise NotImplementedError

    async def stop(self):
        """Stop the transport"""
        self.state = "stopped"
