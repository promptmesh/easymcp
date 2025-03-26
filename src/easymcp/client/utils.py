from uuid import uuid4
from re import sub

from mcp.types import ClientRequest, JSONRPCRequest


def CreateJsonRPCRequest(request: ClientRequest) -> JSONRPCRequest:
    """Create a JSON RPC request"""
    return JSONRPCRequest(jsonrpc="2.0", id=str(uuid4()), **request.model_dump())

def format_server_name(server_name: str) -> str:
    """Format a server name to be namespacing friendly"""

    server_name = server_name.replace("_", "-")
    server_name = server_name.replace(".", "-")

    return sub(r'[^a-zA-Z0-9-]', '', server_name)