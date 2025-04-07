import asyncio
import io
import os
import shutil
import sys
import gc
from typing import Literal

from loguru import logger
from pydantic import BaseModel

from easymcp.client.transports.generic import TransportProtocol


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
        self.buffer.seek(0, io.SEEK_END)
        self.buffer.write(data)

    def read_message(self) -> str | None:
        self.buffer.seek(0)
        data = self.buffer.getvalue()

        if b"\n" in data:
            message, rest = data.split(b"\n", 1)
            self.buffer = io.BytesIO(rest)
            return message.decode().strip()

        return None


class StdioTransport(TransportProtocol):
    """Asynchronous stdio transport."""

    state: Literal["constructed", "initialized", "started", "stopped"]
    arguments: StdioServerParameters
    subprocess: asyncio.subprocess.Process | None
    read_buffer: ReadBuffer
    stderr_task: asyncio.Task | None

    def __init__(self, arguments: StdioServerParameters):
        self.state = "constructed"
        self.arguments = arguments.model_copy(deep=True)
        self.read_buffer = ReadBuffer()
        self.subprocess = None
        self.stderr_task: asyncio.Task | None = None

    async def init(self) -> None:
        self.state = "initialized"

        self.arguments.command = (
            shutil.which(self.arguments.command) or self.arguments.command
        )

        env = os.environ.copy()
        env.update(self.arguments.env)
        self.arguments.env = env

    async def start(self) -> None:
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

    async def send(self, message: str) -> None:
        assert self.subprocess and self.subprocess.stdin, "subprocess stdin not open"
        formatted_message = message.strip() + "\n"
        logger.debug(f"Sending message: {formatted_message}")
        self.subprocess.stdin.write(formatted_message.encode())
        await self.subprocess.stdin.drain()

    async def receive(self) -> str:
        assert self.subprocess and self.subprocess.stdout, "subprocess stdout not open"

        while True:
            chunk = await self.subprocess.stdout.read(1024)
            if not chunk:
                break

            self.read_buffer.append(chunk)

            message = self.read_buffer.read_message()
            if message:
                logger.debug(f"Received message: {message}")
                return message

        raise RuntimeError("Subprocess stdout closed before complete message")

    async def read_stderr(self) -> None:
        if self.subprocess is None or self.subprocess.stderr is None:
            return

        async for line in self.subprocess.stderr:
            print(line.decode(), file=sys.stderr, end="")

    async def stop(self) -> None:
        if self.stderr_task:
            self.stderr_task.cancel()
            try:
                await self.stderr_task
            except asyncio.CancelledError:
                pass
            self.stderr_task = None

        if self.subprocess:
            if self.subprocess.returncode is None:
                try:
                    self.subprocess.terminate()
                    await asyncio.wait_for(self.subprocess.wait(), timeout=5)
                except asyncio.TimeoutError:
                    self.subprocess.kill()
                    await self.subprocess.wait()

            if self.subprocess.stdin and not self.subprocess.stdin.is_closing():
                logger.debug("Closing stdin")
                self.subprocess.stdin.close()
                await self.subprocess.stdin.wait_closed()
            self.subprocess.stdin = None

            if self.subprocess.stdout:
                logger.debug("Closing stdout")
                self.subprocess.stdout.feed_eof()
                try:
                    await self.subprocess.stdout.read()
                except Exception:
                    pass
                self.subprocess.stdout = None

            if self.subprocess.stderr:
                logger.debug("Closing stderr")
                self.subprocess.stderr.feed_eof()
                try:
                    await self.subprocess.stderr.read()
                except Exception:
                    pass
                self.subprocess.stderr = None

            await asyncio.sleep(0.1)
            gc.collect()

            self.subprocess = None


        self.state = "stopped"
        logger.info("Transport stopped successfully.")
