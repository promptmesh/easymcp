# EasyMCP

EasyMCP is a complete rewrite of the model context protocol (MCP) in Python.

## Installation

```bash
uv add easymcp
```

## Usage

The high level API exposes a ClientManager class that can be used to manage multiple MCP servers.

```python
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
    # initialize the client manager
    await mgr.init(servers=servers)

    # list servers
    print(mgr.list_servers())

    # remove a server
    await mgr.remove_server("searxng")

    # add a server
    await mgr.add_server("searxng", searxng)

    # list tools - these are namespaced by server name automatically
    # {server name}.{tool name}
    print(await mgr.list_tools())

    # call tool
    print(await mgr.call_tool("timeserver.get-current-time", {}))

    # list resources - these are namespaced by server name automatically
    # mcp-{server name}+{resource uri}
    print(await mgr.list_resources())

    # read resource
    print(await mgr.read_resource("mcp-timeserver+datetime://Africa/Algiers/now"))

    await asyncio.Future()

asyncio.run(main())
```

## Core Features

- list tools/resources/prompts caching out of the box
- automatic cache invalidation on tool/resource/prompt change notifications
- out of the box support for parallel requests to servers
- full lifecycle management of servers
- dynamic server addition/removal
- namespaced tools/resources/prompts
- lightweight asyncio native implementation

## Why namespace tools?

Namespaced tools remove need to perform a lookup to find the correct tool. This means:

- faster tool calls
- tool calls can be routed across many MCP hosts at scale
- mcp servers do not need globally unique tool names

## Why namespace resources?

Resources are namespaced in a way that makes it easy to make a resource URI to a specific server. You can:

- check if a URL needs to be resolved via mcp by checking if it starts with `mcp`
- check what server to resolve the URI with
- ingest resources into a search system like elastic search without having to store metadata about the server
- completely eliminate the need to map URIs to servers via a database or lookup table

## Comparison of classes to other MCP libraries

| **easyMCP**    | **modelcontextprotocol/python-sdk** |                              |
| -------------- | ----------------------------------- | ---------------------------- |
| ClientManager  |                                     | manages multiple MCP servers |
| ClientSession  | ClientSession                       | manages a single MCP server  |
| StdioTransport | stdio_client                        | raw subprocess transport     |

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
