# Shell Implementation Plan

## Overview

This document provides a detailed implementation plan for the **shell components** of ai-shell. The shell layer is responsible for user interaction, input parsing, command routing, and output rendering.

**Scope**: `ai_shell/shell/` package
**Timeline**: 2-3 weeks for complete implementation
**Prerequisites**: Python 3.11+, basic project structure

---

## Shell Components Architecture

```
ai_shell/shell/
├── __init__.py          # Package exports
├── repl.py              # Main REPL loop
├── parser.py            # Input parsing and command classification
├── renderer.py          # Output formatting and display
├── completer.py         # Tab completion logic
├── history.py           # Command history management
└── commands.py          # Meta commands (/help, /history, etc.)
```

### Component Dependency Graph

```
┌─────────────────────────────────────────────┐
│              User Terminal                   │
└─────────────────┬───────────────────────────┘
                  │
                  ↓
┌─────────────────────────────────────────────┐
│           REPL (repl.py)                     │
│  - Main event loop                           │
│  - Session management                        │
│  - Error handling                            │
└─────┬──────────────┬──────────────┬─────────┘
      │              │              │
      ↓              ↓              ↓
┌─────────┐   ┌──────────┐   ┌──────────┐
│ Parser  │   │ Renderer │   │Completer │
│         │   │          │   │          │
└────┬────┘   └─────┬────┘   └────┬─────┘
     │              │              │
     ↓              ↓              ↓
┌─────────┐   ┌──────────┐   ┌──────────┐
│ History │   │ Commands │   │  Config  │
│         │   │          │   │          │
└─────────┘   └──────────┘   └──────────┘
```

---

## Implementation Phases

### Phase 1: Basic REPL (Days 1-3)
**Goal**: Get a working interactive loop with basic input/output.

**Tasks**:
1. Project setup and dependencies
2. Basic REPL class with prompt
3. Simple echo functionality
4. Ctrl+C and Ctrl+D handling
5. Basic error display

### Phase 2: Input Parser (Days 4-6)
**Goal**: Parse and classify user input.

**Tasks**:
1. Prefix detection (!, ?, \, /)
2. Command tokenization
3. Pipeline parsing (split on |)
4. Variable substitution ($last, $summary)
5. Auto-resolution logic

### Phase 3: Output Renderer (Days 7-9)
**Goal**: Beautiful, streaming output display.

**Tasks**:
1. Rich console integration
2. Markdown rendering for AI responses
3. Syntax highlighting for code
4. Streaming token display
5. Error formatting

### Phase 4: Advanced Features (Days 10-14)
**Goal**: Tab completion, history, meta commands.

**Tasks**:
1. Tab completion implementation
2. Command history (up/down arrows)
3. History search (Ctrl+R)
4. Meta commands (/help, /history, etc.)
5. Session persistence

---

## Detailed Component Specifications

---

## 1. REPL (repl.py)

### Responsibilities
- Main event loop for user interaction
- Coordinate parser, executor, and renderer
- Handle keyboard interrupts and EOF
- Manage session state
- Error handling and recovery

### Dependencies
```python
# Core dependencies
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from rich.console import Console

# Internal dependencies
from ai_shell.shell.parser import Parser
from ai_shell.shell.renderer import Renderer
from ai_shell.shell.completer import ShellCompleter
from ai_shell.shell.commands import MetaCommandHandler
from ai_shell.core.memory import MemoryStore
```

### Class Structure

