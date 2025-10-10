# Mock & Plugin System Plan

## Overview

This document describes the **mock system** and **plugin/registration architecture** for ai-shell. This enables:

1. **Shell development** to proceed independently of agent/command implementation
2. **Clear interfaces** between shell and agent/commands
3. **Easy plugin system** for registering new agentic commands

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    REPL (Shell Layer)                    │
└────────────────────┬────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────┐
│              Abstract Interfaces (Protocols)             │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐ │
│  │   IAgent    │  │ ICommandExec │  │ IToolRegistry  │ │
│  └─────────────┘  └──────────────┘  └────────────────┘ │
└──────────┬────────────────┬────────────────┬───────────┘
           │                │                │
           ↓                ↓                ↓
    ┌──────────┐     ┌──────────┐    ┌──────────┐
    │MockAgent │     │MockExec  │    │MockTools │  (Dev/Test)
    └──────────┘     └──────────┘    └──────────┘
           │                │                │
           ↓                ↓                ↓
    ┌──────────┐     ┌──────────┐    ┌──────────┐
    │RealAgent │     │RealExec  │    │RealTools │  (Production)
    └──────────┘     └──────────┘    └──────────┘
```

---

## Part 1: Abstract Interfaces

Define clear protocols that both mock and real implementations must follow.

### File: `ai_shell/core/interfaces.py`

```python
"""
Abstract interfaces for ai-shell components.

These protocols define the contract between shell layer and execution layer.
Both mock and real implementations must conform to these interfaces.
"""

from typing import Protocol, AsyncIterator, List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

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

    Examples: \summarize, \search, \analyze
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
```

---

## Part 2: Mock Implementations

Mock implementations for testing and shell development.

### File: `ai_shell/mocks/__init__.py`

```python
"""Mock implementations for testing and development."""

from .agent import MockAgent
from .executor import MockCommandExecutor
from .registry import MockToolRegistry
from .bash import MockBashExecutor

__all__ = [
    'MockAgent',
    'MockCommandExecutor',
    'MockToolRegistry',
    'MockBashExecutor',
]
```

### File: `ai_shell/mocks/agent.py`

```python
"""Mock agent for testing."""

import asyncio
from typing import AsyncIterator, Dict

class MockAgent:
    """
    Mock AI agent that returns canned responses.

    Useful for testing shell layer without real LLM.
    """

    def __init__(self, delay: float = 0.05):
        """
        Initialize mock agent.

        Args:
            delay: Delay between tokens (simulates streaming)
        """
        self.delay = delay
        self.responses = {
            "default": "This is a mock response from the AI agent.",
            "hello": "Hello! I'm a mock AI agent. I'm not real, but I can help test the shell!",
            "summarize": "Here's a mock summary: The content discusses various topics in a structured way.",
        }

    async def chat(self, message: str, context: Dict = None) -> AsyncIterator[str]:
        """Stream mock chat response."""
        # Choose response based on message content
        response = self._get_response(message)

        # Stream token by token
        for token in response.split():
            await asyncio.sleep(self.delay)
            yield token + " "

    async def generate(self, prompt: str, context: Dict = None) -> str:
        """Generate complete mock response."""
        return self._get_response(prompt)

    def _get_response(self, message: str) -> str:
        """Select appropriate canned response."""
        message_lower = message.lower()

        if "hello" in message_lower or "hi" in message_lower:
            return self.responses["hello"]
        elif "summarize" in message_lower:
            return self.responses["summarize"]
        else:
            return self.responses["default"]

    def add_response(self, trigger: str, response: str):
        """Add custom response for testing."""
        self.responses[trigger] = response
```

### File: `ai_shell/mocks/executor.py`

```python
"""Mock command executor for testing."""

import asyncio
from typing import AsyncIterator, List, Optional, Dict
from ai_shell.core.interfaces import CommandResult

