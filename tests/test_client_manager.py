import pytest
from mcp.types import CallToolResult, ReadResourceResult
from easymcp.client.ClientManager import ClientManager
from easymcp.client.transports.stdio import StdioServerParameters

@pytest.mark.asyncio
async def test_client_manager_operations():
    mgr = ClientManager()

    searxng = StdioServerParameters(command="uvx", args=["mcp-searxng"])
    timeserver = StdioServerParameters(command="uvx", args=["mcp-timeserver"])

    servers = {
        "searxng": searxng,
        "timeserver": timeserver,
    }

    await mgr.init(servers=servers)
    assert "searxng" in mgr.list_servers()
    assert "timeserver" in mgr.list_servers()

    tools = await mgr.list_tools()
    assert isinstance(tools, list)

    result = await mgr.call_tool("timeserver.get-current-time", {})
    assert isinstance(result, CallToolResult)

    resources = await mgr.list_resources()
    assert isinstance(resources, list)

    resource = await mgr.read_resource("mcp-timeserver+datetime://Africa/Algiers/now")
    assert isinstance(resource, ReadResourceResult)

    await mgr.remove_server("searxng")
    assert "searxng" not in mgr.list_servers()

    await mgr.add_server("searxng", searxng)
    assert "searxng" in mgr.list_servers()