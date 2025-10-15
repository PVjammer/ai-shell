"""
Built-in commands for ai-shell.

These are example commands that can be extended by users.
"""

from ai_shell.commands.text_commands import register_text_commands
from ai_shell.commands.file_commands import register_file_commands
from ai_shell.commands.ai_commands import register_default_ai_commands
from ai_shell.commands.mcp_commands import register_mcp_commands
from ai_shell.commands.help_commands import register_help_commands

def register_builtin_commands(executor, mcp_servers={}):
    """
    Register all built-in commands with the executor.

    Args:
        executor: CommandExecutor instance
    """
    register_help_commands(executor)
    register_text_commands(executor)
    # register_file_commands(executor)
    register_default_ai_commands(executor)
    register_mcp_commands(executor, mcp_servers)
