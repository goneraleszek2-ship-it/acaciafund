"""Unified LLM client based on aisuite (OpenWorker's engine).

Replaces ad-hoc LLM calls with a provider-agnostic interface.
Supports structured outputs via instructor.

Providers are configured via environment variables:
    OPENAI_API_KEY, ANTHROPIC_API_KEY, GROQ_API_KEY, TOGETHER_API_KEY, etc.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel


@dataclass
class LLMConfig:
    provider: str = "openai"
    model: str = "gpt-4o-mini"
    temperature: float = 0.4
    max_tokens: int = 2048
    timeout: int = 60
    max_retries: int = 3
    extra_headers: dict[str, str] = field(default_factory=dict)


@dataclass
class LLMResult:
    content: str | None
    model: str
    provider: str
    usage: dict[str, int] | None = None
    finish_reason: str | None = None
    error: str | None = None


class AcaciaLLMClient:
    """Provider-agnostic LLM client backed by aisuite."""

    def __init__(self, config: LLMConfig | None = None):
        self.config = config or LLMConfig()
        self._client: Any = None
        self._instructor_client: Any = None

    def _ensure_client(self):
        if self._client is not None:
            return
        try:
            from aisuite import Client as AISuiteClient

            provider_configs = self._build_provider_configs()
            self._client = AISuiteClient(provider_configs=provider_configs)
        except ImportError:
            raise ImportError(
                "aisuite is required. Install with: pip install aisuite"
            )
        except Exception as exc:
            raise ImportError(
                "aisuite is required. Install with: pip install aisuite"
            ) from exc

    def _build_provider_configs(self) -> dict[str, dict[str, str]]:
        configs: dict[str, dict[str, str]] = {}
        provider_env_map = {
            "openai": ("api_key", "OPENAI_API_KEY"),
            "anthropic": ("api_key", "ANTHROPIC_API_KEY"),
            "groq": ("api_key", "GROQ_API_KEY"),
            "together": ("api_key", "TOGETHER_API_KEY"),
            "google": ("api_key", "GOOGLE_API_KEY"),
            "cohere": ("api_key", "COHERE_API_KEY"),
            "mistral": ("api_key", "MISTRAL_API_KEY"),
            "deepseek": ("api_key", "DEEPSEEK_API_KEY"),
        }
        for provider, (key_name, env_var) in provider_env_map.items():
            value = os.environ.get(env_var)
            if value:
                configs[provider] = {key_name: value}
        return configs

    def _parse_model(self, model_str: str) -> tuple[str, str]:
        parts = model_str.split(":", 1)
        if len(parts) == 2:
            return parts[0], parts[1]
        return self.config.provider, model_str

    def chat(
        self,
        messages: list[dict[str, str]],
        *,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> LLMResult:
        try:
            self._ensure_client()
        except ImportError as e:
            return LLMResult(
                content=None,
                model=model or self.config.model,
                provider=self.config.provider,
                error=str(e),
            )
        provider, model_name = self._parse_model(model or self.config.model)
        full_model = f"{provider}:{model_name}"
        try:
            resp = self._client.chat.completions.create(
                model=full_model,
                messages=messages,
                temperature=temperature if temperature is not None else self.config.temperature,
                max_tokens=max_tokens if max_tokens is not None else self.config.max_tokens,
                timeout=self.config.timeout,
            )
            choice = resp.choices[0] if resp.choices else None
            return LLMResult(
                content=choice.message.content if choice else None,
                model=model_name,
                provider=provider,
                usage=dict(resp.usage) if resp.usage else None,
                finish_reason=choice.finish_reason if choice else None,
            )
        except Exception as e:
            return LLMResult(
                content=None,
                model=model_name,
                provider=provider,
                error=str(e),
            )

    def structured(
        self,
        messages: list[dict[str, str]],
        response_model: type[BaseModel],
        *,
        model: str | None = None,
        temperature: float | None = None,
    ) -> BaseModel | None:
        try:
            self._ensure_client()
        except ImportError:
            return None
        provider, model_name = self._parse_model(model or self.config.model)
        full_model = f"{provider}:{model_name}"

        if self._instructor_client is None:
            try:
                import instructor

                self._instructor_client = instructor.patch(
                    self._client,
                    mode=instructor.Mode.TOOLS,
                )
            except ImportError:
                raise ImportError(
                    "instructor is required for structured outputs. "
                    "Install with: pip install instructor"
                )

        try:
            resp = self._instructor_client.chat.completions.create(
                model=full_model,
                messages=messages,
                response_model=response_model,
                temperature=temperature if temperature is not None else self.config.temperature,
                max_tokens=self.config.max_tokens,
            )
            return resp
        except Exception:
            return None

    def chat_with_retry(
        self,
        messages: list[dict[str, str]],
        *,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> LLMResult:
        import time

        last_error: str | None = None
        for attempt in range(self.config.max_retries):
            result = self.chat(
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            if result.content is not None:
                return result
            last_error = result.error
            if attempt < self.config.max_retries - 1:
                time.sleep(2.0 * (2**attempt))
        return LLMResult(
            content=None,
            model=model or self.config.model,
            provider=self.config.provider,
            error=f"All retries exhausted: {last_error}",
        )

    @staticmethod
    def parse_json_from_llm(raw: str | None) -> dict[str, Any] | list[Any] | None:
        if not raw:
            return None
        import json

        cleaned = raw.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            lines = [line for line in lines if not line.strip().startswith("```")]
            cleaned = "\n".join(lines)
        match = re.search(r"(\{.*\}|\[.*\])", cleaned, re.DOTALL)
        if match:
            cleaned = match.group(1)
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            return None
