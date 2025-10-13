
import asyncio
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
    
    async def _quick_chat(self, message: str, context: dict | None):
        self.messages.append({"role": "user", "content": message})
        response_stream = self._call_func(messages=self.messages)
        print("Got responsse")
        for chunk in response_stream:
            yield chunk.message.content

    async def chat(self, message: str, context: Dict | None = None) -> AsyncIterator[str]:
        if context:
            print(f"Context: {context}\n\n")
        
        # Simple model chat
        self.messages.append({"role": "user", "content": message})
        response_stream = self._call_func(messages=self.messages, stream=True)

        for chunk in response_stream:
            yield chunk.message.content + ""
        
    async def generate(message: str, context: Dict | None = None) -> AsyncIterator[str]:
        if context:
            print(f"Context: {context}\n\n")
        
        # Simple model chat
        self.messages.append({"role": "user", "content": message})
        response = self._call_func(messages=self.messages, stream=False)

        return response.message.content