"""Tab completion for ai-shell."""

from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.document import Document
from typing import Iterable, List, Set
import os


class ShellCompleter(Completer):
    """
    Tab completion for ai-shell.

    Provides completions for:
    - AI tool names
    - Meta commands (/help, /history, etc.)
    - File paths
    - Shell commands (from PATH and common commands)
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
            '/sessions', '/exit'
        ]

        self.common_shell_commands = [
            'ls', 'cd', 'pwd', 'cat', 'echo', 'grep', 'find',
            'head', 'tail', 'git', 'docker', 'npm', 'pip',
            'python', 'node', 'rm', 'mv', 'cp', 'mkdir',
            'chmod', 'chown', 'curl', 'wget', 'tar', 'zip',
            'unzip', 'ps', 'kill', 'top', 'df', 'du', 'free'
        ]

        # Will be populated by tool registry
        self.tool_names = []

        # Cache of executables from PATH (lazy loaded)
        self._path_executables: Set[str] = set()
        self._path_executables_loaded = False

    def set_tool_names(self, tool_names: list):
        """
        Update available tool names.

        Args:
            tool_names: List of tool names from registry
        """
        self.tool_names = tool_names

    def _load_path_executables(self):
        """
        Load executable names from PATH environment variable.

        This is called lazily on first shell command completion to avoid
        slowing down shell startup.
        """
        if self._path_executables_loaded:
            return

        try:
            path_dirs = os.environ.get('PATH', '').split(os.pathsep)
            # Limit to first 5 directories for performance
            # This covers most common executables while keeping startup fast
            for directory in path_dirs[:5]:
                if not directory or not os.path.isdir(directory):
                    continue
                try:
                    # Use os.scandir for better performance
                    with os.scandir(directory) as entries:
                        for entry in entries:
                            if entry.is_file(follow_symlinks=False) and os.access(entry.path, os.X_OK):
                                self._path_executables.add(entry.name)
                except (PermissionError, OSError):
                    continue
        except Exception:
            pass  # Silently fail if PATH parsing has issues
        finally:
            self._path_executables_loaded = True

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
        # Strip the leading backslash for matching
        search_term = word.lstrip('\\')
        for tool in self.tool_names:
            if tool.startswith(search_term):
                yield Completion(
                    tool,
                    start_position=-len(search_term),
                    display_meta="AI tool"
                )

    def _complete_paths(self, word: str) -> Iterable[Completion]:
        """Complete file paths."""
        # Save original for proper start_position calculation
        original_word = word

        # Expand ~ to home directory for listing
        expanded_word = os.path.expanduser(word) if word.startswith('~') else word

        # Get directory and filename parts
        if '/' in expanded_word:
            directory = os.path.dirname(expanded_word)
            if not directory:
                directory = '/'
            prefix = os.path.basename(expanded_word)
        else:
            directory = '.'
            prefix = expanded_word

        # List directory contents
        try:
            if os.path.isdir(directory):
                for item in os.listdir(directory):
                    if item.startswith(prefix) or not prefix:
                        full_path = os.path.join(directory, item)
                        is_dir = os.path.isdir(full_path)

                        # Build completion text
                        if directory == '.':
                            completion_text = item
                        elif word.startswith('~'):
                            # Preserve ~ in completion
                            home = os.path.expanduser('~')
                            if directory.startswith(home):
                                rel_dir = '~' + directory[len(home):]
                                completion_text = os.path.join(rel_dir, item)
                            else:
                                completion_text = os.path.join(directory, item)
                        else:
                            completion_text = os.path.join(directory, item)

                        # Add trailing slash for directories
                        if is_dir:
                            completion_text += '/'

                        yield Completion(
                            completion_text,
                            start_position=-len(original_word),
                            display_meta="dir" if is_dir else "file"
                        )
        except (OSError, PermissionError):
            pass

    def _complete_shell_commands(self, word: str) -> Iterable[Completion]:
        """Complete shell commands from common commands and PATH."""
        # Common commands first
        yielded = set()
        for cmd in self.common_shell_commands:
            if cmd.startswith(word):
                yielded.add(cmd)
                yield Completion(
                    cmd,
                    start_position=-len(word),
                    display_meta="shell"
                )

        # Lazy load PATH executables on first use
        if not self._path_executables_loaded:
            self._load_path_executables()

        # Then PATH executables (if not already yielded)
        for cmd in sorted(self._path_executables):
            if cmd.startswith(word) and cmd not in yielded:
                yield Completion(
                    cmd,
                    start_position=-len(word),
                    display_meta="executable"
                )