class MockCommandExecutor:
    """
    Mock executor for agentic commands.

    Returns mock responses for commands like summarize, search, etc.
    """

    def __init__(self, delay: float = 0.05):
        """
        Initialize mock executor.

        Args:
            delay: Delay for streaming simulation
        """
        self.delay = delay

        # Canned responses for different commands
        self.command_responses = {
            "summarize": self._mock_summarize,
            "search": self._mock_search,
            "analyze": self._mock_analyze,
            "report": self._mock_report,
            "explain": self._mock_explain,
        }

    async def execute(self,
                     command_name: str,
                     args: List[str],
                     input_data: Optional[str] = None,
                     context: Dict = None) -> CommandResult:
        """Execute command and return complete result."""

        if command_name not in self.command_responses:
            return CommandResult(
                success=False,
                error=f"Unknown command: {command_name}"
            )

        try:
            handler = self.command_responses[command_name]
            output = await handler(args, input_data, context)

            return CommandResult(
                success=True,
                output=output,
                metadata={"mock": True, "command": command_name}
            )

        except Exception as e:
            return CommandResult(
                success=False,
                error=f"Mock execution error: {e}"
            )

    async def execute_streaming(self,
                               command_name: str,
                               args: List[str],
                               input_data: Optional[str] = None,
                               context: Dict = None) -> AsyncIterator[str]:
        """Execute command with streaming output."""

        # Get complete output
        result = await self.execute(command_name, args, input_data, context)

        if not result.success:
            yield f"Error: {result.error}"
            return

        # Stream word by word
        for word in result.output.split():
            await asyncio.sleep(self.delay)
            yield word + " "

    # Mock command implementations

    async def _mock_summarize(self,
                              args: List[str],
                              input_data: Optional[str],
                              context: Dict) -> str:
        """Mock summarize command."""
        if input_data:
            word_count = len(input_data.split())
            return f"**Summary** (mock):\n\nProcessed {word_count} words. Key points:\n- Point 1\n- Point 2\n- Point 3"
        else:
            return "**Summary** (mock): Please provide input to summarize."

    async def _mock_search(self,
                          args: List[str],
                          input_data: Optional[str],
                          context: Dict) -> str:
        """Mock search command."""
        query = " ".join(args) if args else "unknown"
        return f"**Search Results** (mock) for '{query}':\n\n1. Result 1\n2. Result 2\n3. Result 3"

    async def _mock_analyze(self,
                           args: List[str],
                           input_data: Optional[str],
                           context: Dict) -> str:
        """Mock analyze command."""
        return "**Analysis** (mock):\n\n- Patterns detected: 3\n- Anomalies: 1\n- Confidence: 85%"

    async def _mock_report(self,
                          args: List[str],
                          input_data: Optional[str],
                          context: Dict) -> str:
        """Mock report command."""
        return "# Mock Report\n\n## Overview\n\nThis is a mock report generated for testing.\n\n## Details\n\n- Item 1\n- Item 2"

    async def _mock_explain(self,
                           args: List[str],
                           input_data: Optional[str],
                           context: Dict) -> str:
        """Mock explain command."""
        return "**Explanation** (mock):\n\nThis mock explanation provides context about the input. In a real implementation, this would analyze and explain the content."
```

### File: `ai_shell/mocks/registry.py`

```python
"""Mock tool registry for testing."""

from typing import List, Optional, Dict
from ai_shell.core.interfaces import ToolDefinition

