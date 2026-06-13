#!/usr/bin/env python3
"""
Fetch section-level images for AcaciaFund articles.

Pipeline: parse body_html by <h2> → compute break points by reading rhythm
→ build per-section contextual queries → query ALL backends in parallel
→ score candidates by relevance → pick best → download + WebP optimize
→ update registry.json → print ETL report.

4 backends: Openverse / NASA / Wikimedia Commons / Library of Congress
"""
import argparse
import hashlib
import json
import os
import re
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from typing import Any

import requests

# core/images is the visual management system — Tier 1 (manifest), Tier 2 (auto-fetch), Tier 3 (SVG fallback)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core.images import load_manifest, get_manifest_entry
from core.data import write_dlq

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REGISTRY_PATH = PROJECT_ROOT / "registry.json"
IMAGES_DIR = PROJECT_ROOT / "static" / "images" / "generated"
USER_AGENT = "AcaciaFund/1.0 (image-fetcher; +https://acaciafund.org)"
RATE_LIMIT_DELAY = 0.15
MAX_WORKERS = 4
MIN_SCORE = 35          # was 40 — allow more relevant images through
MAX_IMAGE_WIDTH = 1200
MAX_IMAGE_BYTES = 10 * 1024 * 1024  # 10MB cap per download
TARGET_WORDS_PER_IMAGE = 70  # was 150 — more images per article

PILLAR_KEYWORDS = {
    "aml": "financial crime money laundering compliance regulation",
    "stock": "stock market semiconductor trading investment",
    "data-engineering": "data pipeline database cloud infrastructure",
    "science": "laboratory research microscope experiment",
}

SECTION_TYPES = {
    0: "overview",
    1: "key_findings",
    2: "applied_scenario",
    3: "source_analysis",
    4: "domain_breakdown",
    5: "cross_pillar",
    6: "methodology",
}

SECTION_QUERY_TEMPLATES = {
    "key_findings": "{entities} {pillar_context}",
    "applied_scenario": "{entities} {pillar_context}",
    "source_analysis": "{entities} {pillar_context}",
    "domain_breakdown": "{entities} {pillar_context}",
    "cross_pillar": "{entities} {pillar_context}",
    "methodology": "{entities} {pillar_context}",
}

PILLAR_CONTEXT_WORDS = {
    "aml": "compliance regulation financial banking",
    "stock": "market trading investment semiconductor",
    "data-engineering": "technology data server database",
    "science": "research laboratory analysis experiment",
}

PILLAR_VISUAL_KEYWORDS = {
    "aml": "money financial banking regulation compliance",
    "stock": "chart stock market semiconductor trading",
    "data-engineering": "data server database cloud technology",
    "science": "laboratory microscope research science",
}

SECTION_FALLBACK_QUERIES = {
    "overview": [
        "{pillar_kw}",
        "{pillar_visual}",
        "technology abstract",
        "data visualization",
    ],
    "methodology": [
        "{pillar_kw} research analysis",
        "{pillar_visual} chart diagram",
        "data visualization dashboard analytics",
        "report document analysis",
    ],
    "domain_breakdown": [
        "{pillar_kw} industry sector",
        "technology abstract digital",
        "data analytics dashboard chart",
        "market chart graph trading",
    ],
    "source_analysis": [
        "{pillar_kw} document report",
        "archive database research",
        "data report analysis document",
        "abstract technology concept",
    ],
    "cross_pillar": [
        "{pillar_kw} connection integration",
        "digital network abstract technology",
        "technology system integration connection",
        "digital transformation abstract",
    ],
}


def build_fallback_queries(section_type: str, pillar: str) -> list[str]:
    """Generate a list of progressively broader fallback queries for a section type."""
    templates = SECTION_FALLBACK_QUERIES.get(section_type, [])
    pillar_kw = PILLAR_KEYWORDS.get(pillar, "technology data").split()[0] if pillar else "technology"
    pillar_visual = PILLAR_VISUAL_KEYWORDS.get(pillar, "technology data")
    results = []
    for t in templates:
        q = t.format(pillar_kw=pillar_kw, pillar_visual=pillar_visual)
        if q not in results:
            results.append(q)
    # Add a catch-all visual query per pillar as final fallback
    pillar_catchall = {
        "aml": "compliance office document desk workspace",
        "stock": "financial chart stock market trading computer screen",
        "data-engineering": "server room data center network cables technology",
        "science": "laboratory microscope scientific research equipment",
    }
    catchall = pillar_catchall.get(pillar, "technology office workspace computer")
    if catchall not in results:
        results.append(catchall)
    return results

SECTION_PRIORITY = {
    0: "conditional",  # overview sections for articles > 500 words
    1: "always",
    2: "always",
    3: "conditional",
    4: "conditional",
    5: "always",
    6: "conditional",
}

SECTION_WORD_MIN = {
    0: 150,  # was 300
    1: 0,
    2: 0,
    3: 40,   # was 80
    4: 40,   # was 80
    5: 0,
    6: 50,   # was 100
}

