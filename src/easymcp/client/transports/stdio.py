import asyncio
import io
import os
import shutil
import sys

from loguru import logger
from pydantic import BaseModel

from easymcp.client.transports.generic import GenericTransport


class StdioServerParameters(BaseModel):
    """Configuration for StdioTransport."""

    command: str
    """command to run"""

    args: list[str] = []
    """arguments to pass to the command"""

    env: dict[str, str] = {}
    """environment variables to set"""

    cwd: str = os.path.curdir
    """current working directory"""

    log_stderr: bool = True


class ReadBuffer:
    """Buffered reader using BytesIO to handle chunked stdio input."""

    def __init__(self):
        self.buffer = io.BytesIO()

    def append(self, data: bytes):
        """Append new data to the buffer."""
        self.buffer.seek(0, io.SEEK_END)  # Move to the end before writing
        self.buffer.write(data)

    def read_message(self) -> str | None:
        """Extracts the next full message (newline-delimited)."""
        self.buffer.seek(0)  # Move to the start
        data = self.buffer.getvalue()

        if b"\n" in data:
            message, rest = data.split(b"\n", 1)  # Extract first message
            self.buffer = io.BytesIO(rest)  # Keep remaining data
            return message.decode().strip()

        return None


class StdioTransport(GenericTransport):
    """Asynchronous stdio-based transport."""

    arguments: StdioServerParameters

    def __init__(self, arguments: StdioServerParameters):
        super().__init__(arguments)
        self.state = "constructed"
        self.arguments = arguments.model_copy(deep=True)
        self.read_buffer = ReadBuffer()

    async def init(self):
        """Perform initialization."""

        self.state = "initialized"

        # Resolve command
        self.arguments.command = (
            shutil.which(self.arguments.command) or self.arguments.command
        )

        # Inherit environment variables
        env = os.environ.copy()
        env.update(self.arguments.env)
        self.arguments.env = env

    async def start(self):
        """Start the transport process."""
        self.state = "started"

        self.subprocess = await asyncio.create_subprocess_exec(
            self.arguments.command,
            *self.arguments.args,
            cwd=self.arguments.cwd,
            env=self.arguments.env,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        if self.arguments.log_stderr:
            self.stderr_task = asyncio.create_task(self.read_stderr())

    async def send(self, message: str):
        """Send a newline-delimited JSON message."""
        assert self.subprocess is not None, "subprocess is not open"
        assert self.subprocess.stdin is not None, "subprocess stdin is not open"

        formatted_message = message.strip() + "\n"  # Ensure newline
        logger.debug(f"Sending message: {formatted_message}")

        self.subprocess.stdin.write(formatted_message.encode())
        await self.subprocess.stdin.drain()

    async def receive(self):
        """Receive a full message using buffered reading."""
        assert self.subprocess is not None, "subprocess is not open"
        assert self.subprocess.stdout is not None, "subprocess stdout is not open"

        while True:
            chunk = await self.subprocess.stdout.read(1024)
            if not chunk:
                break  # EOF or process closed

            self.read_buffer.append(chunk)

            message = self.read_buffer.read_message()
            if message:
                logger.debug(f"Received message: {message}")
                return message  # Return complete message
            
        raise RuntimeError("Subprocess stdout is not open")

    async def read_stderr(self):
        """Continuously read and print stderr."""
        if self.subprocess is None:
            return

        if self.subprocess.stderr is None:
            return

        async for line in self.subprocess.stderr:
            print(line.decode(), file=sys.stderr, end="")

    async def stop(self):
        """Stop the transport gracefully."""

        try:
            if self.subprocess:
                self.subprocess.terminate()
                try:
                    await asyncio.wait_for(self.subprocess.wait(), timeout=5)
                except asyncio.TimeoutError:
                    self.subprocess.kill()
                    await self.subprocess.wait()

            logger.info("Transport stopped successfully.")
        except Exception as e:
            logger.error(f"Error stopping transport: {e}")
        finally:
            self.subprocess = None
            self.state = "stopped"
