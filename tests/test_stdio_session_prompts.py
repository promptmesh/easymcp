import asyncio
from mcp import GetPromptResult, InitializeResult, ListPromptsResult
import pytest
from easymcp.client.sessions.mcp import MCPClientSession
from easymcp.client.transports.stdio import StdioTransport, StdioServerParameters

@pytest.mark.asyncio()
async def test_stdio_client_session_prompts():
    args = StdioServerParameters(command="uvx", args=["mcp-wolfram-alpha"], env={"WOLFRAM_API_KEY": "DEMO"})
    transport = StdioTransport(args)

    client_session = MCPClientSession(transport)
    await client_session.init()

    result = await client_session.start()
    assert isinstance(result, InitializeResult)

    prompts = await client_session.list_prompts()
    assert isinstance(prompts, ListPromptsResult)

    resolved = await client_session.read_prompt("wa", {"query": "pi"})
    assert isinstance(resolved, GetPromptResult)

    await client_session.stop()
    await asyncio.sleep(0)