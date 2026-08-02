"""Tests for scripts/source_verification.py — source classification, verification, scoring."""

import pytest

from scripts.source_verification import (
    analyze_article_sources,
    classify_source_type,
    compute_article_source_score,
    compute_source_score,
    extract_domain,
    verify_source,
)


class TestExtractDomain:
    def test_protocol_stripped(self):
        assert extract_domain("https://arxiv.org/abs/2401.0001") == "arxiv.org"

    def test_www_stripped(self):
        assert extract_domain("http://www.example.com/path") == "example.com"

    def test_no_protocol(self):
        assert extract_domain("example.com/x") == "example.com"

    def test_empty_url(self):
        assert extract_domain("") == "unknown"


class TestClassifySourceType:
    def test_academic(self):
        assert classify_source_type(url="https://www.sciencedirect.com/science/article/pii/S1") == (
            "academic",
            0.95,
        )

    def test_inspiration_priority(self):
        assert classify_source_type(url="https://arxiv.org/abs/2401.0001") == ("inspiration", 0.95)

    def test_official_gov(self):
        assert classify_source_type(url="https://www.treasury.gov/news") == ("official", 0.9)

    def test_official_org(self):
        assert classify_source_type(url="https://www.icann.org")[0] == "official"

    def test_industry_report(self):
        assert classify_source_type(url="https://www.mckinsey.com/industries") == (
            "industry_report",
            0.85,
        )

    def test_engineering_blog(self):
        assert classify_source_type(url="https://medium.com/foo")[0] == "engineering_blog"

    def test_news(self):
        assert classify_source_type(url="https://www.nytimes.com/2026/07/01")[0] == "news"

    def test_social(self):
        assert classify_source_type(url="https://twitter.com/acaciafund")[0] == "social"

    def test_research_content_type(self):
        assert classify_source_type(url="https://example.com/x", content_type="research") == (
            "research",
            0.85,
        )

    def test_learn_content_type(self):
        assert classify_source_type(url="https://example.com/x", content_type="learn") == (
            "educational",
            0.75,
        )

    def test_knowledge_content_type(self):
        assert classify_source_type(url="https://example.com/x", content_type="knowledge") == (
            "reference",
            0.8,
        )

    def test_ai_tagged(self):
        assert classify_source_type(url="https://example.com/x", tags=["ai"]) == (
            "ai_generated",
            0.6,
        )

    def test_regulatory_title(self):
        assert classify_source_type(title="AML compliance strategies") == ("regulatory", 0.8)

    def test_unknown(self):
        assert classify_source_type(url="https://example.com/x") == ("unknown", 0.5)


class TestVerifySource:
    @pytest.mark.parametrize(
        "source_type",
        [
            "academic",
            "official",
            "industry_report",
            "engineering_blog",
            "news",
            "research",
            "educational",
            "reference",
            "regulatory",
            "inspiration",
        ],
    )
    def test_verified_types(self, source_type):
        result = verify_source(source_type)
        assert result["verified"] is True
        assert result["verification_status"] == "verified"
        assert isinstance(result["evidence"], list) and result["evidence"]

    @pytest.mark.parametrize("source_type", ["ai_generated", "social", "unknown"])
    def test_unverified_types(self, source_type):
        result = verify_source(source_type)
        assert result["verified"] is False
        assert result["verification_status"] == "unverified"


class TestComputeSourceScore:
    def test_academic_verified_caps_at_one(self):
        assert compute_source_score({"source_type": "academic", "verified": True}) == 1.0

    def test_unknown_unverified(self):
        assert compute_source_score({"source_type": "unknown", "verified": False}) == 0.5

    def test_verification_bonus(self):
        unverified = compute_source_score({"source_type": "official", "verified": False})
        verified = compute_source_score({"source_type": "official", "verified": True})
        assert verified > unverified


class TestAnalyzeArticleSources:
    def test_arxiv_academic(self):
        sources = analyze_article_sources(
            {"url": "https://www.sciencedirect.com/science/article/pii/S1", "title": "Paper", "tags": [], "content_type": ""}
        )
        assert len(sources) == 1
        s = sources[0]
        assert s["type"] == "primary"
        assert s["source_type"] == "academic"
        assert s["domain"] == "sciencedirect.com"
        assert s["verified"] is True

    def test_empty_article(self):
        sources = analyze_article_sources({})
        assert len(sources) == 1
        assert sources[0]["source_type"] == "unknown"


class TestComputeArticleSourceScore:
    def test_arxiv_article(self):
        result = compute_article_source_score(
            {"url": "https://www.sciencedirect.com/science/article/pii/S1", "title": "Paper", "tags": [], "content_type": ""}
        )
        assert result["source_type"] == "academic"
        assert result["verified"] is True
        assert result["evidence_level"] == "Peer-reviewed"
        assert result["source_score"] == 1.0

    def test_social_article(self):
        result = compute_article_source_score(
            {"url": "https://twitter.com/x", "title": "tweet", "tags": [], "content_type": ""}
        )
        assert result["source_type"] == "social"
        assert result["verified"] is False
        assert result["source_score"] == 0.5
