"""Docker-based bash executor for sandboxed command execution."""

import asyncio
import subprocess
from typing import AsyncIterator, Optional, Dict
from ai_shell.core.interfaces import CommandResult


class DockerBashExecutor:
    """
    Docker-based bash executor that runs commands in a sandboxed container.

    This provides a safer environment for command execution, preventing
    accidental damage to the host system.
    """

    def __init__(self,
                 image: str = "ubuntu:latest",
                 work_dir: str = "/workspace",
                 mount_current_dir: bool = True,
                 container_name_prefix: str = "ai-shell"):
        """
        Initialize Docker bash executor.

        Args:
            image: Docker image to use (default: ubuntu:latest)
            work_dir: Working directory inside container
            mount_current_dir: Whether to mount current directory into container
            container_name_prefix: Prefix for container names
        """
        self.image = image
        self.work_dir = work_dir
        self.mount_current_dir = mount_current_dir
        self.container_name_prefix = container_name_prefix
        self._docker_available = None

    async def _check_docker(self) -> bool:
        """Check if Docker is available."""
        if self._docker_available is not None:
            return self._docker_available

        try:
            process = await asyncio.create_subprocess_exec(
                'docker', '--version',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await process.communicate()
            self._docker_available = process.returncode == 0
        except FileNotFoundError:
            self._docker_available = False

        return self._docker_available

    async def _ensure_image(self) -> bool:
        """Ensure Docker image is available (pull if needed)."""
        # Check if image exists
        process = await asyncio.create_subprocess_exec(
            'docker', 'image', 'inspect', self.image,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await process.communicate()

        if process.returncode == 0:
            return True

        # Image not found, try to pull
        try:
            process = await asyncio.create_subprocess_exec(
                'docker', 'pull', self.image,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            return process.returncode == 0
        except Exception:
            return False

    def _build_docker_command(self, command: str) -> list:
        """
        Build docker run command.

        Args:
            command: Shell command to execute

        Returns:
            List of command arguments for docker run
        """
        import os

        docker_cmd = [
            'docker', 'run',
            '--rm',  # Remove container after execution
            '--network', 'none',  # No network access (safer)
        ]

        # Mount current directory if requested
        if self.mount_current_dir:
            current_dir = os.getcwd()
            docker_cmd.extend([
                '-v', f'{current_dir}:{self.work_dir}:ro',  # Read-only mount
                '-w', self.work_dir
            ])

        # Add image and command
        docker_cmd.extend([
            self.image,
            'sh', '-c', command
        ])

        return docker_cmd

    async def execute(self,
                     command: str,
                     input_data: Optional[bytes] = None,
                     timeout: int = 30) -> CommandResult:
        """
        Execute bash command in Docker container.

        Args:
            command: Shell command to execute
            input_data: Optional stdin input
            timeout: Timeout in seconds

        Returns:
            CommandResult with output or error
        """
        # Check Docker availability
        if not await self._check_docker():
            return CommandResult(
                success=False,
                error="Docker is not available. Please install Docker or use --bash-backend=native",
                metadata={"docker_available": False}
            )

        # Ensure image is available
        if not await self._ensure_image():
            return CommandResult(
                success=False,
                error=f"Failed to pull Docker image: {self.image}",
                metadata={"image": self.image}
            )

        try:
            # Build docker command
            docker_cmd = self._build_docker_command(command)

            # Run command in Docker
            process = await asyncio.create_subprocess_exec(
                *docker_cmd,
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
                    metadata={
                        "returncode": process.returncode,
                        "command": command,
                        "docker": True,
                        "image": self.image
                    }
                )
            else:
                return CommandResult(
                    success=False,
                    error=stderr.decode('utf-8', errors='replace'),
                    output=stdout.decode('utf-8', errors='replace'),
                    metadata={
                        "returncode": process.returncode,
                        "command": command,
                        "docker": True,
                        "image": self.image
                    }
                )

        except asyncio.TimeoutError:
            return CommandResult(
                success=False,
                error=f"Command timed out after {timeout} seconds",
                metadata={"timeout": True, "command": command, "docker": True}
            )
        except Exception as e:
            return CommandResult(
                success=False,
                error=f"Docker execution error: {e}",
                metadata={"exception": str(e), "command": command, "docker": True}
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
        # Check Docker availability
        if not await self._check_docker():
            yield b"Error: Docker is not available\n"
            return

        # Ensure image is available
        if not await self._ensure_image():
            yield f"Error: Failed to pull image {self.image}\n".encode()
            return

        try:
            # Build docker command
            docker_cmd = self._build_docker_command(command)

            # Start process
            process = await asyncio.create_subprocess_exec(
                *docker_cmd,
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


class DockerBashExecutorWithWrite(DockerBashExecutor):
    """
    Docker executor with read-write mount (less safe, more functional).

    Use this if you need to modify files in the current directory.
    """

    def _build_docker_command(self, command: str) -> list:
        """Build docker run command with read-write mount."""
        import os

        docker_cmd = [
            'docker', 'run',
            '--rm',
            '--network', 'none',
        ]

        if self.mount_current_dir:
            current_dir = os.getcwd()
            docker_cmd.extend([
                '-v', f'{current_dir}:{self.work_dir}',  # Read-write mount
                '-w', self.work_dir
            ])

        docker_cmd.extend([
            self.image,
            'sh', '-c', command
        ])

        return docker_cmd
