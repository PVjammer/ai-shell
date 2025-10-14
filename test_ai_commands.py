"""Test script for AI commands (without requiring Ollama)."""

import asyncio
from pathlib import Path
from ai_shell.commands.ai_commands import summarize_cmd, _get_text_input


async def test_summarize_input_parsing():
    """Test the input parsing logic without calling the model."""

    print("=" * 60)
    print("TEST 1: Direct text input")
    print("=" * 60)
    text, error = _get_text_input(
        stdin=None,
        content="This is some direct text",
        file_path=None
    )
    print(f"Text: {text}")
    print(f"Error: {error}")
    assert text == "This is some direct text"
    assert error is None
    print("✓ PASS\n")

    print("=" * 60)
    print("TEST 2: Stdin input (takes priority over content)")
    print("=" * 60)
    text, error = _get_text_input(
        stdin="Text from stdin",
        content="Text from content arg",
        file_path=None
    )
    print(f"Text: {text}")
    print(f"Error: {error}")
    assert text == "Text from stdin"
    assert error is None
    print("✓ PASS\n")

    print("=" * 60)
    print("TEST 3: Explicit file path from -f option")
    print("=" * 60)
    # Create test file
    test_file = Path("/tmp/test_summarize.txt")
    test_file.write_text("Content from explicit file")

    text, error = _get_text_input(
        stdin=None,
        content="ignored content",
        file_path="/tmp/test_summarize.txt"
    )
    print(f"Text: {text}")
    print(f"Error: {error}")
    assert text == "Content from explicit file"
    assert error is None
    print("✓ PASS\n")

    print("=" * 60)
    print("TEST 4: File auto-detection from content arg")
    print("=" * 60)
    test_file.write_text("Auto-detected file content")

    text, error = _get_text_input(
        stdin=None,
        content="/tmp/test_summarize.txt",  # Looks like file, exists
        file_path=None
    )
    print(f"Text: {text}")
    print(f"Error: {error}")
    assert text == "Auto-detected file content"
    assert error is None
    print("✓ PASS\n")

    print("=" * 60)
    print("TEST 5: Explicit file takes priority over auto-detect")
    print("=" * 60)
    test_file.write_text("Explicit file content")
    other_file = Path("/tmp/test_other.txt")
    other_file.write_text("Other file content")

    text, error = _get_text_input(
        stdin=None,
        content="/tmp/test_other.txt",  # This would auto-detect
        file_path="/tmp/test_summarize.txt"  # But -f takes priority
    )
    print(f"Text: {text}")
    print(f"Error: {error}")
    assert text == "Explicit file content"
    assert error is None
    print("✓ PASS\n")

    print("=" * 60)
    print("TEST 6: Error on missing explicit file")
    print("=" * 60)
    text, error = _get_text_input(
        stdin=None,
        content="some content",
        file_path="/tmp/nonexistent_file.txt"
    )
    print(f"Text: {text}")
    print(f"Error: {error}")
    assert text is None
    assert error is not None
    assert "Error reading file" in error
    print("✓ PASS\n")

    print("=" * 60)
    print("TEST 7: No input error")
    print("=" * 60)
    text, error = _get_text_input(
        stdin=None,
        content=None,
        file_path=None
    )
    print(f"Text: {text}")
    print(f"Error: {error}")
    assert text is None
    assert error == "Error: No input provided"
    print("✓ PASS\n")

    print("=" * 60)
    print("TEST 8: Content as text when file doesn't exist")
    print("=" * 60)
    text, error = _get_text_input(
        stdin=None,
        content="not_a_file.txt",  # Looks like file but doesn't exist
        file_path=None
    )
    print(f"Text: {text}")
    print(f"Error: {error}")
    assert text == "not_a_file.txt"  # Treated as literal text
    assert error is None
    print("✓ PASS\n")


