"""Ontology framework for AcaciaFund — structured knowledge representation.

Defines entities, relationships, and hierarchies for the three pillars
(Compliance, Markets, Data Engineering). Integrates with the knowledge graph
and provides concept extraction/matching utilities for ingestion pipelines.
"""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Set, Tuple

from loguru import logger

if TYPE_CHECKING:
    from core.ontology_cache import OntologyCache

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class Concept(BaseModel):
    """A named knowledge entity within the ontology."""

    id: str = Field(..., min_length=1, description="Unique concept identifier (slug-style)")
    label: str = Field(..., min_length=1, description="Human-readable name")
    description: str = ""
    pillar: str = Field(
        ..., description="Owning pillar: aml | stock | data-engineering | cross-pillar"
    )
    category: str = Field(
        default="reference",
        description="Knowledge category key matching KNOWLEDGE_CATEGORIES or PILLAR_SUBCATEGORIES",
    )
    aliases: List[str] = Field(default_factory=list)
    properties: Dict[str, Any] = Field(default_factory=dict)
    source_inspiration: str = Field(
        default="",
        description="Originating source URL or organisation name",
    )
    confidence_score: float = Field(default=1.0, ge=0.0, le=1.0)

    # Philosophical foundations metadata
    philosophical_lineage: List[str] = Field(
        default_factory=list,
        description="Epistemic/ethical traditions this concept belongs to, e.g. 'social_epistemology', 'foucault_discipline'",
    )
    epistemic_status: str = Field(
        default="",
        description="Epistemic role: 'constitutive' | 'regulatory' | 'pragmatic' | 'ontological' | 'instrumental'",
    )
    normative_basis: str = Field(
        default="",
        description="Normative foundation: 'kantian_duty' | 'utilitarian' | 'rawlsian' | 'virtue_ethics' | 'pragmatic' | 'contractarian'",
    )
    ontological_commitment: str = Field(
        default="",
        description="Metaphysical stance: 'realist' | 'constructivist' | 'fictionalist' | 'pluralist' | 'processual'",
    )
    temporal_ontology: str = Field(
        default="",
        description="Time model: 'state_based' | 'event_based' | 'processual' | 'eternalist'",
    )
    uncertainty_class: str = Field(
        default="",
        description="Uncertainty type: 'knightian' | 'measurable' | 'ambiguity' | 'ignorance'",
    )
    governance_model: str = Field(
        default="",
        description="Governance pattern: 'hierarchical' | 'polycentric' | 'algorithmic' | 'constitutional'",
    )
    semantic_contract_type: str = Field(
        default="",
        description="Semantic role: 'constitutive' | 'coordinating' | 'descriptive'",
    )
    philosophical_sources: List[str] = Field(
        default_factory=list,
        description="Primary source citations e.g. 'Foucault, Discipline and Punish (1975)'",
    )
    cross_pillar_analogs: List[str] = Field(
        default_factory=list,
        description="Concept IDs in other pillars sharing the same epistemic pattern",
    )

    # Feynman learning framework fields
    eli5_explanation: Optional[str] = Field(
        default=None,
        description="Explain Like I'm 5 — one paragraph, no jargon, for absolute beginners",
    )
    analogy: Optional[str] = Field(
        default=None,
        description="Real-world analogy that maps intuitively to this concept",
    )
    concrete_example: Optional[str] = Field(
        default=None,
        description="Specific worked example with numbers, code, or step-by-step walkthrough",
    )
    feynman_diagram: Optional[str] = Field(
        default=None,
        description="SVG or Mermaid diagram for visual / diagrammatic reasoning",
    )
    gap_questions: List[str] = Field(
        default_factory=list,
        description="Questions that reveal understanding gaps when the learner cannot answer them",
    )
    teach_back_prompt: Optional[str] = Field(
        default=None,
        description="Prompt asking the learner to explain the concept in their own words",
    )
    build_exercise: Optional[Dict[str, Any]] = Field(
        default=None,
        description=(
            "Hands-on exercise: "
            "{'type': 'code|calc|diagram', 'prompt': str, 'solution': str}"
        ),
    )
    feynman_difficulty: int = Field(
        default=1, ge=1, le=5,
        description="1=trivial to explain, 5=requires deep prerequisite knowledge",
    )
    explanation_quality: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="Internal quality score for Feynman-generated explanations",
    )

    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    model_config = {"extra": "allow"}


class Relation(BaseModel):
    """A directed relationship between two concepts."""

    source_id: str = Field(..., min_length=1)
    target_id: str = Field(..., min_length=1)
    relation_type: str = Field(
        ...,
        min_length=1,
        description="e.g. requires, part_of, influences, supersedes, enables, detects",
    )
    strength: float = Field(default=1.0, ge=0.0, le=1.0)
    evidence: List[str] = Field(default_factory=list)
    pillar: str = Field(default="cross-pillar")
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    model_config = {"extra": "allow"}


class ResourceLink(BaseModel):
    """A link from a concept to an external authoritative resource."""

    concept_id: str = Field(..., min_length=1)
    url: str = Field(..., min_length=1)
    title: str = ""
    description: str = ""
    source_org: str = Field(default="", description="Organisation that owns the resource")
    credibility_score: float = Field(default=0.5, ge=0.0, le=1.0)
    access_date: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%d")
    )
    license_info: str = ""
    status: str = Field(
        default="active",
        description="Source health: active, degraded, archived",
    )
    last_verified: Optional[str] = Field(
        default=None,
        description="ISO date when source was last HTTP-verified as reachable",
    )
    http_status: Optional[int] = Field(
        default=None,
        description="Last observed HTTP status code (200, 404, etc.)",
    )

    model_config = {"extra": "allow"}


class InspirationSource(BaseModel):
    """An external knowledge source configured per pillar."""

    url: str
    name: str
    frequency: str = Field(default="weekly", description="Scrape/sync frequency")
    relevance: float = Field(default=0.5, ge=0.0, le=1.0)
    description: str = ""
    last_fetched: Optional[str] = None
    enabled: bool = True
    pillar: str = Field(default="", description="Owner pillar key")
    status: str = Field(
        default="active",
        description="Source health: active, degraded, archived",
    )
    last_verified: Optional[str] = Field(
        default=None,
        description="ISO date when source was last HTTP-verified as reachable",
    )
    http_status: Optional[int] = Field(
        default=None,
        description="Last observed HTTP status code (200, 404, etc.)",
    )

    model_config = {"extra": "allow"}


# ---------------------------------------------------------------------------
# OntologyManager — central registry
# ---------------------------------------------------------------------------

# Canonical relation types used across the system
RELATION_TYPES = {
    "requires": "Target concept is a prerequisite for source",
    "part_of": "Source concept is a component of target",
    "influences": "Source concept has measurable impact on target",
    "enables": "Source concept unlocks or facilitates target",
    "detects": "Source concept is used to identify target",
    "supersedes": "Source concept replaces or improves upon target",
    "related_to": "General topical similarity (weaker than others)",
    "implements": "Source concept is a concrete implementation of target",
    "regulates": "Source concept governs or constrains target",
    "measures": "Source concept quantifies or evaluates target",
}

# Valid pillar keys
PILLAR_KEYS = {"aml", "stock", "data-engineering", "cross-pillar"}

