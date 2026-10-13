# AI-Shell: Iterative Implementation Plan

**Version:** 1.0
**Date:** 2025-12-29

This document provides actionable, week-by-week implementation tasks for the AI-Shell improvement roadmap. Each task includes specific files to create/modify, code examples, and acceptance criteria.

---

## Quick Reference

| Phase | Duration | Focus Area | Priority |
|-------|----------|------------|----------|
| Phase 1 | 2-3 weeks | Foundation Hardening | ⭐⭐⭐⭐⭐ Critical |
| Phase 2 | 3-4 weeks | Agent Capabilities | ⭐⭐⭐⭐⭐ Critical |
| Phase 3 | 3-4 weeks | Ecosystem Integration | ⭐⭐⭐⭐ High |
| Phase 4 | 4-5 weeks | Advanced Features | ⭐⭐⭐ Medium |

---

## Phase 1: Foundation Hardening

### Week 1, Day 1-2: Configuration System

#### Task 1.1: Create Configuration Schema

**Files to Create**:
```
ai_shell/config/__init__.py
ai_shell/config/config.py
ai_shell/config/defaults.yaml
```

**ai_shell/config/config.py**:
```python
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from pathlib import Path
import yaml
import os


class ModelConfig(BaseModel):
    """Model configuration."""
    provider: str = Field(default="ollama", description="LLM provider (ollama, openai, anthropic)")
    name: str = Field(default="llama3.1", description="Model name")
    base_url: str = Field(default="http://localhost:11434", description="API base URL")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=4096, ge=1)
    api_key: Optional[str] = Field(default=None, description="API key for cloud providers")


class ShellConfig(BaseModel):
    """Shell configuration."""
    prompt: str = Field(default="ai> ", description="Shell prompt")
    history_file: str = Field(default="~/.ai_shell/history", description="Command history file")
    auto_suggest: bool = Field(default=True, description="Enable auto-suggestions")
    vi_mode: bool = Field(default=False, description="Enable vi keybindings")
    multiline: bool = Field(default=False, description="Enable multiline input")


class ToolsConfig(BaseModel):
    """Tools configuration."""
    builtin_enabled: bool = Field(default=True, description="Enable built-in tools")
    custom_paths: List[str] = Field(default_factory=list, description="Custom tool directories")


class ApprovalConfig(BaseModel):
    """Human-in-the-loop approval configuration."""
    enabled: bool = Field(default=True, description="Enable approval system")
    safe_commands: List[str] = Field(
        default_factory=lambda: ["ls", "cat", "echo", "pwd", "which", "grep", "find"],
        description="Commands that don't require approval"
    )
    dangerous_patterns: List[str] = Field(
        default_factory=lambda: ["rm -rf /", "dd if=", "mkfs", "> /dev/sd"],
        description="Patterns that are always blocked"
    )
    show_risk_level: bool = Field(default=True, description="Show risk assessment")
    allow_dry_run: bool = Field(default=True, description="Allow dry-run mode")


class MemoryConfig(BaseModel):
    """Memory and persistence configuration."""
    db_path: str = Field(default="~/.ai_shell/history.db", description="SQLite database path")
    max_conversation_history: int = Field(default=50, description="Max messages to keep in memory")
    save_sessions: bool = Field(default=True, description="Save sessions to disk")


class MCPServerConfig(BaseModel):
    """MCP server configuration."""
    command: str = Field(description="Command to start MCP server")
    enabled: bool = Field(default=True, description="Enable this server")


class LoggingConfig(BaseModel):
    """Logging configuration."""
    level: str = Field(default="INFO", description="Log level (DEBUG, INFO, WARNING, ERROR)")
    file: str = Field(default="~/.ai_shell/logs/ai-shell.log", description="Log file path")
    format: str = Field(default="json", description="Log format (json, text)")
    audit_commands: bool = Field(default=True, description="Audit log all executed commands")


class AIShellConfig(BaseModel):
    """Main configuration for AI-Shell."""
    model: ModelConfig = Field(default_factory=ModelConfig)
    shell: ShellConfig = Field(default_factory=ShellConfig)
    tools: ToolsConfig = Field(default_factory=ToolsConfig)
    approval: ApprovalConfig = Field(default_factory=ApprovalConfig)
    memory: MemoryConfig = Field(default_factory=MemoryConfig)
    mcp_servers: Dict[str, MCPServerConfig] = Field(default_factory=dict)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)

    @classmethod
    def load(cls, config_path: Optional[str] = None) -> "AIShellConfig":
        """
        Load configuration from file with environment variable overrides.

        Priority:
        1. Environment variables (AI_SHELL_*)
        2. Config file (specified or default locations)
        3. Default values
        """
        # Try config paths in order
        search_paths = []
        if config_path:
            search_paths.append(Path(config_path))

        search_paths.extend([
            Path.cwd() / "ai-shell.config.yaml",
            Path.home() / ".ai_shell" / "config.yaml",
            Path(__file__).parent / "defaults.yaml"
        ])

        config_data = {}
        for path in search_paths:
            if path.exists():
                with open(path) as f:
                    config_data = yaml.safe_load(f) or {}
                break

        # Apply environment variable overrides
        config_data = cls._apply_env_overrides(config_data)

        return cls(**config_data)

    @classmethod
    def _apply_env_overrides(cls, config_data: Dict) -> Dict:
        """Apply environment variable overrides."""
        # Model overrides
        if os.getenv("AI_SHELL_MODEL_PROVIDER"):
            config_data.setdefault("model", {})["provider"] = os.getenv("AI_SHELL_MODEL_PROVIDER")
        if os.getenv("AI_SHELL_MODEL_NAME"):
            config_data.setdefault("model", {})["name"] = os.getenv("AI_SHELL_MODEL_NAME")
        if os.getenv("AI_SHELL_MODEL_API_KEY"):
            config_data.setdefault("model", {})["api_key"] = os.getenv("AI_SHELL_MODEL_API_KEY")

        # Shell overrides
        if os.getenv("AI_SHELL_PROMPT"):
            config_data.setdefault("shell", {})["prompt"] = os.getenv("AI_SHELL_PROMPT")

        # Logging overrides
        if os.getenv("AI_SHELL_LOG_LEVEL"):
            config_data.setdefault("logging", {})["level"] = os.getenv("AI_SHELL_LOG_LEVEL")

        return config_data

    def save(self, path: str):
        """Save configuration to YAML file."""
        path = Path(path).expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, 'w') as f:
            yaml.dump(self.model_dump(), f, default_flow_style=False)
```

