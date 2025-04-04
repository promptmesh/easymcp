import pytest
from aiodocker import Docker
from mcp.types import InitializeResult, ListResourcesResult, ListToolsResult

from easymcp.client.sessions.mcp import MCPClientSession
from easymcp.client.transports.docker import DockerServerParameters, DockerTransport


@pytest.mark.asyncio
async def test_docker_transport():
    try:
        docker = Docker()
        await docker.version()
    except Exception as e:
        print(f"Docker not running: {e}")
        pytest.skip("Docker is not running")

    args = DockerServerParameters(image="mcp/time")
    transport = DockerTransport(args)

    client_session = MCPClientSession(transport)
    await client_session.init()

    result = await client_session.start()
    assert isinstance(result, InitializeResult)

    resources = await client_session.list_resources()
    assert isinstance(resources, ListResourcesResult)

    tools = await client_session.list_tools()
    assert isinstance(tools, ListToolsResult)

    await client_session.stop()
    print("stopped")
