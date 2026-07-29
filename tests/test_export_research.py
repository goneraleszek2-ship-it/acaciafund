"""Tests for scripts/export_research.py — research workspace export."""

import json

import pytest

from core.contradiction import (
    ContradictionPair,
    ContradictionReport,
    ContradictionSeverity,
    ContradictionType,
)
from core.evidence_grade import DowngradeReason, EvidenceLevel, EvidenceScore, UpgradeReason

# ---------------------------------------------------------------------------
# Test the report generation functions from the script
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_scores():
    return [
        EvidenceScore(
            claim="KYC compliance reduces fraud in financial institutions.",
            level=EvidenceLevel.HIGH,
            score=0.85,
            downgrades=[],
            upgrades=[UpgradeReason.LARGE_EFFECT],
            citations_used=2,
            pillar="aml",
            concept_ids=["kyc"],
        ),
        EvidenceScore(
            claim="KYC compliance does not reduce fraud effectively.",
            level=EvidenceLevel.LOW,
            score=0.45,
            downgrades=[DowngradeReason.INCONSISTENCY, DowngradeReason.RISK_OF_BIAS],
            upgrades=[],
            citations_used=1,
            pillar="aml",
            concept_ids=["kyc"],
        ),
        EvidenceScore(
            claim="HFT increases market volatility.",
            level=EvidenceLevel.VERY_LOW,
            score=0.0,
            downgrades=[DowngradeReason.INDIRECTNESS],
            upgrades=[],
            citations_used=0,
            pillar="stock",
            concept_ids=["market-microstructure"],
        ),
    ]


@pytest.fixture
def sample_contradiction_report():
    return ContradictionReport(pairs=[
        ContradictionPair(
            claim_a="KYC compliance reduces fraud.",
            claim_b="KYC compliance does not reduce fraud.",
            contradiction_type=ContradictionType.NEGATION,
            severity=ContradictionSeverity.HIGH,
            concept_ids=["kyc"],
            source_a="aml",
            source_b="aml",
            confidence=0.8,
        ),
    ])


class TestGenerateMarkdown:
    def test_markdown_includes_header(self, sample_scores, sample_contradiction_report):
        from scripts.export_research import generate_markdown_report

        md = generate_markdown_report(sample_scores, sample_contradiction_report)
        assert "Research Workspace Report" in md
        assert "Evidence Quality Summary" in md
        assert "Contradictions" in md
        assert "Claim-Level Evidence" in md
        assert "Downgrade Reasons" in md

    def test_markdown_includes_quality_table(self, sample_scores, sample_contradiction_report):
        from scripts.export_research import generate_markdown_report

        md = generate_markdown_report(sample_scores, sample_contradiction_report)
        assert "| High | 1 |" in md
        assert "| Low | 1 |" in md
        assert "| Very Low | 1 |" in md

    def test_markdown_includes_contradictions(self, sample_scores, sample_contradiction_report):
        from scripts.export_research import generate_markdown_report

        md = generate_markdown_report(sample_scores, sample_contradiction_report)
        assert "Total pairs: 1" in md
        assert "negation" in md
        assert "high" in md

    def test_markdown_no_contradictions(self, sample_scores):
        from scripts.export_research import generate_markdown_report

        empty = ContradictionReport()
        md = generate_markdown_report(sample_scores, empty)
        assert "No contradictions detected" in md

    def test_markdown_includes_downgrades(self, sample_scores, sample_contradiction_report):
        from scripts.export_research import generate_markdown_report

        md = generate_markdown_report(sample_scores, sample_contradiction_report)
        assert "Inconsistency" in md
        assert "Risk Of Bias" in md

    def test_markdown_includes_filter_info(self, sample_scores, sample_contradiction_report):
        from scripts.export_research import generate_markdown_report

        md = generate_markdown_report(
            sample_scores, sample_contradiction_report,
            pillar="aml", concept_id="kyc",
        )
        assert "Pillar = Compliance" in md
        assert "Concept = kyc" in md

    def test_markdown_empty_scores(self):
        from scripts.export_research import generate_markdown_report

        md = generate_markdown_report([], ContradictionReport())
        assert "Research Workspace Report" in md
        assert "0.00" in md


class TestGenerateJSON:
    def test_json_includes_structure(self, sample_scores, sample_contradiction_report):
        from scripts.export_research import generate_json_report

        js = generate_json_report(sample_scores, sample_contradiction_report)
        data = json.loads(js)
        assert data["report_type"] == "research_workspace"
        assert "generated_at" in data
        assert "summary" in data
        assert "contradictions" in data
        assert "evidence_scores" in data

    def test_json_summary_counts(self, sample_scores, sample_contradiction_report):
        from scripts.export_research import generate_json_report

        js = generate_json_report(sample_scores, sample_contradiction_report)
        data = json.loads(js)
        assert data["summary"]["total_claims"] == 3
        assert data["summary"]["average_score"] > 0
        assert data["summary"]["level_counts"]["high"] == 1
        assert data["summary"]["level_counts"]["very_low"] == 1

    def test_json_contradiction_data(self, sample_scores, sample_contradiction_report):
        from scripts.export_research import generate_json_report

        js = generate_json_report(sample_scores, sample_contradiction_report)
        data = json.loads(js)
        assert data["contradictions"]["total_pairs"] == 1
        assert len(data["contradictions"]["pairs"]) == 1
        assert data["contradictions"]["pairs"][0]["type"] == "negation"

    def test_json_no_contradictions(self, sample_scores):
        from scripts.export_research import generate_json_report

        js = generate_json_report(sample_scores, ContradictionReport())
        data = json.loads(js)
        assert data["contradictions"]["total_pairs"] == 0
        assert data["contradictions"]["pairs"] == []

    def test_json_scores_downgrades(self, sample_scores, sample_contradiction_report):
        from scripts.export_research import generate_json_report

        js = generate_json_report(sample_scores, sample_contradiction_report)
        data = json.loads(js)
        score = data["evidence_scores"][1]
        assert "inconsistency" in score["downgrades"]
        assert "risk_of_bias" in score["downgrades"]

    def test_json_filter(self):
        from scripts.export_research import generate_json_report

        js = generate_json_report([], ContradictionReport(), pillar="aml", concept_id="kyc")
        data = json.loads(js)
        assert data["filter"]["pillar"] == "aml"
        assert data["filter"]["concept_id"] == "kyc"

    def test_json_empty(self):
        from scripts.export_research import generate_json_report

        js = generate_json_report([], ContradictionReport())
        data = json.loads(js)
        assert data["summary"]["total_claims"] == 0
        assert data["contradictions"]["total_pairs"] == 0
        assert data["evidence_scores"] == []
