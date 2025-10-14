#!/usr/bin/env python3
"""Quick test of real bash executor."""

import asyncio
from ai_shell.core.bash_executor import BashExecutor


async def main():
    """Test real bash commands."""
    bash = BashExecutor()

    print("Testing real bash executor...\n")

    # Test 1: ls
    print("Test 1: ls")
    result = await bash.execute("ls")
    print(f"Success: {result.success}")
    print(f"Output:\n{result.output}")
    print()

    # Test 2: pwd
    print("Test 2: pwd")
    result = await bash.execute("pwd")
    print(f"Success: {result.success}")
    print(f"Output: {result.output.strip()}")
    print()

    # Test 3: echo
    print("Test 3: echo 'Hello World'")
    result = await bash.execute("echo 'Hello World'")
    print(f"Success: {result.success}")
    print(f"Output: {result.output.strip()}")
    print()

    # Test 4: Error handling
    print("Test 4: Non-existent command")
    result = await bash.execute("nonexistentcommand")
    print(f"Success: {result.success}")
    print(f"Error: {result.error.strip()}")
    print()

    print("All tests complete!")


if __name__ == "__main__":
    asyncio.run(main())