```python
from typing import Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum

class SessionState(Enum):
    """REPL session state."""
    STARTING = "starting"
    READY = "ready"
    EXECUTING = "executing"
    ERROR = "error"
    SHUTTING_DOWN = "shutting_down"

@dataclass
class REPLConfig:
    """REPL configuration."""
    prompt: str = "ai> "
    history_file: str = "~/.ai_shell/history"
    auto_suggest: bool = True
    vi_mode: bool = False
    multiline: bool = False
    show_status: bool = True
    debug_mode: bool = False

class REPL:
    """
    Interactive Read-Eval-Print Loop for ai-shell.

    Features:
    - Async input/output
    - Command history with persistence
    - Tab completion
    - Auto-suggestions
    - Streaming output display
    - Error recovery
    - Session management
    """

    def __init__(self,
                 parser: Parser,
                 renderer: Renderer,
                 memory: MemoryStore,
                 config: REPLConfig = None):
        """
        Initialize REPL.

        Args:
            parser: Input parser
            renderer: Output renderer
            memory: Memory store for history and variables
            config: REPL configuration
        """
        self.parser = parser
        self.renderer = renderer
        self.memory = memory
        self.config = config or REPLConfig()

        # State
        self.state = SessionState.STARTING
        self.session_id = None

        # Initialize components
        self.console = Console()
        self.completer = ShellCompleter(memory)
        self.meta_commands = MetaCommandHandler(self)

        # Prompt toolkit session
        self.prompt_session = PromptSession(
            history=FileHistory(os.path.expanduser(self.config.history_file)),
            auto_suggest=AutoSuggestFromHistory() if self.config.auto_suggest else None,
            completer=self.completer,
            vi_mode=self.config.vi_mode,
            multiline=self.config.multiline,
        )

    async def start(self):
        """
        Start the REPL session.

        Displays welcome message and enters main loop.
        """
        self.session_id = datetime.now().isoformat()
        self.state = SessionState.READY

        # Display welcome
        self._show_welcome()

        # Main loop
        await self._run_loop()

    async def _run_loop(self):
        """Main REPL loop."""
        while self.state != SessionState.SHUTTING_DOWN:
            try:
                # Get user input
                user_input = await self.prompt_session.prompt_async(
                    self._get_prompt(),
                    completer=self.completer
                )

                # Skip empty input
                if not user_input.strip():
                    continue

                # Process input
                await self._process_input(user_input)

            except KeyboardInterrupt:
                # Ctrl+C - cancel current operation
                self.renderer.print_info("\nCancelled")
                self.state = SessionState.READY
                continue

            except EOFError:
                # Ctrl+D - exit
                self.renderer.print_info("\nGoodbye!")
                self.state = SessionState.SHUTTING_DOWN
                break

            except Exception as e:
                # Unexpected error
                self.state = SessionState.ERROR
                self.renderer.print_error(f"Unexpected error: {e}")
                if self.config.debug_mode:
                    import traceback
                    self.renderer.print_debug(traceback.format_exc())
                self.state = SessionState.READY

    async def _process_input(self, user_input: str):
        """
        Process user input.

        Args:
            user_input: Raw input string
        """
        # Save to history
        self.memory.add_command(user_input)

        # Parse input
        try:
            command = self.parser.parse(user_input)
        except ParseError as e:
            self.renderer.print_error(f"Parse error: {e}")
            return

        # Handle different command types
        if command.type == "meta":
            # Meta command (/help, /history, etc.)
            await self._handle_meta_command(command)

        elif command.type == "chat":
            # Chat with AI (? prefix or auto-resolved)
            await self._handle_chat(command)

        elif command.type == "bash":
            # Bash command (! prefix)
            await self._handle_bash(command)

        elif command.type == "tool":
            # AI tool (\ prefix)
            await self._handle_tool(command)

        elif command.type == "pipeline":
            # Pipeline (contains |)
            await self._handle_pipeline(command)

        else:
            self.renderer.print_error(f"Unknown command type: {command.type}")

    async def _handle_meta_command(self, command):
        """Handle meta commands (/help, /history, etc.)."""
        result = await self.meta_commands.execute(command)
        if result:
            self.renderer.render(result)

    async def _handle_chat(self, command):
        """
        Handle chat command.

        Placeholder - will be implemented with Agent integration.
        """
        self.state = SessionState.EXECUTING
        self.renderer.print_info(f"[Chat] {command.message}")
        # TODO: Integrate with Agent
        self.renderer.print_warning("Chat not yet implemented")
        self.state = SessionState.READY

    async def _handle_bash(self, command):
        """
        Handle bash command.

        Placeholder - will be implemented with BashExecutor integration.
        """
        self.state = SessionState.EXECUTING
        self.renderer.print_info(f"[Bash] {command.command}")
        # TODO: Integrate with BashExecutor
        self.renderer.print_warning("Bash execution not yet implemented")
        self.state = SessionState.READY

    async def _handle_tool(self, command):
        """
        Handle AI tool command.

        Placeholder - will be implemented with ToolRegistry integration.
        """
        self.state = SessionState.EXECUTING
        self.renderer.print_info(f"[Tool] {command.tool_name}")
        # TODO: Integrate with ToolRegistry
        self.renderer.print_warning("Tool execution not yet implemented")
        self.state = SessionState.READY

    async def _handle_pipeline(self, command):
        """
        Handle pipeline command.

        Placeholder - will be implemented with PipelineEngine integration.
        """
        self.state = SessionState.EXECUTING
        self.renderer.print_info(f"[Pipeline] {len(command.stages)} stages")
        # TODO: Integrate with PipelineEngine
        self.renderer.print_warning("Pipeline execution not yet implemented")
        self.state = SessionState.READY

    def _get_prompt(self) -> str:
        """Get prompt string with optional status indicator."""
        if self.config.show_status:
            status_colors = {
                SessionState.READY: "green",
                SessionState.EXECUTING: "yellow",
                SessionState.ERROR: "red",
            }
            color = status_colors.get(self.state, "white")
            return f"[{color}]●[/{color}] {self.config.prompt}"
        return self.config.prompt

    def _show_welcome(self):
        """Display welcome message."""
        from rich.panel import Panel
        from rich.text import Text

        welcome_text = Text()
        welcome_text.append("ai-shell", style="bold blue")
        welcome_text.append(" v2.0\n\n", style="bold")
        welcome_text.append("Type ", style="dim")
        welcome_text.append("/help", style="bold cyan")
        welcome_text.append(" for commands, ", style="dim")
        welcome_text.append("Ctrl+D", style="bold")
        welcome_text.append(" to exit\n", style="dim")

        panel = Panel(
            welcome_text,
            title="Welcome",
            border_style="blue"
        )

        self.console.print(panel)
        self.console.print()
```

