# AI Shell - Enhanced Design Document

## Overview

**Project:** ai-shell
**Version:** 2.0 (Enhanced)
**Last Updated:** 2025-10-10

### Vision

Build a **local-first, human-in-the-loop AI shell** that unifies **LLMs**, **Bash**, and **MCP tools** into a single interactive environment. The ai-shell empowers users to compose AI capabilities with traditional Unix tools using familiar pipe syntax, while maintaining safety through approval workflows.

### Core Capabilities

Users can:
- **Chat** with local LLMs (Ollama primary, cloud optional)
- **Execute AI tools** (summarize, search, analyze) directly from command line
- **Run Bash commands** and pipe results to/from AI tools seamlessly
- **Integrate MCP servers** for structured external tools (filesystem, git, browser, databases)
- **Supervise AI actions** before execution - true *human-in-the-loop* operation
- **Compose pipelines** mixing Bash and AI with natural `|` syntax

---

## Design Principles

### 1. Local-First
- **Primary**: Ollama for privacy and offline operation
- **Optional**: Cloud adapters (OpenAI, Anthropic) when needed
- **Rationale**: Privacy, cost control, and independence from cloud services

### 2. Human-in-the-Loop
- AI proposes actions, user approves execution
- Multi-level permission system (auto-approve, require-approval, deny)
- Audit trail of all executed commands
- **Not autonomous** - collaborative and safe

### 3. Composable Workflows
- Unified pipe syntax: `!du -sh * | summarize | \report`
- Mix Bash commands and AI tools naturally
- Variables for intermediate results (`$last`, `$summary`)
- Build complex workflows from simple primitives

### 4. Extensible by Design
- Plugin system for custom tools (Python modules)
- MCP server integration for ecosystem tools
- Config-based tool registration
- User-defined composite tools

### 5. Transparent Execution
- All steps logged with rationale
- Explainable AI decisions (show reasoning)
- Streaming output for real-time visibility
- Debug mode for detailed inspection

### 6. Embeddable Runtime
- Use as library: `from ai_shell import Agent, Pipeline`
- Programmatic access to all features
- Integration into existing tools and workflows

---

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         User Interface                       │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  REPL (Interactive Shell)                            │   │
│  │  - Input parsing (!, ?, \, auto-resolve)             │   │
│  │  - Tab completion                                     │   │
│  │  - History management                                 │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                      Core Orchestration                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Parser     │→ │  Pipeline    │→ │   Renderer   │      │
│  │              │  │   Engine     │  │              │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                     Execution Layer                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  BaseAgent   │  │  ToolRegistry│  │ BashExecutor │      │
│  │  (ReAct)     │  │              │  │              │      │
│  └──────┬───────┘  └──────┬───────┘  └──────────────┘      │
│         │                  │                                 │
│         ↓                  ↓                                 │
│  ┌──────────────┐  ┌──────────────┐                        │
│  │ ModelAdapter │  │  MCPAdapter  │                        │
│  │ (Ollama)     │  │              │                        │
│  └──────────────┘  └──────────────┘                        │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    Storage & Memory                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ MemoryStore  │  │   SQLite     │  │ ConfigStore  │      │
│  │ (In-Memory)  │  │  (History)   │  │              │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

```
User Input
    ↓
[Parser] → Identify command type (Bash/AI/Tool/Auto)
    ↓
[PipelineEngine] → Build execution graph
    ↓
[Node Execution] → Run nodes (stream results)
    │
    ├─→ [BashExecutor] → OS subprocess
    ├─→ [ToolNode] → Tool function call
    └─→ [AgentNode] → LLM reasoning loop
    ↓
[Renderer] → Format and display output
    ↓
User sees streaming result
```

---

## Core Components

### 1. BaseAgent (core/agent.py)

**Responsibility**: AI reasoning, planning, and action proposal.

**Architecture Pattern**: **ReAct (Reasoning + Action)** for MVP

**Why ReAct**:
- More interpretable (explicit reasoning)
- Works with any LLM (no function calling required)
- Good for learning and debugging
- Industry standard (LangChain, AutoGen)

**Implementation**:
```python
class BaseAgent:
    """
    ReAct agent with Thought-Action-Observation loop.
    """

    def __init__(self, model_adapter: ModelAdapter, tool_registry: ToolRegistry):
        self.model = model_adapter
        self.tools = tool_registry
        self.memory = []

    async def execute(self, task: str, max_iterations: int = 10) -> AgentResult:
        """
        Execute task using ReAct loop.

        Returns:
            AgentResult with final answer or action sequence
        """
        scratchpad = []

        for i in range(max_iterations):
            # Thought: Reason about next step
            thought = await self._generate_thought(task, scratchpad)
            scratchpad.append({"type": "thought", "content": thought})

            # Check if done
            if self._is_complete(thought):
                return AgentResult(answer=thought, steps=scratchpad)

            # Action: Choose tool and parameters
            action = await self._generate_action(thought, scratchpad)
            scratchpad.append({"type": "action", "content": action})

            # Human-in-the-loop approval
            if self._requires_approval(action):
                approved = await self._request_approval(action)
                if not approved:
                    return AgentResult(cancelled=True, steps=scratchpad)

            # Observation: Execute and observe result
            observation = await self._execute_action(action)
            scratchpad.append({"type": "observation", "content": observation})

        return AgentResult(max_iterations_reached=True, steps=scratchpad)

    async def chat(self, message: str) -> AsyncIterator[str]:
        """Stream chat response token by token."""
        async for token in self.model.stream(message, self.memory):
            yield token

    async def plan(self, task: str) -> Plan:
        """Generate step-by-step plan (for future Plan-and-Execute mode)."""
        prompt = f"Create a step-by-step plan for: {task}"
        plan_text = await self.model.generate(prompt)
        return Plan.from_text(plan_text)
```

**Key Methods**:
- `execute(task)`: Main ReAct loop with human-in-the-loop
- `chat(message)`: Streaming conversational responses
- `plan(task)`: Generate plans (future enhancement)

**Future Enhancement**: Add function calling mode for faster execution when LLM supports structured outputs.

---

### 2. ToolRegistry (core/registry.py)

**Responsibility**: Catalog and manage all available tools (AI and system).

**Design Pattern**: Registry with auto-discovery

