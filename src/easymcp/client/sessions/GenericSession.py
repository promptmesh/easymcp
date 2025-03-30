from typing import Protocol, runtime_checkable, Awaitable, Callable

from mcp import types

# === Core Capability Protocols ===

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


# === Session Lifecycle Protocols ===

@runtime_checkable
class InitializerProtocol(Protocol):
    async def init(self) -> None: ...


@runtime_checkable
class LifeSpanProtocol(InitializerProtocol, Protocol):
    async def start(self) -> types.InitializeResult: ...
    async def stop(self) -> None: ...


# === Reactive / Push-capable Protocols ===

@runtime_checkable
class PushingToolsCompatible(ToolsCompatible, Protocol):
    async def register_tools_changed_callback(
        self, callback: Callable[[], Awaitable[None]]
    ) -> None: ...


@runtime_checkable
class PushingPromptsCompatible(PromptsCompatible, Protocol):
    async def register_prompts_changed_callback(
        self, callback: Callable[[], Awaitable[None]]
    ) -> None: ...


@runtime_checkable
class PushingResourcesCompatible(ResourcesCompatible, Protocol):
    async def register_resources_changed_callback(
        self, callback: Callable[[], Awaitable[None]]
    ) -> None: ...


@runtime_checkable
class PushingRootsCompatible(Protocol):
    async def register_roots_callback(
        self, callback: Callable[[types.ListRootsRequest], Awaitable[types.ListRootsResult]]
    ) -> None: ...


@runtime_checkable
class PushingSamplingCompatible(Protocol):
    async def register_sampling_callback(
        self, callback: Callable[[types.CreateMessageRequest], Awaitable[types.CreateMessageResult]]
    ) -> None: ...

# === Top-Level Session Protocols ===

@runtime_checkable
class BaseSessionProtocol(InitializerProtocol, Protocol): ...