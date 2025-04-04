import shutil
import pytest
from easymcp.client.transports.stdio import StdioTransport, StdioServerParameters

command = shutil.which("echo")

@pytest.mark.skipif(command is None, reason="echo command not found")
@pytest.mark.asyncio
async def test_basic_stdio_transport():
    args = StdioServerParameters(command="echo", args=["Hello, world!"])
    transport = StdioTransport(args)
    await transport.init()
    await transport.start()
    msg = await transport.receive()
    assert "Hello" in msg
    await transport.stop()
