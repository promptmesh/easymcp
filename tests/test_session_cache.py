from mcp import ListPromptsResult
import pytest
import time
from easymcp.client.sessions.mcp import MCPClientSession
from easymcp.client.transports.stdio import StdioTransport, StdioServerParameters

@pytest.mark.flaky(reruns=3)
@pytest.mark.asyncio
async def test_prompt_cache_is_faster():
    args = StdioServerParameters(
        command="uvx",
        args=["mcp-wolfram-alpha"],
        env={"WOLFRAM_API_KEY": "DEMO"}
    )
    transport = StdioTransport(args)
    client_session = MCPClientSession(transport)

    await client_session.init()
    await client_session.start()

    # First uncached call
    start_uncached = time.perf_counter()
    prompts_uncached = await client_session.list_prompts(force=True)
    uncached_duration = time.perf_counter() - start_uncached

    # Second cached call
    start_cached = time.perf_counter()
    prompts_cached = await client_session.list_prompts()
    cached_duration = time.perf_counter() - start_cached

    print(f"uncached: {uncached_duration:.6f}s, cached: {cached_duration:.6f}s")

    assert isinstance(prompts_uncached, ListPromptsResult), "Expected a list prompts result for uncached call"
    assert isinstance(prompts_cached, ListPromptsResult), "Expected a list prompts result for cached call"
    assert prompts_uncached == prompts_cached  # if results are deterministic

    # Assert cache is faster (allow some margin for fluctuations)
    assert cached_duration < uncached_duration * 0.9, \
        f"Expected cached call to be faster (cached: {cached_duration:.6f}s, uncached: {uncached_duration:.6f}s)"

    await client_session.stop()
