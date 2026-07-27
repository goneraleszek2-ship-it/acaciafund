"""Tool definitions for the AcaciaFund agentic pipeline.

Each tool has a name, description, JSONSchema parameters, and risk level.
Mirrors OpenWorker's capability layer design.
"""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable


class RiskLevel(str, Enum):
    READ = "read"
    WRITE_LOCAL = "write_local"
    EXEC = "exec"
    EXTERNAL = "external"


@dataclass
class Tool:
    name: str
    description: str
    parameters: dict[str, Any]
    risk: RiskLevel = RiskLevel.READ
    requires: list[str] = field(default_factory=list)

    def to_openai_tool(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": self.parameters,
                    "required": [
                        k for k, v in self.parameters.items()
                        if isinstance(v, dict) and v.get("required", True)
                    ],
                },
            },
        }


# ── READ tools (auto-approve) ──

READ_FILE = Tool(
    name="read_file",
    description="Read contents of a file at the given path",
    parameters={
        "path": {"type": "string", "description": "Absolute path to the file"},
    },
    risk=RiskLevel.READ,
)

GLOB_FILES = Tool(
    name="glob_files",
    description="Find files matching a glob pattern",
    parameters={
        "pattern": {"type": "string", "description": "Glob pattern e.g. **/*.py"},
        "path": {"type": "string", "description": "Root directory to search"},
    },
    risk=RiskLevel.READ,
)

GREP_SEARCH = Tool(
    name="grep_search",
    description="Search file contents with a regex pattern",
    parameters={
        "pattern": {"type": "string", "description": "Regex pattern to search for"},
        "path": {"type": "string", "description": "Directory to search in"},
        "include": {"type": "string", "description": "File glob pattern"},
    },
    risk=RiskLevel.READ,
)

LIST_DIR = Tool(
    name="list_directory",
    description="List contents of a directory",
    parameters={
        "path": {"type": "string", "description": "Directory path"},
    },
    risk=RiskLevel.READ,
)

# ── WRITE_LOCAL tools (prompt once per session) ──

WRITE_FILE = Tool(
    name="write_file",
    description="Write content to a file (overwrites existing)",
    parameters={
        "path": {"type": "string", "description": "Absolute path to the file"},
        "content": {"type": "string", "description": "File content"},
    },
    risk=RiskLevel.WRITE_LOCAL,
)

EDIT_FILE = Tool(
    name="edit_file",
    description="Edit a file by replacing exact text with new text",
    parameters={
        "path": {"type": "string", "description": "Absolute path to the file"},
        "old_string": {"type": "string", "description": "Exact text to replace"},
        "new_string": {"type": "string", "description": "Replacement text"},
    },
    risk=RiskLevel.WRITE_LOCAL,
)

CREATE_DIR = Tool(
    name="create_directory",
    description="Create a directory (including parents)",
    parameters={
        "path": {"type": "string", "description": "Directory path to create"},
    },
    risk=RiskLevel.WRITE_LOCAL,
)

# ── EXEC tools (prompt every time) ──

RUN_SHELL = Tool(
    name="run_shell",
    description="Execute a shell command and return output",
    parameters={
        "command": {"type": "string", "description": "Shell command to run"},
        "workdir": {"type": "string", "description": "Working directory"},
        "timeout": {"type": "integer", "description": "Timeout in seconds", "required": False},
    },
    risk=RiskLevel.EXEC,
)

RUN_PYTHON = Tool(
    name="run_python",
    description="Execute Python code and return output",
    parameters={
        "code": {"type": "string", "description": "Python code to execute"},
        "workdir": {"type": "string", "description": "Working directory", "required": False},
    },
    risk=RiskLevel.EXEC,
)

# ── EXTERNAL tools (prompt + audit) ──

WEB_SEARCH = Tool(
    name="web_search",
    description="Search the web for information",
    parameters={
        "query": {"type": "string", "description": "Search query"},
    },
    risk=RiskLevel.EXTERNAL,
)

FETCH_URL = Tool(
    name="fetch_url",
    description="Fetch content from a URL",
    parameters={
        "url": {"type": "string", "description": "URL to fetch"},
    },
    risk=RiskLevel.EXTERNAL,
)

# ── Registry ──

ALL_TOOLS: list[Tool] = [
    READ_FILE,
    GLOB_FILES,
    GREP_SEARCH,
    LIST_DIR,
    WRITE_FILE,
    EDIT_FILE,
    CREATE_DIR,
    RUN_SHELL,
    RUN_PYTHON,
    WEB_SEARCH,
    FETCH_URL,
]

TOOL_MAP: dict[str, Tool] = {t.name: t for t in ALL_TOOLS}


