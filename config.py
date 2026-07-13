"""Single source of truth for AcaciaFund environment configuration.

All paths are relative to this file's directory (project root).
Import this from build.py and anywhere else config values are needed.
"""

from pathlib import Path

PROJECT_ROOT = Path(__file__).parent

# Site identity
SITE_URL = "https://www.acaciafund.org"
SITE_NAME = "AcaciaFund"
SITE_DESCRIPTION = (
    "AcaciaFund — research synthesis & experimental learning platform. "
    "Automated classification of HackerNews + arXiv content using Bloom taxonomy. "
    "Static-first, privacy-preserving."
)
PLAUSIBLE_DOMAIN = ""

# Paths (source)
REGISTRY_PATH = PROJECT_ROOT / "registry.json"
TEMPLATE_DIR = PROJECT_ROOT / "templates"
PIPELINE_STATIC_DIR = PROJECT_ROOT / "static"
CONTENT_DIR = PROJECT_ROOT / "content"

# Paths (build output)
OUTPUT_DIR = PROJECT_ROOT / "dist"
STATIC_DST_DIR = OUTPUT_DIR / "static"

# Quality thresholds
SQI_THRESHOLD_MIN = 0.65  # minimum SQI for quality gate pass
SQI_BADGE_HIGH = 0.6  # SQI above this → green badge
SQI_BADGE_MED = 0.35  # SQI above this → amber badge (below → red)
SQI_DEFAULT = 0.5  # fallback when signal missing

# Interest score weights
INTEREST_SQI_WEIGHT = 0.6
INTEREST_RECENCY_WEIGHT = 0.4
INTEREST_RECENCY_DAYS = 180

# Pillar URL mapping: internal key → URL segment
# "stock" maps to "markets" in URLs for better semantics
PILLAR_URL_MAP = {"aml": "compliance", "stock": "markets", "data-engineering": "data"}
PILLAR_URL_REVERSE = {v: k for k, v in PILLAR_URL_MAP.items()}

# URL structure version — bump to force full cache rebuild on structural changes
URL_STRUCTURE_VERSION = "3.0"

