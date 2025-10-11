# Quick Start Guide

## Installation

```bash
cd /home/nick/Workspace/src/github.com/PVjammer/ai-shell
pip install -e .
```

## Running ai-shell

```bash
# Basic
python -m ai_shell

# Or
ai-shell

# With debug mode
ai-shell --debug

# Custom prompt
ai-shell --prompt="🤖 "
```

## Try These Commands

### Chat with AI (mock)
```bash
ai> ?Hello, how are you?
ai> ?What is Python?
ai> ?Tell me about AI
```

### Run Bash Commands (mock)
```bash
ai> !ls
ai> !pwd
ai> !echo "Hello World"
ai> !cat somefile.txt
```

### Use AI Tools (mock)
```bash
ai> \summarize "This is a long text that needs summarizing"
ai> \search "Python tutorials"
ai> \analyze "Some data to analyze"
ai> \explain "def hello(): print('world')"
```

### Pipelines (parsed but not executed yet)
```bash
ai> !cat file.txt | \summarize
ai> \search "topic" | !grep "keyword"
```

### Meta Commands
```bash
ai> /help        # Show help
ai> /history     # Show command history
ai> /clear       # Clear session
ai> /save        # Save session
ai> /sessions    # List sessions
ai> /exit        # Exit (or Ctrl+D)
```

### Tab Completion

Press `Tab` to complete:
- Meta commands: `/h[Tab]` → `/help`
- Tools: `\sum[Tab]` → `\summarize`
- Files: `./Read[Tab]` → `./README.md`
- Shell commands: `l[Tab]` → `ls`

### Auto-Resolution (No Prefix)

```bash
ai> ls           # Detected as bash (common command)
ai> summarize    # Detected as tool (if in registry)
ai> Hello there  # Falls back to chat
```

## Keyboard Shortcuts

- `Ctrl+D` - Exit shell
- `Ctrl+C` - Cancel current operation
- `↑` / `↓` - Navigate command history
- `Tab` - Auto-complete
- `Ctrl+R` - Search history (prompt-toolkit feature)

## Current State

The shell is **fully functional**:

✅ **Working with REAL backends:**
- ✅ **Bash commands** - REAL! Runs actual commands
- All input parsing
- Tab completion
- Command history
- Meta commands
- Beautiful terminal output
- Session management
- Error handling

⏳ **Mock Mode:**
- AI responses are canned (not real LLM)
- Tool outputs are simulated
- Pipelines are parsed but not executed

## Next Steps

When you're ready to add real functionality:

1. **Implement Real Agent** (you do this)
   - Follow `IAgent` interface in `ai_shell/core/interfaces.py`
   - Pass to REPL: `repl = REPL(..., agent=YourAgent())`

2. **Add Real Tools** (you do this)
   - Create Python files in `~/.ai_shell/tools/`
   - Use `@tool` decorator
   - Auto-discovered on startup

3. **Pipeline Engine** (future)
   - Connect parser output to execution
   - Stream data between stages

## Debugging

Enable debug mode to see detailed errors:

```bash
ai-shell --debug
```

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run parser tests
pytest tests/shell/test_parser.py -v

# With coverage
pytest --cov=ai_shell tests/
```

## Project Structure

```
ai_shell/
├── core/          # Core components
│   ├── interfaces.py   # Abstract interfaces
│   └── memory.py       # Storage
├── shell/         # Shell layer (complete!)
│   ├── repl.py         # Main loop
│   ├── parser.py       # Input parsing
│   ├── renderer.py     # Output display
│   ├── completer.py    # Tab completion
│   └── commands.py     # Meta commands
├── mocks/         # Mock implementations
│   ├── agent.py
│   ├── executor.py
│   ├── registry.py
│   └── bash.py
└── utils/         # Utilities
```

## Documentation

- `README.md` - Project overview
- `Design.md` - Enhanced design document
- `SHELL_IMPLEMENTATION_PLAN.md` - Shell implementation details
- `MOCK_AND_PLUGIN_PLAN.md` - Mock and plugin architecture
- `IMPLEMENTATION_STATUS.md` - Current status and next steps

## Getting Help

Within the shell:
```bash
ai> /help
```

For development questions, check the design documents in the repo.

Enjoy exploring ai-shell! 🚀
