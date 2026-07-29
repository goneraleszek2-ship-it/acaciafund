"""Evidence grading — GRADE-style evidence quality assessment for research claims.

Provides:
  EvidenceLevel, QualityCriterion, EvidenceScore — data models
  EvidenceGrader — engine for scoring evidence quality across claims
  grade_evidence — grade all claims in a SourceTrailManager
  quality_summary — human-readable quality summary
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Set

from core.contradiction import (
    ContradictionReport,
    detect_contradictions,
)
from core.source_trail import ClaimCitation, SourceClaim, SourceTrailManager

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Enums & data models
# ---------------------------------------------------------------------------


class EvidenceLevel(Enum):
    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"
    VERY_LOW = "very_low"


class DowngradeReason(Enum):
    RISK_OF_BIAS = "risk_of_bias"            # low credibility sources
    INCONSISTENCY = "inconsistency"           # contradictory claims
    INDIRECTNESS = "indirectness"             # no direct citations
    IMPRECISION = "imprecision"               # vague or qualitative claims


class UpgradeReason(Enum):
    LARGE_EFFECT = "large_effect"             # multiple verified citations
    DOSE_RESPONSE = "dose_response"           # consistent across pillars
    CONFOUNDING_MINIMIZED = "confounding_minimized"  # high citation count


@dataclass
class EvidenceScore:
    claim: str
    level: EvidenceLevel
    score: float
    downgrades: List[DowngradeReason] = field(default_factory=list)
    upgrades: List[UpgradeReason] = field(default_factory=list)
    criteria: Dict[str, float] = field(default_factory=dict)
    citations_used: int = 0
    pillar: str = ""
    concept_ids: List[str] = field(default_factory=list)
    graded_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


# ---------------------------------------------------------------------------
# GRADE score thresholds
# ---------------------------------------------------------------------------

LEVEL_THRESHOLDS = [
    (EvidenceLevel.HIGH, 0.8),
    (EvidenceLevel.MODERATE, 0.6),
    (EvidenceLevel.LOW, 0.4),
]

BASE_SCORE = 0.8
DOWNGRADE_AMOUNT = 0.15
UPGRADE_AMOUNT = 0.1
PENALTY_UNVERIFIED = 0.1
PENALTY_LOW_CREDIBILITY = 0.15
BONUS_VERIFIED_CITATION = 0.05
BONUS_MULTI_PILLAR = 0.1


# ---------------------------------------------------------------------------
# EvidenceGrader
# ---------------------------------------------------------------------------


def _level_for_score(score: float) -> EvidenceLevel:
    for level, threshold in LEVEL_THRESHOLDS:
        if score >= threshold:
            return level
    return EvidenceLevel.VERY_LOW


class EvidenceGrader:
    """GRADE-style evidence quality grader.

    Scores claims on a [0, 1] scale, starting at HIGH (0.8) and
    applying downgrades for risk of bias, inconsistency, indirectness,
    and imprecision, with possible upgrades for strong evidence.
    """

    def __init__(
        self,
        trail_manager: Optional[SourceTrailManager] = None,
        contradiction_report: Optional[ContradictionReport] = None,
    ):
        self.trail_manager = trail_manager
        self.contradiction_report = contradiction_report
        self._contradictory_claims: Set[str] = set()

        if self.contradiction_report:
            for pair in self.contradiction_report.pairs:
                self._contradictory_claims.add(pair.claim_a)
                self._contradictory_claims.add(pair.claim_b)

    def grade_claim(self, claim: SourceClaim) -> EvidenceScore:
        if not claim.citations:
            return EvidenceScore(
                claim=claim.claim_text,
                level=EvidenceLevel.VERY_LOW,
                score=0.0,
                downgrades=[DowngradeReason.INDIRECTNESS],
                criteria={"citation_count": 0, "avg_credibility": 0.0},
                pillar=claim.pillar,
                concept_ids=claim.concept_ids,
            )

        score = BASE_SCORE
        downgrades: List[DowngradeReason] = []
        upgrades: List[UpgradeReason] = []

        avg_credibility = self._compute_avg_credibility(claim.citations)
        citation_count = len(claim.citations)
        verified_count = sum(1 for c in claim.citations if c.verified)

        if avg_credibility < 0.5 or verified_count == 0:
            score -= PENALTY_LOW_CREDIBILITY
            downgrades.append(DowngradeReason.RISK_OF_BIAS)

        has_unverified = any(not c.verified for c in claim.citations)
        if has_unverified and verified_count == 0:
            score -= PENALTY_UNVERIFIED

        if claim.claim_text in self._contradictory_claims:
            score -= DOWNGRADE_AMOUNT
            downgrades.append(DowngradeReason.INCONSISTENCY)

        if self._is_vague_claim(claim.claim_text):
            score -= DOWNGRADE_AMOUNT
            downgrades.append(DowngradeReason.IMPRECISION)

        if verified_count >= 2:
            score += BONUS_VERIFIED_CITATION
            upgrades.append(UpgradeReason.LARGE_EFFECT)

        if verified_count >= 3:
            score += BONUS_VERIFIED_CITATION

        if claim.pillar and citation_count >= 2:
            score += BONUS_MULTI_PILLAR * 0.5
            upgrades.append(UpgradeReason.DOSE_RESPONSE)

        score = max(0.0, min(1.0, score))
        level = _level_for_score(score)

        return EvidenceScore(
            claim=claim.claim_text,
            level=level,
            score=round(score, 2),
            downgrades=downgrades,
            upgrades=upgrades,
            criteria={
                "avg_credibility": round(avg_credibility, 2),
                "citation_count": citation_count,
                "verified_count": verified_count,
                "is_contradicted": claim.claim_text in self._contradictory_claims,
                "is_vague": self._is_vague_claim(claim.claim_text),
            },
            citations_used=citation_count,
            pillar=claim.pillar,
            concept_ids=claim.concept_ids,
        )

    def _compute_avg_credibility(self, citations: List[ClaimCitation]) -> float:
        if not citations:
            return 0.0
        return sum(c.credibility_score for c in citations) / len(citations)

    def _is_vague_claim(self, text: str) -> bool:
        vague_patterns = [
            r"\bmay\b", r"\bmight\b", r"\bcould\b",
            r"\bsome\b", r"\bmany\b", r"\bseveral\b",
            r"\boften\b", r"\btypically\b", r"\busually\b",
            r"\bsometimes\b", r"\bpossibly\b", r"\bperhaps\b",
            r"\bseems?\b", r"\bappears?\b",
            r"\bsignificant\b", r"\bsubstantial\b",
            r"\bconsiderable\b", r"\bmuch\b", r"\blittle\b",
        ]
        import re
        lower = text.lower()
        return any(re.search(p, lower) for p in vague_patterns)

    def grade_all(self, claims: List[SourceClaim]) -> List[EvidenceScore]:
        return [self.grade_claim(c) for c in claims]

    def grade_trail_manager(self) -> List[EvidenceScore]:
        if not self.trail_manager:
            return []
        claims: List[SourceClaim] = []
        for trail in self.trail_manager.all_trails():
            claims.extend(trail.claims)
        return self.grade_all(claims)

    def summary(self, scores: List[EvidenceScore]) -> str:
        if not scores:
            return "No evidence to grade."

        level_counts: Dict[str, int] = {}
        total = len(scores)
        avg_score = sum(s.score for s in scores) / total

        for s in scores:
            key = s.level.value
            level_counts[key] = level_counts.get(key, 0) + 1

        parts = [
            f"Graded {total} claims — average score: {avg_score:.2f}",
        ]
        parts.append(
            "  Distribution: " + ", ".join(
                f"{lvl}: {cnt}"
                for lvl, cnt in sorted(level_counts.items())
            )
        )

        total_downgrades = sum(len(s.downgrades) for s in scores)
        total_upgrades = sum(len(s.upgrades) for s in scores)
        parts.append(f"  Total downgrades: {total_downgrades}, upgrades: {total_upgrades}")

        low_scorers = [s for s in scores if s.level == EvidenceLevel.VERY_LOW]
        if low_scorers:
            parts.append(f"  Very-low claims ({len(low_scorers)}):")
            for s in low_scorers[:5]:
                reasons = ", ".join(r.value for r in s.downgrades)
                parts.append(f"    - {s.claim[:60]}... [{reasons}]")

        high_scorers = [s for s in scores if s.level == EvidenceLevel.HIGH]
        if high_scorers:
            parts.append(f"  High-quality claims ({len(high_scorers)}):")
            for s in high_scorers[:3]:
                reasons = ", ".join(r.value for r in s.upgrades)
                parts.append(f"    - {s.claim[:60]}... [score: {s.score}, {reasons}]")

        return "\n".join(parts)


# ---------------------------------------------------------------------------
# Convenience functions
# ---------------------------------------------------------------------------


def grade_evidence(
    trail_manager: SourceTrailManager,
    pillar: Optional[str] = None,
    concept_id: Optional[str] = None,
) -> List[EvidenceScore]:
    """Grade all claims in a SourceTrailManager using GRADE-style scoring.

    Optionally filter by pillar or concept_id.
    Also runs contradiction detection and factors it into grading.
    """
    contradiction_report = detect_contradictions(
        trail_manager, pillar=pillar, concept_id=concept_id
    )

    grader = EvidenceGrader(
        trail_manager=trail_manager,
        contradiction_report=contradiction_report,
    )

    if pillar:
        claims = trail_manager.claims_for_pillar(pillar)
    elif concept_id:
        claims = trail_manager.claims_for_concept(concept_id)
    else:
        claims = []
        for trail in trail_manager.all_trails():
            claims.extend(trail.claims)

    return grader.grade_all(claims)


def quality_summary(scores: List[EvidenceScore]) -> str:
    """Generate a human-readable summary of evidence quality scores."""
    if not scores:
        return "No evidence quality scores available."

    avg = sum(s.score for s in scores) / len(scores)
    levels = {}
    for s in scores:
        levels[s.level.value] = levels.get(s.level.value, 0) + 1

    level_order = ["very_low", "low", "moderate", "high"]
    top = max((s.level.value for s in scores), key=lambda lev: level_order.index(lev))

    parts = [
        f"Evidence quality: {top.upper()} (avg {avg:.2f})",
        f"  Claims graded: {len(scores)}",
        "  Distribution: " + ", ".join(
            f"{lvl}: {cnt}" for lvl, cnt in sorted(levels.items())
        ),
        f"  High: {levels.get('high', 0)}, "
        f"Moderate: {levels.get('moderate', 0)}, "
        f"Low: {levels.get('low', 0)}, "
        f"Very low: {levels.get('very_low', 0)}",
    ]

    return "\n".join(parts)