**Implementation**:
```python
from typing import Callable, Dict, List
from pydantic import BaseModel

class Tool(BaseModel):
    """Tool definition with schema validation."""
    name: str
    description: str
    function: Callable
    parameters: Dict[str, any]  # JSON Schema
    requires_approval: bool = False
    category: str = "general"

class ToolRegistry:
    """
    Centralized tool catalog with auto-registration.
    """

    def __init__(self):
        self._tools: Dict[str, Tool] = {}
        self._mcp_tools: Dict[str, Tool] = {}

    def register(self, tool: Tool):
        """Register a tool."""
        self._tools[tool.name] = tool

    def register_from_function(self, func: Callable,
                               description: str = None,
                               requires_approval: bool = False):
        """Auto-register from Python function with type hints."""
        tool = Tool(
            name=func.__name__,
            description=description or func.__doc__,
            function=func,
            parameters=self._extract_schema(func),
            requires_approval=requires_approval
        )
        self.register(tool)

    def register_mcp_tools(self, mcp_adapter: MCPAdapter):
        """Register all tools from MCP server."""
        for tool_def in mcp_adapter.list_tools():
            tool = Tool(
                name=f"mcp_{tool_def.name}",
                description=tool_def.description,
                function=lambda **kwargs: mcp_adapter.call_tool(tool_def.name, **kwargs),
                parameters=tool_def.parameters,
                requires_approval=tool_def.requires_approval
            )
            self._mcp_tools[tool.name] = tool

    def get(self, name: str) -> Tool:
        """Get tool by name."""
        return self._tools.get(name) or self._mcp_tools.get(name)

    def list(self, category: str = None) -> List[Tool]:
        """List all tools, optionally filtered by category."""
        tools = list(self._tools.values()) + list(self._mcp_tools.values())
        if category:
            tools = [t for t in tools if t.category == category]
        return tools

    def to_llm_format(self) -> List[Dict]:
        """Export tools in LLM function calling format."""
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters
                }
            }
            for tool in self.list()
        ]
```

**Key Features**:
- Auto-registration from Python functions using type hints
- MCP tool integration
- Category-based organization
- Export to LLM function calling format
- Permission tracking (requires_approval flag)

---

### 3. PipelineEngine (core/pipeline.py)

**Responsibility**: Orchestrate multi-stage pipelines with streaming.

**Architecture**: Async pipeline with bounded queues for backpressure.

**Based on Research**: Modern async patterns using `asyncio.TaskGroup` (Python 3.11+) and bounded queues.

**Implementation**:
```python
import asyncio
from typing import AsyncIterator, List, Union
from dataclasses import dataclass

@dataclass
class PipelineNode:
    """Base class for pipeline nodes."""
    type: str  # "bash", "tool", "agent"

    async def execute(self, input_stream: AsyncIterator[bytes]) -> AsyncIterator[bytes]:
        """Execute node with streaming input/output."""
        raise NotImplementedError

class BashNode(PipelineNode):
    def __init__(self, command: str):
        super().__init__(type="bash")
        self.command = command

    async def execute(self, input_stream: AsyncIterator[bytes] = None) -> AsyncIterator[bytes]:
        """Run bash command in thread pool (blocking I/O)."""
        loop = asyncio.get_running_loop()

        # Collect input if provided
        input_data = b""
        if input_stream:
            async for chunk in input_stream:
                input_data += chunk

        # Execute in thread pool to avoid blocking event loop
        result = await loop.run_in_executor(
            None,
            self._run_subprocess,
            input_data
        )

        # Yield result
        yield result.encode()

    def _run_subprocess(self, input_data: bytes) -> str:
        """Blocking subprocess execution."""
        import subprocess
        proc = subprocess.run(
            self.command,
            shell=True,
            input=input_data,
            capture_output=True,
            text=True
        )
        if proc.returncode != 0:
            raise BashError(proc.stderr)
        return proc.stdout

class ToolNode(PipelineNode):
    def __init__(self, tool: Tool, args: Dict = None):
        super().__init__(type="tool")
        self.tool = tool
        self.args = args or {}

    async def execute(self, input_stream: AsyncIterator[bytes] = None) -> AsyncIterator[bytes]:
        """Execute tool with streaming."""
        # Collect input
        input_text = ""
        if input_stream:
            async for chunk in input_stream:
                input_text += chunk.decode()

        # Add input to args
        if input_text:
            self.args['input'] = input_text

        # Execute tool
        result = await self.tool.function(**self.args)

        # Stream result
        if hasattr(result, '__aiter__'):
            async for chunk in result:
                yield chunk.encode()
        else:
            yield str(result).encode()

class Pipeline:
    """
    Async pipeline with streaming and backpressure.
    """

    def __init__(self, nodes: List[PipelineNode]):
        self.nodes = nodes

    async def execute(self) -> AsyncIterator[bytes]:
        """
        Execute pipeline with streaming between stages.
        Uses bounded queues for backpressure control.
        """
        if len(self.nodes) == 1:
            # Single node - direct execution
            async for chunk in self.nodes[0].execute():
                yield chunk
            return

        # Multi-stage pipeline
        async with asyncio.TaskGroup() as tg:
            # Create queues between stages
            queues = [asyncio.Queue(maxsize=10) for _ in range(len(self.nodes))]

            # Start all stages
            tasks = []
            for i, node in enumerate(self.nodes):
                input_queue = queues[i-1] if i > 0 else None
                output_queue = queues[i]
                task = tg.create_task(
                    self._run_stage(node, input_queue, output_queue)
                )
                tasks.append(task)

            # Consume final output
            final_queue = queues[-1]
            while True:
                chunk = await final_queue.get()
                if chunk is None:  # Sentinel for end
                    break
                yield chunk

    async def _run_stage(self,
                         node: PipelineNode,
                         input_queue: asyncio.Queue = None,
                         output_queue: asyncio.Queue = None):
        """Run a single pipeline stage."""
        try:
            # Create input stream from queue
            async def input_stream():
                if input_queue:
                    while True:
                        chunk = await input_queue.get()
                        if chunk is None:
                            break
                        yield chunk

            # Execute node
            stream = input_stream() if input_queue else None
            async for chunk in node.execute(stream):
                if output_queue:
                    await output_queue.put(chunk)

            # Signal completion
            if output_queue:
                await output_queue.put(None)

        except Exception as e:
            # Error propagation
            if output_queue:
                await output_queue.put(PipelineError(str(e)))
```

**Key Features**:
- Async streaming between stages
- Bounded queues for backpressure (maxsize=10)
- Thread pool for blocking operations (Bash)
- Proper error propagation
- Cancellation support via TaskGroup

---

### 4. REPL (shell/repl.py)

**Responsibility**: Interactive command loop with streaming display.

