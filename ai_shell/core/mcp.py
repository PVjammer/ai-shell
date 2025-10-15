from __future__ import annotations
import asyncio

from functools import partial
from typing import Optional, Literal
from contextlib import AsyncExitStack
from pydantic import BaseModel

from mcp import ClientSession, StdioServerParameters
from mcp.types import TextContent
from mcp.client.stdio import stdio_client

import logging



class MCPTool:

    def __init__(self, name: str, tool_spec: dict, client: MCPClient) -> None:
        self.name = name
        self._client = client
        self._build_tool(tool_spec)

    def _build_tool(self, tool_spec: dict):
        self.input_schema = tool_spec.inputSchema
        # self._call_func = partial(self._session.call_tool, name=self.name)

    async def execute(self, args={}, **kwargs):
        args.update(kwargs)
        await self._client.reconnect()
        
        # Call Tool

        output = []
        try:
            # result = await self._call_func(arguments=args)
            result = await self._client.session.call_tool(self.name, arguments=args)
            
            for res in result.content:
                if isinstance(res, TextContent):
                    output.append(res.text)
        except Exception as e:
            logging.exception(f"Error calling MCP Tool {e}")
            raise e
        return "\n".join(output)   


class MCPClient:
    name: str = ""
    session: ClientSession = None

    async def _connect_to_server(self, **kwargs):
        raise NotImplementedError()

    async def connect(self, **kwargs):
        await self._connect_to_server(**kwargs)
        self.available_tools: dict = {tool.name: tool for tool in await self.list_tools()}
        self._kwargs = kwargs

    async def reconnect(self):
        await self.connect(**self._kwargs)

    async def list_tools(self):
        if not self.session:  
            raise RuntimeError("No running session")
        response = await self.session.list_tools()
        self.available_tools: dict = {tool.name: tool for tool in response.tools}
        return response.tools
    
    def get_tool(self, name: str) -> MCPTool:
        if name not in self.available_tools:
            raise ValueError(f"Tool {name} is not available for server {name}")
        
        return MCPTool(name=name,tool_spec=self.available_tools[name], client=self)

    def get_all_tools(self) -> list[MCPTool]:
        tool_list = []
        for tool_name in self.available_tools.keys():
            tool_list.append(self.get_tool(tool_name))
        return tool_list

    async def call_tool(self, name: str, arguments: dict = {}):
        
        if not self.session:
            raise RuntimeError("No running session")

        result = await self.session.call_tool(name, arguments)
        return result
    
    async def _cleanup(self):
        raise NotImplementedError()

    async def diconnect(self):
        await self._cleanup()


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
    
    async def _cleanup(self):
        await self.exit_stack.aclose()


async def install_mcp_servers(server_map: dict) -> dict[str, MCPClient]:
    if not server_map or not isinstance(server_map, dict):
        raise ValueError("Invalid MCP Server map.")
    
    mcp_clients = {}
    for server_name, server_obj in server_map["mcpServers"].items():
        _client = StdioMCPClient(name=server_name)
        command = server_obj.get('command')
        if not command:
            raise ValueError("No Command for MCP Server")
        args = server_obj.get("args", [])
        
        await _client.connect(
            command=command,
            arguments=args
        )
        mcp_clients[server_name] = _client
        await _client.diconnect()
    return mcp_clients
