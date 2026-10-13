# AI-Shell: Comprehensive Design Document and Iterative Improvement Roadmap

**Date:** 2025-12-29
**Version:** 1.0
**Status:** Active Development

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Current Implementation Status](#current-implementation-status)
3. [Design Principles Analysis](#design-principles-analysis)
4. [Gap Analysis](#gap-analysis)
5. [Iterative Improvement Plan](#iterative-improvement-plan)
6. [Implementation Priorities](#implementation-priorities)
7. [Technical Architecture Recommendations](#technical-architecture-recommendations)
8. [Success Metrics](#success-metrics)

---

## Executive Summary

The AI-Shell project aims to create an extensible, customizable bash wrapper with LLM integration that embeds AI capabilities directly into the user's workflow. This document provides a comprehensive analysis of the current implementation against the stated design principles and outlines a detailed iterative improvement plan.

### Vision Statement (from DesignPrinciples.md)
An AI shell that serves as a bash substitute with:
- **Variable automation**: Delegate as much or as little to AI as desired
- **Easier done than said**: Mix natural language and explicit commands seamlessly
- **Customizable and Extensible**: Plugin architecture with extensive configuration
- **Embedded in Workflow**: Keep AI close to workflow, avoid context switching
- **Fun**: Enjoyable to use, build, and extend

### Current Status
The project has completed the foundational shell implementation (Phase 1 from README) with:
- ✅ Core interfaces and abstractions
- ✅ Parser for all command types (!, ?, \, /)
- ✅ Rich terminal rendering with markdown support
- ✅ Tab completion and command history
- ✅ REPL with streaming support
- ✅ Real bash execution (native + Docker backends)
- ✅ Basic command executor with CustomFunction abstraction
- ✅ Ollama agent integration

---

## Current Implementation Status

### What's Working Well ✅

#### 1. **Core Architecture**
- **Clean Interface Design** (`ai_shell/core/interfaces.py`):
  - Protocol-based interfaces (IAgent, ICommandExecutor, IBashExecutor)
  - Strong separation between shell layer and execution layer
  - Well-defined data models (CommandResult, ToolDefinition)

- **CustomFunction Abstraction**:
  - Dual-purpose functions (tools for agents + shell commands)
  - Pydantic-based input schemas with automatic parser generation
  - Clean separation between function definition and execution
  - Support for positional args, options, and stdin

#### 2. **Shell Implementation**
- **Robust Parser** (`ai_shell/shell/parser.py`):
  - Handles all prefix types (!, ?, \, /)
  - Pipeline detection and parsing
  - Auto-resolution logic (tool → bash → chat)

- **Rich Rendering** (`ai_shell/shell/renderer.py`):
  - Markdown rendering with syntax highlighting
  - Streaming output support
  - Error/info/debug formatting

- **REPL Features** (`ai_shell/shell/repl.py`):
  - Async prompt-toolkit integration
  - File history persistence
  - Tab completion for tools
  - Session state management
  - Multiple backend support (mock, real, docker)

#### 3. **Backend Flexibility**
- **Bash Executors**:
  - Native bash execution (`BashExecutor`)
  - Docker sandboxed execution (`DockerBashExecutor`, `DockerBashExecutorWithWrite`)
  - Mock for testing (`MockBashExecutor`)

- **Agent Integration**:
  - Ollama agent with streaming (`OllamaAgent`)
  - Context session management
  - Mock agent for development

#### 4. **Command System**
- **AI Commands** (`ai_shell/commands/ai_commands.py`):
  - Summarize with Ollama integration
  - Context management (add/clear/view)
  - Proper input schemas with Field descriptions

- **Command Executor** (`ai_shell/core/command_executor.py`):
  - Function registration system
  - Bash-like argument handling
  - Streaming support
  - Context session management

### What Needs Work 🚧

#### 1. **Missing Core Features from Design Principles**

##### A. **Macros System**
- **Status**: Not implemented
- **Design Goal**: "Custom Macros: Similar to functions, macros can be constructed in the shell and can range from simple (like a custom prompt) to more complex (like a pipeline of bash and custom commands)"
- **Gap**: No macro definition, storage, or execution system

##### B. **Plugin Architecture**
- **Status**: Partially implemented
- **Design Goal**: "Plugin Architecture: Available functions can be extended via plugins... Additionally, the front end supports plugins, allowing for other front ends such as a different shell, a UI, or an API server"
- **Gap**:
  - No plugin discovery mechanism
  - No plugin loading system
  - No plugin registration API
  - Frontend plugins not implemented

##### C. **LLM-based Parsing**
- **Status**: Not implemented
- **Design Goal**: "LLM-based parsing: Optional parsers can be used to help coerce the output of one function or command into the input of the next one"
- **Gap**: No AI-assisted argument filling or type coercion

##### D. **Document Ingestion**
- **Status**: Not implemented
- **Design Goal**: "Document ingestion capabilities"
- **Gap**: No RAG system, no document storage, no retrieval mechanism

##### E. **Multiple Agents**
- **Status**: Single agent only
- **Design Goal**: "Configurable Agents: The shell allows you to configure any number of agents. One agent will be the default for natural language chat, but others can be used by explicitly invoking them"
- **Gap**: No agent registry, no agent switching, no specialized agents

#### 2. **Incomplete Features**

##### A. **Pipeline Engine**
- **Current**: Basic pipeline in REPL (`_handle_pipeline`)
- **Missing**:
  - No proper PipelineEngine class (referenced in Design.md but not implemented)
  - No async streaming between stages with backpressure
  - No error propagation between stages
  - Pipelines don't support variables properly
  - No pipeline composition/nesting

##### B. **Variable System**
- **Current**: Only `$last` variable supported
- **Missing**:
  - No named variables (`$summary`, `$disk_usage`)
  - No variable assignment syntax (`> $varname`)
  - No variable expansion in commands
  - No variable persistence across sessions

##### C. **MCP Integration**
- **Status**: Skeleton only (`ai_shell/core/mcp.py` exists but minimal)
- **Missing**:
  - No stdio transport implementation
  - No tool discovery
  - No tool registration from MCP servers
  - No MCP server lifecycle management

##### D. **Human-in-the-Loop / Approval System**
- **Status**: Not implemented
- **Missing**:
  - No permission manager
  - No approval workflows
  - No risk assessment
  - No dry-run mode
  - No command classification (safe/dangerous)

##### E. **Memory and Persistence**
- **Current**: In-memory only (`MemoryStore` has SQLite references but minimal)
- **Missing**:
  - No persistent conversation history
  - No session save/restore
  - No command history search
  - No context summarization for long conversations

##### F. **Advanced Agent Capabilities**
- **Current**: Simple chat only
- **Missing**:
  - No ReAct loop implementation
  - No tool calling by agent
  - No planning mode
  - No thought-action-observation pattern
  - Agent can't invoke shell tools

#### 3. **Quality and Robustness**

##### A. **Error Handling**
- Inconsistent error handling across components
- No retry logic
- Limited error context in messages
- Some exceptions not properly caught

##### B. **Testing**
- Limited test coverage
- No integration tests for pipelines
- No tests for agent-tool interaction
- Missing evaluation tests for AI quality

##### C. **Documentation**
- Good inline docstrings
- Missing: User guide, plugin development guide, API reference
- No examples of complex workflows

##### D. **Configuration**
- No config file system
- All configuration is hard-coded or CLI args
- No user preferences
- No tool configuration

---

## Design Principles Analysis

Let's evaluate how well the current implementation aligns with each design principle:

### 1. Variable Automation ⚠️ Partial

**Principle**: "The user should be able to delegate as much or as little as they want to an LLM/Agent"

**Current State**:
- ✅ Can use explicit bash (!), AI chat (?), or tools (\)
- ✅ Auto-resolution provides flexibility
- ❌ Agent can't use tools autonomously
- ❌ No approval system to control delegation
- ❌ Can't configure "autonomy level"

**Score**: 4/10

**Recommendations**:
1. Implement approval system with configurable policies
2. Add agent-tool integration (agent can invoke tools)
3. Create "autonomy profiles" (supervised, semi-autonomous, autonomous)
4. Add command whitelisting/blacklisting per profile

### 2. Easier Done Than Said ⚠️ Partial

**Principle**: "Sometimes it is more difficult to explicitly define what you want an agent to do than it is to just do it yourself. This architecture allows the user to mix natural language interaction and LLM-powered functions with explicit command execution."

**Current State**:
- ✅ Mix of explicit (!) and AI (?, \) commands
- ✅ Can use tools directly without explaining to agent
- ❌ No LLM-based parsing to help with partial specification
- ❌ Can't do: `\jira_update_issue NB123 "filled by AI"`
- ❌ No "partial function application" with AI filling gaps

**Score**: 6/10

**Recommendations**:
1. Implement LLM-based argument parsing
2. Add "partial specification" mode for functions
3. Support hybrid: user provides some args, AI fills rest
4. Create "intent completion" for complex tools

### 3. Customizable and Extensible ✅ Good

**Principle**: "Plugin architecture with extensive configuration and customization options"

**Current State**:
- ✅ CustomFunction abstraction is excellent
- ✅ Easy to register new commands
- ✅ Clean interface for adding commands
- ⚠️ No plugin discovery/loading system
- ❌ No configuration system
- ❌ No frontend plugins

**Score**: 7/10

**Recommendations**:
1. Add plugin discovery (load from ~/.ai_shell/plugins/)
2. Create config system (YAML/TOML)
3. Support environment-based config
4. Add plugin dependency management
5. Create plugin development template

### 4. Embedded in Workflow ✅ Excellent

**Principle**: "The goal with this shell is to keep the ai capabilities as close to the user's workflow as possible. This avoids constantly switching between the terminal and a webui"

**Current State**:
- ✅ Full bash integration
- ✅ No context switching required
- ✅ Streaming makes it feel responsive
- ✅ Pipeline syntax is natural
- ✅ History and completion work well

**Score**: 9/10

**Recommendations**:
1. Add session persistence (resume interrupted work)
2. Improve variable system for workflow state
3. Add session sharing/export

### 5. Fun ✅ Good Start

**Principle**: "It should be enjoyable to use, build, and extend"

**Current State**:
- ✅ Rich terminal UI is polished
- ✅ Streaming output is satisfying
- ✅ Clean abstractions make development pleasant
- ⚠️ Limited examples of "cool" workflows
- ⚠️ No showcase of capabilities

**Score**: 7/10

**Recommendations**:
1. Create example gallery of workflows
2. Add "recipe" system for common tasks
3. Improve error messages (make them helpful/friendly)
4. Add ASCII art welcome message
5. Create tutorial/walkthrough

---

## Gap Analysis

### Critical Gaps (Must Have)

1. **Agent-Tool Integration**
   - Agent can't currently invoke shell tools
   - Blocks core use case: "AI helps with task using tools"
   - Needed for agentic workflows

2. **Pipeline Engine**
   - Current implementation is basic
   - No async streaming between stages
   - Can't handle complex pipelines
   - Needed for "easier done than said" principle

3. **Variable System**
   - Only $last supported
   - No assignment syntax
   - Blocks workflow composition
   - Needed for multi-step workflows

4. **Approval/HITL System**
   - No safety controls
   - Can't delegate with confidence
   - Blocks "variable automation" principle
   - Needed for production use

### Important Gaps (Should Have)

5. **Plugin System**
   - Can't easily add third-party tools
   - Blocks extensibility
   - Needed for ecosystem growth

6. **Configuration System**
   - Everything is hard-coded
   - Can't customize behavior
   - Blocks personalization

7. **MCP Integration**
   - Access to ecosystem tools
   - Leverage existing MCP servers
   - Competitive feature

8. **Persistent Memory**
   - Sessions don't persist
   - Can't resume work
   - Poor UX for long-running tasks

### Nice-to-Have Gaps

9. **LLM-based Parsing**
   - Would enable partial specification
   - Advanced feature
   - Can wait for later

10. **Document Ingestion**
    - RAG capabilities
    - Useful but not core
    - Can be added as plugin later

11. **Multiple Agents**
    - Specialized agents
    - Advanced feature
    - Single agent works for MVP+

12. **Macros**
    - User-defined composite commands
    - Can be approximated with plugins
    - Lower priority

---

## Iterative Improvement Plan

### Phase 1: Foundation Hardening (2-3 weeks)

**Goal**: Make current features production-ready and add critical missing pieces

#### Week 1: Core Infrastructure

**1.1 Configuration System**
- Create `ai_shell/config/config.py`
- YAML-based configuration
- Support for:
  - Model settings (provider, model name, temperature)
  - Shell settings (prompt, history path)
  - Tool settings (enabled tools, custom tool paths)
  - Approval settings (safe commands, dangerous patterns)
- Environment variable overrides
- Config file locations: `~/.ai_shell/config.yaml`, `./ai-shell.config.yaml`

**Files to Create/Modify**:
- `ai_shell/config/config.py` - Config loader and schema
- `ai_shell/config/defaults.yaml` - Default configuration
- `ai_shell/__main__.py` - Load config on startup

**Example Config**:
```yaml
model:
  provider: ollama
  name: llama3.1
  base_url: http://localhost:11434

shell:
  prompt: "ai> "
  history_file: ~/.ai_shell/history
  auto_suggest: true

tools:
  builtin_enabled: true
  custom_paths:
    - ~/.ai_shell/tools

approval:
  enabled: true
  safe_commands:
    - ls
    - cat
    - echo
  dangerous_patterns:
    - "rm -rf /"
```

**1.2 Error Handling Improvements**
- Add `ai_shell/utils/errors.py` with custom exceptions
- Consistent error handling across all components
- User-friendly error messages
- Debug mode for detailed traces

**1.3 Logging System**
- Add structured logging with `loguru` or `structlog`
- Log levels: DEBUG, INFO, WARNING, ERROR
- Log to file: `~/.ai_shell/logs/ai-shell.log`
- Audit log for executed commands

#### Week 2-3: Variable System and Pipeline Engine

**2.1 Variable System**
- Extend `MemoryStore` to support named variables
- Add variable assignment syntax: `cmd > $varname`
- Variable expansion: `$varname` in commands
- Special variables: `$last`, `$pwd`, `$user`
- Persist variables in session

**Files to Modify**:
- `ai_shell/core/memory.py` - Add variable methods
- `ai_shell/shell/parser.py` - Parse variable syntax
- `ai_shell/shell/repl.py` - Handle variable assignment/expansion

**Example Usage**:
```bash
!ls -la > $files
!du -sh * > $disk_usage
\summarize $files
?Compare $disk_usage to yesterday
```

**2.2 Enhanced Pipeline Engine**
- Create `ai_shell/core/pipeline.py`
- Async streaming with bounded queues
- Proper error propagation
- Support for variable expansion in pipelines
- Pipeline composition

**Files to Create**:
- `ai_shell/core/pipeline.py` - PipelineEngine, PipelineNode classes

**Key Features**:
```python
class PipelineEngine:
    async def execute(self, stages: List[PipelineStage]) -> AsyncIterator[str]:
        """Execute pipeline with streaming between stages."""

class BashNode(PipelineNode):
    """Bash command node."""

class ToolNode(PipelineNode):
    """AI tool node."""

class AgentNode(PipelineNode):
    """Agent reasoning node."""
```

### Phase 2: Agent Capabilities (3-4 weeks)

**Goal**: Enable agent to use tools and implement human-in-the-loop

#### Week 3-4: Agent-Tool Integration

**3.1 Tool Registry for Agent**
- Agent can discover available tools
- Tools have proper schemas for agent
- Convert CustomFunction to agent-compatible format

**Files to Modify**:
- `ai_shell/core/command_executor.py` - Add `to_agent_tools()` method
- `ai_shell/core/ollama_agent.py` - Tool calling support

**3.2 ReAct Loop Implementation**
- Thought-Action-Observation pattern
- Agent can invoke tools
- Iterative reasoning
- Max iterations limit

**Example Agent Execution**:
```python
class OllamaAgent:
    async def execute_task(self, task: str, tools: List[Tool]) -> AgentResult:
        """Execute task using ReAct loop."""
        for i in range(self.max_iterations):
            # Thought: reason about next step
            thought = await self._generate_thought(task, history)

            # Action: choose tool and args
            action = await self._generate_action(thought, tools)

            # Observation: execute tool
            result = await self._execute_tool(action)

            # Check if task complete
            if self._is_complete(result):
                return AgentResult(answer=result)
```

#### Week 5-6: Human-in-the-Loop System

**4.1 Permission Manager**
- Create `ai_shell/core/approval.py`
- Command classification (safe, dangerous, approval-required)
- Risk assessment
- Approval prompts with context

**Files to Create**:
- `ai_shell/core/approval.py` - PermissionManager

**4.2 Approval Workflow**
- Integration with bash executor
- Integration with agent
- Dry-run mode
- Approval history/audit log

**Example Approval Prompt**:
```
⚠ Approval Required

Command: rm -rf /tmp/test_data
Reasoning: User requested cleanup of test directory
Risk Level: HIGH

Options:
  [y] Execute
  [n] Cancel
  [d] Dry run
  [e] Edit command

>
```

### Phase 3: Ecosystem Integration (3-4 weeks)

**Goal**: Plugin system and MCP integration

#### Week 7-8: Plugin System

**5.1 Plugin Architecture**
- Plugin discovery from `~/.ai_shell/plugins/`
- Plugin manifest format (YAML)
- Plugin loading and registration
- Plugin dependencies

**Files to Create**:
- `ai_shell/core/plugin_manager.py` - PluginManager
- `ai_shell/core/plugin.py` - Plugin base class

**Plugin Manifest Example** (`plugin.yaml`):
```yaml
name: my_plugin
version: 1.0.0
description: My custom tools
entry_point: my_plugin.main:register_tools
dependencies:
  - requests>=2.28.0
tools:
  - name: web_search
    description: Search the web
```

**5.2 Plugin Template**
- Create plugin development template
- Documentation for plugin authors
- Example plugins (weather, calculator, etc.)

#### Week 9-10: MCP Integration

**6.1 MCP Adapter**
- Implement stdio transport in `ai_shell/core/mcp.py`
- JSON-RPC communication
- Tool discovery
- Tool execution

**6.2 MCP Tool Registry**
- Auto-register MCP tools
- MCP server lifecycle management
- Configuration for MCP servers

**Example MCP Config**:
```yaml
mcp_servers:
  filesystem:
    command: npx @modelcontextprotocol/server-filesystem /home/user
    enabled: true
  git:
    command: npx @modelcontextprotocol/server-git
    enabled: true
```

### Phase 4: Advanced Features (4-5 weeks)

**Goal**: Persistence, advanced UI, and polish

#### Week 11-12: Persistent Memory

**7.1 SQLite Backend**
- Implement full SQLite support in `MemoryStore`
- Tables: history, sessions, variables, conversations
- Session save/restore
- History search

**7.2 Context Management**
- Automatic context summarization
- Context window management
- Long-term memory integration

#### Week 13-14: Advanced Pipeline Features

**8.1 LLM-based Parsing**
- Optional AI argument filling
- Partial specification support
- Intent completion

**8.2 Macros System**
- Macro definition syntax
- Macro storage
- Macro execution
- Macro composition

#### Week 15: Polish and Documentation

**9.1 Documentation**
- User guide
- Plugin development guide
- API reference
- Example gallery

**9.2 Testing**
- Increase test coverage to 70%+
- Integration tests
- End-to-end tests
- Evaluation tests for AI quality

**9.3 Examples and Recipes**
- Create example workflows
- Recipe system for common tasks
- Tutorial walkthroughs

---

## Implementation Priorities

### Priority 1: Critical Path (Blocks Core Use Cases)

1. **Agent-Tool Integration** ⭐⭐⭐⭐⭐
   - Enables agentic workflows
   - Core differentiator
   - Dependencies: Tool registry improvements

2. **Variable System** ⭐⭐⭐⭐⭐
   - Enables workflow composition
   - Needed for pipelines
   - Dependencies: Parser updates, MemoryStore updates

3. **Pipeline Engine** ⭐⭐⭐⭐⭐
   - Enables complex workflows
   - Core feature from design doc
   - Dependencies: Variable system

4. **Configuration System** ⭐⭐⭐⭐
   - Enables customization
   - Needed for all other features
   - Dependencies: None (foundational)

### Priority 2: Safety and Robustness

5. **Approval System (HITL)** ⭐⭐⭐⭐⭐
   - Safety for agentic execution
   - Production requirement
   - Dependencies: Agent-tool integration

6. **Error Handling** ⭐⭐⭐⭐
   - Better UX
   - Easier debugging
   - Dependencies: None

7. **Logging and Audit** ⭐⭐⭐⭐
   - Debugging and security
   - Production requirement
   - Dependencies: None

### Priority 3: Extensibility

8. **Plugin System** ⭐⭐⭐⭐
   - Ecosystem growth
   - Competitive feature
   - Dependencies: Configuration system

9. **MCP Integration** ⭐⭐⭐
   - Access to ecosystem
   - Competitive feature
   - Dependencies: Plugin system (similar architecture)

### Priority 4: User Experience

10. **Persistent Memory** ⭐⭐⭐
    - Better UX for long sessions
    - Resume interrupted work
    - Dependencies: MemoryStore enhancement

11. **LLM-based Parsing** ⭐⭐
    - Advanced feature
    - Nice to have
    - Dependencies: Agent-tool integration

12. **Macros** ⭐⭐
    - User convenience
    - Can use plugins instead
    - Dependencies: Parser, executor

---

## Technical Architecture Recommendations

### 1. Configuration System Design

**Recommended Stack**:
- `pydantic-settings` for config management
- YAML for config files (user-friendly)
- Environment variable support via `pydantic`

**Structure**:
```python
from pydantic_settings import BaseSettings

class ModelConfig(BaseSettings):
    provider: str = "ollama"
    name: str = "llama3.1"
    base_url: str = "http://localhost:11434"
    temperature: float = 0.7

class ShellConfig(BaseSettings):
    prompt: str = "ai> "
    history_file: str = "~/.ai_shell/history"
    auto_suggest: bool = True

class AIShellConfig(BaseSettings):
    model: ModelConfig = ModelConfig()
    shell: ShellConfig = ShellConfig()

    class Config:
        env_prefix = "AI_SHELL_"
        env_nested_delimiter = "__"
```

### 2. Pipeline Engine Design

**Architecture**: Async DAG execution with streaming

**Key Components**:
```python
@dataclass
class PipelineStage:
    """Single stage in pipeline."""
    type: str  # "bash", "tool", "agent"
    command: str
    args: List[str]
    options: Dict[str, Any]

class PipelineEngine:
    """Execute multi-stage pipelines with streaming."""

    async def build(self, stages: List[PipelineStage]) -> Pipeline:
        """Build pipeline from stages."""

    async def execute(self, pipeline: Pipeline) -> AsyncIterator[str]:
        """Execute pipeline with streaming."""
```

**Benefits**:
- Proper backpressure control
- Error propagation
- Cancellation support
- Progress tracking

### 3. Agent-Tool Integration Design

**Approach**: Convert CustomFunction to Ollama tool format

**Implementation**:
```python
class CommandExecutor:
    def to_ollama_tools(self) -> List[Dict]:
        """Convert registered functions to Ollama tool format."""
        tools = []
        for name, func in self.commands.items():
            tool = {
                "type": "function",
                "function": {
                    "name": name,
                    "description": self.command_info[name].description,
                    "parameters": self._extract_parameters(func)
                }
            }
            tools.append(tool)
        return tools

class OllamaAgent:
    async def execute_with_tools(self, task: str, tools: List[Dict]):
        """Execute task with tool calling."""
        messages = [{"role": "user", "content": task}]

        while True:
            response = await self.client.chat(
                model=self.model,
                messages=messages,
                tools=tools
            )

            # Check for tool calls
            if response.message.tool_calls:
                for tool_call in response.message.tool_calls:
                    result = await self._execute_tool(tool_call)
                    messages.append({
                        "role": "tool",
                        "content": result,
                        "name": tool_call.function.name
                    })
            else:
                return response.message.content
```

### 4. Approval System Design

**Multi-level Permissions**:
```python
class PermissionLevel(Enum):
    ALWAYS_ALLOW = "always_allow"
    REQUIRE_APPROVAL = "require_approval"
    ALWAYS_DENY = "always_deny"

class PermissionManager:
    def __init__(self, config: Dict):
        self.rules = self._compile_rules(config)

    def check_permission(self, command: str) -> PermissionLevel:
        """Check command against rules."""
        # Check deny list first
        for pattern in self.rules["always_deny"]:
            if re.match(pattern, command):
                return PermissionLevel.ALWAYS_DENY

        # Check allow list
        for pattern in self.rules["always_allow"]:
            if re.match(pattern, command):
                return PermissionLevel.ALWAYS_ALLOW

        # Default: require approval
        return PermissionLevel.REQUIRE_APPROVAL

    async def request_approval(
        self,
        command: str,
        context: Optional[Dict] = None
    ) -> bool:
        """Request user approval with context."""
        permission = self.check_permission(command)

        if permission == PermissionLevel.ALWAYS_DENY:
            print("❌ Command blocked (dangerous pattern)")
            return False

        if permission == PermissionLevel.ALWAYS_ALLOW:
            return True

        # Show approval prompt
        print(f"\n⚠️  Approval Required")
        print(f"Command: {command}")

        if context:
            if "reasoning" in context:
                print(f"Reasoning: {context['reasoning']}")
            if "risk" in context:
                print(f"Risk: {context['risk']}")

        response = input("Execute? [y/N/d(dry-run)]: ")

        if response.lower() == "d":
            await self._dry_run(command)
            response = input("Proceed? [y/N]: ")

        return response.lower() == "y"
```

### 5. Plugin System Design

**Plugin Structure**:
```
~/.ai_shell/plugins/
  my_plugin/
    plugin.yaml         # Manifest
    __init__.py         # Entry point
    tools.py            # Tool implementations
    requirements.txt    # Dependencies
```

**Plugin Manager**:
```python
class PluginManager:
    def __init__(self, plugin_dirs: List[str]):
        self.plugin_dirs = plugin_dirs
        self.loaded_plugins = {}

    def discover_plugins(self) -> List[PluginManifest]:
        """Find all plugins in plugin directories."""
        plugins = []
        for plugin_dir in self.plugin_dirs:
            for path in Path(plugin_dir).glob("*/plugin.yaml"):
                manifest = self._load_manifest(path)
                plugins.append(manifest)
        return plugins

    async def load_plugin(self, manifest: PluginManifest):
        """Load and register plugin."""
        # Install dependencies if needed
        await self._install_dependencies(manifest)

        # Import module
        module = importlib.import_module(manifest.entry_point)

        # Call registration function
        register_fn = getattr(module, "register_tools")
        tools = await register_fn()

        # Register tools with executor
        for tool in tools:
            self.executor.register_function(tool)

        self.loaded_plugins[manifest.name] = manifest
```

---

## Success Metrics

### Phase 1 Success Criteria

✅ **Configuration System**:
- [ ] Config loads from `~/.ai_shell/config.yaml`
- [ ] Environment variables override config
- [ ] Default config works without file

✅ **Variable System**:
- [ ] Can assign: `cmd > $varname`
- [ ] Can expand: `echo $varname`
- [ ] Variables persist in session
- [ ] Can use in pipelines

✅ **Pipeline Engine**:
- [ ] Can chain: `!cmd | \tool | !cmd2`
- [ ] Streaming works between stages
- [ ] Errors propagate properly
- [ ] Can cancel mid-pipeline

### Phase 2 Success Criteria

✅ **Agent-Tool Integration**:
- [ ] Agent can call tools
- [ ] Tools registered from CustomFunction
- [ ] Agent completes multi-step tasks
- [ ] Tool results feed back to agent

✅ **Approval System**:
- [ ] Dangerous commands blocked
- [ ] Safe commands auto-approved
- [ ] User prompted for uncertain commands
- [ ] Dry-run mode works

### Phase 3 Success Criteria

✅ **Plugin System**:
- [ ] Plugins load from directory
- [ ] Third-party plugin works
- [ ] Plugin dependencies install
- [ ] Plugin tools available to agent

✅ **MCP Integration**:
- [ ] MCP server starts and connects
- [ ] MCP tools registered
- [ ] MCP tools callable from shell
- [ ] MCP tools callable by agent

### Phase 4 Success Criteria

✅ **Persistent Memory**:
- [ ] Sessions save to SQLite
- [ ] Sessions restore on startup
- [ ] Command history searchable
- [ ] Conversations persist

✅ **Overall Quality**:
- [ ] 70%+ test coverage
- [ ] User documentation complete
- [ ] 5+ example workflows
- [ ] Plugin development guide

---

## Conclusion

This comprehensive plan transforms the AI-Shell from a solid foundation into a feature-complete, production-ready tool that fulfills all design principles. The phased approach ensures:

1. **Incremental Value**: Each phase delivers working features
2. **Risk Management**: Critical features first
3. **Dependency Order**: Build in logical sequence
4. **Quality Focus**: Testing and docs throughout

The current implementation provides an excellent base with:
- Clean architecture and abstractions
- Working shell and REPL
- Flexible backend support
- Good UX foundations

The improvement plan addresses the gaps systematically while maintaining the project's core vision: **an extensible, customizable bash wrapper that seamlessly embeds AI capabilities in the user's workflow**.

Next steps:
1. Review and validate this plan
2. Begin Phase 1, Week 1: Configuration system
3. Iterate based on feedback and real-world usage
4. Build community around plugins and examples

---

**Document Maintained By**: Development Team
**Last Updated**: 2025-12-29
**Next Review**: After Phase 1 completion