**ai_shell/config/defaults.yaml**:
```yaml
model:
  provider: ollama
  name: llama3.1
  base_url: http://localhost:11434
  temperature: 0.7
  max_tokens: 4096

shell:
  prompt: "ai> "
  history_file: ~/.ai_shell/history
  auto_suggest: true
  vi_mode: false
  multiline: false

tools:
  builtin_enabled: true
  custom_paths: []

approval:
  enabled: true
  safe_commands:
    - ls
    - cat
    - echo
    - pwd
    - which
    - grep
    - find
    - head
    - tail
  dangerous_patterns:
    - "rm -rf /"
    - "dd if="
    - "mkfs"
    - "> /dev/sd"
  show_risk_level: true
  allow_dry_run: true

memory:
  db_path: ~/.ai_shell/history.db
  max_conversation_history: 50
  save_sessions: true

mcp_servers: {}

logging:
  level: INFO
  file: ~/.ai_shell/logs/ai-shell.log
  format: json
  audit_commands: true
```

**Acceptance Criteria**:
- [ ] Config loads from defaults.yaml
- [ ] Config loads from ~/.ai_shell/config.yaml if exists
- [ ] Environment variables override config values
- [ ] Config validation works (invalid values rejected)
- [ ] Can save config to file

---

#### Task 1.2: Integrate Config into Main

