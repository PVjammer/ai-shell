# NeMo Agent Toolkit Integration Plan

## Executive Summary

This document outlines a plan to integrate **NVIDIA NeMo Agent Toolkit (NAT)** with **ai-shell** by registering **NAT workflows as ai-shell commands**. This approach allows users to configure any NAT workflow as a shell command (e.g., `\summarize`, `\analyze_code`), combining ai-shell's interactive experience with NAT's powerful agent orchestration.

## Integration Pattern: NAT Workflows as ai-shell Commands

### Core Concept

Instead of making ai-shell a NAT frontend plugin, we take a **simpler, more flexible approach**:

- **ai-shell remains the primary application** with its existing shell interface
- **NAT workflows are registered as commands** within ai-shell
- **Users configure which workflows map to which commands**
- **Each command executes a complete NAT workflow**

### User Experience

```bash
# User types a command
ai> \summarize report.txt

# ai-shell:
#  1. Parses command (\summarize)
#  2. Looks up "summarize" in command registry
#  3. Discovers it's backed by a NAT workflow
#  4. Loads workflow config (~/.ai_shell/workflows/summarize.yml)
#  5. Executes NAT workflow with input
#  6. Streams response back to shell
#  7. Renders result with Rich markdown

# User can also use in pipelines
ai> !cat *.log | \analyze_code
ai> !ls | \summarize
ai> \research "quantum computing" | \summarize
```

## Why This Pattern?

### Advantages Over Frontend Plugin Approach

1. **Simpler Architecture**: ai-shell stays in control, NAT is a library
2. **User-Friendly**: Users don't need to know about NAT
3. **Flexible**: Mix NAT workflows, custom tools, bash, and chat
4. **Composable**: Pipelines work naturally (`!bash | \nat_workflow`)
5. **Backward Compatible**: Existing ai-shell features unchanged
6. **Configurable**: Easy to add/remove/modify workflow commands
7. **Standalone Capable**: ai-shell works without NAT installed

### When NAT is Most Valuable

- **Complex multi-step tasks**: Research, analysis, code generation
- **Multi-agent workflows**: Teams of specialized agents
- **Framework integration**: Use LangChain, LlamaIndex tools
- **MCP tools**: Access remote tool servers
- **Production workflows**: Pre-tested, optimized workflows

## Architecture

### High-Level Design

```
┌──────────────────────────────────────────────────────────────┐
│                        ai-shell                               │
│                                                                │
│  User Input: \summarize report.txt                           │
│       ↓                                                        │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  Parser                                                   │ │
│  │  Detects: CommandType.TOOL, tool_name="summarize"        │ │
│  └──────────────────────────────────────────────────────────┘ │
│       ↓                                                        │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  Command Registry (Enhanced)                              │ │
│  │                                                            │ │
│  │  Registered Commands:                                     │ │
│  │    summarize → NATWorkflowCommand                         │ │
│  │    analyze_code → NATWorkflowCommand                      │ │
│  │    research → NATWorkflowCommand                          │ │
│  │    custom_tool → PythonToolCommand (non-NAT)             │ │
│  └──────────────────────────────────────────────────────────┘ │
│       ↓                                                        │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  NATWorkflowCommand                                       │ │
│  │                                                            │ │
│  │  1. Load workflow config (YAML)                           │ │
│  │  2. Initialize NAT runtime                                │ │
│  │  3. Execute workflow with input                           │ │
│  │  4. Stream results back                                   │ │
│  └──────────────────────────────────────────────────────────┘ │
│       ↓                                                        │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  Renderer                                                  │ │
│  │  Rich markdown, syntax highlighting, streaming            │ │
│  └──────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────────┐
│              NeMo Agent Toolkit (NAT)                         │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  Workflow Runtime                                         │ │
│  │  • Load YAML config                                       │ │
│  │  • Initialize LLMs, tools, agents                         │ │
│  │  • Execute workflow (ReAct, Plan-Execute, etc.)           │ │
│  │  • Stream responses                                       │ │
│  └──────────────────────────────────────────────────────────┘ │
│                          ↓                                     │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  Functions/Tools Registry                                 │ │
│  │  • NAT built-in tools                                     │ │
│  │  • MCP tools                                              │ │
│  │  • Custom tools (@register_function)                      │ │
│  └──────────────────────────────────────────────────────────┘ │
│                          ↓                                     │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  LLM Clients                                              │ │
│  │  • Ollama (local-first)                                   │ │
│  │  • NVIDIA NIM                                             │ │
│  │  • OpenAI, Anthropic, etc.                                │ │
│  └──────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

### Component Mapping

| ai-shell Component | NAT Integration | Implementation |
|-------------------|-----------------|----------------|
| **Parser** | No change | Existing parser works as-is |
| **IToolRegistry** | Enhanced | Add NATWorkflowRegistry for NAT-backed commands |
| **ICommandExecutor** | Enhanced | Add NATWorkflowExecutor |
| **IAgent** | Optional | Chat (`?`) can optionally use NAT workflow |
| **IBashExecutor** | No change | Works independently |
| **Renderer** | No change | Renders NAT workflow output |
| **REPL** | No change | Orchestrates all components |

## Configuration System

### ai-shell Configuration (`~/.ai_shell/config.yml`)

```yaml
# ai-shell configuration with NAT workflow commands
version: 1.0