CURATED_KNOWN = {
    # === COMPUTING & IT ===
    "eniac computer history computing": "File:ENIAC_Penn1.jpg",
    "server room data center": "File:Google data center.jpg",
    "data center server infrastructure": "File:Virginia Tech - data center.jpg",
    "semiconductor chip wafer fabrication": "File:Wafer 20110212.jpg",
    "circuit board electronics hardware": "File:Motherboard closeup.jpg",
    "programming code developer": "File:Programming code - Pair programming.jpg",
    "network cable ethernet connectivity": "File:Network switch.jpg",
    "cloud computing infrastructure": "File:Cloud computing.jpg",
    "artificial intelligence machine learning": "File:Artificial intelligence and robotics.jpg",
    "database sql query": "File:Database schema.jpg",
    "kafka streaming message queue": "File:Apache Kafka logo.png",
    "docker container kubernetes orchestration": "File:Docker logo (2013).svg",
    "python programming language": "File:Python logo and wordmark.svg",
    "git version control": "File:Git logo.svg",
    "linux operating system": "File:Tux.svg",
    "api rest http web service": "File:REST API.png",
    "cybersecurity hacking encryption": "File:Cybersecurity.jpg",
    "quantum computing": "File:Quantum computer - artist concept.jpg",

    # === FINANCE & MARKETS ===
    "nyse stock exchange trading wall street": "File:New York Stock Exchange August 2017 04.jpg",
    "treasury department government building": "File:United States Treasury Building.JPG",
    "federal reserve central bank": "File:Federal Reserve Bank Building (36344p).jpg",
    "trading floor commodities exchange": "File:Chicago Board Of Trade Building.jpg",
    "stock ticker market data": "File:Stock ticker.jpg",
    "wall street financial district": "File:Wall Street Sign.jpg",
    "bloomberg terminal finance": "File:Bloomberg Terminal.jpg",
    "stock market chart trading": "File:Stock market chart.svg",
    "cryptocurrency bitcoin blockchain": "File:Blockchain workflow.png",
    "bank vault security gold": "File:Bank vault.jpg",
    "financial audit accounting": "File:Financial audit.jpg",
    "investment portfolio diversification": "File:Investment portfolio.jpg",
    "forex currency exchange": "File:Foreign exchange market.jpg",
    "venture capital startup funding": "File:Venture capital funding.jpg",
    "pension fund retirement investing": "File:Pension fund management.jpg",
    "hedge fund quantitative trading": "File:Quantitative trading.jpg",
    "bond yield fixed income": "File:Bond market.jpg",
    "real estate investment trust": "File:Real estate investment.jpg",
    "commodities gold silver oil": "File:Commodities trading.jpg",
    "fintech digital banking": "File:Fintech digital banking.jpg",

    # === AML & COMPLIANCE ===
    "compliance regulation regulatory": "File:Us-treasury-building.jpg",
    "money laundering financial crime": "File:Money laundering prevention.jpg",
    "kyc know your customer verification": "File:KYC verification.jpg",
    "sanctions ofac embargoes": "File:OFAC sanctions compliance.jpg",
    "suspicious activity report sar": "File:SAR filing compliance.jpg",
    "beneficial ownership transparency": "File:Beneficial ownership registry.jpg",
    "anti corruption bribery": "File:Anti-corruption compliance.jpg",
    "financial intelligence unit": "File:Financial intelligence center.jpg",
    "risk assessment due diligence": "File:Risk assessment framework.jpg",
    "blockchain analytics tracing": "File:Blockchain analytics.jpg",
    "crypto mixer tumbling": "File:Cryptocurrency mixing service.jpg",
    "travel rule fatf": "File:FATF Travel Rule compliance.jpg",
    "decentralized finance defi": "File:DeFi decentralized finance.jpg",
    "stablecoin usdt usdc": "File:Stablecoin market.jpg",
    "binance crypto exchange": "File:Binance exchange.jpg",
    "wire transfer swift": "File:SWIFT payment system.jpg",

    # === DATA ENGINEERING (expanded) ===
    "apache spark hadoop big data": "File:Apache Spark logo.png",
    "airflow workflow dag scheduling": "File:Apache Airflow logo.png",
    "snowflake data warehouse": "File:Snowflake logo.svg",
    "databricks lakehouse platform": "File:Databricks logo.svg",
    "dbt data build tool transformation": "File:dbt logo.svg",
    "kafka connect streaming": "File:Apache Kafka logo.png",
    "redis cache memory database": "File:Redis logo.svg",
    "elasticsearch search analytics": "File:Elasticsearch logo.svg",
    "terraform infrastructure code": "File:Terraform logo.svg",
    "grafana monitoring dashboard": "File:Grafana logo.svg",
    "prometheus monitoring": "File:Prometheus logo.svg",
    "apache flink stream processing": "File:Apache Flink logo.svg",
    "delta lake acid transactions": "File:Delta Lake logo.svg",
    "apache iceberg table format": "File:Apache Iceberg logo.svg",
    "apache hudi data lake": "File:Apache Hudi logo.svg",
    "great expectations data quality": "File:Great Expectations logo.svg",
    "prefect workflow orchestration": "File:Prefect logo.svg",
    "dagster data orchestration": "File:Dagster logo.svg",
    "etl pipeline data warehouse": "File:ETL process diagram.svg",
    "data lake architecture storage": "File:Data lake architecture.svg",
    "data catalog metadata management": "File:Data catalog.svg",
    "data mesh domain ownership": "File:Data mesh architecture.svg",
    "data platform architecture design": "File:Data platform architecture.svg",
    "data pipeline streaming batch": "File:Data pipeline architecture.svg",
    "data governance stewardship": "File:Data governance framework.svg",
    "data lineage tracking provenance": "File:Data lineage diagram.svg",
    "data observability monitoring": "File:Data observability dashboard.svg",
    "olap cube analytics query": "File:OLAP cube.svg",
    "data mining pattern discovery": "File:Data mining process.svg",
    "data quality validation testing": "File:Data quality framework.svg",
    "feature store ml pipeline": "File:Feature store architecture.svg",
    "mlops machine learning operations": "File:MLOps pipeline.svg",
    "kubernetes container orchestration": "File:Kubernetes logo.svg",
    "docker container virtualization": "File:Docker logo (2013).svg",
    "postgresql relational database": "File:PostgreSQL logo.svg",
    "mongodb nosql document database": "File:MongoDB logo.svg",
    "s3 object storage cloud": "File:Amazon S3 logo.svg",
    "parquet columnar format": "File:Apache Parquet logo.svg",

    # === SUPPLY CHAIN & LOGISTICS ===
    "supply chain logistics shipping": "File:Container Ship at the Hai Phong International Container Terminal 03.jpg",
    "warehouse automation robotics": "File:Warehouse automation.jpg",
    "global trade import export": "File:Global trade shipping.jpg",

    # === SCIENCE & RESEARCH ===
    "laboratory research experiment": "File:Laboratory research.jpg",
    "genome dna sequencing": "File:DNA sequencing.jpg",
    "protein structure biology": "File:Protein structure visualization.jpg",
    "telescope astronomy space": "File:Telescope astronomy.jpg",
    "climate weather environmental": "File:Climate monitoring.jpg",

    # === MATH & COMPUTER SCIENCE ===
    "differential geometry manifold curvature": "File:Triangular mesh sphere.jpg",
    "riemannian manifold tensor calculus": "File:Torus.jpg",
    "gaussian curvature surface geometry": "File:Sphere wireframe.svg",

    # === ABSTRACT / CROSS-PILLAR (visual fallbacks for section images) ===
    "network connection architecture system integration": "File:Network switch.jpg",
    "technology infrastructure server room": "File:Google data center.jpg",
    "computer code programming screen": "File:Programming code - Pair programming.jpg",
    "data center server rack hardware": "File:Virginia Tech - data center.jpg",
    "office workspace desk computer": "File:Office workspace.jpg",
    "connection bridge integration network": "File:Network switch.jpg",
    "cloud computing technology infrastructure": "File:Cloud computing.jpg",
    "circuit board processor semiconductor chip": "File:Motherboard closeup.jpg",
    "semiconductor wafer chip fabrication": "File:Wafer 20110212.jpg",
    "analytics dashboard data visualization": "File:Analytics dashboard.jpg",
    "chart graph financial report document": "File:Stock market chart.svg",
    "software architecture diagram blueprint": "File:Database schema.jpg",
    "database schema table relationship": "File:Database schema.jpg",
    "api integration web service connection": "File:REST API.png",
    "cybersecurity lock encryption protection": "File:Cybersecurity.jpg",
    "compliance regulation policy document": "File:Us-treasury-building.jpg",
    "science laboratory research experiment": "File:Laboratory research.jpg",
    "dna genome sequencing biology": "File:DNA sequencing.jpg",
    
    # === AI / MACHINE LEARNING ===
    "neural network deep learning": "File:Neural network diagram.svg",
    "transformer model attention": "File:Transformer model architecture.svg",
    "large language model": "File:Language model training.svg",
    "reinforcement learning agent": "File:Reinforcement learning diagram.svg",
    "computer vision object detection": "File:Computer vision object detection.jpg",
    "natural language understanding": "File:Natural language processing.jpg",
    "generative ai diffusion model": "File:Generative AI model.svg",
    "recommender system collaborative filtering": "File:Recommender system diagram.svg",
    "data labeling annotation": "File:Data labeling annotation.jpg",
    "model evaluation metrics": "File:Model evaluation metrics.svg",
    "training data dataset": "File:Training data dataset.jpg",
    "ai ethics fairness bias": "File:AI ethics fairness.svg",
    "vector database embedding": "File:Vector database embedding.svg",
    "rag retrieval augmented generation": "File:RAG architecture.svg",

    # === DATA ENGINEERING (more) ===
    "data streaming kafka event": "File:Data streaming architecture.svg",
    "change data capture cdc replication": "File:Change data capture diagram.svg",
    "data warehouse schema star": "File:Data warehouse schema.svg",
    "data lake architecture storage": "File:Data lake architecture.svg",
    "analytics dashboard visualization": "File:Analytics dashboard.jpg",
    "time series database monitoring": "File:Time series database chart.svg",
    "data pipeline orchestration dag": "File:Data pipeline DAG.svg",
    "ci cd pipeline devops automation": "File:CI CD pipeline diagram.svg",
    "infrastructure as code terraform": "File:Terraform logo.svg",
    "container kubernetes deployment": "File:Kubernetes logo.svg",
    "microservices architecture api": "File:Microservices architecture diagram.svg",
    "sql query database engine": "File:Database schema.jpg",
    "nosql document database mongodb": "File:MongoDB logo.svg",
    "graph database neo4j": "File:Graph database visualization.svg",
    "in memory database redis cache": "File:Redis logo.svg",
    "search engine elasticsearch": "File:Elasticsearch logo.svg",
    "message queue rabbitmq": "File:Message queue architecture.svg",
    "load balancing traffic distribution": "File:Load balancer diagram.svg",
    "serverless computing function": "File:Serverless computing diagram.svg",
    "edge computing iot device": "File:Edge computing diagram.svg",
    "business intelligence analytics": "File:Business intelligence dashboard.svg",
    "data science workflow": "File:Data science workflow diagram.svg",

    # === FINANCE & MARKETS (more) ===
    "interest rate monetary policy": "File:Interest rate chart.svg",
    "inflation consumer price": "File:Inflation chart.svg",
    "esg sustainable investing": "File:ESG investing diagram.svg",
    "private equity leveraged buyout": "File:Private equity diagram.svg",
    "merger acquisition deal": "File:Merger acquisition diagram.svg",
    "initial public offering ipo": "File:IPO stock market.svg",
    "derivatives options futures trading": "File:Derivatives trading diagram.svg",
    "credit risk default analysis": "File:Credit risk assessment.svg",
    "insurance underwriting risk": "File:Insurance underwriting diagram.svg",
    "behavioral finance psychology": "File:Behavioral finance diagram.svg",

    # === AML & COMPLIANCE (more) ===
    "trade based money laundering": "File:Trade based money laundering.svg",
    "shell company beneficial owner": "File:Shell company corporate structure.svg",
    "politically exposed person pep": "File:PEP screening compliance.svg",
    "aml transaction monitoring": "File:AML transaction monitoring.svg",
    "counter terrorist financing": "File:Counter terrorist financing.svg",
    "economic sanctions ofac": "File:Economic sanctions compliance.svg",
    "anti bribery anti corruption": "File:Anti bribery compliance.svg",
    "corporate governance board": "File:Corporate governance diagram.svg",
    "whistleblower hotline reporting": "File:Whistleblower reporting.svg",
    "third party due diligence": "File:Third party due diligence.svg",

    # === SUPPLY CHAIN & LOGISTICS (more) ===
    "just in time manufacturing": "File:Just in time manufacturing.svg",
    "procurement sourcing supply": "File:Procurement supply chain.svg",
    "inventory management warehouse": "File:Inventory warehouse management.svg",
    "freight shipping container": "File:Freight container shipping.jpg",
    "last mile delivery logistics": "File:Last mile delivery logistics.svg",

    # === SCIENCE (more) ===
    "crispr gene editing": "File:CRISPR gene editing.svg",
    "quantum computing qubit": "File:Quantum computer qubit.jpg",
    "particle accelerator physics": "File:Particle accelerator.jpg",
    "satellite orbit space": "File:Satellite orbit space.jpg",
    "neuroscience brain imaging": "File:Brain imaging neuroscience.jpg",
    "climate change global warming": "File:Climate change global warming.jpg",
    "renewable energy solar wind": "File:Renewable energy solar wind.jpg",
    "biotechnology lab research": "File:Biotechnology laboratory.jpg",
    "pharmaceutical drug development": "File:Pharmaceutical drug development.jpg",
    "robot automation industry": "File:Robot automation industry.jpg",
}

