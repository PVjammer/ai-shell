"""Performance tests for shell initialization."""

import time
from ai_shell.shell.completer import ShellCompleter


def test_completer_fast_initialization():
    """Test that completer initializes quickly (under 1 second)."""
    start = time.time()
    completer = ShellCompleter()
    elapsed = time.time() - start

    # Should be very fast (under 1 second)
    assert elapsed < 1.0, f"Initialization took {elapsed:.2f}s, expected < 1.0s"

    # Should not have loaded PATH executables yet
    assert not completer._path_executables_loaded


def test_lazy_load_performance():
    """Test that lazy loading of PATH executables is reasonably fast."""
    completer = ShellCompleter()

    start = time.time()
    completer._load_path_executables()
    elapsed = time.time() - start

    # Should be reasonably fast (under 1 second for first 5 PATH dirs)
    assert elapsed < 1.0, f"Lazy load took {elapsed:.2f}s, expected < 1.0s"

    # Should have loaded some executables
    assert len(completer._path_executables) > 0
    assert completer._path_executables_loaded


def test_lazy_load_only_once():
    """Test that PATH executables are only loaded once."""
    completer = ShellCompleter()

    # First load
    completer._load_path_executables()
    first_count = len(completer._path_executables)

    # Second load should be a no-op
    completer._load_path_executables()
    second_count = len(completer._path_executables)

    assert first_count == second_count
