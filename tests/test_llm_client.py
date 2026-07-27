"""Tests for core/llm_client.py"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.llm_client import AcaciaLLMClient, LLMConfig, LLMResult


class TestLLMConfig:
    def test_defaults(self):
        cfg = LLMConfig()
        assert cfg.provider == "openai"
        assert cfg.model == "gpt-4o-mini"
        assert cfg.temperature == 0.4
        assert cfg.max_tokens == 2048
        assert cfg.max_retries == 3

    def test_custom_values(self):
        cfg = LLMConfig(provider="anthropic", model="claude-3-haiku-20240307", temperature=0.0)
        assert cfg.provider == "anthropic"
        assert cfg.model == "claude-3-haiku-20240307"
        assert cfg.temperature == 0.0


class TestAcaciaLLMClient:
    def test_init_without_api_key_returns_error(self):
        client = AcaciaLLMClient(config=LLMConfig(model="gpt-4o-mini"))
        result = client.chat(messages=[{"role": "user", "content": "hello"}])
        assert isinstance(result, LLMResult)
        assert result.content is None
        assert result.error is not None

    def test_parse_json_from_llm_with_code_fence(self):
        raw = """```json
{"key": "value", "number": 42}
```"""
        result = AcaciaLLMClient.parse_json_from_llm(raw)
        assert result == {"key": "value", "number": 42}

    def test_parse_json_from_llm_plain(self):
        raw = '{"name": "test", "items": [1, 2, 3]}'
        result = AcaciaLLMClient.parse_json_from_llm(raw)
        assert result == {"name": "test", "items": [1, 2, 3]}

    def test_parse_json_from_llm_array(self):
        raw = '[{"a": 1}, {"b": 2}]'
        result = AcaciaLLMClient.parse_json_from_llm(raw)
        assert result == [{"a": 1}, {"b": 2}]

    def test_parse_json_from_llm_empty_returns_none(self):
        assert AcaciaLLMClient.parse_json_from_llm(None) is None
        assert AcaciaLLMClient.parse_json_from_llm("") is None

    def test_parse_json_from_llm_invalid_returns_none(self):
        assert AcaciaLLMClient.parse_json_from_llm("not json at all") is None

    def test_chat_with_retry_exhausts(self):
        client = AcaciaLLMClient(config=LLMConfig(model="gpt-4o-mini", max_retries=2))
        result = client.chat_with_retry(
            messages=[{"role": "user", "content": "hi"}],
        )
        assert result.content is None
        assert "retries exhausted" in (result.error or "")

    def test_parse_model_with_provider_prefix(self):
        client = AcaciaLLMClient()
        provider, model = client._parse_model("anthropic:claude-3-haiku-20240307")
        assert provider == "anthropic"
        assert model == "claude-3-haiku-20240307"

    def test_parse_model_without_provider_prefix(self):
        client = AcaciaLLMClient(config=LLMConfig(provider="groq"))
        provider, model = client._parse_model("mixtral-8x7b-32768")
        assert provider == "groq"
        assert model == "mixtral-8x7b-32768"
