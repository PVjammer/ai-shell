# Docker Backend for ai-shell 🐳

## Overview

The Docker backend provides **sandboxed execution** of bash commands in isolated containers. This is much safer than running commands directly on your host system, especially when testing AI-generated commands.

## ✅ Confirmed Working

Docker backend is **fully functional** and tested. See demo output below.

## Quick Start

### Basic Usage (Read-Only)

```bash
# Use Docker with read-only mount (safest)
ai-shell --bash-backend=docker

# Now your commands run in a sandboxed container:
ai> !ls              # Shows files (read-only)
ai> !whoami          # Shows "root" (inside container)
ai> !touch test.txt  # FAILS - read-only filesystem
```

### Read-Write Usage

```bash
# Use Docker with read-write mount (less safe but more functional)
ai-shell --bash-backend=docker-rw

ai> !echo "test" > test.txt  # Works!
```

### Custom Docker Image

```bash
# Use a specific Docker image
ai-shell --bash-backend=docker --docker-image=python:3.11

# Now you have Python available:
ai> !python --version
```

## Backend Options

| Backend | Description | Safety | Use Case |
|---------|-------------|--------|----------|
| `native` | Direct execution on host | ⚠️ Low | When you trust all commands |
| `docker` | Sandboxed, read-only mount | ✅ High | Testing AI commands safely |
| `docker-rw` | Sandboxed, read-write mount | ⚙️ Medium | When you need file modifications |
| `mock` | Simulated output | 🔒 Highest | Testing shell itself |

## Security Features

### 1. **Isolated Execution**
Commands run in a separate container, isolated from your host system.

```bash
ai> !rm -rf /  # Would only affect the container, not your host!
```

### 2. **No Network Access**
Containers run with `--network none`, preventing network access.

```bash
ai> !curl google.com  # Fails - no network
ai> !ping 8.8.8.8     # Fails - no network
```

### 3. **Read-Only Filesystem** (docker mode)
Your files are mounted read-only, preventing modifications.

```bash
ai> !touch newfile.txt        # Fails - read-only
ai> !rm README.md             # Fails - read-only
ai> !cat README.md            # Works - reading is allowed
```

### 4. **Automatic Cleanup**
Containers are automatically removed after command execution (`--rm` flag).

## How It Works

### Architecture

```
ai-shell
    ↓
DockerBashExecutor
    ↓
docker run --rm --network none -v $(pwd):/workspace:ro alpine:latest sh -c "command"
    ↓
Isolated Container (auto-deleted after execution)
```

### What Gets Mounted

- **Current directory** → `/workspace` inside container
- **Read-only** by default (docker mode)
- **Read-write** optional (docker-rw mode)

### Example

```bash
# On host:
$ pwd
/home/user/projects/myproject

# In ai-shell with Docker backend:
ai> !pwd
/workspace  # Container's working directory

ai> !ls
# Shows files from /home/user/projects/myproject
```

## Use Cases

### 1. Testing AI-Generated Commands

```bash
# Safe to let AI generate commands
ai-shell --bash-backend=docker

ai> ?Generate a bash command to find large files
# AI suggests: find . -type f -size +100M

ai> !find . -type f -size +100M
# Runs safely in container
```

### 2. Experimenting with System Commands

```bash
ai-shell --bash-backend=docker

# Try potentially dangerous commands safely:
ai> !rm -rf /tmp/*     # Only affects container
ai> !killall -9 bash   # Only affects container
ai> !mkfs.ext4 /dev/... # Fails - no device access
```

### 3. Different Environments

```bash
# Python environment
ai-shell --bash-backend=docker --docker-image=python:3.11
ai> !python --version

# Node environment
ai-shell --bash-backend=docker --docker-image=node:20
ai> !node --version

# Rust environment
ai-shell --bash-backend=docker --docker-image=rust:latest
ai> !cargo --version
```

### 4. CI/CD Testing

```bash
# Use in CI pipelines for safe command testing
ai-shell --bash-backend=docker --non-interactive < commands.txt
```

## Comparison with Native Backend

| Feature | Native | Docker | Docker-RW |
|---------|--------|--------|-----------|
| **Speed** | ⚡ Fast | 🐢 Slower (container overhead) | 🐢 Slower |
| **File Access** | ✅ Full | 👁️ Read-only | ✅ Read-write |
| **Network Access** | ✅ Yes | ❌ No | ❌ No |
| **Safety** | ⚠️ Low | ✅ High | ⚙️ Medium |
| **Isolation** | ❌ None | ✅ Full | ✅ Full |
| **Can Damage Host** | ✅ Yes | ❌ No | ⚙️ Limited |