# Pre-defined concept seeds per pillar (expandable)
PILLAR_CONCEPT_SEEDS: Dict[str, List[Dict[str, Any]]] = {
    "aml": [
        # Foundation layer
        {"id": "money-laundering-basics", "label": "Money Laundering Basics", "category": "foundations",
         "aliases": ["money laundering stages", "placement layering integration", "ML lifecycle"]},
        {"id": "aml-regulatory-framework", "label": "AML Regulatory Framework", "category": "foundations",
         "aliases": ["AML regulation", "regulatory landscape", "AML legal basis"]},
        {"id": "financial-crime-types", "label": "Types of Financial Crime", "category": "foundations",
         "aliases": ["financial crime categories", "fraud types", "economic crime"]},
        {"id": "aml-compliance-basics", "label": "AML Compliance Principles", "category": "foundations",
         "aliases": ["compliance basics", "AML fundamentals", "compliance culture"]},
        {"id": "risk-based-approach", "label": "Risk-Based Approach in AML", "category": "foundations",
         "aliases": ["RBA", "risk-based compliance", "AML risk management"]},
        {"id": "kyc", "label": "Know Your Customer (KYC)", "category": "cdd-kyc",
         "aliases": ["KYC", "know-your-customer"]},
        {"id": "cdd", "label": "Customer Due Diligence", "category": "cdd-kyc",
         "aliases": ["CDD"]},
        {"id": "edd", "label": "Enhanced Due Diligence", "category": "cdd-kyc",
         "aliases": ["EDD"]},
        {"id": "sar", "label": "Suspicious Activity Report", "category": "sar-str",
         "aliases": ["SAR", "suspicious-activity-reporting"]},
        {"id": "str", "label": "Suspicious Transaction Report", "category": "sar-str",
         "aliases": ["STR"]},
        {"id": "ctr", "label": "Currency Transaction Report", "category": "sar-str",
         "aliases": ["CTR"]},
        {"id": "pep", "label": "Politically Exposed Person", "category": "risk-assessment",
         "aliases": ["PEP", "politically-exposed-person"]},
        {"id": "sanctions-screening", "label": "Sanctions Screening", "category": "sanctions",
         "aliases": ["OFAC screening", "sanctions list check"]},
        {"id": "transaction-monitoring", "label": "Transaction Monitoring", "category": "transaction-monitoring",
         "aliases": ["TM", "transaction surveillance"]},
        {"id": "entity-resolution", "label": "Entity Resolution", "category": "advanced-techniques",
         "aliases": ["entity matching", "record linkage"]},
        {"id": "network-analysis", "label": "Network Analysis for AML", "category": "advanced-techniques",
         "aliases": ["graph analytics", "network forensics"]},
        {"id": "beneficial-ownership", "label": "Beneficial Ownership", "category": "regulations",
         "aliases": ["UBO", "ultimate beneficial ownership", "BO"]},
        {"id": "fatf-recommendations", "label": "FATF Recommendations", "category": "regulations",
         "aliases": ["FATF 40 Recommendations"]},
        {"id": "bsa", "label": "Bank Secrecy Act", "category": "regulations",
         "aliases": ["BSA", "Currency and Foreign Transactions Act"]},
        {"id": "tbml", "label": "Trade-Based Money Laundering", "category": "risk-assessment",
         "aliases": ["TBML", "trade-based-ml"]},
        {"id": "regtech", "label": "Regulatory Technology", "category": "regtech",
         "aliases": ["RegTech"]},
        {"id": "travel-rule", "label": "FATF Travel Rule", "category": "regulations",
         "aliases": ["travel rule", "VASP travel rule"]},
        {"id": "adverse-media", "label": "Adverse Media Screening", "category": "cdd-kyc",
         "aliases": ["negative news screening", "adverse media check"]},
        {"id": "aml-program", "label": "AML Compliance Program", "category": "risk-assessment",
         "aliases": ["AML program", "BSA/AML program"]},
        {"id": "cyber-aml", "label": "Cyber AML / Financial Cybercrime", "category": "advanced-techniques",
         "aliases": ["financial cybercrime", "cyber-enabled fraud"]},
        {"id": "correspondent-banking", "label": "Correspondent Banking AML", "category": "risk-assessment",
         "aliases": ["correspondent banking", "nested accounts"]},
        {"id": "regulatory-reporting", "label": "Regulatory Reporting Automation", "category": "regtech",
         "aliases": ["automated reporting", "regulatory filings"]},
        {"id": "crypto-aml", "label": "Cryptocurrency AML", "category": "advanced-techniques",
         "aliases": ["crypto compliance", "VASP", "virtual asset compliance"]},
        {"id": "mica-crypto-assets", "label": "MiCA — Markets in Crypto-Assets Regulation", "category": "crypto-aml",
         "aliases": ["MiCA", "Markets in Crypto-Assets", "crypto regulation", "CASPs"]},
        {"id": "ai-aml-surveillance", "label": "AI in AML Surveillance", "category": "advanced-techniques",
         "aliases": ["AML AI", "machine learning AML", "AI surveillance", "AML analytics"]},
        {"id": "fincrime-intelligence", "label": "Financial Crime Intelligence", "category": "advanced-techniques",
         "aliases": ["fin crime intel", "threat intelligence", "crime analytics"]},
        {"id": "fraud-detection", "label": "Fraud Detection Systems", "category": "advanced-techniques",
         "aliases": ["payment fraud", "identity fraud", "application fraud"]},
        {"id": "cross-border-payments", "label": "Cross-Border Payment Compliance", "category": "risk-assessment",
         "aliases": ["cross-border compliance", "SWIFT compliance", "international payments"]},
        {"id": "aml-optimization", "label": "AML Compliance Optimization", "category": "regtech",
         "aliases": ["AML efficiency", "compliance optimization", "automated compliance"]},
        {"id": "aml-training", "label": "AML Training & Awareness", "category": "best-practices",
         "aliases": ["compliance training", "AML education", "anti-money laundering training"]},
        {"id": "regulatory-filing", "label": "Regulatory Filing Automation", "category": "regtech",
         "aliases": ["automated filing", "reg reporting", "compliance filing"]},
        # Extended AML seeds
        {"id": "aml-audit", "label": "AML Audit & Examination", "category": "risk-assessment",
         "aliases": ["AML audit", "regulatory examination", "compliance audit"]},
        {"id": "aml-risk-scoring", "label": "AML Risk Scoring Models", "category": "risk-assessment",
         "aliases": ["risk scoring", "AML risk assessment", "risk-based approach"]},
        {"id": "aml-data-governance", "label": "AML Data Governance", "category": "architecture",
         "aliases": ["AML data management", "data quality AML", "AML data lineage"]},
        {"id": "aml-reporting-dashboard", "label": "AML Reporting Dashboard", "category": "regtech",
         "aliases": ["AML dashboard", "compliance reporting", "AML visualization"]},
        {"id": "aml-case-management", "label": "AML Case Management", "category": "advanced-techniques",
         "aliases": ["investigation case management", "alert case management"]},
        {"id": "aml-model-validation", "label": "AML Model Validation", "category": "advanced-techniques",
         "aliases": ["model risk management", "AML model testing", "model governance"]},
        {"id": "aml-threat-intel", "label": "AML Threat Intelligence", "category": "advanced-techniques",
         "aliases": ["financial threat intel", "AML intelligence", "typology updates"]},
        {"id": "global-sanctions", "label": "Global Sanctions Regimes", "category": "sanctions",
         "aliases": ["OFAC", "EU sanctions", "UN sanctions", "sanctions compliance"]},
        {"id": "fincen-boi", "label": "FinCEN BOI Reporting", "category": "reporting",
         "aliases": ["Corporate Transparency Act", "BOI", "beneficial ownership information"]},
        {"id": "aml-esg-risk", "label": "AML-ESG Integration", "category": "risk-assessment",
         "aliases": ["ESG financial crime", "green crime AML", "environmental crime"]},
        {"id": "de-risk", "label": "De-Risking in Correspondent Banking", "category": "risk-assessment",
         "aliases": ["de-risking", "financial exclusion", "correspondent banking risk"]},
        {"id": "aml-continuous-monitoring", "label": "Continuous AML Monitoring", "category": "transaction-monitoring",
         "aliases": ["real-time monitoring", "ongoing due diligence", "transaction surveillance"]},
        {"id": "aml-data-sharing", "label": "AML Data Sharing & PPP", "category": "best-practices",
         "aliases": ["FIU collaboration", "public-private partnership", "information sharing"]},
        {"id": "aml-international", "label": "International AML Cooperation", "category": "regulations",
         "aliases": ["mutual legal assistance", "cross-border AML", "FIU Egmont Group"]},
        {"id": "trade-finance-aml", "label": "Trade Finance AML", "category": "risk-assessment",
         "aliases": ["trade-based AML", "trade finance compliance", "documentary credits"]},
        {"id": "payment-fraud", "label": "Payment Fraud Detection", "category": "transaction-monitoring",
         "aliases": ["payment fraud", "ACH fraud", "wire fraud", "push payment fraud"]},
        {"id": "aml-oracle", "label": "AML Oracle & AI Decision Systems", "category": "regtech",
         "aliases": ["AML AI", "decision intelligence", "AI compliance"]},
        {"id": "crypto-travel-rule", "label": "Crypto Travel Rule Compliance", "category": "crypto-aml",
         "aliases": ["VASP travel rule", "crypto transfer", "travel rule compliance"]},
        {"id": "defi-aml", "label": "DeFi AML Compliance", "category": "crypto-aml",
         "aliases": ["decentralized finance", "DeFi regulation", "DeFi compliance"]},
    ],
    "stock": [
        # Foundation layer
        {"id": "equity-basics", "label": "Equity & Stock Basics", "category": "foundations",
         "aliases": ["stocks", "shares", "equity securities", "common stock"]},
        {"id": "order-types", "label": "Order Types & Execution", "category": "foundations",
         "aliases": ["market order", "limit order", "stop loss", "order routing"]},
        {"id": "market-participants", "label": "Market Participants", "category": "foundations",
         "aliases": ["retail investors", "institutional investors", "market makers", "HFT firms"]},
        {"id": "trading-venues", "label": "Trading Venues", "category": "foundations",
         "aliases": ["stock exchanges", "NYSE", "NASDAQ", "dark pools", "ATS"]},
        {"id": "market-indices", "label": "Market Indices", "category": "foundations",
         "aliases": ["S&P 500", "Dow Jones", "index construction", "benchmark indices"]},
        {"id": "lob", "label": "Limit Order Book", "category": "foundations",
         "aliases": ["LOB", "order book"]},
        {"id": "market-microstructure", "label": "Market Microstructure", "category": "foundations",
         "aliases": ["microstructure"]},
        {"id": "volatility-surface", "label": "Implied Volatility Surface", "category": "market-analysis",
         "aliases": ["IV surface", "vol surface"]},
        {"id": "hawkes-process", "label": "Hawkes Process", "category": "advanced-techniques",
         "aliases": ["Hawkes self-exciting process"]},
        {"id": "vpin", "label": "VPIN Toxicity", "category": "advanced-techniques",
         "aliases": ["Volume-Synchronized Probability of Informed Trading"]},
        {"id": "supply-chain-analysis", "label": "Supply Chain Analysis", "category": "industry-analysis",
         "aliases": ["supply chain risk"]},
        {"id": "earnings-analysis", "label": "Earnings Analysis", "category": "market-analysis",
         "aliases": ["earnings season", "earnings reports"]},
        {"id": "commodity-trading", "label": "Commodity Trading Strategies", "category": "strategies",
         "aliases": ["commodity futures", "commodity hedging"]},
        {"id": "semiconductor-industry", "label": "Semiconductor Industry", "category": "industry-analysis",
         "aliases": ["chip industry", "semiconductor supply chain"]},
        {"id": "ai-hardware", "label": "AI Hardware Trends", "category": "industry-analysis",
         "aliases": ["AI chips", "GPU market", "AI accelerators"]},
        {"id": "portfolio-optimization", "label": "Portfolio Optimization", "category": "strategies",
         "aliases": ["asset allocation", "portfolio construction"]},
        {"id": "risk-parity", "label": "Risk Parity", "category": "strategies",
         "aliases": ["risk-balanced portfolio"]},
        {"id": "factor-investing", "label": "Factor Investing", "category": "strategies",
         "aliases": ["smart beta", "factor models"]},
        {"id": "technical-analysis", "label": "Technical Analysis", "category": "market-analysis",
         "aliases": ["chart patterns", "technical indicators"]},
        {"id": "macro-analysis", "label": "Macroeconomic Analysis", "category": "market-analysis",
         "aliases": ["macro analysis", "economic indicators"]},
        {"id": "options-trading", "label": "Options Trading Strategies", "category": "strategies",
         "aliases": ["options strategies", "derivatives trading"]},
        {"id": "fixed-income", "label": "Fixed Income Markets", "category": "market-analysis",
         "aliases": ["bond markets", "fixed income", "credit markets"]},
        {"id": "esg-investing", "label": "ESG Investing", "category": "industry-analysis",
         "aliases": ["ESG", "sustainable investing", "responsible investing"]},
        {"id": "behavioral-finance", "label": "Behavioral Finance", "category": "foundations",
         "aliases": ["behavioral economics", "behavioral biases"]},
        {"id": "market-impact", "label": "Market Impact Models", "category": "advanced-techniques",
         "aliases": ["price impact", "market impact cost", "implementation shortfall"]},
        {"id": "statistical-arbitrage", "label": "Statistical Arbitrage", "category": "strategies",
         "aliases": ["stat arb", "pairs trading", "mean reversion"]},
        {"id": "high-frequency-trading", "label": "High Frequency Trading", "category": "advanced-techniques",
         "aliases": ["HFT", "algorithmic trading", "low latency"]},
        {"id": "asset-pricing", "label": "Asset Pricing Models", "category": "foundations",
         "aliases": ["CAPM", "asset pricing", "discount factor models"]},
        {"id": "esg-double-materiality", "label": "ESG Double Materiality", "category": "industry-analysis",
         "aliases": ["double materiality", "CSRD materiality", "impact materiality", "financial materiality"]},
        {"id": "etf-trading", "label": "ETF Trading & Structure", "category": "market-analysis",
         "aliases": ["exchange traded funds", "ETF creation redemption", "ETF arbitrage"]},
        {"id": "crypto-markets", "label": "Cryptocurrency Markets", "category": "market-analysis",
         "aliases": ["digital assets", "crypto trading", "blockchain markets"]},
        {"id": "hedge-funds", "label": "Hedge Fund Strategies", "category": "strategies",
         "aliases": ["hedge funds", "alternative investments", "long short equity"]},
        {"id": "algorithmic-trading", "label": "Algorithmic Trading", "category": "advanced-techniques",
         "aliases": ["algo trading", "automated trading", "execution algorithms"]},
        {"id": "retail-trading", "label": "Retail Trading Trends", "category": "market-analysis",
         "aliases": ["retail investors", "meme stocks", "retail flow"]},
        {"id": "market-data", "label": "Market Data Infrastructure", "category": "foundations",
         "aliases": ["market data", "TAQ data", "market feed", "OPRA"]},
        {"id": "volatility-trading", "label": "Volatility Trading", "category": "strategies",
         "aliases": ["VIX trading", "vol arbitrage", "volatility strategies"]},
        # Extended markets seeds
        {"id": "order-book", "label": "Order Book Dynamics", "category": "market-microstructure",
         "aliases": ["LOB", "limit order book", "order flow", "order book depth"]},
        {"id": "dark-pools", "label": "Dark Pools & ATS", "category": "market-microstructure",
         "aliases": ["dark liquidity", "ATS", "block trading", "alternative trading system"]},
        {"id": "market-making", "label": "Market Making", "category": "market-microstructure",
         "aliases": ["liquidity provision", "market maker", "quote-driven trading"]},
        {"id": "execution-algos", "label": "Execution Algorithms", "category": "high-frequency-trading",
         "aliases": ["VWAP", "TWAP", "implementation shortfall", "smart order routing"]},
        {"id": "cross-asset-trading", "label": "Cross-Asset Trading", "category": "trading-strategies",
         "aliases": ["multi-asset", "asset allocation", "correlation trading"]},
        {"id": "regime-detection", "label": "Market Regime Detection", "category": "macro-analysis",
         "aliases": ["regime switching", "market states", "HMM", "volatility regime"]},
        {"id": "carry-trade", "label": "Carry Trade Strategies", "category": "trading-strategies",
         "aliases": ["currency carry", "FX carry", "interest rate differential"]},
        {"id": "momentum-trading", "label": "Momentum & Trend Following", "category": "trading-strategies",
         "aliases": ["time-series momentum", "cross-sectional momentum", "trend following"]},
        {"id": "mean-reversion", "label": "Mean Reversion Strategies", "category": "trading-strategies",
         "aliases": ["statistical arbitrage", "pairs trading", "reversal trading"]},
        {"id": "event-driven-trading", "label": "Event-Driven Trading", "category": "trading-strategies",
         "aliases": ["corporate actions", "M&A arbitrage", "event study"]},
        {"id": "alternative-data", "label": "Alternative Data in Markets", "category": "market-microstructure",
         "aliases": ["alt data", "satellite imagery", "credit card data", "web scraping"]},
        {"id": "etf-creation", "label": "ETF Creation & Redemption", "category": "market-microstructure",
         "aliases": ["ETF arbitrage", "creation unit", "AP authorized participant"]},
        {"id": "market-surveillance", "label": "Market Surveillance", "category": "market-microstructure",
         "aliases": ["insider detection", "market manipulation", "wash trading"]},
        {"id": "stock-lending", "label": "Securities Lending", "category": "market-microstructure",
         "aliases": ["stock loan", "short selling", "borrow rate"]},
        {"id": "fx-markets", "label": "FX Market Structure", "category": "market-microstructure",
         "aliases": ["forex", "spot FX", "FX swap", "FX prime brokerage"]},
        {"id": "quantitative-trading", "label": "Quantitative Trading", "category": "trading-strategies",
         "aliases": ["quant trading", "systematic trading", "quantitative strategies"]},
        {"id": "volatility-arbitrage", "label": "Volatility Arbitrage", "category": "trading-strategies",
         "aliases": ["vol arb", "dispersion trading", "volatility strategies"]},
        {"id": "machine-learning-markets", "label": "Machine Learning in Markets", "category": "advanced-techniques",
         "aliases": ["ML trading", "deep learning markets", "AI trading"]},
    ],
    "data-engineering": [
        {"id": "etl", "label": "Extract-Transform-Load", "category": "foundations",
         "aliases": ["ETL", "extract transform load"]},
        {"id": "elt", "label": "Extract-Load-Transform", "category": "foundations",
         "aliases": ["ELT"]},
        {"id": "cdc", "label": "Change Data Capture", "category": "advanced-techniques",
         "aliases": ["CDC", "change-data-capture"]},
        {"id": "data-lake", "label": "Data Lake", "category": "foundations",
         "aliases": ["data lakehouse"]},
        {"id": "data-warehouse", "label": "Data Warehouse", "category": "foundations",
         "aliases": ["DWH", "analytical data store"]},
        {"id": "data-mesh", "label": "Data Mesh", "category": "architecture",
         "aliases": ["data mesh architecture"]},
        {"id": "streaming", "label": "Stream Processing", "category": "advanced-techniques",
         "aliases": ["real-time processing", "stream processing"]},
        {"id": "batch-processing", "label": "Batch Processing", "category": "foundations",
         "aliases": ["batch jobs", "scheduled processing"]},
        {"id": "dbt", "label": "dbt (data build tool)", "category": "advanced-techniques",
         "aliases": ["data build tool"]},
        {"id": "dagster", "label": "Dagster Orchestrator", "category": "advanced-techniques",
         "aliases": ["dagster"]},
        {"id": "apache-flink", "label": "Apache Flink", "category": "advanced-techniques",
         "aliases": ["Flink"]},
        {"id": "apache-kafka", "label": "Apache Kafka", "category": "advanced-techniques",
         "aliases": ["Kafka"]},
        {"id": "apache-iceberg", "label": "Apache Iceberg", "category": "advanced-techniques",
         "aliases": ["Iceberg", "table format"]},
        {"id": "schema-registry", "label": "Schema Registry", "category": "architecture",
         "aliases": ["schema evolution", "schema management"]},
        {"id": "data-contracts", "label": "Data Contracts", "category": "architecture",
         "aliases": ["data contract", "SLA for data"]},
        {"id": "data-quality", "label": "Data Quality", "category": "best-practices",
         "aliases": ["data observability", "data validation"]},
        {"id": "arrow-parquet", "label": "Apache Arrow / Parquet", "category": "advanced-techniques",
         "aliases": ["Arrow", "Parquet", "columnar storage"]},
        {"id": "data-observability", "label": "Data Observability", "category": "best-practices",
         "aliases": ["data monitoring", "data health", "observability"]},
        {"id": "data-pipeline", "label": "Data Pipeline Architecture", "category": "architecture",
         "aliases": ["pipeline architecture", "data pipeline design"]},
        {"id": "data-governance", "label": "Data Governance", "category": "architecture",
         "aliases": ["data catalog", "metadata management", "data lineage"]},
        {"id": "orchestration", "label": "Workflow Orchestration", "category": "advanced-techniques",
         "aliases": ["workflow automation", "pipeline orchestration", "DAG"]},
        {"id": "query-optimization", "label": "Query Optimization", "category": "best-practices",
         "aliases": ["SQL optimization", "query tuning", "execution planning"]},
        {"id": "real-time-analytics", "label": "Real-Time Analytics", "category": "advanced-techniques",
         "aliases": ["real-time reporting", "live dashboards", "streaming analytics"]},
        {"id": "data-security", "label": "Data Security & Access Control", "category": "best-practices",
         "aliases": ["RBAC", "data encryption", "access control", "data masking"]},
        {"id": "distributed-systems", "label": "Distributed Systems for Data", "category": "architecture",
         "aliases": ["distributed computing", "consensus", "sharding"]},
        {"id": "ml-pipeline", "label": "ML Pipeline Engineering", "category": "advanced-techniques",
         "aliases": ["MLOps", "feature engineering", "model deployment"]},
        # 2026 Compliance landscape concepts
        {"id": "gdpr-anonymization", "label": "GDPR Anonymization & Pseudonymization", "category": "best-practices",
         "aliases": ["anonymization", "pseudonymization", "data masking", "de-identification"]},
        {"id": "gdpr-synthetic-data", "label": "Synthetic Data Generation for GDPR Compliance", "category": "advanced-techniques",
         "aliases": ["synthetic data", "data generation", "generative modeling", "synth data"]},
        {"id": "debiasing-pipeline", "label": "Debiasing Pipeline", "category": "best-practices",
         "aliases": ["bias mitigation", "fairness pipeline", "bias detection", "algorithmic fairness"]},
        {"id": "differential-privacy", "label": "Differential Privacy", "category": "advanced-techniques",
         "aliases": ["DP", "epsilon-delta privacy", "privacy budget", "noise injection"]},
        {"id": "federated-learning", "label": "Federated Learning", "category": "advanced-techniques",
         "aliases": ["federated ML", "distributed training", "privacy-preserving ML", "federated averaging"]},
        {"id": "model-cards", "label": "Model Cards & Documentation Standards", "category": "best-practices",
         "aliases": ["model card", "model documentation", "model transparency report", "model governance"]},
        {"id": "fairness-metrics", "label": "Fairness Metrics in ML", "category": "best-practices",
         "aliases": ["algorithmic fairness", "demographic parity", "equal opportunity", "fairness metric"]},
        {"id": "ai-act-high-risk", "label": "EU AI Act — High-Risk Classification", "category": "regulations",
         "aliases": ["AI Act", "high-risk AI", "EU AI Act", "AI risk classification"]},
        {"id": "ai-conformity-assessment", "label": "AI Conformity Assessment & Auditing", "category": "regulations",
         "aliases": ["AI auditing", "conformity assessment", "AI compliance audit", "algorithm audit"]},
        {"id": "dora-ict-risk", "label": "DORA — ICT Risk Management", "category": "regulations",
         "aliases": ["DORA", "Digital Operational Resilience Act", "ICT risk", "operational resilience"]},
        {"id": "nis2-cyber-resilience", "label": "NIS2 Directive — Cybersecurity Resilience", "category": "best-practices",
         "aliases": ["NIS2", "NIS 2 Directive", "cyber resilience", "network security"]},
        {"id": "data-act-interoperability", "label": "EU Data Act — Data Interoperability", "category": "architecture",
         "aliases": ["EU Data Act", "data interoperability", "data portability", "smart contract safeguards"]},
        {"id": "data-catalog", "label": "Data Catalog", "category": "architecture",
         "aliases": ["data cataloging", "metadata catalog", "data discovery", "data inventory"]},
        {"id": "data-lineage", "label": "Data Lineage", "category": "architecture",
         "aliases": ["data provenance", "data tracing", "column lineage", "impact analysis"]},
        {"id": "dataops", "label": "DataOps", "category": "best-practices",
         "aliases": ["DataOps practices", "data operations", "data lifecycle"]},
        {"id": "lakehouse", "label": "Lakehouse Architecture", "category": "architecture",
         "aliases": ["data lakehouse", "lakehouse paradigm", "unified analytics"]},
        {"id": "feature-store", "label": "Feature Store", "category": "architecture",
         "aliases": ["ML feature store", "feature engineering", "feature serving"]},
        {"id": "data-versioning", "label": "Data Versioning", "category": "best-practices",
         "aliases": ["data version control", "dataset versioning", "data lineage version"]},
        {"id": "metric-store", "label": "Metric Store", "category": "architecture",
         "aliases": ["business metrics", "metric platform", "KPIs metadata"]},
        # Extended seeds
        {"id": "elt-pipeline", "label": "ELT Pipeline Architecture", "category": "architecture",
         "aliases": ["ELT", "load then transform", "modern ELT"]},
        {"id": "reverse-etl", "label": "Reverse ETL", "category": "architecture",
         "aliases": ["operational analytics", "data activation", "warehouse to SaaS"]},
        {"id": "data-contract-testing", "label": "Data Contract Testing", "category": "best-practices",
         "aliases": ["contract testing", "schema testing", "data quality gates"]},
        {"id": "data-discovery", "label": "Data Discovery & Cataloging", "category": "architecture",
         "aliases": ["data catalog", "metadata management", "data marketplace"]},
        {"id": "data-cost-intelligence", "label": "Data Cost Intelligence", "category": "best-practices",
         "aliases": ["FinOps", "data cost optimization", "cost attribution"]},
        {"id": "data-platform-kpis", "label": "Data Platform KPIs", "category": "best-practices",
         "aliases": ["data maturity", "platform metrics", "data reliability"]},
        {"id": "schema-migration", "label": "Schema Migration Strategies", "category": "best-practices",
         "aliases": ["schema evolution", "backward compatibility", "zero-downtime migration"]},
        {"id": "change-data-capture", "label": "Change Data Capture Patterns", "category": "streaming",
         "aliases": ["CDC patterns", "debezium", "log-based CDC", "incremental"]},
        {"id": "real-time-analytics-architecture", "label": "Real-Time Analytics Architecture", "category": "architecture",
         "aliases": ["real-time OLAP", "streaming analytics", "druid", "clickhouse"]},
        {"id": "data-mesh-governance", "label": "Data Mesh Governance", "category": "best-practices",
         "aliases": ["federated governance", "domain ownership", "data product governance"]},
        {"id": "data-quality-monitoring", "label": "Data Quality Monitoring", "category": "best-practices",
         "aliases": ["data observability", "DQ dashboards", "data SLAs"]},
        {"id": "batch-stream-merging", "label": "Batch & Stream Merging", "category": "streaming",
         "aliases": ["lambda architecture", "kappa architecture", "unified batch streaming"]},
        {"id": "data-warehouse-design", "label": "Data Warehouse Design Patterns", "category": "architecture",
         "aliases": ["warehouse design", "dimensional modeling", "star schema"]},
        {"id": "data-quality-sla", "label": "Data Quality SLAs", "category": "best-practices",
         "aliases": ["data SLA", "data reliability", "data uptime"]},
        {"id": "pipeline-cost-optimization", "label": "Pipeline Cost Optimization", "category": "best-practices",
         "aliases": ["cost optimization", "data FinOps", "pipeline efficiency"]},
    ],
}

