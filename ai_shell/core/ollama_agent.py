
import asyncio
import json
from functools import partial

from typing import AsyncIterator, Dict
from ai_shell.core.interfaces import IAgent
from ollama import Client, AsyncClient
from ollama._types import ChatResponse

class OllamaAgent(IAgent):

    system_message: str = "You are a helpful assistant"

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
        
        self.messages = [{"role": "assistant", "content": self.system_message}]
        print("Initialized agent")
        
    def __call__(self, _input: list[dict]):
        return self._call_func(messages=_input)

    async def chat(self, message: str, context: Dict | None = None) -> AsyncIterator[str]:
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
        response_stream = self._call_func(messages=self.messages, stream=True)

        for chunk in response_stream:
            yield chunk.message.content + ""
        
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