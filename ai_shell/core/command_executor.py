"""
Real command executor implementation.

Manages registration and execution of agentic commands.
"""

from typing import Dict, List, Optional, Callable, AsyncIterator
import inspect
from ai_shell.core.interfaces import CommandResult, ToolDefinition


class CommandExecutor:
    """
    Command executor with integrated registry.

    Manages command registration and executes commands with
    bash-like argument handling (positional args + options).
    """

    def __init__(self):
        """Initialize command executor."""
        self.commands: Dict[str, Callable] = {}
        self.command_info: Dict[str, ToolDefinition] = {}
        self.context_session = {"user_context": []}

    def register_command(self,
                        name: str,
                        handler: Callable,
                        description: str = "",
                        category: str = "general") -> None:
        """
        Register a command with the executor.

        Args:
            name: Command name (e.g., "summarize")
            handler: Async callable that executes the command
            description: Human-readable description
            category: Command category for organization

        Example:
            async def summarize_cmd(args, stdin=None, **options):
                # Implementation
                return "Summary..."

            executor.register_command("summarize", summarize_cmd,
                                     "Summarize text or files")
        """
        # Validate handler is callable
        if not callable(handler):
            raise TypeError(f"Handler must be callable, got {type(handler)}")

        # Validate handler is async
        if not inspect.iscoroutinefunction(handler):
            raise TypeError(f"Handler must be async function (use 'async def')")

        self.commands[name] = handler
        self.command_info[name] = ToolDefinition(
            name=name,
            description=description,
            category=category
        )

    def has_command(self, name: str) -> bool:
        """Check if command is registered."""
        return name in self.commands

    def get_command_names(self) -> List[str]:
        """Get list of all registered command names (for tab completion)."""
        return list(self.commands.keys())

    def get_command_info(self, name: str) -> Optional[ToolDefinition]:
        """Get command metadata by name."""
        return self.command_info.get(name)

    def get_all_commands_info(self) -> Dict[str, ToolDefinition]:
        """Get metadata for all registered commands."""
        return self.command_info.copy()

    def get_help(self, command_name: Optional[str] = None) -> str:
        """
        Get help text for a command or all commands.

        Args:
            command_name: Optional specific command name. If None, returns help for all commands.

        Returns:
            Formatted help text in markdown
        """
        if command_name:
            # Get help for specific command
            if command_name not in self.command_info:
                return f"Unknown command: {command_name}"

            info = self.command_info[command_name]
            help_text = f"# {info.name}\n\n"
            if info.description:
                help_text += f"{info.description}\n\n"

            # Get function signature if available
            if command_name in self.commands:
                handler = self.commands[command_name]
                sig = inspect.signature(handler)
                help_text += f"**Signature:** `{command_name}{sig}`\n\n"

                # Extract docstring
                if handler.__doc__:
                    help_text += f"**Details:**\n```\n{handler.__doc__.strip()}\n```\n"

            help_text += f"\n**Category:** {info.category}\n"
            return help_text
        else:
            # Get help for all commands grouped by category
            categories: Dict[str, List[ToolDefinition]] = {}
            for info in self.command_info.values():
                if info.category not in categories:
                    categories[info.category] = []
                categories[info.category].append(info)

            if not categories:
                return "No commands registered yet."

            help_text = "# Available Commands\n\n"
            for category in sorted(categories.keys()):
                help_text += f"## {category.capitalize()}\n\n"
                for info in sorted(categories[category], key=lambda x: x.name):
                    help_text += f"- **{info.name}**: {info.description or 'No description'}\n"
                help_text += "\n"

            help_text += "\nUse `\\help <command>` for detailed help on a specific command.\n"
            return help_text

    def get_context_session(self):
        return self.context_session
    
    def set_context(self, ctx: dict):
        self.context_session = ctx

    def add_context(self, ctx: str | dict, key: str = "user_context"):
        if key not in self.context_session:
            self.context_session[key] = []
        self.context_session[key].append(ctx)

    def clear_context(self, key: str | None = None):
        if not key:
            self.context_session = {"user_context": []}
            return
        if key not in self.context_session:
            raise ValueError(f"No context found for key: {key}")
        self.context_session[key] = []

    async def execute(self,
                     command_name: str,
                     args: List[str] | None= None,
                     stdin: Optional[str] = None,
                     **options) -> CommandResult:
        """
        Execute a command with bash-like argument parsing.

        Args:
            command_name: Name of command (e.g., "summarize")
            args: Positional arguments (like bash: file1 file2)
            stdin: Optional stdin input from pipeline
            **options: Keyword arguments parsed from --flags

        Returns:
            CommandResult

        Example:
            # User types: \\summarize file.txt --max-length=500
            # Calls: execute("summarize", ["file.txt"], max_length=500)
        """
        if not self.has_command(command_name):
            return CommandResult(
                success=False,
                output="",
                error=f"Unknown command: {command_name}"
            )

        handler = self.commands[command_name]
        args = args or []

        try:
            # Call handler with args, stdin, and options
            result = await handler(args, stdin=stdin, **options)

            # If handler returns a string, wrap in CommandResult
            if isinstance(result, str):
                return CommandResult(success=True, output=result, error="")

            # If handler returns CommandResult, use it directly
            if isinstance(result, CommandResult):
                return result

            # Otherwise, convert to string
            return CommandResult(
                success=True,
                output=str(result),
                error=""
            )

        except Exception as e:
            return CommandResult(
                success=False,
                output="",
                error=f"Command '{command_name}' failed: {e}"
            )

    async def execute_streaming(self,
                               command_name: str,
                               args: List[str] | None = None,
                               stdin: Optional[str] = None,
                               **options) -> AsyncIterator[str]:
        """
        Execute command with streaming output.

        If command doesn't support streaming, falls back to
        execute() and yields the complete result.

        Args:
            command_name: Name of command
            args: Positional arguments
            stdin: Optional stdin from pipeline
            **options: Keyword arguments from --flags

        Yields:
            Output chunks
        """
        if not self.has_command(command_name):
            yield f"[Error: Unknown command: {command_name}]"
            return

        handler = self.commands[command_name]
        args = args or []

        try:
            # Check if handler is an async generator (supports streaming)
            result = await handler(args, stdin=stdin, **options)

            if inspect.isasyncgen(result):
                # Handler returns async generator - stream it
                async for chunk in result:
                    yield str(chunk)
            else:
                # Handler returns complete result - yield it
                if isinstance(result, str):
                    yield result
                elif isinstance(result, CommandResult):
                    if result.success:
                        yield result.output
                    else:
                        yield f"[Error: {result.error}]"
                else:
                    yield str(result)

        except Exception as e:
            yield f"[Error: Command '{command_name}' failed: {e}]"