**Files to Modify**:
- `ai_shell/__main__.py`

**Changes**:
```python
import argparse
from ai_shell.config.config import AIShellConfig

def main():
    parser = argparse.ArgumentParser(description="AI-enhanced shell")
    parser.add_argument("--config", help="Path to config file")
    parser.add_argument("--bash-backend", choices=["native", "docker", "docker-rw", "mock"],
                       default="native", help="Bash execution backend")
    args = parser.parse_args()

    # Load configuration
    config = AIShellConfig.load(args.config)

    # Override bash backend from CLI if provided
    bash_backend = args.bash_backend

    # Initialize components with config
    from ai_shell.shell.repl import REPL, REPLConfig
    from ai_shell.shell.parser import Parser
    from ai_shell.shell.renderer import Renderer
    from ai_shell.core.memory import MemoryStore
    # ... rest of initialization using config values
```

**Acceptance Criteria**:
- [ ] `python -m ai_shell` loads default config
- [ ] `python -m ai_shell --config custom.yaml` loads custom config
- [ ] `AI_SHELL_MODEL_NAME=llama3.2 python -m ai_shell` uses environment override
- [ ] Config values propagate to REPL, agent, executor

---

### Week 1, Day 3-5: Error Handling and Logging

#### Task 1.3: Custom Exception Hierarchy

**Files to Create**:
- `ai_shell/utils/errors.py`

**Code**:
```python
"""Custom exceptions for ai-shell."""


class AIShellError(Exception):
    """Base exception for all ai-shell errors."""
    pass


class ConfigurationError(AIShellError):
    """Configuration-related errors."""
    pass


class ParserError(AIShellError):
    """Input parsing errors."""
    pass


class ExecutionError(AIShellError):
    """Command execution errors."""
    pass


class BashExecutionError(ExecutionError):
    """Bash command execution errors."""
    def __init__(self, command: str, exit_code: int, stderr: str):
        self.command = command
        self.exit_code = exit_code
        self.stderr = stderr
        super().__init__(f"Bash command failed with exit code {exit_code}: {command}\n{stderr}")


class ToolExecutionError(ExecutionError):
    """Tool execution errors."""
    def __init__(self, tool_name: str, error: str):
        self.tool_name = tool_name
        self.error = error
        super().__init__(f"Tool '{tool_name}' failed: {error}")


class AgentError(AIShellError):
    """Agent execution errors."""
    pass


class MCPError(AIShellError):
    """MCP-related errors."""
    pass


class PluginError(AIShellError):
    """Plugin loading/execution errors."""
    pass


class ApprovalDeniedError(ExecutionError):
    """User denied approval for command."""
    pass
```

**Acceptance Criteria**:
- [ ] All exceptions inherit from AIShellError
- [ ] Exceptions include helpful context
- [ ] Can catch specific error types

---

#### Task 1.4: Structured Logging

**Files to Create**:
- `ai_shell/utils/logging.py`

