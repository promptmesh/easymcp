import importlib
from mcp import ListPromptsResult, ListResourcesResult, ListToolsResult, types
from mcp.server.fastmcp import FastMCP

from easymcp.client.sessions.GenericSession import BaseSessionProtocol, PromptsCompatible, ResourcesCompatible, ToolsCompatible
from easymcp.client.sessions.fastmcp.paramaters import FastMCPParamaters

class FastMCPSession(BaseSessionProtocol, ToolsCompatible, ResourcesCompatible, PromptsCompatible):
    """ASGI style fastmcp session"""

    params: FastMCPParamaters
    session: FastMCP

    def __init__(self, params: FastMCPParamaters):
        self.params = params

    async def init(self) -> None:
        """Initialize the session"""
        moduleName, identifier = self.params.module.rsplit(":", 1)

        module = importlib.import_module(moduleName)
        cls = getattr(module, identifier)

        if self.params.factory:
            self.session = cls()
        else:
            self.session = cls

        assert isinstance(self.session, FastMCP), "Session must be a FastMCP instance"

    async def list_prompts(self, force: bool = False) -> ListPromptsResult:
        """List all prompts"""
        return ListPromptsResult(prompts=await self.session.list_prompts())
    
    async def list_resources(self, force: bool = False) -> ListResourcesResult:
        """List all responses"""
        return ListResourcesResult(resources=await self.session.list_resources())
    
    async def list_tools(self, force: bool = False) -> ListToolsResult:
        """List all tools"""
        return ListToolsResult(tools=await self.session.list_tools())
    
    async def read_prompt(self, prompt_name: str, args: dict) -> types.GetPromptResult:
        """Read a prompt"""
        return await self.session.get_prompt(prompt_name, args)
    
    async def read_resource(self, resource_name: str) -> types.ReadResourceResult:
        """Read a resource"""
        content = await self.session.read_resource(resource_name)
        return types.ReadResourceResult(contents=content)
    
    async def call_tool(self, tool_name: str, args: dict) -> types.CallToolResult:
        """Call a tool"""
        content = await self.session.call_tool(tool_name, args)
        return types.CallToolResult(content=content)