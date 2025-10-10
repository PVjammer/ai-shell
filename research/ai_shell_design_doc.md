# AI Shell Design Document

## Overview

**Project name:** ai-shell  
**Goal:** Build a **local-first, human-in-the-loop AI shell** that unifies **LLMs**, **Bash**, and **MCP tools** into a single interactive environment.

The `ai-shell` lets users:
- **Chat** with a local LLM (e.g., via Ollama).
- **Run AI tools** (e.g., `summarize`, `search`, `report`) directly from the command line.
- **Execute Bash commands** and pipe results to/from AI tools.
- **Integrate MCP servers** for access to structured external tools (filesystem, browser, git, etc.).
- **Supervise AI actions** before they are executed — achieving true *human-in-the-loop* operation.

---

## Key Design Principles

1. **Local-first**: Primary runtime via Ollama; optional cloud adapters.
2. **Human-in-the-loop**: Agent proposes actions but requires user confirmation.
3. **Composable workflows**: Unified pipe syntax across AI tools and Bash.
4. **Extensible by design**: Support Python modules, MCP servers, or config-based tools.
5. **Transparent execution**: All steps logged and explainable.
6. **Embeddable runtime**: Agent engine importable as Python library.

---

## System Architecture

**Components:**
- REPL / CLI (`repl.py`)
- Parser (`parser.py`)
- ToolRegistry (`registry.py`)
- PipelineEngine (`pipeline.py`)
- BashExecutor (`bash_executor.py`)
- ModelAdapter(s) (`adapters/ollama.py`, `adapters/openai.py`)
- BaseAgent (`core/agent.py`)
- MCPAdapter (`mcp_adapter.py`)
- MemoryStore (`memory.py`)
- Renderer (`renderer.py`)
- Config (`config.py`)

**High-level flow:**
```
User Input -> REPL -> Parser -> Command Type -> Execute -> Renderer -> Display Output
```

---

## Core Components

### BaseAgent
- Reasoning, planning, action proposals.
- Methods: `plan()`, `execute()`, `chat()`, `summarize()`.

### ToolRegistry
- Catalog of AI and system tools.
- Auto-register MCP tools.

### PipelineEngine
- Orchestrates nodes (Bash/AI) into pipelines.
- Supports streaming and async execution.

### Shell (REPL)
- Interactive loop parsing input prefixes.
- Executes AI, Bash, or hybrid pipelines.
- Shows streaming model output.

---

## Shell Input Grammar

| Prefix | Meaning | Example |
|--------|---------|--------|
| `!` | Bash command | `!ls -l` |
| `?` | Ask AI agent | `?How do I check disk usage?` |
| `\` | Explicit AI tool | `\summarize report.txt` |
| none | Auto-resolve | Try AI tool, fallback to Bash, else LLM |

---

## Sequence Diagram: `!du -sh * | summarize`
```
User -> REPL: '!du -sh * | summarize'
REPL -> Parser: parse into [BashNode, ToolNode]
PipelineEngine -> BashNode: run(stdin=None)
BashNode -> OS/Subproc: spawn('du -sh *')
BashNode -> PipelineEngine: stdout stream
PipelineEngine -> ToolNode: stdin stream
ToolNode -> ModelAdapter: summarize input
ModelAdapter -> LLM: prompt
LLM -> ModelAdapter: tokens
ToolNode -> PipelineEngine: summary
PipelineEngine -> REPL: final bytes
REPL -> Renderer: print summary
```

---

## Technical Details

- **Streaming**: Live token output from models.
- **Data formats**: UTF-8 bytes, JSON lines optional.
- **Safety & sandboxing**: Confirmation required for destructive commands.
- **Error handling**: Node failures propagate structured result.
- **Tab completion**: AI + Bash + MCP tools.
- **Logging**: JSON or SQLite, optional debug for token streaming.

---

## MCP & A2A Integration

- MCPAdapter discovers servers and wraps tools.
- A2A future: Remote agents can be wrapped as `RemoteAgentTool`.
- Authentication and capability filters included.

---

## UX Design

- Prefixes (`!`, `?`, `\`) distinguish command types.
- Default mode: AI-first.
- Pipeline chaining with `|`.
- Variables (`$last`, `$summary`) for reuse.
- Human-in-the-loop for agent-proposed commands.

---

## Package Structure

```
ai_shell/
├── core/
│   ├── agent.py
│   ├── registry.py
│   ├── pipeline.py
│   ├── mcp_adapter.py
│   ├── bash_executor.py
│   └── memory.py
├── shell/
│   ├── repl.py
│   ├── parser.py
│   ├── renderer.py
│   └── completer.py
├── adapters/
│   ├── ollama.py
│   ├── openai.py

