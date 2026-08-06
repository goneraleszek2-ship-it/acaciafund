"""Tests for scripts/enrich.py — Research Enrichment Engine.

Tests ResearchEnricher: SQI calculation, tag extraction, enrichment pipeline,
LLM retry helper, and JSON parsing.
"""

from __future__ import annotations

import time as _time
from datetime import datetime, timedelta, timezone
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

# Must mock sibling module import before importing enrich
_registry_utils_mock = MagicMock()
_registry_utils_mock.load_registry.return_value = {"content": []}
_registry_utils_mock.save_registry.return_value = None

with patch.dict("sys.modules", {"_registry_utils": _registry_utils_mock}):
    import scripts.enrich as _enrich

ResearchEnricher = _enrich.ResearchEnricher
CONCEPT_PATTERNS = _enrich.CONCEPT_PATTERNS
SOURCE_SCORES = _enrich.SOURCE_SCORES
TEMPORAL_HALF_LIFE = _enrich.TEMPORAL_HALF_LIFE
W_SOURCE_AUTHORITY = _enrich.W_SOURCE_AUTHORITY
W_TEMPORAL_DECAY = _enrich.W_TEMPORAL_DECAY
W_INFO_DENSITY = _enrich.W_INFO_DENSITY
SQI_MIN = _enrich.SQI_MIN
SQI_MAX = _enrich.SQI_MAX

from tests.fixtures.ingestion_mocks import make_mock_llm_client  # noqa: E402

# =========================================================================
# ResearchEnricher.__init__
# =========================================================================


class TestResearchEnricherInit:
    def test_infer_mode_false_does_not_init_memory(self) -> None:
        enricher = ResearchEnricher(infer_mode=False)
        assert enricher.infer_mode is False
        assert enricher._memory is None
        assert not hasattr(enricher, "_llm_client") or enricher._llm_client is None

    def test_infer_mode_true_without_api_key_falls_back(self) -> None:
        with patch.dict("os.environ", {}, clear=True):
            enricher = ResearchEnricher(infer_mode=True)
        assert enricher.infer_mode is False

    def test_infer_mode_true_with_api_key_attempts_init(self) -> None:
        pytest.importorskip("mem0")  # requires mem0 installed; falls back gracefully otherwise
        with (
            patch.dict("os.environ", {"NVIDIA_API_KEY": "test-key-123"}),
            patch("mem0.Memory", return_value=MagicMock()),
            patch("openai.OpenAI", return_value=MagicMock()),
        ):
            enricher = ResearchEnricher(infer_mode=True)
        assert enricher.infer_mode is True
        assert enricher._memory is not None
        assert enricher._llm_client is not None

    def test_infer_mode_import_error_falls_back(self) -> None:
        import types
        fake_mem0 = types.ModuleType("mem0")
        with (
            patch.dict("os.environ", {"NVIDIA_API_KEY": "test-key-123"}),
            patch.dict("sys.modules", {"mem0": fake_mem0}),
        ):
            enricher = ResearchEnricher(infer_mode=True)
        assert enricher.infer_mode is False


# =========================================================================
# calculate_sqi
# =========================================================================


class TestCalculateSQI:
    def test_basic_sqi_with_arxiv_source(self) -> None:
        enricher = ResearchEnricher(infer_mode=False)
        item: dict[str, Any] = {
            "source_breakdown": {"arxiv": 1},
            "date_str": datetime.now(timezone.utc).isoformat(),
            "tags": ["aml", "machine-learning", "dataops"],
            "description": "A detailed " * 20 + "quality compliance regulatory framework "
                           "algorithm formula protocol convergence predictive distributed "
                           "optimization governance surveillance latency standardization",
            "title": "Test Article",
        }
        sqi = enricher.calculate_sqi(item)
        assert SQI_MIN <= sqi <= SQI_MAX

    def test_sqi_with_hn_source_lower_authority(self) -> None:
        enricher = ResearchEnricher(infer_mode=False)
        item: dict[str, Any] = {
            "source_breakdown": {"hn": 1},
            "date_str": datetime.now(timezone.utc).isoformat(),
            "tags": ["test"],
            "description": "Short.",
            "title": "Test",
        }
        sqi = enricher.calculate_sqi(item)
        assert sqi > 0.0

    def test_sqi_empty_source_breakdown_uses_content_type_default(self) -> None:
        enricher = ResearchEnricher(infer_mode=False)
        item: dict[str, Any] = {
            "content_type": "research",
            "date_str": datetime.now(timezone.utc).isoformat(),
            "tags": [],
            "description": "",
            "title": "Test",
        }
        sqi = enricher.calculate_sqi(item)
        assert sqi > 0.0

    def test_sqi_clamped_to_min(self) -> None:
        enricher = ResearchEnricher(infer_mode=False)
        item: dict[str, Any] = {
            "source_breakdown": {},
            "date_str": "2000-01-01T00:00:00Z",
            "tags": [],
            "description": "",
            "title": "",
        }
        sqi = enricher.calculate_sqi(item)
        assert sqi >= SQI_MIN

    def test_sqi_clamped_to_max(self) -> None:
        enricher = ResearchEnricher(infer_mode=False)
        item: dict[str, Any] = {
            "source_breakdown": {"arxiv": 100},
            "date_str": datetime.now(timezone.utc).isoformat(),
            "tags": ["a", "b", "c", "d", "e", "f", "g"],
            "description": "high quality " * 30
                           + "compliance regulatory governance framework algorithm "
                           + "formula protocol convergence predictive distributed "
                           + "optimization surveillance latency standardization quality",
            "title": "Comprehensive Research Article About Frameworks",
        }
        sqi = enricher.calculate_sqi(item)
        assert sqi <= SQI_MAX
        assert sqi > 0.8


