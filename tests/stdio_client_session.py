from easymcp.client.ClientSession import ClientSession
from easymcp.client.transports.stdio import StdioTransport, StdioServerParameters

async def main():
    args = StdioServerParameters(command="echo", args=["Hello, world!"])
    transport = StdioTransport(args)
    client_session = ClientSession(transport)
    await client_session.init()
    result = await client_session.start()
    print(result)
    await client_session.stop()