"""GlossaryAgent: generates glossary entries for ontology concepts.

Produces structured glossary entries with:
- Definition (authoritative, pillar-specific)
- Etymology / origin
- Example usage
- Cross-references to related concepts
- External resource links
"""

from __future__ import annotations

import logging

from pydantic import BaseModel, Field

from scripts.agents.base import AgentConfig, BaseAgent

logger = logging.getLogger(__name__)


class GlossaryReference(BaseModel):
    label: str
    url: str = ""
    type: str = Field(description="internal, external, academic")


class GlossaryResult(BaseModel):
    concept: str
    pillar: str
    definition: str
    etymology: str = ""
    example: str = ""
    see_also: list[str] = Field(default_factory=list)
    references: list[GlossaryReference] = Field(default_factory=list)
    difficulty: str = "beginner"


class GlossaryAgent(BaseAgent):
    """Generates glossary entries for ontology concepts.

    Usage:
        agent = GlossaryAgent()
        entry = agent.generate_entry("RAG", pillar="data-engineering")
    """

    def __init__(self, config: AgentConfig | None = None, **kwargs):
        super().__init__(config=config, **kwargs)

    def generate_entry(
        self,
        concept: str,
        pillar: str,
        context: str = "",
    ) -> GlossaryResult | None:
        self.begin()

        messages = [
            self.system_message(
                "You are a technical glossary writer. Given a concept name and pillar, "
                "generate a glossary entry with: definition (1-2 paragraphs), "
                "etymology/origin, practical example, see-also references, "
                "and external resource links. Use precise technical language."
            ),
            self.user_message(
                f"Concept: {concept}\n"
                f"Pillar: {pillar}\n"
                f"Context: {context}\n"
                f"\nGenerate a comprehensive glossary entry."
            ),
        ]

        result = self.llm_structured(messages, GlossaryResult)
        if result is None:
            self.end_with_error(f"Failed to generate glossary for {concept}")
            return None

        result.concept = concept
        result.pillar = pillar

        self.end()
        return result

    def generate_batch(
        self,
        concepts: list[dict[str, str]],
    ) -> list[GlossaryResult]:
        results: list[GlossaryResult] = []
        for spec in concepts:
            try:
                entry = self.generate_entry(
                    concept=spec["concept"],
                    pillar=spec["pillar"],
                    context=spec.get("context", ""),
                )
                if entry:
                    results.append(entry)
                    logger.info(f"  Glossary: {entry.concept}")
            except Exception as e:
                logger.warning(f"  Failed {spec.get('concept', 'unknown')}: {e}")
        return results