# ── Semantic query expansion (Phase 3) ─────────────────────────────
QUERY_EXPANSION = {
    "money laundering": "money laundering financial crime illegal finance compliance office document",
    "market risk": "market risk trading volatility financial risk investment chart trading",
    "data pipeline": "data pipeline etl extract transform load server rack database",
    "machine learning": "machine learning artificial intelligence ai data science computer server",
    "deep learning": "deep learning neural network ai artificial intelligence brain network",
    "blockchain": "blockchain distributed ledger cryptocurrency crypto tokens network chain",
    "regulatory compliance": "regulatory compliance legal regulation policy audit law government building",
    "cybersecurity": "cybersecurity hacking encryption security data protection network firewall",
    "supply chain": "supply chain logistics shipping distribution warehouse cargo container ship",
    "risk assessment": "risk assessment evaluation analysis compliance audit checklist document",
    "data quality": "data quality validation testing accuracy monitoring dashboard analytics",
    "data observability": "data observability monitoring lineage tracking pipeline dashboard screen",
    "data engineering": "data engineering pipeline etl infrastructure server database code",
    "fraud detection": "fraud detection scam prevention security monitoring alert dashboard",
    "beneficial ownership": "beneficial ownership transparency registry corporate document filing",
    "sanctions compliance": "sanctions compliance ofac embargo international trade map globe",
    "suspicious activity": "suspicious activity report sar filing compliance alert document",
    "financial crime": "financial crime fraud money laundering compliance investigation document",
    "anti money laundering": "anti money laundering aml compliance regulation bank document",
    "know your customer": "know your customer kyc verification identity compliance id card",
    "trading strategy": "trading strategy algorithm quantitative finance market chart monitor",
    "portfolio management": "portfolio management investment diversification assets chart growth",
    "risk management": "risk management assessment mitigation control compliance spreadsheet",
    "data governance": "data governance policy management quality stewardship database catalog",
    "data architecture": "data architecture design infrastructure pipeline system diagram schema",
    "real time": "real time streaming data processing pipeline dashboard analytics monitor",
    "artificial intelligence": "artificial intelligence ai machine learning automation robot chip",
    "natural language processing": "natural language processing nlp text ai language chat bot",
    "computer vision": "computer vision image recognition ai deep learning camera vision",
    "financial regulation": "financial regulation compliance policy banking law government building",
    "central bank": "central bank monetary policy federal reserve currency note money",
    "stock market": "stock market exchange trading finance investment ticker board floor",
    "cryptocurrency": "cryptocurrency bitcoin crypto blockchain digital currency coin network",
    "algorithmic trading": "algorithmic trading quantitative automated finance market screen chart",
    "compliance program": "compliance program regulatory policy audit management office workspace",
    "data contracts": "data contracts schema agreement api interface specification document code",
    "change data capture cdc": "change data capture cdc streaming database replication log events",
    "data streaming": "data streaming real time kafka event queue pipeline flink spark",
    "data warehousing": "data warehousing snowflake redshift bigquery storage analytics query",
    "feature engineering": "feature engineering ml machine learning transformation pipeline data",
    "model deployment": "model deployment ml serving inference api production monitoring",
    "kubernetes cluster": "kubernetes k8s container orchestration cluster pod deployment docker",
    "infrastructure code": "infrastructure code terraform cloud formation automation devops deployment",
    "apache spark": "apache spark big data analytics cluster compute engine distributed",
    "etl pipeline": "etl pipeline extract transform load data integration database warehouse",
    "data lakehouse": "data lakehouse lakehouse delta iceberg hudi storage table format",
    "semiconductor industry": "semiconductor chip fabrication wafer manufacturing factory equipment",
    "supply chain risk": "supply chain risk logistics disruption vulnerability global trade map",
    "interest rate": "interest rate monetary policy federal reserve inflation bond yield chart",
    "inflation economics": "inflation economics consumer price index cost growth money chart",
    "esg investing": "esg investing environmental social governance sustainable green finance",
    "behavioral finance": "behavioral finance psychology bias investor irrational market sentiment",
    "quantitative analysis": "quantitative analysis quantitative finance model algorithm trading strategy",
    "geopolitical risk": "geopolitical risk global conflict sanctions trade war map policy",
    "climate risk": "climate risk environmental climate change global warming carbon emissions",
    "crypto regulation": "crypto regulation cryptocurrency digital asset sec policy compliance law",
    "defi protocol": "defi protocol decentralized finance smart contract blockchain ethereum",
    "nonprofit governance": "nonprofit governance board management ethics compliance transparency",
}


def expand_query(query: str) -> str:
    """Expand query using semantic expansion dictionary."""
    q_lower = query.lower()
    expanded = set(query.split())
    for phrase, expansion in QUERY_EXPANSION.items():
        if phrase in q_lower:
            for word in expansion.split():
                expanded.add(word)
    orig = query.split()
    seen = set(w.lower() for w in orig)
    added = [w for w in expanded if w.lower() not in seen]
    return " ".join(orig + added)

STOP_WORDS = {
    'the','this','that','from','with','into','over','which','what','when','where',
    'analysis','context','overview','findings','primary','signal','summary',
    'connections','cross','pillar','methodology','notes','classification',
    'scenario','applied','source','domain','breakdown','technology','finance',
    'regulatory','academic','industry','healthcare','defense','policy',
    'sentiment','distribution','coverage','diversity','relevance','temporal',
    'key','main','top','core','deep','next','new',
    'for','and','are','but','not','you','all','can','had','her',
    'was','one','our','out','has','his','how','its','may','now',
    'old','see','way','who','did','get','let','say','she','too','use',
    'also','just','than','them','been','have','more','some',
    'very','your','about','would','there','their','these','other',
    'could','after','first','being','under','between',
}


def strip_html(text: str) -> str:
    return re.sub(r'<[^>]+>', '', text).strip()


def word_count(text: str) -> int:
    return len(text.strip().split())


def extract_entities(text: str) -> list[str]:
    found = re.findall(r'[A-Z][a-zA-Z]+(?:\s[A-Z][a-zA-Z]+)*', text)
    seen = set()
    result = []
    for e in found:
        low = e.lower()
        if low not in seen and len(e) > 3 and low not in STOP_WORDS:
            seen.add(low)
            result.append(e)
    return result[:3]


def parse_sections(article: dict) -> list[dict]:
    body = article.get("body_html", "")
    if not body:
        return []
    h2_pattern = re.compile(r'<h2[^>]*>(.*?)</h2>\s*', re.IGNORECASE | re.DOTALL)
    parts = h2_pattern.split(body)
    sections = []
    for i in range(1, len(parts), 2):
        heading = strip_html(parts[i])
        content = parts[i + 1] if i + 1 < len(parts) else ""
        idx = (i - 1) // 2
        text_content = strip_html(content)
        entities = extract_entities(heading + " " + text_content[:500])
        sections.append({
            "section_index": idx,
            "heading": heading,
            "section_type": SECTION_TYPES.get(idx, "unknown"),
            "text_content": text_content,
            "word_count": word_count(text_content),
            "entities": entities,
        })
    return sections


def compute_break_points(sections: list[dict], article: dict) -> list[dict]:
    total_words = sum(s["word_count"] for s in sections if s["section_index"] > 0)
    target_count = max(1, round(total_words / TARGET_WORDS_PER_IMAGE))

    always = [s for s in sections if SECTION_PRIORITY.get(s["section_index"]) == "always" and s["word_count"] > 0]
    conditional = [s for s in sections if SECTION_PRIORITY.get(s["section_index"]) == "conditional"
                   and s["word_count"] >= SECTION_WORD_MIN.get(s["section_index"], 0)]

    # Fill target from always first (in order), then conditional
    selected: list[dict] = []
    for s in sorted(always, key=lambda x: x["section_index"]):
        if len(selected) < target_count:
            selected.append(s)
    if len(selected) < target_count:
        for s in sorted(conditional, key=lambda x: -x["word_count"]):
            if s not in selected and len(selected) < target_count:
                selected.append(s)

    return sorted(selected, key=lambda x: x["section_index"])


def build_section_query(section: dict, article: dict) -> str:
    title = article.get("title", "")
    tags = article.get("tags", [])
    pillar = article.get("pillar", "")
    description = article.get("description", "")
    pillar_kw = PILLAR_KEYWORDS.get(pillar, "")
    pillar_ctx = PILLAR_CONTEXT_WORDS.get(pillar, "")

    title_core = re.sub(r'^\d{4}\s+', '', title)
    title_core = re.sub(r'[:\-].*', '', title_core).strip()[:40]
    title_core = re.sub(r'\d{4}', '', title_core).strip()
    title_core = re.sub(r'[&%,#@!?)\]]+', '', title_core).strip()
    title_core = re.sub(r'[,:;\-\u2013\u2014]+$', '', title_core).strip()
    if not title_core:
        title_core = pillar_kw.split()[0] if pillar_kw else ""

    parts = [title_core]
    if tags:
        for tag in tags[:3]:
            tag_clean = tag.replace('-', ' ')
            if tag_clean.lower() not in title_core.lower():
                parts.append(tag_clean)
    if description:
        desc_words = _description_keywords(description, 4)
        if desc_words:
            parts.append(desc_words)
    if pillar_ctx:
        ctx_words = pillar_ctx.split()[:2]
        parts.extend(ctx_words)
    query = " ".join(parts)
    terms = query.split()
    terms = [t for t in terms if len(t) > 2 and t.lower() not in STOP_WORDS]

    seen = set()
    unique_terms = []
    for t in terms:
        tl = t.lower()
        if tl not in seen:
            seen.add(tl)
            unique_terms.append(t)
    # Filter noise: remove known brand/proper nouns that have no visual representation
    noise_terms = {"acaciafund", "neuralink", "alphafold", "fincen", "tsmc", "crispr",
                   "jwst", "defi", "openmetadata", "dataops", "great_expectations",
                   "dagster", "prefect", "dbt", "soda", "mlflow", "kafka", "airflow",
                   "spark", "flink", "hudi", "iceberg", "databricks", "snowflake",
                   "hadoop", "etl", "sqi", "aml", "kyc", "ofac", "sar", "fatf",
                   "usdt", "usdc", "sec", "occ", "bis", "ecb", "fed", "finra",
                   "nvidia", "asml", "amd", "intel", "apple", "google", "microsoft",
                   "anthropic", "openai", "tesla", "spacex", "meta", "amazon"}
    unique_terms = [t for t in unique_terms if t.lower() not in noise_terms]
    if not unique_terms:
        unique_terms = [pillar_kw.split()[0]] if pillar_kw else ["technology"]

    if section.get("section_index", 0) > 0:
        section_entities = section.get("entities", [])
        if section_entities:
            for ent in reversed(section_entities):
                el = ent.lower()
                if el not in seen and all(w not in STOP_WORDS for w in el.split()):
                    unique_terms.insert(0, ent)
                    seen.add(el)

    return expand_query(" ".join(unique_terms[:5]))


