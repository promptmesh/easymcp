from uuid import uuid4

from easymcp.vendored.types import ClientRequest, JSONRPCRequest


def CreateJsonRPCRequest(request: ClientRequest) -> JSONRPCRequest:
    """Create a JSON RPC request"""
    return JSONRPCRequest(jsonrpc="2.0", id=str(uuid4()), **request.model_dump())
