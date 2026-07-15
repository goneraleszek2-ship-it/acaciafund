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
PLAUSIBLE_DOMAIN = "plausible.io"

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
# Derived from PILLAR_CONFIG below; keep as fallbacks until override after PILLAR_CONFIG
PILLAR_NAMES_BASE = {"aml": "Compliance", "stock": "Markets", "data-engineering": "Data Engineering"}
PILLAR_EMOJIS_BASE = {"aml": "🛡️", "stock": "📈", "data-engineering": "⚙️"}
PILLAR_NAMES = dict(PILLAR_NAMES_BASE)
PILLAR_EMOJIS = dict(PILLAR_EMOJIS_BASE)

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
    "methodology": {"aml": "risk-assessment", "stock": "quantitative-methods", "data-engineering": "analytics-engineering"},
    "tutorial-code": {"aml": "regtech", "stock": "trading-strategies", "data-engineering": "pipeline-architecture"},
}

# Pillar visual/config metadata (used by build.py for templates and rendering)
# label, url, emoji are derived from the source-of-truth dicts above;
# extra fields (color, bg, accent, heading, description) are presentation-only.
PILLAR_CONFIG: dict[str, dict[str, str]] = {
    "aml": {
        "label": "Compliance",
        "url": "compliance",
        "emoji": "🛡️",
        "color": "slate",
        "bg": "from-slate-900 to-slate-800",
        "accent": "amber",
        "text_color": "text-slate-900",
        "badge_color": "bg-amber-100 text-amber-800",
        "heading": "Compliance & Financial Crime",
        "description": "Anti-money laundering, regulatory compliance, financial crime detection, and risk management.",
    },
    "stock": {
        "label": "Markets",
        "url": "markets",
        "emoji": "📈",
        "color": "green",
        "bg": "from-green-900 to-green-800",
        "accent": "green",
        "text_color": "text-green-900",
        "badge_color": "bg-green-100 text-green-800",
        "heading": "Markets & Industry",
        "description": "Semiconductors, supply chains, AI industry, manufacturing.",
    },
    "data-engineering": {
        "label": "Data Engineering",
        "url": "data",
        "emoji": "⚙️",
        "color": "indigo",
        "bg": "from-indigo-900 to-indigo-800",
        "accent": "indigo",
        "text_color": "text-indigo-900",
        "badge_color": "bg-indigo-100 text-indigo-800",
        "heading": "Data Engineering & Infrastructure",
        "description": "Data pipelines, orchestration, quality engineering, streaming, storage, and analytics infrastructure.",
    },
}

# Derive simple dicts from PILLAR_CONFIG to eliminate duplication
PILLAR_NAMES = {k: v["label"] for k, v in PILLAR_CONFIG.items()}
PILLAR_EMOJIS = {k: v["emoji"] for k, v in PILLAR_CONFIG.items()}

# Pillar brand colors (used by build.py and core/visuals.py)
PILLAR_COLORS: dict[str, dict[str, str]] = {
    "aml": {
        "bg": "#020617",
        "fg": "#0f172a",
        "text": "#f8fafc",
        "accent": "#d97706",
    },
    "stock": {
        "bg": "#022c22",
        "fg": "#052e16",
        "text": "#f0fdf4",
        "accent": "#22c55e",
    },
    "data-engineering": {
        "bg": "#0f0a3a",
        "fg": "#1e1b4b",
        "text": "#eef2ff",
        "accent": "#818cf8",
    },
}

# Fingerprint colors used for per-article visual identity
PILLAR_FINGERPRINT_COLORS: dict[str, str] = {
    "aml": "#c97d3e",
    "stock": "#3a7d5c",
    "data-engineering": "#6366f1",
    "": "#6b7280",
}