**Implementation**:
```python
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown

class REPL:
    """
    Interactive Read-Eval-Print Loop with rich terminal UI.
    """

    def __init__(self,
                 parser: Parser,
                 pipeline_engine: PipelineEngine,
                 registry: ToolRegistry):
        self.parser = parser
        self.engine = pipeline_engine
        self.registry = registry
        self.console = Console()
        self.session = PromptSession()
        self.memory = MemoryStore()

        # Tab completion
        tool_names = [t.name for t in registry.list()]
        self.completer = WordCompleter(tool_names, ignore_case=True)

    async def run(self):
        """Main REPL loop."""
        self.console.print("[bold blue]ai-shell v2.0[/bold blue]")
        self.console.print("Type [bold]?help[/bold] for commands, [bold]Ctrl+D[/bold] to exit\n")

        while True:
            try:
                # Get input
                user_input = await self.session.prompt_async(
                    "ai> ",
                    completer=self.completer
                )

                if not user_input.strip():
                    continue

                # Parse command
                command = self.parser.parse(user_input)

                # Execute based on type
                if command.type == "chat":
                    await self._handle_chat(command)
                elif command.type == "pipeline":
                    await self._handle_pipeline(command)
                elif command.type == "meta":
                    await self._handle_meta_command(command)

                # Add to history
                self.memory.add_command(user_input)

            except KeyboardInterrupt:
                self.console.print("\n[dim]Cancelled[/dim]")
                continue

            except EOFError:
                self.console.print("\n[dim]Goodbye![/dim]")
                break

            except Exception as e:
                self.console.print(f"[red]Error:[/red] {e}")

    async def _handle_chat(self, command: ChatCommand):
        """Handle chat command with streaming."""
        agent = BaseAgent(self.model, self.registry)

        content = ""
        with Live(Markdown(content), console=self.console, auto_refresh=False) as live:
            async for token in agent.chat(command.message):
                content += token
                live.update(Markdown(content), refresh=True)

        # Save to memory
        self.memory.add_message("assistant", content)

    async def _handle_pipeline(self, command: PipelineCommand):
        """Handle pipeline command with streaming."""
        pipeline = self.engine.build_pipeline(command.nodes)

        output = ""
        async for chunk in pipeline.execute():
            chunk_str = chunk.decode()
            output += chunk_str
            self.console.print(chunk_str, end="")

        # Save to variables
        self.memory.set_variable("$last", output)

    async def _handle_meta_command(self, command: MetaCommand):
        """Handle meta commands (/help, /history, etc.)."""
        if command.name == "help":
            self._show_help()
        elif command.name == "history":
            self._show_history()
        elif command.name == "clear":
            self.memory.clear()
```

**Key Features**:
- Async input with `prompt_toolkit`
- Streaming display with `rich.live`
- Tab completion for tools
- Command history
- Graceful cancellation (Ctrl+C)

---

### 5. ModelAdapter (adapters/ollama.py)

**Responsibility**: Interface with LLM providers (Ollama, OpenAI, Anthropic).

**Pattern**: Adapter pattern for provider abstraction.

**Implementation**:
```python
from abc import ABC, abstractmethod
from typing import AsyncIterator, List, Dict

class ModelAdapter(ABC):
    """Abstract base for LLM providers."""

    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate completion."""
        pass

    @abstractmethod
    async def stream(self, prompt: str, **kwargs) -> AsyncIterator[str]:
        """Stream completion token by token."""
        pass

    @abstractmethod
    async def chat(self, messages: List[Dict], **kwargs) -> str:
        """Chat completion."""
        pass

class OllamaAdapter(ModelAdapter):
    """Ollama local LLM adapter (primary)."""

    def __init__(self, model: str = "llama3.1", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url
        self.client = ollama.AsyncClient(base_url)

    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate completion."""
        response = await self.client.generate(
            model=self.model,
            prompt=prompt,
            **kwargs
        )
        return response['response']

    async def stream(self, prompt: str, **kwargs) -> AsyncIterator[str]:
        """Stream completion with async generator."""
        async for chunk in await self.client.generate(
            model=self.model,
            prompt=prompt,
            stream=True,
            **kwargs
        ):
            yield chunk['response']

    async def chat(self, messages: List[Dict], **kwargs) -> str:
        """Chat completion."""
        response = await self.client.chat(
            model=self.model,
            messages=messages,
            **kwargs
        )
        return response['message']['content']

    async def chat_stream(self, messages: List[Dict], **kwargs) -> AsyncIterator[str]:
        """Streaming chat."""
        async for chunk in await self.client.chat(
            model=self.model,
            messages=messages,
            stream=True,
            **kwargs
        ):
            yield chunk['message']['content']

class OpenAIAdapter(ModelAdapter):
    """OpenAI API adapter (optional, cloud)."""

    def __init__(self, model: str = "gpt-4o", api_key: str = None):
        self.model = model
        self.client = AsyncOpenAI(api_key=api_key)

    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate completion."""
        response = await self.client.completions.create(
            model=self.model,
            prompt=prompt,
            **kwargs
        )
        return response.choices[0].text

    async def stream(self, prompt: str, **kwargs) -> AsyncIterator[str]:
        """Stream completion."""
        stream = await self.client.completions.create(
            model=self.model,
            prompt=prompt,
            stream=True,
            **kwargs
        )
        async for chunk in stream:
            if chunk.choices[0].text:
                yield chunk.choices[0].text

    async def chat(self, messages: List[Dict], **kwargs) -> str:
        """Chat completion with structured outputs support."""
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            **kwargs
        )
        return response.choices[0].message.content
```

**Key Features**:
- Async/await for all operations
- Streaming support (essential for UX)
- Consistent interface across providers
- Easy to add new providers

---

### 6. MCPAdapter (core/mcp_adapter.py)

**Responsibility**: Integration with Model Context Protocol servers.

**MCP Overview**:
- Standard protocol for AI tool integration
- Servers expose tools, resources, and prompts
- Transport: stdio, HTTP/SSE, or WebSocket
- Specification: https://modelcontextprotocol.io/

