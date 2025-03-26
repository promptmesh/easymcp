import asyncio
import time
from easymcp.client.sessions.mcp import MCPClientSession
from easymcp.client.transports.stdio import StdioTransport, StdioServerParameters

class AsyncTimer:
    def __enter__(self):
        self.start = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.end = time.perf_counter()
        self.duration = self.end - self.start
        print(f"Elapsed time: {self.duration:.6f} seconds")

async def main():
    args = StdioServerParameters(command="uvx", args=["mcp-wolfram-alpha"], env={"WOLFRAM_API_KEY": "DEMO"})
    transport = StdioTransport(args)

    client_session = MCPClientSession(transport)
    await client_session.init()

    result = await client_session.start()
    print(f"{result=}")

    # await asyncio.sleep(10)

    with AsyncTimer():
        prompts = await client_session.list_prompts()
        print(f"{prompts=}")

    with AsyncTimer():
        prompts = await client_session.list_prompts()
        print(f"{prompts=}")

    with AsyncTimer():
        prompts = await client_session.list_prompts(force=True)
        print(f"{prompts=}")

    # await client_session.stop()
    await asyncio.Future()


asyncio.run(main())
