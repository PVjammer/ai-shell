"""
Helper functions for command implementations.

These utilities handle common patterns like text/file/stdin resolution,
flag parsing, and argument validation, making it easier to write
bash-like commands.
"""

from typing import List, Optional, Dict, Any
from pathlib import Path


def get_input_text(args: List[str],
                   stdin: Optional[str] = None,
                   file_flag: bool = False,
                   encoding: str = 'utf-8') -> str:
    """
    Get input text from args, stdin, or file with smart resolution.

    This is the most common pattern for commands that accept text:
    - If stdin is provided (piped input), use it
    - If args provided and looks like a file (or file_flag set), read file
    - Otherwise treat args as direct text

    Args:
        args: Positional arguments from command
        stdin: Stdin input from pipeline
        file_flag: If True, force treating first arg as file path
        encoding: File encoding (default: utf-8)

    Returns:
        The input text, or an error message starting with "Error:"

    Examples:
        # From stdin (pipe)
        text = get_input_text([], stdin="hello world")

        # Direct text
        text = get_input_text(["hello world"])

        # Auto-detect file
        text = get_input_text(["file.txt"])

        # Explicit file
        text = get_input_text(["file.txt"], file_flag=True)
    """
    # Priority 1: stdin from pipeline
    if stdin:
        return stdin

    # Priority 2: args
    if args:
        # If only one arg, might be file or text
        if len(args) == 1:
            path = Path(args[0])

            # Explicit file mode
            if file_flag:
                if not path.exists():
                    return f"Error: File not found: {args[0]}"
                if not path.is_file():
                    return f"Error: Not a file: {args[0]}"
                try:
                    return path.read_text(encoding=encoding)
                except Exception as e:
                    return f"Error reading file: {e}"

            # Auto-detect: if file exists, read it; otherwise treat as text
            if path.is_file():
                try:
                    return path.read_text(encoding=encoding)
                except Exception as e:
                    return f"Error reading file: {e}"
            else:
                # Not a file, treat as text
                return args[0]

        # Multiple args - treat as text joined by spaces
        return " ".join(args)

    # No input provided
    return "Error: No input provided. Use: <text>, <file>, or pipe input"


def get_input_lines(args: List[str],
                    stdin: Optional[str] = None,
                    file_flag: bool = False,
                    encoding: str = 'utf-8') -> List[str] | str:
    """
    Get input as list of lines (convenience wrapper around get_input_text).

    Args:
        args: Positional arguments
        stdin: Stdin input
        file_flag: Force file mode
        encoding: File encoding

    Returns:
        List of lines, or error message string
    """
    text = get_input_text(args, stdin, file_flag, encoding)
    if isinstance(text, str) and text.startswith("Error:"):
        return text
    return text.splitlines()


def parse_flag(options: Dict[str, Any], *names: str, default: bool = False) -> bool:
    """
    Parse a boolean flag with multiple possible names.

    Checks for flag under multiple names (e.g., 'verbose' and 'v').
    Returns True if any name is present and truthy.

    Args:
        options: Options dict from command
        *names: Flag names to check (e.g., 'verbose', 'v')
        default: Default value if no names found

    Returns:
        Boolean flag value

    Examples:
        # Check for --verbose or -v
        verbose = parse_flag(options, 'verbose', 'v')

        # Check for --force or -f with default False
        force = parse_flag(options, 'force', 'f', default=False)
    """
    for name in names:
        if name in options and options[name]:
            return True
    return default


def parse_option(options: Dict[str, Any],
                 *names: str,
                 default: Any = None,
                 type_fn: callable = None) -> Any:
    """
    Parse an option with multiple possible names and optional type conversion.

    Args:
        options: Options dict from command
        *names: Option names to check
        default: Default value if not found
        type_fn: Optional type conversion function

    Returns:
        Option value (converted if type_fn provided)

    Examples:
        # Get --max-length or --max with default 100
        max_len = parse_option(options, 'max-length', 'max', default=100, type_fn=int)

        # Get --format or -f with default 'json'
        fmt = parse_option(options, 'format', 'f', default='json')
    """
    for name in names:
        if name in options:
            value = options[name]
            if type_fn:
                try:
                    return type_fn(value)
                except (ValueError, TypeError):
                    return default
            return value
    return default


