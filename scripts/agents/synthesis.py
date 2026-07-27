"""SynthesisAgent: structured multi-source research synthesis.

Takes a topic + list of source items and produces:
- Structured synthesis with citations
- Key insights ranked by confidence
- Contradictions / disagreements between sources
- Knowledge gaps
- Cross-pillar relevance
"""

from __future__ import annotations

import logging
from typing import Any

from pydantic import BaseModel, Field

from scripts.agents.base import AgentConfig, AgentResult, BaseAgent

logger = logging.getLogger(__name__)


class SynthesisInsight(BaseModel):
    insight: str
    confidence: float = Field(ge=0.0, le=1.0)
    source_urls: list[str] = Field(default_factory=list)
    supporting_quotes: list[str] = Field(default_factory=list)


class SynthesisContradiction(BaseModel):
    topic: str
    view_a: str
    view_b: str
    source_a: str
    source_b: str
    resolution: str = ""


class SynthesisGap(BaseModel):
    gap: str
    importance: str = Field(description="high, medium, low")
    suggested_research: str = ""


class SynthesisResult(BaseModel):
    topic: str
    pillar: str
    summary: str
    insights: list[SynthesisInsight] = Field(default_factory=list)
    contradictions: list[SynthesisContradiction] = Field(default_factory=list)
    gaps: list[SynthesisGap] = Field(default_factory=list)
    cross_pillar_relevance: list[dict[str, str]] = Field(default_factory=list)
    overall_confidence: float = Field(ge=0.0, le=1.0)


class SynthesisAgent(BaseAgent):
    """Generates structured multi-source synthesis.

    Usage:
        agent = SynthesisAgent()
        result = agent.synthesize(
            topic="Machine learning for AML",
            pillar="aml",
            sources=[{"url": "...", "title": "...", "content": "..."}]
        )
    """

    def __init__(self, config: AgentConfig | None = None, **kwargs):
        super().__init__(config=config, **kwargs)

    def synthesize(
        self,
        topic: str,
        pillar: str,
        sources: list[dict[str, str]],
        max_sources: int = 10,
    ) -> SynthesisResult | None:
        self.begin()

        source_summaries = self._summarize_sources(sources, max_sources)

        messages = [
            self.system_message(
                "You are a research synthesis analyst. Given a topic and multiple sources, "
                "produce a structured synthesis with ranked insights, contradictions, "
                "knowledge gaps, and confidence assessment. "
                "Cite specific sources for each claim."
            ),
            self.user_message(
                f"Topic: {topic}\n"
                f"Pillar: {pillar}\n"
                f"Sources ({len(sources[:max_sources])}):\n"
                f"{source_summaries}\n"
                f"\nProduce a synthesis with:\n"
                f"- summary (2-3 paragraphs)\n"
                f"- insights ranked by confidence (with source citations and quotes)\n"
                f"- contradictions (differing views with source attribution)\n"
                f"- gaps (what's unknown or underexplored)\n"
                f"- cross-pillar relevance (connections to other pillars)\n"
                f"- overall confidence (0.0-1.0)"
            ),
        ]

        result = self.llm_structured(messages, SynthesisResult)
        if result is None:
            self.end_with_error(f"Failed to synthesize {topic}")
            return None

        result.topic = topic
        result.pillar = pillar

        self.end()
        return result

    @staticmethod
    def _summarize_sources(sources: list[dict[str, str]], max_sources: int) -> str:
        lines: list[str] = []
        for i, src in enumerate(sources[:max_sources]):
            title = src.get("title", "Untitled")[:120]
            url = src.get("url", "")[:80]
            content = src.get("content", "")[:500].replace("\n", " ")
            lines.append(f"[{i+1}] {title}\n    URL: {url}\n    Content: {content}")
        return "\n\n".join(lines) if lines else "No sources provided"