### Testing Strategy

```python
# tests/shell/test_repl.py
import pytest
from ai_shell.shell.repl import REPL, REPLConfig, SessionState

@pytest.fixture
def repl(parser, renderer, memory):
    config = REPLConfig(debug_mode=True)
    return REPL(parser, renderer, memory, config)

def test_repl_initialization(repl):
    """Test REPL initializes correctly."""
    assert repl.state == SessionState.STARTING
    assert repl.session_id is None

@pytest.mark.asyncio
async def test_repl_start(repl):
    """Test REPL starts and enters ready state."""
    # This will be interactive, so we test initialization only
    assert repl.config.prompt == "ai> "

def test_get_prompt_with_status(repl):
    """Test prompt string includes status indicator."""
    repl.config.show_status = True
    repl.state = SessionState.READY
    prompt = repl._get_prompt()
    assert "ai>" in prompt
    assert "●" in prompt  # Status indicator

@pytest.mark.asyncio
async def test_process_empty_input(repl):
    """Test empty input is handled gracefully."""
    # Should not raise exception
    await repl._process_input("")
    await repl._process_input("   ")
```

---

## 2. Parser (parser.py)

### Responsibilities
- Detect input prefix (!, ?, \, /)
- Tokenize commands
- Parse pipeline syntax (|)
- Variable substitution
- Auto-resolution logic
- Validate syntax

### Class Structure

```python
from typing import List, Optional, Union
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

    # For pipelines
    stages: Optional[List['ParsedCommand']] = None

    # For meta commands
    meta_command: Optional[str] = None
    meta_args: Optional[List[str]] = None

class ParseError(Exception):
    """Parse error exception."""
    pass

class Parser:
    """
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
                 memory: MemoryStore = None):
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
        tool_args = parts[1:] if len(parts) > 1 else []

        return ParsedCommand(
            type=CommandType.TOOL,
            raw=f"\\{tool_str}",
            tool_name=tool_name,
            tool_args=tool_args
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
```

### Testing Strategy

```python
# tests/shell/test_parser.py
import pytest
from ai_shell.shell.parser import Parser, ParseError, CommandType

@pytest.fixture
def parser():
    return Parser()

def test_parse_bash_command(parser):
    """Test parsing bash command with ! prefix."""
    result = parser.parse("!ls -la")
    assert result.type == CommandType.BASH
    assert result.command == "ls -la"

def test_parse_chat_command(parser):
    """Test parsing chat command with ? prefix."""
    result = parser.parse("?How are you?")
    assert result.type == CommandType.CHAT
    assert result.message == "How are you?"

def test_parse_tool_command(parser):
    """Test parsing tool command with \\ prefix."""
    result = parser.parse("\\summarize file.txt --max-length=50")
    assert result.type == CommandType.TOOL
    assert result.tool_name == "summarize"
    assert result.tool_args == ["file.txt", "--max-length=50"]

def test_parse_meta_command(parser):
    """Test parsing meta command with / prefix."""
    result = parser.parse("/help")
    assert result.type == CommandType.META
    assert result.meta_command == "help"

def test_parse_pipeline(parser):
    """Test parsing pipeline with | separator."""
    result = parser.parse("!ls -la | \\summarize")
    assert result.type == CommandType.PIPELINE
    assert len(result.stages) == 2
    assert result.stages[0].type == CommandType.BASH
    assert result.stages[1].type == CommandType.TOOL

def test_parse_pipeline_with_quotes(parser):
    """Test pipeline parsing respects quotes."""
    result = parser.parse('!echo "hello | world" | \\summarize')
    assert result.type == CommandType.PIPELINE
    assert len(result.stages) == 2

def test_auto_resolve_shell_command(parser):
    """Test auto-resolve detects common shell commands."""
    result = parser.parse("ls -la")
    assert result.type == CommandType.BASH
    assert result.command == "ls -la"

def test_auto_resolve_fallback_to_chat(parser):
    """Test auto-resolve falls back to chat for unknown input."""
    result = parser.parse("Hello there")
    assert result.type == CommandType.CHAT
    assert result.message == "Hello there"

def test_empty_input_raises_error(parser):
    """Test empty input raises ParseError."""
    with pytest.raises(ParseError):
        parser.parse("")

def test_variable_substitution(parser, memory):
    """Test variable substitution in input."""
    memory.set_variable("$last", "test_value")
    parser = Parser(memory=memory)

    result = parser.parse("!echo $last")
    assert "test_value" in result.command
```