class MockToolRegistry:
    """
    Mock tool registry with pre-defined tools.

    Provides a set of mock tools for testing the shell.
    """

    def __init__(self):
        """Initialize with mock tools."""
        self._tools: Dict[str, ToolDefinition] = {}

        # Register default mock tools
        self._register_defaults()

    def _register_defaults(self):
        """Register default mock tools."""
        default_tools = [
            ToolDefinition(
                name="summarize",
                description="Summarize text into key points",
                category="text",
                requires_approval=False
            ),
            ToolDefinition(
                name="search",
                description="Search for information",
                category="information",
                requires_approval=False
            ),
            ToolDefinition(
                name="analyze",
                description="Analyze data and find patterns",
                category="analysis",
                requires_approval=False
            ),
            ToolDefinition(
                name="report",
                description="Generate formatted report",
                category="output",
                requires_approval=False
            ),
            ToolDefinition(
                name="explain",
                description="Explain code or commands",
                category="text",
                requires_approval=False
            ),
        ]

        for tool in default_tools:
            self.register(tool)

    def register(self, tool: ToolDefinition) -> None:
        """Register a tool."""
        self._tools[tool.name] = tool

    def unregister(self, name: str) -> None:
        """Unregister a tool."""
        if name in self._tools:
            del self._tools[name]

    def get(self, name: str) -> Optional[ToolDefinition]:
        """Get tool by name."""
        return self._tools.get(name)

    def list(self, category: str = None) -> List[ToolDefinition]:
        """List tools, optionally filtered by category."""
        tools = list(self._tools.values())

        if category:
            tools = [t for t in tools if t.category == category]

        return tools

    def list_names(self) -> List[str]:
        """Get list of tool names."""
        return list(self._tools.keys())
```

### File: `ai_shell/mocks/bash.py`

```python
"""Mock bash executor for testing."""

import asyncio
from typing import AsyncIterator, Optional
from ai_shell.core.interfaces import CommandResult

class MockBashExecutor:
    """
    Mock bash executor for testing.

    Returns mock output for common commands.
    """

    def __init__(self, delay: float = 0.05):
        """
        Initialize mock bash executor.

        Args:
            delay: Delay for streaming simulation
        """
        self.delay = delay

        # Mock outputs for common commands
        self.mock_outputs = {
            "ls": "file1.txt\nfile2.py\nREADME.md\n",
            "pwd": "/home/user/ai-shell\n",
            "echo": None,  # Will echo the arguments
            "cat": None,   # Will return mock file content
        }

    async def execute(self,
                     command: str,
                     input_data: Optional[bytes] = None,
                     timeout: int = 30) -> CommandResult:
        """Execute mock bash command."""

        # Parse command
        parts = command.split()
        if not parts:
            return CommandResult(
                success=False,
                error="Empty command"
            )

        cmd = parts[0]

        # Handle specific commands
        if cmd in self.mock_outputs:
            if cmd == "echo":
                output = " ".join(parts[1:]) + "\n"
            elif cmd == "cat":
                output = f"Mock content of {parts[1] if len(parts) > 1 else 'file'}\n"
            else:
                output = self.mock_outputs[cmd]

            return CommandResult(
                success=True,
                output=output,
                metadata={"mock": True, "command": command}
            )

        # Default mock output
        return CommandResult(
            success=True,
            output=f"Mock output for: {command}\n",
            metadata={"mock": True, "command": command}
        )

    async def execute_streaming(self,
                               command: str,
                               input_data: Optional[bytes] = None) -> AsyncIterator[bytes]:
        """Execute command with streaming output."""

        result = await self.execute(command, input_data)

        if not result.success:
            yield result.error.encode()
            return

        # Stream byte by byte (simulating real process output)
        for char in result.output:
            await asyncio.sleep(self.delay / 10)  # Faster than word streaming
            yield char.encode()
```

---

## Part 3: Plugin/Registration System

A flexible system for registering real agentic commands when ready.

### File: `ai_shell/core/registry.py`

```python
"""
Tool/Command registry with plugin support.

This registry manages both built-in and user-defined tools.
"""

from typing import List, Optional, Dict, Callable, Any
from dataclasses import dataclass, field
import inspect
import importlib
import os
from pathlib import Path

from ai_shell.core.interfaces import ToolDefinition, IToolRegistry, CommandResult


