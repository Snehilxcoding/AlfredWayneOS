# ============================================================
# Alfred Wayne OS - Coding Assistant (Phase B)
# Alfred can explain errors, generate code, run safe commands,
# create files, and debug code on Master Wayne's behalf.
# ============================================================

import os
import subprocess
import re
from config.settings import USER_NAME


# ── Safety: commands Alfred will NEVER run without warning ───
DANGEROUS_PATTERNS = [
    r"rm\s+-rf",
    r"rmdir\s+/s",
    r"format\s+c:",
    r"del\s+/f\s+/s",
    r"shutdown",
    r"reboot",
    r":(){:|:&};:",    # Fork bomb
    r"DROP\s+TABLE",
    r"DROP\s+DATABASE",
]

# ── Commands Alfred runs automatically (safe) ────────────────
SAFE_COMMANDS = [
    "python",
    "pip",
    "git status",
    "git log",
    "git diff",
    "dir",
    "ls",
    "cd",
    "echo",
    "type",
    "cat",
    "tree",
    "node",
    "npm",
    "pytest",
    "python -m pytest",
]


def is_safe_command(command: str) -> bool:
    """
    Returns True if the command is safe to run automatically.
    Returns False if it needs user confirmation.
    """
    cmd_lower = command.lower().strip()

    # Check for dangerous patterns first
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, cmd_lower, re.IGNORECASE):
            return False

    # Check if it starts with a known safe command
    for safe in SAFE_COMMANDS:
        if cmd_lower.startswith(safe):
            return True

    return False


def run_command(command: str, require_confirmation: bool = True) -> dict:
    """
    Runs a terminal command and returns the result.

    Returns dict with:
        success:  bool
        output:   stdout string
        error:    stderr string
        command:  the command that was run
    """
    if require_confirmation and not is_safe_command(command):
        return {
            "success":  False,
            "output":   "",
            "error":    "confirmation_required",
            "command":  command,
        }

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30,
            cwd=os.getcwd(),
        )
        return {
            "success": result.returncode == 0,
            "output":  result.stdout.strip(),
            "error":   result.stderr.strip(),
            "command": command,
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "output":  "",
            "error":   "Command timed out after 30 seconds.",
            "command": command,
        }
    except Exception as e:
        return {
            "success": False,
            "output":  "",
            "error":   str(e),
            "command": command,
        }


def create_file_with_content(filepath: str, content: str) -> dict:
    """
    Creates a file at the given path with the given content.
    Creates parent directories if they don't exist.
    Returns dict with success and message.
    """
    try:
        # Expand user home directory if needed
        filepath = os.path.expanduser(filepath)

        # Create parent directories
        parent = os.path.dirname(filepath)
        if parent:
            os.makedirs(parent, exist_ok=True)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        return {
            "success":  True,
            "message":  f"File created: {filepath}",
            "filepath": filepath,
        }
    except Exception as e:
        return {
            "success":  False,
            "message":  f"Failed to create file: {e}",
            "filepath": filepath,
        }


def read_file(filepath: str) -> dict:
    """
    Reads a file and returns its contents.
    Used when Master Wayne asks Alfred to look at a file.
    """
    try:
        filepath = os.path.expanduser(filepath)
        if not os.path.exists(filepath):
            return {
                "success": False,
                "content": "",
                "message": f"File not found: {filepath}",
            }
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        return {
            "success": True,
            "content": content,
            "message": f"Read {len(content)} characters from {filepath}",
        }
    except Exception as e:
        return {
            "success": False,
            "content": "",
            "message": f"Could not read file: {e}",
        }


def get_project_structure(path: str = ".") -> str:
    """
    Returns a tree-like string of the project structure.
    Skips venv, __pycache__, .git, node_modules.
    """
    skip_dirs = {
        "venv", "__pycache__", ".git", "node_modules",
        ".venv", "env", "dist", "build", ".mypy_cache",
    }
    skip_exts = {".pyc", ".pyo", ".pyd"}

    lines = []

    for root, dirs, files in os.walk(path):
        # Remove skipped directories in-place
        dirs[:] = [d for d in dirs if d not in skip_dirs]

        level  = root.replace(path, "").count(os.sep)
        indent = "  " * level
        folder = os.path.basename(root)

        if level == 0:
            lines.append(f"{folder}/")
        else:
            lines.append(f"{indent}{folder}/")

        sub_indent = "  " * (level + 1)
        for file in files:
            if not any(file.endswith(ext) for ext in skip_exts):
                lines.append(f"{sub_indent}{file}")

    return "\n".join(lines)


def format_command_result(result: dict) -> str:
    """
    Formats a command result into a readable string for Alfred to speak.
    """
    if result["error"] == "confirmation_required":
        return (
            f"I'd like to run the following command, {USER_NAME}, "
            f"but it requires your confirmation first:\n\n"
            f"  {result['command']}\n\n"
            f"Shall I proceed? (yes/no)"
        )

    if result["success"]:
        output = result["output"]
        if output:
            # Truncate very long outputs
            if len(output) > 1000:
                output = output[:1000] + "\n... (output truncated)"
            return f"Command completed successfully, {USER_NAME}.\n\n{output}"
        return f"Command completed successfully, {USER_NAME}."
    else:
        error = result["error"]
        return (
            f"The command encountered an error, {USER_NAME}:\n\n{error}\n\n"
            f"Shall I attempt to diagnose this?"
        )