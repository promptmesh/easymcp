from typing import TypeAlias

from easymcp.client.sessions.GenericSession import BaseSessionProtocol
from easymcp.client.sessions.mcp import MCPClientSession
from easymcp.client.transports.stdio import StdioTransport, StdioServerParameters


transportTypes: TypeAlias = StdioServerParameters

def make_transport(arguments: transportTypes) -> BaseSessionProtocol:

    if isinstance(arguments, StdioServerParameters):
        return MCPClientSession(StdioTransport(arguments))
    
    raise ValueError(f"Unknown transport type: {type(arguments)}")