# Shell settings
shell:
  prompt: "ai> "
  history_file: "~/.ai_shell/history"
  auto_suggest: true
  bash_backend: docker
  docker_image: alpine:latest

# NAT workflow commands
nat_commands:
  summarize:
    workflow: ~/.ai_shell/workflows/summarize.yml
    description: "Summarize text, files, or URLs"
    enabled: true

  analyze_code:
    workflow: ~/.ai_shell/workflows/code_analysis.yml
    description: "Analyze code for bugs, style, and improvements"
    enabled: true

  research:
    workflow: ~/.ai_shell/workflows/research.yml
    description: "Research a topic using web search and synthesis"
    enabled: true

  translate:
    workflow: ~/.ai_shell/workflows/translate.yml
    description: "Translate text between languages"
    enabled: false  # Disabled commands don't appear in tab completion

# Chat agent (optional NAT workflow)
chat_agent:
  type: nat_workflow  # or "mock" for testing
  workflow: ~/.ai_shell/workflows/chat.yml
```

### NAT Workflow Configuration (`~/.ai_shell/workflows/summarize.yml`)

```yaml
# NAT workflow for summarization
name: summarize
description: Summarize text or files

functions:
  read_file:
    _type: file_reader
    max_size: 10MB

  fetch_url:
    _type: url_fetcher
    timeout: 30

  text_summarizer:
    _type: text_summarizer
    max_length: 500
    style: bullet_points  # or "paragraph", "executive"

llms:
  ollama_llm:
    _type: ollama
    model_name: llama3.2
    base_url: http://localhost:11434
    temperature: 0.3
    max_tokens: 2000

workflow:
  _type: react_agent
  tool_names: [read_file, fetch_url, text_summarizer]
  llm_name: ollama_llm
  system_prompt: |
    You are a helpful summarization assistant.
    When given text, create concise, accurate summaries.
    Use bullet points for clarity.
  max_iterations: 5
  verbose: false
```

### NAT Workflow for Code Analysis (`~/.ai_shell/workflows/code_analysis.yml`)

```yaml
name: analyze_code
description: Analyze code for issues, style, and improvements

functions:
  read_file:
    _type: file_reader

  code_analyzer:
    _type: code_analyzer
    languages: [python, javascript, rust, go]
    checks:
      - bugs
      - style
      - security
      - performance
      - best_practices

llms:
  code_llm:
    _type: ollama
    model_name: codellama:13b
    temperature: 0.1

workflow:
  _type: react_agent
  tool_names: [read_file, code_analyzer]
  llm_name: code_llm
  system_prompt: |
    You are an expert code reviewer.
    Analyze code for bugs, style issues, security problems, and improvements.
    Provide specific, actionable feedback.
```

### NAT Workflow for Research (`~/.ai_shell/workflows/research.yml`)

```yaml
name: research
description: Research a topic using multiple sources

