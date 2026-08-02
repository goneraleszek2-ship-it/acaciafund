"""Tests for core/generate.py — post generation helper sections.

Tests target the pure string builders. The heavy `generate_post` pipeline
(scrape → analyze → visuals) is exercised via these helpers plus existing
integration tests; we avoid triggering network scrapes in unit tests.
"""

from core.generate import (
    _build_classification_confidence,
    _build_content_deep_analysis,
    _build_cross_pillar_section,
    _build_trending_section,
)
from core.scraper import _url_key


class TestBuildContentDeepAnalysis:
    def test_empty_signals_returns_empty(self):
        assert _build_content_deep_analysis([], {}, "stock", {}) == ""

    def test_key_entities(self):
        out = _build_content_deep_analysis(
            [], {}, "stock", {"top_entities": ["OpenAI", "NVIDIA", "TSMC"]}
        )
        assert "**Key entities:**" in out
        assert "`OpenAI`" in out
        assert "`TSMC`" in out

    def test_key_numbers(self):
        out = _build_content_deep_analysis([], {}, "aml", {"key_numbers": [("$5B", "ctx"), ("12%", "ctx2")]})
        assert "**Key numbers:** $5B · 12%" in out

    def test_trending(self):
        out = _build_content_deep_analysis(
            [], {}, "aml", {"trending_topics": [{"word": "crypto", "ratio": 3.0}]}
        )
        assert "**Trends:** crypto (3.0x)" in out

    def test_scraped_sentences(self):
        story = {"title": "Deep article", "url": "https://example.com/a"}
        key = _url_key(story["url"])
        scraped = {key: {"facts": {"sentences": ["A fairly long sentence describing the result in detail."]}}}
        out = _build_content_deep_analysis([story], scraped, "stock", {})
        assert "**From articles:**" in out
        assert "A fairly long sentence" in out


class TestBuildCrossPillarSection:
    def test_empty(self):
        assert _build_cross_pillar_section("stock", {}) == ""

    def test_no_connections(self):
        stories = {"stock": [{"title": "Alpha one two three"}], "aml": [{"title": "Beta four five six"}]}
        assert _build_cross_pillar_section("stock", stories) == ""

    def test_connection_detected(self):
        stories = {
            "stock": [{"title": "Machine learning for financial risk models"}],
            "aml": [{"title": "Machine learning for financial risk models assessment"}],
        }
        out = _build_cross_pillar_section("stock", stories)
        assert "Cross-pillar connections" in out
        assert "Compliance" in out
        assert "score: 6" in out


class TestBuildClassificationConfidence:
    def test_zero_total(self):
        assert _build_classification_confidence([], "stock", [], 0) == ""

    def test_full_classification(self):
        stories = [{}, {}, {}]
        pillar_stories = [{}, {}]
        out = _build_classification_confidence(stories, "stock", pillar_stories, 0)
        assert "Classification: 100% (5/5)" in out

    def test_partial_classification(self):
        out = _build_classification_confidence([{}, {}, {}], "stock", [{}, {}], 1)
        assert "Classification: 83% (5/6)" in out
        assert "Pillar share: 40%" in out


class TestBuildTrendingSection:
    def test_empty(self):
        assert _build_trending_section([], {}) == ""

    def test_formats_stories(self):
        stories = [
            {"title": "Alpha", "url": "https://a.com", "points": 100, "hn_url": "https://hn/a"},
            {"title": "Beta", "url": "https://b.com", "points": 50},
        ]
        out = _build_trending_section(stories, {})
        lines = out.splitlines()
        assert lines[0] == "1. [Alpha](https://a.com) ([discussion](https://hn/a)) (100 pts)"
        assert lines[1] == "2. [Beta](https://b.com) (50 pts)"

    def test_limits_to_seven(self):
        stories = [
            {"title": f"Story {i}", "url": f"https://x.com/{i}", "points": 10}
            for i in range(10)
        ]
        assert len(_build_trending_section(stories, {}).splitlines()) == 7