# =========================================================================
# _score_source_authority
# =========================================================================


class TestScoreSourceAuthority:
    def test_arxiv_returns_high_score(self) -> None:
        enricher = ResearchEnricher(infer_mode=False)
        score = enricher._score_source_authority(
            {"source_breakdown": {"arxiv": 1}},
        )
        assert score == SOURCE_SCORES["arxiv"]

    def test_hn_returns_lower_score(self) -> None:
        enricher = ResearchEnricher(infer_mode=False)
        score = enricher._score_source_authority(
            {"source_breakdown": {"hn": 1}},
        )
        assert score == SOURCE_SCORES["hn"]

    def test_mixed_sources_weighted_average(self) -> None:
        enricher = ResearchEnricher(infer_mode=False)
        score = enricher._score_source_authority(
            {"source_breakdown": {"arxiv": 1, "hn": 1}},
        )
        expected = (SOURCE_SCORES["arxiv"] + SOURCE_SCORES["hn"]) / 2
        assert score == pytest.approx(expected)

    def test_unknown_source_gets_default_0_40(self) -> None:
        enricher = ResearchEnricher(infer_mode=False)
        score = enricher._score_source_authority(
            {"source_breakdown": {"unknown-source": 1}},
        )
        assert score == pytest.approx(0.40)

    def test_no_source_breakdown_uses_content_type(self) -> None:
        enricher = ResearchEnricher(infer_mode=False)
        score_research = enricher._score_source_authority(
            {"content_type": "research"},
        )
        score_learn = enricher._score_source_authority(
            {"content_type": "learn"},
        )
        score_other = enricher._score_source_authority(
            {"content_type": "blog"},
        )
        assert score_research == 0.60
        assert score_learn == 0.70
        assert score_other == 0.50


# =========================================================================
# _score_temporal_recency
# =========================================================================


class TestScoreTemporalRecency:
    def test_today_item_scores_one(self) -> None:
        enricher = ResearchEnricher(infer_mode=False)
        score = enricher._score_temporal_recency(
            {"date_str": datetime.now(timezone.utc).isoformat()},
        )
        assert score == pytest.approx(1.0, abs=0.01)

    def test_old_item_scores_low(self) -> None:
        enricher = ResearchEnricher(infer_mode=False)
        old_date = (datetime.now(timezone.utc) - timedelta(days=365)).isoformat()
        score = enricher._score_temporal_recency({"date_str": old_date})
        expected = 2 ** (-365.0 / TEMPORAL_HALF_LIFE)
        assert score == pytest.approx(expected, abs=0.01)

    def test_no_date_returns_0_5(self) -> None:
        enricher = ResearchEnricher(infer_mode=False)
        score = enricher._score_temporal_recency({})
        assert score == 0.50

    def test_invalid_date_returns_0_5(self) -> None:
        enricher = ResearchEnricher(infer_mode=False)
        score = enricher._score_temporal_recency(
            {"date_str": "not-a-date"},
        )
        assert score == 0.50

    def test_falls_back_to_created_at(self) -> None:
        enricher = ResearchEnricher(infer_mode=False)
        score = enricher._score_temporal_recency(
            {"created_at": datetime.now(timezone.utc).isoformat()},
        )
        assert score == pytest.approx(1.0, abs=0.01)

    def test_exponential_decay_halves_after_one_halflife(self) -> None:
        enricher = ResearchEnricher(infer_mode=False)
        old_date = (datetime.now(timezone.utc) - timedelta(days=TEMPORAL_HALF_LIFE)).isoformat()
        score = enricher._score_temporal_recency({"date_str": old_date})
        assert score == pytest.approx(0.5, abs=0.01)


# =========================================================================
# extract_semantic_tags (deterministic mode)
# =========================================================================


