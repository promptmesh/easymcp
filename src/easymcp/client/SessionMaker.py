from typing import TypeAlias

from easymcp.client.ClientSession import ClientSession
from easymcp.client.transports.stdio import StdioTransport, StdioServerParameters
from easymcp.client.transports.sse import SseTransport, SseServerParameters


transportTypes: TypeAlias = StdioServerParameters | SseServerParameters

def make_transport(arguments: transportTypes) -> ClientSession:

    if isinstance(arguments, StdioServerParameters):
        return ClientSession(StdioTransport(arguments))
    
    if isinstance(arguments, SseServerParameters):
        return ClientSession(SseTransport(arguments))
    
    raise ValueError(f"Unknown transport type: {type(arguments)}")