def require_args(args: List[str],
                 min_count: int = None,
                 max_count: int = None,
                 usage: str = None) -> Optional[str]:
    """
    Validate argument count and return error message if invalid.

    Args:
        args: Positional arguments
        min_count: Minimum required arguments
        max_count: Maximum allowed arguments
        usage: Usage message to show on error

    Returns:
        None if valid, error message if invalid

    Examples:
        # Require exactly 1 argument
        if error := require_args(args, min_count=1, max_count=1, usage="cmd <file>"):
            return error

        # Require at least 1 argument
        if error := require_args(args, min_count=1, usage="cmd <file> [file2 ...]"):
            return error
    """
    count = len(args) if args else 0

    if min_count is not None and count < min_count:
        msg = f"Error: Too few arguments (got {count}, need at least {min_count})"
        if usage:
            msg += f"\nUsage: {usage}"
        return msg

    if max_count is not None and count > max_count:
        msg = f"Error: Too many arguments (got {count}, maximum {max_count})"
        if usage:
            msg += f"\nUsage: {usage}"
        return msg

    return None


def parse_file_list(args: List[str],
                    stdin: Optional[str] = None,
                    patterns: bool = False) -> List[Path] | str:
    """
    Parse arguments as list of file paths.

    Args:
        args: Arguments (file paths or patterns)
        stdin: Stdin input (newline-separated paths)
        patterns: If True, expand glob patterns (*.txt, etc.)

    Returns:
        List of Path objects, or error message string

    Examples:
        # Get list of files
        files = parse_file_list(["file1.txt", "file2.txt"])

        # From stdin
        files = parse_file_list([], stdin="file1.txt\\nfile2.txt\\n")

        # With glob patterns
        files = parse_file_list(["*.py"], patterns=True)
    """
    paths = []

    # Get path strings from args or stdin
    if stdin:
        path_strs = [line.strip() for line in stdin.splitlines() if line.strip()]
    elif args:
        path_strs = args
    else:
        return "Error: No files specified"

    # Convert to Path objects
    for path_str in path_strs:
        if patterns and ('*' in path_str or '?' in path_str):
            # Expand glob pattern
            expanded = list(Path().glob(path_str))
            if not expanded:
                return f"Error: No files match pattern: {path_str}"
            paths.extend(expanded)
        else:
            path = Path(path_str)
            if not path.exists():
                return f"Error: File not found: {path_str}"
            paths.append(path)

    if not paths:
        return "Error: No files found"

    return paths


def format_error(error: Exception, context: str = None) -> str:
    """
    Format an exception as a user-friendly error message.

    Args:
        error: The exception
        context: Optional context (e.g., "reading file")

    Returns:
        Formatted error message

    Examples:
        try:
            # ... operation ...
        except Exception as e:
            return format_error(e, "reading file")
    """
    if context:
        return f"Error {context}: {error}"
    return f"Error: {error}"


def is_error(result: Any) -> bool:
    """
    Check if a result is an error message.

    Args:
        result: Result to check

    Returns:
        True if result is an error message

    Examples:
        text = get_input_text(args, stdin)
        if is_error(text):
            return text
    """
    return isinstance(result, str) and result.startswith("Error:")


# Convenience re-exports for common Path operations
def read_file(path: str | Path, encoding: str = 'utf-8') -> str:
    """
    Read file contents with error handling.

    Args:
        path: File path
        encoding: Text encoding

    Returns:
        File contents or error message
    """
    try:
        return Path(path).read_text(encoding=encoding)
    except FileNotFoundError:
        return f"Error: File not found: {path}"
    except Exception as e:
        return f"Error reading file: {e}"


def write_file(path: str | Path, content: str, encoding: str = 'utf-8') -> Optional[str]:
    """
    Write file contents with error handling.

    Args:
        path: File path
        content: Content to write
        encoding: Text encoding

    Returns:
        None on success, error message on failure
    """
    try:
        Path(path).write_text(content, encoding=encoding)
        return None
    except Exception as e:
        return f"Error writing file: {e}"