**Implementation**:
```python
import subprocess
import json
from typing import List, Dict

class MCPAdapter:
    """
    Adapter for Model Context Protocol servers.
    Supports stdio transport (most common).
    """

    def __init__(self, server_command: str):
        """
        Initialize MCP server connection.

        Args:
            server_command: Command to start server (e.g., "npx @modelcontextprotocol/server-filesystem /path")
        """
        self.server_command = server_command
        self.process = None
        self.tools = []

    async def connect(self):
        """Start MCP server and discover capabilities."""
        # Start server process
        self.process = subprocess.Popen(
            self.server_command,
            shell=True,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # Initialize connection
        await self._send_request("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {}
            },
            "clientInfo": {
                "name": "ai-shell",
                "version": "2.0"
            }
        })

        # List available tools
        response = await self._send_request("tools/list", {})
        self.tools = response.get("tools", [])

    async def list_tools(self) -> List[Dict]:
        """Get list of available tools."""
        return self.tools

    async def call_tool(self, name: str, arguments: Dict) -> any:
        """
        Call an MCP tool.

        Args:
            name: Tool name
            arguments: Tool arguments

        Returns:
            Tool result
        """
        response = await self._send_request("tools/call", {
            "name": name,
            "arguments": arguments
        })

        return response.get("content", [])

    async def _send_request(self, method: str, params: Dict) -> Dict:
        """Send JSON-RPC request to MCP server."""
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params
        }

        # Send request
        self.process.stdin.write(json.dumps(request) + "\n")
        self.process.stdin.flush()

        # Read response
        response_line = self.process.stdout.readline()
        response = json.loads(response_line)

        if "error" in response:
            raise MCPError(response["error"])

        return response.get("result", {})

    async def disconnect(self):
        """Close MCP server connection."""
        if self.process:
            self.process.terminate()
            self.process.wait()

class MCPError(Exception):
    """MCP protocol error."""
    pass
```

**Key Features**:
- Stdio transport (most common for MCP)
- Automatic tool discovery
- JSON-RPC protocol handling
- Async operation

**Example MCP Servers to Support**:
- `@modelcontextprotocol/server-filesystem` - File operations
- `@modelcontextprotocol/server-git` - Git operations
- `@modelcontextprotocol/server-sqlite` - SQLite queries
- Custom servers (user can define)

---

### 7. MemoryStore (core/memory.py)

**Responsibility**: Short-term (session) and long-term (persistent) memory.

**Architecture**:
- **In-memory**: Current session state, conversation history, variables
- **SQLite**: Command history, saved sessions, user preferences

**Implementation**:
```python
import sqlite3
from typing import List, Dict, Optional
from datetime import datetime

class MemoryStore:
    """
    Hybrid memory: in-memory for session, SQLite for persistence.
    """

    def __init__(self, db_path: str = "~/.ai_shell/history.db"):
        # In-memory state
        self.conversation_history: List[Dict] = []
        self.variables: Dict[str, any] = {}
        self.current_session_id = datetime.now().isoformat()

        # Persistent storage
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize SQLite database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Command history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                command TEXT NOT NULL,
                output TEXT,
                session_id TEXT
            )
        """)

        # Sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                state TEXT NOT NULL
            )
        """)

        conn.commit()
        conn.close()

    def add_message(self, role: str, content: str):
        """Add message to conversation history."""
        self.conversation_history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })

    def add_command(self, command: str, output: str = None):
        """Add command to persistent history."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO history (timestamp, command, output, session_id)
            VALUES (?, ?, ?, ?)
        """, (datetime.now().isoformat(), command, output, self.current_session_id))

        conn.commit()
        conn.close()

    def get_recent_history(self, n: int = 10) -> List[Dict]:
        """Get recent conversation messages."""
        return self.conversation_history[-n:]

    def search_history(self, query: str, limit: int = 10) -> List[str]:
        """Search command history."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT command, timestamp FROM history
            WHERE command LIKE ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (f"%{query}%", limit))

        results = cursor.fetchall()
        conn.close()

        return [row[0] for row in results]

    def set_variable(self, name: str, value: any):
        """Set session variable ($last, $summary, etc.)."""
        self.variables[name] = value

    def get_variable(self, name: str) -> Optional[any]:
        """Get session variable."""
        return self.variables.get(name)

    def save_session(self):
        """Save current session state."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        state = {
            "conversation_history": self.conversation_history,
            "variables": self.variables
        }

        cursor.execute("""
            INSERT OR REPLACE INTO sessions (session_id, timestamp, state)
            VALUES (?, ?, ?)
        """, (self.current_session_id, datetime.now().isoformat(), json.dumps(state)))

        conn.commit()
        conn.close()

    def load_session(self, session_id: str):
        """Load saved session."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT state FROM sessions WHERE session_id = ?
        """, (session_id,))

        row = cursor.fetchone()
        conn.close()

        if row:
            state = json.loads(row[0])
            self.conversation_history = state["conversation_history"]
            self.variables = state["variables"]
            self.current_session_id = session_id

    def clear(self):
        """Clear session state (not persistent history)."""
        self.conversation_history = []
        self.variables = {}
```

**Key Features**:
- Fast in-memory access for current session
- Persistent SQLite storage for history
- Session save/restore
- Command history search
- Variable storage (`$last`, `$summary`)

---

### 8. Human-in-the-Loop System (core/approval.py)

**Responsibility**: Safety system for command approval.

**Design**: Multi-level permission system based on industry best practices.