@dataclass
class RegisteredTool:
    """A registered tool with its handler function."""
    definition: ToolDefinition
    handler: Callable
    metadata: Dict[str, Any] = field(default_factory=dict)


class ToolRegistry(IToolRegistry):
    """
    Central registry for agentic tools/commands.

    Supports:
    - Programmatic registration
    - Decorator-based registration
    - Plugin discovery from directories
    - Hot-reloading (optional)
    """

    def __init__(self):
        """Initialize empty registry."""
        self._tools: Dict[str, RegisteredTool] = {}

    # ========================================================================
    # Basic Registration (IToolRegistry interface)
    # ========================================================================

    def register(self, tool: ToolDefinition, handler: Callable = None) -> None:
        """
        Register a tool.

        Args:
            tool: Tool definition
            handler: Optional handler function
        """
        registered = RegisteredTool(
            definition=tool,
            handler=handler,
            metadata={}
        )
        self._tools[tool.name] = registered

    def unregister(self, name: str) -> None:
        """Unregister a tool."""
        if name in self._tools:
            del self._tools[name]

    def get(self, name: str) -> Optional[ToolDefinition]:
        """Get tool definition by name."""
        registered = self._tools.get(name)
        return registered.definition if registered else None

    def list(self, category: str = None) -> List[ToolDefinition]:
        """List all tools, optionally filtered by category."""
        tools = [t.definition for t in self._tools.values()]

        if category:
            tools = [t for t in tools if t.category == category]

        return tools

    def list_names(self) -> List[str]:
        """Get list of tool names."""
        return list(self._tools.keys())

    # ========================================================================
    # Extended Registration Methods
    # ========================================================================

    def register_function(self,
                         func: Callable,
                         name: str = None,
                         description: str = None,
                         category: str = "general",
                         requires_approval: bool = False) -> None:
        """
        Register a function as a tool.

        Args:
            func: Function to register
            name: Tool name (defaults to function name)
            description: Tool description (defaults to docstring)
            category: Tool category
            requires_approval: Whether tool requires user approval
        """
        tool_name = name or func.__name__
        tool_description = description or func.__doc__ or f"Tool: {tool_name}"

        # Extract parameters from function signature
        parameters = self._extract_parameters(func)

        definition = ToolDefinition(
            name=tool_name,
            description=tool_description,
            category=category,
            requires_approval=requires_approval,
            parameters=parameters
        )

        self.register(definition, handler=func)

    def register_decorator(self,
                          name: str = None,
                          description: str = None,
                          category: str = "general",
                          requires_approval: bool = False):
        """
        Decorator for registering functions as tools.

        Usage:
            @registry.register_decorator(category="text")
            async def summarize(text: str, max_length: int = 100) -> str:
                ...
        """
        def decorator(func: Callable):
            self.register_function(
                func,
                name=name,
                description=description,
                category=category,
                requires_approval=requires_approval
            )
            return func

        return decorator

    def get_handler(self, name: str) -> Optional[Callable]:
        """Get handler function for a tool."""
        registered = self._tools.get(name)
        return registered.handler if registered else None

    # ========================================================================
    # Plugin Discovery
    # ========================================================================

    def discover_plugins(self, plugin_dir: str) -> int:
        """
        Discover and load plugins from a directory.

        Plugin structure:
            plugin_dir/
                my_tool.py
                    def tool_name(...):  # Function name = tool name
                        '''Tool description'''
                        ...

        Args:
            plugin_dir: Directory to search for plugins

        Returns:
            Number of tools loaded
        """
        plugin_path = Path(plugin_dir).expanduser()

        if not plugin_path.exists():
            return 0

        count = 0

        # Find all .py files
        for py_file in plugin_path.glob("*.py"):
            if py_file.name.startswith("_"):
                continue  # Skip private modules

            try:
                # Import module
                module_name = py_file.stem
                spec = importlib.util.spec_from_file_location(module_name, py_file)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                # Find tool functions (look for functions with metadata)
                for name, obj in inspect.getmembers(module, inspect.isfunction):
                    if hasattr(obj, "_ai_shell_tool"):
                        # Function decorated with @tool
                        metadata = obj._ai_shell_tool
                        self.register_function(
                            obj,
                            name=metadata.get("name", name),
                            description=metadata.get("description"),
                            category=metadata.get("category", "plugin"),
                            requires_approval=metadata.get("requires_approval", False)
                        )
                        count += 1

            except Exception as e:
                print(f"Warning: Failed to load plugin {py_file}: {e}")

        return count

    # ========================================================================
    # Utility Methods
    # ========================================================================

    def _extract_parameters(self, func: Callable) -> Dict[str, Any]:
        """
        Extract parameter schema from function signature.

        Returns JSON Schema compatible dict.
        """
        sig = inspect.signature(func)
        parameters = {
            "type": "object",
            "properties": {},
            "required": []
        }

        for param_name, param in sig.parameters.items():
            if param_name in ("self", "cls"):
                continue

            # Basic type extraction
            param_type = "string"  # Default
            if param.annotation != inspect.Parameter.empty:
                if param.annotation == int:
                    param_type = "integer"
                elif param.annotation == float:
                    param_type = "number"
                elif param.annotation == bool:
                    param_type = "boolean"

            parameters["properties"][param_name] = {
                "type": param_type,
                "description": f"Parameter: {param_name}"
            }

            # Required if no default value
            if param.default == inspect.Parameter.empty:
                parameters["required"].append(param_name)

        return parameters

    def clear(self) -> None:
        """Clear all registered tools."""
        self._tools.clear()


