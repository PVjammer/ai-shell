"""Mock bash executor for testing."""

import asyncio
from typing import AsyncIterator, Optional
from ai_shell.core.interfaces import CommandResult


class MockBashExecutor:
    """
    Mock bash executor for testing.

    Returns mock output for common commands.
    """

    def __init__(self, delay: float = 0.05):
        """
        Initialize mock bash executor.

        Args:
            delay: Delay for streaming simulation
        """
        self.delay = delay

        # Mock outputs for common commands
        self.mock_outputs = {
            "ls": "file1.txt\nfile2.py\nREADME.md\n",
            "pwd": "/home/user/ai-shell\n",
            "echo": None,  # Will echo the arguments
            "cat": None,   # Will return mock file content
        }

    async def execute(self,
                     command: str,
                     input_data: Optional[bytes] = None,
                     timeout: int = 30) -> CommandResult:
        """Execute mock bash command."""

        # Parse command
        parts = command.split()
        if not parts:
            return CommandResult(
                success=False,
                error="Empty command"
            )

        cmd = parts[0]

        # Handle specific commands
        if cmd in self.mock_outputs:
            if cmd == "echo":
                output = " ".join(parts[1:]) + "\n"
            elif cmd == "cat":
                output = f"Mock content of {parts[1] if len(parts) > 1 else 'file'}\n"
            else:
                output = self.mock_outputs[cmd]

            return CommandResult(
                success=True,
                output=output,
                metadata={"mock": True, "command": command}
            )

        # Default mock output
        return CommandResult(
            success=True,
            output=f"Mock output for: {command}\n",
            metadata={"mock": True, "command": command}
        )

    async def execute_streaming(self,
                               command: str,
                               input_data: Optional[bytes] = None) -> AsyncIterator[bytes]:
        """Execute command with streaming output."""

        result = await self.execute(command, input_data)

        if not result.success:
            yield result.error.encode()
            return

        # Stream byte by byte (simulating real process output)
        for char in result.output:
            await asyncio.sleep(self.delay / 10)  # Faster than word streaming
            yield char.encode()