**Implementation**:
```python
from enum import Enum
from typing import List, Pattern
import re

class PermissionLevel(Enum):
    """Permission levels for commands."""
    ALWAYS_ALLOW = "always_allow"      # Safe read-only commands
    REQUIRE_APPROVAL = "require_approval"  # Potentially destructive
    ALWAYS_DENY = "always_deny"        # Dangerous patterns

class PermissionManager:
    """
    Multi-level permission system for human-in-the-loop.
    Based on GitHub Copilot CLI and AutoGen patterns.
    """

    def __init__(self, config: Dict = None):
        self.config = config or self._default_config()
        self.console = Console()

    def _default_config(self) -> Dict:
        """Default permission rules."""
        return {
            "always_allow": [
                r"^ls\b",
                r"^cat\b",
                r"^echo\b",
                r"^pwd\b",
                r"^which\b",
                r"^grep\b",
                r"^find\b",
                r"^head\b",
                r"^tail\b",
            ],
            "always_deny": [
                r"rm\s+-rf\s+/",
                r"dd\s+if=",
                r"mkfs\b",
                r":(){:|:&};:",  # Fork bomb
                r">\s*/dev/sd",   # Write to disk
            ],
            "require_approval": [
                r"^rm\b",
                r"^mv\b",
                r"^cp\b.*--force",
                r"^git\s+push",
                r"^docker\s+rm",
                r"^sudo\b",
            ]
        }

    def check_permission(self, command: str) -> PermissionLevel:
        """
        Determine permission level for command.

        Returns:
            PermissionLevel enum value
        """
        # Check always deny first (highest priority)
        for pattern in self.config["always_deny"]:
            if re.search(pattern, command):
                return PermissionLevel.ALWAYS_DENY

        # Check always allow
        for pattern in self.config["always_allow"]:
            if re.search(pattern, command):
                return PermissionLevel.ALWAYS_ALLOW

        # Check require approval
        for pattern in self.config["require_approval"]:
            if re.search(pattern, command):
                return PermissionLevel.REQUIRE_APPROVAL

        # Default: require approval for unknown commands
        return PermissionLevel.REQUIRE_APPROVAL

    async def request_approval(self, command: str, context: Dict = None) -> bool:
        """
        Request user approval for command execution.

        Args:
            command: Command to execute
            context: Additional context (reasoning, expected outcome)

        Returns:
            True if approved, False otherwise
        """
        permission = self.check_permission(command)

        # Always deny
        if permission == PermissionLevel.ALWAYS_DENY:
            self.console.print(f"[bold red]✗ Blocked:[/bold red] {command}")
            self.console.print("[red]This command matches a dangerous pattern and cannot be executed.[/red]")
            return False

        # Always allow
        if permission == PermissionLevel.ALWAYS_ALLOW:
            return True

        # Require approval
        self.console.print("\n[bold yellow]⚠ Approval Required[/bold yellow]")
        self.console.print(f"[bold]Command:[/bold] {command}")

        if context:
            if context.get("reasoning"):
                self.console.print(f"[dim]Reasoning:[/dim] {context['reasoning']}")
            if context.get("expected_outcome"):
                self.console.print(f"[dim]Expected outcome:[/dim] {context['expected_outcome']}")

        # Risk assessment
        risk = self._assess_risk(command)
        risk_color = {"low": "green", "medium": "yellow", "high": "red"}[risk]
        self.console.print(f"[{risk_color}]Risk level: {risk}[/{risk_color}]")

        # Get user input
        response = await self.console.input("\n[bold]Execute this command? [y/N/d (dry-run)]:[/bold] ")

        if response.lower() == 'y':
            return True
        elif response.lower() == 'd':
            # Dry run mode
            self.console.print("[dim]Dry run mode - simulating command...[/dim]")
            await self._dry_run(command)

            # Ask again after dry run
            response = await self.console.input("\n[bold]Proceed with execution? [y/N]:[/bold] ")
            return response.lower() == 'y'
        else:
            self.console.print("[dim]Command cancelled[/dim]")
            return False

    def _assess_risk(self, command: str) -> str:
        """
        Assess risk level of command.

        Returns:
            "low", "medium", or "high"
        """
        high_risk_patterns = [r"^rm\b", r"^sudo\b", r"git\s+push", r"docker"]
        medium_risk_patterns = [r"^mv\b", r"^cp\b", r"^chmod\b"]

        for pattern in high_risk_patterns:
            if re.search(pattern, command):
                return "high"

        for pattern in medium_risk_patterns:
            if re.search(pattern, command):
                return "medium"

        return "low"

    async def _dry_run(self, command: str):
        """Simulate command execution (show what would happen)."""
        # Simple simulation - just show the command
        # Future: could actually run with --dry-run flag if supported
        self.console.print(f"[dim]Would execute: {command}[/dim]")
```

**Key Features**:
- Three-tier permission system
- Regex-based command classification
- Risk assessment
- Dry-run mode
- Configurable rules
- Audit logging (integrated with MemoryStore)

**Configuration Example** (config.yaml):
```yaml
permissions:
  always_allow:
    - "ls"
    - "cat"
    - "echo"

  always_deny:
    - "rm -rf /"
    - "dd if="

  require_approval:
    - "rm"
    - "git push"
    - "docker rm"

approval:
  show_reasoning: true
  show_risk_level: true
  allow_dry_run: true
```

---

## Shell Input Grammar

### Prefix System

| Prefix | Meaning | Example | Behavior |
|--------|---------|---------|----------|
| `!` | Explicit Bash | `!ls -la` | Execute in shell |
| `?` | Chat with AI | `?How do I check disk usage?` | LLM chat response |
| `\` | Explicit AI tool | `\summarize report.txt` | Run named tool |
| none | Auto-resolve | `ls` or `summarize` | Tool → Bash → LLM |
| `/` | Meta command | `/help`, `/history` | Shell control |

### Auto-Resolution Logic

```
Input without prefix → Auto-resolve:
  1. Check if matches registered AI tool
  2. Check if starts with common shell command
  3. Fall back to AI chat
```

### Pipeline Syntax

Unified pipe operator works across Bash and AI:

```bash
# Bash → AI tool
!du -sh * | summarize

# AI tool → Bash
\search "python tips" | !grep "performance"

# AI tool → AI tool
\search "news" | \summarize | \report

# Bash → AI → Bash
!git log --oneline | \summarize | !cowsay
```

### Variable System

Store intermediate results:

```bash
# Automatic variables
!ls -la
$last         # Contains output of last command

\summarize report.txt
$last         # Contains summary

# Named variables
!du -sh * | summarize > $disk_summary
?Compare $disk_summary with last week
```

---

## Built-in Tools

### Core Tools (ai_shell/tools/builtin.py)

#### 1. summarize
**Purpose**: Condense text into key points.

**Signature**:
```python
async def summarize(
    text: str,
    max_length: int = 100,
    style: Literal["brief", "detailed"] = "brief"
) -> str:
    """
    Summarize text into key points.

    Args:
        text: Input text to summarize
        max_length: Maximum length in words
        style: 'brief' for bullets, 'detailed' for paragraphs

    Returns:
        Summarized text
    """
```

**Example**:
```bash
!cat long_article.txt | \summarize --style=brief
```

---

#### 2. search
**Purpose**: Search for information (files, web, docs).

**Signature**:
```python
async def search(
    query: str,
    scope: Literal["files", "web", "history"] = "files",
    max_results: int = 10
) -> List[str]:
    """
    Search for information.

    Args:
        query: Search query
        scope: Where to search (files, web, command history)
        max_results: Maximum results to return

    Returns:
        List of search results
    """
```

**Example**:
```bash
\search "TODO" --scope=files
\search "Python async patterns" --scope=web
```

---

#### 3. analyze
**Purpose**: Analyze data and provide insights.

**Signature**:
```python
async def analyze(
    data: str,
    analysis_type: Literal["sentiment", "statistics", "patterns"] = "patterns"
) -> Dict:
    """
    Analyze data and provide insights.

    Args:
        data: Input data (text, numbers, logs)
        analysis_type: Type of analysis to perform

    Returns:
        Analysis results
    """
