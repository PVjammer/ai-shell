"""Output renderer for ai-shell."""

from typing import AsyncIterator, Optional
from enum import Enum
from rich.console import Console
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.panel import Panel
from rich.live import Live
from rich.text import Text


class OutputType(Enum):
    """Types of output."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"
    DEBUG = "debug"
    AI_RESPONSE = "ai_response"
    BASH_OUTPUT = "bash_output"
    CODE = "code"


class Renderer:
    """
    Output renderer for ai-shell.

    Handles all terminal output formatting using Rich library:
    - Markdown rendering for AI responses
    - Syntax highlighting for code
    - Streaming token display
    - Colored status messages
    - Progress indicators
    """

    def __init__(self,
                 console: Console = None,
                 theme: str = "monokai"):
        """
        Initialize renderer.

        Args:
            console: Rich console instance
            theme: Syntax highlighting theme
        """
        self.console = console or Console()
        self.theme = theme

    def render(self, content: str, output_type: OutputType = OutputType.INFO):
        """
        Render content based on type.

        Args:
            content: Content to render
            output_type: Type of output (determines formatting)
        """
        if output_type == OutputType.AI_RESPONSE:
            self.render_markdown(content)
        elif output_type == OutputType.CODE:
            self.render_code(content)
        elif output_type == OutputType.ERROR:
            self.print_error(content)
        elif output_type == OutputType.WARNING:
            self.print_warning(content)
        elif output_type == OutputType.SUCCESS:
            self.print_success(content)
        elif output_type == OutputType.DEBUG:
            self.print_debug(content)
        else:
            self.print_info(content)

    def render_markdown(self, content: str):
        """
        Render markdown content.

        Used for AI responses.
        """
        md = Markdown(content)
        self.console.print(md)

    def render_code(self,
                   code: str,
                   language: str = "python",
                   line_numbers: bool = False):
        """
        Render code with syntax highlighting.

        Args:
            code: Code to render
            language: Programming language for highlighting
            line_numbers: Show line numbers
        """
        syntax = Syntax(
            code,
            language,
            theme=self.theme,
            line_numbers=line_numbers
        )
        self.console.print(syntax)

    async def render_streaming(self,
                              token_stream: AsyncIterator[str],
                              output_type: OutputType = OutputType.AI_RESPONSE):
        """
        Render streaming tokens in real-time.

        Args:
            token_stream: Async iterator of tokens
            output_type: Output type (determines formatting)
        """
        if output_type == OutputType.AI_RESPONSE:
            await self._stream_markdown(token_stream)
        else:
            await self._stream_plain(token_stream)

    async def _stream_markdown(self, token_stream: AsyncIterator[str]):
        """Stream markdown tokens with live rendering."""
        content = ""

        with Live(Markdown(content), console=self.console, auto_refresh=False) as live:
            async for token in token_stream:
                content += token
                live.update(Markdown(content), refresh=True)

        # Final newline
        self.console.print()

    async def _stream_plain(self, token_stream: AsyncIterator[str]):
        """Stream plain text tokens."""
        async for token in token_stream:
            self.console.print(token, end="")
        self.console.print()  # Final newline

    def print_info(self, message: str):
        """Print info message."""
        self.console.print(message)

    def print_success(self, message: str):
        """Print success message (green)."""
        self.console.print(f"[green]✓[/green] {message}")

    def print_warning(self, message: str):
        """Print warning message (yellow)."""
        self.console.print(f"[yellow]⚠[/yellow] {message}")

    def print_error(self, message: str):
        """Print error message (red)."""
        self.console.print(f"[red]✗[/red] {message}")

    def print_debug(self, message: str):
        """Print debug message (dim)."""
        self.console.print(f"[dim]DEBUG: {message}[/dim]")

    def render_panel(self,
                    content: str,
                    title: str = None,
                    border_style: str = "blue"):
        """
        Render content in a panel.

        Args:
            content: Panel content
            title: Panel title
            border_style: Border color
        """
        panel = Panel(
            content,
            title=title,
            border_style=border_style
        )
        self.console.print(panel)

    def render_table(self,
                    headers: list,
                    rows: list,
                    title: str = None):
        """
        Render data as table.

        Args:
            headers: Column headers
            rows: Table rows
            title: Table title
        """
        from rich.table import Table

        table = Table(title=title)

        for header in headers:
            table.add_column(header, style="cyan")

        for row in rows:
            table.add_row(*[str(cell) for cell in row])

        self.console.print(table)

    def show_progress(self,
                     description: str,
                     total: Optional[int] = None):
        """
        Show progress indicator.

        Args:
            description: Progress description
            total: Total steps (if known)

        Returns:
            Progress context manager
        """
        if total:
            from rich.progress import Progress, SpinnerColumn, TextColumn
            progress = Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console
            )
            return progress
        else:
            # Indeterminate spinner
            return self.console.status(description)
