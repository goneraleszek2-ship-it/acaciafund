"""Tests for core/contradiction.py — cross-claim contradiction detection."""

import pytest

from core.contradiction import (
    ContradictionDetector,
    ContradictionPair,
    ContradictionReport,
    ContradictionSeverity,
    ContradictionType,
    cluster_contradictions,
    contradiction_summary,
    detect_contradictions,
)
from core.source_trail import ClaimCitation, EvidenceTrail, SourceClaim, SourceTrailManager

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def detector():
    return ContradictionDetector()


@pytest.fixture
def sample_claims():
    return [
        SourceClaim(
            claim_text="KYC compliance prevents fraud in financial institutions.",
            pillar="aml",
            concept_ids=["kyc", "aml"],
            citations=[ClaimCitation(url="https://fatf.org/kyc", verified=True)],
        ),
        SourceClaim(
            claim_text="KYC compliance does not prevent fraud effectively.",
            pillar="aml",
            concept_ids=["kyc", "aml"],
            citations=[ClaimCitation(url="https://critic.org/kyc-flaws", verified=True)],
        ),
        SourceClaim(
            claim_text="Stream processing requires backpressure handling.",
            pillar="data-engineering",
            concept_ids=["streaming"],
            citations=[],
        ),
        SourceClaim(
            claim_text="High-frequency trading increases market volatility.",
            pillar="stock",
            concept_ids=["market-microstructure"],
            citations=[ClaimCitation(url="https://sec.gov/hft-study", verified=True)],
        ),
        SourceClaim(
            claim_text="High-frequency trading decreases market volatility.",
            pillar="stock",
            concept_ids=["market-microstructure"],
            citations=[ClaimCitation(url="https://exchange.org/hft-analysis", verified=False)],
        ),
    ]


@pytest.fixture
def trail_manager(sample_claims):
    mgr = SourceTrailManager()
    mgr.add_trail("trail-1", EvidenceTrail(content_slug="article-1", claims=sample_claims[:2]))
    mgr.add_trail("trail-2", EvidenceTrail(content_slug="article-2", claims=sample_claims[2:3]))
    mgr.add_trail("trail-3", EvidenceTrail(content_slug="article-3", claims=sample_claims[3:5]))
    return mgr


# ---------------------------------------------------------------------------
# Unit tests — ContradictionDetector
# ---------------------------------------------------------------------------


class TestContradictionDetector:
    def test_has_negation_with_not(self, detector):
        assert detector.has_negation("KYC does not prevent fraud")
        assert not detector.has_negation("KYC prevents fraud")

    def test_has_negation_with_prevent(self, detector):
        assert not detector.has_negation("KYC prevents fraud")
        assert not detector.has_negation("KYC screens transactions")

    def test_has_negation_without(self, detector):
        assert detector.has_negation("Trading without proper risk controls")

    def test_has_negation_no_match(self, detector):
        assert not detector.has_negation("Market microstructure affects liquidity")

    def test_check_negation_contradiction_true(self, detector):
        assert detector.check_negation_contradiction(
            "KYC prevents fraud",
            "KYC does not prevent fraud",
        )

    def test_check_negation_contradiction_false(self, detector):
        assert not detector.check_negation_contradiction(
            "KYC prevents fraud",
            "KYC screens customers",
        )

    def test_antonym_index(self, detector):
        assert detector.find_antonym("increases") == "decreases"
        assert detector.find_antonym("decreases") == "increases"
        assert detector.find_antonym("bullish") == "bearish"

    def test_check_antonym_contradiction_found(self, detector):
        result = detector.check_antonym_contradiction(
            "HFT increases market volatility",
            "HFT decreases market volatility",
        )
        assert result is not None
        assert result[0] == "increases"
        assert result[1] == "decreases"

    def test_check_antonym_contradiction_none(self, detector):
        result = detector.check_antonym_contradiction(
            "HFT increases volatility",
            "KYC reduces fraud risk",
        )
        assert result is None

    def test_extract_numeric_values(self, detector):
        values = detector.extract_numeric_values("5% rate increase and 10 bps spread")
        assert len(values) >= 2

    def test_extract_numeric_values_none(self, detector):
        values = detector.extract_numeric_values("No numbers here")
        assert values == []

    def test_check_numeric_contradiction_true(self, detector):
        assert detector.check_numeric_contradiction(
            "The rate is 5%",
            "The rate is 10%",
        )

    def test_check_numeric_contradiction_false_same(self, detector):
        assert not detector.check_numeric_contradiction(
            "The rate is 5%",
            "The rate is 5%",
        )

    def test_check_numeric_contradiction_false_no_numbers(self, detector):
        assert not detector.check_numeric_contradiction(
            "The rate is high",
            "The rate is low",
        )

    def test_compute_similarity_high(self, detector):
        sim = detector.compute_similarity(
            "KYC prevents fraud in banking",
            "KYC prevents fraud in banking systems",
        )
        assert sim > 0.5

    def test_compute_similarity_low(self, detector):
        sim = detector.compute_similarity(
            "KYC prevents fraud",
            "HFT increases volatility",
        )
        assert sim < 0.3

    def test_compute_similarity_empty(self, detector):
        sim = detector.compute_similarity("a", "b")
        assert sim == 0.0

    def test_unknown_antonym_returns_none(self, detector):
        assert detector.find_antonym("nonexistentwordxyz") is None