```

**Example**:
```bash
!git log --oneline | \analyze --type=patterns
!cat access.log | \analyze --type=statistics
```

---

#### 4. report
**Purpose**: Generate formatted reports.

**Signature**:
```python
async def report(
    data: str,
    format: Literal["markdown", "html", "json"] = "markdown",
    title: str = "Report"
) -> str:
    """
    Generate formatted report from data.

    Args:
        data: Input data
        format: Output format
        title: Report title

    Returns:
        Formatted report
    """
```

**Example**:
```bash
\search "project status" | \summarize | \report --title="Weekly Status"
```

---

#### 5. explain
**Purpose**: Explain code, commands, or errors.

**Signature**:
```python
async def explain(
    content: str,
    detail_level: Literal["brief", "detailed", "expert"] = "detailed"
) -> str:
    """
    Explain code, commands, or errors.

    Args:
        content: Code, command, or error message
        detail_level: How detailed the explanation should be

    Returns:
        Explanation
    """
```

**Example**:
```bash
!git rebase -i HEAD~3 2>&1 | \explain
\explain "$(cat complex_script.sh)"
```

---

## Package Structure

```
ai_shell/
├── __init__.py
├── __main__.py              # Entry point: python -m ai_shell
│
├── core/                    # Core engine components
│   ├── __init__.py
│   ├── agent.py            # BaseAgent with ReAct loop
│   ├── registry.py         # ToolRegistry
│   ├── pipeline.py         # PipelineEngine with async
│   ├── mcp_adapter.py      # Model Context Protocol integration
│   ├── bash_executor.py    # BashExecutor
│   ├── memory.py           # MemoryStore (hybrid)
│   └── approval.py         # PermissionManager (HITL)
│
├── shell/                   # Interactive shell components
│   ├── __init__.py
│   ├── repl.py             # REPL main loop
│   ├── parser.py           # Input parser (!, ?, \, auto)
│   ├── renderer.py         # Output rendering (rich)
│   └── completer.py        # Tab completion
│
├── adapters/                # LLM provider adapters
│   ├── __init__.py
│   ├── base.py             # ModelAdapter abstract base
│   ├── ollama.py           # OllamaAdapter (primary)
│   ├── openai.py           # OpenAIAdapter (optional)
│   └── anthropic.py        # AnthropicAdapter (optional)
│
├── tools/                   # Built-in and user tools
│   ├── __init__.py
│   ├── builtin.py          # Core tools (summarize, search, etc.)
│   ├── filesystem.py       # File operations
│   └── web.py              # Web search and fetch
│
├── config/                  # Configuration management
│   ├── __init__.py
│   ├── config.py           # ConfigStore
│   └── defaults.yaml       # Default configuration
│
└── utils/                   # Utilities
    ├── __init__.py
    ├── logging.py          # Structured logging
    └── validation.py       # Input validation
```

---

## Configuration

### Configuration File (config.yaml)

```yaml
# Model configuration
model:
  provider: "ollama"                    # ollama, openai, anthropic
  name: "llama3.1"                      # Model name
  temperature: 0.7
  max_tokens: 4096
  base_url: "http://localhost:11434"   # For Ollama

# Optional cloud models
cloud_models:
  openai:
    api_key: "${OPENAI_API_KEY}"
    model: "gpt-4o"
  anthropic:
    api_key: "${ANTHROPIC_API_KEY}"
    model: "claude-3-5-sonnet-20241022"

# Agent configuration
agent:
  type: "react"                # react, function_calling (future)
  max_iterations: 10
  show_reasoning: true         # Display thought process
  stream_responses: true

# Human-in-the-loop configuration
permissions:
  always_allow:
    - "ls"
    - "cat"
    - "echo"
    - "pwd"
    - "which"

  always_deny:
    - "rm -rf /"
    - "dd if="
    - "mkfs"

  require_approval:
    - "rm"
    - "mv"
    - "git push"
    - "docker rm"
    - "sudo"

  show_risk_level: true
  allow_dry_run: true

# Memory configuration
memory:
  db_path: "~/.ai_shell/history.db"
  max_conversation_history: 50
  save_sessions: true

# Pipeline configuration
pipeline:
  queue_size: 10               # Backpressure control
  timeout: 300                 # Seconds
  stream_chunk_size: 1024      # Bytes

# MCP servers
mcp_servers:
  filesystem:
    command: "npx @modelcontextprotocol/server-filesystem /home/user"
    enabled: true

  git:
    command: "npx @modelcontextprotocol/server-git"
    enabled: true

# Tools configuration
tools:
  builtin_enabled: true
  user_tools_path: "~/.ai_shell/tools"

# UI configuration
ui:
  theme: "monokai"
  show_timestamps: false
  streaming_animation: true
  prompt: "ai> "

# Logging
logging:
  level: "INFO"                # DEBUG, INFO, WARNING, ERROR
  file: "~/.ai_shell/logs/ai_shell.log"
  format: "json"               # json or text
  audit_commands: true         # Log all executed commands
```

### Environment Variables

```bash
# Model configuration
export AI_SHELL_MODEL_PROVIDER=ollama
export AI_SHELL_MODEL_NAME=llama3.1

# API keys (optional, for cloud models)
export OPENAI_API_KEY=sk-...
export ANTHROPIC_API_KEY=sk-ant-...

# Paths
export AI_SHELL_CONFIG=~/.ai_shell/config.yaml
export AI_SHELL_TOOLS_PATH=~/.ai_shell/tools

