"""Mock command executor for testing."""

import asyncio
from typing import AsyncIterator, List, Optional, Dict
from ai_shell.core.interfaces import CommandResult


class MockCommandExecutor:
    """
    Mock executor for agentic commands.

    Returns mock responses for commands like summarize, search, etc.
    """

    def __init__(self, delay: float = 0.05):
        """
        Initialize mock executor.

        Args:
            delay: Delay for streaming simulation
        """
        self.delay = delay

        # Canned responses for different commands
        self.command_responses = {
            "summarize": self._mock_summarize,
            "search": self._mock_search,
            "analyze": self._mock_analyze,
            "report": self._mock_report,
            "explain": self._mock_explain,
        }

    async def execute(self,
                     command_name: str,
                     args: List[str],
                     input_data: Optional[str] = None,
                     context: Dict = None) -> CommandResult:
        """Execute command and return complete result."""

        if command_name not in self.command_responses:
            return CommandResult(
                success=False,
                error=f"Unknown command: {command_name}"
            )

        try:
            handler = self.command_responses[command_name]
            output = await handler(args, input_data, context)

            return CommandResult(
                success=True,
                output=output,
                metadata={"mock": True, "command": command_name}
            )

        except Exception as e:
            return CommandResult(
                success=False,
                error=f"Mock execution error: {e}"
            )

    async def execute_streaming(self,
                               command_name: str,
                               args: List[str],
                               input_data: Optional[str] = None,
                               context: Dict = None) -> AsyncIterator[str]:
        """Execute command with streaming output."""

        # Get complete output
        result = await self.execute(command_name, args, input_data, context)

        if not result.success:
            yield f"Error: {result.error}"
            return

        # Stream word by word
        for word in result.output.split():
            await asyncio.sleep(self.delay)
            yield word + " "

    # Mock command implementations

    async def _mock_summarize(self,
                              args: List[str],
                              input_data: Optional[str],
                              context: Dict) -> str:
        """Mock summarize command."""
        if input_data:
            word_count = len(input_data.split())
            return f"**Summary** (mock):\n\nProcessed {word_count} words. Key points:\n- Point 1\n- Point 2\n- Point 3"
        else:
            return "**Summary** (mock): Please provide input to summarize."

    async def _mock_search(self,
                          args: List[str],
                          input_data: Optional[str],
                          context: Dict) -> str:
        """Mock search command."""
        query = " ".join(args) if args else "unknown"
        return f"**Search Results** (mock) for '{query}':\n\n1. Result 1\n2. Result 2\n3. Result 3"

    async def _mock_analyze(self,
                           args: List[str],
                           input_data: Optional[str],
                           context: Dict) -> str:
        """Mock analyze command."""
        return "**Analysis** (mock):\n\n- Patterns detected: 3\n- Anomalies: 1\n- Confidence: 85%"

    async def _mock_report(self,
                          args: List[str],
                          input_data: Optional[str],
                          context: Dict) -> str:
        """Mock report command."""
        return "# Mock Report\n\n## Overview\n\nThis is a mock report generated for testing.\n\n## Details\n\n- Item 1\n- Item 2"

    async def _mock_explain(self,
                           args: List[str],
                           input_data: Optional[str],
                           context: Dict) -> str:
        """Mock explain command."""
        return "**Explanation** (mock):\n\nThis mock explanation provides context about the input. In a real implementation, this would analyze and explain the content."
