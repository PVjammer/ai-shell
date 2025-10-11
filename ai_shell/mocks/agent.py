"""Mock agent for testing."""

import asyncio
from typing import AsyncIterator, Dict


class MockAgent:
    """
    Mock AI agent that returns canned responses.

    Useful for testing shell layer without real LLM.
    """

    def __init__(self, delay: float = 0.05):
        """
        Initialize mock agent.

        Args:
            delay: Delay between tokens (simulates streaming)
        """
        self.delay = delay
        self.responses = {
            "default": "This is a mock response from the AI agent.",
            "hello": "Hello! I'm a mock AI agent. I'm not real, but I can help test the shell!",
            "summarize": "Here's a mock summary: The content discusses various topics in a structured way.",
        }

    async def chat(self, message: str, context: Dict = None) -> AsyncIterator[str]:
        """Stream mock chat response."""
        # Choose response based on message content
        response = self._get_response(message)

        # Stream token by token
        for token in response.split():
            await asyncio.sleep(self.delay)
            yield token + " "

    async def generate(self, prompt: str, context: Dict = None) -> str:
        """Generate complete mock response."""
        return self._get_response(prompt)

    def _get_response(self, message: str) -> str:
        """Select appropriate canned response."""
        message_lower = message.lower()

        if "hello" in message_lower or "hi" in message_lower:
            return self.responses["hello"]
        elif "summarize" in message_lower:
            return self.responses["summarize"]
        else:
            return self.responses["default"]

    def add_response(self, trigger: str, response: str):
        """Add custom response for testing."""
        self.responses[trigger] = response
