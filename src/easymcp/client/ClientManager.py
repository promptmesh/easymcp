

from easymcp.client.ClientSession import ClientSession


class ClientManager:
    """ClientManager class"""

    sessions: list[ClientSession]

    def __init__(self):
        pass

    async def add_server(self):
        """add a server to the manager"""
        raise NotImplementedError
    
    async def remove_server(self):
        """remove a server from the manager"""
        raise NotImplementedError
    
    async def list_servers(self):
        """list available servers"""
        raise NotImplementedError
    
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