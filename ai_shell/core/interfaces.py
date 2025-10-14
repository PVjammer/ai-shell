"""
Abstract interfaces for ai-shell components.

These protocols define the contract between shell layer and execution layer.
Both mock and real implementations must conform to these interfaces.
"""

from typing import Protocol, AsyncIterator, List, Dict, Any, Optional, Callable
from dataclasses import dataclass


# ============================================================================
# Data Models
# ============================================================================

class CommandResult:
    """Result from command execution."""

    def __init__(self,
                 success: bool,
                 output: str = "",
                 error: str = "",
                 metadata: Dict[str, Any] = {}):
        self.success = success
        self.output = output
        self.error = error
        self.metadata = metadata or {}

    def __str__(self):
        return self.output if self.success else self.error


@dataclass
class ToolDefinition:
    """Definition of an agentic tool/command."""
    name: str
    description: str
    category: str = "general"
    requires_approval: bool = False
    parameters: Dict[str, Any] = None

    def __post_init__(self):
        if self.parameters is None:
            self.parameters = {}


# ============================================================================
# Agent Interface
# ============================================================================

class IAgent(Protocol):
    """
    Interface for AI agent.

    The agent handles chat and reasoning operations.
    """

    async def chat(self, message: str, context: Dict | None = None) -> AsyncIterator[str]:
        """
        Chat with the agent, streaming response tokens.

        Args:
            message: User message
            context: Optional context (history, variables, etc.)

        Yields:
            Response tokens
        """
        ...

    async def generate(self, prompt: str, context: Dict = None) -> str:
        """
        Generate a complete response (non-streaming).

        Args:
            prompt: Prompt text
            context: Optional context

        Returns:
            Complete response
        """
        ...


# ============================================================================
# Command Executor Interface
# ============================================================================

class ICommandExecutor(Protocol):
    """
    Interface for executing agentic commands (tools).

    Commands are registered with the executor and can be invoked
    with positional args and keyword options (like bash commands).

    Examples:
        \\summarize file.txt --max-length=500
        \\search "query" --engine=google
        \\analyze code.py --style --security
    """

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
        """
        ...

    def has_command(self, name: str) -> bool:
        """Check if command is registered."""
        ...

    def get_command_names(self) -> List[str]:
        """Get list of all registered command names (for tab completion)."""
        ...

    def get_command_info(self, name: str) -> Optional[ToolDefinition]:
        """Get command metadata by name."""
        ...

    async def execute(self,
                     command_name: str,
                     args: List[str] = None,
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
        ...

    async def execute_streaming(self,
                               command_name: str,
                               args: List[str] = None,
                               stdin: Optional[str] = None,
                               **options) -> AsyncIterator[str]:
        """
        Execute command with streaming output.

        Args:
            command_name: Name of command
            args: Positional arguments
            stdin: Optional stdin from pipeline
            **options: Keyword arguments from --flags

        Yields:
            Output chunks
        """
        ...


# ============================================================================
# Bash Executor Interface
# ============================================================================

class IBashExecutor(Protocol):
    """
    Interface for bash command execution.
    """

    async def execute(self,
                     command: str,
                     input_data: Optional[bytes] = None,
                     timeout: int = 30) -> CommandResult:
        """
        Execute bash command.

        Args:
            command: Shell command to execute
            input_data: Optional stdin input
            timeout: Timeout in seconds

        Returns:
            CommandResult
        """
        ...

    async def execute_streaming(self,
                               command: str,
                               input_data: Optional[bytes] = None) -> AsyncIterator[bytes]:
        """
        Execute bash command with streaming output.

        Args:
            command: Shell command
            input_data: Optional stdin

        Yields:
            Output chunks (bytes)
        """
        ...
