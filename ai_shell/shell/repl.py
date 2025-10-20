"""Interactive REPL for ai-shell."""

import os
from typing import Optional
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from ai_shell.shell.parser import Parser, ParseError, CommandType
from ai_shell.shell.renderer import Renderer, OutputType
from ai_shell.shell.completer import ShellCompleter
from ai_shell.shell.commands import MetaCommandHandler
from ai_shell.core.memory import MemoryStore
from ai_shell.core.ollama_agent import OllamaAgent


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
                 agent=OllamaAgent(),
                 executor=None,
                 bash_executor=None,
                 registry=None,
                 config: REPLConfig = None):
        """
        Initialize REPL.

        Args:
            parser: Input parser
            renderer: Output renderer
            memory: Memory store for history and variables
            agent: AI agent (optional, uses mock if not provided)
            executor: Command executor (optional, uses mock if not provided)
            bash_executor: Bash executor (optional, uses mock if not provided)
            registry: Tool registry (optional, uses mock if not provided)
            config: REPL configuration
        """
        self.parser = parser
        self.renderer = renderer
        self.memory = memory
        self.config = config or REPLConfig()
        self.context_session = {}

        # State
        self.state = SessionState.STARTING
        self.session_id = None

        # Use provided implementations or fall back to mocks
        self.agent = agent or self._create_mock_agent()
        self.executor = executor or self._create_mock_executor()
        self.bash_executor = bash_executor or self._create_mock_bash()
        self.registry = registry or self._create_mock_registry()

        # Update parser with registry
        self.parser.tool_registry = self.registry
        self.parser.memory = self.memory

        # Initialize components
        self.console = Console()
        self.completer = ShellCompleter(memory)
        # Set tool names from executor (if it has get_command_names method)
        if hasattr(self.executor, 'get_command_names'):
            self.completer.set_tool_names(self.executor.get_command_names())
        elif hasattr(self.registry, 'list_names'):
            self.completer.set_tool_names(self.registry.list_names())
        self.meta_commands = MetaCommandHandler(self)

        # Ensure history directory exists
        history_path = os.path.expanduser(self.config.history_file)
        history_dir = os.path.dirname(history_path)
        if history_dir and not os.path.exists(history_dir):
            os.makedirs(history_dir, exist_ok=True)

        # Prompt toolkit session
        self.prompt_session = PromptSession(
            history=FileHistory(history_path),
            auto_suggest=AutoSuggestFromHistory() if self.config.auto_suggest else None,
            completer=self.completer,
            vi_mode=self.config.vi_mode,
            multiline=self.config.multiline,
        )

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
        if command.type == CommandType.META:
            # Meta command (/help, /history, etc.)
            await self._handle_meta_command(command)

        elif command.type == CommandType.CHAT:
            # Chat with AI (? prefix or auto-resolved)
            await self._handle_chat(command)

        elif command.type == CommandType.BASH:
            # Bash command (! prefix)
            await self._handle_bash(command)

        elif command.type == CommandType.TOOL:
            # AI tool (\ prefix)
            await self._handle_tool(command)

        elif command.type == CommandType.PIPELINE:
            # Pipeline (contains |)
            await self._handle_pipeline(command)

        else:
            self.renderer.print_error(f"Unknown command type: {command.type}")

    async def _handle_meta_command(self, command):
        """Handle meta commands (/help, /history, etc.)."""
        result = await self.meta_commands.execute(command)
        if result.success:
            self.renderer.render_markdown(result.message)
        else:
            self.renderer.print_error(result.message)

    async def _handle_chat(self, command):
        """Handle chat command."""
        self.state = SessionState.EXECUTING

        try:
            # Stream response from agent
            self.console.print()  # Empty line before response
            async for token in self.agent.chat(
                command.message,
                context=self.executor.context_session
            ):
                self.console.print(token, end="")

            self.console.print()  # Final newline
            self.console.print()  # Empty line after response
            self.state = SessionState.READY

        except Exception as e:
            self.renderer.print_error(f"Chat error: {e}")
            if self.config.debug_mode:
                import traceback
                self.renderer.print_debug(traceback.format_exc())
            self.state = SessionState.ERROR
            self.state = SessionState.READY

    async def _handle_tool(self, command):
        """Handle tool command using executor interface."""
        self.state = SessionState.EXECUTING

        try:
            result = await self.executor.execute(
                command.tool_name,
                args=command.tool_args or [],
                stdin=None,
                **(command.tool_options or {})
            )

            if result.success:
                self.renderer.render_markdown(result.output)
                self.memory.set_variable("$last", result.output)
            else:
                self.renderer.print_error(result.error)

            self.state = SessionState.READY

        except Exception as e:
            self.renderer.print_error(f"Tool execution error: {e}")
            if self.config.debug_mode:
                import traceback
                self.renderer.print_debug(traceback.format_exc())
            self.state = SessionState.ERROR
            self.state = SessionState.READY

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
            if self.config.debug_mode:
                import traceback
                self.renderer.print_debug(traceback.format_exc())
            self.state = SessionState.ERROR
            self.state = SessionState.READY

    async def _handle_pipeline(self, command, parse=False):
        """Handle pipeline command - pipe output through stages."""
        self.state = SessionState.EXECUTING

        try:
            # Start with empty stdin
            current_output = None

            # Execute each stage, passing output to next stage
            for i, stage in enumerate(command.stages):
                if self.config.debug_mode:
                    self.renderer.print_debug(f"Pipeline stage {i+1}/{len(command.stages)}: {stage.type.value}")

                if stage.type == CommandType.BASH:
                    # Execute bash command
                    if current_output:
                        result = await self.bash_executor.execute(
                            stage.command,
                            input_data=current_output.encode() if isinstance(current_output, str) else current_output
                        )
                    else:
                        result = await self.bash_executor.execute(stage.command)

                    if not result.success:
                        self.renderer.print_error(f"Pipeline failed at stage {i+1}: {result.error}")
                        self.state = SessionState.READY
                        return

                    current_output = result.output

                elif stage.type == CommandType.TOOL:
                    # Execute tool command
                    result = await self.executor.execute(
                        stage.tool_name,
                        args=stage.tool_args or [],
                        stdin=current_output,
                        **(stage.tool_options or {})
                    )

                    if not result.success:
                        self.renderer.print_error(f"Pipeline failed at stage {i+1}: {result.error}")
                        self.state = SessionState.READY
                        return

                    current_output = result.output

                else:
                    self.renderer.print_error(f"Cannot use {stage.type.value} in pipeline")
                    self.state = SessionState.READY
                    return

            # Display final output
            if current_output:
                self.renderer.render_markdown(current_output)
                self.memory.set_variable("$last", current_output)

            self.state = SessionState.READY

        except Exception as e:
            self.renderer.print_error(f"Pipeline error: {e}")
            if self.config.debug_mode:
                import traceback
                self.renderer.print_debug(traceback.format_exc())
            self.state = SessionState.ERROR
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
        welcome_text = Text()
        welcome_text.append("ai-shell", style="bold blue")
        welcome_text.append(" v0.1.0\n\n", style="bold")
        welcome_text.append("Type ", style="dim")
        welcome_text.append("/help", style="bold cyan")
        welcome_text.append(" for commands, ", style="dim")
        welcome_text.append("Ctrl+D", style="bold")
        welcome_text.append(" to exit\n", style="dim")
        welcome_text.append("\n", style="dim")

        # Show backend status
        from ai_shell.mocks import MockAgent, MockCommandExecutor, MockBashExecutor
        from ai_shell.core.bash_executor import BashExecutor
        from ai_shell.core.docker_bash_executor import DockerBashExecutor, DockerBashExecutorWithWrite

        # Determine bash backend type
        if isinstance(self.bash_executor, MockBashExecutor):
            bash_status = "mock"
            bash_color = "yellow"
        elif isinstance(self.bash_executor, DockerBashExecutorWithWrite):
            bash_status = "docker-rw"
            bash_color = "cyan"
        elif isinstance(self.bash_executor, DockerBashExecutor):
            bash_status = "docker"
            bash_color = "blue"
        elif isinstance(self.bash_executor, BashExecutor):
            bash_status = "native"
            bash_color = "green"
        else:
            bash_status = "unknown"
            bash_color = "dim"

        agent_status = "mock" if isinstance(self.agent, MockAgent) else "real"
        executor_status = "mock" if isinstance(self.executor, MockCommandExecutor) else "real"

        welcome_text.append(f"Backends: ", style="dim")
        welcome_text.append(f"bash={bash_status}", style=bash_color)
        welcome_text.append(f" agent={agent_status}", style="green" if agent_status == "real" else "yellow")
        welcome_text.append(f" tools={executor_status}", style="green" if executor_status == "real" else "yellow")

        panel = Panel(
            welcome_text,
            title="Welcome",
            border_style="blue"
        )

        self.console.print(panel)
        self.console.print()
