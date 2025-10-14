"""Meta commands for ai-shell."""

from typing import Dict, Callable, Any
from dataclasses import dataclass


@dataclass
class MetaCommandResult:
    """Result from meta command execution."""
    success: bool
    message: str
    data: Any = None


class MetaCommandHandler:
    """
    Handler for meta commands (/help, /history, etc.).

    Meta commands control the shell itself rather than
    executing AI or bash operations.
    """

    def __init__(self, repl):
        """
        Initialize handler.

        Args:
            repl: REPL instance (for accessing state)
        """
        self.repl = repl

        # Register commands
        self.commands: Dict[str, Callable] = {
            'help': self.cmd_help,
            'history': self.cmd_history,
            'clear': self.cmd_clear,
            'save': self.cmd_save,
            'load': self.cmd_load,
            'sessions': self.cmd_sessions,
            'exit': self.cmd_exit,
        }

    async def execute(self, command) -> MetaCommandResult:
        """
        Execute meta command.

        Args:
            command: Parsed meta command

        Returns:
            MetaCommandResult
        """
        cmd_name = command.meta_command

        if cmd_name not in self.commands:
            return MetaCommandResult(
                success=False,
                message=f"Unknown command: /{cmd_name}\nType /help for available commands"
            )

        handler = self.commands[cmd_name]
        return await handler(command.meta_args)

    async def cmd_help(self, args: list) -> MetaCommandResult:
        """Show help information."""
        help_text = """# ai-shell Commands

## Prefixes
- `!cmd`     Run bash command
- `?text`    Chat with AI
- `\\tool`    Run AI tool
- `/cmd`     Meta command

## Meta Commands
- `/help`      Show this help
- `/history`   Show command history
- `/clear`     Clear session
- `/save`      Save current session
- `/load`      Load saved session
- `/sessions`  List all sessions
- `/exit`      Exit shell (or Ctrl+D)

## Pipeline
- `!cmd | \\tool`   Pipe bash output to AI tool
- `\\tool | !cmd`   Pipe AI output to bash

## Variables
- `$last`      Last command output

## Examples
```bash
# Chat with AI
?How do I list files in Linux?

# Run bash command
!ls -la

# Use AI tool
\\summarize README.md

# Pipeline
!cat myfile.txt | \\summarize

# Auto-resolve (no prefix)
ls          # Detected as bash
summarize   # Detected as tool (if registered)
hello       # Falls back to chat
```
        """

        return MetaCommandResult(
            success=True,
            message=help_text
        )

    async def cmd_history(self, args: list) -> MetaCommandResult:
        """Show command history."""
        limit = 20
        if args:
            try:
                limit = int(args[0])
            except ValueError:
                pass

        commands = self.repl.memory.get_all_commands(limit=limit)

        if not commands:
            return MetaCommandResult(
                success=True,
                message="No command history yet."
            )

        # Format history
        history_lines = ["# Command History\n"]
        for i, cmd in enumerate(reversed(commands), 1):
            timestamp = cmd['timestamp'].split('T')[1][:8]  # HH:MM:SS
            history_lines.append(f"{i:3d}  {timestamp}  {cmd['command']}")

        return MetaCommandResult(
            success=True,
            message="\n".join(history_lines)
        )

    async def cmd_clear(self, args: list) -> MetaCommandResult:
        """Clear session."""
        self.repl.memory.clear()
        return MetaCommandResult(
            success=True,
            message="Session cleared"
        )

    async def cmd_save(self, args: list) -> MetaCommandResult:
        """Save current session."""
        self.repl.memory.save_session()
        return MetaCommandResult(
            success=True,
            message=f"Session saved: {self.repl.memory.current_session_id}"
        )

    async def cmd_load(self, args: list) -> MetaCommandResult:
        """Load saved session."""
        if not args:
            return MetaCommandResult(
                success=False,
                message="Usage: /load <session_id>\nUse /sessions to list available sessions"
            )

        session_id = args[0]
        try:
            self.repl.memory.load_session(session_id)
            return MetaCommandResult(
                success=True,
                message=f"Session loaded: {session_id}"
            )
        except Exception as e:
            return MetaCommandResult(
                success=False,
                message=f"Failed to load session: {e}"
            )

    async def cmd_sessions(self, args: list) -> MetaCommandResult:
        """List all saved sessions."""
        sessions = self.repl.memory.list_sessions()

        if not sessions:
            return MetaCommandResult(
                success=True,
                message="No saved sessions."
            )

        # Format sessions
        lines = ["# Saved Sessions\n"]
        for session in sessions:
            timestamp = session['timestamp']
            session_id = session['session_id']
            lines.append(f"- {timestamp}: {session_id}")

        return MetaCommandResult(
            success=True,
            message="\n".join(lines)
        )

    async def cmd_exit(self, args: list) -> MetaCommandResult:
        """Exit shell."""
        from ai_shell.shell.repl import SessionState
        self.repl.state = SessionState.SHUTTING_DOWN
        return MetaCommandResult(
            success=True,
            message="Goodbye!"
        )
