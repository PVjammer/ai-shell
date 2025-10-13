from ollama import Client 
from ollama._types import ChatResponse
from ai_shell.core.command_helpers import (
    get_input_text,
    get_input_lines,
    parse_flag,
    parse_option,
    is_error
)
import argparse
from pathlib import Path

def get_default_model():
   from functools import partial
#    model = "gpt-oss:20b"
   model = "llama3.1"
   client = Client()
   return partial(client.chat, model=model, stream=False)




async def summarize_cmd(args, stdin=None, **options):
    r"""
    Count lines, words, or characters in text.


    Usage:
        \summarize "hello world"                    # Direct text
        \summarize file.txt                         # File (auto-detected)
        \summarize --file file.txt                  # Explicit file
        \summarize file.txt --instructions "..."    # Custom summary instructions
        \summarize file.txt -l "..."                # Short form
        !cat file.txt | \summarize                  # From pipe
    """
    print(f"{args=}\n{options=}")
    parser = argparse.ArgumentParser()
    parser.add_argument("content")
    parser.add_argument("--file", "-f", default=None)
    parser.add_argument("--instructions", "-i", default=None)
    args = parser.parse_args(args)
    print(f"{args.content=}\n{args.file=}\n{args.instructions=}\n\n")

    # Parse Arguments
    text = stdin or args.content
    if args.file:
        text = Path(text).read_text(encoding="utf-8")


    # Get input with smart file/text resolution
    # text = get_input_text(args, stdin, file_flag=parse_flag(options, 'file', 'f'))
    if is_error(text):
        return text

    DEFAULT_SUMMARY_INSTRUCTIONS = "Provide a succint summary that captures the high level themes and key details of the text. " \
    "End the summary with a short, one line, tl;dr (too long, didn't read) summary of the text"

    # Check output flags
    instructions = args.instructions if args.instructions else DEFAULT_SUMMARY_INSTRUCTIONS
    summary_instructions = instructions or DEFAULT_SUMMARY_INSTRUCTIONS
    messages = [{
        "role": "assistant",
        "content": f"You are a helpful assistant whose job is to summarize the provided text. {summary_instructions}"
    }]

    model = get_default_model()
    messages.append({"role": "user", "content": text})
    result = model(messages=messages)

    return result.message.content


def register_default_ai_commands(executor):
    """
    Register all AI commands included with the default ai-shell installation
    """
    executor.register_command("summarize", summarize_cmd,
                             "Summarize text",
                             category="text")