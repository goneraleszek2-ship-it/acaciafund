"""Tests for scripts/source_synthesis.py — pure helper functions.

Contract tests: verify function promises, not internal implementation.
"""


from scripts.source_synthesis import (
    extract_key_insights,
    extract_tags_from_article,
    generate_synthesis_description,
)

# ── extract_tags_from_article ──
#
# Contract:
#   extract_tags_from_article(article: dict) -> list[str]
#   - Returns article tags + pillar + content_type (all lowercased)
#   - Missing keys are silently omitted


class TestExtractTagsFromArticle:
    def test_returns_tags(self):
        result = extract_tags_from_article({"tags": ["AML", "KYC"]})
        assert "aml" in result
        assert "kyc" in result

    def test_includes_pillar(self):
        result = extract_tags_from_article({"tags": [], "pillar": "AML"})
        assert "aml" in result

    def test_includes_content_type(self):
        result = extract_tags_from_article({"tags": [], "content_type": "RESEARCH"})
        assert "research" in result

    def test_empty_article_returns_empty(self):
        assert extract_tags_from_article({}) == []

    def test_all_lowercased(self):
        result = extract_tags_from_article({"tags": ["AML", "CDD"], "pillar": "AML", "content_type": "RESEARCH"})
        assert all(t == t.lower() for t in result)


# ── generate_synthesis_description ──
#
# Contract:
#   generate_synthesis_description(source: dict, article_tags: list[str]) -> str
#   - Returns description based on source_type/url keyword matching
#   - Falls back to default description on no match


class TestGenerateSynthesisDescription:
    def test_arxiv_source(self):
        result = generate_synthesis_description(
            {"source_type": "arxiv", "url": "https://arxiv.org/abs/1234"}, ["aml"]
        )
        assert "academic" in result.lower()

    def test_sec_source(self):
        result = generate_synthesis_description(
            {"source_type": "sec", "url": "https://sec.gov/filing"}, []
        )
        assert "regulatory" in result.lower()

    def test_fatf_source(self):
        result = generate_synthesis_description(
            {"source_type": "fatf", "url": "https://fatf-gafi.org"}, ["aml"]
        )
        assert "international" in result.lower()

    def test_unknown_source_returns_default(self):
        result = generate_synthesis_description(
            {"source_type": "blog", "url": "https://example.com"}, []
        )
        assert "authoritative" in result.lower()

    def test_url_based_matching(self):
        result = generate_synthesis_description(
            {"source_type": "unknown", "url": "https://github.com/project"}, []
        )
        assert "technical" in result.lower()

    def test_tags_appear_in_description(self):
        result = generate_synthesis_description(
            {"source_type": "arxiv", "url": "https://arxiv.org"}, ["aml", "kyc"]
        )
        assert "aml" in result

    def test_empty_article_tags(self):
        result = generate_synthesis_description(
            {"source_type": "arxiv", "url": "https://arxiv.org"}, []
        )
        assert "this topic" in result


# ── extract_key_insights ──
#
# Contract:
#   extract_key_insights(source: dict) -> list[str]
#   - Returns 3-4 strings based on source_type/url matching
#   - Returns 4 default insights on no match


class TestExtractKeyInsights:
    def test_arxiv_insights(self):
        result = extract_key_insights({"source_type": "arxiv", "url": "https://arxiv.org"})
        assert len(result) >= 3
        assert any("methodology" in i.lower() for i in result)

    def test_pubmed_insights(self):
        result = extract_key_insights({"source_type": "pubmed", "url": "https://pubmed.ncbi.nlm.nih.gov"})
        assert len(result) >= 3
        assert any("clinical" in i.lower() for i in result)

    def test_github_insights(self):
        result = extract_key_insights({"source_type": "github", "url": "https://github.com/project"})
        assert len(result) >= 3
        assert any("architecture" in i.lower() for i in result)

    def test_sec_insights(self):
        result = extract_key_insights({"source_type": "sec", "url": "https://sec.gov"})
        assert len(result) >= 3
        assert any("compliance" in i.lower() for i in result)

    def test_fatf_insights(self):
        result = extract_key_insights({"source_type": "fatf", "url": "https://fatf-gafi.org"})
        assert len(result) >= 3
        assert any("guidance" in i.lower() for i in result)

    def test_unknown_source_returns_defaults(self):
        result = extract_key_insights({"source_type": "blog", "url": "https://example.com"})
        assert len(result) == 4
        assert any("findings" in i.lower() for i in result)

    def test_url_based_matching_fallback(self):
        result = extract_key_insights({"source_type": "unknown", "url": "https://gartner.com/report"})
        assert any("market" in i.lower() for i in result)
