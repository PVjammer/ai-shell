"""File operation commands."""

import os
from pathlib import Path


async def list_cmd(args, stdin=None, **options):
    r"""
    List files in directory.

    Usage:
        \list
        \list /path/to/dir
        \list --all
        \list /path --recursive
    """
    path = args[0] if args else "."
    show_all = options.get('all', False) or options.get('a', False)
    recursive = options.get('recursive', False) or options.get('r', False)

    try:
        path_obj = Path(path)

        if not path_obj.exists():
            return f"Error: Path does not exist: {path}"

        if not path_obj.is_dir():
            return f"Error: Not a directory: {path}"

        if recursive:
            # Recursive listing
            files = []
            for root, dirs, filenames in os.walk(path):
                for name in filenames:
                    if show_all or not name.startswith('.'):
                        rel_path = os.path.relpath(os.path.join(root, name), path)
                        files.append(rel_path)
                for name in dirs:
                    if show_all or not name.startswith('.'):
                        rel_path = os.path.relpath(os.path.join(root, name), path)
                        files.append(rel_path + "/")
            return "\n".join(sorted(files))
        else:
            # Non-recursive listing
            files = []
            for item in path_obj.iterdir():
                if show_all or not item.name.startswith('.'):
                    name = item.name
                    if item.is_dir():
                        name += "/"
                    files.append(name)
            return "\n".join(sorted(files))

    except Exception as e:
        return f"Error: {e}"


async def cat_cmd(args, stdin=None, **options):
    r"""
    Display file contents (like bash cat).

    Usage:
        \cat file.txt
        \cat file1.txt file2.txt
    """
    if not args:
        return "Usage: \\cat <file> [file2 ...]"

    outputs = []
    for filepath in args:
        try:
            with open(filepath, 'r') as f:
                content = f.read()
                outputs.append(content)
        except Exception as e:
            outputs.append(f"Error reading {filepath}: {e}")

    return "\n".join(outputs)


async def tree_cmd(args, stdin=None, **options):
    r"""
    Display directory tree structure.

    Usage:
        \tree
        \tree /path/to/dir
        \tree --max-depth=2
    """
    path = args[0] if args else "."
    max_depth = int(options.get('max_depth', options.get('d', 3)))

    def build_tree(dir_path, prefix="", depth=0):
        """Recursively build tree structure."""
        if depth >= max_depth:
            return []

        try:
            entries = sorted(Path(dir_path).iterdir(), key=lambda x: (not x.is_dir(), x.name))
        except PermissionError:
            return [f"{prefix}[Permission Denied]"]

        lines = []
        for i, entry in enumerate(entries):
            is_last = i == len(entries) - 1
            current_prefix = "└── " if is_last else "├── "
            next_prefix = "    " if is_last else "│   "

            name = entry.name
            if entry.is_dir():
                name += "/"

            lines.append(f"{prefix}{current_prefix}{name}")

            if entry.is_dir():
                lines.extend(build_tree(entry, prefix + next_prefix, depth + 1))

        return lines

    try:
        path_obj = Path(path)
        if not path_obj.exists():
            return f"Error: Path does not exist: {path}"

        if not path_obj.is_dir():
            return f"Error: Not a directory: {path}"

        result = [str(path_obj.resolve())]
        result.extend(build_tree(path_obj))
        return "\n".join(result)

    except Exception as e:
        return f"Error: {e}"


async def find_cmd(args, stdin=None, **options):
    r"""
    Find files by name pattern.

    Usage:
        \find "*.py"
        \find "test_*.py" --path=/src
    """
    if not args:
        return "Usage: \\find <pattern> [--path=/dir]"

    pattern = args[0]
    search_path = options.get('path', '.')

    try:
        path_obj = Path(search_path)
        matches = list(path_obj.rglob(pattern))

        if not matches:
            return "(no files found)"

        # Convert to relative paths
        rel_matches = []
        for match in matches:
            try:
                rel_path = match.relative_to(Path.cwd())
                rel_matches.append(str(rel_path))
            except ValueError:
                rel_matches.append(str(match))

        return "\n".join(sorted(rel_matches))

    except Exception as e:
        return f"Error: {e}"


def register_file_commands(executor):
    """Register all file operation commands."""
    executor.register_command("list", list_cmd,
                             "List files in directory",
                             category="files")

    executor.register_command("cat", cat_cmd,
                             "Display file contents",
                             category="files")

    executor.register_command("tree", tree_cmd,
                             "Display directory tree structure",
                             category="files")

    executor.register_command("find", find_cmd,
                             "Find files by name pattern",
                             category="files")
