# Command Executor Refactor - Summary

## Overview

Refactored the command execution architecture to provide a cleaner, more bash-like interface with integrated registry, proper argument parsing, and working pipelines.

## Changes Made

### 1. Redesigned Command Executor Interface

**Old Interface** (`ICommandExecutor` + `IToolRegistry`):
- Separate registry and executor
- `execute(command_name, args: List[str], input_data: Optional[str], context: Dict)`
- `input_data` parameter didn't map well to bash piping

**New Interface** (`ICommandExecutor` - registry merged in):
- Registry integrated into executor
- `execute(command_name, args: List[str], stdin: Optional[str], **options)`
- Bash-like arguments: positional args + `--option` flags
- Registry methods included: `register_command()`, `has_command()`, `get_command_names()`

### 2. Real CommandExecutor Implementation

Created `ai_shell/core/command_executor.py` with:
- **Registration**: `register_command(name, handler, description, category)`
  - Validates handler is async callable
  - Stores metadata for tab completion

- **Execution**: `execute(command_name, args=[], stdin=None, **options)`
  - Passes stdin from pipelines
  - Unpacks **options as keyword arguments to handler
  - Handles both string and CommandResult returns

- **Streaming**: `execute_streaming()` for async generator support

### 3. Updated Parser for --options

Enhanced `ai_shell/shell/parser.py`:
- Added `tool_options: Optional[dict]` to `ParsedCommand`
- Parse --flags and --key=value options
- Separate positional args from options
- Type conversion (bool, int, string)
- Short options (`-i`) support

**Example**:
```python
# Input: \count file.txt --lines
# Parsed: tool_name="count", tool_args=["file.txt"], tool_options={"lines": True}
```

### 4. Implemented Pipeline Execution

Updated `_handle_pipeline()` in `ai_shell/shell/repl.py`:
- Execute stages sequentially
- Pass output as stdin to next stage
- Support bash → tool and tool → bash
- Proper error handling with stage numbers

**Example pipelines**:
```bash
!cat file.txt | \upper
!ls *.py | \count --lines
!echo "test" | \grep "te" | \upper
```

### 5. Built-in Commands

Created command library in `ai_shell/commands/`:

**Text Commands** (`text_commands.py`):
- `\count` - Count lines, words, or characters
- `\upper` - Convert to uppercase
- `\lower` - Convert to lowercase
- `\reverse` - Reverse lines
- `\grep` - Search for patterns (--ignore-case, -i)
- `\head` - First N lines (--lines=N)
- `\tail` - Last N lines (--lines=N)

**File Commands** (`file_commands.py`):
- `\list` - List files (--all, --recursive)
- `\cat` - Display file contents
- `\tree` - Directory tree (--max-depth=N)
- `\find` - Find files by pattern (--path=/dir)

All commands support:
- File arguments: `\count file.txt`
- Stdin piping: `!cat file.txt | \count`
- Options: `\count file.txt --lines`

### 6. Command Handler Signature

Standardized handler signature:
```python
async def my_command(args: List[str], stdin: Optional[str] = None, **options):
    """
    Args:
        args: Positional arguments (file paths, etc.)
        stdin: Input from pipeline (if piped)
        **options: Keyword arguments from --flags

    Returns:
        str | CommandResult
    """
    pass
```

## Architecture Before/After

### Before
```
User Input → Parser → REPL
                        ↓
         IToolRegistry ← → ICommandExecutor (separate)
                        ↓
                   Mock/Real Implementation
```

### After
```
User Input → Parser (extracts args & options)
                        ↓
                    REPL
                        ↓
            CommandExecutor (integrated registry)
                        ↓
            Registered Command Handlers
```

## Benefits

1. **Simpler**: One component instead of two (executor + registry)
2. **Bash-like**: Arguments map naturally to bash conventions
3. **Options**: Clean `--flag` and `--key=value` support
4. **Pipelines**: Working stdin/stdout piping
5. **Extensible**: Easy to register new commands
6. **Testable**: Commands are simple async functions

## Usage Examples

### Register a Command
```python
executor = CommandExecutor()

async def summarize(args, stdin=None, **options):
    text = stdin if stdin else open(args[0]).read()
    max_length = options.get('max_length', 500)
    # ... summarize text ...
    return summary

executor.register_command("summarize", summarize,
                         "Summarize text or files")
```

### Use in Shell
```bash
# Direct file
ai> \summarize report.txt --max-length=300

# From pipeline
ai> !cat *.log | \summarize

# Multi-stage pipeline
ai> !find . -name "*.py" | \count --lines
```

## Testing

Shell now works with real commands:
```bash
$ python -m ai_shell --debug
Registered 11 commands: count, upper, lower, reverse, grep, head, tail, list, cat, tree, find
Using native bash backend

ai> \count README.md
Lines: 147, Words: 892, Characters: 5432

ai> !echo "hello world" | \upper
HELLO WORLD

ai> !cat README.md | \head --lines=5 | \grep "ai"
ai-shell
An AI-enhanced interactive shell...
```

## Files Changed

- `ai_shell/core/interfaces.py` - Updated `ICommandExecutor` interface
- `ai_shell/core/command_executor.py` - **New**: Real implementation
- `ai_shell/commands/` - **New directory**:
  - `__init__.py` - Registration helper
  - `text_commands.py` - Text processing commands
  - `file_commands.py` - File operation commands
- `ai_shell/shell/parser.py` - Added option parsing
- `ai_shell/shell/repl.py` - Updated tool/pipeline handling
- `ai_shell/__main__.py` - Register built-in commands

## Next Steps

1. **Add More Commands**: Easy to add new commands following the pattern
2. **Streaming Support**: Some commands could stream results
3. **Context Passing**: Add context dict for memory/variables
4. **Error Handling**: Enhanced error messages with suggestions
5. **Documentation**: Auto-generate command help from docstrings

## Migration Notes

- Removed `IToolRegistry` interface (merged into `ICommandExecutor`)
- Changed `input_data` parameter to `stdin` (clearer naming)
- Added `**options` for --flag support
- Commands now return strings directly (auto-wrapped in CommandResult)
- Mock implementations still work but now optional

## Conclusion

The refactored command executor provides a clean, extensible foundation for building agentic commands with bash-like ergonomics. The integrated registry, option parsing, and working pipelines make it easy to compose complex workflows while maintaining simplicity for individual commands.
