"""Base agent infrastructure for agentic pipeline scripts.

Provides shared patterns for all agents:
- LLM client via aisuite (from core.llm_client)
- Tool execution with risk-aware approval (core.agent_tools + core.risk_engine)
- Structured output via instructor
- Retry, error handling, and logging
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Protocol

from core.agent_tools import ALL_TOOLS, RiskLevel, Tool, ToolExecutor
from core.llm_client import AcaciaLLMClient, LLMConfig, LLMResult
from core.risk_engine import RiskEngine

logger = logging.getLogger(__name__)


class LLMClientLike(Protocol):
    """Duck-typed LLM client (real AcaciaLLMClient or test mock)."""

    def chat_with_retry(
        self,
        messages: list[dict[str, str]],
        *,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> LLMResult: ...

    def structured(
        self,
        messages: list[dict[str, str]],
        response_model: type[Any],
        *,
        model: str | None = None,
        temperature: float | None = None,
    ) -> Any | None: ...


@dataclass
class AgentConfig:
    llm_config: LLMConfig = field(default_factory=LLMConfig)
    max_tool_iterations: int = 15
    auto_approve_read: bool = True
    interactive: bool = False
    audit_log_path: str | None = None
    project_root: str | None = None


@dataclass
class AgentResult:
    success: bool = False
    error: str | None = None
    llm_calls: int = 0
    tool_calls: int = 0
    duration_seconds: float = 0.0


class BaseAgent:
    def __init__(
        self,
        config: AgentConfig | None = None,
        llm_client: AcaciaLLMClient | None = None,
        risk_engine: RiskEngine | None = None,
        tool_executor: ToolExecutor | None = None,
        approval_callback: Callable[[str, dict[str, Any], RiskLevel], bool] | None = None,
    ):
        self.config = config or AgentConfig()
        self.llm: LLMClientLike = llm_client or AcaciaLLMClient(config=self.config.llm_config)
        self.risk = risk_engine or RiskEngine(
            approval_callback=approval_callback,
            auto_approve_read=self.config.auto_approve_read,
            interactive=self.config.interactive,
            audit_log_path=self.config.audit_log_path,
        )
        self.tools = tool_executor or ToolExecutor(
            approval_callback=self._approve_tool,
            project_root=self.config.project_root,
        )
        self._start_time: float = 0.0
        self.llm_calls = 0
        self.tool_calls = 0

    def _approve_tool(self, tool: Tool, args: dict[str, Any]) -> bool:
        self.tool_calls += 1
        return self.risk.check(tool.name, args, tool.risk)

    def llm_chat(
        self,
        messages: list[dict[str, str]],
        *,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> LLMResult:
        self.llm_calls += 1
        return self.llm.chat_with_retry(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    def llm_structured(
        self,
        messages: list[dict[str, str]],
        response_model: type[Any],
        *,
        model: str | None = None,
        temperature: float | None = None,
    ) -> Any | None:
        self.llm_calls += 1
        return self.llm.structured(
            messages=messages,
            response_model=response_model,
            model=model,
            temperature=temperature,
        )

    def execute_tool(self, tool_name: str, args: dict[str, Any]) -> dict[str, Any]:
        return self.tools.execute(tool_name, args)

    def system_message(self, content: str) -> dict[str, str]:
        return {"role": "system", "content": content}

    def user_message(self, content: str) -> dict[str, str]:
        return {"role": "user", "content": content}

    def assistant_message(self, content: str) -> dict[str, str]:
        return {"role": "assistant", "content": content}

    def get_tool_definitions(self) -> list[dict[str, Any]]:
        return [t.to_openai_tool() for t in ALL_TOOLS]

    def begin(self):
        self._start_time = time.time()
        self.llm_calls = 0
        self.tool_calls = 0

    def end(self) -> AgentResult:
        return AgentResult(
            success=True,
            llm_calls=self.llm_calls,
            tool_calls=self.tool_calls,
            duration_seconds=time.time() - self._start_time,
        )

    def end_with_error(self, error: str) -> AgentResult:
        return AgentResult(
            success=False,
            error=error,
            llm_calls=self.llm_calls,
            tool_calls=self.tool_calls,
            duration_seconds=time.time() - self._start_time,
        )
