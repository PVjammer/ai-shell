"""Input parser for ai-shell."""

from typing import List, Optional
from dataclasses import dataclass
from enum import Enum
import shlex
import re


class CommandType(Enum):
    """Types of commands."""
    BASH = "bash"           # !command
    CHAT = "chat"           # ?question
    TOOL = "tool"           # \toolname
    PIPELINE = "pipeline"   # cmd1 | cmd2
    META = "meta"           # /help
    UNKNOWN = "unknown"


@dataclass
class ParsedCommand:
    """Parsed command representation."""
    type: CommandType
    raw: str

    # For bash commands
    command: Optional[str] = None

    # For chat
    message: Optional[str] = None

    # For tools
    tool_name: Optional[str] = None
    tool_args: Optional[List[str]] = None
    tool_options: Optional[dict] = None  # --flag or --key=value options

    # For pipelines
    stages: Optional[List['ParsedCommand']] = None

    # For meta commands
    meta_command: Optional[str] = None
    meta_args: Optional[List[str]] = None


class ParseError(Exception):
    """Parse error exception."""
    pass


class Parser:
    r"""
    Input parser for ai-shell.

    Parses user input and classifies into command types:
    - Bash commands (! prefix)
    - Chat messages (? prefix)
    - AI tools (\ prefix)
    - Meta commands (/ prefix)
    - Pipelines (contains |)
    - Auto-resolved (no prefix)
    """

    def __init__(self,
                 tool_registry=None,
                 memory=None):
        """
        Initialize parser.

        Args:
            tool_registry: Registry of available AI tools (for auto-resolve)
            memory: Memory store (for variable substitution)
        """
        self.tool_registry = tool_registry
        self.memory = memory

        # Common shell commands for auto-resolution
        self.common_shell_commands = {
            'ls', 'cd', 'pwd', 'cat', 'echo', 'grep', 'find', 'head', 'tail',
            'git', 'docker', 'npm', 'pip', 'python', 'node', 'curl', 'wget',
            'rm', 'mv', 'cp', 'mkdir', 'touch', 'chmod', 'chown', 'ps', 'kill',
            'top', 'df', 'du', 'tar', 'zip', 'unzip', 'ssh', 'scp', 'rsync'
        }

    def parse(self, input_str: str) -> ParsedCommand:
        """
        Parse input string into structured command.

        Args:
            input_str: Raw user input

        Returns:
            ParsedCommand object

        Raises:
            ParseError: If input cannot be parsed
        """
        # Strip whitespace
        input_str = input_str.strip()

        if not input_str:
            raise ParseError("Empty input")

        # Substitute variables first
        input_str = self._substitute_variables(input_str)

        # Check for pipeline (contains | not in quotes)
        if self._contains_pipe(input_str):
            return self._parse_pipeline(input_str)

        # Check prefix
        prefix = input_str[0]

        if prefix == '!':
            # Bash command
            return self._parse_bash(input_str[1:].strip())

        elif prefix == '?':
            # Chat message
            return self._parse_chat(input_str[1:].strip())

        elif prefix == '\\':
            # AI tool
            return self._parse_tool(input_str[1:].strip())

        elif prefix == '/':
            # Meta command
            return self._parse_meta(input_str[1:].strip())

        else:
            # Auto-resolve
            return self._auto_resolve(input_str)

    def _parse_bash(self, command: str) -> ParsedCommand:
        """Parse bash command."""
        if not command:
            raise ParseError("Empty bash command")

        return ParsedCommand(
            type=CommandType.BASH,
            raw=f"!{command}",
            command=command
        )

    def _parse_chat(self, message: str) -> ParsedCommand:
        """Parse chat message."""
        if not message:
            raise ParseError("Empty chat message")

        return ParsedCommand(
            type=CommandType.CHAT,
            raw=f"?{message}",
            message=message
        )

    def _parse_tool(self, tool_str: str) -> ParsedCommand:
        """Parse AI tool command."""
        if not tool_str:
            raise ParseError("Empty tool command")

        # Split into tool name and arguments
        try:
            parts = shlex.split(tool_str)
        except ValueError as e:
            raise ParseError(f"Invalid tool syntax: {e}")

        if not parts:
            raise ParseError("Empty tool command")

        tool_name = parts[0]

        # Separate positional args from --options
        tool_args = []
        tool_options = {}

        for part in parts[1:]:
            # if part.startswith('--'):
            #     # Parse --flag or --key=value
            #     opt = part[2:]  # Remove --
            #     if '=' in opt:
            #         key, value = opt.split('=', 1)
            #         # Convert value to appropriate type
            #         if value.lower() == 'true':
            #             tool_options[key] = True
            #         elif value.lower() == 'false':
            #             tool_options[key] = False
            #         elif value.isdigit():
            #             tool_options[key] = int(value)
            #         else:
            #             tool_options[key] = value
            #     else:
            #         # Boolean flag (e.g., --verbose)
            #         tool_options[opt] = True
            # elif part.startswith('-') and len(part) == 2:
            #     # Short option like -i
            #     tool_options[part[1]] = True
            # else:
            # Positional argument
            tool_args.append(part)

        return ParsedCommand(
            type=CommandType.TOOL,
            raw=f"\\{tool_str}",
            tool_name=tool_name,
            tool_args=tool_args,
            # tool_options=tool_options
        )

    def _parse_meta(self, meta_str: str) -> ParsedCommand:
        """Parse meta command."""
        if not meta_str:
            raise ParseError("Empty meta command")

        parts = meta_str.split(maxsplit=1)
        meta_command = parts[0]
        meta_args = parts[1:] if len(parts) > 1 else []

        return ParsedCommand(
            type=CommandType.META,
            raw=f"/{meta_str}",
            meta_command=meta_command,
            meta_args=meta_args
        )

    def _parse_pipeline(self, pipeline_str: str) -> ParsedCommand:
        """Parse pipeline (contains |)."""
        # Split on | (not in quotes)
        stages_raw = self._split_pipeline(pipeline_str)

        if len(stages_raw) < 2:
            raise ParseError("Pipeline must have at least 2 stages")

        # Parse each stage
        stages = []
        for stage in stages_raw:
            stage = stage.strip()
            if not stage:
                raise ParseError("Empty pipeline stage")

            # Recursively parse each stage
            parsed_stage = self.parse(stage)
            stages.append(parsed_stage)

        return ParsedCommand(
            type=CommandType.PIPELINE,
            raw=pipeline_str,
            stages=stages
        )

    def _auto_resolve(self, input_str: str) -> ParsedCommand:
        """
        Auto-resolve command type based on context.

        Logic:
        1. Check if matches registered AI tool
        2. Check if starts with common shell command
        3. Fall back to chat
        """
        first_word = input_str.split()[0] if input_str.split() else ""

        # Check AI tools
        if self.tool_registry and first_word in self.tool_registry.list_names():
            return self._parse_tool(input_str)

        # Check common shell commands
        if first_word in self.common_shell_commands:
            return self._parse_bash(input_str)

        # Fall back to chat
        return self._parse_chat(input_str)

    def _substitute_variables(self, input_str: str) -> str:
        """
        Substitute variables like $last, $summary.

        Args:
            input_str: Input with variables

        Returns:
            Input with variables replaced
        """
        if not self.memory:
            return input_str

        # Find all $variable patterns
        pattern = r'\$(\w+)'

        def replace_var(match):
            var_name = match.group(1)
            value = self.memory.get_variable(f"${var_name}")
            if value is not None:
                return str(value)
            return match.group(0)  # Keep original if not found

        return re.sub(pattern, replace_var, input_str)

    def _contains_pipe(self, input_str: str) -> bool:
        """Check if input contains pipe (|) outside quotes."""
        in_quotes = False
        quote_char = None

        for i, char in enumerate(input_str):
            if char in ('"', "'") and (i == 0 or input_str[i-1] != '\\'):
                if not in_quotes:
                    in_quotes = True
                    quote_char = char
                elif char == quote_char:
                    in_quotes = False
                    quote_char = None

            if char == '|' and not in_quotes:
                return True

        return False

    def _split_pipeline(self, pipeline_str: str) -> List[str]:
        """
        Split pipeline on | (respecting quotes).

        Returns:
            List of pipeline stages
        """
        stages = []
        current = []
        in_quotes = False
        quote_char = None

        for i, char in enumerate(pipeline_str):
            if char in ('"', "'") and (i == 0 or pipeline_str[i-1] != '\\'):
                if not in_quotes:
                    in_quotes = True
                    quote_char = char
                elif char == quote_char:
                    in_quotes = False
                    quote_char = None

            if char == '|' and not in_quotes:
                stages.append(''.join(current))
                current = []
            else:
                current.append(char)

        # Add last stage
        if current:
            stages.append(''.join(current))

        return stages
