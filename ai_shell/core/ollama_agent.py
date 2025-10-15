
import asyncio
import logging
import json
from functools import partial

from typing import AsyncIterator, Dict
from ai_shell.core.interfaces import IAgent
from ollama import Client, AsyncClient
from ollama._types import ChatResponse


CONTEXT_PROMPT = """The context consists of your chat history with the user, as well as additional information added to the context by the user.
If the context is relevant to the user message, use this information when responding to the user. 

You have access to the previous conversation for context.

Use that history only when it’s directly relevant to the user’s current message — for example, to:

Clarify ambiguous references (“it,” “that file,” “the same schema,” etc.)

Maintain continuity in multi-step reasoning or related topics

Preserve consistent naming, formatting, or style choices made earlier

However, if the current request is self-contained or unrelated, do not refer back to prior messages or summarize them.
Treat each new question as independent unless the user explicitly connects it to earlier content.

If the user asks the same or similar question multiple times, do not refernce this and do not use your prior response. Assume that
you have access to new information and regenerate the response based on the available context (without using your previous answer).

Always prioritize clarity, directness, and relevance to the current request.
"""


class OllamaAgent(IAgent):

    system_message: str = """You are a helpful assistant. Do your best to respond to the user message. 
    
    **IMPORTANT**: if you do not have enough information or the user message is ambiguous, then provide a response describing the ambiguity or the
    lack of information. UNDER NO CIRCUMSTANCES ARE YOU TO GUESS OR INVENT FACTS!!
    """

    def __init__(self, model: str = "llama3.1", client_args: dict = {}, tools: list = [], is_stream: bool = True):
        """
        Simple AI Agent using Ollama
        """
        self._client = Client(**client_args)
        self._model = model
        self._tools = tools
        self._call_func = partial(
                self._client.chat,
                model=model,
                tools=tools,
            )
        
        self.messages = [{"role": "system", "content": self.system_message}]
        print("Initialized agent")
        
    def __call__(self, _input: list[dict]):
        return self._call_func(messages=_input)

    async def chat(self, message: str, context: Dict | None = None) -> AsyncIterator[str]:
        messages = self.messages
        if context:
            for k, v in context.items():
                print(f"{k}:  {len(v)}")
            print("=="*10)
            if not isinstance(context, dict):
                raise ValueError(f"Got malformed context. Expected dict. Got {type(context)}")
            ctx = json.dumps(context)
            messages.append({"role": "system", "content": f"You have access to the following context: {ctx}. {CONTEXT_PROMPT}"})
            # message = f"{message} If the following context is relevant to the query or task provided by the user, use the context to aid in providing a response:\n\n{ctx}"
            print("Loaded Context")
        # Simple model chat
        messages.append({"role": "user", "content": message})
        if context:
            if "chat_history" not in context:
                context["chat_history"] = []
            context["chat_history"].append({"role": "user", "content": message})
        response_stream = self._call_func(messages=messages, stream=True)
        chat_response = []
        for chunk in response_stream:
            chat_response.append(chunk.message.content)
            yield chunk.message.content + ""

        if context:
            if "chat_history" not in context:
                context["chat_history"] = []
            try:
                context["chat_history"].append({"role": "user", "content": message})
                context["chat_history"].append({"role": "assistant", "content": "".join(chat_response)})
            except Exception as e:
                logging.exception("Error building chat history: {e}")

    async def generate(message: str, context: Dict | None = None) -> AsyncIterator[str]:
        if context:
            for k, v in context.items():
                print(f"{k}:  {len(v)}")
            print("=="*10)
            if not isinstance(context, dict):
                raise ValueError(f"Got malformed context. Expected dict. Got {type(context)}")
            ctx = json.dumps(context)
            message = f"{message} Use the following context to aid in providing a response:\n\n{ctx}"
            print("Loaded Context")
        
        # Simple model chat
        self.messages.append({"role": "user", "content": message})
        response = self._call_func(messages=self.messages, stream=False)

        return response.message.content