"""Real bash executor for ai-shell."""

import asyncio
import subprocess
import os
from typing import AsyncIterator, Optional
from ai_shell.core.interfaces import CommandResult


class BashExecutor:
    """
    Real bash command executor.

    Executes actual shell commands using subprocess.
    Maintains a persistent shell session to support cd, environment variables, etc.
    """

    def __init__(self):
        """Initialize bash executor with persistent shell."""
        self.cwd = os.getcwd()
        self.env = os.environ.copy()

    async def execute(self,
                     command: str,
                     input_data: Optional[bytes] = None,
                     timeout: int = 30) -> CommandResult:
        """
        Execute bash command in persistent shell environment.

        Args:
            command: Shell command to execute
            input_data: Optional stdin input
            timeout: Timeout in seconds

        Returns:
            CommandResult with output or error
        """
        try:
            # Handle cd command specially to update persistent working directory
            cmd_stripped = command.strip()
            if cmd_stripped.startswith('cd ') or cmd_stripped == 'cd':
                return await self._handle_cd(cmd_stripped)

            # Run command in subprocess with persistent environment
            process = await asyncio.create_subprocess_shell(
                command,
                stdin=asyncio.subprocess.PIPE if input_data else None,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.cwd,
                env=self.env,
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
                    metadata={"returncode": process.returncode, "command": command, "cwd": self.cwd}
                )
            else:
                return CommandResult(
                    success=False,
                    error=stderr.decode('utf-8', errors='replace'),
                    output=stdout.decode('utf-8', errors='replace'),
                    metadata={"returncode": process.returncode, "command": command, "cwd": self.cwd}
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

    async def _handle_cd(self, command: str) -> CommandResult:
        """
        Handle cd command by updating persistent working directory.

        Args:
            command: cd command string

        Returns:
            CommandResult
        """
        try:
            parts = command.split(maxsplit=1)

            if len(parts) == 1 or not parts[1]:
                # cd with no args goes to home
                new_dir = os.path.expanduser('~')
            else:
                # cd with path
                target = parts[1].strip()

                # Remove surrounding quotes if present
                if (target.startswith('"') and target.endswith('"')) or \
                   (target.startswith("'") and target.endswith("'")):
                    target = target[1:-1]

                # Handle ~ expansion
                target = os.path.expanduser(target)
                # Handle relative paths
                if not os.path.isabs(target):
                    new_dir = os.path.join(self.cwd, target)
                else:
                    new_dir = target

            # Normalize and resolve the path
            new_dir = os.path.normpath(new_dir)

            # Check if directory exists
            if not os.path.exists(new_dir):
                return CommandResult(
                    success=False,
                    error=f"cd: {target}: No such file or directory",
                    metadata={"command": command, "cwd": self.cwd}
                )

            if not os.path.isdir(new_dir):
                return CommandResult(
                    success=False,
                    error=f"cd: {target}: Not a directory",
                    metadata={"command": command, "cwd": self.cwd}
                )

            # Update working directory
            self.cwd = new_dir

            return CommandResult(
                success=True,
                output="",
                metadata={"command": command, "cwd": self.cwd}
            )

        except Exception as e:
            return CommandResult(
                success=False,
                error=f"cd: {e}",
                metadata={"command": command, "cwd": self.cwd}
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
            # Start process with persistent environment
            process = await asyncio.create_subprocess_shell(
                command,
                stdin=asyncio.subprocess.PIPE if input_data else None,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,  # Merge stderr into stdout
                cwd=self.cwd,
                env=self.env,
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

    def get_cwd(self) -> str:
        """Get current working directory."""
        return self.cwd

    def get_env(self) -> dict:
        """Get current environment variables."""
        return self.env.copy()
