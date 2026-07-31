"""Tests for core/source_trail.py — claim→citation mapping and source attribution."""

import pytest

from core.ontology import (
    OntologyManager,
    ResourceLink,
)
from core.source_trail import (
    ClaimCitation,
    EvidenceTrail,
    SourceClaim,
    SourceTrailManager,
    build_trails_for_item,
    extract_claims_from_text,
    extract_urls_from_text,
    match_citations_to_sources,
)

# ---------------------------------------------------------------------------
# Unit tests — data models
# ---------------------------------------------------------------------------


class TestEvidenceTrail:
    def test_empty_trail(self):
        trail = EvidenceTrail()
        assert trail.total_claims == 0
        assert trail.verified_citations == 0
        assert trail.unverified_citations == 0
        assert trail.sources_used == set()
        assert trail.built_at != ""

    def test_trail_with_claims(self):
        claims = [
            SourceClaim(
                claim_text="KYC reduces fraud risk.",
                pillar="aml",
                citations=[
                    ClaimCitation(url="https://example.com/kyc", verified=True),
                ],
            ),
            SourceClaim(
                claim_text="Streaming pipelines need backpressure.",
                pillar="data-engineering",
                citations=[
                    ClaimCitation(url="https://example.com/streaming", verified=False),
                ],
            ),
        ]
        trail = EvidenceTrail(
            content_slug="test-article",
            content_title="Test Article",
            claims=claims,
        )
        assert trail.total_claims == 2
        assert trail.verified_citations == 1
        assert trail.unverified_citations == 1
        assert "https://example.com/kyc" in trail.sources_used
        assert "https://example.com/streaming" in trail.sources_used


class TestSourceClaim:
    def test_default_citations_empty(self):
        claim = SourceClaim(claim_text="Test claim")
        assert claim.citations == []
        assert claim.confidence == 1.0

    def test_with_citations(self):
        cit = ClaimCitation(url="https://example.com", verified=True)
        claim = SourceClaim(
            claim_text="Verified claim",
            citations=[cit],
            concept_ids=["kyc"],
            pillar="aml",
        )
        assert claim.concept_ids == ["kyc"]
        assert claim.pillar == "aml"
        assert claim.citations[0].verified


class TestClaimCitation:
    def test_defaults(self):
        cit = ClaimCitation(url="https://example.com")
        assert cit.credibility_score == 0.5
        assert cit.verified is False
        assert cit.http_status is None


# ---------------------------------------------------------------------------
# Unit tests — SourceTrailManager
# ---------------------------------------------------------------------------


@pytest.fixture
def manager_with_trails():
    mgr = SourceTrailManager()
    trail1 = EvidenceTrail(
        content_slug="article-1",
        content_title="Article 1",
        claims=[
            SourceClaim(
                claim_text="KYC is essential.",
                pillar="aml",
                citations=[
                    ClaimCitation(url="https://fatf.org/kyc", verified=True),
                    ClaimCitation(url="https://unknown.org/no", verified=False),
                ],
            ),
        ],
    )
    trail2 = EvidenceTrail(
        content_slug="article-2",
        content_title="Article 2",
        claims=[
            SourceClaim(
                claim_text="Market microstructure matters.",
                pillar="stock",
                citations=[
                    ClaimCitation(url="https://sec.gov/market", verified=True),
                ],
            ),
        ],
    )
    mgr.add_trail("article-1", trail1)
    mgr.add_trail("article-2", trail2)
    return mgr


class TestSourceTrailManager:
    def test_add_and_get_trail(self, manager_with_trails):
        trail = manager_with_trails.get_trail("article-1")
        assert trail is not None
        assert trail.content_title == "Article 1"

    def test_get_missing_trail(self, manager_with_trails):
        assert manager_with_trails.get_trail("nonexistent") is None

    def test_remove_trail(self, manager_with_trails):
        assert manager_with_trails.remove_trail("article-1") is True
        assert manager_with_trails.get_trail("article-1") is None
        assert manager_with_trails.remove_trail("nonexistent") is False

    def test_all_trails(self, manager_with_trails):
        trails = manager_with_trails.all_trails()
        assert len(trails) == 2

    def test_trail_count(self, manager_with_trails):
        assert manager_with_trails.trail_count() == 2

    def test_claims_for_pillar(self, manager_with_trails):
        aml_claims = manager_with_trails.claims_for_pillar("aml")
        assert len(aml_claims) == 1
        assert aml_claims[0].claim_text == "KYC is essential."

        stock_claims = manager_with_trails.claims_for_pillar("stock")
        assert len(stock_claims) == 1

    def test_claims_for_concept(self, manager_with_trails):
        mgr = SourceTrailManager()
        trail = EvidenceTrail(
            content_slug="test",
            claims=[
                SourceClaim(
                    claim_text="Test",
                    concept_ids=["kyc", "aml"],
                ),
            ],
        )
        mgr.add_trail("test", trail)
        assert len(mgr.claims_for_concept("kyc")) == 1
        assert len(mgr.claims_for_concept("nonexistent")) == 0

    def test_verify_citations(self):
        ontology = OntologyManager()
        ontology.add_resource_link(
            ResourceLink(
                concept_id="kyc",
                url="https://fatf.org/kyc",
                title="FATF KYC Guide",
                source_org="FATF",
                http_status=200,
                credibility_score=0.9,
            )
        )

        mgr = SourceTrailManager(ontology=ontology)
        trail = EvidenceTrail(
            content_slug="test",
            claims=[
                SourceClaim(
                    claim_text="KYC is essential.",
                    citations=[
                        ClaimCitation(url="https://fatf.org/kyc", verified=False),
                        ClaimCitation(url="https://unknown.org/no", verified=False),
                    ],
                ),
            ],
        )
        mgr.add_trail("test", trail)
        count = mgr.verify_citations()

        assert count == 1
        trail = mgr.get_trail("test")
        assert trail is not None
        citations = trail.claims[0].citations
        fatf_cit = next(c for c in citations if "fatf" in c.url)
        unknown_cit = next(c for c in citations if "unknown" in c.url)
        assert fatf_cit.verified is True
        assert fatf_cit.http_status == 200
        assert fatf_cit.credibility_score == 0.9
        assert unknown_cit.verified is False

    def test_to_dict_roundtrip(self, manager_with_trails):
        data = manager_with_trails.to_dict()
        assert "article-1" in data
        assert data["article-1"]["content_title"] == "Article 1"
        assert data["article-1"]["total_claims"] == 1

        restored = SourceTrailManager.from_dict(data)
        assert restored.trail_count() == 2
        r1 = restored.get_trail("article-1")
        assert r1 is not None
        assert r1.content_title == "Article 1"
        assert r1.total_claims == 1
        assert len(r1.claims[0].citations) == 2


