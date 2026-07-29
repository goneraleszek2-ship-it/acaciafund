"""Source trail — claim→citation mapping and source attribution.

Provides:
  ClaimCitation, SourceClaim, EvidenceTrail — data models
  SourceTrailManager    — registry for managing claim→citation trails
  build_trails_for_item — extract claims and build trails from content
  verify_citations      — bulk citation health check against known sources
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set

from core.ontology import (
    OntologyManager,
    ResourceLink,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass
class ClaimCitation:
    """A specific source reference supporting a claim."""

    url: str
    title: str = ""
    accessed_date: str = ""
    snippet: str = ""
    credibility_score: float = 0.5
    source_name: str = ""
    verified: bool = False
    http_status: Optional[int] = None


@dataclass
class SourceClaim:
    """A claim extracted from content with supporting citations."""

    claim_text: str
    context: str = ""
    pillar: str = ""
    concept_ids: List[str] = field(default_factory=list)
    citations: List[ClaimCitation] = field(default_factory=list)
    confidence: float = 1.0


@dataclass
class EvidenceTrail:
    """Full trail from content item through claims to source verification."""

    content_slug: str = ""
    content_title: str = ""
    claims: List[SourceClaim] = field(default_factory=list)
    total_claims: int = 0
    verified_citations: int = 0
    unverified_citations: int = 0
    sources_used: Set[str] = field(default_factory=set)
    built_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def __post_init__(self):
        self.total_claims = len(self.claims)
        self.verified_citations = sum(
            1 for c in self.claims for cit in c.citations if cit.verified
        )
        self.unverified_citations = sum(
            1 for c in self.claims for cit in c.citations if not cit.verified
        )
        self.sources_used = {
            cit.url for c in self.claims for cit in c.citations
        }


# ---------------------------------------------------------------------------
# SourceTrailManager
# ---------------------------------------------------------------------------


class SourceTrailManager:
    """Central registry for managing claim→citation source trails."""

    def __init__(self, ontology: Optional[OntologyManager] = None):
        self._trails: Dict[str, EvidenceTrail] = {}
        self.ontology = ontology

    # --- Trail CRUD ---

    def add_trail(self, slug: str, trail: EvidenceTrail) -> None:
        self._trails[slug] = trail

    def get_trail(self, slug: str) -> Optional[EvidenceTrail]:
        return self._trails.get(slug)

    def remove_trail(self, slug: str) -> bool:
        return self._trails.pop(slug, None) is not None

    def all_trails(self) -> List[EvidenceTrail]:
        return list(self._trails.values())

    def trail_count(self) -> int:
        return len(self._trails)

    def claims_for_pillar(self, pillar: str) -> List[SourceClaim]:
        claims: List[SourceClaim] = []
        for trail in self._trails.values():
            for claim in trail.claims:
                if claim.pillar == pillar:
                    claims.append(claim)
        return claims

    def claims_for_concept(self, concept_id: str) -> List[SourceClaim]:
        claims: List[SourceClaim] = []
        for trail in self._trails.values():
            for claim in trail.claims:
                if concept_id in claim.concept_ids:
                    claims.append(claim)
        return claims

    # --- Verification ---

    def verify_citations(self) -> int:
        """Check all citations against known resources in ontology.

        Returns count of newly verified citations.
        """
        if not self.ontology:
            return 0

        known_urls: Dict[str, ResourceLink] = {}
        for rl in self.ontology._resource_links:
            known_urls[rl.url] = rl

        count = 0
        for trail in self._trails.values():
            for claim in trail.claims:
                for citation in claim.citations:
                    if citation.verified:
                        continue
                    known = known_urls.get(citation.url)
                    if known:
                        citation.verified = True
                        citation.http_status = known.http_status
                        citation.credibility_score = known.credibility_score
                        count += 1

        return count

    # --- Export ---

    def to_dict(self) -> Dict:
        return {
            slug: {
                "content_slug": trail.content_slug,
                "content_title": trail.content_title,
                "total_claims": trail.total_claims,
                "verified_citations": trail.verified_citations,
                "unverified_citations": trail.unverified_citations,
                "sources_used": list(trail.sources_used),
                "claims": [
                    {
                        "claim_text": c.claim_text,
                        "context": c.context,
                        "pillar": c.pillar,
                        "concept_ids": c.concept_ids,
                        "citations": [
                            {
                                "url": cit.url,
                                "title": cit.title,
                                "source_name": cit.source_name,
                                "verified": cit.verified,
                                "http_status": cit.http_status,
                                "credibility_score": cit.credibility_score,
                            }
                            for cit in c.citations
                        ],
                        "confidence": c.confidence,
                    }
                    for c in trail.claims
                ],
                "built_at": trail.built_at,
            }
            for slug, trail in self._trails.items()
        }

    @classmethod
    def from_dict(
        cls, data: Dict, ontology: Optional[OntologyManager] = None
    ) -> SourceTrailManager:
        mgr = cls(ontology=ontology)
        for slug, d in data.items():
            claims = [
                SourceClaim(
                    claim_text=c["claim_text"],
                    context=c.get("context", ""),
                    pillar=c.get("pillar", ""),
                    concept_ids=c.get("concept_ids", []),
                    citations=[
                        ClaimCitation(
                            url=cit["url"],
                            title=cit.get("title", ""),
                            source_name=cit.get("source_name", ""),
                            verified=cit.get("verified", False),
                            http_status=cit.get("http_status"),
                            credibility_score=cit.get("credibility_score", 0.5),
                        )
                        for cit in c.get("citations", [])
                    ],
                    confidence=c.get("confidence", 1.0),
                )
                for c in d.get("claims", [])
            ]
            mgr._trails[slug] = EvidenceTrail(
                content_slug=d.get("content_slug", slug),
                content_title=d.get("content_title", ""),
                claims=claims,
            )
        return mgr


# ---------------------------------------------------------------------------
# Trail building utilities
# ---------------------------------------------------------------------------


def extract_claims_from_text(
    text: str,
    min_length: int = 40,
    max_length: int = 300,
) -> List[str]:
    """Extract claim-like sentences from text.

    A claim is a sentence containing at least one factive verb or
    analytical assertion pattern.
    """
    if not text:
        return []

    sentences = re.split(r"(?<=[.!?])\s+", text)
    claims: List[str] = []

    claim_indicators = [
        "is", "are", "was", "were", "has", "have", "had",
        "shows", "demonstrates", "indicates", "suggests",
        "proves", "confirms", "reveals", "implies",
        "means", "requires", "enables", "causes",
        "leads to", "results in", "correlates with",
        "increases", "decreases", "affects", "impacts",
        "provides", "ensures", "prevents", "detects",
    ]

    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence) < min_length or len(sentence) > max_length:
            continue
        lower = sentence.lower()
        if any(indicator in lower for indicator in claim_indicators):
            claims.append(sentence)

    return claims


def extract_urls_from_text(text: str) -> List[str]:
    """Extract URLs from text that could serve as citations."""
    raw_pattern = re.compile(r"https?://[^\s<>\"'()]+")
    trailing_punct = re.compile(r"[.,!;?]+$")
    urls = list(set(raw_pattern.findall(text)))
    cleaned = []
    for url in urls:
        clean = trailing_punct.sub("", url)
        if clean:
            cleaned.append(clean)
    return cleaned


def match_citations_to_sources(
    urls: List[str],
    ontology: OntologyManager,
) -> Dict[str, Optional[ResourceLink]]:
    """Match extracted URLs to known ResourceLinks in the ontology."""
    known: Dict[str, ResourceLink] = {}
    for rl in ontology._resource_links:
        known[rl.url] = rl

    result: Dict[str, Optional[ResourceLink]] = {}
    for url in urls:
        result[url] = known.get(url)
    return result


def build_trails_for_item(
    slug: str,
    title: str,
    body: str,
    pillar: str = "",
    concept_ids: Optional[List[str]] = None,
    ontology: Optional[OntologyManager] = None,
) -> EvidenceTrail:
    """Build an EvidenceTrail from a content item's body text."""
    claim_texts = extract_claims_from_text(body)
    raw_urls = extract_urls_from_text(body)

    url_to_source: Dict[str, Optional[ResourceLink]] = {}
    if ontology and raw_urls:
        url_to_source = match_citations_to_sources(raw_urls, ontology)

    claims: List[SourceClaim] = []
    for ct in claim_texts:
        claim_urls = extract_urls_from_text(ct)
        citations: List[ClaimCitation] = []
        for url in claim_urls:
            source = url_to_source.get(url)
            citations.append(
                ClaimCitation(
                    url=url,
                    title=source.title if source else "",
                    source_name=source.source_org if source else "",
                    verified=source is not None,
                    credibility_score=source.credibility_score if source else 0.5,
                    http_status=source.http_status if source else None,
                )
            )

        claims.append(
            SourceClaim(
                claim_text=ct,
                context=ct[:120],
                pillar=pillar,
                concept_ids=concept_ids or [],
                citations=citations,
                confidence=1.0 if citations else 0.5,
            )
        )

    return EvidenceTrail(
        content_slug=slug,
        content_title=title,
        claims=claims,
    )
