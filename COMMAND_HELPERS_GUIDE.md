# Command Helpers Guide

## Overview

The command helpers library (`ai_shell/core/command_helpers.py`) provides utilities for writing bash-like commands with minimal boilerplate. This guide shows how to use them effectively.

## Philosophy

Commands should be:
- **Bash-like**: Support text, files, and pipes naturally
- **Flexible**: Accept multiple flag names (--verbose, -v)
- **Smart**: Auto-detect files vs text
- **Simple**: Minimal code, clear intent

## Quick Start

### Minimal Example

```python
from ai_shell.core.command_helpers import get_input_text, is_error

async def upper_cmd(args, stdin=None, **options):
    """Convert text to uppercase."""
    text = get_input_text(args, stdin)
    if is_error(text):
        return text
    return text.upper()
```

This 7-line command supports:
- `\upper "hello"` - Direct text
- `\upper file.txt` - File (auto-detected)
- `!cat file.txt | \upper` - Stdin pipe

### With Options

```python
from ai_shell.core.command_helpers import (
    get_input_text,
    parse_flag,
    parse_option,
    is_error
)

async def format_cmd(args, stdin=None, **options):
    """Format text with various options."""

    # Get input (smart file/text resolution)
    text = get_input_text(args, stdin,
                         file_flag=parse_flag(options, 'file', 'f'))
    if is_error(text):
        return text

    # Parse options with multiple names
    uppercase = parse_flag(options, 'upper', 'u')
    width = parse_option(options, 'width', 'w', default=80, type_fn=int)
    indent = parse_option(options, 'indent', 'i', default=0, type_fn=int)

    # Process
    if uppercase:
        text = text.upper()

    # Format with width and indent
    # ... formatting logic ...

    return formatted_text
```

Usage:
```bash
\format "hello world" --upper --width=40 --indent=4
\format file.txt -u -w 40 -i 4
!cat file.txt | \format --upper
```

## Helper Functions Reference

### get_input_text()

Smart resolution of text from args, stdin, or files.

```python
text = get_input_text(args, stdin, file_flag=False, encoding='utf-8')
```

**Behavior**:
1. **Stdin first**: If `stdin` provided, use it (from pipe)
2. **File auto-detect**: If single arg and exists as file, read it
3. **Explicit file**: If `file_flag=True`, force file mode (error if not found)
4. **Text fallback**: Otherwise treat args as text

**Returns**: String (text or error starting with "Error:")

**Examples**:
```python
# From pipe
text = get_input_text([], stdin="hello")
# → "hello"

# Direct text
text = get_input_text(["hello world"])
# → "hello world"

# Auto-detected file
text = get_input_text(["README.md"])
# → (file contents)

# Non-existent file → text
text = get_input_text(["nonexistent.txt"])
# → "nonexistent.txt" (treated as text)

# Explicit file (errors if not found)
text = get_input_text(["nonexistent.txt"], file_flag=True)
# → "Error: File not found: nonexistent.txt"
```

### get_input_lines()

Same as `get_input_text()` but returns list of lines.

```python
lines = get_input_lines(args, stdin, file_flag=False, encoding='utf-8')
```

**Returns**: `List[str]` or error string

**Example**:
```python
lines = get_input_lines(["line1\nline2\nline3"])
# → ["line1", "line2", "line3"]
```

### parse_flag()

Parse boolean flags with multiple possible names.

```python
value = parse_flag(options, *names, default=False)
```

**Examples**:
```python
# Check for --verbose or -v
verbose = parse_flag(options, 'verbose', 'v')

# With default
debug = parse_flag(options, 'debug', 'd', default=False)
```

### parse_option()

Parse option with multiple names and type conversion.

```python
value = parse_option(options, *names, default=None, type_fn=None)
```

**Examples**:
```python
# String option
format = parse_option(options, 'format', 'f', default='json')

# Integer with conversion
max_len = parse_option(options, 'max-length', 'max', 'l',
                      default=100, type_fn=int)

# Float
threshold = parse_option(options, 'threshold', 't',
                        default=0.5, type_fn=float)
```

### is_error()

Check if result is an error message.

```python
if is_error(result):
    return result  # Propagate error
```

Checks for strings starting with "Error:".

### require_args()

Validate argument count.

```python
error = require_args(args, min_count=None, max_count=None, usage=None)
if error:
    return error
```

