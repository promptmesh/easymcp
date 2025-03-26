from inspect import iscoroutinefunction
from typing import Awaitable, Callable

from mcp import types
from pydantic import AnyUrl

from easymcp.client.SessionMaker import make_transport, transportTypes
from easymcp.client.sessions.GenericSession import (
    BaseSessionProtocol,
    LifeSpanProtocol,
    PromptsCompatible,
    PushingPromptsCompatible,
    PushingResourcesCompatible,
    PushingRootsCompatible,
    PushingSamplingCompatible,
    PushingToolsCompatible,
    ResourcesCompatible,
    ToolsCompatible,
)
from easymcp.client.utils import format_server_name


class ClientManager:
    """ClientManager class"""

    default_list_roots_callback: (
        Callable[[types.ListRootsRequest], Awaitable[types.ListRootsResult]] | None
    ) = None
    default_sampling_callback: (
        Callable[[types.CreateMessageRequest], Awaitable[types.CreateMessageResult]]
        | None
    ) = None

    default_list_tools_changed_callback: Callable[[], Awaitable[None]] | None = None
    default_list_prompts_changed_callback: Callable[[], Awaitable[None]] | None = None
    default_list_resources_changed_callback: Callable[[], Awaitable[None]] | None = None

    sessions: dict[str, BaseSessionProtocol] = dict()

    def __init__(self):
        pass

    async def init(self, servers: dict[str, transportTypes]):
        """initialize the client manager"""

        for server_name, server in servers.items():
            server_name = format_server_name(server_name)

            if server_name in self.sessions:
                raise ValueError(f"Server name {server_name} already exists")

            session = make_transport(server)
            self.sessions[server_name] = session

            await session.init()

            if self.default_list_roots_callback is not None:
                if isinstance(session, PushingRootsCompatible):
                    await session.register_roots_callback(
                        self.default_list_roots_callback
                    )

            if self.default_sampling_callback is not None:
                if isinstance(session, PushingSamplingCompatible):
                    await session.register_sampling_callback(
                        self.default_sampling_callback
                    )

            if isinstance(session, LifeSpanProtocol):
                await session.start()

    async def add_server(self, name: str, transport: transportTypes):
        """add a server to the manager"""

        name = format_server_name(name)

        if name in self.sessions:
            raise ValueError(f"Session {name} already exists")

        session = make_transport(transport)
        await session.init()

        if self.default_list_roots_callback is not None:
            if isinstance(session, PushingRootsCompatible):
                await session.register_roots_callback(self.default_list_roots_callback)

        if self.default_sampling_callback is not None:
            if isinstance(session, PushingSamplingCompatible):
                await session.register_sampling_callback(self.default_sampling_callback)

        if isinstance(session, LifeSpanProtocol):
            await session.start()

        self.sessions[name] = session

        return True

    async def remove_server(self, name: str):
        """remove a server from the manager"""

        name = format_server_name(name)

        if name not in self.sessions:
            raise ValueError(f"Session {name} does not exist")

        session = self.sessions[name]
        if isinstance(session, LifeSpanProtocol):
            await session.stop()
        del self.sessions[name]

        return True

    def list_servers(self):
        """list available servers"""

        return list(self.sessions.keys())

    async def list_tools(self, force: bool = False) -> list[types.Tool]:
        """list tools on all servers"""

        result: list[types.Tool] = []

        for name, session in self.sessions.items():
            if not isinstance(session, ToolsCompatible):
                continue

            tools = await session.list_tools(force=force)
            if tools is None:
                continue
            for tool in tools.tools:
                tool.name = f"{name}.{tool.name}"
                result.append(tool)

        return result

    async def call_tool(self, name: str, args: dict):
        """call a tool"""

        if "." not in name:
            raise ValueError("Tool name must be in the format <server>.<tool>")

        server_name, tool_name = name.split(".", 1)
        session = self.sessions.get(server_name)

        if session is None:
            raise ValueError(f"Server {server_name} not found")

        if not isinstance(session, ToolsCompatible):
            raise ValueError(f"Server {server_name} does not support tools")

        return await session.call_tool(tool_name, args)

    async def list_resources(self) -> list[types.Resource]:
        """list resources on all servers"""

        result: list[types.Resource] = []

        for name, session in self.sessions.items():
            if not isinstance(session, ResourcesCompatible):
                continue

            resources = await session.list_resources()
            if resources is None:
                continue
            for resource in resources.resources:
                # do not map known schemes to mcp
                if resource.uri.scheme not in (
                    "http",
                    "https",
                ):
                    resource.uri = AnyUrl(f"mcp-{name}+{resource.uri}")

                result.append(resource)

        return result

    async def read_resource(self, uri: AnyUrl | str):
        """read a resource"""

        if not isinstance(uri, AnyUrl):
            uri = AnyUrl(uri)

        if "+" not in uri.scheme:
            raise ValueError("Resource URI must be in the format mcp-<server>+<uri>")

        server_name, resource_scheme = uri.scheme.split("+", 1)
        server_name = server_name.removeprefix("mcp-")
        session = self.sessions.get(server_name)

        if session is None:
            raise ValueError(f"Server {server_name} not found")

        if not isinstance(session, ResourcesCompatible):
            raise ValueError(f"Server {server_name} does not support resources")

        # new_uri = str(URL(str(uri)).with_scheme(resource_scheme))
        new_uri = str(uri).removeprefix(f"mcp-{server_name}+")

        return await session.read_resource(new_uri)

    async def list_prompts(self) -> list[types.Prompt]:
        """list prompts on all servers"""

        result: list[types.Prompt] = []

        for name, session in self.sessions.items():
            if not isinstance(session, PromptsCompatible):
                continue

            prompts = await session.list_prompts()
            if prompts is None:
                continue
            for prompt in prompts.prompts:
                prompt.name = f"{name}.{prompt.name}"
                result.append(prompt)

        return result

    async def read_prompt(self, name: str, args: dict):
        """read a prompt"""
        raise NotImplementedError

    # callbacks
    async def register_roots_callback(
        self,
        callback: Callable[[types.ListRootsRequest], Awaitable[types.ListRootsResult]],
    ):
        """register a callback for roots"""
        assert callable(callback), f"{callback} must be callable"
        assert iscoroutinefunction(callback), f"{callback} must be an async function"

        self.default_list_roots_callback = callback

        sessions = filter(
            lambda x: isinstance(x, PushingRootsCompatible), self.sessions.values()
        )
        for session in sessions:
            assert isinstance(session, PushingRootsCompatible)  # makes mypy happy
            await session.register_roots_callback(callback)

    async def register_sampling_callback(
        self,
        callback: Callable[
            [types.CreateMessageRequest], Awaitable[types.CreateMessageResult]
        ],
    ):
        """register a callback for sampling"""
        assert callable(callback), f"{callback} must be callable"
        assert iscoroutinefunction(callback), f"{callback} must be an async function"

        self.default_sampling_callback = callback

        sessions = filter(
            lambda x: isinstance(x, PushingSamplingCompatible), self.sessions.values()
        )
        for session in sessions:
            assert isinstance(session, PushingSamplingCompatible)  # makes mypy happy
            await session.register_sampling_callback(callback)

    async def register_tools_changed_callback(
        self, callback: Callable[[], Awaitable[None]]
    ):
        """register a callback for tools changed"""
        assert callable(callback), f"{callback} must be callable"
        assert iscoroutinefunction(callback), f"{callback} must be an async function"

        self.default_list_tools_changed_callback = callback

        sessions = filter(
            lambda x: isinstance(x, PushingToolsCompatible), self.sessions.values()
        )
        for session in sessions:
            assert isinstance(session, PushingToolsCompatible)  # makes mypy happy
            await session.register_tools_changed_callback(callback)

    async def register_prompts_changed_callback(
        self, callback: Callable[[], Awaitable[None]]
    ):
        """register a callback for prompts changed"""
        assert callable(callback), f"{callback} must be callable"
        assert iscoroutinefunction(callback), f"{callback} must be an async function"

        self.default_list_prompts_changed_callback = callback

        sessions = filter(
            lambda x: isinstance(x, PushingPromptsCompatible), self.sessions.values()
        )
        for session in sessions:
            assert isinstance(session, PushingPromptsCompatible)  # makes mypy happy
            await session.register_prompts_changed_callback(callback)

    async def register_resources_changed_callback(
        self, callback: Callable[[], Awaitable[None]]
    ):
        """register a callback for resources changed"""
        assert callable(callback), f"{callback} must be callable"
        assert iscoroutinefunction(callback), f"{callback} must be an async function"

        self.default_list_resources_changed_callback = callback

        sessions = filter(
            lambda x: isinstance(x, PushingResourcesCompatible), self.sessions.values()
        )
        for session in sessions:
            assert isinstance(session, PushingResourcesCompatible)
            await session.register_resources_changed_callback(callback)
