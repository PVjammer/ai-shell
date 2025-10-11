"""Tests for parser."""

import pytest
from ai_shell.shell.parser import Parser, ParseError, CommandType


@pytest.fixture
def parser():
    return Parser()


def test_parse_bash_command(parser):
    """Test parsing bash command with ! prefix."""
    result = parser.parse("!ls -la")
    assert result.type == CommandType.BASH
    assert result.command == "ls -la"


def test_parse_chat_command(parser):
    """Test parsing chat command with ? prefix."""
    result = parser.parse("?How are you?")
    assert result.type == CommandType.CHAT
    assert result.message == "How are you?"


def test_parse_tool_command(parser):
    """Test parsing tool command with \\ prefix."""
    result = parser.parse("\\summarize file.txt")
    assert result.type == CommandType.TOOL
    assert result.tool_name == "summarize"
    assert result.tool_args == ["file.txt"]


def test_parse_meta_command(parser):
    """Test parsing meta command with / prefix."""
    result = parser.parse("/help")
    assert result.type == CommandType.META
    assert result.meta_command == "help"


def test_parse_pipeline(parser):
    """Test parsing pipeline with | separator."""
    result = parser.parse("!ls -la | \\summarize")
    assert result.type == CommandType.PIPELINE
    assert len(result.stages) == 2
    assert result.stages[0].type == CommandType.BASH
    assert result.stages[1].type == CommandType.TOOL


def test_auto_resolve_shell_command(parser):
    """Test auto-resolve detects common shell commands."""
    result = parser.parse("ls -la")
    assert result.type == CommandType.BASH
    assert result.command == "ls -la"


def test_auto_resolve_fallback_to_chat(parser):
    """Test auto-resolve falls back to chat for unknown input."""
    result = parser.parse("Hello there")
    assert result.type == CommandType.CHAT
    assert result.message == "Hello there"


def test_empty_input_raises_error(parser):
    """Test empty input raises ParseError."""
    with pytest.raises(ParseError):
        parser.parse("")

    with pytest.raises(ParseError):
        parser.parse("   ")


def test_parse_tool_with_multiple_args(parser):
    """Test parsing tool with multiple arguments."""
    result = parser.parse("\\summarize file.txt --max-length=50")
    assert result.type == CommandType.TOOL
    assert result.tool_name == "summarize"
    assert len(result.tool_args) == 2
    assert result.tool_args[0] == "file.txt"
    assert result.tool_args[1] == "--max-length=50"
