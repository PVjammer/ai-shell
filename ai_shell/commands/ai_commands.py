"""AI-powered commands using LLMs."""

import argparse
from datetime import datetime
from pathlib import Path
from functools import partial


def get_default_model():
    """Get default Ollama model client."""
    try:
        from ollama import Client
        model = "llama3.1"
        client = Client()
        return partial(client.chat, model=model, stream=False)
    except ImportError:
        return None


def _get_text_input(stdin, content, file_path=None):
    """
    Helper to get text input from stdin, content arg, or file.

    Args:
        stdin: Stdin input (takes priority)
        content: Content argument (can be text or auto-detected file)
        file_path: Explicit file path from -f/--file option

    Returns:
        tuple: (text, error)
    """
    # Priority 1: Explicit file path from -f option
    if file_path:
        try:
            return Path(file_path).read_text(encoding="utf-8"), None
        except Exception as e:
            return None, f"Error reading file {file_path}: {e}"

    # Priority 2: Stdin (from pipe)
    if stdin:
        return stdin, None

    # Priority 3: Content argument
    if not content:
        return None, "Error: No input provided"

    # Try auto-detect as file
    path = Path(content)
    if path.is_file():
        try:
            return path.read_text(encoding="utf-8"), None
        except Exception:
            pass  # Not readable, treat as text

    # Otherwise treat as direct text
    return content, None


async def summarize_cmd(args, stdin=None, **options):
    r"""
    Summarize text using an LLM.

    Usage:
        \summarize "hello world"                    # Direct text
        \summarize file.txt                         # File (auto-detected)
        \summarize -f file.txt                      # Explicit file path
        \summarize --file file.txt                  # Long form
        \summarize file.txt -i "be concise"         # Custom instructions
        \summarize -f file.txt -i "focus on key points"
        !cat file.txt | \summarize                  # From pipe
        !cat file.txt | \summarize -i "brief summary"
    """
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("content", nargs='?', default=None)
    parser.add_argument("--file", "-f", type=str, default=None,
                       help="Explicit file path to read")
    parser.add_argument("--instructions", "-i", type=str, default=None,
                       help="Custom summarization instructions")

    try:
        parsed = parser.parse_args(args or [])
    except (SystemExit, argparse.ArgumentError):
        return "Error: Invalid arguments. Usage: \\summarize [text|file] [-f FILE] [-i INSTRUCTIONS]"

    # Get text input
    text, error = _get_text_input(stdin, parsed.content, parsed.file)
    if error:
        return error

    # Get model
    model = get_default_model()
    if not model:
        return "Error: Ollama not installed or not available. Install with: pip install ollama"

    # Set instructions
    DEFAULT_SUMMARY_INSTRUCTIONS = (
        "Provide a succinct summary that captures the high level themes and key details of the text. "
        "End the summary with a short, one line, tl;dr (too long, didn't read) summary of the text"
    )

    instructions = parsed.instructions or DEFAULT_SUMMARY_INSTRUCTIONS

    # Create messages
    messages = [
        {
            "role": "system",
            "content": f"You are a helpful assistant whose job is to summarize the provided text. {instructions}"
        },
        {
            "role": "user",
            "content": text
        }
    ]

    # Call model
    try:
        result = model(messages=messages)
        return result.message.content
    except Exception as e:
        return f"Error calling model: {e}"


async def context_cmd(args, stdin, context_session={}, **options):
    r"""
    """
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("content", nargs='?', default=None)
    parser.add_argument("--file", "-f", type=str, default=None,
                       help="Explicit file path to read")
    parser.add_argument("--key", "-k", type=str, default=None,
                       help="key to store the context under")
    parser.add_argument("--is_append", "-a", default=True,
                       help="append to the content for the provided key",
                       action="store_true")
    try:
        parsed = parser.parse_args(args or [])
    except (SystemExit, argparse.ArgumentError):
        return "Error: Invalid arguments. Usage: \\context [text|file] [-f FILE] [-key KEY]"
    
    text, error = _get_text_input(stdin, parsed.content, parsed.file)
    if error:
        return error
    if not text:
        print("No content was passed to the tool. Nothing was added to the context.")
    
    
    # key = str(datetime.now().isoformat()) if not parsed.key else parsed.key
    key = "user_context" if not parsed.key else parsed.key
    if key not in context_session:
        context_session[key] = []
    if parsed.is_append:
        context_session[key].append(text)
        return f"Context added to {key} key"
    context_session[key] = [text]
    return f"New context set for {key} key"

async def clear_context_cmd(args, stdin, context_session={}, **options):
    r"""
    """
    parser = argparse.ArgumentParser(add_help=False)    
    parser.add_argument("--key", "-k", type=str, default=None,
                       help="key to store the context under")
    
    try:
        parsed = parser.parse_args(args or [])
    except (SystemExit, argparse.ArgumentError):
        return "Error: Invalid arguments. Usage: \\context [-key KEY]"
    if parsed.key:
        if parsed.key not in context_session:
            print(f"No context stored for {parsed.key}. Context remains unchanged.")
        context_session[parsed.key] = []
        return f"Cleared context for key {parsed.key}"
    for k, v in context_session.items():
        context_session[k] = []
    return f"Cleared all context"

async def view_context_cmd(args, stdin, context_session={}, **options):
    r"""
    """
    parser = argparse.ArgumentParser(add_help=False)    
    parser.add_argument("--key", "-k", type=str, default=None,
                       help="key to store the context under")
    try:
        parsed = parser.parse_args(args or [])
    except (SystemExit, argparse.ArgumentError):
        return "Error: Invalid arguments. Usage: \\context [-key KEY]"
    if parsed.key:
        if parsed.key not in context_session:
            print(f"No context stored for {parsed.key}.")
        
        return f"Context for {parsed.key}:\n\n{context_session[parsed.key]}\n\n" + "=="*20
    
    context_str = "All Context:\n\n"
    for k, v in context_session.items():
        context_str += f"{k}:\n{v}\n\n"
    context_str += "==" * 20
    return context_str

def register_default_ai_commands(executor):
    """
    Register all AI commands included with the default ai-shell installation
    """
    executor.register_command("summarize", summarize_cmd,
                             "Summarize text",
                             category="text")
    
    executor.register_command("add_context",
                              partial(context_cmd, context_session=executor.context_session),
                              "Add context for the agent",
                              category="text"
                              )
    
    executor.register_command("clear_context",
                              partial(clear_context_cmd, context_session=executor.context_session),
                              "Add context for the agent",
                              category="text"
                              )

    executor.register_command("view_context",
                              partial(view_context_cmd, context_session=executor.context_session),
                              "View the agent's current context",
                              category="text"
                              )
    
    print(f"Registered Summarize, Add Context and Clear Context commands")