# Streaming LLM Responses & Async Pipeline Execution - Research Report

**Research Date**: 2025-10-09
**Focus**: Modern patterns for streaming LLM responses, async pipeline execution, backpressure handling, error propagation, cancellation, and progress indication.

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Streaming Architectures](#streaming-architectures)
3. [Async Pipeline Patterns](#async-pipeline-patterns)
4. [Backpressure Handling](#backpressure-handling)
5. [Error Propagation](#error-propagation)
6. [Cancellation & Cleanup](#cancellation--cleanup)
7. [Progress Indication & Terminal UI](#progress-indication--terminal-ui)
8. [Implementation Recommendations](#implementation-recommendations)
9. [Code Examples & Patterns](#code-examples--patterns)
10. [References](#references)

---

## Executive Summary

### Key Findings

1. **Server-Sent Events (SSE)** remains the dominant streaming protocol for LLM responses in 2025, preferred over WebSockets due to simplicity, HTTP compatibility, and automatic reconnection.

2. **Python's asyncio** with async generators (PEP 525) provides the foundation for modern streaming pipelines, with structured concurrency via `TaskGroup` (Python 3.11+) enabling safer task management.

3. **Backpressure** is best handled through bounded `asyncio.Queue` with `maxsize` parameter, creating natural flow control between pipeline stages.

4. **Rich** and **Textual** libraries are the state-of-the-art for terminal UI with streaming output, providing flicker-free updates and "latency theater" for better UX.

5. **Mixed sync/async** operations require `loop.run_in_executor()` or `asyncio.to_thread()` to prevent blocking the event loop.

---

## Streaming Architectures

### Server-Sent Events (SSE)

SSE has emerged as the clear winner for LLM streaming in 2025:

**Why SSE Wins:**
- Lightweight and stateless
- Built on standard HTTP (easier to scale)
- Automatic reconnection built-in
- One-way communication (perfect for LLM responses)
- 90% of WebSocket benefits with 10% of the complexity

**2025 Best Practices:**

1. **Heartbeats**: Send heartbeat every few seconds to keep connection alive and detect network issues
2. **Event IDs**: Include sequence ID in event payload to ensure correct ordering
3. **Retry Mechanisms**: Implement exponential backoff for connection failures
4. **Error Events**: Send error events within stream using `error` field or `X-SSE-Error` header
5. **Handle Fragmentation**: Always anticipate responses in multiple fragments

**SSE Event Flow (Anthropic/OpenAI Pattern):**
```
message_start → content_block_start → content_block_delta (multiple) →
content_block_stop → message_delta → message_stop
```

### Async Generators in Python

Python's async generators (PEP 525) are 2x faster than equivalent async iterators and form the basis for streaming pipelines.

**Core Pattern:**
```python
async def stream_generator():
    async for item in source:
        processed = await process(item)
        yield processed
```

**Advantages:**
- Native Python support (3.6+)
- Composable and chainable
- Efficient memory usage
- Integrates with `async for` loops

### LLM SDK Streaming Patterns

**Anthropic SDK (Python):**
```python
# High-level streaming (recommended)
async with client.messages.stream(...) as stream:
    async for text in stream.text_stream:
        print(text, end="", flush=True)
    message = await stream.get_final_message()

# Low-level streaming (less memory)
stream = client.messages.create(stream=True, ...)
async for event in stream:
    if event.type == "content_block_delta":
        print(event.delta.text, end="", flush=True)
```

**Key Differences:**
- High-level: Accumulates message, provides helpers, uses more memory
- Low-level: Raw event iteration, minimal memory overhead

**OpenAI SDK:**
Similar pattern with usage data in final chunk (vs Anthropic providing partial usage early)

---

## Async Pipeline Patterns

### Composing Async Operations

**Three Main Approaches:**

#### 1. Manual Async Generator Chaining
```python
async def pipeline():
    async for item in stage1():
        processed = await stage2(item)
        result = await stage3(processed)
        yield result
```

#### 2. Queue-Based Pipelines
```python
async def stage1(output_queue: asyncio.Queue):
    async for item in source():
        await output_queue.put(item)

async def stage2(input_queue: asyncio.Queue, output_queue: asyncio.Queue):
    while True:
        item = await input_queue.get()
        result = await process(item)
        await output_queue.put(result)
```

#### 3. Operator-Based Composition (aiostream)
```python
from aiostream import stream, pipe

xs = stream.count(interval=0.2)
ys = xs | pipe.map(lambda x: x**2) | pipe.filter(lambda x: x > 10)

async for value in ys:
    print(value)
```

### Structured Concurrency with TaskGroup

Python 3.11+ introduces `TaskGroup` for safer concurrent task management:

**Key Benefits:**
- Automatic task lifecycle management
- Exception propagation (cancels remaining tasks on error)
- No explicit `join()` or `gather()` needed
- Context manager handles cleanup

**Pattern:**
```python
async def run_pipeline():
    async with asyncio.TaskGroup() as tg:
        task1 = tg.create_task(llm_stream())
        task2 = tg.create_task(bash_executor())
        task3 = tg.create_task(tool_runner())
    # All tasks complete or one fails (others cancelled)
```

**Error Handling:**
```python
try:
    async with asyncio.TaskGroup() as tg:
        # Tasks here
        pass
except* ValueError as eg:  # Note: except* for exception groups
    for exc in eg.exceptions:
        handle_error(exc)
```

### aiostream Library

Provides RxJS-like operators for async iteration:

**Features:**
- Pipe operators using `|`
- Stream slicing: `stream[1:10:2]`
- Composition: `merge`, `zip`, `combine`
- Transformations: `map`, `filter`, `accumulate`
- Implicit backpressure via await

**Installation:**
```bash
pip install aiostream
```

**Example:**
```python
from aiostream import stream, pipe

# Creation
xs = stream.iterate([1, 2, 3, 4, 5])

# Transformation
ys = xs | pipe.map(lambda x: x**2)

# Combination
zs = stream.merge(xs, ys)

# Consumption
async for value in zs[:10]:  # Slice syntax
    print(value)
```

---

## Backpressure Handling

### The Problem

Different pipeline stages operate at different speeds:
- LLM generation: Variable speed, token-by-token
- Bash execution: Blocks until completion
- Tool calls: Network-dependent timing

Without backpressure, fast producers overwhelm slow consumers, causing memory bloat.

### Solution: Bounded Queues

**asyncio.Queue with maxsize:**
```python
queue = asyncio.Queue(maxsize=10)  # Maximum 10 items buffered

# Producer blocks when queue is full
await queue.put(item)  # Waits if queue at maxsize

# Consumer blocks when queue is empty
item = await queue.get()  # Waits if queue empty
```

**How It Works:**
1. Queue fills to maxsize
2. Producer's `put()` blocks (awaits)
3. Consumer processes items
4. Producer resumes as space becomes available

**Implicit Backpressure:**
No explicit backpressure handling needed - Python's `await` mechanism provides natural flow control.

### Best Practices

1. **Choose appropriate queue size:**
   - Too small: Excessive context switching
   - Too large: Memory bloat
   - Typical: 5-50 items depending on item size

2. **Monitor queue depth:**
   ```python
   if queue.qsize() > maxsize * 0.8:
       logger.warning("Queue approaching capacity")
   ```

3. **Use bounded queues everywhere:**
   Never use unbounded queues in production pipelines

4. **Consider sentinel values:**
   ```python
   SENTINEL = object()

   async def producer(queue):
       async for item in source():
           await queue.put(item)
       await queue.put(SENTINEL)  # Signal completion

   async def consumer(queue):
       while True:
           item = await queue.get()
           if item is SENTINEL:
               break
           await process(item)
   ```

### Alternative: aioreactive

For reactive programming enthusiasts:
```bash
pip install aioreactive
```

Features implicit synchronous backpressure - producers await until consumers process events.

---

## Error Propagation

### Principles

1. **Be specific**: Catch specific exceptions, let unexpected ones propagate
2. **Preserve context**: Use `raise ... from` to maintain causality chain
3. **Log with tracebacks**: Use `logging.exception()` to preserve stack traces
4. **Top-level handlers**: Always have top-level exception handling

### Async Exception Patterns

#### Basic Try-Except in Async
```python
async def safe_operation():
    try:
        result = await risky_operation()
        return result
    except ValueError as e:
        logger.exception("Value error in operation")
        raise  # Re-raise to propagate
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise OperationError("Operation failed") from e
```

#### TaskGroup Exception Handling
```python
async def run_tasks():
    try:
        async with asyncio.TaskGroup() as tg:
            tg.create_task(task1())
            tg.create_task(task2())
            tg.create_task(task3())
    except* TimeoutError as eg:
        # Handle timeout errors from any task
        for exc in eg.exceptions:
            logger.error(f"Timeout: {exc}")
    except* ValueError as eg:
        # Handle value errors
        for exc in eg.exceptions:
            logger.error(f"Value error: {exc}")
```

**Note:** `except*` (PEP 654) is for exception groups - use with TaskGroup

#### asyncio.gather Error Handling
```python
# Default: First exception propagates immediately
results = await asyncio.gather(
    task1(),
    task2(),
    task3()
)

# Alternative: Collect all results including exceptions
results = await asyncio.gather(
    task1(),
    task2(),
    task3(),
    return_exceptions=True
)

for result in results:
    if isinstance(result, Exception):
        handle_error(result)
    else:
        process_result(result)
```

### Pipeline Error Strategies

#### Strategy 1: Fail Fast
```python
async def pipeline():
    try:
        async for item in source():
            result = await process(item)
            yield result
    except ProcessingError:
        logger.exception("Pipeline failed")
        raise  # Stop entire pipeline
```

#### Strategy 2: Error Collection
```python
async def pipeline():
    errors = []
    async for item in source():
        try:
            result = await process(item)
            yield result
        except ProcessingError as e:
            errors.append((item, e))
            logger.warning(f"Item {item} failed: {e}")
            continue  # Process remaining items

    if errors:
        raise PipelineError(f"{len(errors)} items failed", errors)
```

#### Strategy 3: Error Channel
```python
async def pipeline(error_queue: asyncio.Queue):
    async for item in source():
        try:
            result = await process(item)
            yield result
        except ProcessingError as e:
            await error_queue.put((item, e))
            # Continue processing
```

### LangChain Streaming Error Pattern

LangChain's `astream_events()` provides structured error handling:
```python
async for event in agent.astream_events(...):
    if event["event"] == "on_tool_error":
        handle_tool_error(event["data"])
    elif event["event"] == "on_chain_error":
        handle_chain_error(event["data"])
```

---

## Cancellation & Cleanup

### Core Principles

1. **Always expect cancellation**: Any async operation can be cancelled
2. **Re-raise CancelledError**: Never swallow `asyncio.CancelledError`
3. **Use try-finally for cleanup**: Guaranteed execution of cleanup code
4. **Shield critical operations**: Protect cleanup code from cancellation

### Basic Cancellation Pattern

```python
async def cancellable_task():
    try:
        await long_running_operation()
    except asyncio.CancelledError:
        logger.info("Task was cancelled")
        # Perform cleanup
        await cleanup()
        raise  # MUST re-raise
    finally:
        # This runs even if cancelled
        release_resources()
```

### Task Cancellation Workflow

```python
# Create task
task = asyncio.create_task(worker())

# Cancel task
task.cancel()

# Wait for cancellation to complete
try:
    await task
except asyncio.CancelledError:
    logger.info("Task cancelled successfully")
```

**Important:** After `cancel()`, you must `await` the task to allow cleanup to run.

### Timeout with Cleanup

```python
async def operation_with_timeout():
    try:
        async with asyncio.timeout(10.0):  # Python 3.11+
            result = await slow_operation()
            return result
    except TimeoutError:
        logger.warning("Operation timed out")
        await cleanup()
        raise
```

**Note:** `asyncio.timeout()` transforms `CancelledError` to `TimeoutError`

### Shielded Cleanup (Critical Operations)

When cleanup requires async operations that must complete:

#### Using asyncio.shield
```python
async def task_with_cleanup():
    try:
        await main_operation()
    finally:
        # Shield cleanup from cancellation
        await asyncio.shield(async_cleanup())
```

**Caveat:** `asyncio.shield()` has limitations - doesn't fully prevent cancellation

#### Using AnyIO CancelScope (Recommended)
```python
from anyio import CancelScope

async def task_with_cleanup():
    try:
        await main_operation()
    finally:
        # Shield cleanup from cancellation
        with CancelScope(shield=True):
            await async_cleanup()
```

**Advantages:**
- More reliable shielding than asyncio
- Prevents cancellation propagation to child scope
- Safer and more predictable behavior

### Signal Handling for Graceful Shutdown

#### Basic Pattern
```python
import asyncio
import signal

async def main():
    loop = asyncio.get_running_loop()

    def signal_handler():
        logger.info("Received shutdown signal")
        for task in asyncio.all_tasks():
            task.cancel()

    # Register signal handlers
    loop.add_signal_handler(signal.SIGINT, signal_handler)
    loop.add_signal_handler(signal.SIGTERM, signal_handler)

    try:
        await run_application()
    except asyncio.CancelledError:
        logger.info("Application cancelled")
        await cleanup()
```

#### Advanced Pattern with Graceful Shutdown
```python
import asyncio
import signal

class GracefulShutdown:
    def __init__(self):
        self.shutdown_event = asyncio.Event()
        self.tasks = []

    def register_task(self, task):
        self.tasks.append(task)

    async def shutdown(self):
        logger.info("Shutting down gracefully...")
        self.shutdown_event.set()

        # Cancel all tasks
        for task in self.tasks:
            task.cancel()

        # Wait for tasks to finish cleanup
        await asyncio.gather(*self.tasks, return_exceptions=True)

        logger.info("Shutdown complete")

async def main():
    shutdown = GracefulShutdown()
    loop = asyncio.get_running_loop()

    loop.add_signal_handler(
        signal.SIGINT,
        lambda: asyncio.create_task(shutdown.shutdown())
    )
    loop.add_signal_handler(
        signal.SIGTERM,
        lambda: asyncio.create_task(shutdown.shutdown())
    )

    # Register tasks
    task1 = asyncio.create_task(worker1())
    task2 = asyncio.create_task(worker2())
    shutdown.register_task(task1)
    shutdown.register_task(task2)

    # Wait for shutdown signal
    await shutdown.shutdown_event.wait()
```

### Best Practices

1. **Always re-raise CancelledError**
   ```python
   except asyncio.CancelledError:
       await cleanup()
       raise  # Critical!
   ```

2. **Use try-finally for guaranteed cleanup**
   ```python
   try:
       await operation()
   finally:
       release_resources()  # Always runs
   ```

3. **Shield critical cleanup**
   ```python
   finally:
       with CancelScope(shield=True):
           await async_cleanup()
   ```

4. **Timeout context managers**
   ```python
   async with asyncio.timeout(10.0):
       await operation()
   ```

5. **Avoid swallowing exceptions in async generators**
   - PEP 789 addresses this issue
   - Async generators can hide CancelledError if not careful

---

## Progress Indication & Terminal UI

### Libraries Overview

#### Rich
- Beautiful terminal output library
- Progress bars, tables, syntax highlighting
- Live display with automatic refresh
- Built-in by Textual

#### Textual
- Full TUI framework built on Rich
- Reactive components
- CSS-like styling
- Web browser support

### Rich Live Display

**Basic Pattern:**
```python
from rich.live import Live
from rich.table import Table
import time

table = Table()
table.add_column("Status")
table.add_column("Progress")

with Live(table, refresh_per_second=4) as live:
    for i in range(100):
        table.add_row(f"Step {i}", f"{i}%")
        time.sleep(0.1)
```

**Dynamic Updates:**
```python
from rich.live import Live
from rich.markdown import Markdown

with Live(auto_refresh=False) as live:
    markdown_content = ""

    async for chunk in llm_stream():
        markdown_content += chunk
        live.update(Markdown(markdown_content), refresh=True)
```

### Rich Progress Bars

**Multiple Progress Bars:**
```python
from rich.progress import Progress

with Progress() as progress:
    task1 = progress.add_task("[red]LLM Generation...", total=100)
    task2 = progress.add_task("[green]Processing...", total=100)
    task3 = progress.add_task("[cyan]Validation...", total=100)

    while not progress.finished:
        progress.update(task1, advance=0.5)
        progress.update(task2, advance=0.3)
        progress.update(task3, advance=0.2)
        time.sleep(0.02)
```

**Custom Columns:**
```python
from rich.progress import (
    Progress,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
    TimeRemainingColumn,
    SpinnerColumn
)

progress = Progress(
    SpinnerColumn(),
    TextColumn("[progress.description]{task.description}"),
    BarColumn(),
    TaskProgressColumn(),
    TimeRemainingColumn(),
)

with progress:
    task = progress.add_task("Processing...", total=100)
    for i in range(100):
        progress.update(task, advance=1)
```

### Streaming Text with "Latency Theater"

**Pattern for LLM Streaming:**
```python
from rich.console import Console
from rich.markdown import Markdown

console = Console()

async def stream_llm_response():
    buffer = ""

    async for chunk in llm.stream():
        buffer += chunk
        # Update in place using ANSI escape codes
        console.print(f"\r{buffer}", end="", flush=True)

    console.print()  # Final newline
```

**Using Rich Live for Markdown Streaming:**
```python
from rich.live import Live
from rich.markdown import Markdown

async def stream_markdown_response():
    content = ""

    with Live(Markdown(content), auto_refresh=False) as live:
        async for chunk in llm.stream():
            content += chunk
            live.update(Markdown(content), refresh=True)
```

### Textual for Complex UIs

**Streaming Chat Application:**
```python
from textual.app import App
from textual.widgets import Static
from textual.worker import Worker

class ChatApp(App):
    def compose(self):
        yield Static("", id="chat_output")

    async def on_mount(self):
        output = self.query_one("#chat_output")

        @self.work(exclusive=True)
        async def stream_response():
            content = ""
            async for chunk in llm.stream():
                content += chunk
                output.update(content)

        stream_response()
```

### ANSI Escape Codes

**Core Sequences:**
```python
# Cursor control
CLEAR_LINE = "\033[2K"
MOVE_START = "\033[0G"
MOVE_UP = "\033[1A"

# Colors
RED = "\033[31m"
GREEN = "\033[32m"
RESET = "\033[0m"

# Usage
print(f"{CLEAR_LINE}{MOVE_START}{GREEN}Processing...{RESET}", end="", flush=True)
```

**Flushing Output:**
```python
# Force immediate output
print("text", end="", flush=True)

# Or use sys.stdout
import sys
sys.stdout.write("text")
sys.stdout.flush()
```

**Platform Compatibility:**
```python
# Enable ANSI on Windows 10+
import os
if os.name == 'nt':
    os.system("")  # Enables ANSI escape sequences
```

### UX Best Practices

1. **Latency Theater**: Show progress immediately even if processing hasn't started
2. **Streaming Text**: Display tokens as they arrive, don't wait for completion
3. **Progressive Enhancement**: Show partial results, refine as more data arrives
4. **Clear Status**: Always indicate what's happening (thinking, processing, complete)
5. **Cancellation Feedback**: Immediately show when user cancels
6. **Error Visibility**: Make errors obvious but not disruptive

---

## Implementation Recommendations

### Python Implementation Approach

**Recommended Stack:**
- **Python 3.11+**: For TaskGroup and improved asyncio
- **asyncio**: Core async runtime
- **aiostream**: Optional, for complex operator chains
- **Rich**: Terminal UI and streaming output
- **AnyIO**: Optional, for better cancellation handling

**Architecture:**
```
┌─────────────────────────────────────────────────┐
│              Main Event Loop                     │
│                 (asyncio)                        │
├─────────────────────────────────────────────────┤
│                                                  │
│  ┌──────────────┐    ┌──────────────┐          │
│  │  LLM Stream  │───→│ Output Queue │          │
│  │  (async gen) │    │  (bounded)   │          │
│  └──────────────┘    └──────────────┘          │
│                            │                     │
│                            ↓                     │
│  ┌──────────────┐    ┌──────────────┐          │
│  │  Bash Exec   │───→│ Result Queue │          │
│  │ (in executor)│    │  (bounded)   │          │
│  └──────────────┘    └──────────────┘          │
│                            │                     │
│                            ↓                     │
│  ┌──────────────┐    ┌──────────────┐          │
│  │  Tool Calls  │───→│ Output Queue │          │
│  │  (async)     │    │  (bounded)   │          │
│  └──────────────┘    └──────────────┘          │
│                            │                     │
│                            ↓                     │
│                    ┌──────────────┐             │
│                    │  Rich Live   │             │
│                    │  (terminal)  │             │
│                    └──────────────┘             │
│                                                  │
└─────────────────────────────────────────────────┘
```

### Handling Mixed Sync/Async Operations

**Problem:** Bash execution is synchronous and blocks

**Solution 1: Thread Pool Executor (Recommended)**
```python
import asyncio
import subprocess

async def run_bash_command(cmd: str) -> str:
    loop = asyncio.get_running_loop()

    # Run blocking subprocess in thread pool
    result = await loop.run_in_executor(
        None,  # Use default executor
        subprocess.run,
        cmd,
        True,  # shell=True
        subprocess.PIPE,  # capture_output
        "utf-8"  # text encoding
    )

    return result.stdout
```

**Solution 2: asyncio.to_thread (Python 3.9+)**
```python
async def run_bash_command(cmd: str) -> str:
    def blocking_subprocess():
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True
        )
        return result.stdout

    return await asyncio.to_thread(blocking_subprocess)
```

**Thread Pool Configuration:**
```python
import concurrent.futures

# Custom thread pool for I/O-bound operations
executor = concurrent.futures.ThreadPoolExecutor(
    max_workers=10,  # Adjust based on needs
    thread_name_prefix="bash_executor"
)

async def run_bash(cmd: str) -> str:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(executor, subprocess_wrapper, cmd)
```

**Caution:** Default thread pool is limited (32 threads or CPU count + 4, whichever is lower). For many concurrent I/O operations, create a custom executor.

### Best Practices for Terminal Output with Streaming

#### 1. Use Rich Live for Complex Output
```python
from rich.live import Live
from rich.panel import Panel
from rich.layout import Layout

async def stream_pipeline_output():
    layout = Layout()
    layout.split_column(
        Layout(name="llm"),
        Layout(name="bash"),
        Layout(name="status")
    )

    with Live(layout, refresh_per_second=4) as live:
        async with asyncio.TaskGroup() as tg:
            tg.create_task(stream_llm(layout["llm"]))
            tg.create_task(stream_bash(layout["bash"]))
            tg.create_task(update_status(layout["status"]))
```

#### 2. Buffer Partial Tokens
```python
async def stream_with_buffering():
    buffer = []

    async for chunk in llm.stream():
        buffer.append(chunk)

        # Flush every N chunks or on newline
        if len(buffer) >= 10 or '\n' in chunk:
            text = ''.join(buffer)
            console.print(text, end="", flush=True)
            buffer.clear()

    # Flush remaining
    if buffer:
        console.print(''.join(buffer), flush=True)
```

#### 3. Handle Progress for Multiple Stages
```python
from rich.progress import Progress

async def multi_stage_pipeline():
    with Progress() as progress:
        llm_task = progress.add_task("[cyan]LLM Generation", total=None)
        bash_task = progress.add_task("[yellow]Bash Execution", total=None)
        tool_task = progress.add_task("[green]Tool Calls", total=None)

        async with asyncio.TaskGroup() as tg:
            tg.create_task(llm_stage(progress, llm_task))
            tg.create_task(bash_stage(progress, bash_task))
            tg.create_task(tool_stage(progress, tool_task))
```

#### 4. Separate Channels for Different Output Types
```python
from rich.console import Console

# Separate consoles for different streams
stdout_console = Console(file=sys.stdout)
stderr_console = Console(file=sys.stderr, style="red")

async def stream_output():
    async for event in pipeline():
        if event.type == "output":
            stdout_console.print(event.text)
        elif event.type == "error":
            stderr_console.print(event.text)
        elif event.type == "progress":
            update_progress(event.data)
```

### Cancellation and Cleanup Patterns

#### Pattern 1: Context Manager for Resources
```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def pipeline_context():
    # Setup
    llm_client = await create_llm_client()
    db_conn = await create_db_connection()

    try:
        yield (llm_client, db_conn)
    finally:
        # Cleanup (even if cancelled)
        await llm_client.close()
        await db_conn.close()

async def run_pipeline():
    async with pipeline_context() as (llm, db):
        async for result in process_stream(llm, db):
            yield result
```

#### Pattern 2: TaskGroup with Signal Handling
```python
import signal
import asyncio

class Pipeline:
    def __init__(self):
        self.shutdown_event = asyncio.Event()
        self.tasks = []

    async def setup_signals(self):
        loop = asyncio.get_running_loop()

        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(
                sig,
                lambda: asyncio.create_task(self.shutdown())
            )

    async def shutdown(self):
        print("\nShutting down gracefully...")
        self.shutdown_event.set()

        # Cancel all tasks
        for task in self.tasks:
            task.cancel()

        # Wait with timeout
        try:
            async with asyncio.timeout(5.0):
                await asyncio.gather(*self.tasks, return_exceptions=True)
        except TimeoutError:
            print("Timeout during shutdown")

    async def run(self):
        await self.setup_signals()

        try:
            async with asyncio.TaskGroup() as tg:
                self.tasks.append(tg.create_task(self.llm_stream()))
                self.tasks.append(tg.create_task(self.bash_executor()))
                self.tasks.append(tg.create_task(self.tool_runner()))
        except* asyncio.CancelledError:
            print("Pipeline cancelled")
```

#### Pattern 3: Error Queue for Non-Fatal Errors
```python
async def pipeline_with_error_handling():
    error_queue = asyncio.Queue()
    result_queue = asyncio.Queue(maxsize=10)

    async def error_monitor():
        while True:
            error = await error_queue.get()
            logger.error(f"Pipeline error: {error}")
            # Could send to monitoring service, etc.

    async with asyncio.TaskGroup() as tg:
        tg.create_task(error_monitor())
        tg.create_task(processor(result_queue, error_queue))
```

### Complete Example: Streaming LLM with Tool Execution

```python
import asyncio
from typing import AsyncIterator
from dataclasses import dataclass
from rich.live import Live
from rich.console import Console
from rich.markdown import Markdown

@dataclass
class StreamEvent:
    type: str  # "text", "tool_call", "tool_result", "error"
    data: str
    metadata: dict = None

class StreamingPipeline:
    def __init__(self):
        self.console = Console()
        self.shutdown_event = asyncio.Event()

    async def llm_stream(self) -> AsyncIterator[StreamEvent]:
        """Stream LLM responses"""
        async for chunk in llm_client.stream(...):
            if self.shutdown_event.is_set():
                break

            if chunk.type == "text":
                yield StreamEvent("text", chunk.text)
            elif chunk.type == "tool_use":
                yield StreamEvent("tool_call", chunk.name, chunk.input)

    async def execute_tool(self, name: str, args: dict) -> str:
        """Execute tool in thread pool"""
        if name == "bash":
            return await asyncio.to_thread(
                self._run_bash,
                args["command"]
            )
        else:
            # Other tools...
            pass

    def _run_bash(self, command: str) -> str:
        """Blocking bash execution"""
        import subprocess
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.stdout

    async def process_stream(self) -> AsyncIterator[str]:
        """Main pipeline orchestration"""
        markdown_content = ""

        try:
            async for event in self.llm_stream():
                if event.type == "text":
                    markdown_content += event.data
                    yield markdown_content

                elif event.type == "tool_call":
                    # Execute tool
                    try:
                        result = await self.execute_tool(
                            event.data,
                            event.metadata
                        )
                        markdown_content += f"\n\n```\n{result}\n```\n\n"
                        yield markdown_content
                    except Exception as e:
                        error_msg = f"\n\n**Error**: {e}\n\n"
                        markdown_content += error_msg
                        yield markdown_content

        except asyncio.CancelledError:
            markdown_content += "\n\n*[Cancelled]*\n"
            yield markdown_content
            raise

    async def run(self):
        """Run pipeline with live display"""
        with Live(Markdown(""), auto_refresh=False) as live:
            try:
                async for content in self.process_stream():
                    live.update(Markdown(content), refresh=True)
            except KeyboardInterrupt:
                self.shutdown_event.set()
                live.update(
                    Markdown(content + "\n\n*[Interrupted]*"),
                    refresh=True
                )

async def main():
    pipeline = StreamingPipeline()

    # Setup signal handlers
    loop = asyncio.get_running_loop()
    loop.add_signal_handler(
        signal.SIGINT,
        lambda: pipeline.shutdown_event.set()
    )

    await pipeline.run()

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Code Examples & Patterns

### Example 1: Basic Async Generator Pipeline

```python
async def source() -> AsyncIterator[int]:
    """Data source"""
    for i in range(100):
        await asyncio.sleep(0.01)
        yield i

async def transform(items: AsyncIterator[int]) -> AsyncIterator[int]:
    """Transform stage"""
    async for item in items:
        result = await asyncio.sleep(0.01, item * 2)
        yield result

async def sink(items: AsyncIterator[int]):
    """Output stage"""
    async for item in items:
        print(item)

# Run pipeline
await sink(transform(source()))
```

### Example 2: Queue-Based Pipeline with Backpressure

```python
async def producer(queue: asyncio.Queue):
    """Produce items with backpressure"""
    for i in range(100):
        item = await fetch_data(i)
        await queue.put(item)  # Blocks if queue full
    await queue.put(None)  # Sentinel

async def processor(in_queue: asyncio.Queue, out_queue: asyncio.Queue):
    """Process items"""
    while True:
        item = await in_queue.get()
        if item is None:
            await out_queue.put(None)
            break

        result = await process(item)
        await out_queue.put(result)

async def consumer(queue: asyncio.Queue):
    """Consume results"""
    while True:
        item = await queue.get()
        if item is None:
            break
        print(item)

# Run pipeline
async def main():
    q1 = asyncio.Queue(maxsize=10)
    q2 = asyncio.Queue(maxsize=10)

    async with asyncio.TaskGroup() as tg:
        tg.create_task(producer(q1))
        tg.create_task(processor(q1, q2))
        tg.create_task(consumer(q2))
```

### Example 3: Error Handling with Exception Groups

```python
async def task_with_error_handling():
    async def may_fail(n: int):
        await asyncio.sleep(0.1)
        if n % 3 == 0:
            raise ValueError(f"Task {n} failed")
        return n

    try:
        async with asyncio.TaskGroup() as tg:
            tasks = [tg.create_task(may_fail(i)) for i in range(10)]
    except* ValueError as eg:
        print(f"Caught {len(eg.exceptions)} ValueError exceptions")
        for exc in eg.exceptions:
            print(f"  - {exc}")
    except* Exception as eg:
        print(f"Caught {len(eg.exceptions)} other exceptions")
```

### Example 4: Cancellation with Cleanup

```python
@asynccontextmanager
async def managed_resource():
    """Context manager with cleanup"""
    resource = await acquire_resource()
    try:
        yield resource
    finally:
        # Cleanup even if cancelled
        try:
            # Shield cleanup from cancellation
            with CancelScope(shield=True):
                await resource.cleanup()
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")

async def worker():
    async with managed_resource() as resource:
        try:
            while True:
                await resource.do_work()
        except asyncio.CancelledError:
            logger.info("Worker cancelled")
            raise  # Must re-raise
```

### Example 5: Rich Progress with Async Tasks

```python
from rich.progress import Progress
import asyncio

async def download_file(progress, task_id, url):
    """Simulate file download"""
    for i in range(100):
        await asyncio.sleep(0.05)
        progress.update(task_id, advance=1)

async def main():
    with Progress() as progress:
        tasks = []

        urls = [
            "https://example.com/file1.zip",
            "https://example.com/file2.zip",
            "https://example.com/file3.zip",
        ]

        for url in urls:
            task_id = progress.add_task(f"Downloading {url}", total=100)
            tasks.append(download_file(progress, task_id, url))

        await asyncio.gather(*tasks)

asyncio.run(main())
```

### Example 6: Streaming with aiostream

```python
from aiostream import stream, pipe

async def main():
    # Create source stream
    xs = stream.range(10)

    # Transform with operators
    ys = xs | pipe.map(lambda x: x**2)
    zs = ys | pipe.filter(lambda x: x > 10)

    # Multiple stages
    result = zs | pipe.accumulate(lambda a, b: a + b, initializer=0)

    # Consume
    async for value in result:
        print(value)
```

### Example 7: LangChain-Style Event Streaming

```python
from typing import Literal, TypedDict

class StreamEvent(TypedDict):
    event: Literal["on_llm_start", "on_llm_stream", "on_tool_start", "on_tool_end"]
    data: dict

async def astream_events() -> AsyncIterator[StreamEvent]:
    """LangChain-style event streaming"""
    yield {"event": "on_llm_start", "data": {"prompt": "..."}}

    async for chunk in llm.stream():
        yield {"event": "on_llm_stream", "data": {"chunk": chunk}}

    yield {"event": "on_tool_start", "data": {"tool": "bash", "input": "ls"}}

    result = await execute_bash("ls")

    yield {"event": "on_tool_end", "data": {"result": result}}

async def consume_events():
    async for event in astream_events():
        if event["event"] == "on_llm_stream":
            print(event["data"]["chunk"], end="", flush=True)
        elif event["event"] == "on_tool_start":
            print(f"\nExecuting {event['data']['tool']}...")
        elif event["event"] == "on_tool_end":
            print(f"Result: {event['data']['result']}")
```

---

## References

### Official Documentation
- [Python asyncio](https://docs.python.org/3/library/asyncio.html)
- [PEP 525 - Asynchronous Generators](https://peps.python.org/pep-0525/)
- [PEP 654 - Exception Groups](https://peps.python.org/pep-0654/)
- [PEP 789 - Async Generator Cancellation](https://peps.python.org/pep-0789/)
- [Rich Documentation](https://rich.readthedocs.io/)
- [Textual Documentation](https://textual.textualize.io/)
- [AnyIO Documentation](https://anyio.readthedocs.io/)
- [aiostream Documentation](https://aiostream.readthedocs.io/)

### LLM SDK Documentation
- [Anthropic Python SDK](https://github.com/anthropics/anthropic-sdk-python)
- [Anthropic Streaming Guide](https://docs.claude.com/en/docs/build-with-claude/streaming)
- [OpenAI Python SDK](https://github.com/openai/openai-python)
- [LangChain Streaming](https://python.langchain.com/docs/concepts/streaming/)

### Articles & Tutorials
- [SSE for LLM Responses (Upstash)](https://upstash.com/blog/sse-streaming-llm-responses)
- [Asyncio Task Cancellation Best Practices](https://superfastpython.com/asyncio-task-cancellation-best-practices/)
- [Graceful Shutdowns with asyncio (roguelynn)](https://www.roguelynn.com/words/asyncio-graceful-shutdowns/)
- [Python TaskGroup Guide (Bruce Eckel)](https://bruceeckel.substack.com/p/python-311-asynciotaskgroup)
- [Reactive Streams in Python (Medium)](https://pierrepaci.medium.com/reactive-stream-in-pure-python-a01b41df934)
- [Async Pressure Article (Armin Ronacher)](https://lucumr.pocoo.org/2020/1/1/async-pressure/)

### Key Libraries
```bash
# Core async streaming
pip install aiostream aioreactive

# Terminal UI
pip install rich textual

# Better cancellation handling
pip install anyio

# HTTP streaming
pip install httpx aiohttp

# LLM SDKs
pip install anthropic openai langchain
```

### Design Patterns Summary

| Pattern | Use Case | Complexity |
|---------|----------|------------|
| Async Generators | Simple linear pipelines | Low |
| Queue-Based | Multi-stage with backpressure | Medium |
| aiostream Operators | Complex transformations | Medium |
| TaskGroup | Concurrent tasks with error handling | Low-Medium |
| Event Streaming | LangChain-style composability | Medium-High |
| Rich Live | Terminal UI with updates | Low |
| Textual | Full TUI applications | High |

### Performance Considerations

| Approach | Memory Usage | CPU Usage | Complexity |
|----------|--------------|-----------|------------|
| Async Generators | Very Low | Low | Low |
| Bounded Queues | Low-Medium | Low | Medium |
| Unbounded Queues | High (danger!) | Low | Low |
| Thread Pool | Medium | Medium | Medium |
| Process Pool | High | High | High |
| Rich Live | Low | Low-Medium | Low |

---

## Conclusion

Modern Python provides excellent primitives for streaming LLM responses and building async pipelines:

1. **Use asyncio with TaskGroup** for structured concurrency
2. **Implement backpressure** via bounded queues
3. **Handle errors explicitly** with proper exception propagation
4. **Always plan for cancellation** with try-finally and shielded cleanup
5. **Use Rich/Textual** for professional terminal UIs
6. **Run blocking operations in thread pool** to avoid blocking the event loop
7. **Follow SSE patterns** for LLM streaming compatibility

The combination of these patterns creates robust, responsive, and maintainable streaming applications.
