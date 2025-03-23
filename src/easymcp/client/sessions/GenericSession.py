from typing import Protocol, runtime_checkable, Awaitable, Callable
from easymcp.vendored import types

@runtime_checkable
class ToolsCompatible(Protocol):
    async def list_tools(self, force: bool = False) -> types.ListToolsResult: ...
    async def call_tool(self, tool_name: str, args: dict) -> types.CallToolResult: ...

@runtime_checkable
class ResourcesCompatible(Protocol):
    async def list_resources(self, force: bool = False) -> types.ListResourcesResult: ...
    async def read_resource(self, resource_name: str) -> types.ReadResourceResult: ...

@runtime_checkable
class PromptsCompatible(Protocol):
    async def list_prompts(self, force: bool = False) -> types.ListPromptsResult: ...
    async def read_prompt(self, prompt_name: str, args: dict) -> types.GetPromptResult: ...

@runtime_checkable
class SessionProtocol(ToolsCompatible, ResourcesCompatible, PromptsCompatible, Protocol):
    async def init(self) -> None: ...
    async def start(self) -> types.InitializeResult: ...
    async def stop(self) -> None: ...

    async def register_roots_callback(
        self,
        callback: Callable[[types.ListRootsRequest], Awaitable[types.ListRootsResult]],
    ) -> None: ...

    async def register_sampling_callback(
        self,
        callback: Callable[
            [types.CreateMessageRequest], Awaitable[types.CreateMessageResult]
        ],
    ) -> None: ...

    async def register_tools_changed_callback(
        self, callback: Callable[[], Awaitable[None]]
    ) -> None: ...

    async def register_prompts_changed_callback(
        self, callback: Callable[[], Awaitable[None]]
    ) -> None: ...

    async def register_resources_changed_callback(
        self, callback: Callable[[], Awaitable[None]]
    ) -> None: ...

