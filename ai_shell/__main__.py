"""Entry point for ai-shell CLI."""

import asyncio
import sys
import click

from ai_shell.shell.repl import REPL, REPLConfig
from ai_shell.shell.parser import Parser
from ai_shell.shell.renderer import Renderer
from ai_shell.core.memory import MemoryStore
from ai_shell.core.bash_executor import BashExecutor
from ai_shell.core.docker_bash_executor import DockerBashExecutor, DockerBashExecutorWithWrite


@click.command()
@click.option('--debug', is_flag=True, help='Enable debug mode')
@click.option('--prompt', default='ai> ', help='Custom prompt string')
@click.option('--vi-mode', is_flag=True, help='Enable vi mode')
@click.option('--history', default=None, help='Custom history file path')
@click.option('--bash-backend',
              type=click.Choice(['native', 'docker', 'docker-rw', 'mock'], case_sensitive=False),
              default='native',
              help='Bash executor backend: native (direct), docker (sandboxed read-only), docker-rw (sandboxed read-write), mock (testing)')
@click.option('--docker-image', default='ubuntu:latest', help='Docker image to use (only for docker backends)')
def main(debug, prompt, vi_mode, history, bash_backend, docker_image):
    """
    ai-shell: AI-enhanced interactive shell.

    A local-first, human-in-the-loop AI shell that unifies LLMs, Bash,
    and MCP tools into a single interactive environment.
    """

    # Initialize components
    parser = Parser()
    renderer = Renderer()
    memory = MemoryStore()

    # Select bash executor backend
    if bash_backend == 'docker':
        bash_executor = DockerBashExecutor(image=docker_image)
        if debug:
            renderer.print_info(f"Using Docker backend (read-only) with image: {docker_image}")
    elif bash_backend == 'docker-rw':
        bash_executor = DockerBashExecutorWithWrite(image=docker_image)
        if debug:
            renderer.print_info(f"Using Docker backend (read-write) with image: {docker_image}")
    elif bash_backend == 'mock':
        from ai_shell.mocks import MockBashExecutor
        bash_executor = MockBashExecutor()
        if debug:
            renderer.print_info("Using mock bash backend")
    else:  # native
        bash_executor = BashExecutor()
        if debug:
            renderer.print_info("Using native bash backend")

    config = REPLConfig(
        prompt=prompt,
        debug_mode=debug,
        vi_mode=vi_mode,
        history_file=history if history else "~/.ai_shell/history"
    )

    # Create REPL with selected bash executor
    # (agent, executor, and registry still use mocks)
    repl = REPL(parser, renderer, memory, bash_executor=bash_executor, config=config)

    # Run REPL
    try:
        asyncio.run(repl.start())
    except KeyboardInterrupt:
        renderer.print_info("\nInterrupted")
        return 0
    except Exception as e:
        renderer.print_error(f"Fatal error: {e}")
        if debug:
            import traceback
            traceback.print_exc()
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
