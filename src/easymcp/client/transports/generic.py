from typing import Protocol, runtime_checkable, Literal
from pydantic import BaseModel


@runtime_checkable
class TransportProtocol(Protocol):
    """Generic transport interface"""

    state: Literal["constructed", "initialized", "started", "stopped"]

    def __init__(self, arguments: BaseModel) -> None: ...

    async def init(self) -> None:
        """perform init logic (e.g. pull docker containers, download code, etc.)"""
        ...

    async def start(self) -> None:
        """start the transport (e.g. spawn subprocesses, start docker containers, etc.)"""
        ...

    async def stop(self) -> None:
        """stop the transport"""
        ...

    async def send(self, message: str) -> None:
        """send data to the transport"""
        ...

    async def receive(self) -> str:
        """receive data from the transport"""
        ...