# ========================================================================
# Decorator for Plugin Authors
# ========================================================================

def tool(name: str = None,
         description: str = None,
         category: str = "general",
         requires_approval: bool = False):
    """
    Decorator to mark a function as an ai-shell tool.

    Usage in plugin file:
        @tool(category="text", description="Summarize text")
        async def summarize(text: str, max_length: int = 100) -> str:
            ...

    Args:
        name: Tool name (defaults to function name)
        description: Tool description (defaults to docstring)
        category: Tool category
        requires_approval: Whether tool requires approval
    """
    def decorator(func: Callable):
        func._ai_shell_tool = {
            "name": name,
            "description": description,
            "category": category,
            "requires_approval": requires_approval
        }
        return func

    return decorator
```

---

## Part 4: Command Executor with Registry Integration

Connects the registry to actual command execution.

### File: `ai_shell/core/executor.py`

```python
"""
Command executor that uses the tool registry.

This bridges the shell layer and registered tools.
"""

from typing import AsyncIterator, List, Optional, Dict
import inspect

from ai_shell.core.interfaces import ICommandExecutor, CommandResult
from ai_shell.core.registry import ToolRegistry


class CommandExecutor(ICommandExecutor):
    """
    Executes agentic commands using registered tools.

    Looks up tools in the registry and invokes their handlers.
    """

    def __init__(self, registry: ToolRegistry, agent = None):
        """
        Initialize executor.

        Args:
            registry: Tool registry
            agent: Optional AI agent (for tools that need LLM)
        """
        self.registry = registry
        self.agent = agent

    async def execute(self,
                     command_name: str,
                     args: List[str],
                     input_data: Optional[str] = None,
                     context: Dict = None) -> CommandResult:
        """
        Execute a registered command.

        Args:
            command_name: Name of tool to execute
            args: Command arguments
            input_data: Optional input from pipeline
            context: Execution context

        Returns:
            CommandResult
        """
        # Get tool handler
        handler = self.registry.get_handler(command_name)

        if not handler:
            return CommandResult(
                success=False,
                error=f"Unknown command: {command_name}"
            )

        try:
            # Parse arguments (simple version - can be enhanced)
            kwargs = self._parse_args(handler, args, input_data)

            # Execute handler
            if inspect.iscoroutinefunction(handler):
                result = await handler(**kwargs)
            else:
                result = handler(**kwargs)

            return CommandResult(
                success=True,
                output=str(result),
                metadata={"command": command_name}
            )

        except Exception as e:
            return CommandResult(
                success=False,
                error=f"Execution error: {e}",
                metadata={"command": command_name, "exception": str(e)}
            )

    async def execute_streaming(self,
                               command_name: str,
                               args: List[str],
                               input_data: Optional[str] = None,
                               context: Dict = None) -> AsyncIterator[str]:
        """
        Execute command with streaming.

        If handler returns AsyncIterator, stream it.
        Otherwise, execute normally and yield result.
        """
        handler = self.registry.get_handler(command_name)

        if not handler:
            yield f"Error: Unknown command: {command_name}"
            return

        try:
            kwargs = self._parse_args(handler, args, input_data)

            # Execute handler
            if inspect.iscoroutinefunction(handler):
                result = await handler(**kwargs)
            else:
                result = handler(**kwargs)

            # Check if result is async iterator (streaming)
            if inspect.isasyncgen(result):
                async for chunk in result:
                    yield str(chunk)
            else:
                # Non-streaming result
                yield str(result)

        except Exception as e:
            yield f"Error: {e}"

    def _parse_args(self,
                   handler: Callable,
                   args: List[str],
                   input_data: Optional[str]) -> Dict[str, any]:
        """
        Parse command-line arguments into function kwargs.

        Simple implementation - can be enhanced with argparse.
        """
        kwargs = {}

        # Get function signature
        sig = inspect.signature(handler)
        params = list(sig.parameters.items())

        # First positional parameter gets input_data if available
        if input_data and params:
            first_param = params[0][0]
            kwargs[first_param] = input_data
            params = params[1:]  # Remove first param

        # Parse remaining args as positional
        for i, (param_name, param) in enumerate(params):
            if i < len(args):
                # Convert to appropriate type
                value = args[i]

                # Simple type conversion
                if param.annotation != inspect.Parameter.empty:
                    if param.annotation == int:
                        value = int(value)
                    elif param.annotation == float:
                        value = float(value)
                    elif param.annotation == bool:
                        value = value.lower() in ("true", "1", "yes")

                kwargs[param_name] = value

        return kwargs
