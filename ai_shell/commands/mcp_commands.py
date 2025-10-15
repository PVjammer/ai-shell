import argparse
from pathlib import Path
from ai_shell.core.mcp import MCPClient, MCPTool
from ai_shell.core.command_executor import CommandExecutor

from pprint import pprint


def add_arguments_from_schema(parser, schema, prefix=""):
    """Recursively add arguments to the parser based on JSON schema."""
    properties = schema.get("properties", {})
    required = schema.get("required", [])
    
    for name, prop in properties.items():
        arg_name = f"--{prefix}{name}" if prefix else f"--{name}"
        prop_type = prop.get("type", "string")
        help_text = prop.get("description", "")
        default = prop.get("default")

        # Determine the Python type for argparse
        if prop_type == "integer":
            arg_type = int
        elif prop_type == "number":
            arg_type = float
        elif prop_type == "boolean":
            # For booleans, use store_true/store_false
            if default:
                parser.add_argument(arg_name, action="store_false", help=help_text + " (default: True)")
            else:
                parser.add_argument(arg_name, action="store_true", help=help_text + " (default: False)")
            continue
        elif prop_type == "object":
            # Recursively handle nested objects
            add_arguments_from_schema(parser, prop, prefix=f"{name}.")
            continue
        else:
            arg_type = str

        required_flag = name in required
        parser.add_argument(
            arg_name,
            type=arg_type,
            required=required_flag,
            default=default,
            help=help_text + (f" (default: {default})" if default is not None else "")
        )

def _parse_stdin(stdin):
    pass

class CommandMCP:

    def __init__(self, tool_client: MCPTool) -> None:
        self._client = tool_client
        self._parser = argparse.ArgumentParser()
        self._build_parser_from_schema()

    def _build_parser_from_schema(self):
        tool_schema = self._client.input_schema
        add_arguments_from_schema(schema=tool_schema, parser=self._parser)

    async def run_cmd(self, args, stdin, **options):
        r"""
        """
        try:
            parsed = self._parser.parse_args(args or [])
        except (SystemExit, argparse.ArgumentError):
            return "Error: Invalid arguments. Usage: \\summarize [text|file] [-f FILE] [-i INSTRUCTIONS]"
    
        arguments = vars(parsed)

        result = await self._client.execute(args=arguments)
        await self._client._client.diconnect()
        return result

def register_mcp_commands(executor: CommandExecutor, mcp_servers: dict = {}):
    if not mcp_servers:
        print(f"No MCP Servers installed. Skipping command creation.")
        return
    
    for server_name, client in mcp_servers.items():
        for tool in client.get_all_tools():
            
            executor.register_command(
                    name=tool.name,
                    handler=CommandMCP(tool_client=tool).run_cmd,
                    description=f"MCP Tool {tool.name}",
                    category="MCP"
                )
            print(f"Registered command: '{tool.name}' from MCP Server: '{server_name}'")