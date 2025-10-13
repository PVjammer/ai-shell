"""
Base utilities for argparse-based commands.

This module provides helpers for using argparse in command handlers,
with special handling for stdin from pipes.
"""

import argparse
import sys
from typing import List, Optional
from pathlib import Path


class CommandArgumentParser(argparse.ArgumentParser):
    """
    ArgumentParser subclass that returns errors instead of exiting.

    Normal ArgumentParser calls sys.exit() on error, which is not
    appropriate for shell commands. This version raises an exception
    instead, which can be caught and returned as an error message.
    """

    def __init__(self, *args, add_help=False, **kwargs):
        """
        Initialize parser.

        Args:
            add_help: Disabled by default (use False) since we have /help
        """
        super().__init__(*args, add_help=add_help, **kwargs)
        self._error_message = None

    def error(self, message):
        """
        Override error to raise exception instead of sys.exit().

        Args:
            message: Error message from argparse
        """
        raise argparse.ArgumentError(None, message)

    def parse_command_args(self, args: List[str], stdin: Optional[str] = None):
        """
        Parse command arguments with stdin handling.

        If stdin is provided (from pipe), it's prepended to args as the
        first positional argument. This mimics bash behavior where piped
        input becomes available to the command.

        Args:
            args: Command arguments
            stdin: Stdin from pipe (if any)

        Returns:
            Parsed namespace

        Raises:
            argparse.ArgumentError: If parsing fails

        Example:
            parser = CommandArgumentParser()
            parser.add_argument('input')
            parser.add_argument('--flag', action='store_true')

            # From pipe: !cat file.txt | \cmd --flag
            parsed = parser.parse_command_args(["--flag"], stdin="content")
            # parsed.input = "content", parsed.flag = True

            # Direct: \cmd file.txt --flag
            parsed = parser.parse_command_args(["file.txt", "--flag"])
            # parsed.input = "file.txt", parsed.flag = True
        """
        # If stdin provided, prepend it as first positional arg
        if stdin:
            # Treat stdin as the first positional argument
            combined_args = ['-'] + list(args)
        else:
            combined_args = list(args) if args else []

        try:
            parsed = self.parse_args(combined_args)

            # Special handling: if first positional arg is '-', replace with stdin
            if stdin:
                # Find the first positional argument in parsed namespace
                for key, value in vars(parsed).items():
                    if value == '-':
                        setattr(parsed, key, stdin)
                        break

            return parsed
        except SystemExit as e:
            # Catch sys.exit() from argparse and convert to error
            raise argparse.ArgumentError(None, "Argument parsing failed")


def read_input(input_value: str, is_file_flag: bool = False) -> str:
    """
    Read input from either a file path or direct text.

    This helper resolves the file-vs-text ambiguity:
    - If is_file_flag is True, treat as file path (error if not found)
    - If input looks like a file and exists, read it
    - Otherwise treat as direct text

    Args:
        input_value: Input string (file path or text)
        is_file_flag: If True, force file mode

    Returns:
        Text content

    Raises:
        FileNotFoundError: If file not found (in file mode)

    Example:
        # Auto-detect
        text = read_input("file.txt")  # Reads file if exists
        text = read_input("hello world")  # Returns as-is

        # Explicit file mode
        text = read_input("file.txt", is_file_flag=True)  # Errors if not found
    """
    if input_value == '-':
        # Convention: '-' means stdin was provided
        return input_value

    path = Path(input_value)

    # Explicit file mode
    if is_file_flag:
        if not path.exists():
            raise FileNotFoundError(f"File not found: {input_value}")
        return path.read_text()

    # Auto-detect: if looks like a file and exists, read it
    if path.is_file():
        try:
            return path.read_text()
        except Exception as e:
            # If reading fails, treat as text
            return input_value

    # Otherwise treat as direct text
    return input_value


def handle_command_errors(func):
    """
    Decorator to handle common command errors gracefully.

    Catches argparse errors, file errors, etc. and returns
    user-friendly error messages.

    Example:
        @handle_command_errors
        async def my_cmd(args, stdin=None, **options):
            parser = CommandArgumentParser()
            parser.add_argument('input')
            parsed = parser.parse_command_args(args, stdin)
            # ... command logic
    """
    async def wrapper(args, stdin=None, **options):
        try:
            return await func(args, stdin, **options)
        except argparse.ArgumentError as e:
            return f"Error: {e}"
        except FileNotFoundError as e:
            return f"Error: {e}"
        except Exception as e:
            return f"Error: {e}"

    return wrapper
