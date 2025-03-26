import asyncio
from easymcp.client.sessions.mcp import MCPClientSession
from easymcp.client.transports.stdio import StdioTransport, StdioServerParameters


async def main():
    args = StdioServerParameters(command="uvx", args=["mcp-timeserver"])
    transport = StdioTransport(args)

    client_session = MCPClientSession(transport)
    await client_session.init()

    result = await client_session.start()
    print(f"{result=}")

    # await asyncio.sleep(10)

    resources = await client_session.list_resources()
    print(f"{resources=}")

    tools = await client_session.list_tools()
    print(f"{tools=}")

    call = await client_session.call_tool("get-current-time", {})
    print(f"{call=}")

    resource = await client_session.read_resource("datetime://Asia/Chongqing/now")
    print(f"{resource=}")

    # await client_session.stop()
    await asyncio.Future()


asyncio.run(main())