functions:
  web_search:
    _type: serp_api
    api_key: ${SERP_API_KEY}
    max_results: 10

  fetch_url:
    _type: url_fetcher
    timeout: 30

  synthesize:
    _type: text_synthesizer

llms:
  research_llm:
    _type: ollama
    model_name: llama3.2:70b
    temperature: 0.7

workflow:
  _type: plan_and_execute
  tool_names: [web_search, fetch_url, synthesize]
  llm_name: research_llm
  system_prompt: |
    You are a research assistant.
    Break down research questions into steps.
    Gather information from multiple sources.
    Synthesize findings into coherent summaries.
  max_steps: 10
```

## Implementation Plan

### Phase 1: Core NAT Integration (MVP)

**Goal**: Execute NAT workflows as ai-shell commands.

#### 1. Add NAT Dependency

```toml
# pyproject.toml
[project.dependencies]
# Existing
prompt-toolkit = "^3.0.0"
rich = "^13.0.0"
click = "^8.0.0"

# NAT integration (optional)
nvidia-nat = { version = "^1.2.0", optional = true }
pyyaml = "^6.0.0"  # For config files

[project.optional-dependencies]
nat = ["nvidia-nat>=1.2.0"]
nat-langchain = ["nvidia-nat[langchain]>=1.2.0"]
nat-all = ["nvidia-nat[all]>=1.2.0"]
```

#### 2. Create NAT Integration Module

```
ai_shell/integrations/
├── __init__.py
└── nat/
    ├── __init__.py
    ├── config.py           # Config loading and validation
    ├── executor.py         # NAT workflow executor
    ├── registry.py         # NAT workflow registry
    └── runtime.py          # NAT runtime management
```

#### 3. Implement Config Loader

```python
# ai_shell/integrations/nat/config.py
from pathlib import Path
from typing import Dict, Optional
from pydantic import BaseModel, Field
import yaml

class NATCommandConfig(BaseModel):
    """Configuration for a NAT workflow command."""
    workflow: str = Field(..., description="Path to NAT workflow YAML")
    description: str = Field("", description="Command description")
    enabled: bool = Field(True, description="Enable/disable command")

class AIShellConfig(BaseModel):
    """ai-shell configuration."""
    version: str = "1.0"

    class ShellConfig(BaseModel):
        prompt: str = "ai> "
        history_file: str = "~/.ai_shell/history"
        auto_suggest: bool = True
        bash_backend: str = "native"
        docker_image: str = "alpine:latest"

    shell: ShellConfig = Field(default_factory=ShellConfig)
    nat_commands: Dict[str, NATCommandConfig] = Field(default_factory=dict)

    @classmethod
    def load(cls, path: Optional[Path] = None) -> "AIShellConfig":
        """Load config from file or use defaults."""
        if path is None:
            path = Path.home() / ".ai_shell" / "config.yml"

        if not path.exists():
            # Return default config
            return cls()

        with open(path) as f:
            data = yaml.safe_load(f)

        return cls(**data)

    def get_enabled_nat_commands(self) -> Dict[str, NATCommandConfig]:
        """Get only enabled NAT commands."""
        return {
            name: config
            for name, config in self.nat_commands.items()
            if config.enabled
        }
```

#### 4. Implement NAT Workflow Executor

```python
# ai_shell/integrations/nat/executor.py
from typing import AsyncIterator, Optional
from pathlib import Path
from ai_shell.core.interfaces import CommandResult

try:
    from nat.builder.builder import Builder
    from nat.config.config import WorkflowConfig
    NAT_AVAILABLE = True
except ImportError:
    NAT_AVAILABLE = False