# ── Tool Executor ──

class ToolExecutor:
    """Executes tool calls with risk approval callback."""

    def __init__(
        self,
        approval_callback: Callable[[Tool, dict[str, Any]], bool] | None = None,
        project_root: str | None = None,
    ):
        self.approval_callback = approval_callback
        self.project_root = project_root or os.getcwd()

    def execute(
        self, tool_name: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        tool = TOOL_MAP.get(tool_name)
        if not tool:
            return {"error": f"Unknown tool: {tool_name}"}

        if self.approval_callback and not self.approval_callback(tool, args):
            return {"error": f"Tool {tool_name} was not approved"}

        handlers = {
            "read_file": self._exec_read_file,
            "glob_files": self._exec_glob_files,
            "grep_search": self._exec_grep_search,
            "list_directory": self._exec_list_dir,
            "write_file": self._exec_write_file,
            "create_directory": self._exec_create_dir,
            "run_shell": self._exec_run_shell,
            "run_python": self._exec_run_python,
        }
        handler = handlers.get(tool_name)
        if handler is None:
            return {"error": f"Handler not implemented: {tool_name}"}
        return handler(args)

    def _exec_read_file(self, args: dict[str, Any]) -> dict[str, Any]:
        path = args.get("path", "")
        if not os.path.isabs(path):
            path = os.path.join(self.project_root, path)
        try:
            with open(path, "r", encoding="utf-8") as f:
                return {"content": f.read()}
        except Exception as e:
            return {"error": str(e)}

    def _exec_glob_files(self, args: dict[str, Any]) -> dict[str, Any]:
        import glob

        pattern = args.get("pattern", "")
        root = args.get("path", self.project_root)
        matches = glob.glob(os.path.join(root, pattern), recursive=True)
        return {"matches": matches}

    def _exec_grep_search(self, args: dict[str, Any]) -> dict[str, Any]:
        import subprocess

        pattern = args.get("pattern", "")
        path = args.get("path", self.project_root)
        include = args.get("include", "")
        cmd = ["grep", "-r", "-n", pattern, path]
        if include:
            cmd.extend(["--include", include])
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            lines = result.stdout.strip().split("\n") if result.stdout.strip() else []
            return {"matches": lines[:200]}
        except subprocess.TimeoutExpired:
            return {"error": "grep search timed out"}
        except Exception as e:
            return {"error": str(e)}

    def _exec_list_dir(self, args: dict[str, Any]) -> dict[str, Any]:
        path = args.get("path", self.project_root)
        try:
            entries = os.listdir(path)
            return {"entries": entries}
        except Exception as e:
            return {"error": str(e)}

    def _exec_write_file(self, args: dict[str, Any]) -> dict[str, Any]:
        path = args.get("path", "")
        content = args.get("content", "")
        if not os.path.isabs(path):
            path = os.path.join(self.project_root, path)
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            return {"success": True, "path": path}
        except Exception as e:
            return {"error": str(e)}

    def _exec_create_dir(self, args: dict[str, Any]) -> dict[str, Any]:
        path = args.get("path", "")
        if not os.path.isabs(path):
            path = os.path.join(self.project_root, path)
        try:
            os.makedirs(path, exist_ok=True)
            return {"success": True, "path": path}
        except Exception as e:
            return {"error": str(e)}

    def _exec_run_shell(self, args: dict[str, Any]) -> dict[str, Any]:
        command = args.get("command", "")
        workdir = args.get("workdir", self.project_root)
        timeout = args.get("timeout", 30)
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=workdir,
                timeout=timeout,
            )
            return {
                "stdout": result.stdout[:5000],
                "stderr": result.stderr[:2000],
                "return_code": result.returncode,
            }
        except subprocess.TimeoutExpired:
            return {"error": f"Command timed out after {timeout}s"}
        except Exception as e:
            return {"error": str(e)}

    def _exec_run_python(self, args: dict[str, Any]) -> dict[str, Any]:
        code = args.get("code", "")
        workdir = args.get("workdir", self.project_root)
        try:
            import tempfile

            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".py", delete=False, dir=workdir
            ) as f:
                f.write(code)
                f.flush()
                result = subprocess.run(
                    ["python3", f.name],
                    capture_output=True, text=True, cwd=workdir, timeout=30
                )
                os.unlink(f.name)
                return {
                    "stdout": result.stdout[:5000],
                    "stderr": result.stderr[:2000],
                    "return_code": result.returncode,
                }
        except subprocess.TimeoutExpired:
            return {"error": "Python execution timed out"}
        except Exception as e:
            return {"error": str(e)}
