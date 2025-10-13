# Real Bash Executor Added! 🎉

## What Changed

The shell now uses a **real bash executor** instead of mock! This means you can see your actual files and run real commands.

## What Works Now

### ✅ Real Bash Commands
```bash
ai> !ls                  # Shows YOUR files
ai> !pwd                 # Shows YOUR directory
ai> !cat filename.txt    # Reads YOUR files
ai> !echo "Hello"        # Real output
ai> !git status          # Real git commands
```

### ⚠️ Still Mock
- AI Chat (`?`) - Still returns canned responses
- AI Tools (`\summarize`, `\search`, etc.) - Still mock outputs
- Pipelines - Parsed but not executed

## Files Added

- **`ai_shell/core/bash_executor.py`** - Real bash executor using asyncio subprocess
- **`test_real_bash.py`** - Test script proving it works

## Try It Now

```bash
# Reinstall (already done)
pip install -e .

# Run the shell
python -m ai_shell

# You'll see in welcome:
# Backends: bash=real agent=mock tools=mock
#           ^^^^---- Now green!

# Try real commands:
ai> !ls
ai> !pwd
ai> !echo $PWD
ai> !cat README.md
ai> !git log --oneline -5
```

## How It Works

The new `BashExecutor` uses Python's `asyncio.create_subprocess_shell()` to:
1. Execute real shell commands
2. Capture stdout and stderr
3. Handle timeouts (default 30 seconds)
4. Return proper error codes
5. Support piped input (for future pipelines)

## Backend Status Display

The welcome message now shows which backends are real vs mock:

```
┌─────── Welcome ───────┐
│ ai-shell v0.1.0       │
│                       │
│ Type /help for help   │
│ Ctrl+D to exit        │
│                       │
│ Backends:             │
│ bash=real (green)     │  ← Real!
│ agent=mock (yellow)   │  ← Still mock
│ tools=mock (yellow)   │  ← Still mock
└───────────────────────┘
```

## Safety Note

Since bash commands are now **real**, be careful with destructive commands like `rm`, `mv`, etc. They will actually modify your filesystem!

Future enhancement: Add permission system to ask before running dangerous commands.

## Next Steps

Now you can:
1. ✅ Run real bash commands - **WORKS NOW!**
2. ⏳ Add your AI agent (still needed)
3. ⏳ Add your AI tools (still needed)
4. ⏳ Connect pipelines (still needed)

The shell is getting more real! 🚀

## Code Example

If you want to use the real bash executor in your own code:

```python
from ai_shell.core.bash_executor import BashExecutor
from ai_shell.shell.repl import REPL

# Create with real bash
bash = BashExecutor()
repl = REPL(
    parser=Parser(),
    renderer=Renderer(),
    memory=MemoryStore(),
    bash_executor=bash  # Real bash!
)

await repl.start()
```

Enjoy running real commands! 🎊