class NATWorkflowExecutor:
    """Executes NAT workflows."""

    def __init__(self, workflow_path: Path):
        """
        Initialize NAT workflow executor.

        Args:
            workflow_path: Path to NAT workflow YAML file
        """
        if not NAT_AVAILABLE:
            raise RuntimeError(
                "NVIDIA NeMo Agent Toolkit not installed. "
                "Install with: pip install ai-shell[nat]"
            )

        self.workflow_path = workflow_path
        self.builder: Optional[Builder] = None
        self.workflow = None

    async def initialize(self):
        """Initialize the NAT workflow."""
        # Load workflow config
        config = WorkflowConfig.from_yaml(str(self.workflow_path))

        # Create builder
        self.builder = Builder(config)
        await self.builder.initialize()

        # Get workflow instance
        self.workflow = await self.builder.get_workflow()

    async def execute(self, input_text: str) -> CommandResult:
        """
        Execute workflow with input.

        Args:
            input_text: Input text/prompt for workflow

        Returns:
            CommandResult with workflow output
        """
        if not self.workflow:
            await self.initialize()

        try:
            # Execute workflow
            result = await self.workflow.run(input_text)

            return CommandResult(
                success=True,
                output=result,
                error=""
            )
        except Exception as e:
            return CommandResult(
                success=False,
                output="",
                error=f"NAT workflow error: {e}"
            )

    async def stream(self, input_text: str) -> AsyncIterator[str]:
        """
        Execute workflow and stream results.

        Args:
            input_text: Input text/prompt for workflow

        Yields:
            Chunks of output text
        """
        if not self.workflow:
            await self.initialize()

        try:
            # Stream workflow output
            async for chunk in self.workflow.stream(input_text):
                yield chunk
        except Exception as e:
            yield f"\n[Error: NAT workflow failed: {e}]"

    async def cleanup(self):
        """Cleanup NAT resources."""
        if self.builder:
            await self.builder.cleanup()
```

#### 5. Implement NAT Command Registry

```python
# ai_shell/integrations/nat/registry.py
from typing import Dict, List, Optional
from pathlib import Path
from ai_shell.integrations.nat.executor import NATWorkflowExecutor
from ai_shell.integrations.nat.config import NATCommandConfig

class NATCommandRegistry:
    """Registry for NAT workflow commands."""

    def __init__(self):
        self.commands: Dict[str, NATWorkflowExecutor] = {}
        self.descriptions: Dict[str, str] = {}

    def register(self, name: str, config: NATCommandConfig):
        """
        Register a NAT workflow as a command.

        Args:
            name: Command name (e.g., "summarize")
            config: NAT command configuration
        """
        workflow_path = Path(config.workflow).expanduser()

        if not workflow_path.exists():
            raise FileNotFoundError(
                f"NAT workflow not found: {workflow_path}"
            )

        executor = NATWorkflowExecutor(workflow_path)
        self.commands[name] = executor
        self.descriptions[name] = config.description

    def has_command(self, name: str) -> bool:
        """Check if command is registered."""
        return name in self.commands

    def get_executor(self, name: str) -> Optional[NATWorkflowExecutor]:
        """Get executor for command."""
        return self.commands.get(name)

    def list_commands(self) -> List[str]:
        """List all registered command names."""
        return list(self.commands.keys())

    def get_description(self, name: str) -> str:
        """Get command description."""
        return self.descriptions.get(name, "")
```

#### 6. Integrate with Existing Command Executor

```python
# ai_shell/core/interfaces.py (update)
from typing import Protocol, AsyncIterator

class ICommandExecutor(Protocol):
    """Interface for command execution."""

    async def execute(self, command: str, args: List[str],
                     context: Dict = None) -> CommandResult:
        """Execute a command."""
        ...

    # New: streaming support
    async def stream(self, command: str, args: List[str],
                    context: Dict = None) -> AsyncIterator[str]:
        """Execute command and stream results."""
        ...
```

```python
# ai_shell/core/command_executor.py (new)
from typing import List, Dict, AsyncIterator
from ai_shell.core.interfaces import CommandResult, ICommandExecutor
from ai_shell.integrations.nat.registry import NATCommandRegistry