# ---------------------------------------------------------------------------
# Unit tests — extraction utilities
# ---------------------------------------------------------------------------


class TestExtractClaimsFromText:
    def test_extracts_claim_sentences(self):
        text = (
            "KYC compliance reduces fraud risk significantly. "
            "Streaming pipelines require backpressure handling. "
            "Market microstructure affects liquidity."
        )
        claims = extract_claims_from_text(text)
        assert len(claims) >= 2

    def test_skips_short_sentences(self):
        text = "It is. KYC reduces fraud risk significantly."
        claims = extract_claims_from_text(text)
        assert all(len(c) >= 40 for c in claims)

    def test_empty_text(self):
        assert extract_claims_from_text("") == []
        assert extract_claims_from_text(None) == []


class TestExtractUrlsFromText:
    def test_extracts_urls(self):
        text = "See https://example.com and https://test.org/page for details."
        urls = extract_urls_from_text(text)
        assert "https://example.com" in urls
        assert "https://test.org/page" in urls

    def test_no_urls(self):
        assert extract_urls_from_text("No URLs here.") == []


class TestMatchCitationsToSources:
    def test_matches_known_urls(self):
        ontology = OntologyManager()
        ontology.add_resource_link(
            ResourceLink(
                concept_id="kyc",
                url="https://fatf.org/kyc",
                title="FATF Guide",
                source_org="FATF",
            )
        )

        result = match_citations_to_sources(
            ["https://fatf.org/kyc", "https://unknown.org"],
            ontology,
        )
        assert result["https://fatf.org/kyc"] is not None
        assert result["https://unknown.org"] is None


# ---------------------------------------------------------------------------
# Integration test — build_trails_for_item
# ---------------------------------------------------------------------------


class TestBuildTrailsForItem:
    def test_builds_trail_from_text(self):
        body = (
            "KYC compliance reduces fraud risk significantly. "
            "See https://fatf.org/kyc for more details. "
            "Streaming pipelines require backpressure handling. "
            "This was discussed at https://confluent.io/streaming. "
            "Market microstructure affects liquidity and price discovery."
        )
        trail = build_trails_for_item(
            slug="test-article",
            title="Test Article",
            body=body,
            pillar="aml",
            concept_ids=["kyc"],
        )
        assert trail.content_slug == "test-article"
        assert trail.content_title == "Test Article"
        assert trail.total_claims >= 2
        # At least one URL-based citation should be found
        assert len(trail.claims) >= 2
        # At least one claim should have a citation with a URL
        cited = [c for c in trail.claims if c.citations]
        assert len(cited) >= 1

    def test_builds_trail_with_ontology_lookup(self):
        ontology = OntologyManager()
        ontology.add_resource_link(
            ResourceLink(
                concept_id="kyc",
                url="https://fatf.org/kyc",
                title="FATF KYC Guide",
                source_org="FATF",
                http_status=200,
            ),
        )

        body = (
            "KYC compliance prevents fraud risk in financial institutions. "
            "See https://fatf.org/kyc for the full guide."
        )
        trail = build_trails_for_item(
            slug="test",
            title="Test",
            body=body,
            pillar="aml",
            ontology=ontology,
        )
        assert trail.total_claims >= 1, f"Expected at least 1 claim, got {trail.total_claims}"
        for claim in trail.claims:
            for cit in claim.citations:
                if cit.url == "https://fatf.org/kyc":
                    assert cit.verified is True
                    assert cit.source_name == "FATF"

    def test_no_body_produces_empty_trail(self):
        trail = build_trails_for_item(
            slug="empty", title="Empty", body=""
        )
        assert trail.total_claims == 0
