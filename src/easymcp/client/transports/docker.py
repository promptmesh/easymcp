import asyncio
from typing import Any, Literal

import anyio
import anyio.abc
from aiodocker import Docker, containers
from anyio.streams.memory import MemoryObjectReceiveStream, MemoryObjectSendStream
from loguru import logger
from pydantic import BaseModel, Field

from easymcp.client.transports.generic import TransportProtocol


class DockerServerParameters(BaseModel):
    """Configuration for Docker transport."""

    image: str = Field(description="Image of the docker container")
    args: list[str] = Field(
        default_factory=list,
        description="Command line arguments for the docker container",
    )
    env: dict[str, str] = Field(
        default_factory=dict,
        description="Environment variables for the docker container",
    )


class DockerTransport(TransportProtocol):
    state: Literal["constructed", "initialized", "started", "stopped"] = "constructed"

    def __init__(self, config: DockerServerParameters) -> None:
        self.config = config
        self.docker: Docker | None = None
        self.container: containers.DockerContainer | None = None
        self.attach_result: Any = None

        self._reader_send: MemoryObjectSendStream[str]
        self._reader_recv: MemoryObjectReceiveStream[str]

        self._writer_send: MemoryObjectSendStream[str]
        self._writer_recv: MemoryObjectReceiveStream[str]

        self._task_group: anyio.abc.TaskGroup | None = None

    async def init(self) -> None:
        self.docker = Docker()
        await self.docker.images.pull(self.config.image)

        self._reader_send, self._reader_recv = anyio.create_memory_object_stream()
        self._writer_send, self._writer_recv = anyio.create_memory_object_stream()

        self.state = "initialized"
        logger.debug("DockerTransport initialized")

    async def start(self) -> None:
        if not self.docker:
            raise RuntimeError("Docker not initialized")

        self.container = await self.docker.containers.create(
            {
                "Image": self.config.image,
                "Cmd": self.config.args,
                "OpenStdin": True,
                "AttachStdin": True,
                "AttachStdout": True,
                "AttachStderr": True,
                "Tty": False,
                "Env": [f"{k}={v}" for k, v in self.config.env.items()],
                "HostConfig": {"AutoRemove": True},
            }
        )

        await self.container.start()
        logger.debug(f"Started container {self.container.id}")

        self.attach_result = self.container.attach(stdin=True, stdout=True, stderr=True)

        async def read_stdout():
            assert self.attach_result is not None

            buffer = ""
            async with self._reader_send:
                while True:
                    try:
                        msg = await self.attach_result.read_out()
                        if msg is None:
                            logger.debug("Docker stream closed (EOF)")
                            break
                        if msg.data is None:
                            continue

                        if isinstance(msg.data, (bytes, bytearray)):
                            chunk = msg.data.decode("utf-8", errors="replace")
                        else:
                            chunk = str(msg.data)

                        buffer += chunk
                        while "\n" in buffer:
                            line, buffer = buffer.split("\n", 1)
                            await self._reader_send.send(line)
                    except Exception as e:
                        logger.error(f"Error reading container output: {e}")
                        break
            logger.debug("read_stdout task exited")

        async def write_stdin():
            assert self.attach_result is not None
            async with self._writer_recv:
                async for msg in self._writer_recv:
                    try:
                        await self.attach_result.write_in(msg.encode("utf-8") + b"\n")
                    except Exception as e:
                        logger.warning(f"Failed to write to container stdin: {e}")
            logger.debug("write_stdin task exited")

        self._task_group = anyio.create_task_group()
        await self._task_group.__aenter__()
        self._task_group.start_soon(read_stdout)
        self._task_group.start_soon(write_stdin)

        self.state = "started"
        await asyncio.sleep(1)

    async def stop(self) -> None:
        logger.debug("Stopping DockerTransport...")

        if self.attach_result:
            try:
                await self.attach_result.close()
            except Exception:
                pass
            self.attach_result = None

        if self.container:
            try:
                await self.container.stop()
            except Exception:
                pass
            try:
                await self.container.delete()
            except Exception:
                pass
            self.container = None

        # Close input stream to stop write_stdin task
        try:
            await self._writer_send.aclose()
        except Exception:
            pass

        if self._task_group:
            await self._task_group.__aexit__(None, None, None)
            self._task_group = None

        if self.docker:
            await self.docker.close()
            self.docker = None

        self.state = "stopped"
        logger.debug("DockerTransport stopped and cleaned up")


    async def send(self, message: str) -> None:
        if self.state != "started":
            raise RuntimeError("Transport not started")
        await self._writer_send.send(message)

    async def receive(self) -> str:
        if self.state != "started":
            raise RuntimeError("Transport not started")
        return await self._reader_recv.receive()