---

## 3. Renderer (renderer.py)

### Responsibilities
- Format output for terminal display
- Render markdown (AI responses)
- Syntax highlight code
- Display streaming tokens
- Format errors and warnings
- Progress indicators

### Class Structure

```python
from typing import AsyncIterator, Optional
from enum import Enum
from rich.console import Console
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.panel import Panel
from rich.live import Live
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.text import Text

class OutputType(Enum):
    """Types of output."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"
    DEBUG = "debug"
    AI_RESPONSE = "ai_response"
    BASH_OUTPUT = "bash_output"
    CODE = "code"

class Renderer:
    """
    Output renderer for ai-shell.

    Handles all terminal output formatting using Rich library:
    - Markdown rendering for AI responses
    - Syntax highlighting for code
    - Streaming token display
    - Colored status messages
    - Progress indicators
    """

    def __init__(self,
                 console: Console = None,
                 theme: str = "monokai"):
        """
        Initialize renderer.

        Args:
            console: Rich console instance
            theme: Syntax highlighting theme
        """
        self.console = console or Console()
        self.theme = theme

    def render(self, content: str, output_type: OutputType = OutputType.INFO):
        """
        Render content based on type.

        Args:
            content: Content to render
            output_type: Type of output (determines formatting)
        """
        if output_type == OutputType.AI_RESPONSE:
            self.render_markdown(content)
        elif output_type == OutputType.CODE:
            self.render_code(content)
        elif output_type == OutputType.ERROR:
            self.print_error(content)
        elif output_type == OutputType.WARNING:
            self.print_warning(content)
        elif output_type == OutputType.SUCCESS:
            self.print_success(content)
        elif output_type == OutputType.DEBUG:
            self.print_debug(content)
        else:
            self.print_info(content)

    def render_markdown(self, content: str):
        """
        Render markdown content.

        Used for AI responses.
        """
        md = Markdown(content)
        self.console.print(md)

    def render_code(self,
                   code: str,
                   language: str = "python",
                   line_numbers: bool = False):
        """
        Render code with syntax highlighting.

        Args:
            code: Code to render
            language: Programming language for highlighting
            line_numbers: Show line numbers
        """
        syntax = Syntax(
            code,
            language,
            theme=self.theme,
            line_numbers=line_numbers
        )
        self.console.print(syntax)

    async def render_streaming(self,
                              token_stream: AsyncIterator[str],
                              output_type: OutputType = OutputType.AI_RESPONSE):
        """
        Render streaming tokens in real-time.

        Args:
            token_stream: Async iterator of tokens
            output_type: Output type (determines formatting)
        """
        if output_type == OutputType.AI_RESPONSE:
            await self._stream_markdown(token_stream)
        else:
            await self._stream_plain(token_stream)

    async def _stream_markdown(self, token_stream: AsyncIterator[str]):
        """Stream markdown tokens with live rendering."""
        content = ""

        with Live(Markdown(content), console=self.console, auto_refresh=False) as live:
            async for token in token_stream:
                content += token
                live.update(Markdown(content), refresh=True)

        # Final newline
        self.console.print()

    async def _stream_plain(self, token_stream: AsyncIterator[str]):
        """Stream plain text tokens."""
        async for token in token_stream:
            self.console.print(token, end="")
        self.console.print()  # Final newline

    def print_info(self, message: str):
        """Print info message."""
        self.console.print(message)

    def print_success(self, message: str):
        """Print success message (green)."""
        self.console.print(f"[green]✓[/green] {message}")

    def print_warning(self, message: str):
        """Print warning message (yellow)."""
        self.console.print(f"[yellow]⚠[/yellow] {message}")

    def print_error(self, message: str):
        """Print error message (red)."""
        self.console.print(f"[red]✗[/red] {message}")

    def print_debug(self, message: str):
        """Print debug message (dim)."""
        self.console.print(f"[dim]DEBUG: {message}[/dim]")

    def render_panel(self,
                    content: str,
                    title: str = None,
                    border_style: str = "blue"):
        """
        Render content in a panel.

        Args:
            content: Panel content
            title: Panel title
            border_style: Border color
        """
        panel = Panel(
            content,
            title=title,
            border_style=border_style
        )
        self.console.print(panel)

    def render_table(self,
                    headers: list,
                    rows: list,
                    title: str = None):
        """
        Render data as table.

        Args:
            headers: Column headers
            rows: Table rows
            title: Table title
        """
        from rich.table import Table

        table = Table(title=title)

        for header in headers:
            table.add_column(header, style="cyan")

        for row in rows:
            table.add_row(*[str(cell) for cell in row])

        self.console.print(table)

    def show_progress(self,
                     description: str,
                     total: Optional[int] = None):
        """
        Show progress indicator.

        Args:
            description: Progress description
            total: Total steps (if known)

        Returns:
            Progress context manager
        """
        if total:
            progress = Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console
            )
            return progress
        else:
            # Indeterminate spinner
            from rich.spinner import Spinner
            spinner = Spinner("dots", text=description)
            return self.console.status(spinner)
```

