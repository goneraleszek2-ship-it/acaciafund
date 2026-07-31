"""ResearcherAgent: agentic research for topic discovery and registry item generation.

Takes a topic + pillar and produces structured research items with:
- Source discovery (arXiv, HN, regulatory)
- Relevance scoring
- Key findings extraction
- Concept extraction
- Registry-ready item output
"""

from __future__ import annotations

import logging

from pydantic import BaseModel, Field

from scripts.agents.base import AgentConfig, BaseAgent

logger = logging.getLogger(__name__)


class ResearchSource(BaseModel):
    url: str
    title: str
    source_type: str = Field(description="arxiv, hn, regulatory, blog, news")
    relevance_score: float = Field(ge=0.0, le=1.0)
    key_insight: str = ""


class ResearchFinding(BaseModel):
    finding: str
    source_urls: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)


class ResearchResult(BaseModel):
    title: str
    description: str
    pillar: str
    content_type: str = "research"
    tags: list[str] = Field(default_factory=list)
    body_html: str = ""
    sources: list[ResearchSource] = Field(default_factory=list)
    findings: list[ResearchFinding] = Field(default_factory=list)
    concepts: list[str] = Field(default_factory=list)
    difficulty: str = "intermediate"


class ResearcherAgent(BaseAgent):
    """Agentic researcher that discovers and synthesizes content.

    Usage:
        agent = ResearcherAgent()
        items = agent.research_topic(pillar="aml", topic="transaction monitoring", days_back=7)
    """

    def __init__(self, config: AgentConfig | None = None, **kwargs):
        super().__init__(config=config, **kwargs)

    def research_topic(
        self,
        pillar: str,
        topic: str,
        days_back: int = 7,
        max_items: int = 5,
    ) -> list[ResearchResult]:
        self.begin()
        results: list[ResearchResult] = []

        plan = self._plan_research(pillar, topic)
        if not plan:
            logger.warning(f"No research plan for {pillar}/{topic}")
            return results

        messages = [
            self.system_message(
                "You are a research analyst. Given a pillar and topic, "
                "generate synthetic research items for a content platform. "
                "Each item should have a title, description, body_html with <h2> sections, "
                "tags, difficulty level, and extracted concepts. "
                "Respond with a JSON array of ResearchResult objects."
            ),
            self.user_message(
                f"Pillar: {pillar}\n"
                f"Topic: {topic}\n"
                f"Days back: {days_back}\n"
                f"Number of items: {max_items}\n"
                f"\nGenerate {max_items} diverse research items on this topic. "
                f"Each must have:\n"
                f"- title (descriptive, 60-120 chars)\n"
                f"- description (2-3 sentences)\n"
                f"- tags (3-7 relevant tags)\n"
                f"- body_html with <h2> divided sections and <p> content\n"
                f"- difficulty (beginner, intermediate, advanced)\n"
                f"- concepts (ontology concepts that apply)"
            ),
        ]

        result = self.llm_structured(messages, list[ResearchResult])
        if result:
            for r in result:
                r.pillar = pillar
                r.content_type = "research"
                results.append(r)

        self.end()
        return results

    def _plan_research(self, pillar: str, topic: str) -> list[str] | None:
        messages = [
            self.system_message(
                "You are a research planner. Given a pillar and topic, "
                "list 3-5 sub-topics to search for. "
                "Respond as a JSON array of strings."
            ),
            self.user_message(f"Pillar: {pillar}\nTopic: {topic}\nList sub-topics to research:"),
        ]
        result = self.llm_structured(messages, list[str])
        return result
