import asyncio

import httpx
import pytest
from mcp import InitializeResult, ListResourcesResult, ListToolsResult

from easymcp.client.sessions.mcp import MCPClientSession
from easymcp.client.transports.sse import SseServerParameters, SseTransport

available = False
try:
    available = httpx.get("http://localhost:8000/sse").status_code == 200
except Exception:
    pass


@pytest.mark.skipif(not available, reason="sse server not available")
@pytest.mark.asyncio()
async def test_sse_client_session():
    args = SseServerParameters(url="http://localhost:8000/sse")
    transport = SseTransport(args)

    client_session = MCPClientSession(transport)
    await client_session.init()

    result = await client_session.start()
    assert isinstance(result, InitializeResult)

    resources = await client_session.list_resources()
    assert isinstance(resources, ListResourcesResult)

    tools = await client_session.list_tools()
    assert isinstance(tools, ListToolsResult)

    await client_session.stop()
    await asyncio.sleep(0)