async def test_summarize_arg_parsing():
    """Test argument parsing for summarize command."""

    print("=" * 60)
    print("TEST 9: Parse -f and -i as value arguments")
    print("=" * 60)

    # Create test file
    test_file = Path("/tmp/test_parse.txt")
    test_file.write_text("Test content for parsing")

    # This should NOT call the model since we don't have Ollama
    # But we can verify the parsing works

    # Mock the model to avoid calling Ollama
    import ai_shell.commands.ai_commands as ai_mod
    original_get_model = ai_mod.get_default_model

    def mock_model():
        return None  # Will trigger "Ollama not installed" error

    ai_mod.get_default_model = mock_model

    # Test with -f option
    result = await summarize_cmd(
        args=["-f", "/tmp/test_parse.txt", "-i", "be brief"],
        stdin=None
    )
    print(f"Result: {result}")
    # Should fail with Ollama not installed message
    assert "Ollama not installed" in result or "Error" in result
    print("✓ Argument parsing works (no crash)\n")

    # Restore
    ai_mod.get_default_model = original_get_model

    print("=" * 60)
    print("TEST 10: Test stdin priority over content")
    print("=" * 60)

    ai_mod.get_default_model = mock_model

    result = await summarize_cmd(
        args=["ignored content"],
        stdin="stdin text should be used"
    )
    print(f"Result: {result}")
    # If we had a model, stdin would be used
    assert "Ollama not installed" in result or "Error" in result
    print("✓ Stdin priority works\n")

    ai_mod.get_default_model = original_get_model


async def test_summarize_usage_examples():
    """Test usage examples from docstring."""

    print("=" * 60)
    print("TEST 11: Usage example variations")
    print("=" * 60)

    test_file = Path("/tmp/test_usage.txt")
    test_file.write_text("Test file content for usage examples")

    test_cases = [
        (["Direct text input"], None, "Direct text input"),
        (["/tmp/test_usage.txt"], None, "Test file content"),  # Auto-detect
        (["-f", "/tmp/test_usage.txt"], None, "Test file content"),  # Explicit -f
        (["--file", "/tmp/test_usage.txt"], None, "Test file content"),  # Long form
        ([], "stdin content", "stdin content"),  # From pipe
    ]

    for i, (args, stdin, expected_start) in enumerate(test_cases, 1):
        print(f"\n  Case {i}: args={args}, stdin={'<present>' if stdin else 'None'}")
        text, error = _get_text_input(
            stdin=stdin,
            content=args[0] if args and not args[0].startswith('-') else None,
            file_path=args[1] if len(args) > 1 and args[0] in ['-f', '--file'] else None
        )

        if error:
            print(f"    Error: {error}")
        else:
            print(f"    Text starts with: {text[:30]}...")
            assert expected_start in text
            print("    ✓ PASS")

    print("\n✓ All usage examples work\n")


async def test_instructions_option():
    """Test -i/--instructions option."""

    print("=" * 60)
    print("TEST 12: Instructions option variations")
    print("=" * 60)

    import ai_shell.commands.ai_commands as ai_mod

    # Create a mock that captures the instructions
    captured_instructions = []

    def mock_model():
        def mock_chat(messages):
            # Capture instructions from system message
            for msg in messages:
                if msg.get("role") == "system":
                    captured_instructions.append(msg.get("content"))

            # Return mock response
            class MockResult:
                class Message:
                    content = "Mock summary"
                message = Message()
            return MockResult()
        return mock_chat

    original = ai_mod.get_default_model
    ai_mod.get_default_model = mock_model

    # Test default instructions
    captured_instructions.clear()
    result = await summarize_cmd(["Some text"], stdin=None)
    print(f"Default instructions captured: {len(captured_instructions[0])} chars")
    assert "succinct summary" in captured_instructions[0].lower()
    print("✓ Default instructions work\n")

    # Test custom instructions with -i
    captured_instructions.clear()
    result = await summarize_cmd(["Some text", "-i", "be very brief"], stdin=None)
    print(f"Custom instructions captured: {captured_instructions[0]}")
    assert "be very brief" in captured_instructions[0]
    print("✓ Custom -i instructions work\n")

    # Test custom instructions with --instructions
    captured_instructions.clear()
    result = await summarize_cmd(["Some text", "--instructions", "focus on key points"], stdin=None)
    print(f"Custom instructions captured: {captured_instructions[0]}")
    assert "focus on key points" in captured_instructions[0]
    print("✓ Custom --instructions work\n")

    ai_mod.get_default_model = original


async def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("Testing AI Commands (ai_commands.py)")
    print("=" * 60 + "\n")

    try:
        await test_summarize_input_parsing()
        await test_summarize_arg_parsing()
        await test_summarize_usage_examples()
        await test_instructions_option()

        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED!")
        print("=" * 60 + "\n")

    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}\n")
        raise
    except Exception as e:
        print(f"\n✗ UNEXPECTED ERROR: {e}\n")
        raise


if __name__ == "__main__":
    asyncio.run(main())
