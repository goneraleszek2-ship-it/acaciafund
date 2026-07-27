"""LearnModuleGenerator: generates interactive learn modules from ontology concepts.

Produces structured learn content with:
- Multi-section body with code examples (matching existing MODULES format)
- Bloom taxonomy questions (6 levels)
- Flashcards (front/back pairs)
- Prerequisites from ontology
- Cross-pillar connections
"""

from __future__ import annotations

import logging
from typing import Any

from pydantic import BaseModel, Field

from scripts.agents.base import AgentConfig, AgentResult, BaseAgent

logger = logging.getLogger(__name__)


class ModuleSection(BaseModel):
    heading: str
    content: str = Field(description="HTML content including <p>, <pre><code>, <ul>")


class BloomQuestion(BaseModel):
    level: str = Field(description="remember, understand, apply, analyze, evaluate, create")
    question: str


class Flashcard(BaseModel):
    front: str
    back: str


class LearnModuleResult(BaseModel):
    slug: str
    title: str
    pillar: str
    tags: list[str] = Field(default_factory=list)
    difficulty: str = "intermediate"
    prerequisites: list[str] = Field(default_factory=list)
    description: str
    sections: list[ModuleSection] = Field(default_factory=list)
    bloom_questions: list[BloomQuestion] = Field(default_factory=list)
    flashcards: list[Flashcard] = Field(default_factory=list)


class LearnModuleGenerator(BaseAgent):
    """Generates interactive learn modules from ontology concept seeds.

    Usage:
        generator = LearnModuleGenerator()
        module = generator.generate("rag-architecture", pillar="data-engineering")
    """

    def __init__(self, config: AgentConfig | None = None, **kwargs):
        super().__init__(config=config, **kwargs)

    def generate(
        self,
        topic_slug: str,
        pillar: str,
        title: str | None = None,
        tags: list[str] | None = None,
        num_sections: int = 5,
    ) -> LearnModuleResult | None:
        self.begin()
        topic_label = title or topic_slug.replace("-", " ").title()

        messages = [
            self.system_message(
                "You are a curriculum designer. Generate an interactive learn module "
                "with hands-on code examples, Bloom taxonomy questions, and flashcards. "
                "Use the following structure exactly: 5+ sections with headings and HTML content, "
                "6 Bloom questions (one per level), and 3-5 flashcards. "
                "Content must be technical, accurate, and production-oriented."
            ),
            self.user_message(
                f"Topic slug: {topic_slug}\n"
                f"Title: {topic_label}\n"
                f"Pillar: {pillar}\n"
                f"Tags: {tags or [pillar, topic_slug]}\n"
                f"Number of sections: {num_sections}\n"
                f"\nGenerate a complete learn module. Each section must have:\n"
                f"- heading (short, descriptive)\n"
                f"- content (HTML with <p>, <pre><code>, <ul> where appropriate)\n"
                f"- Include real code examples in <pre><code class='language-python'>(or other lang)\n"
                f"\nBloom questions must cover: remember, understand, apply, analyze, evaluate, create.\n"
                f"Flashcards: 3-5 quality front/back pairs."
            ),
        ]

        result = self.llm_structured(messages, LearnModuleResult)
        if result is None:
            self.end_with_error(f"Failed to generate module for {topic_slug}")
            return None

        result.slug = f"{pillar}/learn/{topic_slug}" if "/" not in topic_slug else topic_slug
        result.pillar = pillar
        if tags:
            result.tags = tags
        if title:
            result.title = title

        self.end()
        return result

    def generate_batch(
        self,
        topics: list[dict[str, Any]],
    ) -> list[LearnModuleResult]:
        results: list[LearnModuleResult] = []
        for spec in topics:
            try:
                module = self.generate(
                    topic_slug=spec["slug"],
                    pillar=spec["pillar"],
                    title=spec.get("title"),
                    tags=spec.get("tags"),
                )
                if module:
                    results.append(module)
                    logger.info(f"  Generated: {module.title}")
            except Exception as e:
                logger.warning(f"  Failed {spec.get('slug', 'unknown')}: {e}")
        return results
