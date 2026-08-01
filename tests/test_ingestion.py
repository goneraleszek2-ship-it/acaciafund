"""Tests for scripts/knowledge_ingester.py — ingestion pipeline.

Tests pure helper functions, deduplication, and registry operations.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

# Must mock sibling module imports before importing knowledge_ingester
_registry_utils_mock = MagicMock()
_registry_utils_mock.load_registry.return_value = {"content": []}
_registry_utils_mock.save_registry.return_value = None

with patch.dict("sys.modules", {"_registry_utils": _registry_utils_mock}):
    import scripts.knowledge_ingester as _ki

_slugify = _ki._slugify
jaccard_similarity = _ki.jaccard_similarity
score_pillar_relevance = _ki.score_pillar_relevance
_source_to_item = _ki._source_to_item
deduplicate = _ki.deduplicate
prune_and_archive_registry = _ki.prune_and_archive_registry
_existing_slugs = _ki._existing_slugs
_existing_titles = _ki._existing_titles
_existing_urls = _ki._existing_urls

from tests.fixtures.ingestion_mocks import (  # noqa: E402
    MOCK_REGISTRY,
    make_mock_pillar_config,
)

# =========================================================================
# _slugify
# =========================================================================


class TestSlugify:
    def test_basic_text(self) -> None:
        assert _slugify("Hello World") == "hello-world"

    def test_multiple_spaces(self) -> None:
        assert _slugify("Hello   World   Test") == "hello-world-test"

    def test_leading_trailing_whitespace(self) -> None:
        assert _slugify("  Hello World  ") == "hello-world"

    def test_unicode_removed(self) -> None:
        assert _slugify("café étudián") == "caf-tudi-n"

    def test_emoji_removed(self) -> None:
        assert _slugify("emoji 😊 test") == "emoji-test"

    def test_leading_dash_stripped(self) -> None:
        assert _slugify("-hello") == "hello"

    def test_trailing_dash_stripped(self) -> None:
        assert _slugify("hello-") == "hello"

    def test_multiple_dashes_collapsed(self) -> None:
        assert _slugify("hello--world") == "hello-world"

    def test_apostrophe_removed(self) -> None:
        assert _slugify("don't stop") == "dont-stop"

    def test_quotes_removed(self) -> None:
        assert _slugify('"hello" world') == "hello-world"

    def test_max_len_truncation(self) -> None:
        result = _slugify("a" * 100, max_len=10)
        assert len(result) == 10
        assert result == "a" * 10

    def test_max_len_respects_word_boundary_indirectly(self) -> None:
        result = _slugify("hello-world-testing", max_len=12)
        assert result == "hello-world"  # truncated to 12, .rstrip("-")

    def test_max_len_no_trailing_dash(self) -> None:
        result = _slugify("hello-world-", max_len=20)
        assert not result.endswith("-")

    def test_empty_string(self) -> None:
        assert _slugify("") == ""

    def test_only_special_chars(self) -> None:
        assert _slugify("!@#$%^&*()") == ""


# =========================================================================
# jaccard_similarity
# =========================================================================


class TestJaccardSimilarity:
    def test_identical_strings(self) -> None:
        assert jaccard_similarity("hello world", "hello world") == 1.0

    def test_completely_different(self) -> None:
        assert jaccard_similarity("abc def", "ghi jkl") == 0.0

    def test_partial_overlap(self) -> None:
        result = jaccard_similarity("hello world foo", "hello world bar")
        assert result == pytest.approx(2 / 4)

    def test_case_insensitive(self) -> None:
        assert jaccard_similarity("Hello World", "hello world") == 1.0

    def test_first_empty(self) -> None:
        assert jaccard_similarity("", "hello world") == 0.0

    def test_second_empty(self) -> None:
        assert jaccard_similarity("hello world", "") == 0.0

    def test_both_empty(self) -> None:
        assert jaccard_similarity("", "") == 0.0

    def test_single_word(self) -> None:
        assert jaccard_similarity("hello", "hello") == 1.0

    def test_no_common_words(self) -> None:
        result = jaccard_similarity("machine learning", "financial compliance")
        assert result == 0.0


# =========================================================================
# score_pillar_relevance
# =========================================================================


class TestScorePillarRelevance:
    def test_keyword_match_returns_positive_score(self) -> None:
        config = make_mock_pillar_config("aml")
        score, tags = score_pillar_relevance(
            "This paper discusses AML compliance and machine learning techniques.",
            config,
        )
        assert score > 0.0
        assert "aml" in tags

    def test_no_match_returns_zero(self) -> None:
        config = make_mock_pillar_config("aml")
        score, tags = score_pillar_relevance(
            "This is completely unrelated content about cooking recipes.",
            config,
        )
        assert score == 0.0
        assert tags == []

    def test_category_boost_increases_score(self) -> None:
        config = make_mock_pillar_config("aml")
        text = (
            "AML compliance is an important topic in modern financial "
            "institutions that deal with cross-border transactions and "
            "regulatory requirements across multiple jurisdictions"
        )
        score_no_cat, _ = score_pillar_relevance(text, config)
        score_with_cat, _ = score_pillar_relevance(
            text, config, categories=["cs.CR"],
        )
        assert score_with_cat > score_no_cat

    def test_category_boost_only_no_keyword_hits(self) -> None:
        config = make_mock_pillar_config("data")
        score, tags = score_pillar_relevance(
            "Unrelated text with no keyword matches at all",
            config,
            categories=["cs.DB"],
        )
        assert score > 0.0
        assert tags == []

    def test_multiple_tags_detected(self) -> None:
        config = make_mock_pillar_config("aml")
        _, tags = score_pillar_relevance(
            "Machine learning for AML transaction monitoring and anomaly detection.",
            config,
        )
        assert "aml" in tags
        assert "machine-learning" in tags
        assert "transaction-monitoring" in tags

    def test_score_capped_at_one(self) -> None:
        config = make_mock_pillar_config("aml")
        text = "aml " * 500
        score, _ = score_pillar_relevance(text, config)
        assert score <= 1.0

    def test_different_pillar_scoring(self) -> None:
        config = make_mock_pillar_config("data")
        score_aml, _ = score_pillar_relevance(
            "AML compliance and KYC regulations",
            config,
        )
        score_data, _ = score_pillar_relevance(
            "Data pipeline orchestration with Kafka streaming",
            config,
        )
        assert score_data > score_aml


# =========================================================================
# _source_to_item
# =========================================================================


class TestSourceToItem:
    def test_empty_title_returns_none(self) -> None:
        config = make_mock_pillar_config("aml")
        result = _source_to_item(
            {"_detected_tags": []},
            config,
            source_key="arxiv",
            title="",
            url="https://example.com",
        )
        assert result is None

    def test_minimal_data_returns_valid_item(self) -> None:
        config = make_mock_pillar_config("aml")
        result = _source_to_item(
            {"_detected_tags": ["aml"]},
            config,
            source_key="arxiv",
            title="Test Title",
        )
        assert result is not None
        assert result["title"] == "Test Title"
        assert result["slug"] is not None
        assert result["pillar"] == "aml"
        assert result["content_type"] == "research"
        assert result["sqi"] is None
        assert result["enriched"] is False
        assert result["slug"].startswith("compliance/research/")

    def test_base_tag_inserted_when_missing(self) -> None:
        config = make_mock_pillar_config("aml")
        result = _source_to_item(
            {"_detected_tags": ["custom-tag"]},
            config,
            source_key="arxiv",
            title="Test Title",
        )
        assert result is not None
        assert "aml" in result["tags"]
        assert "custom-tag" in result["tags"]

    def test_tags_are_deduplicated(self) -> None:
        config = make_mock_pillar_config("aml")
        result = _source_to_item(
            {"_detected_tags": ["aml", "aml"]},
            config,
            source_key="arxiv",
            title="Test Title",
        )
        assert result is not None
        assert result["tags"].count("aml") == 1

    def test_explicit_tags_override_detected(self) -> None:
        config = make_mock_pillar_config("aml")
        result = _source_to_item(
            {"_detected_tags": ["aml"]},
            config,
            source_key="arxiv",
            title="Test Title",
            tags=["custom-tag"],
        )
        assert result is not None
        assert "custom-tag" in result["tags"]

    def test_slug_uses_pillar_url_mapping(self) -> None:
        config = make_mock_pillar_config("data")
        result = _source_to_item(
            {"_detected_tags": ["dataops"]},
            config,
            source_key="arxiv",
            title="Data Pipeline Test",
        )
        assert result is not None
        assert result["slug"].startswith("data/research/")
        assert result["pillar"] == "data-engineering"

    def test_full_data_populates_all_fields(self) -> None:
        config = make_mock_pillar_config("market")
        result = _source_to_item(
            {"_detected_tags": ["market-microstructure"]},
            config,
            source_key="arxiv",
            title="Market Research Paper",
            url="https://example.com/paper",
            date_str="2026-06-15T00:00:00Z",
            summary="A comprehensive study of market microstructure.",
            body_html="<p>Full text here</p>",
            author="Dr. Smith",
            avg_sqi=0.80,
            score=0.85,
        )
        assert result is not None
        assert result["slug"].startswith("markets/research/")
        assert result["pillar"] == "stock"
        assert result["source_url"] == "https://example.com/paper"
        assert result["date_str"] == "2026-06-15"
        assert result["author"] == "Dr. Smith"
        assert result["source_breakdown"] == {"arxiv": 1}
        assert result["signals"]["avg_sqi"] == 0.80
        assert result["quality_metrics"]["score"] == 0.85

    def test_body_html_fallback_to_summary_paragraph(self) -> None:
        config = make_mock_pillar_config("aml")
        result = _source_to_item(
            {"_detected_tags": []},
            config,
            source_key="arxiv",
            title="Test",
            summary="A short summary.",
        )
        assert result is not None
        assert result["body_html"] == "<p>A short summary.</p>"

    def test_description_truncated_at_300(self) -> None:
        config = make_mock_pillar_config("aml")
        long_summary = "word " * 400
        result = _source_to_item(
            {"_detected_tags": []},
            config,
            source_key="arxiv",
            title="Test",
            summary=long_summary,
        )
        assert result is not None
        assert len(result["description"]) <= 303

    def test_date_str_slug_date_uses_first_10_chars(self) -> None:
        config = make_mock_pillar_config("aml")
        result = _source_to_item(
            {"_detected_tags": []},
            config,
            source_key="arxiv",
            title="Test",
            date_str="2026-06-15T10:30:00Z",
        )
        assert result is not None
        assert result["date_str"] == "2026-06-15"


# =========================================================================
# Deduplication helpers
# =========================================================================


class TestExistingSlugs:
    def test_returns_set_of_slugs(self) -> None:
        result = _existing_slugs(MOCK_REGISTRY)
        assert "compliance/research/aml-machine-learning-2024" in result
        assert "data/research/stream-processing-kafka" in result

    def test_empty_registry(self) -> None:
        assert _existing_slugs({"content": []}) == set()

    def test_missing_content_key(self) -> None:
        assert _existing_slugs({}) == set()

    def test_skips_items_without_slug(self) -> None:
        data = {"content": [{"title": "no slug"}, {"slug": "valid-slug"}]}
        result = _existing_slugs(data)
        assert "valid-slug" in result
        assert "" not in result


class TestExistingUrls:
    def test_returns_set_of_source_urls(self) -> None:
        result = _existing_urls(MOCK_REGISTRY)
        assert "https://arxiv.org/abs/2401.12345" in result

    def test_strips_trailing_slash(self) -> None:
        data = {"content": [{"source_url": "https://example.com/url/"}]}
        result = _existing_urls(data)
        assert "https://example.com/url" in result

    def test_empty_registry(self) -> None:
        assert _existing_urls({"content": []}) == set()

    def test_skips_empty_urls(self) -> None:
        data = {"content": [{"source_url": ""}, {"source_url": "https://valid.com"}]}
        result = _existing_urls(data)
        assert "https://valid.com" in result
        assert "" not in result


class TestExistingTitles:
    def test_returns_lowercased_titles(self) -> None:
        result = _existing_titles(MOCK_REGISTRY)
        assert "aml machine learning 2024" in result

    def test_empty_registry(self) -> None:
        assert _existing_titles({"content": []}) == []

    def test_skips_missing_title(self) -> None:
        data = {"content": [{"slug": "x"}, {"title": "Valid Title"}]}
        result = _existing_titles(data)
        assert "valid title" in result
        assert len(result) == 1


# =========================================================================
# deduplicate
# =========================================================================


class TestDeduplicate:
    def test_empty_registry_all_items_pass(self) -> None:
        config = make_mock_pillar_config("aml")
        items = [
            _source_to_item(
                {"_detected_tags": []}, config,
                source_key="arxiv", title="New Item 1",
            ),
            _source_to_item(
                {"_detected_tags": []}, config,
                source_key="arxiv", title="New Item 2",
            ),
        ]
        assert items[0] is not None
        assert items[1] is not None
        result = deduplicate(items, {"content": []})  # type: ignore[arg-type]
        assert len(result) == 2

    def test_exact_slug_dup_removed(self) -> None:
        registry: dict[str, Any] = {
            "content": [{"slug": "dup-slug", "title": "Original", "source_url": "https://a.com"}],
        }
        items = [
            {
                "slug": "dup-slug",
                "title": "Different Title",
                "source_url": "https://b.com",
            },
        ]
        result = deduplicate(items, registry)
        assert len(result) == 0

    def test_exact_url_dup_removed(self) -> None:
        registry: dict[str, Any] = {
            "content": [
                {
                    "slug": "existing-slug",
                    "title": "Existing",
                    "source_url": "https://example.com/paper",
                },
            ],
        }
        items = [
            {
                "slug": "new-slug",
                "title": "New Title",
                "source_url": "https://example.com/paper",
            },
        ]
        result = deduplicate(items, registry)
        assert len(result) == 0

    def test_exact_title_dup_removed(self) -> None:
        registry: dict[str, Any] = {
            "content": [
                {
                    "slug": "existing-slug",
                    "title": "Exact Title Match",
                    "source_url": "https://a.com",
                },
            ],
        }
        items = [
            {
                "slug": "new-slug",
                "title": "  exact title match  ",
                "source_url": "https://b.com",
            },
        ]
        result = deduplicate(items, registry)
        assert len(result) == 0

    def test_near_duplicate_jaccard_removed(self) -> None:
        registry: dict[str, Any] = {
            "content": [
                {
                    "slug": "existing-slug",
                    "title": "Machine Learning for Anti-Money Laundering Detection",
                    "source_url": "https://a.com",
                },
            ],
        }
        items = [
            {
                "slug": "new-slug",
                "title": "Machine Learning for Anti Money Laundering Detection",
                "source_url": "https://b.com",
            },
        ]
        result = deduplicate(items, registry)
        assert len(result) == 0

    def test_no_dup_all_pass(self) -> None:
        registry: dict[str, Any] = {
            "content": [
                {
                    "slug": "existing",
                    "title": "Existing Title",
                    "source_url": "https://a.com",
                },
            ],
        }
        items = [
            {
                "slug": "new-one",
                "title": "Completely Different Topic",
                "source_url": "https://b.com",
            },
            {
                "slug": "new-two",
                "title": "Another Different Topic Here",
                "source_url": "https://c.com",
            },
        ]
        result = deduplicate(items, registry)
        assert len(result) == 2

    def test_slug_collision_within_batch_adds_uuid(self) -> None:
        registry: dict[str, Any] = {"content": []}
        items = [
            {"slug": "same-slug", "title": "First Item", "source_url": "https://a.com"},
            {"slug": "same-slug", "title": "Second Item", "source_url": "https://b.com"},
        ]
        result = deduplicate(items, registry)
        assert len(result) == 2
        assert result[0]["slug"] == "same-slug"
        assert result[1]["slug"] != "same-slug"
        assert result[1]["slug"].startswith("same-slug-")

    def test_short_title_skips_jaccard_check(self) -> None:
        registry: dict[str, Any] = {
            "content": [
                {
                    "slug": "existing",
                    "title": "hello world",
                    "source_url": "https://a.com",
                },
            ],
        }
        items = [
            {
                "slug": "new",
                "title": "hi",
                "source_url": "https://b.com",
            },
        ]
        result = deduplicate(items, registry)
        assert len(result) == 1


# =========================================================================
# prune_and_archive_registry
# =========================================================================


class TestPruneAndArchiveRegistry:
    def test_under_limit_returns_zero(self) -> None:
        registry: dict[str, Any] = {
            "content": [{"slug": "a"}, {"slug": "b"}],
        }
        with patch.object(_ki, "ROOT", Path("/tmp")):
            count = prune_and_archive_registry(registry, max_active=10)
        assert count == 0

    def test_basic_pruning_archives_oldest(self, tmp_path: Path) -> None:
        now = datetime.now(timezone.utc)
        items: list[dict[str, Any]] = []
        for i in range(5):
            created = (now - timedelta(days=i)).isoformat()
            items.append({
                "slug": f"item-{i}",
                "title": f"Item {i}",
                "created_at": created,
                "source_url": f"https://e.com/{i}",
            })
        registry: dict[str, Any] = {"content": items}

        with patch.object(_ki, "ROOT", tmp_path):
            count = prune_and_archive_registry(registry, max_active=3, max_age_months=60)

        assert count == 2
        assert len(registry["content"]) == 3

    def test_old_items_archived_by_age(self, tmp_path: Path) -> None:
        items: list[dict[str, Any]] = [
            {
                "slug": "old-item",
                "title": "Old",
                "created_at": "2020-01-01T00:00:00Z",
                "source_url": "https://old.com",
            },
            {
                "slug": "new-item",
                "title": "New",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "source_url": "https://new.com",
            },
        ]
        registry: dict[str, Any] = {"content": items}

        with patch.object(_ki, "ROOT", tmp_path):
            count = prune_and_archive_registry(registry, max_active=1, max_age_months=1)

        assert count == 1
        assert len(registry["content"]) == 1
        assert registry["content"][0]["slug"] == "new-item"

    def test_archive_writes_to_file(self, tmp_path: Path) -> None:
        items: list[dict[str, Any]] = [
            {
                "slug": "old",
                "title": "Old",
                "created_at": "2020-01-01T00:00:00Z",
                "source_url": "https://old.com",
            },
        ]
        registry: dict[str, Any] = {"content": items}
        archive_dir = tmp_path / "data" / "registry_archive"
        archive_dir.mkdir(parents=True, exist_ok=True)

        with patch.object(_ki, "ROOT", tmp_path):
            count = prune_and_archive_registry(registry, max_active=0, max_age_months=1)

        assert count == 1
        archive_files = list(archive_dir.glob("*.json"))
        assert len(archive_files) == 1
        archived = json.loads(archive_files[0].read_text(encoding="utf-8"))
        assert len(archived["items"]) == 1
        assert archived["items"][0]["slug"] == "old"