# Pre-defined relation seeds (source_id, target_id, relation_type, pillar)
PILLAR_RELATION_SEEDS: List[Tuple[str, str, str, str]] = [
    # Compliance
    ("cdd", "kyc", "part_of", "aml"),
    ("edd", "cdd", "part_of", "aml"),
    ("sar", "transaction-monitoring", "enables", "aml"),
    ("str", "transaction-monitoring", "enables", "aml"),
    ("ctr", "transaction-monitoring", "enables", "aml"),
    ("pep", "edd", "requires", "aml"),
    ("sanctions-screening", "kyc", "part_of", "aml"),
    ("entity-resolution", "network-analysis", "related_to", "aml"),
    ("beneficial-ownership", "cdd", "requires", "aml"),
    ("fatf-recommendations", "kyc", "regulates", "aml"),
    ("fatf-recommendations", "sar", "regulates", "aml"),
    ("bsa", "sar", "regulates", "aml"),
    ("bsa", "ctr", "regulates", "aml"),
    ("tbml", "transaction-monitoring", "detects", "aml"),
    ("regtech", "transaction-monitoring", "enables", "aml"),
    ("regtech", "kyc", "enables", "aml"),
    ("travel-rule", "fatf-recommendations", "part_of", "aml"),
    ("travel-rule", "crypto-aml", "regulates", "aml"),
    ("adverse-media", "kyc", "part_of", "aml"),
    ("adverse-media", "sanctions-screening", "related_to", "aml"),
    ("aml-program", "bsa", "implements", "aml"),
    ("cyber-aml", "transaction-monitoring", "related_to", "aml"),
    ("correspondent-banking", "cdd", "requires", "aml"),
    ("regulatory-reporting", "regtech", "implements", "aml"),
    ("crypto-aml", "travel-rule", "requires", "aml"),
    ("crypto-aml", "transaction-monitoring", "enables", "aml"),
    # Markets
    ("market-microstructure", "lob", "requires", "stock"),
    ("hawkes-process", "market-microstructure", "influences", "stock"),
    ("vpin", "market-microstructure", "measures", "stock"),
    ("volatility-surface", "market-microstructure", "related_to", "stock"),
    ("earnings-analysis", "macro-analysis", "related_to", "stock"),
    ("commodity-trading", "macro-analysis", "related_to", "stock"),
    ("portfolio-optimization", "risk-parity", "implements", "stock"),
    ("factor-investing", "portfolio-optimization", "implements", "stock"),
    ("technical-analysis", "market-microstructure", "influences", "stock"),
    ("semiconductor-industry", "supply-chain-analysis", "part_of", "stock"),
    ("ai-hardware", "semiconductor-industry", "influences", "stock"),
    ("options-trading", "volatility-surface", "requires", "stock"),
    ("options-trading", "market-microstructure", "influences", "stock"),
    ("fixed-income", "macro-analysis", "related_to", "stock"),
    ("esg-investing", "factor-investing", "implements", "stock"),
    ("behavioral-finance", "market-microstructure", "influences", "stock"),
    ("behavioral-finance", "technical-analysis", "influences", "stock"),
    ("market-impact", "market-microstructure", "part_of", "stock"),
    ("market-impact", "high-frequency-trading", "related_to", "stock"),
    ("statistical-arbitrage", "market-impact", "requires", "stock"),
    ("high-frequency-trading", "market-microstructure", "enables", "stock"),
    ("asset-pricing", "portfolio-optimization", "requires", "stock"),
    ("asset-pricing", "factor-investing", "related_to", "stock"),
    # Data Engineering
    ("elt", "etl", "supersedes", "data-engineering"),
    ("cdc", "batch-processing", "related_to", "data-engineering"),
    ("streaming", "batch-processing", "related_to", "data-engineering"),
    ("dbt", "elt", "implements", "data-engineering"),
    ("dagster", "etl", "implements", "data-engineering"),
    ("dagster", "elt", "implements", "data-engineering"),
    ("apache-flink", "streaming", "implements", "data-engineering"),
    ("apache-kafka", "streaming", "enables", "data-engineering"),
    ("apache-iceberg", "data-lake", "implements", "data-engineering"),
    ("schema-registry", "data-contracts", "implements", "data-engineering"),
    ("data-contracts", "data-quality", "enables", "data-engineering"),
    ("arrow-parquet", "data-lake", "enables", "data-engineering"),
    ("data-mesh", "data-contracts", "requires", "data-engineering"),
    ("data-observability", "data-quality", "implements", "data-engineering"),
    ("data-pipeline", "etl", "implements", "data-engineering"),
    ("data-pipeline", "streaming", "related_to", "data-engineering"),
    ("data-governance", "data-mesh", "requires", "data-engineering"),
    ("orchestration", "dagster", "related_to", "data-engineering"),
    ("orchestration", "data-pipeline", "enables", "data-engineering"),
    ("query-optimization", "data-warehouse", "enables", "data-engineering"),
    ("real-time-analytics", "streaming", "enables", "data-engineering"),
    ("data-security", "data-governance", "part_of", "data-engineering"),
    ("distributed-systems", "data-mesh", "requires", "data-engineering"),
    ("distributed-systems", "streaming", "enables", "data-engineering"),
    ("ml-pipeline", "data-pipeline", "related_to", "data-engineering"),
    ("ml-pipeline", "orchestration", "requires", "data-engineering"),
    # 2026 Compliance landscape relations
    ("gdpr-anonymization", "gdpr-synthetic-data", "enables", "data-engineering"),
    ("gdpr-synthetic-data", "data-quality", "requires", "data-engineering"),
    ("gdpr-synthetic-data", "debiasing-pipeline", "enables", "data-engineering"),
    ("gdpr-anonymization", "data-security", "implements", "data-engineering"),
    ("differential-privacy", "gdpr-anonymization", "implements", "data-engineering"),
    ("federated-learning", "differential-privacy", "related_to", "data-engineering"),
    ("debiasing-pipeline", "fairness-metrics", "requires", "data-engineering"),
    ("debiasing-pipeline", "ml-pipeline", "implements", "data-engineering"),
    ("model-cards", "ml-pipeline", "implements", "data-engineering"),
    ("model-cards", "debiasing-pipeline", "requires", "data-engineering"),
    ("ai-conformity-assessment", "ml-pipeline", "implements", "data-engineering"),
    ("ai-conformity-assessment", "model-cards", "requires", "data-engineering"),
    ("mica-crypto-assets", "travel-rule", "regulates", "aml"),
    ("esg-double-materiality", "esg-investing", "regulates", "stock"),
    ("data-act-interoperability", "data-contracts", "requires", "data-engineering"),
    ("data-act-interoperability", "schema-registry", "requires", "data-engineering"),
    # New AML relations
    ("ai-aml-surveillance", "transaction-monitoring", "enables", "aml"),
    ("ai-aml-surveillance", "entity-resolution", "enables", "aml"),
    ("fincrime-intelligence", "sar", "enables", "aml"),
    ("fincrime-intelligence", "network-analysis", "requires", "aml"),
    ("fraud-detection", "ai-aml-surveillance", "requires", "aml"),
    ("cross-border-payments", "correspondent-banking", "requires", "aml"),
    ("cross-border-payments", "travel-rule", "requires", "aml"),
    ("aml-optimization", "regtech", "implements", "aml"),
    ("aml-training", "aml-program", "implements", "aml"),
    ("regulatory-filing", "regulatory-reporting", "implements", "aml"),
    # New Markets relations
    ("etf-trading", "market-microstructure", "requires", "stock"),
    ("etf-trading", "lob", "requires", "stock"),
    ("crypto-markets", "market-microstructure", "influences", "stock"),
    ("hedge-funds", "portfolio-optimization", "implements", "stock"),
    ("algorithmic-trading", "high-frequency-trading", "related_to", "stock"),
    ("algorithmic-trading", "market-impact", "requires", "stock"),
    ("retail-trading", "behavioral-finance", "requires", "stock"),
    ("market-data", "lob", "requires", "stock"),
    ("volatility-trading", "volatility-surface", "requires", "stock"),
    ("volatility-trading", "options-trading", "requires", "stock"),
    # New Data Engineering relations
    ("data-catalog", "data-governance", "implements", "data-engineering"),
    ("data-catalog", "data-lineage", "enables", "data-engineering"),
    ("data-lineage", "data-governance", "implements", "data-engineering"),
    ("dataops", "data-pipeline", "enables", "data-engineering"),
    ("dataops", "data-observability", "requires", "data-engineering"),
    ("lakehouse", "data-lake", "supersedes", "data-engineering"),
    ("lakehouse", "apache-iceberg", "implements", "data-engineering"),
    ("feature-store", "ml-pipeline", "requires", "data-engineering"),
    ("feature-store", "data-catalog", "requires", "data-engineering"),
    ("data-versioning", "data-lineage", "enables", "data-engineering"),
    ("metric-store", "data-observability", "implements", "data-engineering"),
    # Extended AML relations
    ("aml-audit", "aml-program", "requires", "aml"),
    ("aml-risk-scoring", "transaction-monitoring", "enables", "aml"),
    ("aml-data-governance", "data-governance", "related_to", "aml"),
    ("aml-case-management", "sar", "implements", "aml"),
    ("aml-model-validation", "ai-aml-surveillance", "requires", "aml"),
    ("aml-threat-intel", "fincrime-intelligence", "enables", "aml"),
    ("global-sanctions", "sanctions-screening", "regulates", "aml"),
    ("trade-finance-aml", "tbml", "detects", "aml"),
    ("payment-fraud", "fraud-detection", "related_to", "aml"),
    ("payment-fraud", "transaction-monitoring", "implements", "aml"),
    ("aml-continuous-monitoring", "transaction-monitoring", "implements", "aml"),
    ("aml-data-sharing", "regulatory-reporting", "enables", "aml"),
    ("aml-oracle", "aml-case-management", "enables", "aml"),
    ("crypto-travel-rule", "travel-rule", "implements", "aml"),
    ("defi-aml", "crypto-aml", "requires", "aml"),
    # Extended Markets relations
    ("order-book", "lob", "implements", "stock"),
    ("dark-pools", "order-book", "related_to", "stock"),
    ("market-making", "order-book", "enables", "stock"),
    ("execution-algos", "algorithmic-trading", "implements", "stock"),
    ("cross-asset-trading", "portfolio-optimization", "implements", "stock"),
    ("regime-detection", "volatility-surface", "enables", "stock"),
    ("carry-trade", "fixed-income", "requires", "stock"),
    ("momentum-trading", "technical-analysis", "implements", "stock"),
    ("mean-reversion", "statistical-arbitrage", "implements", "stock"),
    ("event-driven-trading", "earnings-analysis", "implements", "stock"),
    ("alternative-data", "market-microstructure", "enables", "stock"),
    ("market-surveillance", "market-impact", "detects", "stock"),
    ("quantitative-trading", "algorithmic-trading", "implements", "stock"),
    ("volatility-arbitrage", "volatility-trading", "implements", "stock"),
    ("machine-learning-markets", "alternative-data", "enables", "stock"),
    # Extended Data Engineering relations
    ("elt-pipeline", "elt", "implements", "data-engineering"),
    ("reverse-etl", "data-warehouse", "enables", "data-engineering"),
    ("data-contract-testing", "data-contracts", "implements", "data-engineering"),
    ("data-discovery", "data-catalog", "implements", "data-engineering"),
    ("data-cost-intelligence", "dataops", "implements", "data-engineering"),
    ("data-platform-kpis", "data-observability", "requires", "data-engineering"),
    ("schema-migration", "schema-registry", "enables", "data-engineering"),
    ("change-data-capture", "cdc", "implements", "data-engineering"),
    ("real-time-analytics-architecture", "real-time-analytics", "implements", "data-engineering"),
    ("data-mesh-governance", "data-mesh", "implements", "data-engineering"),
    ("data-quality-monitoring", "data-quality", "implements", "data-engineering"),
    ("batch-stream-merging", "streaming", "requires", "data-engineering"),
    ("batch-stream-merging", "batch-processing", "related_to", "data-engineering"),
    ("data-warehouse-design", "data-warehouse", "implements", "data-engineering"),
    ("data-quality-sla", "data-quality", "implements", "data-engineering"),
    ("pipeline-cost-optimization", "data-cost-intelligence", "implements", "data-engineering"),
    # Wire up orphan concepts
    ("aml-esg-risk", "aml-program", "related_to", "aml"),
    ("aml-esg-risk", "esg-investing", "related_to", "aml"),
    ("aml-international", "aml-data-sharing", "enables", "aml"),
    ("aml-international", "regulatory-reporting", "enables", "aml"),
    ("aml-reporting-dashboard", "regulatory-reporting", "implements", "aml"),
    ("de-risk", "correspondent-banking", "related_to", "aml"),
    ("de-risk", "aml-risk-scoring", "requires", "aml"),
    ("fincen-boi", "beneficial-ownership", "implements", "aml"),
    ("fincen-boi", "regulatory-filing", "implements", "aml"),
    ("etf-creation", "etf-trading", "requires", "stock"),
    ("etf-creation", "order-book", "enables", "stock"),
    ("fx-markets", "market-microstructure", "related_to", "stock"),
    ("fx-markets", "market-participants", "requires", "stock"),
    ("stock-lending", "market-making", "enables", "stock"),
    ("stock-lending", "market-impact", "related_to", "stock"),
]