```

---

## Part 5: Integration with Shell

Update shell components to use interfaces and support mocking.

### Updated: `ai_shell/shell/repl.py` (key changes)

```python
class REPL:
    """REPL with pluggable backends."""

    def __init__(self,
                 parser: Parser,
                 renderer: Renderer,
                 memory: MemoryStore,
                 agent: IAgent = None,              # Interface, not concrete class
                 executor: ICommandExecutor = None,  # Interface
                 bash_executor: IBashExecutor = None, # Interface
                 registry: IToolRegistry = None,    # Interface
                 config: REPLConfig = None):

        self.parser = parser
        self.renderer = renderer
        self.memory = memory
        self.config = config or REPLConfig()

        # Use provided implementations or fall back to mocks
        self.agent = agent or self._create_mock_agent()
        self.executor = executor or self._create_mock_executor()
        self.bash_executor = bash_executor or self._create_mock_bash()
        self.registry = registry or self._create_mock_registry()

        # Update parser with registry
        self.parser.tool_registry = self.registry

        # ... rest of initialization

    def _create_mock_agent(self):
        """Create mock agent for testing."""
        from ai_shell.mocks import MockAgent
        return MockAgent()

    def _create_mock_executor(self):
        """Create mock executor for testing."""
        from ai_shell.mocks import MockCommandExecutor
        return MockCommandExecutor()

    def _create_mock_bash(self):
        """Create mock bash executor."""
        from ai_shell.mocks import MockBashExecutor
        return MockBashExecutor()

    def _create_mock_registry(self):
        """Create mock registry."""
        from ai_shell.mocks import MockToolRegistry
        return MockToolRegistry()

    async def _handle_chat(self, command):
        """Handle chat using agent interface."""
        self.state = SessionState.EXECUTING

        try:
            # Stream response from agent
            async for token in self.agent.chat(command.message):
                self.renderer.console.print(token, end="")

            self.renderer.console.print()  # Final newline
            self.state = SessionState.READY

        except Exception as e:
            self.renderer.print_error(f"Chat error: {e}")
            self.state = SessionState.ERROR

    async def _handle_tool(self, command):
        """Handle tool command using executor interface."""
        self.state = SessionState.EXECUTING

        try:
            result = await self.executor.execute(
                command.tool_name,
                command.tool_args,
                context={"memory": self.memory}
            )

            if result.success:
                self.renderer.render(result.output)
                self.memory.set_variable("$last", result.output)
            else:
                self.renderer.print_error(result.error)

            self.state = SessionState.READY

        except Exception as e:
            self.renderer.print_error(f"Tool execution error: {e}")
            self.state = SessionState.ERROR

    async def _handle_bash(self, command):
        """Handle bash using bash executor interface."""
        self.state = SessionState.EXECUTING

        try:
            result = await self.bash_executor.execute(command.command)

            if result.success:
                self.renderer.print_info(result.output)
                self.memory.set_variable("$last", result.output)
            else:
                self.renderer.print_error(result.error)

            self.state = SessionState.READY

        except Exception as e:
            self.renderer.print_error(f"Bash error: {e}")
            self.state = SessionState.ERROR
