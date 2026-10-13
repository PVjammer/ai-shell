"""
Plugin interfaces for AI-Shell.

This module defines the core plugin system interfaces. All plugins must
implement the appropriate interface based on their type.

Plugin Types:
- Runtime: Execution backend (bash, docker, ssh, etc.)
- Agent: AI reasoning and tool calling (ollama, openai, anthropic, etc.)
- Shell: User interface (prompt, web ui, api server, etc.)
- Tool: Custom functions and commands
- Parser: Input parsing (default, AI-enhanced, etc.)
- Renderer: Output formatting (rich, markdown, html, etc.)
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, AsyncIterator, Callable
from pydantic import BaseModel
from dataclasses import dataclass

from ai_shell.core.interfaces import CommandResult, CustomFunction


# ============================================================================
# Base Plugin Interface
# ============================================================================


class PluginMetadata(BaseModel):
    """Plugin metadata."""
    name: str
    version: str
    plugin_type: str
    description: str
    author: str
    config: Dict[str, Any] = {}


class PluginInitializationError(Exception):
    """Raised when plugin initialization fails."""
    pass


class IPlugin(ABC):
    """
    Base interface for all plugins.

    All plugins must implement this interface regardless of type.
    """

    @abstractmethod
    def get_metadata(self) -> PluginMetadata:
        """
        Return plugin metadata.

        Returns:
            PluginMetadata with name, version, type, etc.
        """
        pass

    @abstractmethod
    async def initialize(self, config: Dict[str, Any]) -> None:
        """
        Initialize plugin with configuration.

        This is called once when the plugin is loaded. Plugins should:
        - Validate configuration
        - Connect to external services
        - Setup internal state
        - Raise PluginInitializationError if initialization fails

        Args:
            config: Plugin-specific configuration from config file

        Raises:
            PluginInitializationError: If initialization fails
        """
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """
        Cleanup resources before unloading.

        This is called when:
        - AI-Shell is shutting down
        - Plugin is being hot-reloaded
        - User switches to different plugin

        Plugins should:
        - Close connections
        - Free resources
        - Save state if needed
        """
        pass

    async def health_check(self) -> bool:
        """
        Check if plugin is healthy and ready.

        Returns:
            True if healthy, False otherwise
        """
        return True

    def get_config_schema(self) -> Optional[Dict[str, Any]]:
        """
        Return JSON schema for plugin configuration.

        This schema is used to:
        - Validate user configuration
        - Generate documentation
        - Provide autocomplete in editors

        Returns:
            JSON Schema dict, or None if no config needed
        """
        return None


# ============================================================================
# Runtime Plugin Interface
# ============================================================================


class IRuntimePlugin(IPlugin):
    """
    Interface for runtime execution plugins.

    Runtime plugins execute commands in different environments:
    - Native bash (local machine)
    - Docker containers (sandboxed)
    - SSH remote (remote machine)
    - WSL (Windows Subsystem for Linux)
    - Podman (alternative to Docker)
    - Custom environments
    """

    @abstractmethod
    async def execute(
        self,
        command: str,
        input_data: Optional[bytes] = None,
        timeout: int = 30,
        env: Optional[Dict[str, str]] = None,
        working_dir: Optional[str] = None
    ) -> CommandResult:
        """
        Execute a command and return result.

        Args:
            command: Command to execute (shell command string)
            input_data: Optional stdin data (bytes)
            timeout: Timeout in seconds
            env: Environment variables (extends system env)
            working_dir: Working directory (defaults to current)

        Returns:
            CommandResult with success, output, error

        Example:
            result = await runtime.execute("ls -la", working_dir="/tmp")
            if result.success:
                print(result.output)
        """
        pass

    @abstractmethod
    async def execute_streaming(
        self,
        command: str,
        input_data: Optional[bytes] = None,
        env: Optional[Dict[str, str]] = None,
        working_dir: Optional[str] = None
    ) -> AsyncIterator[bytes]:
        """
        Execute command with streaming output.

        This is preferred over execute() for long-running commands
        or commands with large output, as it allows real-time display.

        Args:
            command: Command to execute
            input_data: Optional stdin
            env: Environment variables
            working_dir: Working directory

        Yields:
            Output chunks (bytes)

        Example:
            async for chunk in runtime.execute_streaming("find / -name '*.py'"):
                print(chunk.decode(), end='')
        """
        pass

    @abstractmethod
    async def get_environment_info(self) -> Dict[str, Any]:
        """
        Get information about execution environment.

        Returns:
            Dict with environment info:
                - os: Operating system (linux, darwin, windows)
                - shell: Shell path (/bin/bash, /bin/zsh, etc.)
                - path: PATH environment variable
                - user: Current user
                - home: Home directory
                - cwd: Current working directory
                - remote: bool (True if remote execution)
                - custom fields specific to runtime

        Example:
            info = await runtime.get_environment_info()
            print(f"Running on {info['os']} as {info['user']}")
        """
        pass

    async def supports_feature(self, feature: str) -> bool:
        """
        Check if runtime supports a specific feature.

        Features:
            - "streaming": Supports execute_streaming()
            - "timeout": Supports command timeout
            - "env": Supports custom environment variables
            - "working_dir": Supports custom working directory
            - "pipes": Supports bash pipes in commands
            - "background": Supports background processes
            - "signals": Supports sending signals to processes

        Args:
            feature: Feature name

        Returns:
            True if supported, False otherwise
        """
        return False


# ============================================================================
# Agent Plugin Interface
# ============================================================================


@dataclass
class Tool:
    """Tool definition for agent."""
    name: str
    description: str
    parameters: Dict[str, Any]
    function: Callable


class IAgentPlugin(IPlugin):
    """
    Interface for AI agent plugins.

    Agent plugins provide AI reasoning and tool calling:
    - Ollama (local LLMs)
    - OpenAI (GPT-4, etc.)
    - Anthropic (Claude)
    - Local LLM servers (llama.cpp, vLLM, etc.)
    - Mock agents (for testing)
    """

    @abstractmethod
    async def chat(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        tools: Optional[List[Tool]] = None
    ) -> AsyncIterator[str]:
        """
        Chat with agent, streaming response tokens.

        Args:
            message: User message
            context: Optional context dict:
                - history: List[Dict] - Conversation history
                - user_context: List[str] - User-provided context
                - system_prompt: str - System prompt override
            tools: Optional list of available tools

        Yields:
            Response tokens (str)

        Example:
            async for token in agent.chat("What is Python?"):
                print(token, end='')
        """
        pass

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate complete response (non-streaming).

        Use this for:
        - Internal tool calls
        - Batch processing
        - When streaming not needed

        Args:
            prompt: Prompt text
            context: Optional context

        Returns:
            Complete response

        Example:
            summary = await agent.generate("Summarize: " + long_text)
        """
        pass

    @abstractmethod
    async def execute_task(
        self,
        task: str,
        tools: List[Tool],
        max_iterations: int = 10
    ) -> Dict[str, Any]:
        """
        Execute task using tools (agentic workflow).

        This implements a reasoning loop (e.g., ReAct pattern) where
        the agent:
        1. Thinks about the task
        2. Chooses a tool to use
        3. Executes the tool
        4. Observes the result
        5. Repeats until task is complete

        Args:
            task: Task description
            tools: Available tools
            max_iterations: Maximum reasoning iterations

        Returns:
            Result dict:
                - answer: str - Final answer
                - steps: List[Dict] - Reasoning steps
                - iterations: int - Number of iterations used
                - cancelled: bool - True if cancelled by user
                - max_iterations_reached: bool

        Example:
            result = await agent.execute_task(
                "Find all Python files and count lines",
                tools=[find_tool, count_tool]
            )
            print(result['answer'])
        """
        pass

    @abstractmethod
    def supports_tool_calling(self) -> bool:
        """
        Check if agent supports native tool calling.

        Returns:
            True if agent has native tool calling (like OpenAI function calling),
            False if tool calling must be implemented via prompting
        """
        pass

    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the model.

        Returns:
            Dict with model info:
                - provider: str (ollama, openai, anthropic, etc.)
                - model: str (llama3.1, gpt-4o, claude-3-5-sonnet, etc.)
                - supports_streaming: bool
                - supports_tools: bool
                - context_window: int (in tokens)
                - max_output_tokens: int
                - custom fields

        Example:
            info = agent.get_model_info()
            print(f"Using {info['provider']} {info['model']}")
        """
        pass


# ============================================================================
# Shell Plugin Interface
# ============================================================================


class IShellPlugin(IPlugin):
    """
    Interface for shell/frontend plugins.

    Shell plugins provide user interface:
    - Prompt (terminal REPL)
    - Web UI (browser-based)
    - API Server (REST/GraphQL)
    - Jupyter (notebook integration)
    - VS Code (extension)
    """

    @abstractmethod
    async def run(
        self,
        runtime: IRuntimePlugin,
        agent: IAgentPlugin,
        executor: Any  # ICommandExecutor
    ) -> None:
        """
        Run the shell interface.

        This is the main entry point. The shell should:
        1. Setup UI
        2. Get user input
        3. Parse input
        4. Execute commands using runtime/agent/executor
        5. Display results
        6. Repeat

        Args:
            runtime: Runtime plugin for command execution
            agent: Agent plugin for AI interactions
            executor: Command executor for tools

        Example:
            await shell.run(runtime, agent, executor)
            # Blocks until user exits
        """
        pass

    @abstractmethod
    async def display_output(
        self,
        output: str,
        output_type: str = "text"
    ) -> None:
        """
        Display output to user.

        Args:
            output: Output text
            output_type: Output type:
                - "text": Plain text
                - "markdown": Markdown-formatted
                - "error": Error message
                - "info": Info message
                - "debug": Debug message
                - "code": Code block
                - "json": JSON data

        Example:
            await shell.display_output("# Success!", "markdown")
        """
        pass

    @abstractmethod
    async def get_user_input(self, prompt: str = "") -> str:
        """
        Get input from user.

        Args:
            prompt: Prompt to display

        Returns:
            User input (raw string)

        Example:
            user_input = await shell.get_user_input("ai> ")
        """
        pass

    @abstractmethod
    async def request_approval(
        self,
        command: str,
        context: Dict[str, Any]
    ) -> bool:
        """
        Request user approval for command execution.

        This is called by the approval system (HITL) before executing
        potentially dangerous commands.

        Args:
            command: Command to approve
            context: Context dict:
                - reasoning: str - Why agent wants to run this
                - risk: str - Risk level (low, medium, high)
                - expected_outcome: str - What will happen
                - dry_run_available: bool

        Returns:
            True if approved, False if denied

        Example:
            approved = await shell.request_approval(
                "rm -rf /tmp/data",
                {"reasoning": "Clean up temp files", "risk": "medium"}
            )
        """
        pass

    async def show_progress(
        self,
        message: str,
        progress: Optional[float] = None
    ) -> None:
        """
        Show progress indicator.

        Args:
            message: Progress message
            progress: Optional progress (0.0 to 1.0)

        Example:
            await shell.show_progress("Processing...", 0.5)
        """
        pass

    async def clear_output(self) -> None:
        """Clear the output display."""
        pass


# ============================================================================
# Tool Plugin Interface
# ============================================================================


class IToolPlugin(IPlugin):
    """
    Interface for tool plugins.

    Tool plugins provide custom functions/commands:
    - Built-in tools (summarize, search, etc.)
    - MCP tools (Model Context Protocol)
    - Custom user tools
    - Web tools (search, scrape)
    - File tools (advanced operations)
    """

    @abstractmethod
    def get_tools(self) -> List[CustomFunction]:
        """
        Return list of tools provided by this plugin.

        Returns:
            List of CustomFunction instances

        Example:
            tools = tool_plugin.get_tools()
            for tool in tools:
                executor.register_function(tool)
        """
        pass

    async def on_tool_executed(
        self,
        tool_name: str,
        result: Any
    ) -> None:
        """
        Callback after tool execution.

        This is called after a tool from this plugin is executed,
        allowing the plugin to:
        - Log execution
        - Update internal state
        - Trigger side effects

        Args:
            tool_name: Name of executed tool
            result: Execution result

        Example:
            # Called after \summarize executes
            await plugin.on_tool_executed("summarize", summary_result)
        """
        pass


# ============================================================================
# Parser Plugin Interface
# ============================================================================


class IParserPlugin(IPlugin):
    """
    Interface for parser plugins.

    Parser plugins parse user input into commands:
    - Default parser (prefix-based: !, ?, \, /)
    - AI-enhanced parser (LLM helps parse)
    - Multi-language parser (support multiple languages)
    - Macro parser (expand macros)
    """

    @abstractmethod
    def parse(self, user_input: str) -> Any:  # ParsedCommand
        """
        Parse user input into a command.

        Args:
            user_input: Raw user input

        Returns:
            ParsedCommand object

        Raises:
            ParseError: If input cannot be parsed

        Example:
            command = parser.parse("!ls -la")
            # Returns ParsedCommand(type=BASH, command="ls -la")
        """
        pass

    async def suggest_completions(
        self,
        partial_input: str
    ) -> List[str]:
        """
        Suggest completions for partial input.

        Args:
            partial_input: Incomplete user input

        Returns:
            List of completion suggestions

        Example:
            suggestions = await parser.suggest_completions("\\sum")
            # Returns ["\\summarize"]
        """
        return []


# ============================================================================
# Renderer Plugin Interface
# ============================================================================


class IRendererPlugin(IPlugin):
    """
    Interface for renderer plugins.

    Renderer plugins format and display output:
    - Rich renderer (colored terminal output)
    - Markdown renderer (pure markdown)
    - HTML renderer (HTML output)
    - JSON renderer (JSON output)
    - Plain text renderer (no formatting)
    """

    @abstractmethod
    async def render(
        self,
        content: str,
        content_type: str = "text"
    ) -> str:
        """
        Render content for display.

        Args:
            content: Content to render
            content_type: Content type (text, markdown, code, json, error)

        Returns:
            Rendered content (formatted string, HTML, etc.)

        Example:
            rendered = await renderer.render("# Hello", "markdown")
        """
        pass

    async def render_stream(
        self,
        content_stream: AsyncIterator[str],
        content_type: str = "text"
    ) -> AsyncIterator[str]:
        """
        Render streaming content.

        Args:
            content_stream: Async iterator of content chunks
            content_type: Content type

        Yields:
            Rendered chunks

        Example:
            async for chunk in renderer.render_stream(agent.chat("Hi")):
                print(chunk, end='')
        """
        async for chunk in content_stream:
            yield await self.render(chunk, content_type)
