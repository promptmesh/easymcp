import pytest
from mcp.types import CallToolResult, ReadResourceResult
from easymcp.client.ClientManager import ClientManager
from easymcp.client.sessions.fastmcp.parameters import FastMcpParameters
from easymcp.client.transports.stdio import StdioServerParameters

@pytest.mark.asyncio
async def test_client_manager_operations():
    mgr = ClientManager()

    searxng = StdioServerParameters(command="uvx", args=["mcp-searxng"])
    timeserver = StdioServerParameters(command="uvx", args=["mcp-timeserver"])
    fastmcpserver = FastMcpParameters(module="fastmcp_test:mcp")

    servers = {
        "searxng": searxng,
        "timeserver": timeserver,
    }

    await mgr.init(servers=servers)
    assert "searxng" in mgr.list_servers()
    assert "timeserver" in mgr.list_servers()

    tools = await mgr.list_tools()
    assert isinstance(tools, list)
    assert len(tools) > 0
    assert 'searxng.search' in [tool.name for tool in tools]
    assert 'timeserver.get-current-time' in [tool.name for tool in tools]

    result = await mgr.call_tool("timeserver.get-current-time", {})
    assert isinstance(result, CallToolResult)

    resources = await mgr.list_resources()
    assert isinstance(resources, list)
    assert len(resources) > 0
    assert 'mcp-timeserver+datetime://Africa/Algiers/now' in [str(resource.uri) for resource in resources]

    resource = await mgr.read_resource("mcp-timeserver+datetime://Africa/Algiers/now")
    assert isinstance(resource, ReadResourceResult)

    await mgr.remove_server("searxng")
    assert "timeserver" in mgr.list_servers()
    assert "searxng" not in mgr.list_servers()

    tools = await mgr.list_tools()
    assert isinstance(tools, list)
    assert len(tools) > 0
    assert 'searxng.search' not in [tool.name for tool in tools]
    assert 'timeserver.get-current-time' in [tool.name for tool in tools]

    await mgr.add_server("searxng", searxng)
    assert "searxng" in mgr.list_servers()
    assert "timeserver" in mgr.list_servers()
    assert "fastmcpserver" not in mgr.list_servers()

    await mgr.add_server("fastmcpserver", fastmcpserver)
    assert "fastmcpserver" in mgr.list_servers()

    resources = await mgr.list_resources()
    assert isinstance(resources, list)
    assert len(resources) > 0

    tools = await mgr.list_tools()
    assert isinstance(tools, list)
    assert len(tools) > 0