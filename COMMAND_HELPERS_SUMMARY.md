# Command Helpers - Summary

## What We Built

Created a **lightweight helper library** for writing bash-like commands with minimal boilerplate.

## Files Created

- **`ai_shell/core/command_helpers.py`** - Helper functions library
- **`COMMAND_HELPERS_GUIDE.md`** - Comprehensive usage guide
- Updated **`ai_shell/commands/text_commands.py`** - Refactored to use helpers

## Key Features

### 1. Smart Input Resolution

```python
text = get_input_text(args, stdin, file_flag=False)
```

Automatically handles:
- ✅ `\count "hello world"` - Direct text
- ✅ `\count file.txt` - File (auto-detected)
- ✅ `!cat file.txt | \count` - Stdin pipe
- ✅ `\count --file file.txt` - Explicit file mode

### 2. Multi-Name Flag Parsing

```python
verbose = parse_flag(options, 'verbose', 'v')
lines = parse_flag(options, 'lines', 'l')
```

Supports both long and short forms automatically.

### 3. Type-Safe Options

```python
count = parse_option(options, 'count', 'n', default=10, type_fn=int)
format = parse_option(options, 'format', 'f', default='json')
```

With automatic type conversion.

### 4. Easy Error Handling

```python
text = get_input_text(args, stdin)
if is_error(text):
    return text  # Propagate error
```

Simple, consistent error checking.

## Before/After Comparison

### Before (without helpers)

```python
async def count_cmd(args, stdin=None, **options):
    if stdin:
        text = stdin
    elif args:
        try:
            with open(args[0], 'r') as f:
                text = f.read()
        except FileNotFoundError:
            return f"Error: File not found: {args[0]}"
        except Exception as e:
            return f"Error reading file: {e}"
    else:
        return "Usage: \\count <file> or pipe text"

    lines = len(text.splitlines())
    words = len(text.split())
    chars = len(text)

    if options.get('lines') or options.get('l'):
        return str(lines)
    elif options.get('words') or options.get('w'):
        return str(words)
    # ... etc
```

**Issues**:
- ❌ Always tries to open as file (no direct text support)
- ❌ Repetitive error handling
- ❌ Duplicate flag checking (`options.get('lines') or options.get('l')`)

### After (with helpers)

```python
async def count_cmd(args, stdin=None, **options):
    # Get input with smart file/text resolution
    text = get_input_text(args, stdin, file_flag=parse_flag(options, 'file', 'f'))
    if is_error(text):
        return text

    # Count
    lines = len(text.splitlines())
    words = len(text.split())
    chars = len(text)

    # Check flags
    if parse_flag(options, 'lines', 'l'):
        return str(lines)
    elif parse_flag(options, 'words', 'w'):
        return str(words)
    elif parse_flag(options, 'chars', 'c'):
        return str(chars)
    else:
        return f"Lines: {lines}, Words: {words}, Characters: {chars}"
```

**Benefits**:
- ✅ Direct text: `\count "hello"`
- ✅ Auto-detect files: `\count file.txt`
- ✅ Explicit files: `\count --file file.txt`
- ✅ Clean error handling
- ✅ Multi-name flags

## Helper Functions

| Function | Purpose | Example |
|----------|---------|---------|
| `get_input_text()` | Smart text/file/stdin resolution | `text = get_input_text(args, stdin)` |
| `get_input_lines()` | Same but returns list of lines | `lines = get_input_lines(args, stdin)` |
| `parse_flag()` | Multi-name boolean flags | `verbose = parse_flag(options, 'verbose', 'v')` |
| `parse_option()` | Multi-name options with type conversion | `n = parse_option(options, 'count', 'n', default=10, type_fn=int)` |
| `is_error()` | Check if result is error | `if is_error(text): return text` |
| `require_args()` | Validate argument count | `if error := require_args(args, min_count=1): return error` |
| `parse_file_list()` | Parse file list (with globs) | `files = parse_file_list(args, patterns=True)` |

## Updated Commands

Refactored text commands to use helpers:
- `count` / `wc` - Word count
- `upper` - Uppercase
- `lower` - Lowercase
- `reverse` - Reverse lines
- `grep` - Search
- `head` - First N lines
- `tail` - Last N lines
- `sort` - Sort (new!)
- `uniq` - Remove duplicates (new!)

All now support:
- Direct text input
- File input (auto-detect)
- Stdin pipes
- Short and long flags

## Testing

```bash
$ python -c "
import asyncio
from ai_shell.commands.text_commands import count_cmd

async def test():
    # Direct text - NEW!
    print(await count_cmd(['Hello I am a little bird']))
    # → Lines: 1, Words: 6, Characters: 24

    # File
    print(await count_cmd(['README.md']))
    # → Lines: 146, Words: 489, Characters: 3158

    # Stdin
    print(await count_cmd([], 'Hello from pipe'))
    # → Lines: 1, Words: 3, Characters: 15

    # With flags
    print(await count_cmd(['Hello world'], None, lines=True))
    # → 1

asyncio.run(test())
"
```

All tests pass! ✅

## Design Decision: Custom vs Click

We chose **custom helpers** over Click because:

1. **Async-first**: Designed for async command handlers
2. **Return-based**: Errors return strings, not exceptions/sys.exit()
3. **Simpler**: Just what we need for shell commands
4. **Shell-optimized**: Features like smart file/text resolution
5. **Evolution path**: Can add more structure later if needed

## Example: Writing a New Command

```python
from ai_shell.core.command_helpers import (
    get_input_text,
    parse_flag,
    parse_option,
    is_error
)

async def my_cmd(args, stdin=None, **options):
    """My awesome command."""

    # Get input (smart resolution)
    text = get_input_text(args, stdin,
                         file_flag=parse_flag(options, 'file', 'f'))
    if is_error(text):
        return text

    # Parse options
    verbose = parse_flag(options, 'verbose', 'v')
    max_len = parse_option(options, 'max-length', 'max',
                          default=100, type_fn=int)

    # Process
    result = process(text, verbose, max_len)
    return result

# Register
executor.register_command("my", my_cmd, "My awesome command")
```

That's it! Just 15 lines for a fully-featured command.

## Next Steps

Helpers are now ready for:
1. **More built-in commands**: Easy to add with this pattern
2. **User commands**: Users can write custom commands easily
3. **NAT integration**: Can wrap NAT workflows with same interface
4. **Future structure**: Can add declarative layer later if patterns emerge

## Key Insight

The helpers solve the core problem: **making commands bash-like without boilerplate**.

Users expect:
- `\cmd "text"` - Direct text
- `\cmd file.txt` - File
- `!cat file.txt | \cmd` - Pipe

We now support all three naturally, with clean code.
