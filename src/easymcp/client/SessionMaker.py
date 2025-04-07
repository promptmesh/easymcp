from typing import TypeAlias

from easymcp.client.sessions.GenericSession import BaseSessionProtocol
from easymcp.client.sessions.fastmcp.main import FastMCPSession
from easymcp.client.sessions.fastmcp.paramaters import FastMCPParamaters
from easymcp.client.sessions.mcp import MCPClientSession
from easymcp.client.transports.stdio import StdioTransport, StdioServerParameters
from easymcp.client.transports.docker import DockerTransport, DockerServerParameters
from easymcp.client.transports.sse import SseTransport, SseServerParameters


transportTypes: TypeAlias = StdioServerParameters | DockerServerParameters | SseServerParameters

make_transport_input: TypeAlias = transportTypes | FastMCPParamaters

def make_transport(arguments: make_transport_input) -> BaseSessionProtocol:

    if isinstance(arguments, StdioServerParameters):
        return MCPClientSession(StdioTransport(arguments))

    if isinstance(arguments, DockerServerParameters):
        return MCPClientSession(DockerTransport(arguments))
    
    if isinstance(arguments, SseServerParameters):
        return MCPClientSession(SseTransport(arguments))
    
    if isinstance(arguments, FastMCPParamaters):
        return FastMCPSession(arguments)
    
    raise ValueError(f"Unknown transport type: {type(arguments)}")
