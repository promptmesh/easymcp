from mcp import ListResourcesResult, ListToolsResult, ReadResourceResult
from mcp.types import CallToolResult
import pytest

from easymcp.client.sessions.fastmcp.main import FastMCPSession
from easymcp.client.sessions.fastmcp.parameters import FastMcpParameters

# test valid module
@pytest.mark.asyncio
async def test_fastmcp_session():
    params = FastMcpParameters(module="fastmcp_test:mcp")
    session = FastMCPSession(params)
    await session.init()
    assert session.session is not None

    # tools
    tools = await session.list_tools()
    assert isinstance(tools, ListToolsResult)
    assert len(tools.tools) > 0
    for tool in tools.tools:
        assert tool.name is not None
        assert tool.inputSchema is not None

    tool_call = await session.call_tool(tool_name="get_random_bool", args={})
    assert isinstance(tool_call, CallToolResult)
    assert isinstance(tool_call.content, list)
    assert len(tool_call.content) > 0
    assert tool_call.isError is False

    # resources
    resources = await session.list_resources()
    assert isinstance(resources, ListResourcesResult)
    assert len(resources.resources) > 0
    for resource in resources.resources:
        assert resource.name is not None

    resolved_resource = await session.read_resource(resource_name="demo://random-number")
    assert isinstance(resolved_resource, ReadResourceResult)
    assert isinstance(resolved_resource.contents, list)
    assert len(resolved_resource.contents) > 0


# test missing fastmcp class
@pytest.mark.asyncio
async def test_fastmcp_session_missing_fastmcp_class():
    params = FastMcpParameters(module="fastmcp_test:invalid")
    session = FastMCPSession(params)
    with pytest.raises(ImportError, match="Module fastmcp_test does not contain invalid"):
        await session.init()

# test invalid module
@pytest.mark.asyncio
async def test_fastmcp_session_invalid_module():
    params = FastMcpParameters(module="invalid:mcp")
    session = FastMCPSession(params)
    with pytest.raises(ImportError, match="Module invalid not found"):
        await session.init()
