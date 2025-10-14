"""Text processing commands using argparse."""

import argparse
from pathlib import Path


def _get_text_input(stdin, content, is_file=False):
    """
    Helper to get text input from stdin or content arg.
    Handles file reading and auto-detection.
    """
    text = stdin or content
    if not text:
        return None, "Error: No input provided"

    if is_file:
        try:
            text = Path(text).read_text(encoding="utf-8")
        except Exception as e:
            return None, f"Error reading file: {e}"
    else:
        # Auto-detect: if it looks like a file and exists, read it
        path = Path(text)
        if path.is_file():
            try:
                text = path.read_text(encoding="utf-8")
            except Exception:
                pass  # Not readable, treat as text

    return text, None


async def count_cmd(args, stdin=None, **options):
    r"""
    Count lines, words, or characters in text.

    Usage:
        \count "hello world"              # Direct text
        \count file.txt                   # File (auto-detected)
        \count --file file.txt            # Explicit file
        \count file.txt --lines           # Only line count
        \count file.txt -l                # Short form
        !cat file.txt | \count            # From pipe
    """
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("content", nargs='?', default=None)
    parser.add_argument("--file", "-f", action="store_true")
    parser.add_argument("--lines", "-l", action="store_true")
    parser.add_argument("--words", "-w", action="store_true")
    parser.add_argument("--chars", "-c", action="store_true")

    try:
        parsed = parser.parse_args(args or [])
    except (SystemExit, argparse.ArgumentError):
        return "Error: Invalid arguments. Usage: \\count [text|file] [--file] [--lines|--words|--chars]"

    # Get input using helper
    text, error = _get_text_input(stdin, parsed.content, parsed.file)
    if error:
        return error

    # Count
    lines = len(text.splitlines())
    words = len(text.split())
    chars = len(text)

    # Return based on flags
    if parsed.lines:
        return str(lines)
    elif parsed.words:
        return str(words)
    elif parsed.chars:
        return str(chars)
    else:
        # Default: show all counts
        return f"Lines: {lines}, Words: {words}, Characters: {chars}"


async def upper_cmd(args, stdin=None, **options):
    r"""
    Convert text to uppercase.

    Usage:
        \upper "hello world"
        \upper file.txt
        !echo "hello" | \upper
    """
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("content", nargs='?', default=None)
    parser.add_argument("--file", "-f", action="store_true")

    try:
        parsed = parser.parse_args(args or [])
    except (SystemExit, argparse.ArgumentError):
        return "Error: Invalid arguments. Usage: \\upper [text|file] [--file]"

    text, error = _get_text_input(stdin, parsed.content, parsed.file)
    if error:
        return error

    return text.upper()


async def lower_cmd(args, stdin=None, **options):
    r"""
    Convert text to lowercase.

    Usage:
        \lower "HELLO WORLD"
        \lower file.txt
        !echo "HELLO" | \lower
    """
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("content", nargs='?', default=None)
    parser.add_argument("--file", "-f", action="store_true")

    try:
        parsed = parser.parse_args(args or [])
    except (SystemExit, argparse.ArgumentError):
        return "Error: Invalid arguments. Usage: \\lower [text|file] [--file]"

    text, error = _get_text_input(stdin, parsed.content, parsed.file)
    if error:
        return error

    return text.lower()


async def reverse_cmd(args, stdin=None, **options):
    r"""
    Reverse lines of text.

    Usage:
        \reverse "line1\nline2"
        \reverse file.txt
        !cat file.txt | \reverse
    """
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("content", nargs='?', default=None)
    parser.add_argument("--file", "-f", action="store_true")

    try:
        parsed = parser.parse_args(args or [])
    except (SystemExit, argparse.ArgumentError):
        return "Error: Invalid arguments. Usage: \\reverse [text|file] [--file]"

    text, error = _get_text_input(stdin, parsed.content, parsed.file)
    if error:
        return error

    lines = text.splitlines()
    return "\n".join(reversed(lines))


async def grep_cmd(args, stdin=None, **options):
    r"""
    Simple grep-like text search.

    Usage:
        \grep "pattern" "some text to search"
        \grep "pattern" file.txt
        !cat file.txt | \grep "pattern"
        \grep "pattern" file.txt --ignore-case
        \grep "pattern" file.txt -i
    """
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("pattern")
    parser.add_argument("content", nargs='?', default=None)
    parser.add_argument("--file", "-f", action="store_true")
    parser.add_argument("--ignore-case", "-i", action="store_true")

    try:
        parsed = parser.parse_args(args or [])
    except (SystemExit, argparse.ArgumentError):
        return "Error: Invalid arguments. Usage: \\grep <pattern> [text|file] [--file] [-i]"

    text, error = _get_text_input(stdin, parsed.content, parsed.file)
    if error:
        return error

    # Search for pattern in lines
    lines = text.splitlines()
    matches = []

    for line in lines:
        if parsed.ignore_case:
            if parsed.pattern.lower() in line.lower():
                matches.append(line)
        else:
            if parsed.pattern in line:
                matches.append(line)

    return "\n".join(matches) if matches else "(no matches)"


