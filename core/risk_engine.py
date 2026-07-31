"""Risk engine for safe agentic automation.

Port of OpenWorker's 4-tier risk classification system.
Controls which tool operations can execute without human approval.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from core.agent_tools import RiskLevel


@dataclass
class ApprovalRequest:
    tool_name: str
    args: dict[str, Any]
    risk: RiskLevel
    timestamp: float = field(default_factory=time.time)
    approved: bool | None = None
    reason: str = ""


@dataclass
class AuditEntry:
    tool_name: str
    args: dict[str, Any]
    risk: RiskLevel
    approved: bool
    reason: str
    timestamp: float = field(default_factory=time.time)
    duration_ms: float = 0.0


class RiskEngine:
    """Controls tool execution based on risk level and approval policy.

    - READ: auto-approved
    - WRITE_LOCAL: approved once per session (per unique operation)
    - EXEC: always prompts for approval
    - EXTERNAL: always prompts + audit logged
    """

    def __init__(
        self,
        approval_callback: Callable[[str, dict[str, Any], RiskLevel], bool] | None = None,
        auto_approve_read: bool = True,
        session_timeout: int = 3600,
        audit_log_path: str | None = None,
        interactive: bool = False,
    ):
        self.approval_callback = approval_callback
        self.auto_approve_read = auto_approve_read
        self.session_timeout = session_timeout
        self.audit_log_path = audit_log_path
        self.interactive = interactive

        self._session_approvals: dict[str, float] = {}
        self._audit_log: list[AuditEntry] = []
        self._session_start = time.time()

    def check(self, tool_name: str, args: dict[str, Any], risk: RiskLevel) -> bool:
        if risk == RiskLevel.READ and self.auto_approve_read:
            self._audit(tool_name, args, risk, True, "auto-approved (read)")
            return True

        if risk == RiskLevel.WRITE_LOCAL:
            key = self._write_key(tool_name, args)
            if key in self._session_approvals:
                elapsed = time.time() - self._session_approvals[key]
                if elapsed < self.session_timeout:
                    self._audit(tool_name, args, risk, True, "session-approved")
                    return True
                del self._session_approvals[key]

        if self.approval_callback:
            approved = self.approval_callback(tool_name, args, risk)
        elif self.interactive:
            approved = self._interactive_approve(tool_name, args, risk)
        else:
            approved = False

        if approved and risk == RiskLevel.WRITE_LOCAL:
            key = self._write_key(tool_name, args)
            self._session_approvals[key] = time.time()

        self._audit(tool_name, args, risk, approved, "prompt-approved" if approved else "denied")
        return approved

    def _write_key(self, tool_name: str, args: dict[str, Any]) -> str:
        return f"{tool_name}:{hash(frozenset(args.items()))}"

    def _interactive_approve(
        self, tool_name: str, args: dict[str, Any], risk: RiskLevel
    ) -> bool:
        print(f"\n⚠️  Risk Level: {risk.value}")
        print(f"   Tool: {tool_name}")
        for k, v in args.items():
            val = v if len(str(v)) < 200 else str(v)[:197] + "..."
            print(f"   {k}: {val}")
        response = input("   Approve? (y/N/s for session): ").strip().lower()
        if response == "s":
            key = self._write_key(tool_name, args)
            self._session_approvals[key] = time.time()
            return True
        return response == "y"

    def _audit(
        self,
        tool_name: str,
        args: dict[str, Any],
        risk: RiskLevel,
        approved: bool,
        reason: str,
    ):
        entry = AuditEntry(
            tool_name=tool_name,
            args=args,
            risk=risk,
            approved=approved,
            reason=reason,
        )
        self._audit_log.append(entry)
        if self.audit_log_path:
            try:
                log_path = Path(self.audit_log_path)
                log_path.parent.mkdir(parents=True, exist_ok=True)
                with open(log_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(entry.__dict__) + "\n")
            except OSError:
                pass

    def get_audit_log(self) -> list[AuditEntry]:
        return list(self._audit_log)

    def get_stats(self) -> dict[str, Any]:
        total = len(self._audit_log)
        approved = sum(1 for e in self._audit_log if e.approved)
        by_risk: dict[str, int] = {}
        for e in self._audit_log:
            by_risk[e.risk.value] = by_risk.get(e.risk.value, 0) + 1
        return {
            "total_calls": total,
            "approved": approved,
            "denied": total - approved,
            "by_risk": by_risk,
            "session_approvals": len(self._session_approvals),
            "session_duration_seconds": time.time() - self._session_start,
        }


def make_cli_approval_callback() -> Callable[[str, dict[str, Any], RiskLevel], bool]:
    """Returns a CLI-based approval callback for interactive use."""

    def _callback(tool_name: str, args: dict[str, Any], risk: RiskLevel) -> bool:
        print(f"\n🔐 [{risk.value.upper()}] {tool_name}")
        for k, v in args.items():
            val = v if len(str(v)) < 200 else str(v)[:197] + "..."
            print(f"  {k}: {val}")
        result = input("  Approve? (y/N): ").strip().lower()
        return result == "y"

    return _callback


def make_auto_callback(
    auto_read: bool = True,
    auto_write_local: bool = False,
    auto_exec: bool = False,
    auto_external: bool = False,
) -> Callable[[str, dict[str, Any], RiskLevel], bool]:
    """Returns an automatic approval callback (for CI/testing)."""

    risk_map: dict[RiskLevel, bool] = {
        RiskLevel.READ: auto_read,
        RiskLevel.WRITE_LOCAL: auto_write_local,
        RiskLevel.EXEC: auto_exec,
        RiskLevel.EXTERNAL: auto_external,
    }

    def _callback(tool_name: str, args: dict[str, Any], risk: RiskLevel) -> bool:
        return risk_map.get(risk, False)

    return _callback