### Testing Strategy

```python
# tests/shell/test_renderer.py
import pytest
from io import StringIO
from rich.console import Console
from ai_shell.shell.renderer import Renderer, OutputType

@pytest.fixture
def renderer():
    # Use StringIO to capture output for testing
    console = Console(file=StringIO(), force_terminal=True)
    return Renderer(console=console)

def test_render_markdown(renderer):
    """Test markdown rendering."""
    renderer.render_markdown("# Hello\n\nThis is **bold**")
    output = renderer.console.file.getvalue()
    assert "Hello" in output

def test_render_code(renderer):
    """Test code rendering with syntax highlighting."""
    code = "def hello():\n    print('world')"
    renderer.render_code(code, language="python")
    output = renderer.console.file.getvalue()
    assert "hello" in output

def test_print_info(renderer):
    """Test info message printing."""
    renderer.print_info("Test info")
    output = renderer.console.file.getvalue()
    assert "Test info" in output

def test_print_success(renderer):
    """Test success message with checkmark."""
    renderer.print_success("Operation succeeded")
    output = renderer.console.file.getvalue()
    assert "succeeded" in output

def test_print_error(renderer):
    """Test error message in red."""
    renderer.print_error("Error occurred")
    output = renderer.console.file.getvalue()
    assert "Error occurred" in output

def test_render_panel(renderer):
    """Test panel rendering."""
    renderer.render_panel("Content", title="Test Panel")
    output = renderer.console.file.getvalue()
    assert "Test Panel" in output

@pytest.mark.asyncio
async def test_stream_plain(renderer):
    """Test streaming plain text."""
    async def token_gen():
        for token in ["Hello", " ", "world"]:
            yield token

    await renderer._stream_plain(token_gen())
    output = renderer.console.file.getvalue()
    assert "Hello world" in output
```

---

## 4. Completer (completer.py)

### Responsibilities
- Tab completion for commands
- Complete tool names
- Complete file paths
- Complete meta commands
- Context-aware suggestions

### Class Structure

```python
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.document import Document
from typing import Iterable
import os

class ShellCompleter(Completer):
    """
    Tab completion for ai-shell.

    Provides completions for:
    - AI tool names
    - Meta commands (/help, /history, etc.)
    - File paths
    - Shell commands (basic)
    """

    def __init__(self, memory: MemoryStore = None):
        """
        Initialize completer.

        Args:
            memory: Memory store (for context)
        """
        self.memory = memory

        # Static completions
        self.meta_commands = [
            '/help', '/history', '/clear', '/save', '/load',
            '/model', '/config', '/exit'
        ]

        self.common_shell_commands = [
            'ls', 'cd', 'pwd', 'cat', 'echo', 'grep', 'find'
        ]

        # Will be populated by tool registry
        self.tool_names = []

    def set_tool_names(self, tool_names: list):
        """Update available tool names."""
        self.tool_names = tool_names

    def get_completions(self,
                       document: Document,
                       complete_event) -> Iterable[Completion]:
        """
        Get completions for current input.

        Args:
            document: Current document state
            complete_event: Completion event

        Yields:
            Completion objects
        """
        text = document.text_before_cursor
        word = document.get_word_before_cursor()

        # Meta commands
        if text.startswith('/'):
            yield from self._complete_meta_commands(word)

        # AI tools
        elif text.startswith('\\'):
            yield from self._complete_tools(word)

        # File paths (in any context)
        elif '/' in word or '~' in word:
            yield from self._complete_paths(word)

        # Shell commands (with ! or auto-resolve)
        elif text.startswith('!') or not any(text.startswith(p) for p in ['?', '\\', '/']):
            yield from self._complete_shell_commands(word)

    def _complete_meta_commands(self, word: str) -> Iterable[Completion]:
        """Complete meta commands."""
        for cmd in self.meta_commands:
            if cmd.startswith('/' + word.lstrip('/')):
                yield Completion(
                    cmd,
                    start_position=-len(word),
                    display_meta="meta command"
                )

    def _complete_tools(self, word: str) -> Iterable[Completion]:
        """Complete AI tool names."""
        for tool in self.tool_names:
            if tool.startswith(word.lstrip('\\')):
                yield Completion(
                    tool,
                    start_position=-len(word),
                    display_meta="AI tool"
                )

    def _complete_paths(self, word: str) -> Iterable[Completion]:
        """Complete file paths."""
        # Expand ~ to home directory
        if word.startswith('~'):
            word = os.path.expanduser(word)

        # Get directory and filename parts
        if '/' in word:
            directory = os.path.dirname(word) or '.'
            prefix = os.path.basename(word)
        else:
            directory = '.'
            prefix = word

        # List directory contents
        try:
            if os.path.isdir(directory):
                for item in os.listdir(directory):
                    if item.startswith(prefix):
                        full_path = os.path.join(directory, item)
                        display = item + ('/' if os.path.isdir(full_path) else '')
                        yield Completion(
                            display,
                            start_position=-len(prefix),
                            display_meta="file" if not os.path.isdir(full_path) else "dir"
                        )
        except (OSError, PermissionError):
            pass

    def _complete_shell_commands(self, word: str) -> Iterable[Completion]:
        """Complete shell commands."""
        for cmd in self.common_shell_commands:
            if cmd.startswith(word):
                yield Completion(
                    cmd,
                    start_position=-len(word),
                    display_meta="shell command"
                )
```