**Examples**:
```python
# Exactly 1 argument
if error := require_args(args, min_count=1, max_count=1,
                        usage=r"\cmd <file>"):
    return error

# At least 1, at most 3
if error := require_args(args, min_count=1, max_count=3):
    return error

# At least 2
if error := require_args(args, min_count=2,
                        usage=r"\cmd <input> <output>"):
    return error
```

### parse_file_list()

Parse arguments as file paths (with optional glob patterns).

```python
files = parse_file_list(args, stdin=None, patterns=False)
if is_error(files):
    return files

for file in files:
    # Process each file
    ...
```

**Examples**:
```python
# Multiple files
files = parse_file_list(["file1.txt", "file2.txt"])

# With glob patterns
files = parse_file_list(["*.py"], patterns=True)

# From stdin (newline-separated)
files = parse_file_list([], stdin="file1.txt\nfile2.txt\n")
```

## Common Patterns

### Pattern 1: Text Processing

Commands that transform text:

```python
async def my_transform_cmd(args, stdin=None, **options):
    """Transform text in some way."""
    # Get input
    text = get_input_text(args, stdin,
                         file_flag=parse_flag(options, 'file', 'f'))
    if is_error(text):
        return text

    # Parse options
    flag1 = parse_flag(options, 'flag1', 'f1')
    option1 = parse_option(options, 'option1', 'o', default='value')

    # Transform
    result = transform(text, flag1, option1)

    return result
```

### Pattern 2: Line-by-Line Processing

Commands that operate on lines:

```python
async def my_line_cmd(args, stdin=None, **options):
    """Process lines of text."""
    # Get lines
    lines = get_input_lines(args, stdin,
                           file_flag=parse_flag(options, 'file', 'f'))
    if is_error(lines):
        return lines

    # Process each line
    results = []
    for line in lines:
        result = process_line(line)
        results.append(result)

    return "\n".join(results)
```

### Pattern 3: Multiple File Processing

Commands that work on multiple files:

```python
async def my_multi_file_cmd(args, stdin=None, **options):
    """Process multiple files."""
    # Get file list (with glob support)
    files = parse_file_list(args, stdin, patterns=True)
    if is_error(files):
        return files

    # Process each file
    results = []
    for file in files:
        content = file.read_text()
        result = process(content)
        results.append(f"{file.name}: {result}")

    return "\n".join(results)
```

### Pattern 4: Argument Validation

Commands with specific argument requirements:

```python
async def my_cmd(args, stdin=None, **options):
    """Do something with exactly 2 arguments."""
    # Validate argument count
    if error := require_args(args, min_count=2, max_count=2,
                            usage=r"\cmd <input> <output>"):
        return error

    input_file = args[0]
    output_file = args[1]

    # ... process ...
```

### Pattern 5: Format Conversion

Commands that convert between formats:

```python
async def convert_cmd(args, stdin=None, **options):
    """Convert between formats."""
    # Get input
    text = get_input_text(args, stdin,
                         file_flag=parse_flag(options, 'file', 'f'))
    if is_error(text):
        return text

    # Parse format options
    from_fmt = parse_option(options, 'from', 'f', default='auto')
    to_fmt = parse_option(options, 'to', 't', default='json')

    # Convert
    result = convert(text, from_fmt, to_fmt)

    return result
```

## Real-World Examples

### Example 1: Word Count

```python
async def count_cmd(args, stdin=None, **options):
    """Count lines, words, or characters in text."""
    # Get input with smart file/text resolution
    text = get_input_text(args, stdin,
                         file_flag=parse_flag(options, 'file', 'f'))
    if is_error(text):
        return text

    # Count
    lines = len(text.splitlines())
    words = len(text.split())
    chars = len(text)

    # Check output flags
    if parse_flag(options, 'lines', 'l'):
        return str(lines)
    elif parse_flag(options, 'words', 'w'):
        return str(words)
    elif parse_flag(options, 'chars', 'c'):
        return str(chars)
    else:
        return f"Lines: {lines}, Words: {words}, Characters: {chars}"
```

Usage:
```bash
\count "hello world"                    # Direct text
\count file.txt                         # File
\count file.txt --lines                 # Only lines
\count file.txt -l                      # Short form
!cat file.txt | \count                  # Pipe
```

### Example 2: Grep

