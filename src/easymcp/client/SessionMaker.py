from typing import TypeAlias

from easymcp.client.ClientSession import ClientSession
from easymcp.client.transports.stdio import StdioTransport, StdioServerParameters


transportTypes: TypeAlias = StdioServerParameters

def make_transport(arguments: transportTypes) -> ClientSession:

    if isinstance(arguments, StdioServerParameters):
        return ClientSession(StdioTransport(arguments))
    
    raise ValueError(f"Unknown transport type: {type(arguments)}")


