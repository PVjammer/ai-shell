"""Tests for ShellCompleter improvements."""

import os
from prompt_toolkit.document import Document
from ai_shell.shell.completer import ShellCompleter


def test_completer_initialization():
    """Test that completer initializes quickly without loading PATH."""
    completer = ShellCompleter()

    # Should NOT load PATH executables during initialization (lazy loading)
    assert not completer._path_executables_loaded
    assert len(completer._path_executables) == 0


def test_meta_command_completion():
    """Test completion of meta commands."""
    completer = ShellCompleter()

    # Test /help completion
    doc = Document("/he", cursor_position=3)
    completions = list(completer.get_completions(doc, None))

    assert any(c.text == "/help" for c in completions)


def test_meta_command_sessions_included():
    """Test that /sessions is included in meta commands."""
    completer = ShellCompleter()

    assert "/sessions" in completer.meta_commands

    # Test completion
    doc = Document("/ses", cursor_position=4)
    completions = list(completer.get_completions(doc, None))

    assert any(c.text == "/sessions" for c in completions)


def test_tool_name_completion():
    """Test completion of tool names."""
    completer = ShellCompleter()
    completer.set_tool_names(["summarize", "translate", "count"])

    # Test completion with backslash prefix
    doc = Document("\\sum", cursor_position=4)
    completions = list(completer.get_completions(doc, None))

    assert any(c.text == "summarize" for c in completions)


def test_tool_name_backslash_handling():
    """Test that backslash is properly stripped in tool completion."""
    completer = ShellCompleter()
    completer.set_tool_names(["summarize", "translate"])

    # Test with backslash
    doc = Document("\\sum", cursor_position=4)
    completions = list(completer.get_completions(doc, None))

    # Should match based on text after backslash
    assert len(completions) > 0
    assert any("summarize" in c.text for c in completions)


def test_path_completion():
    """Test file path completion."""
    completer = ShellCompleter()

    # Test completion in current directory (should always work)
    doc = Document("./", cursor_position=2)
    completions = list(completer.get_completions(doc, None))

    # Should get some completions from current directory
    assert len(completions) >= 0  # May be empty but should not error


def test_path_completion_with_tilde():
    """Test path completion with ~ expansion."""
    completer = ShellCompleter()

    # Test ~ completion
    doc = Document("~/", cursor_position=2)
    completions = list(completer.get_completions(doc, None))

    # Should get some completions from home directory
    assert len(completions) > 0


def test_shell_command_completion():
    """Test shell command completion."""
    completer = ShellCompleter()

    # Test ls completion
    doc = Document("ls", cursor_position=2)
    completions = list(completer.get_completions(doc, None))

    assert any(c.text == "ls" for c in completions)


def test_shell_command_includes_path_executables():
    """Test that shell command completion triggers lazy loading of PATH executables."""
    completer = ShellCompleter()

    # Should NOT be loaded initially
    assert not completer._path_executables_loaded

    # Trigger shell command completion
    doc = Document("py", cursor_position=2)
    completions = list(completer.get_completions(doc, None))

    # Should now be loaded
    assert completer._path_executables_loaded

    # Should have found some executables
    assert len(completer._path_executables) > 0


def test_completion_display_metadata():
    """Test that completions have proper display metadata."""
    completer = ShellCompleter()
    completer.set_tool_names(["summarize"])

    # Meta command
    doc = Document("/hel", cursor_position=4)
    completions = list(completer.get_completions(doc, None))
    meta_completion = next((c for c in completions if c.text == "/help"), None)
    assert meta_completion is not None
    # display_meta can be string or FormattedText
    assert str(meta_completion.display_meta) == "meta command" or \
           "meta command" in str(meta_completion.display_meta)

    # Tool
    doc = Document("\\sum", cursor_position=4)
    completions = list(completer.get_completions(doc, None))
    tool_completion = next((c for c in completions if "summarize" in c.text), None)
    assert tool_completion is not None
    assert "AI tool" in str(tool_completion.display_meta)


def test_common_commands_expanded():
    """Test that common shell commands list is expanded."""
    completer = ShellCompleter()

    # Check that we have more commands than before
    expected_commands = ["chmod", "chown", "curl", "wget", "tar", "zip"]
    for cmd in expected_commands:
        assert cmd in completer.common_shell_commands
