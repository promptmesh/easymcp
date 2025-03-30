import asyncio
from easymcp.client.sessions.mcp import MCPClientSession
from easymcp.client.transports.docker import DockerTransport, DockerServerParameters


async def main():
    args = DockerServerParameters(image="mcp/time")
    transport = DockerTransport(args)

    client_session = MCPClientSession(transport)
    await client_session.init()

    result = await client_session.start()
    print(f"{result=}")

    # await asyncio.sleep(10)

    resources = await client_session.list_resources()
    print(f"{resources=}")

    tools = await client_session.list_tools()
    print(f"{tools=}")

    await client_session.stop()
    print("stopped")


asyncio.run(main())
