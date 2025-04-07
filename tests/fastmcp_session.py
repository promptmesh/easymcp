from easymcp.client.sessions.fastmcp.main import FastMCPSession
from easymcp.client.sessions.fastmcp.parameters import FastMcpParameters



config = FastMcpParameters(module="fastmcp_test:mcp")

async def main():
    session = FastMCPSession(config)
    await session.init()
    print(await session.list_tools())
    print()
    print(await session.call_tool("get_random_bool", {}))
    print()
    print(await session.list_resources())
    print()
    # print(await session.read_resource("demo://lorem-ipsum"))
    print()
    print(await session.list_prompts())

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())