```python
async def grep_cmd(args, stdin=None, **options):
    """Search for pattern in text."""
    # Need at least pattern argument
    if not args:
        return r"Usage: \grep <pattern> [text or file]"

    pattern = args[0]
    ignore_case = parse_flag(options, 'ignore-case', 'i')

    # Get text from remaining args or stdin
    search_args = args[1:] if len(args) > 1 else []
    text = get_input_text(search_args, stdin,
                         file_flag=parse_flag(options, 'file', 'f'))
    if is_error(text):
        return text

    # Search
    lines = text.splitlines()
    matches = []
    for line in lines:
        if ignore_case:
            if pattern.lower() in line.lower():
                matches.append(line)
        else:
            if pattern in line:
                matches.append(line)

    return "\n".join(matches) if matches else "(no matches)"
```

Usage:
```bash
\grep "error" "some log text"
\grep "error" log.txt
\grep "ERROR" log.txt --ignore-case
!cat log.txt | \grep "error" -i
```

### Example 3: Sort

```python
async def sort_cmd(args, stdin=None, **options):
    """Sort lines of text."""
    # Get input as lines
    lines = get_input_lines(args, stdin,
                           file_flag=parse_flag(options, 'file', 'f'))
    if is_error(lines):
        return lines

    # Parse options
    reverse = parse_flag(options, 'reverse', 'r')
    unique = parse_flag(options, 'unique', 'u')

    # Sort
    sorted_lines = sorted(lines, reverse=reverse)

    # Remove duplicates if requested
    if unique:
        sorted_lines = list(dict.fromkeys(sorted_lines))

    return "\n".join(sorted_lines)
```

Usage:
```bash
\sort "zebra\napple\nbanana"
\sort file.txt --reverse
\sort file.txt -r -u
!cat file.txt | \sort
```

## Best Practices

### 1. Always Check for Errors

```python
text = get_input_text(args, stdin)
if is_error(text):
    return text  # Propagate error immediately
```

### 2. Support Both Long and Short Flags

```python
verbose = parse_flag(options, 'verbose', 'v')
max_len = parse_option(options, 'max-length', 'max', 'm')
```

### 3. Provide Good Usage Messages

```python
if not args:
    return r"Usage: \cmd <input> [options]"

if error := require_args(args, min_count=1,
                        usage=r"\cmd <input> --output <file>"):
    return error
```

### 4. Use Type Conversion for Numeric Options

```python
count = parse_option(options, 'count', 'n', default=10, type_fn=int)
threshold = parse_option(options, 'threshold', 't', default=0.5, type_fn=float)
```

### 5. Document All Options in Docstring

```python
async def my_cmd(args, stdin=None, **options):
    r"""
    Do something useful.

    Usage:
        \cmd <input>              # Basic usage
        \cmd <input> --flag       # With flag
        \cmd <input> --opt=val    # With option
        \cmd --file input.txt     # Explicit file

    Options:
        --flag, -f      Enable flag
        --opt, -o       Set option value
        --file          Treat input as file path
    """
```

## Tips

### When to Use file_flag

Use `file_flag=True` when:
- File path is required (not optional)
- Ambiguity between file path and text is likely
- You want explicit error if file doesn't exist

```python
# Auto-detect (permissive)
text = get_input_text(args, stdin)

# Explicit file (strict)
text = get_input_text(args, stdin,
                     file_flag=parse_flag(options, 'file', 'f'))
```

### Multiple Input Sources

Commands can accept input from any source:

```python
async def flexible_cmd(args, stdin=None, **options):
    """Accept input from anywhere."""

    # Try to get input from various sources
    if stdin:
        text = stdin
    elif args:
        text = get_input_text(args, None)
        if is_error(text):
            return text
    else:
        # Could also read from clipboard, URL, etc.
        return "Error: No input provided"
```

### Combining Commands

Commands compose naturally through pipes:

```bash
# Text processing pipeline
!cat log.txt | \grep "error" | \sort | \uniq | \count --lines

# Format and analyze
!echo "HELLO WORLD" | \lower | \count --words
```

## Summary

The command helpers make it easy to write bash-like commands:

- **get_input_text()**: Smart file/text/stdin resolution
- **parse_flag()**: Multi-name boolean flags
- **parse_option()**: Multi-name options with type conversion
- **is_error()**: Easy error checking
- **require_args()**: Argument validation

With these helpers, most commands are just 10-20 lines of clear, focused code.
