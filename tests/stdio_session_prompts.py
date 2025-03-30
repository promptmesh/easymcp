import asyncio
from easymcp.client.sessions.mcp import MCPClientSession
from easymcp.client.transports.stdio import StdioTransport, StdioServerParameters


async def main():
    args = StdioServerParameters(command="uvx", args=["mcp-wolfram-alpha"], env={"WOLFRAM_API_KEY": "DEMO"})
    transport = StdioTransport(args)

    client_session = MCPClientSession(transport)
    await client_session.init()

    result = await client_session.start()
    print(f"{result=}")

    # await asyncio.sleep(10)

    prompts = await client_session.list_prompts()
    print(f"{prompts=}")

    resolved = await client_session.read_prompt("wa", {"query": "pi"})
    print(f"{resolved=}")

    # await client_session.stop()
    await asyncio.Future()


asyncio.run(main())
