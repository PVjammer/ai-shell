"""Text processing commands using command helpers."""

from ai_shell.core.command_helpers import (
    get_input_text,
    get_input_lines,
    parse_flag,
    parse_option,
    is_error
)


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
    # Get input with smart file/text resolution
    text = get_input_text(args, stdin, file_flag=parse_flag(options, 'file', 'f'))
    if is_error(text):
        return text

    # Count
    lines = len(text.splitlines())
    words = len(text.split())
    chars = len(text)

    # Check output flags
    show_lines = parse_flag(options, 'lines', 'l')
    show_words = parse_flag(options, 'words', 'w')
    show_chars = parse_flag(options, 'chars', 'c')

    # Return based on flags
    if show_lines:
        return str(lines)
    elif show_words:
        return str(words)
    elif show_chars:
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
    text = get_input_text(args, stdin, file_flag=parse_flag(options, 'file', 'f'))
    if is_error(text):
        return text
    return text.upper()


async def lower_cmd(args, stdin=None, **options):
    r"""
    Convert text to lowercase.

    Usage:
        \lower "HELLO WORLD"
        \lower file.txt
        !echo "HELLO" | \lower
    """
    text = get_input_text(args, stdin, file_flag=parse_flag(options, 'file', 'f'))
    if is_error(text):
        return text
    return text.lower()


async def reverse_cmd(args, stdin=None, **options):
    r"""
    Reverse lines of text.

    Usage:
        \reverse "line1\nline2"
        \reverse file.txt
        !cat file.txt | \reverse
    """
    lines = get_input_lines(args, stdin, file_flag=parse_flag(options, 'file', 'f'))
    if is_error(lines):
        return lines
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
    if not args:
        return r"Usage: \grep <pattern> [text or file]"

    pattern = args[0]
    ignore_case = parse_flag(options, 'ignore-case', 'i')

    # Get text from remaining args or stdin
    search_args = args[1:] if len(args) > 1 else []
    text = get_input_text(search_args, stdin, file_flag=parse_flag(options, 'file', 'f'))
    if is_error(text):
        return text

    # Search for pattern in lines
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


async def head_cmd(args, stdin=None, **options):
    r"""
    Show first N lines of text (default: 10).

    Usage:
        \head "multi\nline\ntext"
        \head file.txt
        \head file.txt --lines=20
        \head file.txt -n 5
        !cat file.txt | \head --lines=5
    """
    # Parse line count
    n = parse_option(options, 'lines', 'n', default=10, type_fn=int)

    # Get input
    lines = get_input_lines(args, stdin, file_flag=parse_flag(options, 'file', 'f'))
    if is_error(lines):
        return lines

    return "\n".join(lines[:n])


async def tail_cmd(args, stdin=None, **options):
    r"""
    Show last N lines of text (default: 10).

    Usage:
        \tail "multi\nline\ntext"
        \tail file.txt
        \tail file.txt --lines=20
        \tail file.txt -n 5
        !cat file.txt | \tail --lines=5
    """
    # Parse line count
    n = parse_option(options, 'lines', 'n', default=10, type_fn=int)

    # Get input
    lines = get_input_lines(args, stdin, file_flag=parse_flag(options, 'file', 'f'))
    if is_error(lines):
        return lines

    return "\n".join(lines[-n:])


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
    # Get input
    lines = get_input_lines(args, stdin, file_flag=parse_flag(options, 'file', 'f'))
    if is_error(lines):
        return lines

    # Sort
    reverse = parse_flag(options, 'reverse', 'r')
    sorted_lines = sorted(lines, reverse=reverse)

    return "\n".join(sorted_lines)


async def uniq_cmd(args, stdin=None, **options):
    r"""
    Remove duplicate lines (adjacent duplicates only, like bash uniq).

    Usage:
        \uniq "apple\napple\nbanana\napple"
        \uniq file.txt
        !cat file.txt | \sort | \uniq
    """
    # Get input
    lines = get_input_lines(args, stdin, file_flag=parse_flag(options, 'file', 'f'))
    if is_error(lines):
        return lines

    # Remove adjacent duplicates
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
