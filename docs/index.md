# EasyMCP

EasyMCP is a modern Python implementation of the Model Context Protocol (MCP), designed to manage and interact with distributed AI servers, tools, and resources using a consistent and extensible API.

---

## Features

- 🌐 Multi-server orchestration via `ClientManager`
- 🧠 Built-in support for tools, resources, and prompts
- 🔄 Automatic cache invalidation via push notifications
- 🧪 Async-native, with support for subprocesses, Docker, SSE transports
- 🔌 Easy integration with search engines like Meilisearch

---

## Installation

```bash
uv add easymcp
```

---

## Quickstart

```python
from easymcp.client.ClientManager import ClientManager
from easymcp.client.transports.stdio import StdioServerParameters

mgr = ClientManager()

servers = {
    "timeserver": StdioServerParameters(command="uvx", args=["mcp-timeserver"])
}

await mgr.init(servers)
tools = await mgr.list_tools()
```

Check out [Usage](usage.md) to learn more.