## Performance Considerations

### First Command (Cold Start)
```
- Docker image pull: ~10-30 seconds (one time)
- Container creation: ~1-2 seconds
```

### Subsequent Commands
```
- Container creation: ~1-2 seconds per command
- Overhead compared to native: ~1-2 seconds
```

### Optimization Tips

1. **Use lightweight images**: `alpine:latest` (5MB) vs `ubuntu:latest` (70MB)
2. **Pre-pull images**: `docker pull alpine:latest`
3. **Use docker-rw** only when needed (slightly faster)

## Troubleshooting

### Docker Not Available

```bash
$ ai-shell --bash-backend=docker
Error: Docker is not available. Please install Docker...

# Install Docker:
# Ubuntu/Debian:
sudo apt install docker.io

# macOS:
brew install --cask docker

# Or visit: https://docs.docker.com/get-docker/
```

### Permission Denied

```bash
# If you get permission errors:
sudo usermod -aG docker $USER
# Then logout and login again
```

### Image Pull Fails

```bash
# Manually pull image:
docker pull alpine:latest

# Or use different image:
ai-shell --bash-backend=docker --docker-image=ubuntu:latest
```

### Slow Performance

```bash
# Use lightweight image:
ai-shell --bash-backend=docker --docker-image=alpine:latest

# Pre-pull image:
docker pull alpine:latest
```

## Advanced Configuration

### Custom Image with Tools

Create a custom Dockerfile:

```dockerfile
FROM alpine:latest
RUN apk add --no-cache \
    bash \
    git \
    python3 \
    nodejs \
    npm
```

Build and use:

```bash
docker build -t my-ai-shell:latest .
ai-shell --bash-backend=docker --docker-image=my-ai-shell:latest
```

### Programmatic Usage

```python
from ai_shell.core.docker_bash_executor import DockerBashExecutor

# Create executor
docker = DockerBashExecutor(
    image="alpine:latest",
    work_dir="/workspace",
    mount_current_dir=True
)

# Execute command
result = await docker.execute("ls -la")
print(result.output)
```

## Testing

```bash
# Run test suite
python test_docker_bash.py

# Run demo
python demo_docker.py
```

## Limitations

### What Docker Backend CAN'T Do

1. ❌ **Access devices**: No access to `/dev/sda`, etc.
2. ❌ **Network operations**: No internet access
3. ❌ **System modifications**: Can't modify host system
4. ❌ **Install packages on host**: Only in container
5. ❌ **Access other containers**: Isolated environment

### What Docker Backend CAN Do

1. ✅ **Read mounted files**: Can read from current directory
2. ✅ **Write files** (docker-rw): Can modify files in workspace
3. ✅ **Run commands**: Any command available in the image
4. ✅ **Install packages in container**: `apk add`, `apt install`, etc.
5. ✅ **Process data**: Text processing, calculations, etc.

## Security Recommendations

### For Development
- Use `--bash-backend=docker` by default
- Switch to `native` only when needed

### For AI Testing
- **Always** use `--bash-backend=docker`
- Never use `native` with untrusted AI-generated commands

### For Production
- Use `docker-rw` sparingly
- Consider custom images with specific tools
- Monitor container resource usage

## Demo Output

```
🐳 Docker Backend Demo

Checking Docker availability...
✓ Docker is available

Demo 1: List files in mounted directory
Command: ls
✓ Success

Demo 2: Show working directory
Command: pwd
✓ Success
/workspace

Demo 3: Show current user
Command: whoami
✓ Success
root

[... more demos ...]

🔒 Security Features Demo

Test 1: Try to modify files (should fail - read-only)
✓ Correctly blocked write operation
touch: /workspace/test.txt: Read-only file system

Test 2: Try to access network (should fail - no network)
✓ Network access blocked

✅ Docker Backend Confirmed Working!
```

## Summary

The Docker backend provides:

✅ **Safety**: Sandboxed execution, no host damage
✅ **Security**: No network, read-only by default
✅ **Flexibility**: Use any Docker image
✅ **Isolation**: Separate environment per command
✅ **Cleanup**: Automatic container removal

**Recommended for:**
- Testing AI-generated commands
- Experimenting safely
- Development and debugging
- CI/CD pipelines

**Use native backend for:**
- Maximum performance
- Full system access needed
- Trusted commands only

---

**Status**: ✅ Fully implemented and tested
**Version**: ai-shell v0.1.0
**Date**: 2025-10-10