```

---

## Part 6: Usage Examples

### Example 1: Using Mocks for Shell Development

```python
# shell_dev.py - Shell development with mocks

from ai_shell.shell.repl import REPL, REPLConfig
from ai_shell.shell.parser import Parser
from ai_shell.shell.renderer import Renderer
from ai_shell.core.memory import MemoryStore

# Mocks are created automatically by REPL
async def main():
    parser = Parser()
    renderer = Renderer()
    memory = MemoryStore()

    config = REPLConfig(debug_mode=True)
    repl = REPL(parser, renderer, memory, config)

    # All backends are mocked - shell works standalone!
    await repl.start()

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
```

### Example 2: Registering a Real Tool

```python
# tools/my_summarizer.py - Real tool implementation

from ai_shell.core.registry import tool

@tool(
    name="summarize",
    description="Summarize text intelligently",
    category="text"
)
async def summarize(text: str, max_length: int = 100) -> str:
    """
    Real summarization using LLM.

    Args:
        text: Text to summarize
        max_length: Maximum length

    Returns:
        Summary
    """
    # Real implementation
    from my_llm import get_llm

    llm = get_llm()
    prompt = f"Summarize the following in {max_length} words:\n\n{text}"
    summary = await llm.generate(prompt)

    return summary
```

### Example 3: Loading Real Tools into Shell

```python
# main.py - Production shell with real tools

from ai_shell.shell.repl import REPL
from ai_shell.shell.parser import Parser
from ai_shell.shell.renderer import Renderer
from ai_shell.core.memory import MemoryStore
from ai_shell.core.registry import ToolRegistry
from ai_shell.core.executor import CommandExecutor
from my_agent import MyRealAgent  # Your agent implementation

async def main():
    # Setup
    parser = Parser()
    renderer = Renderer()
    memory = MemoryStore()

    # Real components
    agent = MyRealAgent()

    registry = ToolRegistry()
    registry.discover_plugins("~/.ai_shell/tools")  # Load user tools

    executor = CommandExecutor(registry, agent)

    # Create REPL with real backends
    repl = REPL(
        parser=parser,
        renderer=renderer,
        memory=memory,
        agent=agent,
        executor=executor,
        registry=registry
    )

    await repl.start()

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
```

### Example 4: Mixed Mode (Some Mock, Some Real)

```python
# test_with_real_bash.py - Test shell with real bash but mock AI