---

## 5. Meta Commands (commands.py)

### Responsibilities
- Implement /help, /history, /clear, etc.
- Session management (/save, /load)
- Configuration (/model, /config)
- System information

### Class Structure

```python
from typing import Dict, Callable, Any
from dataclasses import dataclass

@dataclass
class MetaCommandResult:
    """Result from meta command execution."""
    success: bool
    message: str
    data: Any = None

class MetaCommandHandler:
    """
    Handler for meta commands (/help, /history, etc.).
    """

    def __init__(self, repl):
        """
        Initialize handler.

        Args:
            repl: REPL instance (for accessing state)
        """
        self.repl = repl

        # Register commands
        self.commands: Dict[str, Callable] = {
            'help': self.cmd_help,
            'history': self.cmd_history,
            'clear': self.cmd_clear,
            'save': self.cmd_save,
            'load': self.cmd_load,
            'model': self.cmd_model,
            'config': self.cmd_config,
            'exit': self.cmd_exit,
        }

    async def execute(self, command) -> MetaCommandResult:
        """
        Execute meta command.

        Args:
            command: Parsed meta command

        Returns:
            MetaCommandResult
        """
        cmd_name = command.meta_command

        if cmd_name not in self.commands:
            return MetaCommandResult(
                success=False,
                message=f"Unknown command: /{cmd_name}\nType /help for available commands"
            )

        handler = self.commands[cmd_name]
        return await handler(command.meta_args)

    async def cmd_help(self, args: list) -> MetaCommandResult:
        """Show help information."""
        help_text = """
# ai-shell Commands

## Prefixes
- `!cmd`     Run bash command
- `?text`    Chat with AI
- `\\tool`    Run AI tool
- `/cmd`     Meta command

## Meta Commands
- `/help`      Show this help
- `/history`   Show command history
- `/clear`     Clear session
- `/save`      Save current session
- `/load`      Load saved session
- `/model`     Change AI model
- `/config`    Show configuration
- `/exit`      Exit shell (or Ctrl+D)

## Pipeline
- `!cmd | \\tool`   Pipe bash output to AI tool
- `\\tool | !cmd`   Pipe AI output to bash

## Variables
- `$last`      Last command output
        """

        return MetaCommandResult(
            success=True,
            message=help_text
        )

    async def cmd_history(self, args: list) -> MetaCommandResult:
        """Show command history."""
        # TODO: Query from memory store
        return MetaCommandResult(
            success=True,
            message="History not yet implemented"
        )

    async def cmd_clear(self, args: list) -> MetaCommandResult:
        """Clear session."""
        self.repl.memory.clear()
        return MetaCommandResult(
            success=True,
            message="Session cleared"
        )

    async def cmd_save(self, args: list) -> MetaCommandResult:
        """Save current session."""
        session_id = args[0] if args else self.repl.session_id
        self.repl.memory.save_session()
        return MetaCommandResult(
            success=True,
            message=f"Session saved: {session_id}"
        )

    async def cmd_load(self, args: list) -> MetaCommandResult:
        """Load saved session."""
        if not args:
            return MetaCommandResult(
                success=False,
                message="Usage: /load <session_id>"
            )

        session_id = args[0]
        try:
            self.repl.memory.load_session(session_id)
            return MetaCommandResult(
                success=True,
                message=f"Session loaded: {session_id}"
            )
        except Exception as e:
            return MetaCommandResult(
                success=False,
                message=f"Failed to load session: {e}"
            )

    async def cmd_model(self, args: list) -> MetaCommandResult:
        """Change AI model."""
        # TODO: Implement model switching
        return MetaCommandResult(
            success=False,
            message="Model switching not yet implemented"
        )

    async def cmd_config(self, args: list) -> MetaCommandResult:
        """Show configuration."""
        # TODO: Display current configuration
        return MetaCommandResult(
            success=False,
            message="Config display not yet implemented"
        )

    async def cmd_exit(self, args: list) -> MetaCommandResult:
        """Exit shell."""
        self.repl.state = SessionState.SHUTTING_DOWN
        return MetaCommandResult(
            success=True,
            message="Goodbye!"
        )
```