async def head_cmd(args, stdin=None, **options):
    r"""
    Show first N lines of text (default: 10).

    Usage:
        \head "multi\nline\ntext"
        \head file.txt
        \head file.txt --lines 20
        \head file.txt -n 5
        !cat file.txt | \head --lines 5
    """
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("content", nargs='?', default=None)
    parser.add_argument("--file", "-f", action="store_true")
    parser.add_argument("--lines", "-n", type=int, default=10)

    try:
        parsed = parser.parse_args(args or [])
    except (SystemExit, argparse.ArgumentError):
        return "Error: Invalid arguments. Usage: \\head [text|file] [--lines N]"

    text, error = _get_text_input(stdin, parsed.content, parsed.file)
    if error:
        return error

    lines = text.splitlines()
    return "\n".join(lines[:parsed.lines])


async def tail_cmd(args, stdin=None, **options):
    r"""
    Show last N lines of text (default: 10).

    Usage:
        \tail "multi\nline\ntext"
        \tail file.txt
        \tail file.txt --lines 20
        \tail file.txt -n 5
        !cat file.txt | \tail --lines 5
    """
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("content", nargs='?', default=None)
    parser.add_argument("--file", "-f", action="store_true")
    parser.add_argument("--lines", "-n", type=int, default=10)

    try:
        parsed = parser.parse_args(args or [])
    except (SystemExit, argparse.ArgumentError):
        return "Error: Invalid arguments. Usage: \\tail [text|file] [--lines N]"

    text, error = _get_text_input(stdin, parsed.content, parsed.file)
    if error:
        return error

    lines = text.splitlines()
    return "\n".join(lines[-parsed.lines:])


async def sort_cmd(args, stdin=None, **options):
    r"""
    Sort lines of text.

    Usage:
        \sort "zebra\napple\nbanana"
        \sort file.txt
        \sort file.txt --reverse
        \sort file.txt -r
        !cat file.txt | \sort
    """
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("content", nargs='?', default=None)
    parser.add_argument("--file", "-f", action="store_true")
    parser.add_argument("--reverse", "-r", action="store_true")

    try:
        parsed = parser.parse_args(args or [])
    except (SystemExit, argparse.ArgumentError):
        return "Error: Invalid arguments. Usage: \\sort [text|file] [--reverse]"

    text, error = _get_text_input(stdin, parsed.content, parsed.file)
    if error:
        return error

    lines = text.splitlines()
    sorted_lines = sorted(lines, reverse=parsed.reverse)
    return "\n".join(sorted_lines)


async def uniq_cmd(args, stdin=None, **options):
    r"""
    Remove duplicate lines (adjacent duplicates only, like bash uniq).

    Usage:
        \uniq "apple\napple\nbanana\napple"
        \uniq file.txt
        !cat file.txt | \sort | \uniq
    """
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("content", nargs='?', default=None)
    parser.add_argument("--file", "-f", action="store_true")

    try:
        parsed = parser.parse_args(args or [])
    except (SystemExit, argparse.ArgumentError):
        return "Error: Invalid arguments. Usage: \\uniq [text|file]"

    text, error = _get_text_input(stdin, parsed.content, parsed.file)
    if error:
        return error

    lines = text.splitlines()
    if not lines:
        return ""

    unique_lines = [lines[0]]
    for line in lines[1:]:
        if line != unique_lines[-1]:
            unique_lines.append(line)

    return "\n".join(unique_lines)


async def wc_cmd(args, stdin=None, **options):
    r"""
    Word count (alias for count with different defaults).

    Usage:
        \wc "hello world"
        \wc file.txt
        !cat file.txt | \wc
    """
    # Just delegate to count_cmd
    return await count_cmd(args, stdin, **options)


def register_text_commands(executor):
    """Register all text processing commands."""
    executor.register_command("count", count_cmd,
                             "Count lines, words, or characters",
                             category="text")

    executor.register_command("wc", wc_cmd,
                             "Word count (alias for count)",
                             category="text")

    executor.register_command("upper", upper_cmd,
                             "Convert text to uppercase",
                             category="text")

    executor.register_command("lower", lower_cmd,
                             "Convert text to lowercase",
                             category="text")

    executor.register_command("reverse", reverse_cmd,
                             "Reverse lines of text",
                             category="text")

    executor.register_command("grep", grep_cmd,
                             "Search for pattern in text",
                             category="text")

    executor.register_command("head", head_cmd,
                             "Show first N lines",
                             category="text")

    executor.register_command("tail", tail_cmd,
                             "Show last N lines",
                             category="text")

    executor.register_command("sort", sort_cmd,
                             "Sort lines of text",
                             category="text")

    executor.register_command("uniq", uniq_cmd,
                             "Remove duplicate lines",
                             category="text")