# Cross-pillar relations
CROSS_PILLAR_SEEDS: List[Tuple[str, str, str]] = [
    ("transaction-monitoring", "streaming", "requires"),
    ("transaction-monitoring", "cdc", "requires"),
    ("entity-resolution", "data-quality", "requires"),
    ("network-analysis", "data-mesh", "related_to"),
    ("regtech", "dagster", "related_to"),
    ("market-microstructure", "streaming", "requires"),
    ("data-contracts", "fatf-recommendations", "related_to"),
    ("crypto-aml", "data-security", "related_to"),
    ("cyber-aml", "distributed-systems", "related_to"),
    ("adverse-media", "ml-pipeline", "related_to"),
    ("regulatory-reporting", "data-pipeline", "enables"),
    ("high-frequency-trading", "streaming", "requires"),
    ("real-time-analytics", "market-microstructure", "enables"),
    ("behavioral-finance", "data-quality", "related_to"),
    ("aml-program", "orchestration", "related_to"),
    ("market-impact", "distributed-systems", "related_to"),
    # 2026 Compliance landscape cross-pillar relations
    ("ai-act-high-risk", "transaction-monitoring", "regulates"),
    ("ai-act-high-risk", "high-frequency-trading", "regulates"),
    ("ai-act-high-risk", "ml-pipeline", "regulates"),
    ("ai-conformity-assessment", "ai-act-high-risk", "implements"),
    ("dora-ict-risk", "data-observability", "requires"),
    ("dora-ict-risk", "distributed-systems", "requires"),
    ("dora-ict-risk", "data-contracts", "requires"),
    ("dora-ict-risk", "orchestration", "requires"),
    ("nis2-cyber-resilience", "cyber-aml", "related_to"),
    ("nis2-cyber-resilience", "data-security", "regulates"),
    ("nis2-cyber-resilience", "dora-ict-risk", "related_to"),
    ("mica-crypto-assets", "crypto-aml", "regulates"),
    ("mica-crypto-assets", "transaction-monitoring", "regulates"),
    ("esg-double-materiality", "aml-program", "related_to"),
    ("data-act-interoperability", "data-mesh", "related_to"),
    ("market-surveillance", "transaction-monitoring", "related_to"),
    ("alternative-data", "data-catalog", "related_to"),
    ("payment-fraud", "streaming", "related_to"),
    ("trade-finance-aml", "cdc", "related_to"),
    ("aml-model-validation", "data-quality", "related_to"),
    ("execution-algos", "real-time-analytics", "related_to"),
    ("machine-learning-markets", "data-quality", "related_to"),
    ("aml-risk-scoring", "fairness-metrics", "related_to"),
    # AML ↔ Stock cross-pillar analogs
    ("kyc", "market-data", "related_to"),
    ("kyc", "market-participants", "related_to"),
    ("transaction-monitoring", "market-surveillance", "related_to"),
    ("sar", "market-impact", "related_to"),
    ("entity-resolution", "order-book", "related_to"),
    ("network-analysis", "market-microstructure", "related_to"),
    ("beneficial-ownership", "stock-lending", "related_to"),
    ("aml-program", "portfolio-optimization", "related_to"),
    ("regtech", "algorithmic-trading", "related_to"),
    ("risk-based-approach", "risk-parity", "related_to"),
    ("aml-compliance-basics", "equity-basics", "related_to"),
    ("aml-regulatory-framework", "market-indices", "related_to"),
    ("financial-crime-types", "trading-venues", "related_to"),
    ("money-laundering-basics", "order-types", "related_to"),
]


