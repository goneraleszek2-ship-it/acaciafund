"""Tests for core/evidence_grade.py — GRADE-style evidence quality scoring."""

import pytest

from core.contradiction import (
    ContradictionPair,
    ContradictionReport,
    ContradictionSeverity,
    ContradictionType,
)
from core.evidence_grade import (
    DowngradeReason,
    EvidenceGrader,
    EvidenceLevel,
    EvidenceScore,
    UpgradeReason,
    grade_evidence,
    quality_summary,
)
from core.source_trail import ClaimCitation, EvidenceTrail, SourceClaim, SourceTrailManager

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def grader():
    return EvidenceGrader()


@pytest.fixture
def claim_with_citations():
    return SourceClaim(
        claim_text="KYC compliance reduces fraud in financial institutions.",
        pillar="aml",
        concept_ids=["kyc", "aml"],
        citations=[
            ClaimCitation(url="https://fatf.org/kyc", verified=True, credibility_score=0.9),
            ClaimCitation(url="https://worldbank.org/aml", verified=True, credibility_score=0.85),
        ],
    )


@pytest.fixture
def claim_no_citations():
    return SourceClaim(
        claim_text="KYC compliance reduces fraud in financial institutions.",
        pillar="aml",
        concept_ids=["kyc"],
        citations=[],
    )


@pytest.fixture
def claim_vague():
    return SourceClaim(
        claim_text="KYC may help reduce some types of fraud.",
        pillar="aml",
        concept_ids=["kyc"],
        citations=[
            ClaimCitation(url="https://example.org", verified=False, credibility_score=0.3),
        ],
    )


@pytest.fixture
def sample_trail_manager():
    mgr = SourceTrailManager()
    mgr.add_trail("article-1", EvidenceTrail(
        content_slug="article-1",
        content_title="KYC Study",
        claims=[
            SourceClaim(
                claim_text="KYC compliance reduces fraud in financial institutions.",
                pillar="aml",
                concept_ids=["kyc"],
                citations=[
                    ClaimCitation(url="https://fatf.org/kyc", verified=True, credibility_score=0.9),
                ],
            ),
            SourceClaim(
                claim_text="KYC compliance does not reduce fraud effectively.",
                pillar="aml",
                concept_ids=["kyc"],
                citations=[
                    ClaimCitation(url="https://critic.org/kyc-flaws", verified=True, credibility_score=0.8),
                ],
            ),
        ],
    ))
    mgr.add_trail("article-2", EvidenceTrail(
        content_slug="article-2",
        content_title="HFT Impact",
        claims=[
            SourceClaim(
                claim_text="High-frequency trading increases market volatility.",
                pillar="stock",
                concept_ids=["market-microstructure"],
                citations=[],
            ),
        ],
    ))
    return mgr


# ---------------------------------------------------------------------------
# Unit tests — EvidenceLevel
# ---------------------------------------------------------------------------


class TestEvidenceLevel:
    def test_high_threshold(self):
        from core.evidence_grade import _level_for_score
        assert _level_for_score(0.9) == EvidenceLevel.HIGH
        assert _level_for_score(0.8) == EvidenceLevel.HIGH

    def test_moderate_threshold(self):
        from core.evidence_grade import _level_for_score
        assert _level_for_score(0.7) == EvidenceLevel.MODERATE
        assert _level_for_score(0.6) == EvidenceLevel.MODERATE

    def test_low_threshold(self):
        from core.evidence_grade import _level_for_score
        assert _level_for_score(0.5) == EvidenceLevel.LOW
        assert _level_for_score(0.4) == EvidenceLevel.LOW

    def test_very_low_threshold(self):
        from core.evidence_grade import _level_for_score
        assert _level_for_score(0.3) == EvidenceLevel.VERY_LOW
        assert _level_for_score(0.0) == EvidenceLevel.VERY_LOW


# ---------------------------------------------------------------------------
# Unit tests — EvidenceGrader
# ---------------------------------------------------------------------------


