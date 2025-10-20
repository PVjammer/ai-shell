"""AI-powered commands using LLMs."""

import argparse
from datetime import datetime
from pathlib import Path
from functools import partial
from pydantic import Field
from typing import Any

from ai_shell.core.interfaces import CustomFunction, FunctionInput, CommandError, EmptyFunctionInput, OptionOnlyFunctionInput


def get_default_model():
    """Get default Ollama model client."""
    try:
        from ollama import Client
        model = "llama3.1"
        client = Client()
        return partial(client.chat, model=model, stream=False)
    except ImportError:
        return None


class ModelNotFoundError(CommandError):
    pass


DEFAULT_SUMMARY_INSTRUCTIONS = (
        "Provide a succinct summary that captures the high level themes and key details of the text. "
        "End the summary with a short, one line, tl;dr (too long, didn't read) summary of the text"
    )

# New Summarize
class SummarizeInput(FunctionInput):
    content: Any = Field(description="The text to summarize")
    instructions: str = Field(
        description="Additional summary instructions to provide to the model",
        default=""
    )
    model: str = Field(
        description="Name of the model to use. If not specified it will use the default",
        default=""
    )

async def summarize(_input: SummarizeInput) -> str:
    """
    Summarize the provided text.
    """
    if not _input.model:
        model = get_default_model()
        if not model:
            raise  ModelNotFoundError("Error: Ollama not installed or not available. Install with: pip install ollama")
    else:
        raise NotImplementedError("Model selection is not currently available")
    
    instructions = _input.instructions or DEFAULT_SUMMARY_INSTRUCTIONS

     # Create messages
    messages = [
        {
            "role": "system",
            "content": f"You are a helpful assistant whose job is to summarize the provided text. {instructions}"
        },
        {
            "role": "user",
            "content": _input.content
        }
    ]

    # Call model
    try:
        result = model(messages=messages)
        return result.message.content or ""
    except Exception as e:
        return f"Error calling model: {e}"


class ContextAddSchema(FunctionInput):
    content: str = Field(description="The content to add to the Agent's context")
    key: str = Field(
        description="The dict key to assign the context too. By default it will assign to 'user_context'",
        default="user_context",
    )
    append: bool = Field(
        description="Whether or not to append the new context to the key. Will overwrite the other information if 'False'",
        default=True,
    )
    quiet: bool = Field(
        description="If 'True' it wll not provide any output upon success. 'False by default",
        default=False,    
    )

async def add_context(_input: ContextAddSchema, context_session={}) -> str:
    """
    """

    if _input.key not in context_session:
        context_session[_input.key] = []
    if _input.append:
        context_session[_input.key].append(_input.content)

        return f"Context added to {_input.key} key" if not _input.quiet else ""
    context_session[_input.key] = [_input.content]
    return f"New context set for {_input.key} key" if not _input.quiet else ""


class ClearContextSchema(OptionOnlyFunctionInput):
    key: str = Field(
        description="The dict key to assign the context too. By default it will assign to 'user_context'",
        default="user_context",
    )
    quiet: bool = Field(
        description="If 'True' it wll not provide any output upon success. 'False by default",
        default=False,    
    )


async def clear_context(_input: ClearContextSchema, context_session: dict = {}) -> str:
    """
    """
    if _input.key:
        if _input.key not in context_session:
            print(f"No context stored for {_input.key}. Context remains unchanged.")
        context_session[_input.key] = []
        return f"Cleared context for key {_input.key}" if not _input.quiet else ""
    for k, _ in context_session.items():
        context_session[k] = []
    return f"Cleared all context" if not _input.quiet else ""


class ViewContextSchema(OptionOnlyFunctionInput):
    key: str = Field(
        description="The dict key to assign the context too. By default it will assign to 'user_context'",
        default="user_context",
    )


async def view_context(_input: ViewContextSchema, context_session: dict = {}) -> str:
    """
    """
    if _input.key:
        if _input.key not in context_session:
            print(f"No context stored for {_input.key}.")
        
        return f"Context for {_input.key}:\n\n{context_session[_input.key]}\n\n" + "=="*20
    
    context_str = "All Context:\n\n"
    for k, v in context_session.items():
        context_str += f"{k}:\n{v}\n\n"
    context_str += "==" * 20
    return context_str


def register_default_ai_commands(executor):
    """
    Register all AI commands included with the default ai-shell installation
    """
    summarize_command = CustomFunction(name="summarize",
                               description="Summarize the provided text",
                               func=summarize,
                               input_schema=SummarizeInput)
    
    add_context_command = CustomFunction(name="add_context",
                                         description="Add content to the agent's context window",
                                         func=partial(add_context, context_session=executor.context_session),
                                         input_schema=ContextAddSchema)
    
    clear_context_command = CustomFunction(name="clear_context",
                                         description="Clear the agent's context. Specify a key to clear only that context.",
                                         func=partial(clear_context, context_session=executor.context_session),
                                         input_schema=ClearContextSchema)
    
    view_context_command = CustomFunction(name="view_context",
                                         description="View the agent's current context",
                                         func=partial(view_context, context_session=executor.context_session),
                                         input_schema=ViewContextSchema)
    
    
    executor.register_function(summarize_command)
    executor.register_function(add_context_command)
    executor.register_function(clear_context_command)
    executor.register_function(view_context_command)

    
    print(f"Registered Summarize, Add Context and Clear Context commands")