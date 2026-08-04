"""Tests for tag→subcategory mapping, category backfill, and the news pipeline.

Covers:
  - TAG_TO_SUBCATEGORY / category_from_tags (scripts.knowledge_ingester)
  - scripts/backfill_categories.py — categorize_item + validate_categories
  - scripts/fetch_news.py — RSS parsing helpers + GDELT item mapping
  - core/fetch.py — GDELT article parsing (network mocked)

Contract tests: verify function promises, not internal implementation.
"""

import json
from collections import Counter
from unittest import mock

import pytest

from config import PILLAR_SUBCATEGORIES
from scripts.backfill_categories import categorize_item, validate_categories
from scripts.fetch_news import (
    _dedupe,
    _norm_url,
    _parse_date,
    _parse_rss,
    fetch_gdelt_items,
)
from scripts.knowledge_ingester import (
    TAG_TO_SUBCATEGORY,
    _PILLAR_BASE_TAGS,
    category_from_tags,
)

RSS_FIXTURE = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel><title>Test</title>
<item><title>AML update on sanctions</title><link>https://example.com/1</link><pubDate>Mon, 03 Aug 2026 10:00:00 GMT</pubDate></item>
<item><title>Data pipeline patterns</title><link>https://example.com/2</link><pubDate>Mon, 03 Aug 2026 11:00:00 GMT</pubDate></item>
<item><title>Duplicate</title><link>https://example.com/1</link><pubDate>Mon, 03 Aug 2026 12:00:00 GMT</pubDate></item>
</channel></rss>"""

GDELT_FIXTURE = {
    "articles": [
        {
            "title": "FinCEN sanctions action",
            "url": "https://example.com/fincen",
            "seendate": "20260804T103000Z",
            "domain": "example.com",
            "language": "English",
        },
        {"title": "", "url": "https://example.com/empty", "seendate": "", "domain": "x"},
        {"title": "No URL", "url": "", "seendate": "20260804T103000Z", "domain": "x"},
    ]
}


# ── category_from_tags / TAG_TO_SUBCATEGORY ──


class TestTagToSubcategory:
    def test_all_targets_exist_in_pillar_taxonomy(self):
        for pillar_slug, mapping in TAG_TO_SUBCATEGORY.items():
            registry_key = {"aml": "aml", "data": "data-engineering", "market": "stock"}[pillar_slug]
            taxonomy = PILLAR_SUBCATEGORIES[registry_key]
            for target in mapping.values():
                assert target in taxonomy, f"{pillar_slug}: {target} not in taxonomy"

    def test_all_tags_covered(self):
        from scripts.knowledge_ingester import AML_TAGS, DATA_TAGS, MARKET_TAGS

        for pillar_slug, tag_map in {
            "aml": AML_TAGS, "data": DATA_TAGS, "market": MARKET_TAGS,
        }.items():
            for tag in tag_map:
                assert tag in TAG_TO_SUBCATEGORY[pillar_slug], f"unmapped tag {pillar_slug}.{tag}"

    def test_specific_tag_beats_base_tag(self):
        assert category_from_tags(["aml", "transaction-monitoring"], "aml") == "transaction-monitoring"
        assert category_from_tags(["dataops", "stream-processing"], "data") == "streaming"
        assert category_from_tags(["market-microstructure", "quantitative-modeling"], "market") == "quantitative-methods"

    def test_base_tag_fallback(self):
        assert category_from_tags(["aml"], "aml") == "cdd-kyc"
        assert category_from_tags(["dataops"], "data") == "pipeline-architecture"
        assert category_from_tags(["market-microstructure"], "market") == "market-microstructure"

    def test_unknown_pillar_falls_back(self):
        assert category_from_tags([], "nope") == "blog"


# ── backfill_categories ──


class TestBackfillCategories:
    def test_research_item_gets_category(self):
        item = {
            "content_type": "research",
            "pillar": "aml",
            "category": "blog",
            "title": "FinCEN issues new suspicious activity monitoring guidance",
            "description": "Transaction monitoring and SAR filing updates.",
            "tags": ["aml", "transaction-monitoring"],
        }
        new_cat, new_tags = categorize_item(item)
        assert new_cat == "transaction-monitoring"
        assert "aml" in new_tags and "transaction-monitoring" in new_tags

    def test_learn_and_knowledge_untouched(self):
        learn = {"content_type": "learn", "pillar": "aml", "category": "learn", "title": "x"}
        assert categorize_item(learn) == (None, None)
        kn = {"content_type": "knowledge", "pillar": "aml", "category": "foundations", "title": "x"}
        assert categorize_item(kn) == (None, None)

    def test_already_canonical_untouched(self):
        item = {"content_type": "research", "pillar": "aml", "category": "regtech", "title": "x"}
        assert categorize_item(item) == (None, None)

    def test_validate_categories_clean(self):
        data = {"content": [
            {"content_type": "research", "pillar": "aml", "category": "cdd-kyc"},
            {"content_type": "learn", "pillar": "stock", "category": "learn"},
        ]}
        assert validate_categories(data) == Counter()

    def test_validate_categories_reports_bad(self):
        data = {"content": [
            {"content_type": "research", "pillar": "aml", "category": "bogus"},
        ]}
        bad = validate_categories(data)
        assert bad[("aml", "research", "bogus")] == 1


# ── fetch_news helpers ──


class TestNewsHelpers:
    def test_parse_rss_items_and_dedup(self):
        items = _parse_rss(RSS_FIXTURE)
        assert len(items) == 3
        assert items[0]["title"] == "AML update on sanctions"
        deduped = _dedupe(items)
        assert len(deduped) == 2

    def test_norm_url(self):
        assert _norm_url("https://Example.com/a?x=1") == "https://example.com/a"
        assert _norm_url("https://example.com/a/") == "https://example.com/a"

    def test_parse_date(self):
        dt = _parse_date("Mon, 03 Aug 2026 10:00:00 GMT")
        assert dt is not None and dt.year == 2026 and dt.month == 8
        assert _parse_date("") is None
        assert _parse_date("garbage") is None


class TestGdeltNews:
    @mock.patch("core.fetch.fetch_gdelt_articles", return_value=GDELT_FIXTURE["articles"])
    def test_fetch_gdelt_items_maps_fields(self, _mocked):
        items = fetch_gdelt_items()
        assert len(items) == 3  # malformed entries still flow to scoring/dedup
        first = items[0]
        assert first["title"] == "FinCEN sanctions action"
        assert first["source_type"] == "gdelt"
        assert first["published_at"] == "2026-08-04T10:30:00Z"


# ── core.fetch GDELT parsing (network mocked) ──


class TestFetchGdeltArticles:
    def test_parses_articles(self):
        from core.fetch import fetch_gdelt_articles

        with mock.patch("core.fetch._request", return_value=json.dumps(GDELT_FIXTURE)):
            articles = fetch_gdelt_articles("test query", max_records=5)
        assert len(articles) == 1  # blank title/url dropped
        assert articles[0]["domain"] == "example.com"

    def test_error_returns_empty(self):
        from core.fetch import fetch_gdelt_articles

        with mock.patch("core.fetch._request", return_value=None):
            articles = fetch_gdelt_articles("test query")
        assert articles == []

    def test_bad_json_returns_empty(self):
        from core.fetch import fetch_gdelt_articles

        with mock.patch("core.fetch._request", return_value="<html>not json</html>"):
            articles = fetch_gdelt_articles("test query")
        assert articles == []

    def test_query_includes_english_filter(self):
        from core.fetch import fetch_gdelt_articles, GDELT_DOC_URL

        with mock.patch("core.fetch._request", return_value=json.dumps(GDELT_FIXTURE)) as m:
            fetch_gdelt_articles("inflation", max_records=3)
        url = m.call_args[0][0]
        assert url.startswith(GDELT_DOC_URL)
        assert "sourcelang" in url and "english" in url
        assert "maxrecords=3" in url


# ── knowledge module generator integrity ──


@pytest.fixture(scope="module")
def modules():
    from scripts.generate_knowledge_modules import MODULES

    return MODULES


class TestKnowledgeModules:
    def test_two_per_empty_category(self, modules):
        from collections import Counter

        cats = Counter(m["knowledge_category"] for m in modules)
        assert set(cats) == {
            "advanced-techniques", "best-practices", "market-analysis",
            "strategies", "methodology", "tutorial-code",
        }
        assert all(n == 2 for n in cats.values())

    def test_slugs_unique_and_content_type_knowledge(self, modules):
        slugs = [m["slug"] for m in modules]
        assert len(slugs) == len(set(slugs))
        for m in modules:
            assert m["pillar"] in {"aml", "stock", "data-engineering"}
            assert m.get("description")
            assert len(m["sections"]) >= 2

    def test_generate_body_handles_2_and_3_part_sections(self, modules):
        from scripts.generate_knowledge_modules import generate_body

        for m in modules:
            body = generate_body(m)
            assert body.startswith("<h2>")
            assert body.count("<h2>") == len(m["sections"])
            assert len(body) > 200
