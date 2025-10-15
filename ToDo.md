# Project Review Summary - ToDo List

Based on comprehensive review of the ai-shell project on 2025-10-15.

## 1. Missing Dependencies in pyproject.toml

Your `pyproject.toml` is missing several critical dependencies that are actively used in the codebase:

**Required additions:**
```toml
dependencies = [
    "prompt-toolkit>=3.0.0",
    "rich>=13.0.0",
    "click>=8.0.0",
    "ollama>=0.1.0",           # NEW - used in ai_shell/core/ollama_agent.py
    "mcp>=1.0.0",              # NEW - used in ai_shell/core/mcp.py
    "pydantic>=2.0.0",         # NEW - used in ai_shell/core/mcp.py
]
```

The project currently uses `ollama`, `mcp` (Model Context Protocol client), and `pydantic` but they're not listed in dependencies.

## 2. Unused/Legacy Code to Prune

### Files that appear unused:
1. **`ai_shell/core/command_base.py`** (173 lines) - Not imported anywhere in the codebase. This appears to be an earlier implementation of argparse-based command handling that has been superseded.

2. **`ai_shell/core/command_helpers.py`** (343 lines) - Also not imported anywhere. This contains utility functions that may have been intended for use but are currently unused.

3. **Root-level test files** - These should be moved:
   - `test_ai_commands.py` → should be in `tests/commands/`
   - `test_argparse_commands.py` → should be in `tests/commands/`

4. **`ai_shell/commands/file_commands.py`** - Currently commented out in `commands/__init__.py:20`, suggesting it's not ready or not needed. Consider removing or completing it.

### Other observations:
- The `scripts/` directory contains demo/test scripts that could be cleaned up after development stabilizes
- `ai_shell/utils/` package is defined but empty - either use it or remove it from setup

## 3. Refactoring Recommendations

### A. Context Management Issues

**Problem:** The context passing is messy and inconsistent:
- `ai_shell/core/ollama_agent.py:63-95` - Agent manipulates context dict directly
- `ai_shell/commands/ai_commands.py:123-176` - Commands also manipulate context directly
- `ai_shell/core/command_executor.py` - Has `context_session` dict passed around

**Recommendation:** Create a proper `ContextManager` class:

```python
# ai_shell/core/context.py
class ContextManager:
    """Manages conversation and user context for AI agent."""

    def __init__(self):
        self._contexts: Dict[str, List[str]] = {}
        self._chat_history: List[Dict] = []

    def add_context(self, key: str, content: str, append: bool = True):
        """Add content to context under a key."""
        ...

    def get_context(self, key: Optional[str] = None) -> Dict:
        """Get context for agent consumption."""
        ...

    def add_chat_turn(self, role: str, content: str):
        """Add a chat turn to history."""
        ...

    def clear_context(self, key: Optional[str] = None):
        """Clear specific or all context."""
        ...
```

This would eliminate the direct dict manipulation scattered across `ollama_agent.py` and `ai_commands.py`.

### B. MCP Connection Management

**Problem:** In `ai_shell/core/mcp.py:60-61`, the code reconnects on every tool execution:
```python
async def execute(self, args={}, **kwargs):
    await self._client.reconnect()  # This is expensive!
```

And in `install_mcp_servers:137`, it disconnects immediately after connecting:
```python
await _client.connect(...)
mcp_clients[server_name] = _client
await _client.diconnect()  # Typo: "diconnect" should be "disconnect"
```

**Recommendations:**
1. Fix the typo: `diconnect` → `disconnect` throughout
2. Use connection pooling or keep connections alive
3. Consider async context managers for automatic cleanup:

```python
async with mcp_client.connected():
    result = await mcp_client.call_tool(...)
```

### C. Duplicate Input Handling Logic

**Problem:** Similar input handling logic exists in multiple places:
- `ai_shell/commands/ai_commands.py:20-56` (`_get_text_input`)
- `ai_shell/core/command_helpers.py:13-83` (`get_input_text`, unused)
- `ai_shell/core/command_base.py:97-145` (`read_input`, unused)

**Recommendation:**
Since `command_helpers.py` and `command_base.py` are unused, delete them and keep only the working implementation in `ai_commands.py`. If you decide to reuse the logic, extract it to a single utility module.

### D. Agent Interface Inconsistency

**Problem:** In `ai_shell/core/ollama_agent.py`:
- The `chat()` method at line 63 is async and streaming
- The `generate()` method at line 96 is missing `self` parameter and has inconsistent behavior
- Context handling is embedded in the agent rather than separated

**Recommendation:**
```python
class OllamaAgent(IAgent):
    def __init__(self, model: str = "llama3.1", context_manager: ContextManager = None):
        self._client = Client()
        self._model = model
        self._context_manager = context_manager or ContextManager()

    async def chat(self, message: str) -> AsyncIterator[str]:
        """Stream chat response using managed context."""
        context = self._context_manager.get_context()
        messages = self._build_messages(message, context)

        response_content = []
        async for chunk in self._stream_chat(messages):
            response_content.append(chunk)
            yield chunk

        self._context_manager.add_chat_turn("user", message)
        self._context_manager.add_chat_turn("assistant", "".join(response_content))
```

### E. Error Handling in MCP Commands

**Problem:** In `ai_shell/commands/mcp_commands.py:68`, error handling is too generic:
```python
return "Error: Invalid arguments. Usage: \\summarize [text|file] [-f FILE] [-i INSTRUCTIONS]"
```

**Recommendation:** Provide specific error messages based on the actual parsing error.

### F. Packaging Configuration

**Problem:** `pyproject.toml:49` manually lists packages:
```toml
packages = ["ai_shell", "ai_shell.core", "ai_shell.shell", "ai_shell.mocks", "ai_shell.utils"]
```

**Recommendation:** Use automatic discovery:
```toml
[tool.setuptools.packages.find]
where = ["."]
include = ["ai_shell*"]
exclude = ["tests*", "scripts*"]
```

This is less error-prone when adding new subpackages.

## Summary of Actions

### High Priority
- [x] Add missing dependencies (`ollama`, `mcp`, `pydantic`) to pyproject.toml
- [x] Delete unused files: `command_base.py`, `command_helpers.py`
- [x] Fix typo: `diconnect` → `disconnect` in `mcp.py`
- [x] Move test files to proper `tests/` subdirectories

### Medium Priority
- [ ] Create `ContextManager` class to centralize context handling
- [ ] Fix MCP connection management (avoid reconnecting on every call)
- [ ] Fix `generate()` method in `OllamaAgent` (missing `self` parameter)
- [ ] Remove or complete `file_commands.py` (currently commented out)

### Lower Priority
- [ ] Use automatic package discovery in setuptools
- [ ] Clean up demo scripts after development stabilizes
- [ ] Either populate or remove the empty `ai_shell/utils/` package

---

**Overall Assessment:** The codebase is in good shape overall - these are mostly cleanup items and architectural improvements that will make the code more maintainable going forward.
