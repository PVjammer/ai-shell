"""
Abstract interfaces for ai-shell components.

These protocols define the contract between shell layer and execution layer.
Both mock and real implementations must conform to these interfaces.
"""
from __future__ import annotations
from typing import Protocol, AsyncIterator, List, Dict, Any, Optional, Callable
from dataclasses import dataclass
import json
import inspect
import argparse
from pydantic import BaseModel, Field
from typing import Optional, Type

# ============================================================================
# Data Models
# ============================================================================

class CommandError(Exception):
    pass

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
    parameters: Dict[str, Any] | None = None

    def __post_init__(self):
        if self.parameters is None:
            self.parameters = {}


# ============================================================================
# Custom Function Interface
# ============================================================================

class Tool(BaseModel):

    def __init__(self, func: CustomFunction):
        self._custom_function = func

    @property
    def name(self):
        return self._custom_function.name

    @property
    def input_schema(self, as_dict: bool = True):
        func_schema = self._custom_function.input_schema_model or DefaultFunctionInput
        if as_dict:
            return func_schema.model_json_schema()
        return func_schema
    
    @property
    def description(self):
        return self._custom_function.description

    async def ainvoke(self, _input: Any = None):
       return await self._custom_function.execute(_input)


class BaseFunctionInput(BaseModel):
    
    @classmethod
    def _from_str(cls, content: str):
        return cls.model_validate_json(content)

    @classmethod
    def _from_dict(cls, content: dict):
        return cls.model_validate(content)

    @classmethod
    def parse_input(cls, content: str | dict | None):
        if not content:
            return cls(content=None)
        if isinstance(content, str):
            return cls.model_validate_json(content)
        if isinstance(content, dict):
            return cls.model_validate(content)
        else:
            raise ValueError("Input must be a dict or string")

    @classmethod
    def get_arg_parser(cls, cmd_name: str, description: str = ""):
        parser = argparse.ArgumentParser(
            prog=cmd_name,
            description=description,
            exit_on_error=False
        )
        short_flags = []
        for field_name, field_info in cls.model_fields.items():
            if field_name == "content":
                kwarg_dict = {}
                if field_info.description:
                    kwarg_dict["help"] = field_info.description
                parser.add_argument(field_name, **kwarg_dict)
                continue
            arg_name = f"--{field_name.replace('_', '-')}"
            short_flag = f"-{field_name[0]}"
            arg_kwargs = {}

            typ = field_info.annotation
            default = field_info.default
            required = field_info.is_required()
            if field_info.description:
                arg_kwargs["help"] = field_info.description

            # Booleans
            if typ == bool:
                arg_kwargs["action"] = "store_true" if default is False else "store_false"
            else:
                arg_kwargs["type"] = typ
                if default is not None:
                    arg_kwargs["default"] = default
                if required:
                    arg_kwargs["required"] = True
            
            if short_flag in short_flags:
                parser.add_argument(arg_name, **arg_kwargs)
            else:
                parser.add_argument(short_flag, arg_name, **arg_kwargs)
                short_flags.append(short_flag)
        
        return parser
    
    @classmethod
    def from_parser(cls, parsed_args: argparse.Namespace):
        args_dict = vars(parsed_args)
        return cls.model_validate(args_dict)

class FunctionInput(BaseFunctionInput):
    # Override this field in your input Schema to provide a better description. Will act as positional arg and handle stdin
    content: Any


class DefaultFunctionInput(FunctionInput):
    content: Any = None


class OptionOnlyFunctionInput(BaseFunctionInput):
    pass


class EmptyFunctionInput(FunctionInput):
    
    @classmethod
    def parse_input(cls, content: str | Dict | None):
        if content:
            raise ValueError("Function does not take any arguments")
        return cls(content=None)

    @classmethod
    def get_arg_parser(cls, cmd_name: str, description: str = ""):
        parser = argparse.ArgumentParser(
            prog=cmd_name,
            description=description,
            exit_on_error=False
        )
        return parser
    
    @classmethod
    def from_parser(cls, parsed_args: argparse.Namespace):
        return cls(content=None)


class CustomFunction:
    """
    """
    def __init__(self,
                 name: str,
                 description: str,
                 func: Callable, 
                 input_schema: BaseFunctionInput | None = None,
                ):
        self._name = name
        self.description = description
        self.input_schema_model = input_schema or FunctionInput
        self.func = func
        self.parser = self.input_schema_model.get_arg_parser(self.cmd_name, self.description)    

    @property
    def name(self):
        return self._name

    @property
    def cmd_name(self):
        return "\\"+self._name

    async def execute(self, function_input: str | dict = {}):
        """"""
        # if not self.input_schema_model:
        #     return await self._excecute(DefaultFunctionInput(content=function_input))
        
        _input = self.input_schema_model.parse_input(function_input)
        return await self._excecute(_input)

    async def _excecute(self, _input: BaseFunctionInput):
        return await self.func(_input)
    
    def as_tool(self):
        return Tool(self)
    
    async def execute_command(self, args: list[str], stdin: str | None = None, **options):
        """
        """
        # if "--help" in args or "-h" in args:
        #     return self.parser.format_help()
        
        try:
            if stdin:
                args = [stdin, *args]
            parsed_args = self.parser.parse_args(args)
            _input_model = self.input_schema_model.from_parser(parsed_args)

        except SystemExit as ex:
            if str(ex) != "0":
                raise CommandError(f"Invalid input for {self.cmd_name}")
            return ""
        
        except Exception as e:
             print("Throwing the other exception")
             raise CommandError(f"Invalid input for {self.cmd_name}: {e}\n\n{self.parser.format_help()}")
        
        
        return await self._excecute(_input_model)
            



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

    async def generate(self, message: str, context: Dict | None = None) -> str:
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
