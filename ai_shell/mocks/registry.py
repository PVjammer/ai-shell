"""Mock tool registry for testing."""

from typing import List, Optional, Dict
from ai_shell.core.interfaces import ToolDefinition


class MockToolRegistry:
    """
    Mock tool registry with pre-defined tools.

    Provides a set of mock tools for testing the shell.
    """

    def __init__(self):
        """Initialize with mock tools."""
        self._tools: Dict[str, ToolDefinition] = {}

        # Register default mock tools
        self._register_defaults()

    def _register_defaults(self):
        """Register default mock tools."""
        default_tools = [
            ToolDefinition(
                name="summarize",
                description="Summarize text into key points",
                category="text",
                requires_approval=False
            ),
            ToolDefinition(
                name="search",
                description="Search for information",
                category="information",
                requires_approval=False
            ),
            ToolDefinition(
                name="analyze",
                description="Analyze data and find patterns",
                category="analysis",
                requires_approval=False
            ),
            ToolDefinition(
                name="report",
                description="Generate formatted report",
                category="output",
                requires_approval=False
            ),
            ToolDefinition(
                name="explain",
                description="Explain code or commands",
                category="text",
                requires_approval=False
            ),
        ]

        for tool in default_tools:
            self.register(tool)

    def register(self, tool: ToolDefinition) -> None:
        """Register a tool."""
        self._tools[tool.name] = tool

    def unregister(self, name: str) -> None:
        """Unregister a tool."""
        if name in self._tools:
            del self._tools[name]

    def get(self, name: str) -> Optional[ToolDefinition]:
        """Get tool by name."""
        return self._tools.get(name)

    def list(self, category: str = None) -> List[ToolDefinition]:
        """List tools, optionally filtered by category."""
        tools = list(self._tools.values())

        if category:
            tools = [t for t in tools if t.category == category]

        return tools

    def list_names(self) -> List[str]:
        """Get list of tool names."""
        return list(self._tools.keys())