class OntologyManager:
    """Central registry for concepts, relations, and resource links."""

    def __init__(self) -> None:
        self._concepts: Dict[str, Concept] = {}
        self._relations: List[Relation] = []
        self._resource_links: List[ResourceLink] = []
        self._alias_index: Dict[str, str] = {}  # alias_lower → concept_id
        self._pillar_index: Dict[str, Set[str]] = defaultdict(set)  # pillar → {concept_ids}
        self._category_index: Dict[str, Set[str]] = defaultdict(set)  # category → {concept_ids}
        self._cache: Optional[OntologyCache] = None
        self._revision: int = 0  # incremented on mutations; read by PhraseMatcher

    def _bump_revision(self):
        """Increment revision counter and invalidate the spaCy matcher."""
        self._revision += 1
        _invalidate_matcher()

    # ---- Concepts ----

    def add_concept(self, concept: Concept, *, overwrite: bool = False) -> None:
        """Add or update a concept in the ontology."""
        existing = self._concepts.get(concept.id)
        if existing and not overwrite:
            # Merge aliases
            for alias in concept.aliases:
                if alias.lower() not in self._alias_index:
                    self._alias_index[alias.lower()] = concept.id
            existing.aliases = list(set(existing.aliases + concept.aliases))
            existing.properties.update(concept.properties)
            existing.updated_at = datetime.now(timezone.utc).isoformat()
            if self._cache:
                self._cache.invalidate()
            self._bump_revision()
            return
        self._concepts[concept.id] = concept
        self._pillar_index[concept.pillar].add(concept.id)
        self._category_index[concept.category].add(concept.id)
        for alias in concept.aliases:
            self._alias_index[alias.lower()] = concept.id
        if self._cache:
            self._cache.invalidate()
        self._bump_revision()

    def get_concept(self, concept_id: str) -> Optional[Concept]:
        return self._concepts.get(concept_id)

    def resolve_alias(self, name: str) -> Optional[Concept]:
        """Resolve a label or alias to a Concept."""
        cid = self._alias_index.get(name.lower())
        if cid:
            return self._concepts.get(cid)
        return None

    def find_concepts(
        self,
        *,
        pillar: Optional[str] = None,
        category: Optional[str] = None,
        text_query: Optional[str] = None,
    ) -> List[Concept]:
        """Filter concepts by pillar, category, or substring match on label."""
        candidates: Optional[Set[str]] = None
        if pillar:
            candidates = set(self._pillar_index.get(pillar, set()))
        if category:
            cat_set = set(self._category_index.get(category, set()))
            candidates = cat_set if candidates is None else candidates & cat_set
        if candidates is None:
            candidates = set(self._concepts.keys())
        results = [self._concepts[cid] for cid in candidates if cid in self._concepts]
        if text_query:
            tq = text_query.lower()
            results = [c for c in results if tq in c.label.lower() or any(tq in a.lower() for a in c.aliases)]
        return sorted(results, key=lambda c: c.label)

    def concepts_by_pillar(self) -> Dict[str, List[Concept]]:
        """Return concepts grouped by pillar."""
        out: Dict[str, List[Concept]] = defaultdict(list)
        for c in self._concepts.values():
            out[c.pillar].append(c)
        for k in out:
            out[k].sort(key=lambda c: c.label)
        return dict(out)

    # ---- Relations ----

    def add_relation(self, relation: Relation, *, allow_self: bool = False) -> None:
        """Add a relation, validating that both concepts exist."""
        if not allow_self and relation.source_id == relation.target_id:
            return
        key = (relation.source_id, relation.target_id, relation.relation_type)
        for existing in self._relations:
            if (existing.source_id, existing.target_id, existing.relation_type) == key:
                existing.strength = max(existing.strength, relation.strength)
                existing.evidence = list(set(existing.evidence + relation.evidence))
                if self._cache:
                    self._cache.invalidate()
                return
        self._relations.append(relation)
        if self._cache:
            self._cache.invalidate()

    def relations_for(self, concept_id: str) -> List[Relation]:
        """Get all relations where concept_id is source or target."""
        return [
            r for r in self._relations
            if r.source_id == concept_id or r.target_id == concept_id
        ]

    def outgoing_relations(self, concept_id: str) -> List[Relation]:
        return [r for r in self._relations if r.source_id == concept_id]

    def incoming_relations(self, concept_id: str) -> List[Relation]:
        return [r for r in self._relations if r.target_id == concept_id]

    def related_concepts(self, concept_id: str) -> List[Concept]:
        """Get all concepts related (source or target) to concept_id."""
        ids: Set[str] = set()
        for r in self.relations_for(concept_id):
            other = r.target_id if r.source_id == concept_id else r.source_id
            ids.add(other)
        return [self._concepts[cid] for cid in ids if cid in self._concepts]

    # ---- Resource Links ----

    def add_resource_link(self, link: ResourceLink) -> None:
        self._resource_links.append(link)

    def resource_links_for(self, concept_id: str) -> List[ResourceLink]:
        return [rl for rl in self._resource_links if rl.concept_id == concept_id]

    # ---- Graph export / import ----

    def to_dict(self) -> Dict[str, Any]:
        """Serialise to a JSON-compatible dict."""
        return {
            "concepts": [c.model_dump() for c in self._concepts.values()],
            "relations": [r.model_dump() for r in self._relations],
            "resource_links": [rl.model_dump() for rl in self._resource_links],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OntologyManager":
        """Load from a serialised dict."""
        mgr = cls()
        for c_data in data.get("concepts", []):
            mgr.add_concept(Concept(**c_data))
        for r_data in data.get("relations", []):
            mgr.add_relation(Relation(**r_data))
        for rl_data in data.get("resource_links", []):
            mgr.add_resource_link(ResourceLink(**rl_data))
        return mgr

    def save(self, path: Path | str) -> None:
        Path(path).write_text(json.dumps(self.to_dict(), indent=2, default=str), encoding="utf-8")

    @classmethod
    def load(cls, path: Path | str) -> "OntologyManager":
        p = Path(path)
        if not p.exists():
            return cls()
        return cls.from_dict(json.loads(p.read_text(encoding="utf-8")))

    # ---- Integration with existing knowledge graph ----

    def to_cytograph_nodes(self) -> List[Dict[str, Any]]:
        """Export concepts as Cytoscape-compatible node dicts."""
        nodes = []
        for c in self._concepts.values():
            nodes.append({
                "data": {
                    "id": f"ont:{c.id}",
                    "label": c.label,
                    "type": "concept",
                    "domain": c.pillar,
                    "category": c.category,
                    "size": 30 + int(c.confidence_score * 20),
                }
            })
        return nodes

    def to_cytograph_edges(self) -> List[Dict[str, Any]]:
        """Export relations as Cytoscape-compatible edge dicts."""
        edges = []
        for i, r in enumerate(self._relations):
            src = self._concepts.get(r.source_id)
            tgt = self._concepts.get(r.target_id)
            source_pillar = src.pillar if src else ""
            target_pillar = tgt.pillar if tgt else ""
            edges.append({
                "data": {
                    "id": f"ont-rel:{i}",
                    "source": f"ont:{r.source_id}",
                    "target": f"ont:{r.target_id}",
                    "relation": r.relation_type,
                    "strength": r.strength,
                    "sourcePillar": source_pillar,
                    "targetPillar": target_pillar,
                }
            })
        return edges

    def merge_into_cytograph(self, cytograph: Dict[str, Any]) -> Dict[str, Any]:
        """Merge ontology nodes/edges into an existing Cytoscape graph dict."""
        existing_ids = {
            n["data"]["id"] for n in cytograph.get("nodes", [])
        }
        for node in self.to_cytograph_nodes():
            if node["data"]["id"] not in existing_ids:
                cytograph.setdefault("nodes", []).append(node)
        existing_edges = {
            e["data"]["id"] for e in cytograph.get("edges", [])
        }
        for edge in self.to_cytograph_edges():
            if edge["data"]["id"] not in existing_edges:
                cytograph.setdefault("edges", []).append(edge)
        return cytograph

    # ---- Seeding from canonical data ----

    def seed_pillar(self, pillar: str) -> int:
        """Seed the ontology with canonical concepts for a pillar. Returns count added."""
        seeds = PILLAR_CONCEPT_SEEDS.get(pillar, [])
        added = 0
        for seed in seeds:
            if pillar not in self._pillar_index or seed["id"] not in self._concepts:
                self.add_concept(Concept(pillar=pillar, **seed))
                added += 1
        return added

    def seed_all_pillars(self) -> int:
        """Seed all pillars. Returns total concepts added."""
        total = 0
        for pillar in PILLAR_CONCEPT_SEEDS:
            total += self.seed_pillar(pillar)
        if self._cache:
            self._cache.invalidate()
        return total

    def seed_relations(self) -> int:
        """Seed canonical relations. Returns count added."""
        added = 0
        for src, tgt, rtype, pillar in PILLAR_RELATION_SEEDS:
            if src in self._concepts and tgt in self._concepts:
                self.add_relation(Relation(
                    source_id=src, target_id=tgt, relation_type=rtype, pillar=pillar,
                ))
                added += 1
        for src, tgt, rtype in CROSS_PILLAR_SEEDS:
            if src in self._concepts and tgt in self._concepts:
                self.add_relation(Relation(
                    source_id=src, target_id=tgt, relation_type=rtype, pillar="cross-pillar",
                ))
                added += 1
        return added

    # ---- Cross-pillar analog auto-population ----

    def auto_populate_cross_pillar_analogs(self) -> int:
        """Auto-populate cross_pillar_analogs based on epistemic_status AND category.

        For each pair of concepts in different pillars, they are cross-linked as
        analogs only when BOTH epistemic_status AND category match (AND predicate).
        Caps at 3 analogs per concept, ranked by confidence_score.
        Returns count of analogs added.
        """
        from collections import defaultdict

        PILLAR_KEYS_SET = {"aml", "stock", "data-engineering"}
        added = 0
        concepts = list(self._concepts.values())

        # Build candidate pairs: group by (category, epistemic_status)
        groups: dict[tuple, list] = defaultdict(list)
        for c in concepts:
            if c.pillar not in PILLAR_KEYS_SET:
                continue
            ep = getattr(c, "epistemic_status", None)
            cat = getattr(c, "category", None)
            if ep and cat:
                groups[(cat, ep)].append(c)

        MAX_ANALOGS = 3

        # Within each group, link cross-pillar pairs
        for (cat, ep), group in groups.items():
            for i, c1 in enumerate(group):
                for c2 in group[i + 1:]:
                    if c1.pillar == c2.pillar:
                        continue

                    existing = getattr(c1, "cross_pillar_analogs", []) or []
                    if c2.id not in existing:
                        existing.append(c2.id)
                        c1.cross_pillar_analogs = existing
                        added += 1

                    existing2 = getattr(c2, "cross_pillar_analogs", []) or []
                    if c1.id not in existing2:
                        existing2.append(c1.id)
                        c2.cross_pillar_analogs = existing2
                        added += 1

        # Cap at MAX_ANALOGS per concept, keeping highest-confidence analogs
        for c in concepts:
            analogs = getattr(c, "cross_pillar_analogs", []) or []
            if len(analogs) <= MAX_ANALOGS:
                continue
            # Rank by confidence_score of the analog concept
            scored = []
            for aid in analogs:
                ac = self._concepts.get(aid)
                if ac:
                    scored.append((aid, getattr(ac, "confidence_score", 0.5)))
            scored.sort(key=lambda x: -x[1])
            c.cross_pillar_analogs = [aid for aid, _ in scored[:MAX_ANALOGS]]

        return added

    # ---- Cache integration ----

    def enable_cache(self, cache_dir: Optional[Path] = None) -> OntologyCache:
        """Enable multi-level caching for expensive ontology operations.

        Creates and returns an :class:`OntologyCache` instance.  The cache is
        *not* enabled by default (backward compatible).  Once enabled, mutation
        methods (``add_concept``, ``add_relation``, ``seed_all_pillars``)
        automatically invalidate cached entries.
        """
        from core.ontology_cache import OntologyCache as _OntologyCache

        self._cache = _OntologyCache(self, cache_dir=cache_dir)
        return self._cache

    # ---- Utility ----

    def concept_count(self) -> int:
        return len(self._concepts)

    def relation_count(self) -> int:
        return len(self._relations)

    def resource_link_count(self) -> int:
        return len(self._resource_links)

    def pillar_summary(self) -> Dict[str, Dict[str, int]]:
        """Return per-pillar counts of concepts and relations."""
        summary: Dict[str, Dict[str, int]] = {}
        for pillar in PILLAR_KEYS:
            c_count = len(self._pillar_index.get(pillar, set()))
            r_count = sum(1 for r in self._relations if r.pillar == pillar)
            summary[pillar] = {"concepts": c_count, "relations": r_count}
        return summary

# ---------------------------------------------------------------------------
# Text-based concept extraction (spaCy PhraseMatcher with regex fallback)
# ---------------------------------------------------------------------------

_NLP: Any = None
_PHRASE_MATCHER: Any = None
_MATCHER_REVISION = -1


def _load_nlp():
    """Load spaCy English model lazily (once per process)."""
    global _NLP
    if _NLP is None:
        try:
            import spacy
            _NLP = spacy.load("en_core_web_sm", disable=["parser", "ner", "lemmatizer"])
            logger.info("spaCy PhraseMatcher loaded for concept extraction")
        except Exception as e:
            logger.warning(f"spaCy model unavailable ({e}), using regex fallback")
            _NLP = False  # sentinel: don't retry
    return _NLP if _NLP is not False else None


def _strip_parens(label: str) -> str:
    """Strip parenthetical annotations from labels for matching."""
    import re as _re
    cleaned = _re.sub(r'\s*\([^)]*\)', '', label).strip()
    return cleaned or label


def _collect_phrases(manager: OntologyManager) -> Dict[str, str]:
    """Collect all unique label/alias texts -> concept_id.

    For labels with parentheses (e.g. 'Know Your Customer (KYC)'),
    adds both the full label and the parenthetical-stripped version.
    """
    phrases: Dict[str, str] = {}
    for cid, concept in manager._concepts.items():
        stripped = _strip_parens(concept.label)
        if stripped and stripped not in phrases:
            phrases[stripped] = cid
        if concept.label not in phrases:
            phrases[concept.label] = cid
        for alias in concept.aliases:
            alias_s = _strip_parens(alias)
            if alias_s and alias_s not in phrases and alias_s != stripped:
                phrases[alias_s] = cid
            if alias not in phrases and alias != concept.label:
                phrases[alias] = cid
    return phrases


def _build_phrase_matcher(manager: OntologyManager):
    """Build or rebuild the spaCy PhraseMatcher from the manager's concepts.

    Uses a revision counter to avoid rebuilding on every call.
    """
    global _PHRASE_MATCHER, _MATCHER_REVISION
    current_revision = getattr(manager, '_revision', 0)
    if _PHRASE_MATCHER is not None and _MATCHER_REVISION == current_revision:
        return _PHRASE_MATCHER

    nlp = _load_nlp()
    if nlp is None:
        _PHRASE_MATCHER = None
        return None

    try:
        from spacy.matcher import PhraseMatcher
    except ImportError:
        _PHRASE_MATCHER = None
        return None

    phrases = _collect_phrases(manager)
    matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
    patterns = [nlp.make_doc(text) for text in phrases]
    if patterns:
        matcher.add("CONCEPTS", patterns)
    _PHRASE_MATCHER = matcher
    _MATCHER_REVISION = current_revision
    return matcher


def extract_concepts_from_text(
    text: str,
    manager: OntologyManager,
    *,
    min_confidence: float = 0.5,
) -> List[Tuple[Concept, float]]:
    """Match text against known concepts (label + aliases). Returns (concept, confidence).

    Uses spaCy PhraseMatcher for token-aware matching when available.
    Falls back to regex word-boundary matching when spaCy model is unavailable.
    """
    if not text:
        return []

    matcher = _build_phrase_matcher(manager)
    if matcher is not None:
        return _extract_with_spacy(text, manager, matcher, min_confidence)
    return _extract_with_regex(text, manager, min_confidence)


def _extract_with_spacy(
    text: str,
    manager: OntologyManager,
    matcher: Any,
    min_confidence: float,
) -> List[Tuple[Concept, float]]:
    """Concept extraction using spaCy PhraseMatcher (token-aware)."""
    nlp = _NLP
    if nlp is None:
        return _extract_with_regex(text, manager, min_confidence)

    doc = nlp(text)
    matches = matcher(doc)
    phrases = _collect_phrases(manager)
    phrase_to_cid = {k.lower(): v for k, v in phrases.items()}
    seen: Dict[str, float] = {}

    for match_id, start, end in matches:
        span_text = doc[start:end].text.lower()
        cid = phrase_to_cid.get(span_text, "")
        if not cid:
            continue
        concept = manager._concepts.get(cid)
        if concept is None:
            continue
        # Determine if this is a label match or alias match
        label_lower = concept.label.lower()
        label_stripped = _strip_parens(concept.label).lower()
        is_label_match = (
            span_text == label_lower
            or span_text == label_stripped
        )
        score = concept.confidence_score if is_label_match else concept.confidence_score * 0.9
        if score >= min_confidence and cid not in seen:
            seen[cid] = score
    return [(manager._concepts[cid], score) for cid, score in
            sorted(seen.items(), key=lambda x: -x[1])]


def _extract_with_regex(
    text: str,
    manager: OntologyManager,
    min_confidence: float,
) -> List[Tuple[Concept, float]]:
    """Fallback concept extraction using regex word-boundary matching."""
    import re as _re
    text_lower = text.lower()
    seen: Dict[str, float] = {}
    for concept in manager._concepts.values():
        label = concept.label.lower()
        if _re.search(r'\b' + _re.escape(label) + r'\b', text_lower):
            score = concept.confidence_score
            if score >= min_confidence and concept.id not in seen:
                seen[concept.id] = score
                continue
        for alias in concept.aliases:
            alias_lower = alias.lower()
            if _re.search(r'\b' + _re.escape(alias_lower) + r'\b', text_lower) and alias_lower != label:
                score = concept.confidence_score * 0.9
                if score >= min_confidence and concept.id not in seen:
                    seen[concept.id] = score
                    break
    return [(manager._concepts[cid], score) for cid, score in
            sorted(seen.items(), key=lambda x: -x[1])]


def _invalidate_matcher():
    """Force PhraseMatcher rebuild on next extraction (called when concepts change)."""
    global _MATCHER_REVISION
    _MATCHER_REVISION = -1
