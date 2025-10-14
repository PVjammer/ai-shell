# ai-shell

An AI-enhanced interactive shell with local-first LLMs and human-in-the-loop design.

## Features

- 🤖 **AI Integration**: Chat with AI agents and run agentic commands
- 🔧 **Unified Interface**: Mix Bash and AI commands naturally
- 🔌 **Plugin System**: Easy-to-extend with custom tools
- 🔒 **Local-First**: Works with local LLMs (Ollama) - privacy by default
- 🛡️ **Human-in-the-Loop**: Safe AI operations with approval workflows
- 📝 **Command History**: Persistent history across sessions

## Installation

```bash
# Clone repository
git clone https://github.com/PVjammer/ai-shell.git
cd ai-shell

# Install in development mode
pip install -e .

# Or install with dev dependencies
pip install -e ".[dev]"
```

## Quick Start

```bash
# Run with native bash (direct execution)
python -m ai_shell

# Run with Docker backend (sandboxed, safer)
python -m ai_shell --bash-backend=docker

# Or if installed as script
ai-shell
ai-shell --bash-backend=docker
```

## Usage

### Prefix System

- `!cmd` - Run bash command: `!ls -la`
- `?text` - Chat with AI: `?How do I list files?`
- `\tool` - Run AI tool: `\summarize file.txt`
- `/cmd` - Meta command: `/help`
- No prefix - Auto-resolve (tool → bash → chat)

### Examples

```bash
# Chat with AI
ai> ?What is Python?

# Run bash command
ai> !ls -la

# Use AI tool
ai> \summarize README.md

# Pipeline bash → AI
ai> !cat report.txt | \summarize

# Meta commands
ai> /help
ai> /history
ai> /exit
```

## Project Status

**Current Phase**: Shell Implementation ✅

- [x] Core interfaces and mocks
- [x] Parser (all command types)
- [x] Renderer (markdown, syntax highlighting)
- [x] Tab completion
- [x] Command history
- [x] Meta commands
- [x] REPL with streaming

**Next Phase**: Agent & Tool Integration

- [ ] Real agent implementation
- [ ] Tool registry and executor
- [ ] Pipeline engine
- [ ] MCP integration

## Development

```bash
# Run tests
pytest

# Run tests with coverage
pytest --cov=ai_shell

# Format code
black ai_shell tests
isort ai_shell tests

# Type checking
mypy ai_shell
```

## Architecture

```
ai_shell/
├── core/          # Core interfaces and components
│   ├── interfaces.py   # Abstract interfaces
│   └── memory.py       # Memory/history storage
├── shell/         # Shell layer (REPL, parser, renderer)
│   ├── repl.py         # Main REPL loop
│   ├── parser.py       # Input parser
│   ├── renderer.py     # Output renderer
│   ├── completer.py    # Tab completion
│   └── commands.py     # Meta commands
├── mocks/         # Mock implementations for testing
│   ├── agent.py
│   ├── executor.py
│   ├── registry.py
│   └── bash.py
└── utils/         # Utilities
```

## Current State (Mock Mode)

The shell currently runs with **mock backends** for:
- AI Agent (canned responses)
- Command Executor (mock tool outputs)
- Bash Executor (simulated bash)
- Tool Registry (pre-defined tools)

This allows the shell to be developed and tested independently while real components are being built.

## Contributing

See `SHELL_IMPLEMENTATION_PLAN.md` and `MOCK_AND_PLUGIN_PLAN.md` for detailed implementation plans.

## License

MIT License - see LICENSE file for details.
