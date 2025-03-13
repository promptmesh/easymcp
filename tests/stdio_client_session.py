import asyncio
from easymcp.client.ClientSession import ClientSession
from easymcp.client.transports.stdio import StdioTransport, StdioServerParameters

async def main():
    args = StdioServerParameters(command="uvx", args=["mcp-timeserver"])# | tee.exe log.jsonl"])
    transport = StdioTransport(args)
    
    client_session = ClientSession(transport)
    await client_session.init()
    
    result = await client_session.start()
    print(f"{result=}")

    # await asyncio.sleep(10)

    resources = await client_session.list_resources()
    print(f"{resources=}")

    tools = await client_session.list_tools()
    print(f"{tools=}")

    # await client_session.stop()
    await asyncio.Future()

asyncio.run(main())