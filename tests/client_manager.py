import asyncio

from easymcp.client.ClientManager import ClientManager
from easymcp.client.transports.stdio import StdioServerParameters

mgr = ClientManager()

searxng = StdioServerParameters(
    command="uvx",
    args=["mcp-searxng"],
)

timeserver = StdioServerParameters(
    command="uvx",
    args=["mcp-timeserver"],
)

servers = {
    "searxng": searxng,
    "timeserver": timeserver,
}

async def main():
    print("Listing servers")
    await mgr.init(servers=servers)
    print(mgr.list_servers())

    # print("Removing searxng")
    # await mgr.remove_server("searxng")
    # print(mgr.list_servers())

    # print("Adding searxng")
    # await mgr.add_server("searxng", searxng)
    # print(mgr.list_servers())

    print("Listing tools")
    print(await mgr.list_tools())

    print("Calling tool")
    print(await mgr.call_tool("timeserver.get-current-time", {}))

    print("Listing resources")
    print(await mgr.list_resources())

    print("Reading resource")
    # await mgr.sessions["timeserver"].read_resource("datetime://Africa/Algiers/now")
    print(await mgr.read_resource("mcp-timeserver+datetime://Africa/Algiers/now"))


    await asyncio.Future()

asyncio.run(main())