class TestEvidenceGrader:
    def test_grade_high_quality(self, grader, claim_with_citations):
        result = grader.grade_claim(claim_with_citations)
        assert result.level == EvidenceLevel.HIGH
        assert result.score >= 0.8
        assert result.citations_used == 2
        assert UpgradeReason.LARGE_EFFECT in result.upgrades

    def test_grade_no_citations(self, grader, claim_no_citations):
        result = grader.grade_claim(claim_no_citations)
        assert result.level == EvidenceLevel.VERY_LOW
        assert result.score == 0.0
        assert DowngradeReason.INDIRECTNESS in result.downgrades

    def test_grade_vague_claim(self, grader, claim_vague):
        result = grader.grade_claim(claim_vague)
        assert DowngradeReason.RISK_OF_BIAS in result.downgrades
        assert DowngradeReason.IMPRECISION in result.downgrades
        assert result.level in (EvidenceLevel.LOW, EvidenceLevel.VERY_LOW)

    def test_grade_contradicted_claim(self):
        report = ContradictionReport(pairs=[
            ContradictionPair("A is true", "A is false", ContradictionType.NEGATION, ContradictionSeverity.HIGH),
        ])
        grader = EvidenceGrader(contradiction_report=report)
        claim = SourceClaim(
            claim_text="A is true",
            citations=[ClaimCitation(url="https://x.com", verified=True, credibility_score=0.8)],
        )
        result = grader.grade_claim(claim)
        assert DowngradeReason.INCONSISTENCY in result.downgrades

    def test_grade_unverified_citations(self, grader):
        claim = SourceClaim(
            claim_text="Test claim.",
            citations=[
                ClaimCitation(url="https://x.com", verified=False, credibility_score=0.3),
            ],
        )
        result = grader.grade_claim(claim)
        assert DowngradeReason.RISK_OF_BIAS in result.downgrades
        assert result.level in (EvidenceLevel.LOW, EvidenceLevel.VERY_LOW)

    def test_score_clamped(self, grader):
        claim = SourceClaim(
            claim_text="Test.",
            citations=[
                ClaimCitation(url="https://a.com", verified=True, credibility_score=0.1),
                ClaimCitation(url="https://b.com", verified=False, credibility_score=0.1),
            ],
        )
        result = grader.grade_claim(claim)
        assert 0.0 <= result.score <= 1.0

    def test_grade_single_verified(self, grader):
        claim = SourceClaim(
            claim_text="Single well-sourced claim.",
            citations=[
                ClaimCitation(url="https://fatf.org", verified=True, credibility_score=0.9),
            ],
        )
        result = grader.grade_claim(claim)
        assert result.level == EvidenceLevel.HIGH


class TestGraderAll:
    def test_grade_all_returns_list(self, grader, claim_with_citations, claim_no_citations):
        results = grader.grade_all([claim_with_citations, claim_no_citations])
        assert len(results) == 2
        assert results[0].level == EvidenceLevel.HIGH
        assert results[1].level == EvidenceLevel.VERY_LOW

    def test_grade_all_empty(self, grader):
        assert grader.grade_all([]) == []


class TestGraderSummary:
    def test_summary_basic(self, grader, claim_with_citations, claim_no_citations):
        scores = grader.grade_all([claim_with_citations, claim_no_citations])
        summary = grader.summary(scores)
        assert "Graded 2 claims" in summary
        assert "high" in summary.lower()
        assert "very_low" in summary.lower()

    def test_summary_empty(self, grader):
        summary = grader.summary([])
        assert "No evidence to grade" in summary


class TestGraderTrailManager:
    def test_grade_trail_manager(self, grader, sample_trail_manager):
        grader.trail_manager = sample_trail_manager
        scores = grader.grade_trail_manager()
        assert len(scores) == 3

    def test_grade_trail_manager_no_manager(self, grader):
        assert grader.grade_trail_manager() == []


# ---------------------------------------------------------------------------
# Integration tests — grade_evidence
# ---------------------------------------------------------------------------


class TestGradeEvidence:
    def test_grade_all_claims(self, sample_trail_manager):
        scores = grade_evidence(sample_trail_manager)
        assert len(scores) == 3

    def test_grade_by_pillar(self, sample_trail_manager):
        scores = grade_evidence(sample_trail_manager, pillar="aml")
        assert len(scores) == 2

    def test_grade_by_pillar_no_results(self, sample_trail_manager):
        scores = grade_evidence(sample_trail_manager, pillar="data-engineering")
        assert len(scores) == 0

    def test_grade_by_concept(self, sample_trail_manager):
        scores = grade_evidence(sample_trail_manager, concept_id="kyc")
        assert len(scores) >= 1

    def test_grade_by_concept_no_results(self, sample_trail_manager):
        scores = grade_evidence(sample_trail_manager, concept_id="nonexistent")
        assert len(scores) == 0


# ---------------------------------------------------------------------------
# Unit tests — quality_summary
# ---------------------------------------------------------------------------


class TestQualitySummary:
    def test_quality_summary_includes_counts(self):
        scores = [
            EvidenceScore(claim="a", level=EvidenceLevel.HIGH, score=0.9),
            EvidenceScore(claim="b", level=EvidenceLevel.LOW, score=0.4),
        ]
        summary = quality_summary(scores)
        assert "HIGH" in summary
        assert "2" in summary
        assert "1" in summary  # one high

    def test_quality_summary_empty(self):
        summary = quality_summary([])
        assert "No evidence quality scores available" in summary
