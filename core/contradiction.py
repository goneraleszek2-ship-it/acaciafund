"""Contradiction detection — cross-claim contradiction analysis using source trails.

Provides:
  ContradictionPair, ContradictionReport — data models
  ContradictionDetector — engine for finding contradictions across claims
  detect_contradictions   — find contradictions across a SourceTrailManager
  cluster_contradictions  — group related contradictions by concept
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple

from core.source_trail import (
    SourceClaim,
    SourceTrailManager,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Enums & data models
# ---------------------------------------------------------------------------


class ContradictionType(Enum):
    DIRECT = "direct"           # "X is true" vs "X is false"
    NEGATION = "negation"       # "X prevents Y" vs "X does not prevent Y"
    ANTONYM = "antonym"         # "X increases Y" vs "X decreases Y"
    NUMERIC = "numeric"         # "X=5" vs "X=10"
    TEMPORAL = "temporal"       # "deadline 2023" vs "deadline 2024"
    QUALITATIVE = "qualitative" # "X is effective" vs "X is ineffective"


class ContradictionSeverity(Enum):
    HIGH = "high"      # Direct contradiction with strong supporting citations
    MEDIUM = "medium"  # Indirect contradiction or weak citation support
    LOW = "low"        # Partial divergence, may be contextual


@dataclass
class ContradictionPair:
    """A detected contradiction between two claims."""

    claim_a: str
    claim_b: str
    contradiction_type: ContradictionType
    severity: ContradictionSeverity
    concept_ids: List[str] = field(default_factory=list)
    source_a: str = ""
    source_b: str = ""
    citation_a: str = ""
    citation_b: str = ""
    confidence: float = 0.0
    detected_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


@dataclass
class ContradictionReport:
    """Aggregated contradiction report for a set of claims."""

    total_pairs: int = 0
    by_type: Dict[str, int] = field(default_factory=dict)
    by_severity: Dict[str, int] = field(default_factory=dict)
    by_concept: Dict[str, int] = field(default_factory=dict)
    pairs: List[ContradictionPair] = field(default_factory=list)
    generated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def __post_init__(self):
        self.total_pairs = len(self.pairs)
        self.by_type = {}
        self.by_severity = {}
        self.by_concept = {}

        for pair in self.pairs:
            t = pair.contradiction_type.value
            self.by_type[t] = self.by_type.get(t, 0) + 1

            s = pair.severity.value
            self.by_severity[s] = self.by_severity.get(s, 0) + 1

            for cid in pair.concept_ids:
                self.by_concept[cid] = self.by_concept.get(cid, 0) + 1


# ---------------------------------------------------------------------------
# Contradiction patterns
# ---------------------------------------------------------------------------

# Pairs of opposite/contrasting terms
ANTONYM_PAIRS: List[Tuple[str, str]] = [
    ("increases", "decreases"),
    ("raises", "lowers"),
    ("improves", "worsens"),
    ("strengthens", "weakens"),
    ("accelerates", "slows"),
    ("expands", "contracts"),
    ("grows", "shrinks"),
    ("rises", "falls"),
    ("wins", "loses"),
    ("gains", "losses"),
    ("profits", "losses"),
    ("positive", "negative"),
    ("effective", "ineffective"),
    ("efficient", "inefficient"),
    ("stable", "unstable"),
    ("safe", "unsafe"),
    ("secure", "insecure"),
    ("compliant", "non-compliant"),
    ("valid", "invalid"),
    ("required", "optional"),
    ("mandatory", "voluntary"),
    ("transparent", "opaque"),
    ("liquid", "illiquid"),
    ("bullish", "bearish"),
    ("buy", "sell"),
    ("long", "short"),
    ("overvalued", "undervalued"),
    ("correlated", "uncorrelated"),
    ("centralized", "decentralized"),
    ("regulated", "unregulated"),
    ("authorized", "unauthorized"),
    ("permitted", "prohibited"),
    ("enabled", "disabled"),
    ("active", "inactive"),
]

# Negation patterns
NEGATION_PATTERNS = [
    r"\bnot\s+\w+",
    r"\bdoesn'?t\s+\w+",
    r"\bdon'?t\s+\w+",
    r"\bwon'?t\s+\w+",
    r"\bcan'?t\s+\w+",
    r"\bcannot\s+\w+",
    r"\bno\s+\w+",
    r"\bnever\s+\w+",
    r"\bwithout\s+\w+",
    r"\black(?:s|ed|ing)?\s+of\s+\w+",
    r"\babsence\s+of\s+\w+",
]

# Numeric pattern
NUMERIC_PATTERN = re.compile(r"\b\d+(?:\.\d+)?(?:\s*[%]|\s*(?:bps|bp|basis\s*points|USD|EUR|GBP))?", re.IGNORECASE)


# ---------------------------------------------------------------------------
# ContradictionDetector
# ---------------------------------------------------------------------------


class ContradictionDetector:
    """Detects contradictions among claims using lexical patterns."""

    def __init__(self, trail_manager: Optional[SourceTrailManager] = None):
        self.trail_manager = trail_manager
        self._antonym_index: Dict[str, str] = {}
        self._build_antonym_index()

    def _build_antonym_index(self):
        for a, b in ANTONYM_PAIRS:
            self._antonym_index[a] = b
            self._antonym_index[b] = a

    def has_negation(self, text: str) -> bool:
        lower = text.lower()
        return any(re.search(p, lower) for p in NEGATION_PATTERNS)

    def check_negation_contradiction(self, claim_a: str, claim_b: str) -> bool:
        """Check if one claim negates the other."""
        neg_a = self.has_negation(claim_a)
        neg_b = self.has_negation(claim_b)
        return neg_a != neg_b

    def find_antonym(self, word: str) -> Optional[str]:
        return self._antonym_index.get(word.lower())

    def check_antonym_contradiction(self, claim_a: str, claim_b: str) -> Optional[Tuple[str, str]]:
        words_a = set(claim_a.lower().split())
        words_b = set(claim_b.lower().split())

        for word in words_a:
            antonym = self.find_antonym(word)
            if antonym and antonym in words_b:
                return (word, antonym)
        return None

    def extract_numeric_values(self, text: str) -> List[str]:
        return NUMERIC_PATTERN.findall(text)

    def check_numeric_contradiction(self, claim_a: str, claim_b: str) -> bool:
        nums_a = self.extract_numeric_values(claim_a)
        nums_b = self.extract_numeric_values(claim_b)
        if not nums_a or not nums_b:
            return False
        for na in nums_a:
            for nb in nums_b:
                if na != nb:
                    num_a = self._parse_number(na)
                    num_b = self._parse_number(nb)
                    if num_a is not None and num_b is not None and num_a != num_b:
                        return True
        return False

    def _parse_number(self, token: str) -> Optional[float]:
        clean = re.sub(r"[^\d.]", "", token)
        try:
            return float(clean)
        except ValueError:
            return None

    def compute_similarity(self, claim_a: str, claim_b: str) -> float:
        """Jaccard similarity of non-stopword tokens."""
        stopwords = {
            "a", "an", "the", "is", "are", "was", "were", "has", "have", "had",
            "do", "does", "did", "will", "would", "can", "could", "may", "might",
            "shall", "should", "to", "of", "in", "for", "on", "with", "at", "by",
            "from", "and", "or", "but", "not", "no", "this", "that", "it", "its",
        }
        tokens_a = {w for w in claim_a.lower().split() if w not in stopwords and len(w) > 2}
        tokens_b = {w for w in claim_b.lower().split() if w not in stopwords and len(w) > 2}
        if not tokens_a or not tokens_b:
            return 0.0
        intersection = tokens_a & tokens_b
        union = tokens_a | tokens_b
        return len(intersection) / len(union)

    def detect_pair(self, claim_a: SourceClaim, claim_b: SourceClaim) -> Optional[ContradictionPair]:
        """Check if two claims contradict each other. Returns ContradictionPair or None."""
        sim = self.compute_similarity(claim_a.claim_text, claim_b.claim_text)
        if sim < 0.3:
            return None

        shared_concepts = set(claim_a.concept_ids) & set(claim_b.concept_ids)
        concept_ids = list(shared_concepts) if shared_concepts else []

        contradiction_type = None

        if self.check_negation_contradiction(claim_a.claim_text, claim_b.claim_text):
            contradiction_type = ContradictionType.NEGATION
        elif self.check_antonym_contradiction(claim_a.claim_text, claim_b.claim_text):
            contradiction_type = ContradictionType.ANTONYM
        elif self.check_numeric_contradiction(claim_a.claim_text, claim_b.claim_text):
            contradiction_type = ContradictionType.NUMERIC

        if contradiction_type is None:
            return None

        citations_a = claim_a.citations
        citations_b = claim_b.citations
        verified_a = any(c.verified for c in citations_a) if citations_a else False
        verified_b = any(c.verified for c in citations_b) if citations_b else False

        if verified_a and verified_b:
            severity = ContradictionSeverity.HIGH
        elif verified_a or verified_b:
            severity = ContradictionSeverity.MEDIUM
        else:
            severity = ContradictionSeverity.LOW

        confidence = sim * (0.7 if verified_a or verified_b else 0.3)

        return ContradictionPair(
            claim_a=claim_a.claim_text,
            claim_b=claim_b.claim_text,
            contradiction_type=contradiction_type,
            severity=severity,
            concept_ids=concept_ids,
            source_a=claim_a.pillar,
            source_b=claim_b.pillar,
            citation_a=citations_a[0].url if citations_a else "",
            citation_b=citations_b[0].url if citations_b else "",
            confidence=round(confidence, 2),
        )

    def detect_all(self, claims: List[SourceClaim]) -> ContradictionReport:
        """Detect all contradictions within a list of claims."""
        pairs: List[ContradictionPair] = []
        seen: Set[Tuple[str, str]] = set()

        for i in range(len(claims)):
            for j in range(i + 1, len(claims)):
                pair_key = (claims[i].claim_text, claims[j].claim_text)
                if pair_key in seen:
                    continue
                seen.add(pair_key)

                result = self.detect_pair(claims[i], claims[j])
                if result:
                    pairs.append(result)

        pairs.sort(key=lambda p: p.confidence, reverse=True)
        return ContradictionReport(pairs=pairs)


# ---------------------------------------------------------------------------
# Convenience functions
# ---------------------------------------------------------------------------


def detect_contradictions(
    trail_manager: SourceTrailManager,
    pillar: Optional[str] = None,
    concept_id: Optional[str] = None,
) -> ContradictionReport:
    """Run contradiction detection across a SourceTrailManager.

    Args:
        trail_manager: Source trail manager with loaded claims.
        pillar: Optional pillar filter.
        concept_id: Optional concept ID filter.

    Returns:
        ContradictionReport with all detected contradictions.
    """
    if pillar:
        claims = trail_manager.claims_for_pillar(pillar)
    elif concept_id:
        claims = trail_manager.claims_for_concept(concept_id)
    else:
        claims = []
        for trail in trail_manager.all_trails():
            claims.extend(trail.claims)

    detector = ContradictionDetector(trail_manager=trail_manager)
    return detector.detect_all(claims)


def cluster_contradictions(report: ContradictionReport) -> Dict[str, List[ContradictionPair]]:
    """Group contradictions by concept ID."""
    clusters: Dict[str, List[ContradictionPair]] = {}
    for pair in report.pairs:
        for cid in pair.concept_ids:
            clusters.setdefault(cid, []).append(pair)
        if not pair.concept_ids:
            clusters.setdefault("unassigned", []).append(pair)
    return clusters


def contradiction_summary(report: ContradictionReport) -> str:
    """Generate a human-readable summary of a contradiction report."""
    parts = [
        f"Found {report.total_pairs} contradiction pairs",
    ]

    if report.by_type:
        type_counts = ", ".join(f"{t}: {c}" for t, c in sorted(report.by_type.items()))
        parts.append(f"  Types: {type_counts}")

    if report.by_severity:
        sev_counts = ", ".join(f"{s}: {c}" for s, c in sorted(report.by_severity.items()))
        parts.append(f"  Severity: {sev_counts}")

    if report.by_concept:
        concept_counts = ", ".join(
            f"{cid}: {c}"
            for cid, c in sorted(report.by_concept.items(), key=lambda x: -x[1])[:10]
        )
        parts.append(f"  Top concepts: {concept_counts}")

    return "\n".join(parts)
