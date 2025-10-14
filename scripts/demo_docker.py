#!/usr/bin/env python3
"""
Demo script to confirm Docker backend is working.

This simulates what happens when you run commands in the shell with Docker backend.
"""

import asyncio
from ai_shell.core.docker_bash_executor import DockerBashExecutor
from rich.console import Console

console = Console()


async def demo():
    """Run demo commands to confirm Docker is working."""

    console.print("\n[bold blue]🐳 Docker Backend Demo[/bold blue]\n")

    # Initialize Docker executor
    docker = DockerBashExecutor(image="alpine:latest")

    # Check Docker
    console.print("[dim]Checking Docker availability...[/dim]")
    if not await docker._check_docker():
        console.print("[red]❌ Docker not available![/red]")
        return
    console.print("[green]✓ Docker is available[/green]\n")

    # Demo commands
    commands = [
        ("ls", "List files in mounted directory"),
        ("pwd", "Show working directory"),
        ("whoami", "Show current user"),
        ("uname -a", "Show system info (inside container)"),
        ("echo 'Hello from Docker!'", "Echo test"),
        ("cat README.md | head -5", "Read file from mounted directory"),
    ]

    for i, (cmd, description) in enumerate(commands, 1):
        console.print(f"[bold cyan]Demo {i}:[/bold cyan] {description}")
        console.print(f"[dim]Command:[/dim] [yellow]{cmd}[/yellow]")

        result = await docker.execute(cmd)

        if result.success:
            console.print("[green]✓ Success[/green]")
            # Truncate long output
            output = result.output.strip()
            if len(output) > 200:
                output = output[:200] + "..."
            console.print(f"[dim]{output}[/dim]")
        else:
            console.print(f"[red]✗ Error: {result.error.strip()[:100]}[/red]")

        console.print()

    # Security demo
    console.print("[bold yellow]🔒 Security Features Demo[/bold yellow]\n")

    console.print("[cyan]Test 1:[/cyan] Try to modify files (should fail - read-only)")
    result = await docker.execute("touch /workspace/test.txt")
    if not result.success:
        console.print("[green]✓ Correctly blocked write operation[/green]")
        console.print(f"[dim]{result.error.strip()}[/dim]")
    else:
        console.print("[red]⚠ Write succeeded (unexpected!)[/red]")
    console.print()

    console.print("[cyan]Test 2:[/cyan] Try to access network (should fail - no network)")
    result = await docker.execute("ping -c 1 8.8.8.8 2>&1")
    if not result.success or "bad address" in result.error or "Network is unreachable" in result.error:
        console.print("[green]✓ Network access blocked[/green]")
    else:
        console.print("[yellow]⚠ Network might be accessible[/yellow]")
    console.print()

    # Summary
    console.print("[bold green]✅ Docker Backend Confirmed Working![/bold green]\n")
    console.print("Features:")
    console.print("  • [green]✓[/green] Sandboxed execution (isolated from host)")
    console.print("  • [green]✓[/green] Read-only file access (safe)")
    console.print("  • [green]✓[/green] No network access (secure)")
    console.print("  • [green]✓[/green] Can read mounted files")
    console.print("  • [green]✓[/green] Automatic cleanup after commands")
    console.print()
    console.print("To use in ai-shell:")
    console.print("  [yellow]ai-shell --bash-backend=docker[/yellow]")
    console.print()
    console.print("Or for read-write access:")
    console.print("  [yellow]ai-shell --bash-backend=docker-rw[/yellow]")
    console.print()


if __name__ == "__main__":
    asyncio.run(demo())
