"""Shared mock data and helpers for ingestion and enrichment tests."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

MOCK_ARXIV_PAPER: dict[str, Any] = {
    "title": "Machine Learning for Anti-Money Laundering Detection",
    "abstract": (
        "This paper presents a novel approach to detecting suspicious "
        "transactions using graph neural networks and anomaly detection."
    ),
    "url": "https://arxiv.org/abs/2401.12345",
    "published": "2026-06-15T00:00:00Z",
    "categories": ["cs.LG", "cs.CR", "q-fin.GN"],
    "_detected_tags": ["aml", "machine-learning"],
    "_relevance_score": 0.850,
    "_pillar": "aml",
}

MOCK_HN_STORY: dict[str, Any] = {
    "title": "Show HN: A New Approach to Stream Processing with Kafka",
    "hn_url": "https://news.ycombinator.com/item?id=12345678",
    "url": "https://example.com/stream-processing",
    "points": 120,
    "author": "testuser",
    "created_at": "2026-06-20T12:00:00Z",
    "_detected_tags": ["dataops", "stream-processing"],
    "_relevance_score": 0.720,
    "_pillar": "data",
}

MOCK_PUBMED_PAPER: dict[str, Any] = {
    "title": "Systematic Review of Financial Risk Factors in Market Microstructure",
    "url": "https://pubmed.ncbi.nlm.nih.gov/12345678/",
    "published": "2026-05-01T00:00:00Z",
    "abstract": (
        "This systematic review examines 150 studies on liquidity, "
        "volatility, and systemic risk in financial markets."
    ),
    "author": "Smith J",
    "_detected_tags": ["risk-management", "market-microstructure"],
    "_relevance_score": 0.780,
    "_pillar": "market",
}

MOCK_S2_PAPER: dict[str, Any] = {
    "title": "Distributed Data Quality Monitoring at Scale",
    "url": "https://api.semanticscholar.org/CorpusID:12345678",
    "published": "2026-04-10T00:00:00Z",
    "abstract": (
        "We present a framework for monitoring data quality across "
        "thousands of distributed pipelines."
    ),
    "venue": "VLDB 2026",
    "citations": 15,
    "author": "Jane Doe",
    "_detected_tags": ["dataops", "data-quality"],
    "_relevance_score": 0.810,
    "_pillar": "data",
}

MOCK_SEC_FILING: dict[str, Any] = {
    "title": "10-K Annual Report: Anti-Money Laundering Compliance Update",
    "url": "https://www.sec.gov/Archives/edgar/data/123456/000123456-26-000001.txt",
    "published": "2026-03-15",
    "summary": (
        "This filing describes the registrant's AML compliance program, "
        "including KYC procedures and suspicious activity monitoring."
    ),
    "_detected_tags": ["aml"],
    "_relevance_score": 0.650,
    "_pillar": "aml",
}

MOCK_REGISTRY: dict[str, Any] = {
    "content": [
        {
            "slug": "compliance/research/aml-machine-learning-2024",
            "title": "AML Machine Learning 2024",
            "source_url": "https://arxiv.org/abs/2401.12345",
            "pillar": "compliance",
            "tags": ["aml", "machine-learning"],
            "description": "A paper about AML ML",
        },
        {
            "slug": "data/research/stream-processing-kafka",
            "title": "Stream Processing with Kafka",
            "source_url": "https://news.ycombinator.com/item?id=12345678",
            "pillar": "data-engineering",
            "tags": ["dataops", "streaming"],
            "description": "HN discussion about Kafka",
        },
        {
            "slug": "markets/research/market-microstructure-review",
            "title": "Market Microstructure Review",
            "source_url": "https://pubmed.ncbi.nlm.nih.gov/12345678/",
            "pillar": "markets",
            "tags": ["market-microstructure"],
            "description": "A review of market microstructure",
        },
        {
            "slug": "data/research/data-quality-at-scale",
            "title": "Data Quality at Scale",
            "source_url": "https://api.semanticscholar.org/CorpusID:12345678",
            "pillar": "data-engineering",
            "tags": ["data-quality"],
            "description": "Data quality monitoring",
        },
        {
            "slug": "compliance/research/aml-compliance-update",
            "title": "AML Compliance Update",
            "source_url": "https://www.sec.gov/Archives/edgar/data/123456/000123456-26-000001.txt",
            "pillar": "compliance",
            "tags": ["aml"],
            "description": "SEC filing about AML compliance",
        },
        {
            "slug": "compliance/research/near-duplicate-article",
            "title": "A Near Duplicate Article About Machine Learning for AML Detection",
            "source_url": "https://example.com/near-dup",
            "pillar": "compliance",
            "tags": ["aml"],
            "description": "Near duplicate test",
        },
    ],
}

MOCK_AML_KEYWORD_PATTERNS: dict[str, list[str]] = {
    "aml": [r"\baml\b", r"\banti.money.launder\b", r"\bkyc\b"],
    "machine-learning": [r"\bmachine.learning\b", r"\bdeep.learning\b", r"\bneural\b"],
    "transaction-monitoring": [r"\btransaction\b", r"\bsuspicious\b", r"\banomaly\b"],
}

MOCK_DATA_KEYWORD_PATTERNS: dict[str, list[str]] = {
    "dataops": [r"\bdataops\b", r"\bpipeline\b", r"\borchestration\b"],
    "stream-processing": [r"\bstream\b", r"\bkafka\b", r"\bflink\b"],
    "data-quality": [r"\bdata.quality\b", r"\bobservability\b", r"\blineage\b"],
}

MOCK_MARKET_KEYWORD_PATTERNS: dict[str, list[str]] = {
    "market-microstructure": [r"\bmarket.microstructure\b", r"\bliquidity\b", r"\border.book\b"],
    "risk-management": [r"\brisk\b", r"\bvolatility\b", r"\bportfolio\b"],
    "quantitative-modeling": [r"\bregime.switch\b", r"\bbayesian\b", r"\bcorrelation\b"],
}


def make_mock_pillar_config(slug_name: str) -> Any:
    """Return a dict-like PillarConfig for the given slug name."""
    configs: dict[str, dict[str, Any]] = {
        "aml": {
            "slug_name": "aml",
            "label": "Financial Compliance",
            "arxiv_categories": ["cs.CR", "cs.LG", "q-fin.GN"],
            "category_boosts": {"cs.cr": 0.12, "cs.lg": 0.10, "q-fin.gn": 0.15},
            "keyword_patterns": MOCK_AML_KEYWORD_PATTERNS,
            "hn_min_score": 0.20,
            "arxiv_min_score": 0.15,
        },
        "data": {
            "slug_name": "data",
            "label": "Data Engineering & DataOps",
            "arxiv_categories": ["cs.DB", "cs.DC"],
            "category_boosts": {"cs.db": 0.15, "cs.dc": 0.15},
            "keyword_patterns": MOCK_DATA_KEYWORD_PATTERNS,
            "hn_min_score": 0.20,
            "arxiv_min_score": 0.15,
        },
        "market": {
            "slug_name": "market",
            "label": "Financial Markets & Macroeconomics",
            "arxiv_categories": ["q-fin.MF", "q-fin.TR", "econ.EM"],
            "category_boosts": {"q-fin.mf": 0.15, "q-fin.tr": 0.10},
            "keyword_patterns": MOCK_MARKET_KEYWORD_PATTERNS,
            "hn_min_score": 0.20,
            "arxiv_min_score": 0.15,
        },
    }
    raw = configs.get(slug_name, configs["aml"])
    return _DictPillarConfig(**raw)


class _DictPillarConfig:
    """Dict-like object that behaves like PillarConfig for test purposes."""

    def __init__(
        self,
        slug_name: str,
        label: str,
        arxiv_categories: list[str],
        category_boosts: dict[str, float],
        keyword_patterns: dict[str, list[str]],
        hn_min_score: float = 0.20,
        arxiv_min_score: float = 0.15,
    ) -> None:
        self.slug_name = slug_name
        self.label = label
        self.arxiv_categories = arxiv_categories
        self.category_boosts = category_boosts
        self.keyword_patterns = keyword_patterns
        self.hn_min_score = hn_min_score
        self.arxiv_min_score = arxiv_min_score


def make_mock_llm_client(
    return_value: str = '["test-tag"]',
) -> MagicMock:
    """Return a MagicMock that simulates an OpenAI client."""
    client = MagicMock()
    choice = MagicMock()
    choice.message.content = return_value
    response = MagicMock()
    response.choices = [choice]
    client.chat.completions.create.return_value = response
    return client