class TestExtractSemanticTags:
    def test_deterministic_matches_concept_patterns(self) -> None:
        enricher = ResearchEnricher(infer_mode=False)
        tags = enricher.extract_semantic_tags(
            title="Machine Learning for AML and KYC Compliance",
            description="A study of anti-money laundering techniques using pipeline orchestration.",
        )
        assert "aml" in tags
        assert "machine-learning" in tags
        assert "dataops" in tags

    def test_deterministic_no_match_returns_existing_tags(self) -> None:
        enricher = ResearchEnricher(infer_mode=False)
        tags = enricher.extract_semantic_tags(
            title="Completely Unrelated Content",
            description="Nothing matches any pattern.",
            existing_tags=["custom-existing-tag"],
        )
        assert "custom-existing-tag" in tags

    def test_deterministic_preserves_existing_and_adds_new(self) -> None:
        enricher = ResearchEnricher(infer_mode=False)
        tags = enricher.extract_semantic_tags(
            title="Data Pipeline with Kafka Streaming",
            description="Building real-time data pipelines.",
            existing_tags=["dataops"],
        )
        assert tags.count("dataops") == 1
        assert "dataops" in tags
        assert "streaming" in tags

    def test_deterministic_returns_at_most_10_tags(self) -> None:
        enricher = ResearchEnricher(infer_mode=False)
        many_patterns = " ".join(
            t for p, t in CONCEPT_PATTERNS[:15]
            for _ in range(1)
        )
        tags = enricher.extract_semantic_tags(
            title=many_patterns,
            description=many_patterns,
        )
        assert len(tags) <= 10


# =========================================================================
# _llm_call
# =========================================================================


class TestLlmCall:
    _MODEL = "test-model"

    def _make_enricher(self) -> ResearchEnricher:
        enricher = ResearchEnricher(infer_mode=False)
        enricher._llm_client = None  # type: ignore[reportAttributeAccessIssue]
        enricher._llm_model = self._MODEL
        return enricher

    def test_no_client_returns_none(self) -> None:
        enricher = self._make_enricher()
        result = enricher._llm_call("system", "user")
        assert result is None

    def test_successful_call_returns_content(self) -> None:
        enricher = self._make_enricher()
        enricher._llm_client = make_mock_llm_client("Hello response")
        result = enricher._llm_call("system", "user")
        assert result == "Hello response"

    def test_retry_on_failure_then_succeeds(self) -> None:
        enricher = self._make_enricher()
        client = MagicMock()
        responses = [
            Exception("Rate limited"),
            Exception("Server error"),
            MagicMock(choices=[MagicMock(message=MagicMock(content="Success!"))]),
        ]
        client.chat.completions.create.side_effect = responses
        enricher._llm_client = client

        with patch.object(_time, "sleep") as mock_sleep:
            result = enricher._llm_call(
                "system", "user",
                max_retries=3, base_delay=0.01,
            )

        assert result == "Success!"
        assert client.chat.completions.create.call_count == 3
        assert mock_sleep.call_count == 2

    def test_max_retries_exhausted_returns_none(self) -> None:
        enricher = self._make_enricher()
        client = MagicMock()
        client.chat.completions.create.side_effect = Exception("Always fails")
        enricher._llm_client = client

        with patch.object(_time, "sleep") as mock_sleep:
            result = enricher._llm_call(
                "system", "user",
                max_retries=2, base_delay=0.01,
            )

        assert result is None
        assert client.chat.completions.create.call_count == 2
        assert mock_sleep.call_count == 1

    def test_exponential_backoff_delays(self) -> None:
        enricher = self._make_enricher()
        client = MagicMock()
        client.chat.completions.create.side_effect = Exception("fail")
        enricher._llm_client = client
        delays: list[float] = []

        def capture_sleep(delay: float) -> None:
            delays.append(delay)

        with patch.object(_time, "sleep", side_effect=capture_sleep):
            enricher._llm_call(
                "system", "user",
                max_retries=4, base_delay=1.0,
            )

        assert delays == [1.0, 2.0, 4.0]

    def test_empty_response_stripped(self) -> None:
        enricher = self._make_enricher()
        client = MagicMock()
        client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="  "))],
        )
        enricher._llm_client = client
        result = enricher._llm_call("system", "user")
        assert result == ""


# =========================================================================
# _parse_llm_json
# =========================================================================


