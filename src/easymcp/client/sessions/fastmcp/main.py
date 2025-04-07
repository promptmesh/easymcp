import importlib
import os
import sys
from mcp import ListPromptsResult, ListResourcesResult, ListToolsResult, types
from mcp.server.fastmcp import FastMCP

from easymcp.client.sessions.GenericSession import (
    BaseSessionProtocol,
    PromptsCompatible,
    ResourcesCompatible,
    ToolsCompatible,
)
from easymcp.client.sessions.fastmcp.parameters import FastMcpParameters


class FastMCPSession(
    BaseSessionProtocol, ToolsCompatible, ResourcesCompatible, PromptsCompatible
):
    """ASGI style fastmcp session"""

    params: FastMcpParameters
    session: FastMCP

    def __init__(self, params: FastMcpParameters):
        self.params = params

    async def init(self) -> None:
        """Initialize the session"""
        moduleName, identifier = self.params.module.rsplit(":", 1)

        originalEnv = os.environ
        originalArgv = sys.argv.copy()

        mcpEnv = os.environ.copy()
        mcpEnv.update(self.params.env)
        mcpArgv = [
            "uvx",
        ]
        mcpArgv.extend(self.params.argv)

        os.environ = mcpEnv  # type: ignore
        sys.argv = mcpArgv

        try:
            module = importlib.import_module(moduleName)

            cls = getattr(module, identifier)
            if self.params.factory:
                self.session = cls()
            else:
                self.session = cls

        except ModuleNotFoundError as e:
            raise ImportError(f"Module {moduleName} not found") from e

        except AttributeError as e:
            raise ImportError(
                f"Module {moduleName} does not contain {identifier}"
            ) from e

        except ImportError as e:
            raise ImportError(f"Error importing {moduleName}") from e

        finally:
            os.environ = originalEnv
            sys.argv = originalArgv

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
        data = [
            {
                "mimeType": c.mime_type,
                "text": c.content,
                "uri": resource_name,
            }
            for c in content
        ]
        result = {
            "contents": data,
        }
        return types.ReadResourceResult.model_validate(result)

    async def call_tool(self, tool_name: str, args: dict) -> types.CallToolResult:
        """Call a tool"""
        content = await self.session.call_tool(tool_name, args)
        return types.CallToolResult(content=list(content))