from ai_shell.shell.repl import REPL
from ai_shell.mocks import MockAgent, MockCommandExecutor, MockToolRegistry
from ai_shell.core.bash_executor import RealBashExecutor  # Real bash
# ... other imports

async def main():
    # ... setup

    # Use real bash executor but mock everything else
    repl = REPL(
        parser=parser,
        renderer=renderer,
        memory=memory,
        agent=MockAgent(),           # Mock
        executor=MockCommandExecutor(), # Mock
        bash_executor=RealBashExecutor(), # Real!
        registry=MockToolRegistry()  # Mock
    )

    await repl.start()
```

---

## Part 7: Testing Strategy

### Testing with Mocks

```python
# tests/test_shell_with_mocks.py

import pytest
from ai_shell.shell.repl import REPL
from ai_shell.mocks import MockAgent, MockCommandExecutor, MockToolRegistry
# ... other imports

@pytest.fixture
def repl_with_mocks(parser, renderer, memory):
    """REPL with all mocks."""
    return REPL(
        parser=parser,
        renderer=renderer,
        memory=memory,
        agent=MockAgent(),
        executor=MockCommandExecutor(),
        registry=MockToolRegistry()
    )

@pytest.mark.asyncio
async def test_chat_with_mock_agent(repl_with_mocks):
    """Test chat command uses mock agent."""
    command = repl_with_mocks.parser.parse("?hello")

    # Should use mock agent
    await repl_with_mocks._handle_chat(command)

    # Check output was rendered (captured in test renderer)
    # ...

@pytest.mark.asyncio
async def test_tool_with_mock_executor(repl_with_mocks):
    """Test tool command uses mock executor."""
    command = repl_with_mocks.parser.parse("\\summarize test")

    await repl_with_mocks._handle_tool(command)

    # Verify mock executor was called
    # ...
```

---

## Part 8: Plugin Development Guide

### For Users Creating Custom Tools

Create a file in `~/.ai_shell/tools/my_tool.py`:

```python
"""My custom ai-shell tool."""

from ai_shell.core.registry import tool

@tool(
    name="my_custom_tool",
    description="Does something amazing",
    category="custom"
)
async def my_custom_tool(input_text: str, option: int = 5) -> str:
    """
    My custom tool implementation.

    Args:
        input_text: Input text to process
        option: Some option (default: 5)

    Returns:
        Processed result
    """
    # Your implementation
    result = f"Processed: {input_text} with option={option}"
    return result
```

Then run:
```bash
ai-shell  # Tools are auto-discovered!
ai> \my_custom_tool "hello" 10
```

---

## Summary

This mock and plugin system provides:

### ✅ **For Shell Development**
- Complete mocks for all backends
- Shell can be developed and tested independently
- Mock responses simulate real behavior
- Easy to test edge cases

### ✅ **For Agent Development**
- Clear interfaces to implement (`IAgent`, `ICommandExecutor`)
- Drop-in replacement for mocks when ready
- No changes to shell code needed

### ✅ **For Plugin Authors**
- Simple `@tool` decorator
- Auto-discovery from directories
- Type hints for parameters
- Async support built-in

### ✅ **Integration**
- Mocks default, real components opt-in
- Can mix mock and real components
- Easy testing at all levels
- Clear separation of concerns

### 📁 **File Structure**
```
ai_shell/
├── core/
│   ├── interfaces.py      # Abstract interfaces
│   ├── registry.py        # Tool registry with plugins
│   └── executor.py        # Command executor
├── mocks/
│   ├── __init__.py
│   ├── agent.py           # Mock agent
│   ├── executor.py        # Mock executor
│   ├── registry.py        # Mock registry
│   └── bash.py            # Mock bash
└── shell/
    └── repl.py            # Updated to use interfaces
```

This system allows completely independent development of shell and agent layers, with clear contracts and easy testing!
