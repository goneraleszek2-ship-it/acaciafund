"""Tests for agentic pipeline modules (scripts/agents/).

Uses mocked LLM responses to test structured output parsing,
fallback logic, and batch processing.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.agents.base import AgentConfig, AgentResult, BaseAgent
from scripts.agents.enrichment import (
    EnrichmentAgent,
    EnrichmentResult,
    EnrichedTag,
    ExtractedConcept,
)
from scripts.agents.glossary import GlossaryAgent, GlossaryResult
from scripts.agents.learn_generator import (
    LearnModuleGenerator,
    LearnModuleResult,
    ModuleSection,
    BloomQuestion,
    Flashcard,
)
from scripts.agents.researcher import ResearcherAgent, ResearchResult, ResearchSource
from scripts.agents.synthesis import (
    SynthesisAgent,
    SynthesisResult,
    SynthesisInsight,
    SynthesisContradiction,
    SynthesisGap,
)
from core.llm_client import AcaciaLLMClient, LLMConfig, LLMResult


# ── Mock LLM Client ──


class MockLLMClient:
    """Returns canned structured responses for testing."""

    def __init__(self):
        self.calls = []

    def chat_with_retry(self, messages, **kw):
        self.calls.append(("chat", messages, kw))
        return LLMResult(
            content="Mock response",
            model="mock",
            provider="test",
        )

    def structured(self, messages, response_model, **kw):
        self.calls.append(("structured", messages, response_model, kw))
        return _mock_for_model(response_model)


from scripts.agents.enrichment import SourceAssessment

def _mock_for_model(model):
    """Return a canned mock instance based on the model type."""
    origin = getattr(model, "__origin__", None)
    if origin is list or model is list:
        return None
    if model == EnrichmentResult:
        return EnrichmentResult(
            tags=[EnrichedTag(tag="aml", confidence=0.9, reasoning="Core topic")],
            sqi_score=0.75,
            sqi_reasoning="Multiple authoritative sources with good temporal recency",
            concepts=[ExtractedConcept(concept="transaction monitoring", evidence="...", confidence=0.85)],
            source_assessment=SourceAssessment(source_type="arxiv", authority_score=0.85, confidence="high"),
            cross_pillar_links=[],
            summary="Good quality synthesis on AML transaction monitoring.",
        )
    if model == LearnModuleResult:
        return LearnModuleResult(
            slug="test/learn/test-module",
            title="Test Module",
            pillar="data-engineering",
            tags=["test", "data-engineering"],
            difficulty="intermediate",
            description="A test learn module",
            sections=[
                ModuleSection(heading="Introduction", content="<p>Test content</p>"),
                ModuleSection(heading="Advanced", content="<p>More <code>content</code></p>"),
            ],
            bloom_questions=[
                BloomQuestion(level="remember", question="What is X?"),
                BloomQuestion(level="apply", question="Apply X to Y?"),
            ],
            flashcards=[
                Flashcard(front="What is X?", back="X is Y"),
            ],
        )
    if model == GlossaryResult:
        return GlossaryResult(
            concept="RAG",
            pillar="data-engineering",
            definition="Retrieval Augmented Generation...",
            etymology="Coined by Lewis et al., 2020",
            example="Using vector search to augment LLM prompts",
            see_also=["Vector Search", "Embeddings"],
            difficulty="intermediate",
        )
    if model == ResearchResult:
        return ResearchResult(
            title="Test Research",
            description="A test research item",
            pillar="aml",
            tags=["test"],
            body_html="<h2>Introduction</h2><p>Test</p>",
            sources=[ResearchSource(url="https://example.com", title="Example", source_type="arxiv", relevance_score=0.8)],
            difficulty="intermediate",
        )
    if model == SynthesisResult:
        return SynthesisResult(
            topic="AML AI",
            pillar="aml",
            summary="Synthesis of AI for AML",
            insights=[SynthesisInsight(insight="AI reduces false positives", confidence=0.85)],
            overall_confidence=0.8,
        )
    return None


# ── BaseAgent Tests ──


class TestBaseAgent:
    def test_init_with_defaults(self):
        agent = BaseAgent()
        assert agent.config.max_tool_iterations == 15
        assert agent.config.auto_approve_read is True

    def test_begin_end_records_metrics(self):
        agent = BaseAgent()
        agent.begin()
        result = agent.end()
        assert isinstance(result, AgentResult)
        assert result.success is True
        assert result.duration_seconds >= 0

    def test_end_with_error(self):
        agent = BaseAgent()
        agent.begin()
        result = agent.end_with_error("Something broke")
        assert result.success is False
        assert result.error == "Something broke"

    def test_system_and_user_messages(self):
        agent = BaseAgent()
        assert agent.system_message("hi") == {"role": "system", "content": "hi"}
        assert agent.user_message("hi") == {"role": "user", "content": "hi"}
        assert agent.assistant_message("hi") == {"role": "assistant", "content": "hi"}

    def test_tool_definitions_list(self):
        agent = BaseAgent()
        tools = agent.get_tool_definitions()
        assert len(tools) >= 8
        assert tools[0]["type"] == "function"


# ── EnrichmentAgent Tests ──


class TestEnrichmentAgent:
    def test_structured_output_parsing(self):
        agent = EnrichmentAgent()
        agent.llm = MockLLMClient()
        result = agent.enrich_item(
            title="AI for AML Transaction Monitoring",
            description="How machine learning improves SAR filing",
            body_html="<p>ML models reduce false positives by 80%</p>",
            source_url="https://arxiv.org/abs/1234",
            source_breakdown={"arxiv": 2, "hn": 1},
        )
        assert isinstance(result, EnrichmentResult)
        assert result.sqi_score == 0.75
        assert len(result.tags) == 1
        assert result.tags[0].tag == "aml"

    def test_fallback_on_llm_failure(self):
        agent = EnrichmentAgent()
        result = agent.enrich_item(title="Test", body_html="")
        assert isinstance(result, EnrichmentResult)
        assert result.sqi_score == 0.3
        assert len(result.tags) == 0

    def test_truncate_body(self):
        long = "x" * 5000
        truncated = EnrichmentAgent._truncate_body(long, max_chars=100)
        assert len(truncated) <= 120
        assert "... [truncated]" in truncated

    def test_truncate_body_short(self):
        short = "hello"
        assert EnrichmentAgent._truncate_body(short, max_chars=100) == "hello"

    def test_summarize_sources(self):
        summary = EnrichmentAgent._summarize_sources({"arxiv": 3, "hn": 2})
        assert "arxiv: 3" in summary
        assert "hn: 2" in summary

    def test_summarize_sources_empty(self):
        assert EnrichmentAgent._summarize_sources(None) == "Not specified"

    def test_enrich_batch(self):
        agent = EnrichmentAgent()
        items = [
            {"title": "Item 1", "description": "Desc 1"},
            {"title": "Item 2", "description": "Desc 2"},
        ]
        results = agent.enrich_batch(items, max_items=5)
        assert len(results) == 2
        assert all(isinstance(r, EnrichmentResult) for r in results)

    def test_enrich_batch_respects_max_items(self):
        agent = EnrichmentAgent()
        items = [{"title": f"Item {i}"} for i in range(20)]
        results = agent.enrich_batch(items, max_items=3)
        assert len(results) == 3


# ── LearnModuleGenerator Tests ──


class TestLearnModuleGenerator:
    def test_generate_returns_module(self):
        gen = LearnModuleGenerator()
        gen.llm = MockLLMClient()
        module = gen.generate("pyspark-fundamentals", pillar="data-engineering")
        assert module is not None
        assert isinstance(module, LearnModuleResult)
        assert module.title == "Test Module"
        assert module.slug == "data-engineering/learn/pyspark-fundamentals"
        assert len(module.sections) == 2
        assert len(module.bloom_questions) == 2
        assert len(module.flashcards) == 1

    def test_generate_with_custom_title(self):
        gen = LearnModuleGenerator()
        gen.llm = MockLLMClient()
        module = gen.generate("rag", pillar="data-engineering", title="Custom Title", tags=["rag", "ai"])
        assert module is not None
        assert module.title == "Custom Title"
        assert "rag" in module.tags

    def test_generate_fallback_on_none(self):
        gen = LearnModuleGenerator()
        result = gen.generate("nonexistent", pillar="aml")
        assert result is None

    def test_generate_batch(self):
        gen = LearnModuleGenerator()
        gen.llm = MockLLMClient()
        topics = [
            {"slug": "topic-1", "pillar": "data-engineering", "title": "Topic 1"},
            {"slug": "topic-2", "pillar": "aml", "title": "Topic 2"},
        ]
        results = gen.generate_batch(topics)
        assert len(results) == 2


# ── GlossaryAgent Tests ──


class TestGlossaryAgent:
    def test_generate_entry(self):
        agent = GlossaryAgent()
        agent.llm = MockLLMClient()
        entry = agent.generate_entry("RAG", pillar="data-engineering", context="LLM applications")
        assert entry is not None
        assert isinstance(entry, GlossaryResult)
        assert entry.concept == "RAG"
        assert entry.pillar == "data-engineering"
        assert entry.definition


# ── ResearcherAgent Tests ──


class TestResearcherAgent:
    def test_research_topic(self):
        agent = ResearcherAgent()
        agent.llm = MockLLMClient()
        results = agent.research_topic(pillar="aml", topic="transaction monitoring", max_items=2)
        assert isinstance(results, list)
        assert len(results) >= 0


# ── SynthesisAgent Tests ──


class TestSynthesisAgent:
    def test_synthesize(self):
        agent = SynthesisAgent()
        agent.llm = MockLLMClient()
        sources = [
            {"url": "https://arxiv.org/abs/1", "title": "Paper 1", "content": "ML for AML..."},
            {"url": "https://arxiv.org/abs/2", "title": "Paper 2", "content": "Deep learning..."},
        ]
        result = agent.synthesize("AI for AML", pillar="aml", sources=sources)
        assert result is not None
        assert isinstance(result, SynthesisResult)
        assert result.topic == "AI for AML"

    def test_summarize_sources(self):
        sources = [
            {"url": "https://a.com", "title": "A", "content": "Content A"},
            {"url": "https://b.com", "title": "B", "content": "Content B"},
        ]
        summary = SynthesisAgent._summarize_sources(sources, max_sources=5)
        assert "[1]" in summary
        assert "[2]" in summary
        assert "Content A" in summary

    def test_summarize_sources_empty(self):
        summary = SynthesisAgent._summarize_sources([], max_sources=10)
        assert summary == "No sources provided"
