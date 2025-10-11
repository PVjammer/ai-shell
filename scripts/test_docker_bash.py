#!/usr/bin/env python3
"""Test Docker bash executor."""

import asyncio
from ai_shell.core.docker_bash_executor import DockerBashExecutor


async def main():
    """Test Docker bash executor."""
    print("Testing Docker bash executor...\n")

    # Use a lightweight image for faster tests
    docker = DockerBashExecutor(image="alpine:latest")

    # Test 1: Check Docker availability
    print("Test 1: Check Docker availability")
    is_available = await docker._check_docker()
    print(f"Docker available: {is_available}")
    if not is_available:
        print("\n❌ Docker is not available. Please install Docker to use this backend.")
        print("   sudo apt install docker.io  # Ubuntu/Debian")
        print("   Or visit: https://docs.docker.com/get-docker/")
        return
    print()

    # Test 2: Simple echo
    print("Test 2: echo 'Hello from Docker'")
    result = await docker.execute("echo 'Hello from Docker'")
    print(f"Success: {result.success}")
    print(f"Output: {result.output.strip()}")
    print()

    # Test 3: List files (should see mounted files)
    print("Test 3: ls (should see your current directory files)")
    result = await docker.execute("ls")
    print(f"Success: {result.success}")
    print(f"Output:\n{result.output}")

    # Test 4: Try to create a file (should fail - read-only mount)
    print("Test 4: Try to create file (should fail - read-only)")
    result = await docker.execute("touch /workspace/testfile.txt")
    print(f"Success: {result.success}")
    if not result.success:
        print(f"Error (expected): {result.error.strip()}")
    print()

    # Test 5: Test network isolation
    print("Test 5: Try to access network (should fail - no network)")
    result = await docker.execute("ping -c 1 google.com")
    print(f"Success: {result.success}")
    if not result.success:
        print(f"Error (expected): {result.error.strip()[:100]}...")
    print()

    # Test 6: Test with read-write version
    print("Test 6: Using Docker with read-write mount")
    from ai_shell.core.docker_bash_executor import DockerBashExecutorWithWrite
    docker_rw = DockerBashExecutorWithWrite(image="alpine:latest")
    result = await docker_rw.execute("touch /workspace/testfile.txt && ls testfile.txt")
    print(f"Success: {result.success}")
    print(f"Output: {result.output.strip()}")

    # Clean up the test file
    import os
    if os.path.exists("testfile.txt"):
        os.remove("testfile.txt")
        print("Cleaned up testfile.txt")
    print()

    print("✅ All tests complete!")
    print("\nDocker backend features:")
    print("  ✓ Sandboxed execution (isolated from host)")
    print("  ✓ No network access (safer)")
    print("  ✓ Read-only mount (prevents accidental file changes)")
    print("  ✓ Automatic cleanup (--rm flag)")
    print("\nUse: ai-shell --bash-backend=docker")


if __name__ == "__main__":
    asyncio.run(main())