---

## Integration Points

### With Core Components

The shell layer integrates with core components:

```python
# In REPL._handle_chat()
from ai_shell.core.agent import BaseAgent

async def _handle_chat(self, command):
    """Handle chat using BaseAgent."""
    agent = BaseAgent(self.model_adapter, self.tool_registry)

    async for token in agent.chat(command.message):
        await self.renderer.render_streaming(token)

# In REPL._handle_bash()
from ai_shell.core.bash_executor import BashExecutor

async def _handle_bash(self, command):
    """Handle bash using BashExecutor."""
    executor = BashExecutor()

    async for chunk in executor.execute(command.command):
        self.renderer.print_info(chunk.decode())

# In REPL._handle_pipeline()
from ai_shell.core.pipeline import PipelineEngine

async def _handle_pipeline(self, command):
    """Handle pipeline using PipelineEngine."""
    pipeline = self.pipeline_engine.build_from_parsed(command)

    async for chunk in pipeline.execute():
        self.renderer.print_info(chunk.decode())
```

---

## Development Workflow

### Day-by-Day Plan

**Days 1-3: Basic REPL**
```bash
# Create basic structure
mkdir -p ai_shell/shell tests/shell
touch ai_shell/shell/{__init__,repl,parser,renderer,completer,commands}.py

# Implement minimal REPL
# - Input loop
# - Echo functionality
# - Ctrl+C/Ctrl+D handling

# Test manually
python -m ai_shell
```

**Days 4-6: Parser**
```bash
# Implement parser
# - Prefix detection
# - Command classification
# - Basic tokenization

# Write tests
pytest tests/shell/test_parser.py -v

# Test in REPL
ai> !echo hello    # Should parse as bash
ai> ?hello         # Should parse as chat
ai> \summarize     # Should parse as tool
```

**Days 7-9: Renderer**
```bash
# Implement renderer
# - Rich console integration
# - Markdown rendering
# - Syntax highlighting

# Test rendering
ai> /help          # Should show formatted help

# Test streaming (mock)
# (Will need real streaming in Phase 3)
```

**Days 10-14: Advanced Features**
```bash
# Implement completer
# - Tab completion
# - File path completion

# Implement meta commands
# - /help
# - /history
# - /clear

# Integration testing
pytest tests/shell/ -v

# Manual testing
ai> [TAB]          # Should show completions
ai> /history       # Should show history
```

---

## Testing Strategy

### Unit Tests

```bash
# Test each component in isolation
pytest tests/shell/test_parser.py -v
pytest tests/shell/test_renderer.py -v
pytest tests/shell/test_completer.py -v
pytest tests/shell/test_commands.py -v
```

### Integration Tests

```python
# tests/shell/test_integration.py
@pytest.mark.asyncio
async def test_full_shell_flow(repl):
    """Test complete input → parse → execute → render flow."""
    # Simulate user input
    user_input = "!echo hello"

    # Parse
    command = repl.parser.parse(user_input)
    assert command.type == CommandType.BASH

    # Execute (mock)
    # (Will test with real executors in later phases)

    # Render
    repl.renderer.print_success("hello")
```

### Manual Testing

```bash
# Test scenarios
ai> !ls                          # Bash command
ai> ?What is Python?             # Chat
ai> \summarize README.md         # Tool
ai> !cat file.txt | \summarize   # Pipeline
ai> /help                        # Meta command
ai> [Ctrl+C]                     # Should cancel gracefully
ai> [Ctrl+D]                     # Should exit
```

---

## Dependencies

### Python Packages

