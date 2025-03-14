import asyncio
from easymcp.client.transports.stdio import StdioTransport, StdioServerParameters


async def main():
    args = StdioServerParameters(command="echo", args=["Hello, world!"])
    transport = StdioTransport(args)
    await transport.init()
    await transport.start()
    print(f"{await transport.receive()=}")
    await transport.stop()


if __name__ == "__main__":
    asyncio.run(main())
