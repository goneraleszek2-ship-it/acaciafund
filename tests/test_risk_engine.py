"""Tests for core/risk_engine.py"""

import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.risk_engine import (
    RiskEngine,
    RiskLevel,
    make_auto_callback,
    make_cli_approval_callback,
)


class TestRiskEngine:
    def test_auto_approve_read(self):
        engine = RiskEngine(auto_approve_read=True)
        assert engine.check("read_file", {"path": "/tmp/test.txt"}, RiskLevel.READ) is True

    def test_deny_read_when_auto_disabled(self):
        engine = RiskEngine(auto_approve_read=False, interactive=False)
        assert engine.check("read_file", {"path": "/tmp/test.txt"}, RiskLevel.READ) is False

    def test_write_local_requires_approval(self):
        engine = RiskEngine(interactive=False)
        assert engine.check("write_file", {"path": "/tmp/test.txt", "content": "data"}, RiskLevel.WRITE_LOCAL) is False

    def test_write_local_session_approval(self):
        engine = RiskEngine(approval_callback=lambda n, a, r: True)
        # First call: should be approved via callback
        assert engine.check("write_file", {"path": "/tmp/test.txt", "content": "data"}, RiskLevel.WRITE_LOCAL) is True
        # Second call: same operation should be session-approved
        assert engine.check("write_file", {"path": "/tmp/test.txt", "content": "data"}, RiskLevel.WRITE_LOCAL) is True

    def test_write_local_different_ops_not_cached(self):
        engine = RiskEngine(interactive=False)
        engine._session_approvals["write_file:123"] = float("inf")
        assert engine.check("write_file", {"path": "/tmp/different.txt"}, RiskLevel.WRITE_LOCAL) is False

    def test_exec_always_prompts(self):
        engine = RiskEngine(interactive=False)
        assert engine.check("run_shell", {"command": "rm -rf /"}, RiskLevel.EXEC) is False

    def test_external_always_prompts(self):
        engine = RiskEngine(interactive=False)
        assert engine.check("web_search", {"query": "test"}, RiskLevel.EXTERNAL) is False

    def test_approval_callback_called(self):
        calls = []
        def cb(name, args, risk):
            calls.append((name, risk.value))
            return True
        engine = RiskEngine(approval_callback=cb, auto_approve_read=False)
        engine.check("read_file", {"path": "/x"}, RiskLevel.READ)
        assert len(calls) == 1
        assert calls[0] == ("read_file", "read")

    def test_denied_by_callback(self):
        engine = RiskEngine(approval_callback=lambda n, a, r: False, auto_approve_read=False)
        assert engine.check("read_file", {}, RiskLevel.READ) is False

    def test_audit_log_records_approved(self):
        engine = RiskEngine(approval_callback=lambda n, a, r: True, auto_approve_read=False)
        engine.check("test_tool", {"arg": "val"}, RiskLevel.EXEC)
        log = engine.get_audit_log()
        assert len(log) == 1
        assert log[0].tool_name == "test_tool"
        assert log[0].approved is True
        assert log[0].risk == RiskLevel.EXEC

    def test_audit_log_records_denied(self):
        engine = RiskEngine(interactive=False)
        engine.check("test_tool", {}, RiskLevel.EXEC)
        log = engine.get_audit_log()
        assert len(log) == 1
        assert log[0].approved is False

    def test_audit_log_file(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            log_path = f.name
        engine = RiskEngine(
            approval_callback=lambda n, a, r: True,
            audit_log_path=log_path,
            auto_approve_read=False,
        )
        engine.check("tool_a", {}, RiskLevel.READ)
        written = Path(log_path).read_text()
        assert "tool_a" in written
        Path(log_path).unlink(missing_ok=True)

    def test_get_stats(self):
        engine = RiskEngine(approval_callback=lambda n, a, r: True, auto_approve_read=False)
        engine.check("r1", {}, RiskLevel.READ)
        engine.check("w1", {}, RiskLevel.WRITE_LOCAL)
        engine.check("e1", {}, RiskLevel.EXEC)
        stats = engine.get_stats()
        assert stats["total_calls"] == 3
        assert stats["approved"] == 3
        assert stats["denied"] == 0


class TestMakeAutoCallback:
    def test_read_only(self):
        cb = make_auto_callback(auto_read=True, auto_write_local=False, auto_exec=False, auto_external=False)
        assert cb("read_file", {}, RiskLevel.READ) is True
        assert cb("write_file", {}, RiskLevel.WRITE_LOCAL) is False
        assert cb("run_shell", {}, RiskLevel.EXEC) is False

    def test_all_approved(self):
        cb = make_auto_callback(auto_read=True, auto_write_local=True, auto_exec=True, auto_external=True)
        assert cb("any", {}, RiskLevel.READ) is True
        assert cb("any", {}, RiskLevel.WRITE_LOCAL) is True
        assert cb("any", {}, RiskLevel.EXEC) is True
        assert cb("any", {}, RiskLevel.EXTERNAL) is True


class TestMakeCliApprovalCallback:
    def test_is_callable(self):
        cb = make_cli_approval_callback()
        assert callable(cb)