# ---------------------------------------------------------------------------
# Pillar-specific subcategories (12-15 per pillar)
# Used for knowledge taxonomy and content classification within each pillar.
# Keys match the `category` field on Knowledge items and Concept objects.
# ---------------------------------------------------------------------------
PILLAR_SUBCATEGORIES: dict[str, dict[str, dict[str, str]]] = {
    "aml": {
        "risk-assessment": {
            "label": "Risk Assessment",
            "icon": "⚖️",
            "description": "AML risk scoring, typologies, and mitigation strategies",
        },
        "cdd-kyc": {
            "label": "CDD/KYC",
            "icon": "🆔",
            "description": "Customer due diligence, identity verification, and onboarding",
        },
        "sar-str": {
            "label": "SAR/STR Reporting",
            "icon": "🚨",
            "description": "Suspicious activity and transaction report detection and filing",
        },
        "regtech": {
            "label": "RegTech",
            "icon": "💻",
            "description": "Technology solutions for compliance automation and monitoring",
        },
        "sanctions": {
            "label": "Sanctions",
            "icon": "🚫",
            "description": "OFAC, UN, EU sanctions screening and compliance",
        },
        "transaction-monitoring": {
            "label": "Transaction Monitoring",
            "icon": "📡",
            "description": "Real-time and batch monitoring for suspicious patterns",
        },
        "beneficial-ownership": {
            "label": "Beneficial Ownership",
            "icon": "🏢",
            "description": "UBO identification, corporate structure analysis, transparency",
        },
        "trade-based-ml": {
            "label": "Trade-Based ML",
            "icon": "🚢",
            "description": "TBML detection, trade invoice manipulation, customs fraud",
        },
        "regulations": {
            "label": "Regulations",
            "icon": "📋",
            "description": "FATF, BSA, MiFID II, Basel III, GDPR compliance frameworks",
        },
        "financial-intelligence": {
            "label": "Financial Intelligence",
            "icon": "🔍",
            "description": "FIU operations, intelligence analysis, cross-border cooperation",
        },
        "crypto-aml": {
            "label": "Crypto AML",
            "icon": "₿",
            "description": "Virtual asset service provider compliance, Travel Rule, DeFi AML",
        },
        "adverse-media": {
            "label": "Adverse Media",
            "icon": "📰",
            "description": "Negative news screening, reputation risk, open-source intelligence",
        },
        "network-analysis": {
            "label": "Network Analysis",
            "icon": "🕸️",
            "description": "Graph analytics, entity relationship mapping, fund flow tracing",
        },
        "enforcement": {
            "label": "Enforcement",
            "icon": "🔨",
            "description": "Regulatory enforcement actions, penalties, compliance failures",
        },
    },
    "data-engineering": {
        "pipeline-architecture": {
            "label": "Pipeline Architecture",
            "icon": "🏗️",
            "description": "ETL/ELT pipeline design, orchestration, and patterns",
        },
        "streaming": {
            "label": "Streaming",
            "icon": "⚡",
            "description": "Real-time stream processing with Kafka, Flink, Spark Streaming",
        },
        "batch-processing": {
            "label": "Batch Processing",
            "icon": "📦",
            "description": "Scheduled batch jobs, Spark, distributed compute",
        },
        "storage-formats": {
            "label": "Storage Formats",
            "icon": "🗄️",
            "description": "Parquet, Iceberg, Delta Lake, Hudi, columnar storage",
        },
        "data-quality": {
            "label": "Data Quality",
            "icon": "✅",
            "description": "Data validation, observability, testing, contracts",
        },
        "data-governance": {
            "label": "Data Governance",
            "icon": "📜",
            "description": "Data catalogs, lineage, access control, metadata management",
        },
        "analytics-engineering": {
            "label": "Analytics Engineering",
            "icon": "🧮",
            "description": "dbt, SQLMesh, semantic layer, metrics frameworks",
        },
        "orchestration": {
            "label": "Orchestration",
            "icon": "🎛️",
            "description": "Dagster, Airflow, Prefect — workflow orchestration and scheduling",
        },
        "schema-management": {
            "label": "Schema Management",
            "icon": "📐",
            "description": "Schema registries, evolution strategies, data contracts",
        },
        "cost-optimization": {
            "label": "Cost Optimization",
            "icon": "💰",
            "description": "Compute efficiency, storage tiering, workload scheduling",
        },
        "data-mesh-fabric": {
            "label": "Data Mesh/Fabric",
            "icon": "🌐",
            "description": "Decentralized data architectures, domain-oriented ownership",
        },
        "ml-pipelines": {
            "label": "ML Pipelines",
            "icon": "🤖",
            "description": "Feature stores, model training pipelines, ML ops",
        },
        "platform-engineering": {
            "label": "Platform Engineering",
            "icon": "⚙️",
            "description": "Internal developer platforms, self-service data infrastructure",
        },
        "cybernetic-theory": {
            "label": "Cybernetic Theory",
            "icon": "🧠",
            "description": "Theoretical foundations — feedback loops, information theory, SQI",
        },
    },
    "stock": {
        "market-microstructure": {
            "label": "Market Microstructure",
            "icon": "🔬",
            "description": "Limit order books, price formation, execution dynamics",
        },
        "volatility-analysis": {
            "label": "Volatility Analysis",
            "icon": "📊",
            "description": "Implied surfaces, stochastic models, term structure",
        },
        "quantitative-methods": {
            "label": "Quantitative Methods",
            "icon": "🧮",
            "description": "Statistical modeling, Hawkes processes, VPIN, point processes",
        },
        "trading-strategies": {
            "label": "Trading Strategies",
            "icon": "🎯",
            "description": "Systematic, algorithmic, and factor-based trading approaches",
        },
        "risk-management": {
            "label": "Risk Management",
            "icon": "🛡️",
            "description": "Portfolio risk, VaR, stress testing, systemic risk",
        },
        "portfolio-construction": {
            "label": "Portfolio Construction",
            "icon": "📐",
            "description": "Asset allocation, optimization, factor investing",
        },
        "industry-analysis": {
            "label": "Industry Analysis",
            "icon": "🏭",
            "description": "Sector research, supply chains, competitive dynamics",
        },
        "macro-economics": {
            "label": "Macro Economics",
            "icon": "🌍",
            "description": "Economic indicators, monetary policy, global macro",
        },
        "earnings-analysis": {
            "label": "Earnings Analysis",
            "icon": "💹",
            "description": "Earnings reports, financial modeling, valuation frameworks",
        },
        "commodity-markets": {
            "label": "Commodity Markets",
            "icon": "🛢️",
            "description": "Commodity trading, futures curves, supply/demand dynamics",
        },
        "semiconductor-sector": {
            "label": "Semiconductor Sector",
            "icon": "💎",
            "description": "Chip industry analysis, supply chain, AI hardware trends",
        },
        "behavioral-finance": {
            "label": "Behavioral Finance",
            "icon": "🧠",
            "description": "Cognitive biases, sentiment analysis, market psychology",
        },
        "technical-analysis": {
            "label": "Technical Analysis",
            "icon": "📈",
            "description": "Chart patterns, indicators, momentum, mean reversion",
        },
        "structured-products": {
            "label": "Structured Products",
            "icon": "🔗",
            "description": "Derivatives, options pricing, structured finance",
        },
    },
}

# Mapping from knowledge categories (cross-pillar) to pillar-specific subcategories.
# Used to resolve knowledge items to their relevant pillar taxonomy.
KNOWLEDGE_TO_PILLAR_CATEGORY: dict[str, dict[str, str]] = {
    "platform": {"aml": "regtech", "stock": "market-microstructure", "data-engineering": "platform-engineering"},
    "guide": {"aml": "cdd-kyc", "stock": "trading-strategies", "data-engineering": "pipeline-architecture"},
    "reference": {"aml": "regulations", "stock": "market-microstructure", "data-engineering": "data-governance"},
    "architecture": {"aml": "network-analysis", "stock": "portfolio-construction", "data-engineering": "data-mesh-fabric"},
    "foundations": {"aml": "risk-assessment", "stock": "market-microstructure", "data-engineering": "pipeline-architecture"},
    "advanced-techniques": {"aml": "network-analysis", "stock": "quantitative-methods", "data-engineering": "streaming"},
    "best-practices": {"aml": "regtech", "stock": "risk-management", "data-engineering": "data-quality"},
    "regulations": {"aml": "regulations", "stock": "risk-management", "data-engineering": "data-governance"},
    "industry-analysis": {"aml": "trade-based-ml", "stock": "industry-analysis", "data-engineering": "analytics-engineering"},
    "market-analysis": {"aml": "financial-intelligence", "stock": "market-microstructure", "data-engineering": "analytics-engineering"},
    "strategies": {"aml": "regtech", "stock": "trading-strategies", "data-engineering": "orchestration"},
}