**Code**:
```python
"""Structured logging for ai-shell."""

import logging
import json
from pathlib import Path
from datetime import datetime
from typing import Optional


class JSONFormatter(logging.Formatter):
    """Format log records as JSON."""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields
        if hasattr(record, "command"):
            log_data["command"] = record.command
        if hasattr(record, "duration"):
            log_data["duration"] = record.duration
        if hasattr(record, "user"):
            log_data["user"] = record.user

        return json.dumps(log_data)


class AuditLogger:
    """Audit logger for command execution."""

    def __init__(self, log_file: str):
        self.log_file = Path(log_file).expanduser()
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

        self.logger = logging.getLogger("ai_shell.audit")
        self.logger.setLevel(logging.INFO)

        handler = logging.FileHandler(self.log_file)
        handler.setFormatter(JSONFormatter())
        self.logger.addHandler(handler)

    def log_command(
        self,
        command_type: str,
        command: str,
        success: bool,
        duration: float,
        output: Optional[str] = None,
        error: Optional[str] = None
    ):
        """Log command execution."""
        extra = {
            "command": command,
            "duration": duration,
            "command_type": command_type,
            "success": success
        }

        if output:
            extra["output_length"] = len(output)
        if error:
            extra["error"] = error

        if success:
            self.logger.info(f"Command executed: {command}", extra=extra)
        else:
            self.logger.warning(f"Command failed: {command}", extra=extra)


def setup_logging(config):
    """Setup logging based on configuration."""
    log_file = Path(config.logging.file).expanduser()
    log_file.parent.mkdir(parents=True, exist_ok=True)

    # Root logger
    logger = logging.getLogger("ai_shell")
    logger.setLevel(getattr(logging, config.logging.level.upper()))

    # File handler
    file_handler = logging.FileHandler(log_file)

    if config.logging.format == "json":
        file_handler.setFormatter(JSONFormatter())
    else:
        file_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        )

    logger.addHandler(file_handler)

    # Console handler (only WARNING and above)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
    logger.addHandler(console_handler)

    return logger
```

**Files to Modify**:
- `ai_shell/__main__.py` - Add `setup_logging(config)`

**Acceptance Criteria**:
- [ ] Logs written to configured file
- [ ] JSON format works
- [ ] Text format works
- [ ] Audit logger tracks commands
- [ ] Log levels work correctly

---

### Week 2: Variable System

#### Task 2.1: Extend MemoryStore for Variables

**Files to Modify**:
- `ai_shell/core/memory.py`

**Changes to Add**:
```python
class MemoryStore:
    """Memory store for history and variables."""

    def __init__(self, db_path: str = "~/.ai_shell/history.db"):
        self.history: List[str] = []
        self.variables: Dict[str, str] = {}  # Add variable storage
        self.special_vars = {  # Special read-only variables
            "$pwd": lambda: os.getcwd(),
            "$user": lambda: os.getenv("USER", "unknown"),
            "$home": lambda: os.path.expanduser("~"),
        }

    def set_variable(self, name: str, value: str):
        """Set a variable value."""
        if not name.startswith("$"):
            name = "$" + name

        # Don't allow overwriting special variables
        if name in self.special_vars:
            raise ValueError(f"Cannot override special variable: {name}")

        self.variables[name] = value

    def get_variable(self, name: str) -> Optional[str]:
        """Get a variable value."""
        if not name.startswith("$"):
            name = "$" + name

        # Check special variables first
        if name in self.special_vars:
            return self.special_vars[name]()

        return self.variables.get(name)

    def expand_variables(self, text: str) -> str:
        """Expand variables in text."""
        import re

        def replace_var(match):
            var_name = match.group(0)
            value = self.get_variable(var_name)
            return value if value is not None else var_name

        # Match $varname or ${varname}
        pattern = r'\$\{?[a-zA-Z_][a-zA-Z0-9_]*\}?'
        return re.sub(pattern, replace_var, text)

    def list_variables(self) -> Dict[str, str]:
        """List all variables and their values."""
        all_vars = dict(self.variables)

        # Add special variables
        for name, getter in self.special_vars.items():
            all_vars[name] = getter()

        return all_vars

    def clear_variables(self):
        """Clear all user-defined variables."""
        self.variables.clear()
```

**Acceptance Criteria**:
- [ ] Can set variables: `memory.set_variable("$test", "value")`
- [ ] Can get variables: `memory.get_variable("$test")`
- [ ] Can expand variables: `memory.expand_variables("echo $test")`
- [ ] Special variables work ($pwd, $user, $home)
- [ ] Cannot override special variables

---

#### Task 2.2: Add Variable Assignment to Parser

