import asyncio
import os
import shutil
import sys

from loguru import logger
from pydantic import BaseModel

from easymcp.client.transports.generic import GenericTransport


class StdioServerParameters(BaseModel):
    """StdioServerParameters class"""

    command: str
    """command to run"""

    args: list[str] = []
    """arguments to pass to the command"""

    env: dict[str, str] = {}
    """environment variables to set"""

    cwd: str = os.path.curdir
    """current working directory"""

    log_stderr: bool = True
    """log stderr to host stderr"""


class StdioTransport(GenericTransport):
    """StdioTransport class"""

    arguments: StdioServerParameters

    def __init__(self, arguments: StdioServerParameters):
        super().__init__(arguments)
        self.state = "constructed"
        self.arguments = arguments.model_copy(deep=True)

    async def init(self):
        """Perform init logic"""
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
        """Start the transport"""
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
        """Send data to the transport"""
        assert self.subprocess.stdin is not None, "subprocess stdin is not open"

        logger.debug(f"Sending message: {message}")

        self.subprocess.stdin.write(message.strip().encode())
        self.subprocess.stdin.write(b"\n")
        await self.subprocess.stdin.drain()

    async def receive(self):
        """Receive data from the transport"""
        assert self.subprocess.stdout is not None, "subprocess stdout is not open"

        message = (await self.subprocess.stdout.readline()).decode()

        logger.debug(f"Received message: {message}")

        return message

    async def read_stderr(self):
        """Read stderr from the subprocess and print to host stderr"""
        if self.subprocess.stderr is None:
            return

        async for line in self.subprocess.stderr:
            print(line.decode(), file=sys.stderr, end="")

    async def stop(self):
        """Stop the transport"""
        self.state = "stopped"
        try:
            self.subprocess.terminate()

            try:
                await asyncio.wait_for(self.subprocess.wait(), timeout=5)
            except asyncio.TimeoutError:
                self.subprocess.kill()
        
        except RuntimeError:
            pass

