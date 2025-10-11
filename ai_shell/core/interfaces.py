"""
Abstract interfaces for ai-shell components.

These protocols define the contract between shell layer and execution layer.
Both mock and real implementations must conform to these interfaces.
"""

from typing import Protocol, AsyncIterator, List, Dict, Any, Optional
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
                 metadata: Dict[str, Any] = None):
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

    async def chat(self, message: str, context: Dict = None) -> AsyncIterator[str]:
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

    Examples: \\summarize, \\search, \\analyze
    """

    async def execute(self,
                     command_name: str,
                     args: List[str],
                     input_data: Optional[str] = None,
                     context: Dict = None) -> CommandResult:
        """
        Execute an agentic command.

        Args:
            command_name: Name of command (e.g., "summarize")
            args: Command arguments
            input_data: Optional input from pipeline
            context: Execution context

        Returns:
            CommandResult
        """
        ...

    async def execute_streaming(self,
                               command_name: str,
                               args: List[str],
                               input_data: Optional[str] = None,
                               context: Dict = None) -> AsyncIterator[str]:
        """
        Execute command with streaming output.

        Args:
            command_name: Name of command
            args: Command arguments
            input_data: Optional input from pipeline
            context: Execution context

        Yields:
            Output chunks
        """
        ...


# ============================================================================
# Tool Registry Interface
# ============================================================================

class IToolRegistry(Protocol):
    """
    Interface for tool/command registry.

    Manages available agentic commands and their metadata.
    """

    def register(self, tool: ToolDefinition) -> None:
        """Register a tool."""
        ...

    def unregister(self, name: str) -> None:
        """Unregister a tool."""
        ...

    def get(self, name: str) -> Optional[ToolDefinition]:
        """Get tool definition by name."""
        ...

    def list(self, category: str = None) -> List[ToolDefinition]:
        """List all registered tools, optionally filtered by category."""
        ...

    def list_names(self) -> List[str]:
        """Get list of tool names (for completion)."""
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