**Files to Modify**:
- `ai_shell/shell/parser.py`

**Add to ParsedCommand**:
```python
@dataclass
class ParsedCommand:
    # ... existing fields ...
    variable_assignment: Optional[str] = None  # Variable to assign output to
```

**Add to Parser**:
```python
class Parser:
    def parse(self, user_input: str) -> ParsedCommand:
        """Parse user input into a command."""
        user_input = user_input.strip()

        # Check for variable assignment: cmd > $var
        variable_assignment = None
        if " > $" in user_input:
            parts = user_input.split(" > $", 1)
            user_input = parts[0].strip()
            variable_assignment = "$" + parts[1].strip()

        # Expand variables in input
        if self.memory:
            user_input = self.memory.expand_variables(user_input)

        # ... rest of existing parsing logic ...

        # Add variable_assignment to result
        command.variable_assignment = variable_assignment
        return command
```

**Acceptance Criteria**:
- [ ] Parses: `!ls > $files`
- [ ] Parses: `\summarize doc.txt > $summary`
- [ ] Variables expanded before execution
- [ ] Invalid syntax rejected

---

#### Task 2.3: Handle Variable Assignment in REPL

**Files to Modify**:
- `ai_shell/shell/repl.py`

**Changes in command handlers**:
```python
async def _handle_bash(self, command):
    """Handle bash using bash executor interface."""
    self.state = SessionState.EXECUTING

    try:
        result = await self.bash_executor.execute(command.command)

        if result.success:
            self.renderer.print_info(result.output)

            # Store in $last
            self.memory.set_variable("$last", result.output)

            # Store in named variable if specified
            if command.variable_assignment:
                self.memory.set_variable(command.variable_assignment, result.output)
                self.renderer.print_debug(
                    f"Stored output in {command.variable_assignment}"
                )
        else:
            self.renderer.print_error(result.error)

        self.state = SessionState.READY

    except Exception as e:
        # ... error handling ...
```

**Add meta command for variables**:
```python
# In ai_shell/shell/commands.py

class MetaCommandHandler:
    async def execute(self, command: ParsedCommand):
        # ... existing commands ...

        elif command.meta_command == "vars":
            # List all variables
            variables = self.repl.memory.list_variables()
            if not variables:
                return CommandResult(success=True, message="No variables defined")

            output = "**Variables:**\n\n"
            for name, value in sorted(variables.items()):
                preview = value[:50] + "..." if len(value) > 50 else value
                output += f"- `{name}` = `{preview}`\n"

            return CommandResult(success=True, message=output)

        elif command.meta_command == "unset":
            # Unset a variable
            if not command.meta_args:
                return CommandResult(success=False, message="Usage: /unset $varname")

            var_name = command.meta_args[0]
            if var_name in self.repl.memory.variables:
                del self.repl.memory.variables[var_name]
                return CommandResult(success=True, message=f"Unset {var_name}")
            else:
                return CommandResult(success=False, message=f"Variable not found: {var_name}")
```

**Acceptance Criteria**:
- [ ] `!ls > $files` stores output in $files
- [ ] `echo $files` expands the variable
- [ ] `/vars` lists all variables
- [ ] `/unset $files` removes variable
- [ ] `$last` always has last output

---

### Week 3: Pipeline Engine

#### Task 3.1: Create Pipeline Components

**Files to Create**:
- `ai_shell/core/pipeline.py`

