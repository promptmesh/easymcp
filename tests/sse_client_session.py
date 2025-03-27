import asyncio
from easymcp.client.sessions.mcp import MCPClientSession
from easymcp.client.transports.sse import SseTransport, SseServerParameters


async def main():
    args = SseServerParameters(url="http://localhost:8000/sse")
    transport = SseTransport(args)

    client_session = MCPClientSession(transport)
    await client_session.init()

    result = await client_session.start()
    print(f"{result=}")

    # await asyncio.sleep(10)

    resources = await client_session.list_resources()
    print(f"{resources=}")

    tools = await client_session.list_tools()
    print(f"{tools=}")

    await asyncio.Future()


asyncio.run(main())
