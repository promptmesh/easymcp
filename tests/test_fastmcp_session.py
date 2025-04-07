from mcp import ListResourcesResult, ListToolsResult
import pytest

from easymcp.client.sessions.fastmcp.main import FastMCPSession
from easymcp.client.sessions.fastmcp.paramaters import FastMCPParamaters

# test valid module
@pytest.mark.asyncio
async def test_fastmcp_session():
    params = FastMCPParamaters(module="fastmcp_test:mcp")
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


    # resources
    resources = await session.list_resources()
    assert isinstance(resources, ListResourcesResult)
    assert len(resources.resources) > 0
    for resource in resources.resources:
        assert resource.name is not None


# test missing fastmcp class
@pytest.mark.asyncio
async def test_fastmcp_session_missing_fastmcp_class():
    params = FastMCPParamaters(module="fastmcp_test:invalid")
    session = FastMCPSession(params)
    with pytest.raises(ImportError, match="Module fastmcp_test does not contain invalid"):
        await session.init()

# test invalid module
@pytest.mark.asyncio
async def test_fastmcp_session_invalid_module():
    params = FastMCPParamaters(module="invalid:mcp")
    session = FastMCPSession(params)
    with pytest.raises(ImportError, match="Module invalid not found"):
        await session.init()
