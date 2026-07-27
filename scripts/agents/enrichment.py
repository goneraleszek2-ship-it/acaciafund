"""EnrichmentAgent: LLM-powered semantic enrichment for registry items.

Takes a registry item and produces:
- Semantic tags (beyond regex keyword matching)
- Signal Quality Index (SQI) with reasoning
- Cross-pillar connections
- Concept extraction with evidence
- Source authority assessment
"""

from __future__ import annotations

import logging
from typing import Any

from pydantic import BaseModel, Field

from core.agent_tools import RiskLevel
from scripts.agents.base import AgentConfig, AgentResult, BaseAgent

logger = logging.getLogger(__name__)


class EnrichedTag(BaseModel):
    tag: str = Field(description="Canonical tag name")
    confidence: float = Field(ge=0.0, le=1.0, description="LLM confidence in this tag")
    reasoning: str = Field(description="Why this tag applies")


class ExtractedConcept(BaseModel):
    concept: str = Field(description="Extracted concept or entity name")
    evidence: str = Field(description="Excerpt from the content supporting this")
    confidence: float = Field(ge=0.0, le=1.0)


class SourceAssessment(BaseModel):
    source_type: str = Field(description="arxiv, pubmed, regulatory, industry, blog, news")
    authority_score: float = Field(ge=0.0, le=1.0)
    confidence: str = Field(description="high, medium, low")


class CrossPillarLink(BaseModel):
    target_pillar: str = Field(description="aml, stock, or data-engineering")
    topic: str = Field(description="Related topic in that pillar")
    relevance: float = Field(ge=0.0, le=1.0)
    reasoning: str = Field(description="Nature of the connection")


class EnrichmentResult(BaseModel):
    tags: list[EnrichedTag] = Field(description="Semantic tags")
    sqi_score: float = Field(ge=0.01, le=0.99, description="Signal Quality Index")
    sqi_reasoning: str = Field(description="Breakdown of SQI factors")
    concepts: list[ExtractedConcept] = Field(description="Key concepts found")
    source_assessment: SourceAssessment | None = None
    cross_pillar_links: list[CrossPillarLink] = Field(default_factory=list)
    summary: str = Field(description="One-paragraph enrichment summary")


class EnrichmentAgent(BaseAgent):
    """LLM-powered enrichment for a single registry item.

    Usage:
        agent = EnrichmentAgent()
        result = agent.enrich_item(title="...", description="...", body_html="...", source_url="...")
    """

    def __init__(self, config: AgentConfig | None = None, **kwargs):
        super().__init__(config=config, **kwargs)

    def enrich_item(
        self,
        title: str,
        description: str = "",
        body_html: str = "",
        source_url: str = "",
        source_breakdown: dict[str, int] | None = None,
    ) -> EnrichmentResult:
        self.begin()
        body_preview = self._truncate_body(body_html, 3000)
        source_summary = self._summarize_sources(source_breakdown)

        messages = [
            self.system_message(
                "You are a research enrichment analyst. Given a content item, "
                "extract structured metadata including semantic tags, concepts, "
                "Signal Quality Index, and cross-pillar connections. "
                "Respond with valid JSON matching the required schema."
            ),
            self.user_message(
                f"Title: {title}\n"
                f"Description: {description[:500]}\n"
                f"Body preview: {body_preview[:2000]}\n"
                f"Source URL: {source_url}\n"
                f"Source breakdown: {source_summary}\n"
                f"\nExtract: tags (canonical + confidence + reasoning), "
                f"concepts (with evidence excerpts), SQI score (0.01-0.99) with reasoning, "
                f"source assessment (type + authority), cross-pillar links if any, "
                f"and a brief enrichment summary."
            ),
        ]

        result = self.llm_structured(messages, EnrichmentResult)
        if result is None:
            return self._fallback_result(title)

        self.end()
        return result  # type: ignore[return-value]

    def enrich_batch(
        self,
        items: list[dict[str, Any]],
        *,
        max_items: int = 10,
    ) -> list[EnrichmentResult]:
        results: list[EnrichmentResult] = []
        for i, item in enumerate(items[:max_items]):
            try:
                result = self.enrich_item(
                    title=item.get("title", ""),
                    description=item.get("description", ""),
                    body_html=item.get("body_html", ""),
                    source_url=item.get("source_url", ""),
                    source_breakdown=item.get("source_breakdown"),
                )
                results.append(result)
                logger.info(f"  [{i+1}/{min(max_items, len(items))}] enriched: {item.get('title', '')[:60]}")
            except Exception as e:
                logger.warning(f"  [{i+1}/{min(max_items, len(items))}] failed: {e}")
                results.append(self._fallback_result(item.get("title", "")))
        return results

    def _fallback_result(self, title: str) -> EnrichmentResult:
        return EnrichmentResult(
            tags=[],
            sqi_score=0.3,
            sqi_reasoning="Fallback: LLM enrichment unavailable",
            concepts=[],
            summary=f"Fallback enrichment for: {title[:120]}",
        )

    @staticmethod
    def _truncate_body(body: str, max_chars: int = 3000) -> str:
        if not body:
            return ""
        text = body[:max_chars]
        if len(body) > max_chars:
            text += "... [truncated]"
        return text

    @staticmethod
    def _summarize_sources(breakdown: dict[str, int] | None) -> str:
        if not breakdown:
            return "Not specified"
        parts = [f"{k}: {v}" for k, v in sorted(breakdown.items())]
        return ", ".join(parts) if parts else "Not specified"
