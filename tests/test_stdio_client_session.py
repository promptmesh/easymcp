import asyncio
from mcp import ReadResourceResult
from mcp.types import CallToolResult, InitializeResult, ListResourcesResult, ListToolsResult
import pytest
from easymcp.client.sessions.mcp import MCPClientSession
from easymcp.client.transports.stdio import StdioTransport, StdioServerParameters

@pytest.mark.asyncio()
async def test_stdio_client_session():
    args = StdioServerParameters(command="uvx", args=["mcp-timeserver"])
    transport = StdioTransport(args)

    client_session = MCPClientSession(transport)
    await client_session.init()

    result = await client_session.start()
    assert isinstance(result, InitializeResult)

    resources = await client_session.list_resources()
    assert isinstance(resources, ListResourcesResult)

    tools = await client_session.list_tools()
    assert isinstance(tools, ListToolsResult)

    call = await client_session.call_tool("get-current-time", {})
    assert isinstance(call, CallToolResult)

    resource = await client_session.read_resource("datetime://Asia/Chongqing/now")
    assert isinstance(resource, ReadResourceResult)

    await client_session.stop()
    await asyncio.sleep(0)