class TestParseLlmJson:
    def test_none_input_returns_none(self) -> None:
        assert ResearchEnricher._parse_llm_json("") is None

    def test_clean_json_array(self) -> None:
        result = ResearchEnricher._parse_llm_json('["tag1", "tag2", "tag3"]')
        assert result == ["tag1", "tag2", "tag3"]

    def test_clean_json_object(self) -> None:
        result = ResearchEnricher._parse_llm_json('{"key": "value"}')
        assert result == {"key": "value"}

    def test_markdown_fences_stripped(self) -> None:
        raw = '```json\n["tag1", "tag2"]\n```'
        result = ResearchEnricher._parse_llm_json(raw)
        assert result == ["tag1", "tag2"]

    def test_markdown_fences_without_language(self) -> None:
        raw = '```\n{"key": 42}\n```'
        result = ResearchEnricher._parse_llm_json(raw)
        assert result == {"key": 42}

    def test_invalid_json_returns_none(self) -> None:
        result = ResearchEnricher._parse_llm_json("this is not json")
        assert result is None

    def test_whitespace_around_json_is_handled(self) -> None:
        result = ResearchEnricher._parse_llm_json(' \n\n ["a", "b"] \n\n')
        assert result == ["a", "b"]

    def test_mixed_fences_and_extra_text_returns_none(self) -> None:
        raw = "Here is the result:\n```\n[1, 2, 3]\n```\nEnd."
        result = ResearchEnricher._parse_llm_json(raw)
        assert result is None


# =========================================================================
# enrich_item
# =========================================================================


class TestEnrichItem:
    def test_enrich_sets_all_fields_deterministic(self) -> None:
        enricher = ResearchEnricher(infer_mode=False)
        item: dict[str, Any] = {
            "slug": "test-item",
            "title": "AML Detection with Machine Learning",
            "description": "A paper about using ML for detecting suspicious transactions.",
            "body_html": "<p>Full content here.</p>",
            "tags": ["aml"],
            "source_breakdown": {"arxiv": 1},
            "date_str": datetime.now(timezone.utc).isoformat(),
        }
        result = enricher.enrich_item(item)

        assert result["enriched"] is True
        assert "enriched_at" in result
        assert "reading_time" in result
        assert result["reading_time"] >= 1
        assert "sqi" in result
        assert isinstance(result["sqi"], float)
        assert SQI_MIN <= result["sqi"] <= SQI_MAX
        assert "aml" in result["tags"]
        assert "enriched" in result

    def test_enrich_preserves_existing_sqi(self) -> None:
        enricher = ResearchEnricher(infer_mode=False)
        item: dict[str, Any] = {
            "slug": "test-item",
            "title": "Test Article",
            "description": "Description text.",
            "body_html": "<p>Body</p>",
            "tags": ["aml"],
            "sqi": 0.42,
            "source_breakdown": {"arxiv": 1},
            "date_str": datetime.now(timezone.utc).isoformat(),
        }
        result = enricher.enrich_item(item)
        assert result["sqi"] == 0.42

    def test_enrich_sets_sqi_when_absent(self) -> None:
        enricher = ResearchEnricher(infer_mode=False)
        item: dict[str, Any] = {
            "slug": "test-item",
            "title": "Test Article",
            "description": "Description here.",
            "body_html": "<p>Body</p>",
            "tags": ["aml"],
            "source_breakdown": {"arxiv": 1},
            "date_str": datetime.now(timezone.utc).isoformat(),
        }
        assert "sqi" not in item
        result = enricher.enrich_item(item)
        assert "sqi" in result
        assert result["sqi"] is not None
        assert isinstance(result["sqi"], float)

    def test_enrich_reading_time_based_on_body(self) -> None:
        enricher = ResearchEnricher(infer_mode=False)
        long_body = "word " * 500
        item: dict[str, Any] = {
            "slug": "test",
            "title": "Long Article",
            "description": "Desc",
            "body_html": long_body,
            "tags": [],
        }
        result = enricher.enrich_item(item)
        assert result["reading_time"] >= 2

    def test_enrich_reading_time_minimum_one(self) -> None:
        enricher = ResearchEnricher(infer_mode=False)
        item: dict[str, Any] = {
            "slug": "test",
            "title": "Tiny Article",
            "description": "Desc",
            "body_html": "<p>Hi</p>",
            "tags": [],
        }
        result = enricher.enrich_item(item)
        assert result["reading_time"] == 1

    def test_enriched_at_has_zulu_format(self) -> None:
        enricher = ResearchEnricher(infer_mode=False)
        item: dict[str, Any] = {
            "slug": "test",
            "title": "Test",
            "description": "Desc",
            "body_html": "",
            "tags": [],
        }
        result = enricher.enrich_item(item)
        assert result["enriched_at"].endswith("Z")
        assert "T" in result["enriched_at"]

    def test_enrich_preserves_existing_bloom_questions(self) -> None:
        enricher = ResearchEnricher(infer_mode=False)
        existing_bloom = [{"level": "remember", "question": "What is X?"}]
        item: dict[str, Any] = {
            "slug": "test",
            "title": "Test",
            "description": "Desc",
            "body_html": "",
            "tags": [],
            "bloom_questions": existing_bloom,
        }
        result = enricher.enrich_item(item)
        assert result["bloom_questions"] == existing_bloom
