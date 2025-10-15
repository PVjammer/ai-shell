"""Help commands for viewing tool documentation."""

import argparse


async def help_cmd(args, stdin=None, executor=None, **options):
    r"""
    Display help for registered commands.

    Usage:
        \help                    # List all commands
        \help <command>          # Show detailed help for a command
        \help count              # Example: get help for count command
    """
    if not executor:
        return "Error: Executor not available for help command"

    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("command", nargs='?', default=None,
                       help="Command name to get help for")

    try:
        parsed = parser.parse_args(args or [])
    except (SystemExit, argparse.ArgumentError):
        return "Error: Invalid arguments. Usage: \\help [command]"

    # Get help from executor
    return executor.get_help(parsed.command)


def register_help_commands(executor):
    """Register help commands with the executor."""
    # Create a wrapper that passes the executor to the help command
    async def help_wrapper(args, stdin=None, **options):
        return await help_cmd(args, stdin, executor=executor, **options)

    executor.register_command("help", help_wrapper,
                             "Show help for commands",
                             category="meta")
