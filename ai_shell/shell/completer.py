"""Tab completion for ai-shell."""

from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.document import Document
from typing import Iterable
import os


class ShellCompleter(Completer):
    """
    Tab completion for ai-shell.

    Provides completions for:
    - AI tool names
    - Meta commands (/help, /history, etc.)
    - File paths
    - Shell commands (basic)
    """

    def __init__(self, memory=None):
        """
        Initialize completer.

        Args:
            memory: Memory store (for context)
        """
        self.memory = memory

        # Static completions
        self.meta_commands = [
            '/help', '/history', '/clear', '/save', '/load',
            '/model', '/config', '/exit'
        ]

        self.common_shell_commands = [
            'ls', 'cd', 'pwd', 'cat', 'echo', 'grep', 'find',
            'head', 'tail', 'git', 'docker', 'npm', 'pip',
            'python', 'node', 'rm', 'mv', 'cp', 'mkdir'
        ]

        # Will be populated by tool registry
        self.tool_names = []

    def set_tool_names(self, tool_names: list):
        """
        Update available tool names.

        Args:
            tool_names: List of tool names from registry
        """
        self.tool_names = tool_names

    def get_completions(self,
                       document: Document,
                       complete_event) -> Iterable[Completion]:
        """
        Get completions for current input.

        Args:
            document: Current document state
            complete_event: Completion event

        Yields:
            Completion objects
        """
        text = document.text_before_cursor
        word = document.get_word_before_cursor()

        # Meta commands
        if text.startswith('/'):
            yield from self._complete_meta_commands(word)

        # AI tools
        elif text.startswith('\\'):
            yield from self._complete_tools(word)

        # File paths (in any context)
        elif '/' in word or '~' in word:
            yield from self._complete_paths(word)

        # Shell commands (with ! or auto-resolve)
        elif text.startswith('!') or not any(text.startswith(p) for p in ['?', '\\', '/']):
            yield from self._complete_shell_commands(word)

    def _complete_meta_commands(self, word: str) -> Iterable[Completion]:
        """Complete meta commands."""
        for cmd in self.meta_commands:
            if cmd.startswith('/' + word.lstrip('/')):
                yield Completion(
                    cmd,
                    start_position=-len(word),
                    display_meta="meta command"
                )

    def _complete_tools(self, word: str) -> Iterable[Completion]:
        """Complete AI tool names."""
        for tool in self.tool_names:
            if tool.startswith(word.lstrip('\\')):
                yield Completion(
                    tool,
                    start_position=-len(word),
                    display_meta="AI tool"
                )

    def _complete_paths(self, word: str) -> Iterable[Completion]:
        """Complete file paths."""
        # Expand ~ to home directory
        if word.startswith('~'):
            word = os.path.expanduser(word)

        # Get directory and filename parts
        if '/' in word:
            directory = os.path.dirname(word) or '.'
            prefix = os.path.basename(word)
        else:
            directory = '.'
            prefix = word

        # List directory contents
        try:
            if os.path.isdir(directory):
                for item in os.listdir(directory):
                    if item.startswith(prefix):
                        full_path = os.path.join(directory, item)
                        display = item + ('/' if os.path.isdir(full_path) else '')
                        yield Completion(
                            display,
                            start_position=-len(prefix),
                            display_meta="file" if not os.path.isdir(full_path) else "dir"
                        )
        except (OSError, PermissionError):
            pass

    def _complete_shell_commands(self, word: str) -> Iterable[Completion]:
        """Complete shell commands."""
        for cmd in self.common_shell_commands:
            if cmd.startswith(word):
                yield Completion(
                    cmd,
                    start_position=-len(word),
                    display_meta="shell command"
                )