class TestDetectPair:
    def test_detect_negation_pair(self, detector, sample_claims):
        result = detector.detect_pair(sample_claims[0], sample_claims[1])
        assert result is not None
        assert result.contradiction_type == ContradictionType.NEGATION
        assert result.severity == ContradictionSeverity.HIGH
        assert result.confidence > 0

    def test_detect_antonym_pair(self, detector, sample_claims):
        result = detector.detect_pair(sample_claims[3], sample_claims[4])
        assert result is not None
        assert result.contradiction_type == ContradictionType.ANTONYM
        assert "increases" in result.claim_a.lower() or "increases" in result.claim_b.lower()

    def test_detect_no_contradiction(self, detector, sample_claims):
        result = detector.detect_pair(sample_claims[0], sample_claims[2])
        assert result is None

    def test_detect_pair_low_similarity(self, detector):
        claim_a = SourceClaim(claim_text="KYC prevents fraud.")
        claim_b = SourceClaim(claim_text="HFT increases volatility.")
        result = detector.detect_pair(claim_a, claim_b)
        assert result is None

    def test_detect_pair_unverified(self, detector):
        claim_a = SourceClaim(
            claim_text="KYC prevents fraud.",
            citations=[ClaimCitation(url="https://x.com", verified=False)],
        )
        claim_b = SourceClaim(
            claim_text="KYC does not prevent fraud.",
            citations=[ClaimCitation(url="https://y.com", verified=False)],
        )
        result = detector.detect_pair(claim_a, claim_b)
        assert result is not None
        assert result.severity == ContradictionSeverity.LOW

    def test_detect_pair_shared_concepts(self, detector):
        claim_a = SourceClaim(
            claim_text="KYC prevents fraud.",
            concept_ids=["kyc"],
        )
        claim_b = SourceClaim(
            claim_text="KYC does not prevent fraud.",
            concept_ids=["kyc"],
        )
        result = detector.detect_pair(claim_a, claim_b)
        assert result is not None
        assert "kyc" in result.concept_ids

    def test_detect_numeric_contradiction(self, detector):
        claim_a = SourceClaim(
            claim_text="Capital requirement is 8% of risk-weighted assets.",
            concept_ids=["capital"],
        )
        claim_b = SourceClaim(
            claim_text="Capital requirement should be 12% of risk-weighted assets.",
            concept_ids=["capital"],
        )
        result = detector.detect_pair(claim_a, claim_b)
        assert result is not None, "Expected contradiction, got None"


