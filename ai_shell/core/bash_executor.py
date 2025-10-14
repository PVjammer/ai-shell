"""Real bash executor for ai-shell."""

import asyncio
import subprocess
from typing import AsyncIterator, Optional
from ai_shell.core.interfaces import CommandResult


class BashExecutor:
    """
    Real bash command executor.

    Executes actual shell commands using subprocess.
    """

    def __init__(self):
        """Initialize bash executor."""
        pass

    async def execute(self,
                     command: str,
                     input_data: Optional[bytes] = None,
                     timeout: int = 30) -> CommandResult:
        """
        Execute bash command.

        Args:
            command: Shell command to execute
            input_data: Optional stdin input
            timeout: Timeout in seconds

        Returns:
            CommandResult with output or error
        """
        try:
            # Run command in subprocess
            process = await asyncio.create_subprocess_shell(
                command,
                stdin=asyncio.subprocess.PIPE if input_data else None,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            # Communicate with process
            stdout, stderr = await asyncio.wait_for(
                process.communicate(input=input_data),
                timeout=timeout
            )

            # Check result
            if process.returncode == 0:
                return CommandResult(
                    success=True,
                    output=stdout.decode('utf-8', errors='replace'),
                    metadata={"returncode": process.returncode, "command": command}
                )
            else:
                return CommandResult(
                    success=False,
                    error=stderr.decode('utf-8', errors='replace'),
                    output=stdout.decode('utf-8', errors='replace'),
                    metadata={"returncode": process.returncode, "command": command}
                )

        except asyncio.TimeoutError:
            return CommandResult(
                success=False,
                error=f"Command timed out after {timeout} seconds",
                metadata={"timeout": True, "command": command}
            )
        except Exception as e:
            return CommandResult(
                success=False,
                error=f"Execution error: {e}",
                metadata={"exception": str(e), "command": command}
            )

    async def execute_streaming(self,
                               command: str,
                               input_data: Optional[bytes] = None) -> AsyncIterator[bytes]:
        """
        Execute bash command with streaming output.

        Args:
            command: Shell command
            input_data: Optional stdin

        Yields:
            Output chunks (bytes)
        """
        try:
            # Start process
            process = await asyncio.create_subprocess_shell(
                command,
                stdin=asyncio.subprocess.PIPE if input_data else None,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,  # Merge stderr into stdout
            )

            # Send input if provided
            if input_data:
                process.stdin.write(input_data)
                await process.stdin.drain()
                process.stdin.close()

            # Stream output
            while True:
                chunk = await process.stdout.read(1024)
                if not chunk:
                    break
                yield chunk

            # Wait for completion
            await process.wait()

        except Exception as e:
            yield f"Error: {e}".encode()
