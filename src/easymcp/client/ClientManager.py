import asyncio
from typing import Awaitable
from easymcp.client.ClientSession import ClientSession
from easymcp.client.SessionMaker import make_transport, transportTypes


class ClientManager:
    """ClientManager class"""

    default_list_roots_callback: Awaitable | None = None
    default_list_sampling_callback: Awaitable | None = None

    sessions: dict[str, ClientSession]

    def __init__(self):
        pass

    async def init(self, servers: dict[str, transportTypes]):
        """initialize the client manager"""
        self.sessions = dict()

        for server_name, server in servers.items():
            self.sessions[server_name] = make_transport(server)

        await asyncio.gather(*[session.init() for session in self.sessions.values()])

        if self.default_list_roots_callback is not None:
            await asyncio.gather(
                *[
                    session.register_roots_callback(self.default_list_roots_callback)
                    for session in self.sessions.values()
                ]
            )

        if self.default_list_sampling_callback is not None:
            await asyncio.gather(
                *[
                    session.register_sampling_callback(
                        self.default_list_sampling_callback
                    )
                    for session in self.sessions.values()
                ]
            )

        await asyncio.gather(*[session.start() for session in self.sessions.values()])

    async def add_server(self, name: str, transport: transportTypes):
        """add a server to the manager"""

        if name in self.sessions:
            raise ValueError(f"Session {name} already exists")

        session = make_transport(transport)
        await session.init()

        if self.default_list_roots_callback is not None:
            await session.register_roots_callback(self.default_list_roots_callback)

        if self.default_list_sampling_callback is not None:
            await session.register_sampling_callback(
                self.default_list_sampling_callback
            )

        await session.start()
        self.sessions[name] = session

        return True

    async def remove_server(self, name: str):
        """remove a server from the manager"""

        if name not in self.sessions:
            raise ValueError(f"Session {name} does not exist")

        await self.sessions[name].stop()
        del self.sessions[name]

        return True

    def list_servers(self):
        """list available servers"""

        return list(self.sessions.keys())

    async def list_tools(self):
        """list tools on all servers"""
        raise NotImplementedError

    async def call_tool(self, name: str, args: dict):
        """call a tool"""
        raise NotImplementedError

    async def list_resources(self):
        """list resources on all servers"""
        raise NotImplementedError

    async def read_resource(self, uri: str):
        """read a resource"""
        raise NotImplementedError

    async def list_prompts(self):
        """list prompts on all servers"""
        raise NotImplementedError

    async def read_prompt(self, name: str, args: dict):
        """read a prompt"""
        raise NotImplementedError

    # callbacks
    async def register_roots_callback(self, callback: Awaitable):
        """register a callback for roots"""
        self.default_list_roots_callback = callback
        for session in self.sessions.values():
            await session.register_roots_callback(callback)

    async def register_sampling_callback(self, callback: Awaitable):
        """register a callback for sampling"""
        self.default_list_sampling_callback = callback
        for session in self.sessions.values():
            await session.register_sampling_callback(callback)
