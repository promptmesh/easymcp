import pytest
from aiodocker import Docker

from easymcp.client.sessions.mcp import MCPClientSession
from easymcp.client.transports.docker import DockerTransport, DockerServerParameters

@pytest.mark.skip(reason="this test hangs")
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
    print(f"{result=}")

    resources = await client_session.list_resources()
    print(f"{resources=}")

    tools = await client_session.list_tools()
    print(f"{tools=}")

    await client_session.stop()
    print("stopped")
