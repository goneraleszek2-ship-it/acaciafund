"""OpenWorker server mode client.

Connects to a running OpenWorker FastAPI agent server to submit tasks,
check status, and retrieve results. Integrates with AcaciaFund's
RiskEngine for approval callbacks and uses existing agent_tools.

Usage:
    client = OpenWorkerClient(base_url="http://localhost:8000")
    task_id = client.submit_task("research", {"pillar": "aml", "topic": "..."})
    result = client.wait_for_result(task_id, poll_interval=2.0)
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass
from typing import Any, Callable

logger = logging.getLogger(__name__)


class OpenWorkerError(Exception):
    """Base exception for OpenWorker client errors."""


class TaskFailedError(OpenWorkerError):
    """Raised when a task completes with a failure status."""


@dataclass
class OpenWorkerConfig:
    base_url: str = "http://localhost:8000"
    api_key: str | None = None
    timeout: float = 60.0
    poll_interval: float = 1.0
    max_poll_time: float = 300.0
    auto_approve_read: bool = True


class OpenWorkerClient:
    """HTTP client for OpenWorker FastAPI agent server.

    Uses httpx for async HTTP communication.
    Falls back to urllib if httpx is unavailable.
    """

    def __init__(
        self,
        config: OpenWorkerConfig | None = None,
        approval_callback: Callable[[str, dict[str, Any], str], bool] | None = None,
    ):
        self.config = config or OpenWorkerConfig()
        self.approval_callback = approval_callback
        self._session = self._create_session()

    def _create_session(self):
        try:
            import httpx  # noqa: F401
            headers = {}
            if self.config.api_key:
                headers["Authorization"] = f"Bearer {self.config.api_key}"
            return _HttpxSession(
                base_url=self.config.base_url.rstrip("/"),
                headers=headers,
                timeout=self.config.timeout,
            )
        except ImportError:
            logger.warning("httpx not available, using urllib fallback")
            return _UrllibSession(
                base_url=self.config.base_url.rstrip("/"),
                api_key=self.config.api_key,
                timeout=self.config.timeout,
            )

    def health_check(self) -> dict[str, Any]:
        return self._session.get("/health")

    def submit_task(
        self,
        task_type: str,
        params: dict[str, Any],
        *,
        priority: int = 0,
        tags: list[str] | None = None,
    ) -> str:
        payload = {
            "task_type": task_type,
            "params": params,
            "priority": priority,
            "tags": tags or [],
        }
        result = self._session.post("/tasks", json=payload)
        task_id = result.get("task_id", "")
        if not task_id:
            raise OpenWorkerError(f"No task_id in response: {result}")
        logger.info(f"Submitted {task_type} task: {task_id}")
        return task_id

    def get_task_status(self, task_id: str) -> dict[str, Any]:
        return self._session.get(f"/tasks/{task_id}")

    def get_task_result(self, task_id: str) -> dict[str, Any] | None:
        status = self.get_task_status(task_id)
        if status.get("status") == "completed":
            return status.get("result")
        return None

    def cancel_task(self, task_id: str) -> bool:
        result = self._session.delete(f"/tasks/{task_id}")
        return result.get("cancelled", False)

    def wait_for_result(
        self,
        task_id: str,
        *,
        poll_interval: float | None = None,
        timeout: float | None = None,
    ) -> dict[str, Any]:
        interval = poll_interval or self.config.poll_interval
        deadline = time.time() + (timeout or self.config.max_poll_time)
        last_status = ""
        while time.time() < deadline:
            status = self.get_task_status(task_id)
            current = status.get("status", "unknown")
            if current != last_status:
                logger.debug(f"  task {task_id[:8]}... status: {current}")
                last_status = current
            if current == "completed":
                result = status.get("result")
                if result is None:
                    raise OpenWorkerError(f"Task {task_id} completed with no result")
                return result  # type: ignore[return-value]
            if current in ("failed", "error"):
                error = status.get("error", "Unknown error")
                raise TaskFailedError(f"Task {task_id} failed: {error}")
            if current == "cancelled":
                raise TaskFailedError(f"Task {task_id} was cancelled")
            if current == "pending_approval":
                self._handle_approval(task_id, status)
            time.sleep(interval)
        raise OpenWorkerError(f"Task {task_id} timed out after {deadline - time.time() + (timeout or self.config.max_poll_time):.0f}s")

    def _handle_approval(self, task_id: str, status: dict[str, Any]):
        if not self.approval_callback:
            logger.warning(f"Task {task_id[:8]}... needs approval but no callback set — denying")
            self._session.post(f"/tasks/{task_id}/deny", json={"reason": "No approval callback configured"})
            return
        tool_name = (status.get("approval_request") or {}).get("tool_name", "unknown")
        args = (status.get("approval_request") or {}).get("args", {})
        risk_level = (status.get("approval_request") or {}).get("risk_level", "read")
        approved = self.approval_callback(tool_name, args, risk_level)
        if approved:
            self._session.post(f"/tasks/{task_id}/approve", json={})
        else:
            self._session.post(f"/tasks/{task_id}/deny", json={"reason": "Denied by callback"})

    def submit_and_wait(
        self,
        task_type: str,
        params: dict[str, Any],
        *,
        priority: int = 0,
        poll_interval: float | None = None,
        timeout: float | None = None,
    ) -> dict[str, Any]:
        task_id = self.submit_task(task_type, params, priority=priority)
        return self.wait_for_result(task_id, poll_interval=poll_interval, timeout=timeout)


class _HttpxSession:
    def __init__(self, base_url: str, headers: dict[str, str], timeout: float):
        import httpx
        self._client = httpx.Client(base_url=base_url, headers=headers, timeout=timeout)

    def get(self, path: str) -> dict[str, Any]:
        r = self._client.get(path)
        r.raise_for_status()
        return r.json()

    def post(self, path: str, json: dict[str, Any]) -> dict[str, Any]:
        r = self._client.post(path, json=json)
        r.raise_for_status()
        return r.json()

    def delete(self, path: str) -> dict[str, Any]:
        r = self._client.delete(path)
        r.raise_for_status()
        return r.json()


class _UrllibSession:
    def __init__(self, base_url: str, api_key: str | None, timeout: float):
        self.base_url = base_url
        self.api_key = api_key
        self.timeout = timeout

    def _request(self, method: str, path: str, body: bytes | None = None) -> dict[str, Any]:
        import urllib.request
        url = f"{self.base_url}{path}"
        req = urllib.request.Request(url, data=body, method=method)
        if self.api_key:
            req.add_header("Authorization", f"Bearer {self.api_key}")
        if body:
            req.add_header("Content-Type", "application/json")
        r = urllib.request.urlopen(req, timeout=self.timeout)
        return json.loads(r.read().decode("utf-8"))

    def get(self, path: str) -> dict[str, Any]:
        return self._request("GET", path)

    def post(self, path: str, json: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", path, body=json.dumps(json).encode())

    def delete(self, path: str) -> dict[str, Any]:
        return self._request("DELETE", path)