# Debug
export AI_SHELL_DEBUG=1
export AI_SHELL_LOG_LEVEL=DEBUG
```

---

## Implementation Roadmap

### Phase 1: MVP (Weeks 1-4)

**Goal**: Basic working shell with local LLM.

**Deliverables**:
- ✅ REPL with prefix parsing (`!`, `?`, `\`)
- ✅ OllamaAdapter with streaming
- ✅ Basic tool registry (3-5 core tools)
- ✅ Simple bash executor
- ✅ In-memory conversation history
- ✅ Rich terminal output
- ✅ Basic error handling

**Success Criteria**:
- Can chat with LLM: `?How do I list files?`
- Can run bash: `!ls -la`
- Can use AI tool: `\summarize report.txt`
- Streaming responses work
- Basic error messages

---

### Phase 2: Pipelines & Safety (Weeks 5-8)

**Goal**: Add pipeline composition and human-in-the-loop.

**Deliverables**:
- ✅ PipelineEngine with async streaming
- ✅ Pipeline syntax: `!cmd | \tool`
- ✅ Variable system (`$last`)
- ✅ PermissionManager with approval workflows
- ✅ SQLite history persistence
- ✅ Session save/restore
- ✅ Improved error handling with retry

**Success Criteria**:
- Can chain: `!du -sh * | summarize`
- Approval prompt for dangerous commands
- Command history searchable
- Sessions persist across restarts

---

### Phase 3: MCP & Advanced Features (Weeks 9-12)

**Goal**: MCP integration and advanced agent capabilities.

**Deliverables**:
- ✅ MCPAdapter (stdio transport)
- ✅ Auto-register MCP tools
- ✅ Plan-and-execute mode (optional)
- ✅ Context management (summarization)
- ✅ Tab completion for tools
- ✅ Plugin system for user tools
- ✅ Comprehensive documentation

**Success Criteria**:
- Can use MCP servers (filesystem, git)
- Planning mode works for complex tasks
- Context doesn't overflow
- Users can write custom tools
- Full documentation published

---

### Phase 4: Polish & Extensions (Weeks 13-16)

**Goal**: Production-ready with ecosystem.

**Deliverables**:
- ✅ OpenAI/Anthropic adapters
- ✅ Semantic history search
- ✅ Advanced UI features (progress bars, colors)
- ✅ Docker sandbox execution (optional)
- ✅ Example tool library
- ✅ CI/CD with tests
- ✅ PyPI package release

**Success Criteria**:
- Multi-model support working
- Search history by semantic meaning
- Professional terminal UI
- Published on PyPI
- 80%+ test coverage

---

## Testing Strategy

### Unit Tests

```python
# tests/test_parser.py
def test_bash_prefix():
    parser = Parser()
    cmd = parser.parse("!ls -la")
    assert cmd.type == "bash"
    assert cmd.command == "ls -la"

def test_chat_prefix():
    parser = Parser()
    cmd = parser.parse("?How are you?")
    assert cmd.type == "chat"
    assert cmd.message == "How are you?"

# tests/test_registry.py
def test_register_tool():
    registry = ToolRegistry()

    def my_tool(x: int) -> int:
        return x * 2

    registry.register_from_function(my_tool)
    tool = registry.get("my_tool")
    assert tool is not None
    assert tool.function(5) == 10

# tests/test_pipeline.py
@pytest.mark.asyncio
async def test_simple_pipeline():
    bash_node = BashNode("echo hello")
    tool_node = ToolNode(summarize_tool)

    pipeline = Pipeline([bash_node, tool_node])

    output = ""
    async for chunk in pipeline.execute():
        output += chunk.decode()

    assert len(output) > 0
```

### Integration Tests

```python
# tests/integration/test_ollama.py
@pytest.mark.asyncio
async def test_ollama_streaming():
    adapter = OllamaAdapter(model="llama3.1")

    chunks = []
    async for chunk in adapter.stream("Say hello"):
        chunks.append(chunk)

    assert len(chunks) > 0
    assert "".join(chunks).strip() != ""

# tests/integration/test_end_to_end.py
@pytest.mark.asyncio
async def test_full_pipeline():
    """Test complete workflow: bash → AI → output."""
    repl = REPL(parser, engine, registry)

    result = await repl.execute("!echo 'test data' | summarize")

    assert "test data" in result or "summary" in result.lower()
```

### Evaluation Tests

```python
# tests/evals/test_tool_quality.py
def test_summarize_quality():
    """Test summarization preserves key information."""
    long_text = """
    [Long article about Python async...]
    """

    summary = summarize(long_text, max_length=50)

    # Check key concepts present
    assert "async" in summary.lower()
    assert len(summary.split()) <= 50

    # Semantic similarity check
    similarity = semantic_similarity(long_text, summary)
    assert similarity > 0.5  # Summary captures main ideas
```

---

## Security Considerations

### 1. Command Injection Prevention

**Risk**: User input interpreted as shell commands.

**Mitigation**:
- Never use `shell=True` with user-controlled strings
- Validate all command arguments
- Use `shlex.quote()` for argument escaping
- Human-in-the-loop approval for all bash execution

### 2. Prompt Injection Defense

**Risk**: Malicious input manipulating LLM behavior.

**Mitigation**:
- Use proper message structure (role-based)
- Never concatenate user input into system prompts
- Validate tool outputs before returning to LLM
- Sanitize sensitive data before sending to LLM

### 3. Data Leakage Prevention

**Risk**: Secrets (API keys, passwords) sent to LLM.

**Mitigation**:
```python
def sanitize_for_llm(text: str) -> str:
    """Remove sensitive patterns before sending to LLM."""
    patterns = {
        r'API_KEY=[\w-]+': 'API_KEY=[REDACTED]',
        r'password=[\w-]+': 'password=[REDACTED]',
        r'token=[\w-]+': 'token=[REDACTED]',
        r'sk-[a-zA-Z0-9]+': '[REDACTED_API_KEY]',
    }

    for pattern, replacement in patterns.items():
        text = re.sub(pattern, replacement, text)

    return text
```

### 4. Excessive Agency Control

**Risk**: AI executes dangerous operations without oversight.

**Mitigation**:
- Multi-level permission system (implemented)
- Audit logging (all commands logged)
- Sandboxed execution (future: Docker containers)
- Principle of least privilege (whitelist safe commands)

### 5. Dependency Security

**Risk**: Third-party vulnerabilities.

**Mitigation**:
- Pin all dependency versions
- Regular security audits (`pip-audit`)
- Minimal dependencies
- Review MCP servers before enabling

---

## Performance Optimization

### 1. Latency Reduction

**Streaming Everywhere**:
- Start displaying LLM responses immediately
- Stream bash output (not buffered)
- Pipeline stages stream between each other

**Parallel Execution**:
```python
# Execute independent tools in parallel
async with asyncio.TaskGroup() as tg:
    task1 = tg.create_task(tool1.execute())
    task2 = tg.create_task(tool2.execute())

results = [task1.result(), task2.result()]
```

**Caching**:
- Cache tool descriptions (expensive to generate)
- Cache LLM responses for identical inputs (optional)
- Memoize expensive operations

### 2. Memory Management

**Context Window Control**:
```python
def manage_context(messages, max_tokens=4000):
    """Truncate or summarize when approaching limit."""
    if count_tokens(messages) > max_tokens * 0.8:
        # Keep system + recent messages, summarize old
        summary = llm.summarize(messages[1:-10])
        return [messages[0], summary] + messages[-10:]
    return messages