class UnifiedCommandExecutor(ICommandExecutor):
    """
    Unified command executor supporting multiple backends.

    Checks in order:
    1. NAT workflow commands
    2. Python tool commands (@tool decorated)
    3. Mock commands (for testing)
    """

    def __init__(self):
        self.nat_registry = NATCommandRegistry()
        self.python_tools = {}  # Existing @tool decorated functions
        self.mock_executor = None  # For testing

    def register_nat_command(self, name: str, config):
        """Register a NAT workflow command."""
        self.nat_registry.register(name, config)

    async def execute(self, command: str, args: List[str],
                     context: Dict = None) -> CommandResult:
        """Execute command using appropriate backend."""

        # Try NAT workflow first
        if self.nat_registry.has_command(command):
            executor = self.nat_registry.get_executor(command)
            input_text = " ".join(args) if args else ""
            return await executor.execute(input_text)

        # Try Python tool
        if command in self.python_tools:
            tool = self.python_tools[command]
            result = await tool(*args)
            return CommandResult(success=True, output=result, error="")

        # Try mock (fallback for testing)
        if self.mock_executor:
            return await self.mock_executor.execute(command, args, context)

        return CommandResult(
            success=False,
            output="",
            error=f"Unknown command: {command}"
        )

    async def stream(self, command: str, args: List[str],
                    context: Dict = None) -> AsyncIterator[str]:
        """Stream command output."""

        # NAT workflows support streaming
        if self.nat_registry.has_command(command):
            executor = self.nat_registry.get_executor(command)
            input_text = " ".join(args) if args else ""
            async for chunk in executor.stream(input_text):
                yield chunk
        else:
            # Non-streaming fallback
            result = await self.execute(command, args, context)
            if result.success:
                yield result.output
            else:
                yield f"[Error: {result.error}]"
