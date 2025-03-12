from abc import ABC, abstractmethod
from typing import Any, Literal
from pydantic import BaseModel

class GenericTransport(ABC):
    """Generic abstract class for transports"""

    state: Literal["constructed", "initialized", "started", "stopped"]


    def __init__(self, arguments: BaseModel):
        self.state = "constructed"

    @abstractmethod
    async def init(self):
        """perform init logic (e.g. pull docker containers, download code, etc.)"""
        self.state = "initialized"

    @abstractmethod
    async def start(self):
        """start the transport (e.g. spawn subprocesses, start docker containers, etc.)"""
        self.state = "started"

    @abstractmethod
    async def stop(self):
        """stop the transport"""
        self.state = "stopped"
    
    @abstractmethod
    async def send(self, message: Any):
        """send data to the transport"""
        raise NotImplementedError
    
    @abstractmethod
    async def receive(self):
        """receive data from the transport"""
        raise NotImplementedError