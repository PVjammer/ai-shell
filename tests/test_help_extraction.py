"""Tests for help extraction functionality."""

import asyncio
import pytest
from ai_shell.core.command_executor import CommandExecutor


async def sample_command(args, stdin=None, **options):
    """
    A sample command for testing.

    This is a detailed docstring that should be extracted.
    It has multiple lines.
    """
    return "Hello, world!"


async def another_command(args, stdin=None, **options):
    """Another command without much detail."""
    return "Goodbye!"


@pytest.mark.asyncio
async def test_get_help_for_all_commands():
    """Test getting help for all commands."""
    executor = CommandExecutor()

    # Register some commands
    executor.register_command("sample", sample_command, "A sample command", "test")
    executor.register_command("another", another_command, "Another command", "test")

    # Get help for all commands
    help_text = executor.get_help()

    assert "sample" in help_text
    assert "another" in help_text
    assert "A sample command" in help_text
    assert "Another command" in help_text
    assert "test" in help_text.lower()


@pytest.mark.asyncio
async def test_get_help_for_specific_command():
    """Test getting help for a specific command."""
    executor = CommandExecutor()

    executor.register_command("sample", sample_command, "A sample command", "test")

    # Get help for specific command
    help_text = executor.get_help("sample")

    assert "sample" in help_text
    assert "A sample command" in help_text
    assert "detailed docstring" in help_text
    assert "Signature:" in help_text


@pytest.mark.asyncio
async def test_get_help_for_unknown_command():
    """Test getting help for unknown command."""
    executor = CommandExecutor()

    help_text = executor.get_help("nonexistent")

    assert "Unknown command" in help_text


@pytest.mark.asyncio
async def test_get_help_with_no_commands():
    """Test getting help when no commands are registered."""
    executor = CommandExecutor()

    help_text = executor.get_help()

    assert "No commands registered" in help_text


@pytest.mark.asyncio
async def test_get_all_commands_info():
    """Test get_all_commands_info method."""
    executor = CommandExecutor()

    executor.register_command("sample", sample_command, "A sample command", "test")
    executor.register_command("another", another_command, "Another command", "util")

    info = executor.get_all_commands_info()

    assert len(info) == 2
    assert "sample" in info
    assert "another" in info
    assert info["sample"].description == "A sample command"
    assert info["another"].category == "util"


@pytest.mark.asyncio
async def test_help_groups_by_category():
    """Test that help groups commands by category."""
    executor = CommandExecutor()

    executor.register_command("cmd1", sample_command, "Command 1", "category_a")
    executor.register_command("cmd2", another_command, "Command 2", "category_b")
    executor.register_command("cmd3", sample_command, "Command 3", "category_a")

    help_text = executor.get_help()

    # Check categories are present
    assert "category_a" in help_text.lower()
    assert "category_b" in help_text.lower()

    # Check commands are listed
    assert "cmd1" in help_text
    assert "cmd2" in help_text
    assert "cmd3" in help_text