**Code**:
```python
"""Pipeline execution engine with async streaming."""

import asyncio
from typing import AsyncIterator, List, Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum

from ai_shell.core.interfaces import CommandResult
from ai_shell.utils.errors import ExecutionError


class PipelineStageType(Enum):
    """Type of pipeline stage."""
    BASH = "bash"
    TOOL = "tool"
    AGENT = "agent"


@dataclass
class PipelineStage:
    """Single stage in a pipeline."""
    type: PipelineStageType
    command: str
    args: List[str]
    options: Dict[str, Any]


class PipelineNode:
    """Base class for pipeline nodes."""

    async def execute(self, input_data: Optional[str] = None) -> str:
        """Execute node with optional input."""
        raise NotImplementedError


class BashNode(PipelineNode):
    """Bash command node."""

    def __init__(self, bash_executor, command: str):
        self.bash_executor = bash_executor
        self.command = command

    async def execute(self, input_data: Optional[str] = None) -> str:
        """Execute bash command."""
        input_bytes = input_data.encode() if input_data else None
        result = await self.bash_executor.execute(self.command, input_data=input_bytes)

        if not result.success:
            raise ExecutionError(f"Bash command failed: {result.error}")

        return result.output


class ToolNode(PipelineNode):
    """AI tool node."""

    def __init__(self, executor, tool_name: str, args: List[str], options: Dict[str, Any]):
        self.executor = executor
        self.tool_name = tool_name
        self.args = args
        self.options = options

    async def execute(self, input_data: Optional[str] = None) -> str:
        """Execute tool."""
        result = await self.executor.execute(
            self.tool_name,
            args=self.args,
            stdin=input_data,
            **self.options
        )

        if not result.success:
            raise ExecutionError(f"Tool '{self.tool_name}' failed: {result.error}")

        return result.output


class Pipeline:
    """Async pipeline with streaming."""

    def __init__(self, nodes: List[PipelineNode]):
        self.nodes = nodes

    async def execute(self) -> AsyncIterator[str]:
        """Execute pipeline, streaming final output."""
        current_output = None

        # Execute each stage sequentially
        for i, node in enumerate(self.nodes):
            try:
                current_output = await node.execute(current_output)
            except ExecutionError as e:
                yield f"\n[Error at stage {i+1}: {e}]\n"
                return

        # Yield final output
        if current_output:
            yield current_output


class PipelineEngine:
    """Build and execute pipelines."""

    def __init__(self, bash_executor, command_executor):
        self.bash_executor = bash_executor
        self.command_executor = command_executor

    def build_pipeline(self, stages: List[PipelineStage]) -> Pipeline:
        """Build pipeline from stages."""
        nodes = []

        for stage in stages:
            if stage.type == PipelineStageType.BASH:
                node = BashNode(self.bash_executor, stage.command)
            elif stage.type == PipelineStageType.TOOL:
                node = ToolNode(
                    self.command_executor,
                    stage.command,
                    stage.args,
                    stage.options
                )
            else:
                raise ValueError(f"Unsupported stage type: {stage.type}")

            nodes.append(node)

        return Pipeline(nodes)
```

**Acceptance Criteria**:
- [ ] Can build pipeline from stages
- [ ] Bash nodes execute correctly
- [ ] Tool nodes execute correctly
- [ ] Data flows between stages
- [ ] Errors propagate properly

---

#### Task 3.2: Integrate Pipeline Engine into REPL

**Files to Modify**:
- `ai_shell/shell/repl.py`

