"""Agentic pipeline modules for AcaciaFund.

Agents use core.llm_client (aisuite), core.agent_tools, and core.risk_engine
to perform structured tasks with human-in-the-loop safety.
"""

from .base import BaseAgent, AgentConfig, AgentResult
from .enrichment import EnrichmentAgent, EnrichmentResult
from .glossary import GlossaryAgent, GlossaryResult
from .learn_generator import LearnModuleGenerator, LearnModuleResult
from .researcher import ResearchResult, ResearcherAgent
from .synthesis import SynthesisAgent, SynthesisResult

__all__ = [
    "AgentConfig",
    "AgentResult",
    "BaseAgent",
    "EnrichmentAgent",
    "EnrichmentResult",
    "GlossaryAgent",
    "GlossaryResult",
    "LearnModuleGenerator",
    "LearnModuleResult",
    "ResearchResult",
    "ResearcherAgent",
    "SynthesisAgent",
    "SynthesisResult",
]
