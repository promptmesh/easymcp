# Usage

## Managing Servers

Use `ClientManager` to start and stop multiple MCP servers.

```python
from easymcp.client.ClientManager import ClientManager
from easymcp.client.transports.stdio import StdioServerParameters

mgr = ClientManager()

await mgr.init({
    "timeserver": StdioServerParameters(command="uvx", args=["mcp-timeserver"])
})
```

---

## Listing & Calling Tools

```python
tools = await mgr.list_tools()
result = await mgr.call_tool("timeserver.get-current-time", {})
```

---

## Reading Resources

```python
resources = await mgr.list_resources()
data = await mgr.read_resource("mcp-timeserver+datetime://UTC/now")
```

---

## Using Prompts

```python
prompts = await mgr.list_prompts()
response = await mgr.read_prompt("wa", {"query": "pi"})
```