**Changes**:
```python
from ai_shell.core.pipeline import PipelineEngine, PipelineStage, PipelineStageType

class REPL:
    def __init__(self, ...):
        # ... existing init ...

        # Create pipeline engine
        self.pipeline_engine = PipelineEngine(self.bash_executor, self.executor)

    async def _handle_pipeline(self, command, parse=False):
        """Handle pipeline command using PipelineEngine."""
        self.state = SessionState.EXECUTING

        try:
            # Convert command.stages to PipelineStages
            stages = []
            for stage in command.stages:
                if stage.type == CommandType.BASH:
                    stage_obj = PipelineStage(
                        type=PipelineStageType.BASH,
                        command=stage.command,
                        args=[],
                        options={}
                    )
                elif stage.type == CommandType.TOOL:
                    stage_obj = PipelineStage(
                        type=PipelineStageType.TOOL,
                        command=stage.tool_name,
                        args=stage.tool_args or [],
                        options=stage.tool_options or {}
                    )
                else:
                    self.renderer.print_error(f"Cannot use {stage.type.value} in pipeline")
                    self.state = SessionState.READY
                    return

                stages.append(stage_obj)

            # Build and execute pipeline
            pipeline = self.pipeline_engine.build_pipeline(stages)

            output = ""
            async for chunk in pipeline.execute():
                output += chunk
                self.console.print(chunk, end="")

            self.console.print()  # Final newline

            # Store output
            if output:
                self.memory.set_variable("$last", output)

                # Store in named variable if specified
                if command.variable_assignment:
                    self.memory.set_variable(command.variable_assignment, output)

            self.state = SessionState.READY

        except Exception as e:
            self.renderer.print_error(f"Pipeline error: {e}")
            if self.config.debug_mode:
                import traceback
                self.renderer.print_debug(traceback.format_exc())
            self.state = SessionState.READY
```

**Acceptance Criteria**:
- [ ] Pipelines use PipelineEngine
- [ ] `!cmd | \tool` works
- [ ] `\tool | !cmd` works
- [ ] `!cmd1 | \tool | !cmd2` works
- [ ] Pipeline output stored in $last
- [ ] Pipeline output can be assigned to variable

---

## Phase 2: Agent Capabilities

*(Continuing with detailed tasks for Weeks 3-6)*

### Week 4: Agent-Tool Integration

#### Task 4.1: Convert CustomFunction to Agent Tools

**Files to Modify**:
- `ai_shell/core/command_executor.py`

**Add Method**:
```python
class CommandExecutor:
    def to_ollama_tools(self) -> List[Dict]:
        """Convert registered functions to Ollama tool format."""
        tools = []

        for name, info in self.command_info.items():
            # Get function to extract parameters
            func = self.commands[name]

            # Build tool definition
            tool = {
                "type": "function",
                "function": {
                    "name": name,
                    "description": info.description,
                    "parameters": self._extract_parameters_schema(name)
                }
            }
            tools.append(tool)

        return tools

    def _extract_parameters_schema(self, func_name: str) -> Dict:
        """Extract JSON schema for function parameters."""
        # Find the CustomFunction that created this command
        # Get its input_schema_model
        # Convert to JSON schema

        # For now, simplified version:
        return {
            "type": "object",
            "properties": {
                "input": {
                    "type": "string",
                    "description": "Input data for the tool"
                }
            }
        }
```

**Acceptance Criteria**:
- [ ] Registered functions convert to tool format
- [ ] Tool schemas are valid JSON Schema
- [ ] Descriptions are helpful

---

*(Continue with similar detailed breakdowns for remaining weeks)*

---

## Summary Checklist

### Phase 1 Deliverables
- [ ] Configuration system (YAML + env vars)
- [ ] Error handling and custom exceptions
- [ ] Structured logging (JSON + audit)
- [ ] Variable system (set, get, expand)
- [ ] Variable assignment syntax (> $var)
- [ ] Meta commands for variables (/vars, /unset)
- [ ] Pipeline engine (async streaming)
- [ ] Pipeline integration in REPL

### Phase 2 Deliverables
- [ ] Agent tool calling
- [ ] ReAct loop implementation
- [ ] Approval system (permission manager)
- [ ] Risk assessment
- [ ] Dry-run mode

### Phase 3 Deliverables
- [ ] Plugin discovery and loading
- [ ] MCP adapter (stdio)
- [ ] MCP tool integration
- [ ] Plugin system documentation

### Phase 4 Deliverables
- [ ] SQLite persistence
- [ ] Session save/restore
- [ ] LLM-based parsing (optional)
- [ ] Macros system (optional)
- [ ] Comprehensive documentation

---

**Next Steps**: Begin with Week 1, Day 1 tasks and work through systematically.