```toml
# pyproject.toml
[project]
dependencies = [
    "prompt-toolkit>=3.0.0",   # Interactive input
    "rich>=13.0.0",             # Terminal formatting
    "click>=8.0.0",             # CLI framework (for entry point)
]
```

### Installation

```bash
# Development mode
pip install -e ".[dev]"

# Install with test dependencies
pip install -e ".[dev,test]"
```

---

## Entry Point

### Main Entry Point

```python
# ai_shell/__main__.py
"""Entry point for ai-shell CLI."""

import asyncio
import click
from ai_shell.shell.repl import REPL, REPLConfig
from ai_shell.shell.parser import Parser
from ai_shell.shell.renderer import Renderer
from ai_shell.core.memory import MemoryStore

@click.command()
@click.option('--debug', is_flag=True, help='Enable debug mode')
@click.option('--prompt', default='ai> ', help='Custom prompt string')
@click.option('--vi-mode', is_flag=True, help='Enable vi mode')
def main(debug, prompt, vi_mode):
    """ai-shell: AI-enhanced interactive shell."""

    # Initialize components
    parser = Parser()
    renderer = Renderer()
    memory = MemoryStore()

    config = REPLConfig(
        prompt=prompt,
        debug_mode=debug,
        vi_mode=vi_mode
    )

    repl = REPL(parser, renderer, memory, config)

    # Run REPL
    try:
        asyncio.run(repl.start())
    except KeyboardInterrupt:
        renderer.print_info("\nInterrupted")
    except Exception as e:
        renderer.print_error(f"Fatal error: {e}")
        if debug:
            import traceback
            traceback.print_exc()
        return 1

    return 0

if __name__ == '__main__':
    exit(main())
```

### Running

```bash
# As module
python -m ai_shell

# With options
python -m ai_shell --debug --prompt="$ "

# After pip install
ai-shell
```

---

## Success Criteria

### Phase 1 Complete When:
- [x] REPL starts and shows prompt
- [x] Can input text and see echo
- [x] Ctrl+C cancels gracefully
- [x] Ctrl+D exits cleanly
- [x] Basic error messages display

### Phase 2 Complete When:
- [x] Parser correctly identifies all command types
- [x] Pipeline syntax parsed correctly
- [x] Variables substituted properly
- [x] All parser tests pass

### Phase 3 Complete When:
- [x] Markdown renders beautifully
- [x] Code has syntax highlighting
- [x] Errors are red, warnings yellow
- [x] Streaming display works (mock)

### Phase 4 Complete When:
- [x] Tab completion suggests tools/commands
- [x] File path completion works
- [x] /help shows formatted help
- [x] /history displays past commands
- [x] All integration tests pass

---

## Next Steps After Shell Implementation

Once the shell layer is complete:

1. **Integrate with Core Components**
   - Connect to BaseAgent for chat
   - Connect to BashExecutor for commands
   - Connect to PipelineEngine for pipelines

2. **Add Streaming Support**
   - Real LLM streaming (Ollama)
   - Bash streaming output
   - Pipeline streaming between stages

3. **Testing with Real Components**
   - End-to-end testing
   - Performance testing
   - User acceptance testing

4. **Documentation**
   - User guide for shell features
   - Examples and tutorials
   - Troubleshooting guide

---

## Appendix

### A. Keyboard Shortcuts (Planned)

| Key | Action |
|-----|--------|
| `Ctrl+C` | Cancel current operation |
| `Ctrl+D` | Exit shell |
| `Ctrl+R` | Search history |
| `Ctrl+L` | Clear screen |
| `Tab` | Complete command |
| `↑` | Previous command |
| `↓` | Next command |
| `Ctrl+A` | Move to start of line |
| `Ctrl+E` | Move to end of line |

### B. Error Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | Parse error |
| 130 | Interrupted (Ctrl+C) |

### C. Environment Variables

| Variable | Purpose |
|----------|---------|
| `AI_SHELL_DEBUG` | Enable debug mode |
| `AI_SHELL_PROMPT` | Custom prompt |
| `AI_SHELL_HISTORY` | History file location |
| `AI_SHELL_CONFIG` | Config file location |

---

## Summary

This implementation plan provides a complete roadmap for building the shell layer of ai-shell. The modular design allows incremental development and testing, with clear success criteria at each phase.

**Key Takeaways**:
1. **Start simple**: Basic REPL first, add features incrementally
2. **Test early**: Unit tests for each component
3. **Mock integrations**: Shell can work standalone initially
4. **Focus on UX**: Beautiful output and smooth interaction are critical

**Estimated Timeline**: 2-3 weeks for complete shell implementation with all features and tests.

---

**Document Version**: 1.0
**Date**: 2025-10-10
**Status**: Ready for implementation
