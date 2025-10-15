"""Tests for BashExecutor improvements."""

import asyncio
import os
import pytest
from ai_shell.core.bash_executor import BashExecutor


@pytest.mark.asyncio
async def test_cd_command_persists():
    """Test that cd command updates persistent working directory."""
    executor = BashExecutor()

    # Get initial directory
    initial_cwd = executor.get_cwd()

    # Change to home directory
    result = await executor.execute("cd ~")
    assert result.success
    assert executor.get_cwd() == os.path.expanduser("~")

    # Verify subsequent commands use the new directory
    result = await executor.execute("pwd")
    assert result.success
    assert result.output.strip() == os.path.expanduser("~")


@pytest.mark.asyncio
async def test_cd_relative_path():
    """Test cd with relative paths."""
    executor = BashExecutor()

    # Change to home directory first
    await executor.execute("cd ~")
    home = executor.get_cwd()

    # Try to go to a subdirectory (if it exists)
    result = await executor.execute("cd ..")
    assert result.success
    assert executor.get_cwd() != home
    assert len(executor.get_cwd()) <= len(home)


@pytest.mark.asyncio
async def test_cd_nonexistent_directory():
    """Test cd with non-existent directory."""
    executor = BashExecutor()

    initial_cwd = executor.get_cwd()

    # Try to change to non-existent directory
    result = await executor.execute("cd /nonexistent_directory_12345")
    assert not result.success
    assert "No such file or directory" in result.error

    # Verify cwd hasn't changed
    assert executor.get_cwd() == initial_cwd


@pytest.mark.asyncio
async def test_cd_to_file():
    """Test cd to a file (should fail)."""
    executor = BashExecutor()

    # Create a temporary file
    test_file = "/tmp/test_file_for_cd"
    with open(test_file, "w") as f:
        f.write("test")

    try:
        initial_cwd = executor.get_cwd()

        # Try to cd to the file
        result = await executor.execute(f"cd {test_file}")
        assert not result.success
        assert "Not a directory" in result.error

        # Verify cwd hasn't changed
        assert executor.get_cwd() == initial_cwd
    finally:
        os.remove(test_file)


@pytest.mark.asyncio
async def test_environment_persists():
    """Test that commands run with persistent environment."""
    executor = BashExecutor()

    # Verify we can access the PATH
    result = await executor.execute("echo $PATH")
    assert result.success
    assert len(result.output.strip()) > 0


@pytest.mark.asyncio
async def test_executables_work():
    """Test that installed executables can be run."""
    executor = BashExecutor()

    # Test common executables
    executables = ["ls", "pwd", "echo", "cat"]

    for exe in executables:
        result = await executor.execute(f"which {exe}")
        assert result.success, f"{exe} should be in PATH"
        assert len(result.output.strip()) > 0


@pytest.mark.asyncio
async def test_cd_with_spaces():
    """Test cd with directory names containing spaces."""
    executor = BashExecutor()

    # Create a directory with spaces
    test_dir = "/tmp/test dir with spaces"
    os.makedirs(test_dir, exist_ok=True)

    try:
        # Change to the directory
        result = await executor.execute(f'cd "{test_dir}"')
        assert result.success
        assert executor.get_cwd() == test_dir
    finally:
        os.rmdir(test_dir)


@pytest.mark.asyncio
async def test_get_cwd():
    """Test get_cwd method."""
    executor = BashExecutor()

    cwd = executor.get_cwd()
    assert isinstance(cwd, str)
    assert len(cwd) > 0
    assert os.path.isabs(cwd)


@pytest.mark.asyncio
async def test_get_env():
    """Test get_env method."""
    executor = BashExecutor()

    env = executor.get_env()
    assert isinstance(env, dict)
    assert "PATH" in env
    assert len(env["PATH"]) > 0