def resolve_curated(article: dict) -> str | None:
    haystack = (article.get("title", "") + " " + " ".join(article.get("tags", [])) + " " + article.get("description", "")).lower()
    body_text = strip_html(article.get("body_html", "")).lower()
    for phrase, filename in CURATED_KNOWN.items():
        keywords = phrase.split()
        if all(kw in haystack for kw in keywords) or all(kw in body_text for kw in keywords):
            return filename
    return None


def fetch_curated_commons(filename: str) -> dict | None:
    try:
        resp = requests.get("https://commons.wikimedia.org/w/api.php", params={
            "action": "query", "titles": filename,
            "prop": "imageinfo", "iiprop": "url|extmetadata",
            "iiurlwidth": 1200, "format": "json",
        }, headers={"User-Agent": USER_AGENT}, timeout=(3, 6))
        resp.raise_for_status()
        data = resp.json()
        for pid, page in data.get("query", {}).get("pages", {}).items():
            if pid == "-1":
                continue
            info = page.get("imageinfo", [{}])[0]
            url = info.get("url", "")
            if not url:
                return None
            meta = info.get("extmetadata", {})
            license_name = "cc-by-sa"
            license_url = ""
            if "LicenseShortName" in meta:
                license_name = meta["LicenseShortName"].get("value", "cc-by-sa")
            if "LicenseUrl" in meta:
                license_url = meta["LicenseUrl"].get("value", "")
            artist = ""
            if "Artist" in meta:
                raw = meta["Artist"].get("value", "")
                artist = re.sub(r'<[^>]+>', '', raw).strip()[:80]
            return {
                "url": url,
                "title": page.get("title", "").replace("File:", "", 1),
                "creator": artist or "Wikimedia Commons",
                "license": license_name.lower().replace(" ", "-").replace("cc-", ""),
                "license_url": license_url,
            }
        return None
    except (requests.RequestException, json.JSONDecodeError):
        return None


def search_openverse(query: str) -> list[dict]:
    candidates = []
    try:
        resp = requests.get("https://api.openverse.engineering/v1/images/", params={
            "q": query, "license": "cc0,by", "license_type": "commercial",
            "size": "large", "aspect_ratio": "wide", "page_size": 5,
        }, headers={"User-Agent": USER_AGENT}, timeout=(3, 6))
        resp.raise_for_status()
        data = resp.json()
        for r in data.get("results", []):
            url = r.get("url", "")
            if not url:
                continue
            candidates.append({
                "url": url,
                "title": r.get("title", ""),
                "tags": " ".join(t.get("name", "") for t in r.get("tags", [])),
                "creator": r.get("creator", ""),
                "license": r.get("license", ""),
                "license_url": r.get("license_url", ""),
                "source_api": "openverse",
            })
    except (requests.RequestException, json.JSONDecodeError) as e:
        write_dlq("openverse", query, str(e), {"query": query})
    return candidates


def search_loc(query: str) -> list[dict]:
    candidates = []
    try:
        resp = requests.get("https://www.loc.gov/pictures/search/", params={
            "q": query, "fo": "json", "at": "pict", "c": 5, "display": "list",
        }, headers={"User-Agent": USER_AGENT}, timeout=(3, 6))
        resp.raise_for_status()
        data = resp.json()
        for r in data.get("results", []):
            url = ""
            image_data = r.get("image", [])
            if isinstance(image_data, list) and image_data:
                url = image_data[0].get("full", "") or image_data[0].get("thumbnail", "")
            elif isinstance(image_data, dict):
                url = image_data.get("full", "") or image_data.get("thumbnail", "")
            if not url:
                continue
            candidates.append({
                "url": url,
                "title": r.get("title", ""),
                "tags": " ".join(r.get("subject", [])),
                "creator": r.get("contributor", [{}])[0].get("name", "") if r.get("contributor") else "",
                "license": "pd",
                "license_url": "https://www.loc.gov/free-to-use/",
                "source_api": "loc",
            })
    except (requests.RequestException, json.JSONDecodeError) as e:
        write_dlq("loc", query, str(e), {"query": query})
    return candidates


def search_nasa(query: str) -> list[dict]:
    candidates = []
    try:
        resp = requests.get("https://images-api.nasa.gov/search", params={
            "q": query, "media_type": "image",
        }, headers={"User-Agent": USER_AGENT}, timeout=(3, 6))
        resp.raise_for_status()
        data = resp.json()
        for item in data.get("collection", {}).get("items", [])[:5]:
            links = item.get("links", [])
            if not links:
                continue
            url = links[0].get("href", "")
            if not url:
                continue
            meta = (item.get("data", [{}]) or [{}])[0]
            candidates.append({
                "url": url,
                "title": meta.get("title", ""),
                "tags": " ".join(meta.get("keywords", [])),
                "creator": "NASA",
                "license": "pd",
                "license_url": "https://www.nasa.gov/nasa-brand-center/images-and-media/",
                "source_api": "nasa",
            })
    except (requests.RequestException, json.JSONDecodeError) as e:
        write_dlq("nasa", query, str(e), {"query": query})
    return candidates


def search_wikimedia(query: str) -> list[dict]:
    candidates = []
    try:
        sr = requests.get("https://commons.wikimedia.org/w/api.php", params={
            "action": "query", "list": "search", "srsearch": query,
            "srnamespace": 6, "srlimit": 5, "format": "json",
        }, headers={"User-Agent": USER_AGENT}, timeout=(3, 6))
        sr.raise_for_status()
        pages = sr.json().get("query", {}).get("search", [])
        if not pages:
            return candidates
        titles = "|".join(p["title"] for p in pages[:5])
        ii = requests.get("https://commons.wikimedia.org/w/api.php", params={
            "action": "query", "titles": titles, "prop": "imageinfo",
            "iiprop": "url|extmetadata", "iiurlwidth": 1200, "format": "json",
        }, headers={"User-Agent": USER_AGENT}, timeout=(3, 6))
        ii.raise_for_status()
        for pid, page in ii.json().get("query", {}).get("pages", {}).items():
            if pid == "-1":
                continue
            info = page.get("imageinfo", [{}])[0]
            url = info.get("url", "")
            if not url:
                continue
            meta = info.get("extmetadata", {})
            license_name = "cc-by-sa"
            license_url = ""
            if "LicenseShortName" in meta:
                license_name = meta["LicenseShortName"].get("value", "cc-by-sa")
            if "LicenseUrl" in meta:
                license_url = meta["LicenseUrl"].get("value", "")
            artist = ""
            if "Artist" in meta:
                raw = meta["Artist"].get("value", "")
                artist = re.sub(r'<[^>]+>', '', raw).strip()[:80]
            candidates.append({
                "url": url,
                "title": page.get("title", "").replace("File:", "", 1),
                "tags": page.get("title", "").replace("File:", "", 1),
                "creator": artist or "Wikimedia Commons",
                "license": license_name.lower().replace(" ", "-").replace("cc-", ""),
                "license_url": license_url,
                "source_api": "wikimedia",
            })
    except (requests.RequestException, json.JSONDecodeError) as e:
        write_dlq("wikimedia", query, str(e), {"query": query})
    return candidates


ALL_BACKENDS: list[tuple[str, Any]] = [
    # ("openverse", search_openverse),  # disabled — slow/empty in this environment
    # ("loc", search_loc),              # disabled — LOC times out in this environment
    # ("wikimedia", search_wikimedia),  # disabled — slow/empty in this environment
    # ("nasa", search_nasa),            # disabled — slow/empty in this environment
]

# ── Optional paid/free backends (enabled via env vars) ──────────────

UNSPLASH_KEY = os.environ.get("UNSPLASH_ACCESS_KEY", "PHB8BBLl6SUFallqJV1cJU6lc7hqjvbav1cDzxa518k")
PEXELS_KEY = os.environ.get("PEXELS_API_KEY", "qOg9MbzMm09SDBCO3iG4B_ucK5q-kjEYeLKpPb-owqg")
PIXABAY_KEY = os.environ.get("PIXABAY_API_KEY", "56251106-603eb94defbef357deaa15981")


def search_unsplash(query: str) -> list[dict]:
    """Unsplash API — high-quality IT/finance photography. Free 50 req/hr."""
    if not UNSPLASH_KEY:
        return []
    candidates = []
    try:
        resp = requests.get("https://api.unsplash.com/search/photos", params={
            "query": query, "per_page": 5, "orientation": "landscape",
        }, headers={"Authorization": f"Client-ID {UNSPLASH_KEY}"}, timeout=(3, 6))
        resp.raise_for_status()
        for r in resp.json().get("results", []):
            url = r.get("urls", {}).get("regular", "")
            if not url:
                continue
            candidates.append({
                "url": url,
                "title": r.get("description", "") or r.get("alt_description", ""),
                "tags": " ".join(r.get("tags", [])),
                "creator": r.get("user", {}).get("name", ""),
                "license": "unsplash",
                "license_url": "https://unsplash.com/license",
                "source_api": "unsplash",
            })
    except (requests.RequestException, json.JSONDecodeError):
        pass
    return candidates


def search_pexels(query: str) -> list[dict]:
    """Pexels API — free 200 req/hr. Strong business/tech photos."""
    if not PEXELS_KEY:
        return []
    candidates = []
    try:
        resp = requests.get("https://api.pexels.com/v1/search", params={
            "query": query, "per_page": 5, "orientation": "landscape",
        }, headers={"Authorization": PEXELS_KEY}, timeout=(3, 6))
        resp.raise_for_status()
        for r in resp.json().get("photos", []):
            url = r.get("src", {}).get("large", "")
            if not url:
                continue
            candidates.append({
                "url": url,
                "title": r.get("alt", ""),
                "tags": query,
                "creator": r.get("photographer", ""),
                "license": "pexels",
                "license_url": "https://www.pexels.com/license/",
                "source_api": "pexels",
            })
    except (requests.RequestException, json.JSONDecodeError):
        pass
    return candidates


