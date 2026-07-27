"""Tests for core/agent_tools.py"""

import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.agent_tools import (
    ALL_TOOLS,
    READ_FILE,
    RUN_SHELL,
    WEB_SEARCH,
    WRITE_FILE,
    RiskLevel,
    Tool,
    ToolExecutor,
)


class TestTool:
    def test_risk_levels_defined(self):
        assert RiskLevel.READ.value == "read"
        assert RiskLevel.WRITE_LOCAL.value == "write_local"
        assert RiskLevel.EXEC.value == "exec"
        assert RiskLevel.EXTERNAL.value == "external"

    def test_to_openai_tool(self):
        tool = Tool(
            name="test_tool",
            description="A test tool",
            parameters={"arg1": {"type": "string", "description": "First arg"}},
            risk=RiskLevel.READ,
        )
        ot = tool.to_openai_tool()
        assert ot["type"] == "function"
        assert ot["function"]["name"] == "test_tool"
        assert "arg1" in ot["function"]["parameters"]["properties"]

    def test_all_tools_have_implementations(self):
        names = {t.name for t in ALL_TOOLS}
        expected = {"read_file", "glob_files", "grep_search", "list_directory",
                     "write_file", "edit_file", "create_directory",
                     "run_shell", "run_python", "web_search", "fetch_url"}
        assert names == expected

    def test_read_file_risk(self):
        assert READ_FILE.risk == RiskLevel.READ

    def test_write_file_risk(self):
        assert WRITE_FILE.risk == RiskLevel.WRITE_LOCAL

    def test_run_shell_risk(self):
        assert RUN_SHELL.risk == RiskLevel.EXEC

    def test_web_search_risk(self):
        assert WEB_SEARCH.risk == RiskLevel.EXTERNAL


class TestToolExecutor:
    def test_unknown_tool_returns_error(self):
        exe = ToolExecutor()
        result = exe.execute("nonexistent_tool", {})
        assert "error" in result
        assert "Unknown tool" in result["error"]

    def test_denied_by_callback(self):
        exe = ToolExecutor(approval_callback=lambda t, a: False)
        result = exe.execute("read_file", {"path": "/tmp/test.txt"})
        assert "error" in result
        assert "not approved" in result["error"]

    def test_read_file_success(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("hello world")
            f.flush()
            fname = f.name
        exe = ToolExecutor()
        result = exe.execute("read_file", {"path": fname})
        Path(fname).unlink(missing_ok=True)
        assert result.get("content") == "hello world"

    def test_read_file_not_found(self):
        exe = ToolExecutor()
        result = exe.execute("read_file", {"path": "/tmp/nonexistent_file_xyz.txt"})
        assert "error" in result

    def test_write_file_creates_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test_output.txt"
            exe = ToolExecutor()
            result = exe.execute("write_file", {"path": str(path), "content": "test content"})
            assert result.get("success") is True
            assert path.read_text() == "test content"

    def test_list_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "a.txt").touch()
            Path(tmpdir, "b.txt").touch()
            exe = ToolExecutor()
            result = exe.execute("list_directory", {"path": tmpdir})
            assert "entries" in result
            assert "a.txt" in result["entries"]
            assert "b.txt" in result["entries"]

    def test_run_shell_echo(self):
        exe = ToolExecutor(approval_callback=lambda t, a: True)
        result = exe.execute("run_shell", {"command": "echo hello"})
        assert result.get("stdout", "").strip() == "hello"

    def test_run_shell_denied(self):
        exe = ToolExecutor(approval_callback=lambda t, a: False)
        result = exe.execute("run_shell", {"command": "echo danger"})
        assert "error" in result

    def test_run_python_simple(self):
        exe = ToolExecutor(approval_callback=lambda t, a: True)
        result = exe.execute("run_python", {"code": "print(2 + 2)"})
        assert result.get("stdout", "").strip() == "4"
