# AI-Shell Plugin System Design

**Version:** 1.0
**Date:** 2025-12-29
**Status:** Design Document

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Plugin Types](#plugin-types)
4. [Plugin Discovery and Loading](#plugin-discovery-and-loading)
5. [Plugin Interfaces](#plugin-interfaces)
6. [Configuration System](#configuration-system)
7. [Implementation Plan](#implementation-plan)
8. [Plugin Development Guide](#plugin-development-guide)
9. [Example Plugins](#example-plugins)

---

## Overview

### Design Goals

The AI-Shell plugin system transforms every major component into a swappable, configurable plugin:

1. **Everything is a Plugin**: Runtime executors, agents, shell interfaces, tools, and parsers
2. **Default Implementations**: Current code becomes "built-in" plugins
3. **Hot-Swappable**: Change components without recompiling
4. **Configuration-Driven**: Select plugins via config files
5. **Dependency Management**: Plugins declare dependencies
6. **Lifecycle Management**: Proper initialization, cleanup, and error handling

### Core Principle

> **Inversion of Control**: The AI-Shell core becomes a thin orchestration layer. All functionality lives in plugins.

---

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    AI-Shell Core                             │
│  ┌────────────────────────────────────────────────────────┐ │
│  │         Plugin Manager (Discovery & Loading)            │ │
│  └────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────┐ │
│  │         Configuration Loader (YAML/ENV)                 │ │
│  └────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────┐ │
│  │         Dependency Resolver                             │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    Plugin Ecosystem                          │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Runtime    │  │    Agent     │  │    Shell     │      │
│  │   Plugins    │  │   Plugins    │  │   Plugins    │      │
│  ├──────────────┤  ├──────────────┤  ├──────────────┤      │
│  │ • Bash       │  │ • Ollama     │  │ • Prompt     │      │
│  │ • Docker     │  │ • OpenAI     │  │ • Web UI     │      │
│  │ • SSH Remote │  │ • Anthropic  │  │ • API Server │      │
│  │ • Podman     │  │ • Local LLM  │  │ • Jupyter    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │    Tool      │  │   Parser     │  │   Renderer   │      │
│  │   Plugins    │  │   Plugins    │  │   Plugins    │      │
│  ├──────────────┤  ├──────────────┤  ├──────────────┤      │
│  │ • Built-in   │  │ • Default    │  │ • Rich       │      │
│  │ • MCP        │  │ • AI-Enhanced│  │ • Markdown   │      │
│  │ • Custom     │  │ • Multi-lang │  │ • HTML       │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

### Plugin Lifecycle

```
┌──────────────┐
│  Discovery   │  Scan plugin directories, read manifests
└──────┬───────┘
       ↓
┌──────────────┐
│  Validation  │  Check compatibility, dependencies
└──────┬───────┘
       ↓
┌──────────────┐
│   Loading    │  Import modules, instantiate classes
└──────┬───────┘
       ↓
┌──────────────┐
│Initialization│  Setup, connect to external services
└──────┬───────┘
       ↓
┌──────────────┐
│   Running    │  Plugin serves requests
└──────┬───────┘
       ↓
┌──────────────┐
│   Cleanup    │  Disconnect, free resources
└──────────────┘
```

---

## Plugin Types

### 1. Runtime Plugin (Execution Backend)

**Purpose**: Execute bash commands in different environments

**Interface**: `IRuntimePlugin`

**Examples**:
- `NativeBashPlugin` - Direct local execution (default)
- `DockerRuntimePlugin` - Sandboxed Docker execution
- `SSHRuntimePlugin` - Execute on remote machine
- `WSLRuntimePlugin` - Windows Subsystem for Linux
- `PodmanRuntimePlugin` - Alternative to Docker

### 2. Agent Plugin

**Purpose**: Provide AI reasoning and tool calling

**Interface**: `IAgentPlugin`

**Examples**:
- `OllamaAgentPlugin` - Local Ollama (default)
- `OpenAIAgentPlugin` - GPT-4 via API
- `AnthropicAgentPlugin` - Claude via API
- `LocalLLMPlugin` - llama.cpp, vLLM, etc.
- `MockAgentPlugin` - For testing

### 3. Shell Plugin (Frontend Interface)

**Purpose**: Present interface to user

**Interface**: `IShellPlugin`

**Examples**:
- `PromptShellPlugin` - Terminal REPL (default)
- `WebUIPlugin` - Browser-based interface
- `APIServerPlugin` - REST/GraphQL API
- `JupyterPlugin` - Jupyter notebook integration
- `VSCodePlugin` - VS Code extension interface

### 4. Tool Plugin

**Purpose**: Provide custom functions/tools

**Interface**: `IToolPlugin`

**Examples**:
- `BuiltinToolsPlugin` - Core tools (summarize, etc.)
- `MCPToolPlugin` - Model Context Protocol integration
- `CustomToolsPlugin` - User-defined tools
- `WebToolsPlugin` - Web search, scraping
- `FileToolsPlugin` - Advanced file operations

### 5. Parser Plugin

**Purpose**: Parse user input into commands

**Interface**: `IParserPlugin`

**Examples**:
- `DefaultParserPlugin` - Current prefix-based parser
- `AIParserPlugin` - LLM-enhanced parsing
- `MultiLangParserPlugin` - Support multiple languages
- `MacroParserPlugin` - Macro expansion

### 6. Renderer Plugin

**Purpose**: Format and display output

**Interface**: `IRendererPlugin`

**Examples**:
- `RichRendererPlugin` - Rich terminal output (default)
- `MarkdownRendererPlugin` - Pure markdown
- `HTMLRendererPlugin` - HTML output
- `JSONRendererPlugin` - JSON output

---

## Plugin Discovery and Loading

### Directory Structure

```
Plugin Locations (searched in order):
1. ~/.ai_shell/plugins/          (user plugins)
2. ./ai_shell_plugins/           (project-local plugins)
3. ai_shell/plugins/builtin/     (built-in plugins, packaged with ai-shell)
```

### Plugin Package Structure

```
plugin_name/
├── plugin.yaml              # Plugin manifest (required)
├── __init__.py             # Python package marker
├── plugin.py               # Plugin implementation (entry point)
├── requirements.txt        # Dependencies (optional)
├── README.md              # Plugin documentation (optional)
├── tests/                 # Plugin tests (optional)
│   └── test_plugin.py
└── config/                # Plugin-specific config (optional)
    └── defaults.yaml
```

### Plugin Manifest (plugin.yaml)

```yaml
# Required fields
name: docker_runtime          # Unique identifier
version: 1.0.0               # Semantic version
plugin_type: runtime         # Type: runtime, agent, shell, tool, parser, renderer
entry_point: plugin:DockerRuntimePlugin  # module:ClassName

# Metadata
display_name: Docker Runtime
description: Execute commands in Docker containers
author: Your Name
license: MIT
homepage: https://github.com/user/plugin

# Dependencies
requires:
  ai_shell: ">=0.2.0"       # Minimum ai-shell version
  python: ">=3.11"          # Python version

dependencies:
  - docker>=6.0.0           # Python package dependencies
  - requests>=2.28.0

system_dependencies:        # System-level dependencies (informational)
  - docker                  # Docker daemon required

# Plugin-specific configuration
config_schema:
  type: object
  properties:
    default_image:
      type: string
      default: "ubuntu:22.04"
    timeout:
      type: integer
      default: 300

# Compatibility
compatible_plugins:
  runtime: []               # Can coexist with other runtime plugins
  agent: ["*"]             # Compatible with all agents

incompatible_plugins:
  runtime: ["ssh_runtime"]  # Cannot be used with SSH runtime

# Lifecycle hooks
hooks:
  on_load: setup_docker_client
  on_unload: cleanup_docker_resources
  on_config_change: reconfigure
```

### Plugin Discovery Process

```python
class PluginManager:
    def discover_plugins(self) -> List[PluginManifest]:
        """Discover all available plugins."""
        plugins = []

        # Search plugin directories
        for plugin_dir in self.plugin_search_paths:
            for manifest_path in plugin_dir.glob("*/plugin.yaml"):
                try:
                    manifest = self._load_manifest(manifest_path)
                    self._validate_manifest(manifest)
                    plugins.append(manifest)
                except Exception as e:
                    logger.warning(f"Failed to load plugin at {manifest_path}: {e}")

        return plugins

    def _validate_manifest(self, manifest: PluginManifest):
        """Validate plugin manifest."""
        # Check required fields
        required = ["name", "version", "plugin_type", "entry_point"]
        for field in required:
            if not getattr(manifest, field):
                raise ValueError(f"Missing required field: {field}")

        # Validate plugin type
        if manifest.plugin_type not in PLUGIN_TYPES:
            raise ValueError(f"Invalid plugin type: {manifest.plugin_type}")

        # Validate version
        try:
            Version(manifest.version)
        except Exception:
            raise ValueError(f"Invalid version: {manifest.version}")
```

---

## Plugin Interfaces

### Base Plugin Interface

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pydantic import BaseModel


class PluginMetadata(BaseModel):
    """Plugin metadata."""
    name: str
    version: str
    plugin_type: str
    description: str
    author: str
    config: Dict[str, Any] = {}


class IPlugin(ABC):
    """Base interface for all plugins."""

    @abstractmethod
    def get_metadata(self) -> PluginMetadata:
        """Return plugin metadata."""
        pass

    @abstractmethod
    async def initialize(self, config: Dict[str, Any]) -> None:
        """
        Initialize plugin with configuration.

        Args:
            config: Plugin-specific configuration

        Raises:
            PluginInitializationError: If initialization fails
        """
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """Cleanup resources before unloading."""
        pass

    async def health_check(self) -> bool:
        """Check if plugin is healthy and ready."""
        return True

    def get_config_schema(self) -> Optional[Dict[str, Any]]:
        """Return JSON schema for plugin configuration."""
        return None
```

### 1. Runtime Plugin Interface

```python
from ai_shell.core.interfaces import CommandResult
from typing import Optional, AsyncIterator


class IRuntimePlugin(IPlugin):
    """Interface for runtime execution plugins."""

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
        Execute a command.

        Args:
            command: Command to execute
            input_data: Optional stdin data
            timeout: Timeout in seconds
            env: Environment variables
            working_dir: Working directory

        Returns:
            CommandResult with output/error
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

        Args:
            command: Command to execute
            input_data: Optional stdin
            env: Environment variables
            working_dir: Working directory

        Yields:
            Output chunks
        """
        pass

    @abstractmethod
    async def get_environment_info(self) -> Dict[str, Any]:
        """
        Get information about execution environment.

        Returns:
            Dict with info like: os, shell, PATH, etc.
        """
        pass

    async def supports_feature(self, feature: str) -> bool:
        """Check if runtime supports a feature."""
        return False


# Built-in implementation
class NativeBashRuntimePlugin(IRuntimePlugin):
    """Default native bash runtime plugin."""

    def __init__(self):
        self.shell = "/bin/bash"

    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="native_bash",
            version="1.0.0",
            plugin_type="runtime",
            description="Native bash execution on local machine",
            author="AI-Shell Team"
        )

    async def initialize(self, config: Dict[str, Any]) -> None:
        self.shell = config.get("shell", "/bin/bash")
        # Verify shell exists
        if not Path(self.shell).exists():
            raise PluginInitializationError(f"Shell not found: {self.shell}")

    async def cleanup(self) -> None:
        pass  # Nothing to cleanup

    async def execute(
        self,
        command: str,
        input_data: Optional[bytes] = None,
        timeout: int = 30,
        env: Optional[Dict[str, str]] = None,
        working_dir: Optional[str] = None
    ) -> CommandResult:
        """Execute bash command."""
        import subprocess

        try:
            process = subprocess.run(
                command,
                shell=True,
                executable=self.shell,
                input=input_data,
                capture_output=True,
                timeout=timeout,
                env=env,
                cwd=working_dir
            )

            return CommandResult(
                success=process.returncode == 0,
                output=process.stdout.decode(),
                error=process.stderr.decode()
            )
        except subprocess.TimeoutExpired:
            return CommandResult(
                success=False,
                output="",
                error=f"Command timed out after {timeout}s"
            )
        except Exception as e:
            return CommandResult(
                success=False,
                output="",
                error=str(e)
            )

    async def execute_streaming(
        self,
        command: str,
        input_data: Optional[bytes] = None,
        env: Optional[Dict[str, str]] = None,
        working_dir: Optional[str] = None
    ) -> AsyncIterator[bytes]:
        """Stream command output."""
        import asyncio

        process = await asyncio.create_subprocess_shell(
            command,
            executable=self.shell,
            stdin=asyncio.subprocess.PIPE if input_data else None,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
            cwd=working_dir
        )

        if input_data:
            process.stdin.write(input_data)
            await process.stdin.drain()
            process.stdin.close()

        while True:
            chunk = await process.stdout.read(1024)
            if not chunk:
                break
            yield chunk

        await process.wait()

    async def get_environment_info(self) -> Dict[str, Any]:
        import os
        import platform

        return {
            "os": platform.system(),
            "shell": self.shell,
            "path": os.environ.get("PATH", ""),
            "user": os.environ.get("USER", "unknown"),
            "home": os.environ.get("HOME", ""),
            "cwd": os.getcwd()
        }
```

### 2. Agent Plugin Interface

```python
from typing import List, Dict, Any, AsyncIterator, Optional


class Tool(BaseModel):
    """Tool definition for agent."""
    name: str
    description: str
    parameters: Dict[str, Any]
    function: Callable


class IAgentPlugin(IPlugin):
    """Interface for AI agent plugins."""

    @abstractmethod
    async def chat(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        tools: Optional[List[Tool]] = None
    ) -> AsyncIterator[str]:
        """
        Chat with agent, streaming response.

        Args:
            message: User message
            context: Conversation context
            tools: Available tools

        Yields:
            Response tokens
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

        Args:
            prompt: Prompt text
            context: Context

        Returns:
            Complete response
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

        Args:
            task: Task description
            tools: Available tools
            max_iterations: Max reasoning iterations

        Returns:
            Result dict with answer, steps, etc.
        """
        pass

    @abstractmethod
    def supports_tool_calling(self) -> bool:
        """Check if agent supports native tool calling."""
        pass

    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the model."""
        pass


# Built-in implementation
class OllamaAgentPlugin(IAgentPlugin):
    """Default Ollama agent plugin."""

    def __init__(self):
        self.client = None
        self.model = "llama3.1"

    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="ollama_agent",
            version="1.0.0",
            plugin_type="agent",
            description="Local AI agent using Ollama",
            author="AI-Shell Team"
        )

    async def initialize(self, config: Dict[str, Any]) -> None:
        from ollama import AsyncClient

        base_url = config.get("base_url", "http://localhost:11434")
        self.model = config.get("model", "llama3.1")
        self.client = AsyncClient(base_url=base_url)

        # Verify model exists
        try:
            await self.client.show(self.model)
        except Exception as e:
            raise PluginInitializationError(f"Model {self.model} not available: {e}")

    async def cleanup(self) -> None:
        self.client = None

    async def chat(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        tools: Optional[List[Tool]] = None
    ) -> AsyncIterator[str]:
        """Stream chat response."""
        messages = [{"role": "user", "content": message}]

        # Add context if provided
        if context and "history" in context:
            messages = context["history"] + messages

        async for chunk in await self.client.chat(
            model=self.model,
            messages=messages,
            stream=True
        ):
            yield chunk['message']['content']

    async def generate(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate complete response."""
        response = await self.client.generate(
            model=self.model,
            prompt=prompt
        )
        return response['response']

    async def execute_task(
        self,
        task: str,
        tools: List[Tool],
        max_iterations: int = 10
    ) -> Dict[str, Any]:
        """Execute task using ReAct pattern."""
        # Simplified - full implementation would have ReAct loop
        result = await self.generate(task)
        return {
            "answer": result,
            "steps": [],
            "iterations": 1
        }

    def supports_tool_calling(self) -> bool:
        return True  # Ollama supports tools

    def get_model_info(self) -> Dict[str, Any]:
        return {
            "provider": "ollama",
            "model": self.model,
            "supports_streaming": True,
            "supports_tools": True
        }
```

### 3. Shell Plugin Interface

```python
class IShellPlugin(IPlugin):
    """Interface for shell/frontend plugins."""

    @abstractmethod
    async def run(
        self,
        runtime: IRuntimePlugin,
        agent: IAgentPlugin,
        executor: ICommandExecutor
    ) -> None:
        """
        Run the shell interface.

        Args:
            runtime: Runtime plugin for command execution
            agent: Agent plugin for AI interactions
            executor: Command executor for tools
        """
        pass

    @abstractmethod
    async def display_output(self, output: str, output_type: str = "text") -> None:
        """
        Display output to user.

        Args:
            output: Output text
            output_type: Type (text, markdown, error, etc.)
        """
        pass

    @abstractmethod
    async def get_user_input(self, prompt: str = "") -> str:
        """
        Get input from user.

        Args:
            prompt: Prompt to display

        Returns:
            User input
        """
        pass

    @abstractmethod
    async def request_approval(self, command: str, context: Dict[str, Any]) -> bool:
        """
        Request user approval for command.

        Args:
            command: Command to approve
            context: Context (reasoning, risk, etc.)

        Returns:
            True if approved
        """
        pass


# Built-in implementation
class PromptShellPlugin(IShellPlugin):
    """Default terminal REPL shell plugin."""

    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="prompt_shell",
            version="1.0.0",
            plugin_type="shell",
            description="Interactive terminal shell with prompt-toolkit",
            author="AI-Shell Team"
        )

    async def initialize(self, config: Dict[str, Any]) -> None:
        from ai_shell.shell.repl import REPL, REPLConfig

        self.repl_config = REPLConfig(
            prompt=config.get("prompt", "ai> "),
            history_file=config.get("history_file", "~/.ai_shell/history"),
            auto_suggest=config.get("auto_suggest", True),
            vi_mode=config.get("vi_mode", False)
        )

        self.repl = None  # Will be created in run()

    async def cleanup(self) -> None:
        if self.repl:
            # Save history, cleanup resources
            pass

    async def run(
        self,
        runtime: IRuntimePlugin,
        agent: IAgentPlugin,
        executor: ICommandExecutor
    ) -> None:
        """Run the REPL."""
        from ai_shell.shell.repl import REPL
        from ai_shell.shell.parser import Parser
        from ai_shell.shell.renderer import Renderer
        from ai_shell.core.memory import MemoryStore

        # Create REPL with plugins
        memory = MemoryStore()
        parser = Parser()
        renderer = Renderer()

        self.repl = REPL(
            parser=parser,
            renderer=renderer,
            memory=memory,
            agent=agent,
            executor=executor,
            bash_executor=runtime,
            config=self.repl_config
        )

        # Start REPL loop
        await self.repl.start()

    async def display_output(self, output: str, output_type: str = "text") -> None:
        """Display output using renderer."""
        if self.repl:
            if output_type == "error":
                self.repl.renderer.print_error(output)
            elif output_type == "markdown":
                self.repl.renderer.render_markdown(output)
            else:
                self.repl.renderer.print_info(output)

    async def get_user_input(self, prompt: str = "") -> str:
        """Get user input."""
        if self.repl:
            return await self.repl.prompt_session.prompt_async(prompt)
        return ""

    async def request_approval(self, command: str, context: Dict[str, Any]) -> bool:
        """Request approval via prompt."""
        print(f"\n⚠️  Approval Required")
        print(f"Command: {command}")

        if "reasoning" in context:
            print(f"Reasoning: {context['reasoning']}")

        response = input("Execute? [y/N]: ")
        return response.lower() == 'y'
```

### 4. Tool Plugin Interface

```python
from ai_shell.core.interfaces import CustomFunction


class IToolPlugin(IPlugin):
    """Interface for tool plugins."""

    @abstractmethod
    def get_tools(self) -> List[CustomFunction]:
        """
        Return list of tools provided by this plugin.

        Returns:
            List of CustomFunction instances
        """
        pass

    async def on_tool_executed(self, tool_name: str, result: Any) -> None:
        """
        Callback after tool execution.

        Args:
            tool_name: Name of executed tool
            result: Execution result
        """
        pass


# Built-in implementation
class BuiltinToolsPlugin(IToolPlugin):
    """Built-in tools plugin."""

    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="builtin_tools",
            version="1.0.0",
            plugin_type="tool",
            description="Core AI-Shell tools (summarize, context management)",
            author="AI-Shell Team"
        )

    async def initialize(self, config: Dict[str, Any]) -> None:
        # Load built-in tools
        from ai_shell.commands.ai_commands import (
            summarize, add_context, clear_context, view_context
        )

        self.tools = []
        # Tools will be registered in get_tools()

    async def cleanup(self) -> None:
        pass

    def get_tools(self) -> List[CustomFunction]:
        """Return built-in tools."""
        from ai_shell.commands.ai_commands import (
            SummarizeInput, summarize,
            ContextAddSchema, add_context,
            ClearContextSchema, clear_context,
            ViewContextSchema, view_context
        )
        from ai_shell.core.interfaces import CustomFunction

        return [
            CustomFunction(
                name="summarize",
                description="Summarize the provided text",
                func=summarize,
                input_schema=SummarizeInput
            ),
            # ... other tools
        ]
```

---

## Configuration System

### Plugin Configuration Schema

```yaml
# ~/.ai_shell/config.yaml

plugins:
  # Plugin search paths
  search_paths:
    - ~/.ai_shell/plugins
    - ./ai_shell_plugins

  # Auto-load plugins on startup
  auto_load: true

  # Plugin selection (active plugins)
  active:
    runtime: native_bash          # Which runtime plugin to use
    agent: ollama_agent            # Which agent plugin to use
    shell: prompt_shell            # Which shell plugin to use
    tools:                         # Tool plugins (can have multiple)
      - builtin_tools
      - custom_tools
    parser: default_parser         # Parser plugin
    renderer: rich_renderer        # Renderer plugin

  # Plugin-specific configurations
  runtime:
    native_bash:
      shell: /bin/bash
      timeout: 300

    docker_runtime:
      default_image: ubuntu:22.04
      timeout: 300
      mount_home: true
      network: bridge

  agent:
    ollama_agent:
      base_url: http://localhost:11434
      model: llama3.1
      temperature: 0.7
      max_tokens: 4096

    openai_agent:
      api_key: ${OPENAI_API_KEY}
      model: gpt-4o
      temperature: 0.7

  shell:
    prompt_shell:
      prompt: "ai> "
      history_file: ~/.ai_shell/history
      auto_suggest: true
      vi_mode: false

    web_ui:
      host: 0.0.0.0
      port: 8080
      theme: dark

  tools:
    builtin_tools:
      enabled: true

    mcp_tools:
      enabled: true
      servers:
        filesystem:
          command: npx @modelcontextprotocol/server-filesystem /home/user
        git:
          command: npx @modelcontextprotocol/server-git
```

### Configuration Loading

```python
class PluginConfig(BaseModel):
    """Plugin configuration."""
    search_paths: List[str] = [
        "~/.ai_shell/plugins",
        "./ai_shell_plugins"
    ]
    auto_load: bool = True
    active: Dict[str, Any] = {}

    # Plugin-specific configs
    runtime: Dict[str, Dict[str, Any]] = {}
    agent: Dict[str, Dict[str, Any]] = {}
    shell: Dict[str, Dict[str, Any]] = {}
    tools: Dict[str, Dict[str, Any]] = {}


class AIShellConfig(BaseModel):
    """Extended main config with plugins."""
    # ... existing fields ...
    plugins: PluginConfig = PluginConfig()
```

---

## Plugin Discovery and Loading

### Plugin Manager Implementation

```python
# ai_shell/core/plugin_manager.py

from pathlib import Path
from typing import Dict, List, Optional, Type
import importlib.util
import yaml
from packaging.version import Version

from ai_shell.core.plugin_interfaces import (
    IPlugin, IRuntimePlugin, IAgentPlugin, IShellPlugin, IToolPlugin
)
from ai_shell.utils.errors import PluginError


class PluginManifest(BaseModel):
    """Plugin manifest from plugin.yaml."""
    name: str
    version: str
    plugin_type: str
    entry_point: str
    display_name: Optional[str] = None
    description: Optional[str] = None
    author: Optional[str] = None
    license: Optional[str] = None
    homepage: Optional[str] = None
    requires: Dict[str, str] = {}
    dependencies: List[str] = []
    system_dependencies: List[str] = []
    config_schema: Optional[Dict[str, Any]] = None
    compatible_plugins: Dict[str, List[str]] = {}
    incompatible_plugins: Dict[str, List[str]] = {}
    hooks: Dict[str, str] = {}


class PluginManager:
    """Manage plugin discovery, loading, and lifecycle."""

    def __init__(self, config: PluginConfig):
        self.config = config
        self.search_paths = [Path(p).expanduser() for p in config.search_paths]

        # Loaded plugins by type
        self.runtime_plugins: Dict[str, IRuntimePlugin] = {}
        self.agent_plugins: Dict[str, IAgentPlugin] = {}
        self.shell_plugins: Dict[str, IShellPlugin] = {}
        self.tool_plugins: Dict[str, IToolPlugin] = {}

        # Manifests
        self.manifests: Dict[str, PluginManifest] = {}

    def discover_plugins(self) -> List[PluginManifest]:
        """Discover all available plugins."""
        manifests = []

        for search_path in self.search_paths:
            if not search_path.exists():
                continue

            # Look for plugin.yaml in subdirectories
            for manifest_path in search_path.glob("*/plugin.yaml"):
                try:
                    manifest = self._load_manifest(manifest_path)
                    self._validate_manifest(manifest)
                    manifests.append(manifest)
                    self.manifests[manifest.name] = manifest
                except Exception as e:
                    logger.warning(f"Failed to load plugin manifest {manifest_path}: {e}")

        return manifests

    def _load_manifest(self, path: Path) -> PluginManifest:
        """Load plugin manifest from YAML."""
        with open(path) as f:
            data = yaml.safe_load(f)
        return PluginManifest(**data)

    def _validate_manifest(self, manifest: PluginManifest):
        """Validate plugin manifest."""
        # Check ai-shell version requirement
        if "ai_shell" in manifest.requires:
            required_version = manifest.requires["ai_shell"]
            # Compare with current ai-shell version
            # if not version_compatible(CURRENT_VERSION, required_version):
            #     raise PluginError(f"Plugin {manifest.name} requires ai-shell {required_version}")

        # Check Python version
        if "python" in manifest.requires:
            import sys
            required = Version(manifest.requires["python"].replace(">=", ""))
            current = Version(f"{sys.version_info.major}.{sys.version_info.minor}")
            if current < required:
                raise PluginError(
                    f"Plugin {manifest.name} requires Python {required}, got {current}"
                )

    async def load_plugin(self, plugin_name: str) -> IPlugin:
        """Load a plugin by name."""
        if plugin_name not in self.manifests:
            raise PluginError(f"Plugin not found: {plugin_name}")

        manifest = self.manifests[plugin_name]

        # Install dependencies if needed
        await self._install_dependencies(manifest)

        # Import module and instantiate plugin
        plugin_instance = await self._import_plugin(manifest)

        # Get plugin-specific config
        plugin_config = self._get_plugin_config(manifest)

        # Initialize plugin
        await plugin_instance.initialize(plugin_config)

        # Store in appropriate registry
        self._register_plugin(plugin_instance, manifest)

        return plugin_instance

    async def _install_dependencies(self, manifest: PluginManifest):
        """Install plugin dependencies."""
        if not manifest.dependencies:
            return

        import subprocess

        # Check if dependencies are installed
        for dep in manifest.dependencies:
            package_name = dep.split(">=")[0].split("==")[0]
            try:
                importlib.import_module(package_name)
            except ImportError:
                # Install dependency
                logger.info(f"Installing dependency: {dep}")
                subprocess.run(
                    ["pip", "install", dep],
                    check=True,
                    capture_output=True
                )

    async def _import_plugin(self, manifest: PluginManifest) -> IPlugin:
        """Import and instantiate plugin."""
        # Parse entry point: "module:ClassName"
        module_name, class_name = manifest.entry_point.split(":")

        # Find plugin directory
        plugin_dir = None
        for search_path in self.search_paths:
            candidate = search_path / manifest.name
            if candidate.exists():
                plugin_dir = candidate
                break

        if not plugin_dir:
            raise PluginError(f"Plugin directory not found: {manifest.name}")

        # Import module
        module_path = plugin_dir / f"{module_name}.py"
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Get class and instantiate
        plugin_class = getattr(module, class_name)
        return plugin_class()

    def _get_plugin_config(self, manifest: PluginManifest) -> Dict[str, Any]:
        """Get configuration for plugin."""
        plugin_type = manifest.plugin_type
        plugin_name = manifest.name

        # Get from config
        if plugin_type in self.config.__dict__:
            type_configs = getattr(self.config, plugin_type)
            if plugin_name in type_configs:
                return type_configs[plugin_name]

        return {}

    def _register_plugin(self, plugin: IPlugin, manifest: PluginManifest):
        """Register plugin in appropriate registry."""
        if manifest.plugin_type == "runtime":
            self.runtime_plugins[manifest.name] = plugin
        elif manifest.plugin_type == "agent":
            self.agent_plugins[manifest.name] = plugin
        elif manifest.plugin_type == "shell":
            self.shell_plugins[manifest.name] = plugin
        elif manifest.plugin_type == "tool":
            self.tool_plugins[manifest.name] = plugin

    async def load_active_plugins(self):
        """Load all active plugins from config."""
        active = self.config.active

        # Load runtime plugin
        if "runtime" in active:
            await self.load_plugin(active["runtime"])

        # Load agent plugin
        if "agent" in active:
            await self.load_plugin(active["agent"])

        # Load shell plugin
        if "shell" in active:
            await self.load_plugin(active["shell"])

        # Load tool plugins
        if "tools" in active:
            for tool_plugin in active["tools"]:
                await self.load_plugin(tool_plugin)

    def get_active_runtime(self) -> IRuntimePlugin:
        """Get active runtime plugin."""
        active_name = self.config.active.get("runtime")
        if not active_name or active_name not in self.runtime_plugins:
            raise PluginError("No active runtime plugin")
        return self.runtime_plugins[active_name]

    def get_active_agent(self) -> IAgentPlugin:
        """Get active agent plugin."""
        active_name = self.config.active.get("agent")
        if not active_name or active_name not in self.agent_plugins:
            raise PluginError("No active agent plugin")
        return self.agent_plugins[active_name]

    def get_active_shell(self) -> IShellPlugin:
        """Get active shell plugin."""
        active_name = self.config.active.get("shell")
        if not active_name or active_name not in self.shell_plugins:
            raise PluginError("No active shell plugin")
        return self.shell_plugins[active_name]

    def get_all_tools(self) -> List[CustomFunction]:
        """Get all tools from all tool plugins."""
        tools = []
        for tool_plugin in self.tool_plugins.values():
            tools.extend(tool_plugin.get_tools())
        return tools

    async def cleanup_all(self):
        """Cleanup all loaded plugins."""
        all_plugins = (
            list(self.runtime_plugins.values()) +
            list(self.agent_plugins.values()) +
            list(self.shell_plugins.values()) +
            list(self.tool_plugins.values())
        )

        for plugin in all_plugins:
            try:
                await plugin.cleanup()
            except Exception as e:
                logger.error(f"Error cleaning up plugin: {e}")
```

---

## Implementation Plan

### Phase 1: Core Plugin Infrastructure (Week 1)

**Tasks**:
1. Create plugin interfaces (`ai_shell/core/plugin_interfaces.py`)
2. Create plugin manager (`ai_shell/core/plugin_manager.py`)
3. Update config system to support plugins
4. Add plugin discovery and validation

**Files to Create**:
- `ai_shell/core/plugin_interfaces.py`
- `ai_shell/core/plugin_manager.py`
- `ai_shell/plugins/builtin/` (directory for built-in plugins)

### Phase 2: Convert Current Code to Plugins (Week 2)

**Tasks**:
1. Create built-in runtime plugins:
   - `NativeBashRuntimePlugin` (from `BashExecutor`)
   - `DockerRuntimePlugin` (from `DockerBashExecutor`)
   - `MockRuntimePlugin` (from `MockBashExecutor`)

2. Create built-in agent plugins:
   - `OllamaAgentPlugin` (from `OllamaAgent`)
   - `MockAgentPlugin` (from `MockAgent`)

3. Create built-in shell plugin:
   - `PromptShellPlugin` (from `REPL`)

4. Create built-in tool plugin:
   - `BuiltinToolsPlugin` (from `ai_commands.py`)

**Files to Create**:
```
ai_shell/plugins/builtin/
├── runtime/
│   ├── native_bash/
│   │   ├── plugin.yaml
│   │   └── plugin.py
│   ├── docker/
│   │   ├── plugin.yaml
│   │   └── plugin.py
│   └── mock/
│       ├── plugin.yaml
│       └── plugin.py
├── agent/
│   ├── ollama/
│   │   ├── plugin.yaml
│   │   └── plugin.py
│   └── mock/
│       ├── plugin.yaml
│       └── plugin.py
├── shell/
│   └── prompt/
│       ├── plugin.yaml
│       └── plugin.py
└── tools/
    └── builtin/
        ├── plugin.yaml
        └── plugin.py
```

### Phase 3: Main Entry Point Integration (Week 3)

**Tasks**:
1. Update `__main__.py` to use PluginManager
2. Load plugins from config
3. Initialize AI-Shell with plugins
4. Test all plugin combinations

**Updated `__main__.py`**:
```python
async def main():
    # Parse args
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", help="Config file path")
    args = parser.parse_args()

    # Load configuration
    config = AIShellConfig.load(args.config)

    # Setup logging
    setup_logging(config)

    # Create plugin manager
    plugin_manager = PluginManager(config.plugins)

    # Discover plugins
    plugins = plugin_manager.discover_plugins()
    logger.info(f"Discovered {len(plugins)} plugins")

    # Load active plugins
    await plugin_manager.load_active_plugins()

    # Get active plugins
    runtime = plugin_manager.get_active_runtime()
    agent = plugin_manager.get_active_agent()
    shell = plugin_manager.get_active_shell()

    # Create command executor with tools from plugins
    executor = CommandExecutor()
    for tool in plugin_manager.get_all_tools():
        executor.register_function(tool)

    # Run shell
    try:
        await shell.run(runtime, agent, executor)
    finally:
        await plugin_manager.cleanup_all()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

### Phase 4: Documentation and Examples (Week 4)

**Tasks**:
1. Write plugin development guide
2. Create example plugins:
   - SSH runtime plugin
   - OpenAI agent plugin
   - Web UI shell plugin
3. Create plugin testing guide
4. Document plugin API

---

## Plugin Development Guide

### Creating a Custom Runtime Plugin

**Example: SSH Runtime Plugin**

**Directory Structure**:
```
~/.ai_shell/plugins/ssh_runtime/
├── plugin.yaml
├── plugin.py
├── requirements.txt
└── README.md
```

**plugin.yaml**:
```yaml
name: ssh_runtime
version: 1.0.0
plugin_type: runtime
entry_point: plugin:SSHRuntimePlugin

display_name: SSH Runtime
description: Execute commands on remote machine via SSH
author: Your Name
license: MIT

requires:
  ai_shell: ">=0.2.0"
  python: ">=3.11"

dependencies:
  - paramiko>=3.0.0

config_schema:
  type: object
  properties:
    host:
      type: string
      description: SSH host
    port:
      type: integer
      default: 22
    username:
      type: string
    key_file:
      type: string
      description: Path to SSH private key
```

**plugin.py**:
```python
from ai_shell.core.plugin_interfaces import IRuntimePlugin, PluginMetadata
from ai_shell.core.interfaces import CommandResult
from ai_shell.utils.errors import PluginInitializationError
from typing import Dict, Any, Optional, AsyncIterator
import paramiko
import asyncio


class SSHRuntimePlugin(IRuntimePlugin):
    """Execute commands on remote machine via SSH."""

    def __init__(self):
        self.client = None
        self.host = None
        self.port = 22
        self.username = None
        self.key_file = None

    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="ssh_runtime",
            version="1.0.0",
            plugin_type="runtime",
            description="Execute commands on remote machine via SSH",
            author="Your Name"
        )

    async def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize SSH connection."""
        self.host = config.get("host")
        self.port = config.get("port", 22)
        self.username = config.get("username")
        self.key_file = config.get("key_file")

        if not self.host or not self.username:
            raise PluginInitializationError("SSH runtime requires 'host' and 'username'")

        # Create SSH client
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # Connect
        try:
            self.client.connect(
                hostname=self.host,
                port=self.port,
                username=self.username,
                key_filename=self.key_file
            )
        except Exception as e:
            raise PluginInitializationError(f"Failed to connect to SSH: {e}")

    async def cleanup(self) -> None:
        """Close SSH connection."""
        if self.client:
            self.client.close()

    async def execute(
        self,
        command: str,
        input_data: Optional[bytes] = None,
        timeout: int = 30,
        env: Optional[Dict[str, str]] = None,
        working_dir: Optional[str] = None
    ) -> CommandResult:
        """Execute command via SSH."""
        if not self.client:
            return CommandResult(
                success=False,
                output="",
                error="SSH client not initialized"
            )

        try:
            # Build command with cd if working_dir specified
            if working_dir:
                command = f"cd {working_dir} && {command}"

            # Execute command
            stdin, stdout, stderr = self.client.exec_command(
                command,
                timeout=timeout
            )

            # Write stdin if provided
            if input_data:
                stdin.write(input_data)
                stdin.close()

            # Read output
            output = stdout.read().decode()
            error = stderr.read().decode()
            exit_code = stdout.channel.recv_exit_status()

            return CommandResult(
                success=exit_code == 0,
                output=output,
                error=error
            )

        except Exception as e:
            return CommandResult(
                success=False,
                output="",
                error=str(e)
            )

    async def execute_streaming(
        self,
        command: str,
        input_data: Optional[bytes] = None,
        env: Optional[Dict[str, str]] = None,
        working_dir: Optional[str] = None
    ) -> AsyncIterator[bytes]:
        """Stream command output via SSH."""
        if working_dir:
            command = f"cd {working_dir} && {command}"

        stdin, stdout, stderr = self.client.exec_command(command)

        if input_data:
            stdin.write(input_data)
            stdin.close()

        # Stream output
        while True:
            chunk = stdout.read(1024)
            if not chunk:
                break
            yield chunk

    async def get_environment_info(self) -> Dict[str, Any]:
        """Get remote environment info."""
        result = await self.execute("uname -a && whoami && pwd")
        return {
            "remote": True,
            "host": self.host,
            "info": result.output
        }
```

**requirements.txt**:
```
paramiko>=3.0.0
```

**Configuration** (in `~/.ai_shell/config.yaml`):
```yaml
plugins:
  active:
    runtime: ssh_runtime  # Use SSH runtime instead of native bash

  runtime:
    ssh_runtime:
      host: myserver.example.com
      username: myuser
      key_file: ~/.ssh/id_rsa
```

**Usage**:
```bash
# All commands now execute on remote machine!
ai> !ls -la
ai> !cat /etc/hostname
ai> \summarize remote_file.txt
```

---

## Example Plugins

### 1. OpenAI Agent Plugin

```python
# ~/.ai_shell/plugins/openai_agent/plugin.py

from ai_shell.core.plugin_interfaces import IAgentPlugin, PluginMetadata
from typing import Dict, Any, List, AsyncIterator, Optional
from openai import AsyncOpenAI


class OpenAIAgentPlugin(IAgentPlugin):
    """OpenAI GPT agent plugin."""

    def __init__(self):
        self.client = None
        self.model = "gpt-4o"

    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="openai_agent",
            version="1.0.0",
            plugin_type="agent",
            description="OpenAI GPT-4 agent",
            author="AI-Shell Community"
        )

    async def initialize(self, config: Dict[str, Any]) -> None:
        api_key = config.get("api_key")
        if not api_key:
            raise PluginInitializationError("OpenAI API key required")

        self.model = config.get("model", "gpt-4o")
        self.client = AsyncOpenAI(api_key=api_key)

    async def cleanup(self) -> None:
        await self.client.close()

    async def chat(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        tools: Optional[List[Tool]] = None
    ) -> AsyncIterator[str]:
        """Stream chat response."""
        messages = [{"role": "user", "content": message}]

        stream = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            stream=True
        )

        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    # ... implement other methods
```

### 2. Web UI Shell Plugin

```python
# ~/.ai_shell/plugins/web_ui/plugin.py

from ai_shell.core.plugin_interfaces import IShellPlugin, PluginMetadata
from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
import uvicorn


class WebUIShellPlugin(IShellPlugin):
    """Web-based UI shell plugin."""

    def __init__(self):
        self.app = FastAPI()
        self.runtime = None
        self.agent = None
        self.executor = None

    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="web_ui",
            version="1.0.0",
            plugin_type="shell",
            description="Web-based user interface",
            author="AI-Shell Community"
        )

    async def initialize(self, config: Dict[str, Any]) -> None:
        self.host = config.get("host", "0.0.0.0")
        self.port = config.get("port", 8080)

        # Setup routes
        @self.app.get("/")
        async def get_ui():
            return HTMLResponse(self._get_html())

        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            await self._handle_websocket(websocket)

    async def run(
        self,
        runtime: IRuntimePlugin,
        agent: IAgentPlugin,
        executor: ICommandExecutor
    ) -> None:
        """Run web server."""
        self.runtime = runtime
        self.agent = agent
        self.executor = executor

        config = uvicorn.Config(
            self.app,
            host=self.host,
            port=self.port,
            log_level="info"
        )
        server = uvicorn.Server(config)
        await server.serve()

    def _get_html(self) -> str:
        """Return HTML UI."""
        return """
        <!DOCTYPE html>
        <html>
        <head><title>AI-Shell Web UI</title></head>
        <body>
            <h1>AI-Shell</h1>
            <div id="output"></div>
            <input id="input" type="text" />
            <script>
                const ws = new WebSocket('ws://localhost:8080/ws');
                ws.onmessage = (event) => {
                    document.getElementById('output').innerHTML += event.data;
                };
                document.getElementById('input').addEventListener('keypress', (e) => {
                    if (e.key === 'Enter') {
                        ws.send(e.target.value);
                        e.target.value = '';
                    }
                });
            </script>
        </body>
        </html>
        """
```

---

## Summary

This plugin system design provides:

1. **Complete Flexibility**: Every component can be replaced
2. **Built-in Defaults**: Current code becomes default plugins
3. **Easy Extension**: Simple interface for new plugins
4. **Configuration-Driven**: Change behavior via config files
5. **Professional Architecture**: Lifecycle management, dependencies, validation

**Next Steps**:
1. Implement core plugin infrastructure (Phase 1)
2. Convert current code to built-in plugins (Phase 2)
3. Update main entry point (Phase 3)
4. Create example plugins (Phase 4)

This transforms AI-Shell from a monolithic application into a true plugin ecosystem!
