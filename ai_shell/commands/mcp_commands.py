import argparse
from pathlib import Path
from ai_shell.core.mcp import MCPClient, MCPTool


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

def _get_text_input(stdin, content, file_path=None):
    """
    Helper to get text input from stdin, content arg, or file.

    Args:
        stdin: Stdin input (takes priority)
        content: Content argument (can be text or auto-detected file)
        file_path: Explicit file path from -f/--file option

    Returns:
        tuple: (text, error)
    """
    # Priority 1: Explicit file path from -f option
    if file_path:
        try:
            return Path(file_path).read_text(encoding="utf-8"), None
        except Exception as e:
            return None, f"Error reading file {file_path}: {e}"

    # Priority 2: Stdin (from pipe)
    if stdin:
        return stdin, None

    # Priority 3: Content argument
    if not content:
        return None, "Error: No input provided"

    # Try auto-detect as file
    path = Path(content)
    if path.is_file():
        try:
            return path.read_text(encoding="utf-8"), None
        except Exception:
            pass  # Not readable, treat as text

    # Otherwise treat as direct text
    return content, None

class CommandMCP:

    def __init__(self, tool_client: MCPTool) -> None:
        self._client = tool_client
        self._parser = argparse.ArgumentParser()
        self._build_parser_from_schema()

    def _build_parser_from_schema(self):
        tool_schema = self._client.input_schema
        add_arguments_from_schema(schema=tool_schema, parser=self._parser)

    def run_cmd(self, args, stdin, **options):
        r"""
        """
        try:
            parsed = self._parser.parse_args(args or [])  
        except (SystemExit, argparse.ArgumentError):
            return "Error: Invalid arguments. Usage: \\summarize [text|file] [-f FILE] [-i INSTRUCTIONS]"