```

#### 7. Update REPL to Use NAT Commands

```python
# ai_shell/shell/repl.py (update _handle_tool method)
async def _handle_tool(self, command):
    """Handle tool command using executor interface."""
    self.state = SessionState.EXECUTING

    try:
        # Check if executor supports streaming
        if hasattr(self.executor, 'stream'):
            # Stream the response
            self.console.print()  # Empty line before
            async for chunk in self.executor.stream(
                command.tool_name,
                command.tool_args or [],
                context={"memory": self.memory}
            ):
                self.console.print(chunk, end="", flush=True)
            self.console.print()  # Final newline
            self.console.print()  # Empty line after
        else:
            # Non-streaming fallback
            result = await self.executor.execute(
                command.tool_name,
                command.tool_args or [],
                context={"memory": self.memory}
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
```

#### 8. Update CLI Initialization

```python
# ai_shell/__main__.py (update main function)
@click.command()
@click.option('--bash-backend',
              type=click.Choice(['native', 'docker', 'docker-rw', 'mock']),
              default='native',
              help='Bash executor backend')
@click.option('--docker-image', default='alpine:latest',
              help='Docker image to use for docker backend')
@click.option('--config', type=click.Path(),
              help='Path to ai-shell config file')
def main(bash_backend, docker_image, config):
    """ai-shell: AI-enhanced interactive shell."""
    asyncio.run(async_main(bash_backend, docker_image, config))

async def async_main(bash_backend, docker_image, config_path):
    """Async main function."""

    # Load configuration
    from ai_shell.integrations.nat.config import AIShellConfig
    config = AIShellConfig.load(Path(config_path) if config_path else None)

    # Create components
    parser = Parser()
    renderer = Renderer()
    memory = MemoryStore()

    # Create bash executor
    bash_executor = create_bash_executor(bash_backend, docker_image)

    # Create unified command executor
    from ai_shell.core.command_executor import UnifiedCommandExecutor
    executor = UnifiedCommandExecutor()

    # Register NAT workflow commands
    for name, cmd_config in config.get_enabled_nat_commands().items():
        try:
            executor.register_nat_command(name, cmd_config)
            print(f"Registered NAT command: {name}")
        except Exception as e:
            print(f"Warning: Failed to register {name}: {e}")

    # Create agent (can also be NAT-backed if configured)
    agent = create_agent(config)

    # Create REPL
    repl = REPL(
        parser=parser,
        renderer=renderer,
        memory=memory,
        agent=agent,
        executor=executor,
        bash_executor=bash_executor,
        registry=executor.nat_registry,  # For tab completion
        config=REPLConfig(
            prompt=config.shell.prompt,
            history_file=config.shell.history_file,
            auto_suggest=config.shell.auto_suggest
        )
    )

    # Run shell
    await repl.start()
```

#### 9. Update Tab Completion

```python
# ai_shell/shell/completer.py (update)
class ShellCompleter(Completer):
    """Tab completion for ai-shell."""

    def __init__(self, memory: MemoryStore):
        self.memory = memory
        self.tool_names = []
        self.nat_commands = []  # New: NAT command names

    def set_nat_commands(self, commands: List[str]):
        """Set NAT command names for completion."""
        self.nat_commands = commands

    def get_completions(self, document, complete_event):
        """Get completion suggestions."""
        text = document.text_before_cursor

        # Tool completion (\command)
        if text.startswith('\\'):
            prefix = text[1:]
            # Combine Python tools and NAT commands
            all_tools = self.tool_names + self.nat_commands
            for tool in all_tools:
                if tool.startswith(prefix):
                    yield Completion(
                        tool,
                        start_position=-len(prefix),
                        display_meta=self._get_tool_description(tool)
                    )
        # ... rest of completion logic

    def _get_tool_description(self, tool: str) -> str:
        """Get tool description for display."""
        # Check NAT registry for description
        if hasattr(self, 'nat_registry'):
            desc = self.nat_registry.get_description(tool)
            if desc:
                return f"NAT: {desc}"
        return ""
```

**Success Criteria for Phase 1**:
- [ ] Load NAT workflows from config file
- [ ] Register NAT workflows as shell commands
- [ ] Execute NAT workflows from shell (`\summarize`, etc.)
- [ ] Stream NAT workflow responses to shell
- [ ] Tab completion shows NAT commands
- [ ] Pipelines work with NAT commands (`!cat file | \summarize`)
- [ ] Error handling for missing NAT or workflow files

### Phase 2: Enhanced Features

**Goal**: Add advanced NAT features and better user experience.

#### Tasks:

1. **Workflow Management Commands**
   ```python
   ai> /nat workflows list
   ai> /nat workflows reload
   ai> /nat workflows info summarize
   ai> /nat workflows enable translate
   ai> /nat workflows disable research
   ```

2. **Configuration Wizard**
   ```python
   ai> /nat setup
   # Interactive wizard to:
   # - Configure NAT commands
   # - Set up API keys
   # - Choose default LLMs
   # - Test workflows
   ```

3. **Workflow Templates**
   ```bash
   # Pre-built workflow templates
   ai> /nat template list
   ai> /nat template install summarize
   ai> /nat template create my_workflow
   ```

4. **Profiling Integration**
   ```python
   ai> /nat profile on
   ai> \summarize report.txt
   # Shows: tokens used, time taken, LLM calls, etc.
   ```

5. **Error Diagnostics**
   ```python
   # Better error messages
   ai> \summarize
   Error: NAT workflow 'summarize' failed
   Cause: Ollama not running at http://localhost:11434
   Suggestion: Start Ollama with: ollama serve
   ```

**Success Criteria**:
- [ ] Management commands work
- [ ] Configuration wizard functional
- [ ] Templates installable
- [ ] Profiling shows useful metrics
- [ ] Error messages are helpful

### Phase 3: Advanced Integration

**Goal**: Deep integration with NAT ecosystem.

#### Tasks:

1. **MCP Tool Discovery**
   ```python
   ai> /nat mcp connect http://localhost:8080
   # Auto-discover and register MCP tools as commands
   ai> \remote_search "quantum computing"
   ```

2. **Multi-Workflow Pipelines**
   ```python
   # Chain multiple NAT workflows
   ai> \research "AI safety" | \summarize | \translate spanish
   ```

3. **Workflow Composition**
   ```python
   # Create new workflows from existing ones
   ai> /nat workflow compose research+summarize -> brief_research
   ai> \brief_research "latest ML papers"
   ```

4. **Shared State Across Workflows**
   ```python
   # Workflows can access shared memory
   ai> \research "topic X"
   ai> \analyze_code  # Uses context from research
   ```

5. **Interactive Workflow Debugging**
   ```python
   ai> /nat debug on
   ai> \summarize file.txt
   # Shows each step of ReAct loop
   # [Thought] I need to read the file
   # [Action] read_file(file.txt)
   # [Observation] File contains...
   ```

**Success Criteria**:
- [ ] MCP tools discoverable and usable
- [ ] Multi-workflow pipelines work
- [ ] Workflow composition functional
- [ ] Shared state works correctly
- [ ] Debugging shows workflow steps

## Usage Examples

### Example 1: Summarization

```bash
# Configure summarize command
cat > ~/.ai_shell/config.yml << EOF
nat_commands:
  summarize:
    workflow: ~/.ai_shell/workflows/summarize.yml
    description: "Summarize text or files"
    enabled: true
EOF

# Use it
ai> \summarize README.md
📝 Summary of README.md:

• ai-shell is an AI-enhanced interactive shell
• Supports local LLMs via Ollama
• Features include bash integration, tool system, and Docker backend
• Commands use prefixes: ! (bash), ? (chat), \ (tools)
• Designed for human-in-the-loop workflows

ai> !curl https://example.com/article | \summarize
# Fetches URL and summarizes content
```

### Example 2: Code Analysis

```bash
ai> \analyze_code src/parser.py

🔍 Code Analysis for src/parser.py:

Strengths:
✓ Well-documented with comprehensive docstrings
✓ Clear separation of concerns
✓ Good error handling with custom exceptions

Issues Found:
⚠ Line 145: Regex pattern could be more efficient
⚠ Line 203: Consider using match-case (Python 3.10+)
⚠ Line 287: Magic string should be a constant

Security:
✓ No obvious security issues

Performance:
⚠ Pipeline parsing is O(n²), could be optimized

Suggestions:
• Add type hints to _parse_stages()
• Extract regex patterns to module constants
• Consider caching compiled regexes
```

### Example 3: Research Workflow

```bash
ai> \research "quantum computing trends 2025"

🔬 Research: "quantum computing trends 2025"

Step 1: Searching for sources...
Found 10 relevant sources

Step 2: Analyzing content...
• IBM Quantum roadmap
• Google's quantum supremacy update
• Academic papers on error correction
• Industry adoption trends

Step 3: Synthesizing findings...

📊 Key Trends in Quantum Computing (2025):

1. Error Correction Advances
   - Improved qubit stability
   - Surface code implementations
   - Target: 1000+ logical qubits

2. Commercial Applications
   - Drug discovery (Moderna, Roche)
   - Financial modeling (Goldman Sachs)
   - Optimization (logistics companies)

3. Hardware Development
   - Superconducting qubits (IBM, Google)
   - Trapped ions (IonQ, Honeywell)
   - Photonic quantum (Xanadu)

Sources: [10 links]
```

### Example 4: Pipeline Composition

```bash
# Complex pipeline combining bash, NAT workflows, and custom tools
ai> !find . -name "*.py" | \analyze_code | \summarize | !tee report.txt

# Breakdown:
# 1. find . -name "*.py"         → Find all Python files
# 2. \analyze_code                → Analyze each with NAT workflow
# 3. \summarize                   → Summarize findings with NAT
# 4. !tee report.txt              → Save to file and display
```

## Benefits of This Pattern

### For Users

1. **Simple Mental Model**: Commands are just commands, don't need to understand NAT
2. **Composable**: Mix bash, NAT workflows, and custom tools freely
3. **Configurable**: Easy to add/modify/remove workflow commands
4. **Transparent**: Can inspect workflow YAML configs
5. **Gradual Adoption**: Start with one NAT command, add more as needed

### For Developers

1. **Clean Architecture**: ai-shell owns the UX, NAT is a library
2. **Flexible Backend**: Can mix NAT, Python tools, and other backends
3. **Testable**: Can test with/without NAT installed
4. **Maintainable**: Clear separation of concerns
5. **Extensible**: Easy to add new command backends

### For NAT Ecosystem

1. **Great UX**: Premium interactive shell for NAT workflows
2. **Discoverability**: Users naturally discover NAT through commands
3. **Validation**: Real-world testing of NAT workflows
4. **Integration**: Bash pipelines + NAT workflows = powerful combo

## Migration Strategy

### Backward Compatibility

**Fully backward compatible**:
- NAT is optional (`pip install ai-shell[nat]`)
- Works without NAT (uses mocks or Python tools)
- No breaking changes to existing commands
- Config file is optional (sensible defaults)

### Installation Options

```bash
# Minimal (no NAT)
pip install ai-shell

# With NAT core
pip install ai-shell[nat]

# With NAT + LangChain
pip install ai-shell[nat-langchain]

# With NAT + all frameworks
pip install ai-shell[nat-all]
```

### Configuration Migration

```bash
# First time setup wizard
ai-shell
ai> /nat setup

Welcome to ai-shell NAT setup!

Do you want to use NeMo Agent Toolkit? (y/n): y
Install workflow templates? (y/n): y

Available templates:
1. summarize - Text summarization
2. code_analysis - Code review and analysis
3. research - Web research and synthesis
4. translate - Language translation

Select templates (1,2,3 or 'all'): 1,2

Installing templates...
✓ summarize → ~/.ai_shell/workflows/summarize.yml
✓ code_analysis → ~/.ai_shell/workflows/code_analysis.yml

Configuration saved to: ~/.ai_shell/config.yml

Try it out:
  ai> \summarize README.md
  ai> \analyze_code src/main.py
```

## Technical Considerations

### Dependencies

```toml
[project.dependencies]
# Core (always required)
prompt-toolkit = "^3.0.0"
rich = "^13.0.0"
click = "^8.0.0"
pyyaml = "^6.0.0"

[project.optional-dependencies]
# NAT integration
nat = [
    "nvidia-nat>=1.2.0",
]
nat-langchain = [
    "nvidia-nat[langchain]>=1.2.0",
]
nat-all = [
    "nvidia-nat[all]>=1.2.0",
]
```

### Error Handling

```python
# Graceful degradation when NAT not installed
try:
    from ai_shell.integrations.nat import NATCommandRegistry
    NAT_AVAILABLE = True
except ImportError:
    NAT_AVAILABLE = False
    # Show helpful message on first attempt to use NAT command
```

### Performance

- **Lazy Loading**: NAT workflows loaded only when first used
- **Caching**: Initialized workflows cached for reuse
- **Streaming**: Use NAT streaming to show progress
- **Async**: All NAT operations are async

### Testing

```python
# Unit tests don't require NAT
@pytest.mark.skipif(not NAT_AVAILABLE, reason="NAT not installed")
def test_nat_workflow_execution():
    # Test NAT integration
    pass

# Mock NAT for testing without dependency
class MockNATExecutor:
    async def execute(self, input_text):
        return CommandResult(success=True, output="Mock result")
```

## Timeline Estimate

| Phase | Tasks | Time | Priority |
|-------|-------|------|----------|
| Phase 1: Core Integration | Config, executor, registry, REPL updates | 1-2 weeks | High |
| Phase 2: Enhanced Features | Management commands, wizard, templates | 1 week | Medium |
| Phase 3: Advanced Integration | MCP, composition, debugging | 1-2 weeks | Low |

**Total**: 3-5 weeks for complete integration

**MVP** (Phase 1 only): 1-2 weeks

## Next Steps

1. **Create Example Config**
   ```bash
   mkdir -p ~/.ai_shell/workflows
   # Create example summarize.yml
   ```

2. **Install NAT**
   ```bash
   pip install nvidia-nat
   ```

3. **Implement Phase 1**
   - Config loading
   - NAT executor
   - Registry
   - REPL integration

4. **Test with Real Workflow**
   ```bash
   ai-shell --config ~/.ai_shell/config.yml
   ai> \summarize README.md
   ```

## Conclusion

This integration pattern provides:

✅ **Clean Architecture**: ai-shell as the shell, NAT as the backend
✅ **User-Friendly**: Simple command interface, no NAT knowledge required
✅ **Flexible**: Mix NAT, Python tools, bash, and chat
✅ **Composable**: Powerful pipeline support
✅ **Optional**: Works with or without NAT
✅ **Extensible**: Easy to add more NAT workflows

**Recommended Approach**:
1. Start with **Phase 1** (core integration)
2. Create 2-3 example workflows (summarize, code_analysis)
3. Test with real usage
4. Iterate based on feedback
5. Add Phase 2/3 features as needed

This positions ai-shell as the **premier interactive interface** for NAT workflows while maintaining its standalone value and flexibility.