```

**Bounded Queues**:
- Prevent memory bloat in pipelines
- Backpressure naturally controls memory usage

### 3. Cost Optimization

**Local-First Strategy**:
- Use Ollama for most operations (free)
- Fall back to cloud only when needed
- Track token usage per provider

**Model Selection**:
```python
def select_model(task_complexity):
    """Use cheapest capable model."""
    if task_complexity == "simple":
        return "llama3.1:8b"      # Fast, local
    elif task_complexity == "medium":
        return "llama3.1:70b"     # Capable, local
    else:
        return "gpt-4o"           # Most capable, cloud
```

---

## API Reference (Embeddable Library)

```python
from ai_shell import Agent, ToolRegistry, Pipeline, OllamaAdapter

# Initialize
model = OllamaAdapter(model="llama3.1")
registry = ToolRegistry()
agent = Agent(model, registry)

# Chat
async for token in agent.chat("Hello!"):
    print(token, end="")

# Execute task
result = await agent.execute("Summarize /path/to/file.txt")
print(result.answer)

# Build pipeline programmatically
from ai_shell import BashNode, ToolNode

pipeline = Pipeline([
    BashNode("du -sh *"),
    ToolNode(registry.get("summarize"))
])

async for chunk in pipeline.execute():
    print(chunk.decode(), end="")

# Register custom tool
@registry.register_tool(description="Multiply by 2")
def double(x: int) -> int:
    return x * 2

# Use MCP server
from ai_shell import MCPAdapter

mcp = MCPAdapter("npx @modelcontextprotocol/server-filesystem /tmp")
await mcp.connect()
registry.register_mcp_tools(mcp)
```

---

## Differentiators

### What Makes ai-shell Unique?

1. **Local-First Philosophy**
   - Privacy by default (Ollama primary)
   - Offline capable
   - No mandatory cloud dependencies

2. **True Unix Pipes for AI**
   - Natural `|` syntax works across Bash and AI
   - Compose complex workflows easily
   - Familiar mental model for shell users

3. **Human-in-the-Loop by Design**
   - Not autonomous - collaborative
   - Multi-level permission system
   - Dry-run mode and risk assessment

4. **MCP Ecosystem Integration**
   - Leverage growing MCP server ecosystem
   - Auto-discover and register tools
   - Standard protocol for extensibility

5. **Embeddable Agent Runtime**
   - Use as library, not just CLI
   - `from ai_shell import Agent`
   - Integrate into existing tools

6. **Transparent & Explainable**
   - Show reasoning (ReAct pattern)
   - Audit trail of all actions
   - Debug mode for detailed inspection

---

## Comparison with Existing Tools

| Feature | ai-shell | Warp | Aider | GitHub Copilot CLI | ShellGPT |
|---------|----------|------|-------|-------------------|----------|
| **Local LLM** | ✅ Primary | ❌ | ✅ | ❌ | ✅ |
| **Cloud LLM** | ✅ Optional | ✅ | ✅ | ✅ | ✅ |
| **Unix Pipes** | ✅ Native | ❌ | ❌ | ❌ | ❌ |
| **Human-in-the-Loop** | ✅ Multi-level | ⚠️ Basic | ⚠️ Basic | ✅ | ❌ |
| **MCP Support** | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Embeddable** | ✅ Python lib | ❌ | ⚠️ Limited | ❌ | ⚠️ Limited |
| **Open Source** | ✅ | ❌ | ✅ | ❌ | ✅ |
| **Streaming** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Session Memory** | ✅ SQLite | ✅ | ✅ | ✅ | ✅ |

---

## Future Enhancements

### Short-Term (3-6 months)

1. **Multi-Agent Patterns**
   - Specialized agents per task type
   - Agent handoffs (inspired by OpenAI Swarm)
   - Parallel agent execution

2. **Advanced Context Management**
   - Semantic history search (vector DB)
   - Automatic context summarization
   - Context-aware tool selection

3. **Enhanced UI**
   - Multiple terminal panes (WaveTerm style)
   - Visual file previews
   - Interactive approval flows

4. **Tool Ecosystem**
   - Official tool marketplace
   - Easy tool installation: `ai-shell install filesystem`
   - Community-contributed tools

### Long-Term (6-12 months)

1. **Collaborative Sessions**
   - Share sessions with team members
   - Real-time collaboration
   - Session replay for debugging

2. **Advanced Planning**
   - Plan-and-execute mode with DAG
   - Parallel step execution
   - Automatic replanning on failure

3. **Web Interface**
   - Browser-based UI (optional)
   - Remote access to ai-shell instance
   - Visual workflow builder

4. **Enterprise Features**
   - Team permission policies
   - Centralized audit logging
   - SSO integration

---

## References & Research

This design is informed by:

**Frameworks**:
- LangChain/LangGraph - State management, checkpointing patterns
- CrewAI - Role-based agent design
- Microsoft AutoGen - Human-in-the-loop patterns
- OpenAI Swarm - Agent handoff concepts

**Projects**:
- Warp Terminal - UX patterns for AI terminals
- Aider - Git-aware code assistance
- GitHub Copilot CLI - Tool permission system
- ShellGPT - REPL simplicity
- WaveTerm - Local LLM integration

**Specifications**:
- Model Context Protocol (MCP) - Tool integration standard
- OpenAI Function Calling - Structured outputs
- Anthropic Tool Use - Best practices guide

**Research Papers**:
- ReAct (Reasoning + Action) - Yao et al.
- ReWOO (Reasoning Without Observation) - Planning patterns
- Anthropic: "Building Effective Agents" (2024)
- OpenAI: "A Practical Guide to Building Agents"

---

## Contributing

See `CONTRIBUTING.md` for:
- How to add custom tools
- Development setup
- Testing guidelines
- Code style (Black, isort, mypy)

---

## License

MIT License - see `LICENSE` file.

---

## Conclusion

**ai-shell** brings AI assistance to the command line while respecting user control, privacy, and Unix philosophy. By combining local LLMs, human-in-the-loop safety, and natural pipe syntax, we create a powerful yet safe environment for AI-augmented computing.

**Key Innovations**:
1. Local-first with Ollama (privacy-focused)
2. True Unix pipes for AI tools (compose workflows)
3. Multi-level human-in-the-loop (collaborative, not autonomous)
4. MCP integration (extensible ecosystem)
5. Embeddable runtime (Python library)

**Next Steps**:
1. Begin Phase 1 implementation (MVP)
2. Build core components (Agent, Registry, Pipeline)
3. Iterate based on user feedback
4. Grow tool ecosystem

Let's build the future of AI-enhanced shells together.

---

**Document Version**: 2.0
**Date**: 2025-10-10
**Status**: Enhanced with 2024-2025 best practices
