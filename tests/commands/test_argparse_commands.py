"""Test script for argparse-based commands."""

import asyncio
from ai_shell.commands.text_commands import count_cmd, upper_cmd, grep_cmd, head_cmd


async def test_commands():
    """Test various command scenarios."""

    print("=" * 60)
    print("TEST 1: count with direct text")
    print("=" * 60)
    result = await count_cmd(["Hello I am a little bird"], stdin=None)
    print(f"Result: {result}")
    print()

    print("=" * 60)
    print("TEST 2: count with stdin (simulating pipe)")
    print("=" * 60)
    result = await count_cmd([], stdin="Hello I am a little bird")
    print(f"Result: {result}")
    print()

    print("=" * 60)
    print("TEST 3: count with --lines flag")
    print("=" * 60)
    result = await count_cmd(["Hello\nWorld\nTest", "--lines"], stdin=None)
    print(f"Result: {result}")
    print()

    print("=" * 60)
    print("TEST 4: upper with direct text")
    print("=" * 60)
    result = await upper_cmd(["hello world"], stdin=None)
    print(f"Result: {result}")
    print()

    print("=" * 60)
    print("TEST 5: upper with stdin")
    print("=" * 60)
    result = await upper_cmd([], stdin="hello from stdin")
    print(f"Result: {result}")
    print()

    print("=" * 60)
    print("TEST 6: grep with pattern and text")
    print("=" * 60)
    result = await grep_cmd(["hello", "hello world\ngoodbye world"], stdin=None)
    print(f"Result: {result}")
    print()

    print("=" * 60)
    print("TEST 7: grep with pattern and stdin")
    print("=" * 60)
    result = await grep_cmd(["world"], stdin="hello world\ngoodbye world\nhello there")
    print(f"Result: {result}")
    print()

    print("=" * 60)
    print("TEST 8: head with default lines")
    print("=" * 60)
    text = "\n".join([f"Line {i}" for i in range(1, 21)])
    result = await head_cmd([text], stdin=None)
    print(f"Result:\n{result}")
    print()

    print("=" * 60)
    print("TEST 9: head with custom --lines 5")
    print("=" * 60)
    result = await head_cmd([text, "--lines", "5"], stdin=None)
    print(f"Result:\n{result}")
    print()

    print("=" * 60)
    print("TEST 10: Test file auto-detection (create test file)")
    print("=" * 60)
    # Create a test file
    with open("/tmp/test_count.txt", "w") as f:
        f.write("Line 1\nLine 2\nLine 3\n")

    result = await count_cmd(["/tmp/test_count.txt"], stdin=None)
    print(f"Result: {result}")
    print()

    print("=" * 60)
    print("TEST 11: Test --file flag explicitly")
    print("=" * 60)
    result = await count_cmd(["/tmp/test_count.txt", "--file"], stdin=None)
    print(f"Result: {result}")
    print()

    print("=" * 60)
    print("All tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_commands())