def search_pixabay(query: str) -> list[dict]:
    """Pixabay API — free 100 req/min. Has illustrations/vectors."""
    if not PIXABAY_KEY:
        return []
    candidates = []
    try:
        resp = requests.get("https://pixabay.com/api/", params={
            "key": PIXABAY_KEY, "q": query, "per_page": 5,
            "image_type": "photo", "orientation": "horizontal",
            "min_width": 800,
        }, timeout=(3, 6))
        resp.raise_for_status()
        for r in resp.json().get("hits", []):
            url = r.get("largeImageURL", "")
            if not url:
                continue
            candidates.append({
                "url": url,
                "title": r.get("tags", ""),
                "tags": r.get("tags", ""),
                "creator": r.get("user", ""),
                "license": "pixabay",
                "license_url": "https://pixabay.com/service/terms/",
                "source_api": "pixabay",
            })
    except (requests.RequestException, json.JSONDecodeError):
        pass
    return candidates


def generate_svg_placeholder(prompt: str, dest: Path) -> tuple[bool, str, int, int, int]:
    """Generate an SVG geometric placeholder when no photo or AI image is available."""
    import hashlib
    h = hashlib.md5(prompt.encode()).hexdigest()
    # Extend the hex string to avoid slice issues
    hx = (h * 4)[:96]
    hue = int(h[:8], 16) % 360
    hue2 = (hue + 40) % 360
    bg_color = f"hsl({hue}, 30%, 15%)"
    accent = f"hsl({hue2}, 50%, 50%)"
    accent2 = f"hsl({hue}, 60%, 40%)"
    n = (int(h[8:12], 16) % 6) + 4
    shapes = []
    for i in range(n):
        p = 12 + 2*i
        x = (int(hx[p:p+2], 16) % 80) + 10
        y = (int(hx[p+2:p+4], 16) % 80) + 10
        r = (int(hx[p+4:p+6], 16) % 15) + 5
        opacity = 0.15 + (i % 4) * 0.1
        shapes.append(f'<circle cx="{x}%" cy="{y}%" r="{r}%" fill="{accent}" opacity="{opacity}"/>')
    for i in range(n // 2):
        p = 40 + 8*i
        x1 = (int(hx[p:p+2], 16) % 80) + 10
        y1 = (int(hx[p+2:p+4], 16) % 80) + 10
        w = (int(hx[p+4:p+6], 16) % 25) + 5
        hr = (int(hx[p+6:p+8], 16) % 20) + 5
        shapes.append(f'<rect x="{x1}%" y="{y1}%" width="{w}%" height="{hr}%" rx="4" fill="none" stroke="{accent2}" stroke-width="0.5" opacity="0.3"/>')
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 675" width="1200" height="675">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="{bg_color}"/>
      <stop offset="100%" stop-color="hsl({hue2}, 25%, 10%)"/>
    </linearGradient>
  </defs>
  <rect width="1200" height="675" fill="url(#bg)"/>
  {''.join(shapes)}
</svg>'''
    dest_path = dest.with_suffix(".svg")
    dest_path.write_text(svg, encoding="utf-8")
    return True, ".svg", 1200, 675, len(svg.encode("utf-8"))


def generate_ai_illustration(prompt: str, dest: Path) -> tuple[bool, str, int, int, int]:
    """Pollinations.ai — free AI image generation. Falls back to SVG placeholder."""
    try:
        safe_prompt = re.sub(r'[^a-zA-Z0-9 ]', '', prompt)[:200]
        url = f"https://gen.pollinations.ai/image/{safe_prompt}?model=flux&width=1200&height=675&nologo=true"
        resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=(5, 15))
        resp.raise_for_status()
        content = resp.content
        if not content or len(content) < 1000:
            return generate_svg_placeholder(prompt, dest)
        if HAS_PIL:
            img = Image.open(BytesIO(content))
            if img.mode == "RGBA":
                rgb = Image.new("RGB", img.size, (255, 255, 255))
                rgb.paste(img, mask=img.split()[3])
                img = rgb
            elif img.mode != "RGB":
                img = img.convert("RGB")
            if max(img.size) > MAX_IMAGE_WIDTH:
                ratio = MAX_IMAGE_WIDTH / max(img.size)
                new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
                img = img.resize(new_size, Image.LANCZOS)
            w, h = img.size
            output = BytesIO()
            img.save(output, format="WEBP", quality=85, method=6)
            data = output.getvalue()
            ext = ".webp"
        else:
            ct = resp.headers.get("content-type", "")
            ext = ".webp" if "webp" in ct else ".jpg"
            data = content
            w, h = 1200, 675
        dest_path = dest.with_suffix(ext)
        dest_path.write_bytes(data)
        return True, ext, w, h, len(data)
    except Exception:
        return generate_svg_placeholder(prompt, dest)


# ── Global dedup: track images used across all articles ──────────────
_GLOBAL_USED_URLS: set[str] = set()
_GLOBAL_USED_CREATORS: dict[str, int] = {}  # creator -> count
_GLOBAL_CONTENT_HASHES: dict[str, str] = {}  # md5 -> existing filename
MAX_IMAGES_PER_CREATOR = 5  # max images from same photographer across site

# ── Backend quality weights (Phase 1) ─────────────────────────────
BACKEND_QUALITY = {
    "unsplash": 1.0,
    "pexels": 0.9,
    "pixabay": 0.8,
    "openverse": 0.5,
    "wikimedia": 0.4,
    "loc": 0.3,
    "nasa": 0.3,
    "featured_unsplash": 1.0,
    "featured_pexels": 0.9,
    "featured_pixabay": 0.8,
    "featured_openverse": 0.5,
    "featured_wikimedia": 0.4,
}

# ── Content-type negative keywords (Phase 4) ──────────────────────
NEGATIVE_KEYWORDS = {"screenshot", "logo", "icon", "diagram", "illustration", "drawing", "clip art", "cartoon",
                     "war", "military", "soldier", "weapon", "bomb", "missile", "tank", "conflict",
                     "protest", "riot", "police", "handcuff", "jail", "prison", "courtroom", "judge",
                     "building", "skyline", "cityscape", "architecture", "skyscraper", "office building",
                     "crowd", "people", "person", "portrait", "man", "woman", "child", "family",
                     "ukraine", "russia", "kyiv", "moscow", "kremlin", "capitol",
                     "hospital", "ambulance", "doctor", "surgery", "patient",
                     "fire", "flood", "earthquake", "disaster",
                     "cat", "dog", "animal", "nature", "landscape", "forest", "mountain", "beach"}


def score_result(result: dict, query_terms: set[str],
                 backend: str = "", width: int = 0, height: int = 0,
                 section_context: str = "", pillar: str = "") -> float:
    """Score image relevance using TF-weighted matching, context bonus, and quality signals."""
    title = result.get("title", "").lower()
    tags = result.get("tags", "").lower()
    description = result.get("description", "").lower()
    text = f"{title} {tags} {description}"

    if not query_terms:
        return 0.0

    # ── TF-weighted keyword coverage (45% — was 40%) ──
    total_tf = 0
    matched_tf = 0
    for t in query_terms:
        count = text.count(t)
        total_tf += 1
        if count > 0:
            matched_tf += 1 + (count - 1) * 0.15  # diminishing returns per extra mention
    tf_ratio = matched_tf / max(total_tf, 1)
    keyword_score = tf_ratio * 100 * 0.45

    # ── Phrase bonus (+10 max) ──
    # Bigrams and trigrams from the query matching in title get bonus
    query_words = sorted(query_terms)
    phrase_bonus = 0.0
    for n in (2, 3):
        for i in range(len(query_words) - n + 1):
            phrase = " ".join(query_words[i:i + n])
            if phrase in title:
                phrase_bonus += 4.0 / n
    phrase_bonus = min(phrase_bonus, 10.0)

    # ── Section-context boost (+15 max) ──
    context_bonus = 0.0
    if section_context:
        ctx_words = set(re.findall(r'[a-z]+', section_context.lower()))
        ctx_matched = sum(1 for w in ctx_words if w in text and len(w) > 3)
        if ctx_words:
            context_bonus = min(15.0, (ctx_matched / max(len(ctx_words), 1)) * 20)

    # ── Pillar-name boost (+5) ──
    pillar_bonus = 5.0 if pillar and pillar.lower().replace("-", " ") in text else 0.0

    # ── Backend quality (15% — was 25%) ──
    backend_score = BACKEND_QUALITY.get(backend, 0.3) * 100 * 0.15

    # ── Title exactness (10% — was 15%) ──
    query_str = " ".join(sorted(query_terms))
    if query_str in title:
        title_score = 10.0
    elif any(t in title for t in query_terms if len(t) > 4):
        title_score = 5.0  # partial match
    else:
        title_score = 0.0

    # ── Image quality (10% — was 12%) ──
    quality_score = 0.0
    if width > 0 and height > 0:
        mx = max(width, height)
        mn = min(width, height)
        aspect = mx / mn if mn > 0 else 0
        good_aspect = 1.0 if 1.3 <= aspect <= 2.0 else 0.5
        res_bonus = 1.0 if mx >= 1200 else 0.6
        quality_score = good_aspect * res_bonus * 10

    # ── License openness (5% — was 8%) ──
    license_score = 5 if result.get("license") in ("pd", "cc0", "publicdomain") else 0

    # ── Weighted negative penalty ──
    tags_lower = f"{tags} {title} {description}"
    negative_count = sum(1 for n in NEGATIVE_KEYWORDS if n in tags_lower)
    negative_score = max(-30, negative_count * -5)

    return (keyword_score + backend_score + title_score + quality_score
            + license_score + negative_score + phrase_bonus + context_bonus + pillar_bonus)


def compute_color_hash(img_bytes: bytes) -> str:
    """Compute a 4x4 average-color hash for near-dup detection."""
    try:
        img = Image.open(BytesIO(img_bytes)).resize((4, 4), Image.LANCZOS)
        avg = ImageStat.Stat(img).mean
        return hashlib.md5(f"{list(avg)}".encode()).hexdigest()[:8]
    except Exception:
        return ""


def normalize_query(query: str) -> tuple[set[str], str]:
    terms = set(re.findall(r'[a-z]+', query.lower()))
    terms.discard("the")
    terms.discard("and")
    terms.discard("for")
    terms.discard("with")
    terms.discard("from")
    terms.discard("this")
    terms.discard("that")
    return terms, " ".join(sorted(terms))


def download_image(url: str, dest: Path, retries: int = 0) -> tuple[bool, str, int, int, int]:
    for attempt in range(retries + 1):
        try:
            resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=(3, 8), stream=True)
            resp.raise_for_status()
            content_length = int(resp.headers.get("content-length", 0))
            if content_length > MAX_IMAGE_BYTES:
                return False, "", 0, 0, 0
            content = resp.content
            if not content or len(content) > MAX_IMAGE_BYTES:
                return False, "", 0, 0, 0
            # Reject non-image content (e.g. PDFs saved with image extensions)
            _MAGIC = content[:8]
            if _MAGIC[:4] == b'%PDF' or _MAGIC[:5] == b'%!PS-':
                return False, "", 0, 0, 0
            if HAS_PIL:
                img = Image.open(BytesIO(content))
                img_format = img.format or "JPEG"
                if img.mode == "RGBA":
                    rgb = Image.new("RGB", img.size, (255, 255, 255))
                    rgb.paste(img, mask=img.split()[3])
                    img = rgb
                elif img.mode != "RGB":
                    img = img.convert("RGB")
                if max(img.size) > MAX_IMAGE_WIDTH:
                    ratio = MAX_IMAGE_WIDTH / max(img.size)
                    new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
                    img = img.resize(new_size, Image.LANCZOS)
                w, h = img.size
                output = BytesIO()
                img.save(output, format="WEBP", quality=85, method=6)
                data = output.getvalue()
                ext = ".webp"
            else:
                ct = resp.headers.get("content-type", "")
                if "png" in ct:
                    ext = ".png"
                elif "gif" in ct:
                    ext = ".gif"
                elif "jpeg" in ct or "jpg" in ct or "image/jpg" in ct:
                    ext = ".jpg"
                elif "webp" in ct:
                    ext = ".webp"
                else:
                    ext = ".jpg"
                data = content
                w, h = 0, 0
            content_md5 = hashlib.md5(data).hexdigest()
            if content_md5 in _GLOBAL_CONTENT_HASHES:
                existing_name = _GLOBAL_CONTENT_HASHES[content_md5]
                existing_path = dest.parent / existing_name
                if existing_path.exists():
                    dest_path = dest.with_suffix(ext)
                    dest_path.write_text(f"REF:{existing_name}")
                    return True, ext, w, h, len(data)
            _GLOBAL_CONTENT_HASHES[content_md5] = dest.name
            dest_path = dest.with_suffix(ext)
            dest_path.write_bytes(data)
            if not HAS_PIL and w == 0:
                try:
                    img = Image.open(BytesIO(data))
                    w, h = img.size
                except Exception:
                    w, h = 1200, 675
            return True, ext, w, h, len(data)
        except (requests.RequestException, OSError, Exception):
            if attempt < retries:
                time.sleep(2 ** attempt)
                continue
    return False, "", 0, 0, 0


def build_credit(result: dict, backend_name: str) -> str:
    creator = result.get("creator", "") or ""
    license_name = result.get("license", "by").upper()
    license_url = result.get("license_url", "") or ""
    backend_labels = {"openverse": "Openverse", "loc": "Library of Congress",
                      "nasa": "NASA", "wikimedia": "Wikimedia Commons",
                      "unsplash": "Unsplash", "pexels": "Pexels",
                      "pixabay": "Pixabay", "ai_generated": "SVG Placeholder"}
    label = backend_labels.get(backend_name, backend_name)
    parts = [f"Photo by {creator}"] if creator else ["Photo"]
    parts.append(f"via {label} ({license_name})")
    if license_url:
        parts.append(f" — {license_url}")
    return " ".join(parts)


def generate_alt_text(section: dict) -> str:
    heading = section.get("heading", "")
    entities = section.get("entities", [])
    section_type = section.get("section_type", "")
    entity_str = " and ".join(entities[:3]) if entities else heading
    type_labels = {
        "key_findings": f"Illustration of key findings about {entity_str}",
        "applied_scenario": f"Scene related to {entity_str}",
        "source_analysis": f"Source document or archive related to {entity_str}",
        "domain_breakdown": f"Visual overview of {entity_str}",
        "cross_pillar": f"Diagram showing connections involving {entity_str}",
        "methodology": f"Research methodology visual for {entity_str}",
    }
    return type_labels.get(section_type, f"Illustration of {entity_str}")[:120]


def fetch_section_images(article: dict, force: bool = False) -> list[dict]:
    sections = parse_sections(article)
    if not sections:
        return article.get("section_images", []) or []

    break_sections = compute_break_points(sections, article)
    if not break_sections:
        return article.get("section_images", []) or []

    slug = article.get("slug", "")

    # Tier 1 — Editorial Manifest (highest priority)
    manifest_entries = get_manifest_entry(slug)
    if manifest_entries:
        manifest_results = []
        for me in manifest_entries:
            idx = me.get("section_index")
            section = next((s for s in break_sections if s["section_index"] == idx), None)
            if not section:
                continue
            dest = IMAGES_DIR / f"manifest_{slug.replace('/', '_')}_s{idx}"
            dest.parent.mkdir(parents=True, exist_ok=True)
            ok, ext, w, h, size = download_image(me["image_url"], dest)
            if ok:
                rel_path = f"/static/images/generated/manifest_{slug.replace('/', '_')}_s{idx}{ext}"
                manifest_results.append({
                    "section_index": idx,
                    "heading": section["heading"],
                    "image_url": rel_path,
                    "image_credit": me.get("image_credit", ""),
                    "image_alt": me.get("image_alt", ""),
                    "relevance_score": 100.0,
                    "source_api": "manifest",
                    "width": w,
                    "height": h,
                    "content_hash": hashlib.sha256(section.get("text_content", "").encode()).hexdigest()[:16],
                })
        if manifest_results:
            return manifest_results

    existing_raw = article.get("section_images", []) or []
    existing_indices = {s.get("section_index") for s in existing_raw}
    if not force and existing_indices >= {s["section_index"] for s in break_sections}:
        return article["section_images"]

    pillar = article.get("pillar", "")
    results: list[dict] = []
    used_urls: set[str] = set()
    used_creators: set[str] = set()

    # Preserve any existing images whose section indices are not in the new break set
    existing_raw = article.get("section_images", []) or []
    break_indices = {s["section_index"] for s in break_sections}
    for ex in existing_raw:
        if ex.get("section_index") not in break_indices:
            img_path = ex.get("image_url", "")
            if img_path and (PROJECT_ROOT / img_path.lstrip("/")).exists():
                results.append(ex)
                used_urls.add(img_path)
                _GLOBAL_USED_URLS.add(img_path)
                cr = ex.get("image_credit", "").split("via")[0].strip().lower()
                if cr:
                    used_creators.add(cr)

    curated_file = resolve_curated(article)
    curated_done = False

    for section in break_sections:
        idx = section["section_index"]
        if not force and idx in existing_indices:
            existing_entry = next((s for s in (article.get("section_images", []) or [])
                                  if s.get("section_index") == idx), None)
            if existing_entry:
                img_path = existing_entry.get("image_url", "")
                if img_path and (PROJECT_ROOT / img_path.lstrip("/")).exists():
                    results.append(existing_entry)
                    used_urls.add(existing_entry.get("image_url", ""))
                    used_creators.add(existing_entry.get("image_credit", "").split("via")[0].strip().lower())
                    _GLOBAL_USED_URLS.add(img_path)
                    continue

        if not curated_done and curated_file:
            curated_result = fetch_curated_commons(curated_file)
            if curated_result:
                dest = IMAGES_DIR / f"{slug}_s{idx}"
                dest.parent.mkdir(parents=True, exist_ok=True)
                ok, ext, w, h, size = download_image(curated_result["url"], dest)
                if ok:
                    rel_path = f"/static/images/generated/{slug}_s{idx}{ext}"
                    results.append({
                        "section_index": idx,
                        "heading": section["heading"],
                        "image_url": rel_path,
                        "image_credit": build_credit(curated_result, "wikimedia"),
                        "image_alt": generate_alt_text(section),
                        "relevance_score": 100.0,
                        "source_api": "curated",
                        "width": w,
                        "height": h,
                        "content_hash": hashlib.sha256(section.get("text_content", "").encode()).hexdigest()[:16],
                    })
                    used_urls.add(rel_path)
                    _GLOBAL_USED_URLS.add(rel_path)
                    used_creators.add(curated_result.get("creator", "").lower()[:30])
                    curated_done = True
                    continue

        query = build_section_query(section, article)
        query_terms, _ = normalize_query(query)
        if not query_terms:
            continue

        all_backends: list[tuple[str, Any]] = []
        if UNSPLASH_KEY:
            all_backends.append(("unsplash", search_unsplash))
        if PIXABAY_KEY:
            all_backends.append(("pixabay", search_pixabay))
        if PEXELS_KEY:
            all_backends.append(("pexels", search_pexels))

        # Build query list: primary + fallbacks for low-coverage section types
        section_type = SECTION_TYPES.get(section.get("section_index", 0), "unknown")
        queries_to_try = [query]
        if section_type in SECTION_FALLBACK_QUERIES:
            queries_to_try.extend(build_fallback_queries(section_type, article.get("pillar", "")))

        # Phase 2: Cross-query candidate pool — search ALL queries + backends
        pool: list[tuple[dict, str, str, int, int]] = []  # (candidate, backend, query_used, width, height)
        for try_query in queries_to_try:
            try_terms, _ = normalize_query(try_query)
            if not try_terms:
                continue
            for backend_name, search_fn in all_backends:
                for attempt in range(1):
                    try:
                        candidates = search_fn(try_query)
                        for c in candidates:
                            url = c.get("url", "")
                            creator = c.get("creator", "").lower()[:30] if c.get("creator") else ""
                            if url in used_urls or url in _GLOBAL_USED_URLS:
                                continue
                            if creator in used_creators:
                                continue
                            creator_key = creator[:20] if creator else ""
                            if creator_key and _GLOBAL_USED_CREATORS.get(creator_key, 0) >= MAX_IMAGES_PER_CREATOR:
                                continue
                            # Pre-filter negative keywords (Phase 4)
                            tags_lower = c.get("tags", "").lower() + " " + c.get("title", "").lower()
                            if any(n in tags_lower for n in {"screenshot", "logo", "icon", "cartoon"}):
                                continue
                            pool.append((c, backend_name, try_query, 0, 0))
                        break
                    except Exception:
                        if attempt < 2:
                            time.sleep(1)
                        continue

        # Score entire pool globally, pick best
        best: dict | None = None
        best_score = 0.0
        best_backend = ""
        if pool:
            scored: list[tuple[float, dict, str]] = []
            for c, backend_name, try_query, w, h in pool:
                try_terms, _ = normalize_query(try_query)
                section_heading = section.get("heading", "")
                pillar_name = article.get("pillar", "")
                score = score_result(c, try_terms, backend_name, w, h,
                                     section_context=section_heading, pillar=pillar_name)
                scored.append((score, c, backend_name))
            scored.sort(key=lambda x: -x[0])
            best_score, best, best_backend = scored[0]

        # Tier 3: SVG fallback (skip AI generation — too slow/unreliable)
        if best is None or best_score < MIN_SCORE:
            dest = IMAGES_DIR / f"{slug}_s{idx}"
            dest.parent.mkdir(parents=True, exist_ok=True)
            ok, ext, w, h, size = generate_svg_placeholder(query, dest)
            if ok:
                rel_path = f"/static/images/generated/{slug}_s{idx}{ext}"
                results.append({
                    "section_index": idx,
                    "heading": section["heading"],
                    "image_url": rel_path,
                    "image_credit": "SVG Placeholder (AcaciaFund)",
                    "image_alt": generate_alt_text(section),
                    "relevance_score": 50.0,
                    "source_api": "svg_fallback",
                    "width": w,
                    "height": h,
                    "content_hash": hashlib.sha256(section.get("text_content", "").encode()).hexdigest()[:16],
                })
                used_urls.add(rel_path)
                _GLOBAL_USED_URLS.add(rel_path)
                continue

        dest = IMAGES_DIR / f"{slug}_s{idx}"
        dest.parent.mkdir(parents=True, exist_ok=True)
        ok, ext, w, h, size = download_image(best["url"], dest)
        if not ok:
            # Download failed — try SVG fallback
            dest = IMAGES_DIR / f"{slug}_s{idx}"
            dest.parent.mkdir(parents=True, exist_ok=True)
            ok2, ext2, w2, h2, size2 = generate_svg_placeholder(query, dest)
            if ok2:
                rel_path = f"/static/images/generated/{slug}_s{idx}{ext2}"
                results.append({
                    "section_index": idx,
                    "heading": section["heading"],
                    "image_url": rel_path,
                    "image_credit": "SVG Placeholder (AcaciaFund)",
                    "image_alt": generate_alt_text(section),
                    "relevance_score": 50.0,
                    "source_api": "svg_fallback",
                    "width": w2,
                    "height": h2,
                    "content_hash": hashlib.sha256(section.get("text_content", "").encode()).hexdigest()[:16],
                })
                used_urls.add(rel_path)
                _GLOBAL_USED_URLS.add(rel_path)
            continue

        # Phase 5: Perceptual hash near-dup check
        dest_file = dest.with_suffix(ext)
        if dest_file.exists():
            try:
                img_bytes = dest_file.read_bytes()
                phash = compute_color_hash(img_bytes)
                existing = _GLOBAL_CONTENT_HASHES.get(phash)
                if existing and existing != dest_file.name:
                    dest_file.unlink()
                    continue
                _GLOBAL_CONTENT_HASHES[phash] = dest_file.name
            except Exception:
                pass

        rel_path = f"/static/images/generated/{slug}_s{idx}{ext}"
        results.append({
            "section_index": idx,
            "heading": section["heading"],
            "image_url": rel_path,
            "image_credit": build_credit(best, best_backend),
            "image_alt": generate_alt_text(section),
            "relevance_score": round(best_score, 1),
            "source_api": best_backend,
            "width": w,
            "height": h,
            "content_hash": hashlib.sha256(section.get("text_content", "").encode()).hexdigest()[:16],
        })
        used_urls.add(rel_path)
        _GLOBAL_USED_URLS.add(rel_path)
        used_creators.add(best.get("creator", "").lower()[:30] if best.get("creator") else "")
        # Track global creator count
        ck = (best.get("creator", "") or "")[:20].lower()
        if ck:
            _GLOBAL_USED_CREATORS[ck] = _GLOBAL_USED_CREATORS.get(ck, 0) + 1

    return results


def _description_keywords(description: str, max_words: int = 6) -> str:
    """Extract meaningful keywords from article description for image search."""
    if not description:
        return ""
    skip = {'the','and','for','with','from','how','what','why','when','into','your',
            'that','this','does','make','using','best','guide','part','series','new',
            'top','overview','analysis','study','report','review','update','learn',
            'about','also','its','than','them','been','have','more','some','very',
            'their','other','could','after','first','being','under','between'}
    words = re.findall(r'[a-zA-Z]{4,}', description.lower())
    words = [w for w in words if w not in skip]
    seen = set()
    unique = []
    for w in words:
        if w not in seen:
            seen.add(w)
            unique.append(w)
    return " ".join(unique[:max_words])


def _build_featured_queries(article: dict) -> list[str]:
    """Build query variations for featured image search, most specific to broadest."""
    pillar = article.get("pillar", "")
    tags = article.get("tags", [])
    title = article.get("title", "")
    description = article.get("description", "")

    skip_words = {'the','and','for','with','from','how','what','why','when','into',
                  'your','that','this','does','make','using','best','guide','part',
                  'series','new','top','guide','overview'}
    title_words = [w for w in re.findall(r'[a-z]{3,}', title.lower()) if w not in skip_words]
    title_phrase = " ".join(title_words[:4])

    tag_phrase = " ".join(t[:3] for t in tags if len(t) > 2) if tags else ""
    desc_phrase = _description_keywords(description, 6)

    pillar_kw = PILLAR_KEYWORDS.get(pillar, "").split()[:2]
    pillar_phrase = " ".join(pillar_kw)

    visual_kw = PILLAR_VISUAL_KEYWORDS.get(pillar, "").split()[:2]
    visual_phrase = " ".join(visual_kw)

    broad_kw = {"aml": "financial regulation banking compliance",
                "stock": "market trading semiconductor investment",
                "data-engineering": "data pipeline database technology",
                "science": "research laboratory experiment science"}.get(pillar, "technology")

    queries = []

    # Compound: all signals combined + description + semantic expansion
    compound = " ".join(filter(None, [title_phrase, tag_phrase, desc_phrase, pillar_phrase]))
    if compound.strip() and len(compound) > 5:
        queries.append(expand_query(compound.strip()[:120]))

    # Title + description
    if title_phrase and desc_phrase:
        td = f"{title_phrase} {desc_phrase}".strip()[:100]
        if td not in queries:
            queries.append(td)

    # Title + visual
    if title_phrase:
        fallback = f"{title_phrase} {visual_phrase}".strip()[:100]
        if fallback not in queries:
            queries.append(fallback)

    # Tags + pillar
    if tag_phrase and pillar_phrase:
        tp = f"{tag_phrase} {pillar_phrase}".strip()[:80]
        if tp not in queries:
            queries.append(tp)

    # Pillar + visual
    broad = f"{pillar_phrase} {visual_phrase}".strip()
    if broad and broad not in queries:
        queries.append(broad)

    # Ultra broad pillar keywords
    for kw in broad_kw.split():
        if kw not in queries:
            queries.append(kw)

    return queries


def fetch_featured_image(article: dict) -> str | None:
    """Fetch a single featured image for an article's card/thumbnail.

    Uses cross-query candidate pool (Phase 2) + multi-dimensional scoring (Phase 1).
    """
    slug = article.get("slug", "")

    dest = IMAGES_DIR / slug
    dest.parent.mkdir(parents=True, exist_ok=True)

    all_backends: list[tuple[str, Any]] = []
    if PIXABAY_KEY:
        all_backends.append(("pixabay", search_pixabay))
    if UNSPLASH_KEY:
        all_backends.append(("unsplash", search_unsplash))
    if PEXELS_KEY:
        all_backends.append(("pexels", search_pexels))

    queries = _build_featured_queries(article)

    # Phase 2: Cross-query candidate pool
    pool: list[tuple[dict, str, str]] = []
    for query in queries:
        query_terms, _ = normalize_query(query)
        if not query_terms:
            continue
        for backend_name, search_fn in all_backends:
            try:
                candidates = search_fn(query)
                for c in candidates:
                    url = c.get("url", "")
                    if url in _GLOBAL_USED_URLS:
                        continue
                    tags_lower = c.get("tags", "").lower() + " " + c.get("title", "").lower()
                    if any(n in tags_lower for n in {"screenshot", "logo", "icon", "cartoon"}):
                        continue
                    pool.append((c, backend_name, query))
            except Exception:
                continue

    if not pool:
        return None

    pillar_name = article.get("pillar", "")
    scored: list[tuple[float, dict, str]] = []
    for c, backend_name, query in pool:
        query_terms, _ = normalize_query(query)
        score = score_result(c, query_terms, backend_name, pillar=pillar_name)
        scored.append((score, c, backend_name))
    scored.sort(key=lambda x: -x[0])

    best_score, best, best_backend = scored[0]
    if best_score < MIN_SCORE:
        return None

    ok, ext, w, h, size = download_image(best["url"], dest)
    if ok:
        # Phase 5: Perceptual hash near-dup check
        dest_file = dest.with_suffix(ext)
        if dest_file.exists():
            try:
                img_bytes = dest_file.read_bytes()
                phash = compute_color_hash(img_bytes)
                existing = _GLOBAL_CONTENT_HASHES.get(phash)
                if existing and existing != dest_file.name:
                    dest_file.unlink()
                    return None
                _GLOBAL_CONTENT_HASHES[phash] = dest_file.name
            except Exception:
                pass
        _GLOBAL_USED_URLS.add(best["url"])
        rel_path = f"/static/images/generated/{slug}{ext}"
        return rel_path

    return None


PIPELINE_RUNS_PATH = PROJECT_ROOT / "registry" / "image-pipeline-runs.json"
MAX_PIPELINE_RUNS = 50


def save_pipeline_stats(stats: dict) -> None:
    """Append this run's stats to the pipeline runs history file."""
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_articles": stats.get("total_articles", 0),
        "articles_with_images": stats.get("articles_with_images", 0),
        "total_section_slots": stats.get("total_section_slots", 0),
        "filled_slots": stats.get("filled_slots", 0),
        "backend_hits": dict(stats.get("backend_hits", {})),
        "section_coverage": {k: {"filled": v[0], "total": v[1]} for k, v in stats.get("section_coverage", {}).items()},
        "relevance_scores": stats.get("relevance_scores", []),
        "avg_score": round(sum(stats.get("relevance_scores", [])) / max(len(stats.get("relevance_scores", [])), 1), 1),
        "total_bytes": stats.get("total_bytes", 0),
        "fill_rate": round(stats.get("filled_slots", 0) / max(stats.get("total_section_slots", 1), 1) * 100, 1),
        "above_70_count": sum(1 for s in stats.get("relevance_scores", []) if s >= 70),
    }
    runs: list[dict] = []
    if PIPELINE_RUNS_PATH.exists():
        try:
            runs = json.loads(PIPELINE_RUNS_PATH.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            runs = []
    runs.append(record)
    runs = runs[-MAX_PIPELINE_RUNS:]
    PIPELINE_RUNS_PATH.parent.mkdir(parents=True, exist_ok=True)
    PIPELINE_RUNS_PATH.write_text(json.dumps(runs, indent=2, default=str), encoding="utf-8")


def print_report(stats: dict):
    print()
    print("═" * 55)
    print(" Section Image Pipeline — Build Report")
    print("═" * 55)
    total = stats.get("total_articles", 0)
    with_images = stats.get("articles_with_images", 0)
    total_sections = stats.get("total_section_slots", 0)
    filled = stats.get("filled_slots", 0)
    print(f"  Articles processed:      {total}")
    print(f"  Articles with images:    {with_images} ({with_images / max(total, 1) * 100:.0f}%)")
    if total_sections:
        print(f"  Sections targeted:       {total_sections}")
        print(f"  Images placed:           {filled} ({filled / total_sections * 100:.1f}%)")
    backend_hits = stats.get("backend_hits", {})
    if backend_hits:
        print()
        print("  Backend hit rate:")
        total_hits = sum(backend_hits.values()) or 1
        for name, count in sorted(backend_hits.items(), key=lambda x: -x[1]):
            print(f"    {name:20s} {count:4d} ({count / total_hits * 100:5.1f}%)")
    section_coverage = stats.get("section_coverage", {})
    if section_coverage:
        print()
        print("  Section coverage:")
        for name, (hits, total_s) in sorted(section_coverage.items(), key=lambda x: -x[1][0]):
            pct = hits / max(total_s, 1) * 100
            bar = "█" * int(pct / 10) + "░" * (10 - int(pct / 10))
            print(f"    {name:20s} {bar} {hits:3d}/{total_s} ({pct:.0f}%)")
    scores = stats.get("relevance_scores", [])
    if scores:
        avg = sum(scores) / max(len(scores), 1)
        print(f"\n  Avg relevance score:     {avg:.1f}")
        print(f"  Above threshold (70+):  {sum(1 for s in scores if s >= 70)} ({sum(1 for s in scores if s >= 70) / max(len(scores), 1) * 100:.0f}%)")
    bandwidth = stats.get("total_bytes", 0)
    if bandwidth:
        print(f"  Total bandwidth:         {bandwidth / 1024 / 1024:.1f} MB")
    print("═" * 55)
    print()


def main():
    parser = argparse.ArgumentParser(description="Fetch section-level images for articles")
    parser.add_argument("--max", type=int, default=0, help="Max articles (0 = all)")
    parser.add_argument("--force", action="store_true", help="Re-fetch all images")
    parser.add_argument("--re-evaluate", action="store_true", help="Re-score cached section images below 70 threshold and re-fetch if better")
    parser.add_argument("--cache", action="store_true", help="Skip articles that already have images")
    args = parser.parse_args()

    # --cache is the default when --force is not set
    use_cache = args.cache or not args.force

    if not REGISTRY_PATH.exists():
        print(f"Registry not found at {REGISTRY_PATH}")
        return 1

    if IMAGES_DIR.exists():
        for f in IMAGES_DIR.rglob("*"):
            if f.is_file() and f.suffix in (".jpg", ".webp", ".png", ".jpeg", ".gif"):
                try:
                    md5 = hashlib.md5(f.read_bytes()).hexdigest()
                    _GLOBAL_CONTENT_HASHES[md5] = f.name
                except Exception:
                    pass
        print(f"Loaded {len(_GLOBAL_CONTENT_HASHES)} existing image hashes for dedup")

    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    content_list = registry.get("content", [])
    max_count = args.max if args.max > 0 else len(content_list)

    content_list.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    articles_to_process = content_list[:max_count]

    print(f"Processing {len(articles_to_process)} articles...")

    stats: dict[str, Any] = {
        "total_articles": len(articles_to_process),
        "articles_with_images": 0,
        "total_section_slots": 0,
        "filled_slots": 0,
        "backend_hits": Counter(),
        "section_coverage": {},
        "relevance_scores": [],
        "total_bytes": 0,
    }
    updated_count = 0

    for article in articles_to_process:
        slug = article.get("slug", "")
        print(f"  {slug} … ", end="", flush=True)

        # Cache mode: check if break points are already fully covered
        existing_images = article.get("section_images", [])
        if use_cache and existing_images and not args.force:
            valid_images = [img for img in existing_images if img.get("image_url")]
            if valid_images:
                # Compute break points to check if all are covered
                sections = parse_sections(article)
                if sections:
                    break_sections = compute_break_points(sections, article)
                    break_indices = {s["section_index"] for s in break_sections}
                    existing_indices = {s.get("section_index") for s in valid_images}
                    fully_covered = existing_indices >= break_indices
                else:
                    fully_covered = True

                if fully_covered and not (args.re_evaluate and any(img.get("relevance_score", 0) < 70 for img in valid_images)):
                    # Still fetch featured image if missing (section images don't imply hero)
                    feat = article.get("featured_image", "")
                    if not feat or not (PROJECT_ROOT / feat.lstrip("/")).exists():
                        fi = fetch_featured_image(article)
                        if fi:
                            article["featured_image"] = fi
                            updated_count += 1
                    print(f"\u2713 cached ({len(valid_images)} images)")
                    stats["articles_with_images"] += 1
                    stats["filled_slots"] += len(valid_images)
                    for si in valid_images:
                        backend = si.get("source_api", "unknown")
                        stats["backend_hits"][backend] += 1
                        score = si.get("relevance_score", 0)
                        stats["relevance_scores"].append(score)
                        stype = SECTION_TYPES.get(si.get("section_index", 0), "unknown")
                        if stype not in stats["section_coverage"]:
                            stats["section_coverage"][stype] = [0, 0]
                        stats["section_coverage"][stype][0] += 1
                        stats["section_coverage"][stype][1] += 1
                    continue

        # Fetch featured image if missing
        feat = article.get("featured_image", "")
        if not feat or not (PROJECT_ROOT / feat.lstrip("/")).exists():
            fi = fetch_featured_image(article)
            if fi:
                article["featured_image"] = fi

        section_images = fetch_section_images(article, force=args.force)
        if section_images:
            article["section_images"] = section_images
            updated_count += 1
            images_placed = len(section_images)
            stats["articles_with_images"] += 1
            stats["filled_slots"] += images_placed
            for si in section_images:
                backend = si.get("source_api", "unknown")
                stats["backend_hits"][backend] += 1
                score = si.get("relevance_score", 0)
                stats["relevance_scores"].append(score)
                stype = SECTION_TYPES.get(si.get("section_index", 0), "unknown")
                if stype not in stats["section_coverage"]:
                    stats["section_coverage"][stype] = [0, 0]
                stats["section_coverage"][stype][0] += 1
                img_path = si.get("image_url", "")
                if img_path:
                    fpath = PROJECT_ROOT / img_path.lstrip("/")
                    if fpath.exists():
                        stats["total_bytes"] += fpath.stat().st_size
            print(f"\u2713 {images_placed} images")
        else:
            print("\u2717")

        time.sleep(RATE_LIMIT_DELAY)

    for article in articles_to_process:
        sections = parse_sections(article)
        for s in sections:
            idx = s["section_index"]
            stype = SECTION_TYPES.get(idx, "unknown")
            if stype not in stats["section_coverage"]:
                stats["section_coverage"][stype] = [0, 0]
            stats["section_coverage"][stype][1] += 1
            if idx in (1, 2, 5):
                stats["total_section_slots"] += 1

    if updated_count > 0:
        registry["content"] = content_list
        REGISTRY_PATH.write_text(json.dumps(registry, indent=2, default=str), encoding="utf-8")
        print(f"\nUpdated {updated_count} articles in registry")
    else:
        print("\nNo articles updated")

    print_report(stats)
    save_pipeline_stats(stats)
    return 0


if __name__ == "__main__":
    exit(main())
