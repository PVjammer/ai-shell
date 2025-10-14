import asyncio

from functools import partial
from typing import Optional, Literal
from contextlib import AsyncExitStack
from pydantic import BaseModel

from mcp import ClientSession, StdioServerParameters
from mcp.types import TextContent
from mcp.client.stdio import stdio_client


class MCPTool:

    def __init__(self, name: str, tool_spec: dict, session: ClientSession) -> None:
        self.name = name
        self._session = session
        self._build_tool(tool_spec)

    def _build_tool(self, tool_spec: dict):
        self.input_schema = tool_spec.inputSchema
        self._call_func = partial(self._session.call_tool, name=self.name)

    async def execute(self, args={}, **kwargs):
        args.update(kwargs)

        if not self._session:
            raise RuntimeError("No running session")
        # Call Tool
        output = []
        result = await self._call_func(arguments=args)
        for res in result.content:
            if isinstance(res, TextContent):
                output.append(res.text)
        return "\n".join(output)   


class MCPClient:
    name: str = ""
    session: ClientSession = None

    async def _connect_to_server(*args, **kwargs):
        raise NotImplementedError()

    async def connect(self, *args, **kwargs):
        await self._connect_to_server(*args, **kwargs)

    async def list_tools(self):
        if not self.session:  
            raise RuntimeError("No running session")
        response = await self.session.list_tools()
        return response.tools
    
    async def get_tool(self, name: str):
        available_tools: dict = {tool.name: tool for tool in await self.list_tools()}

        if name not in available_tools:
            raise ValueError(f"Tool {name} is not available for server {name}")
        
        return MCPTool(name=name,tool_spec=available_tools[name], session=self.session)

    async def call_tool(self, name: str, arguments: dict = {}):
        if not self.session:
            raise RuntimeError("No running session")

        result = await self.session.call_tool(name, arguments)
        return result


class StdioMCPClient(MCPClient):
    def __init__(self, name: str = "") -> None:
        self.name = name
        self.exit_stack = AsyncExitStack()
        self.session: Optional[ClientSession] = None

    async def _connect_to_server(self,*,command: str, arguments: list = [], env: dict = {}):
        server_params = StdioServerParameters(
            command=command,
            args=arguments,
            env=env
        )
        
        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        self.stdio, self.write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))

        await self.session.initialize()
    
    async def cleanup(self):
        await self.exit_stack.aclose()