class TestDetectAll:
    def test_detect_all_finds_contradictions(self, detector, sample_claims):
        report = detector.detect_all(sample_claims)
        assert report.total_pairs >= 2
        assert ContradictionType.NEGATION.value in report.by_type
        assert ContradictionType.ANTONYM.value in report.by_type

    def test_detect_all_sorts_by_confidence(self, detector, sample_claims):
        report = detector.detect_all(sample_claims)
        for i in range(len(report.pairs) - 1):
            assert report.pairs[i].confidence >= report.pairs[i + 1].confidence

    def test_detect_all_no_duplicates(self, detector, sample_claims):
        report = detector.detect_all(sample_claims)
        seen = set()
        for pair in report.pairs:
            key = tuple(sorted([pair.claim_a, pair.claim_b]))
            assert key not in seen
            seen.add(key)

    def test_detect_all_empty(self, detector):
        report = detector.detect_all([])
        assert report.total_pairs == 0
        assert report.pairs == []

    def test_detect_all_no_contradictions(self, detector):
        claims = [
            SourceClaim(claim_text="KYC prevents fraud.", pillar="aml"),
            SourceClaim(claim_text="Streaming needs backpressure.", pillar="data-engineering"),
        ]
        report = detector.detect_all(claims)
        assert report.total_pairs == 0


# ---------------------------------------------------------------------------
# Integration tests — detect_contradictions
# ---------------------------------------------------------------------------


class TestDetectContradictions:
    def test_detect_all_claims(self, trail_manager):
        report = detect_contradictions(trail_manager)
        assert report.total_pairs >= 2

    def test_detect_by_pillar(self, trail_manager):
        report = detect_contradictions(trail_manager, pillar="stock")
        assert report.total_pairs >= 1

    def test_detect_by_pillar_no_results(self, trail_manager):
        report = detect_contradictions(trail_manager, pillar="data-engineering")
        assert report.total_pairs == 0

    def test_detect_by_concept(self, trail_manager):
        report = detect_contradictions(trail_manager, concept_id="market-microstructure")
        assert report.total_pairs >= 1

    def test_detect_by_concept_no_results(self, trail_manager):
        report = detect_contradictions(trail_manager, concept_id="streaming")
        assert report.total_pairs == 0


# ---------------------------------------------------------------------------
# Unit tests — ContradictionReport & helpers
# ---------------------------------------------------------------------------


class TestContradictionReport:
    def test_empty_report(self):
        report = ContradictionReport()
        assert report.total_pairs == 0
        assert report.by_type == {}
        assert report.by_severity == {}
        assert report.by_concept == {}

    def test_report_aggregates_stats(self):
        pairs = [
            ContradictionPair(
                claim_a="a", claim_b="b",
                contradiction_type=ContradictionType.NEGATION,
                severity=ContradictionSeverity.HIGH,
                concept_ids=["kyc"],
            ),
            ContradictionPair(
                claim_a="c", claim_b="d",
                contradiction_type=ContradictionType.ANTONYM,
                severity=ContradictionSeverity.MEDIUM,
                concept_ids=["hft"],
            ),
        ]
        report = ContradictionReport(pairs=pairs)
        assert report.total_pairs == 2
        assert report.by_type[ContradictionType.NEGATION.value] == 1
        assert report.by_type[ContradictionType.ANTONYM.value] == 1
        assert report.by_severity[ContradictionSeverity.HIGH.value] == 1
        assert report.by_severity[ContradictionSeverity.MEDIUM.value] == 1
        assert report.by_concept["kyc"] == 1
        assert report.by_concept["hft"] == 1


class TestClusterContradictions:
    def test_clusters_by_concept(self):
        report = ContradictionReport(pairs=[
            ContradictionPair("a", "b", ContradictionType.NEGATION, ContradictionSeverity.HIGH, concept_ids=["kyc"]),
            ContradictionPair("c", "d", ContradictionType.ANTONYM, ContradictionSeverity.LOW, concept_ids=["hft"]),
        ])
        clusters = cluster_contradictions(report)
        assert "kyc" in clusters
        assert "hft" in clusters
        assert len(clusters["kyc"]) == 1
        assert len(clusters["hft"]) == 1

    def test_clusters_unassigned(self):
        report = ContradictionReport(pairs=[
            ContradictionPair("a", "b", ContradictionType.NEGATION, ContradictionSeverity.HIGH, concept_ids=[]),
        ])
        clusters = cluster_contradictions(report)
        assert "unassigned" in clusters


class TestContradictionSummary:
    def test_summary_includes_counts(self):
        report = ContradictionReport(pairs=[
            ContradictionPair("a", "b", ContradictionType.NEGATION, ContradictionSeverity.HIGH),
        ])
        summary = contradiction_summary(report)
        assert "1" in summary
        assert "negation" in summary
        assert "high" in summary
