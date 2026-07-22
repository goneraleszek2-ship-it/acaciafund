#!/usr/bin/env python3
"""Multi-Pillar Knowledge Ingestion Adapter.

Unified ingestion engine for all three AcaciaFund pillars:
  - aml    (Financial Compliance / AML)
  - data   (Data Engineering & DataOps)
  - market (Financial Markets & Macroeconomics)

Fetches from arXiv and HackerNews, scores items against per-pillar keyword
matrices, generates structured registry items, deduplicates via slug/URL/title
and Jaccard similarity (≥0.93), and merges into registry.json.

Usage:
    python scripts/knowledge_ingester.py --pillar all             # Full run
    python scripts/knowledge_ingester.py --pillar data --source arxiv --days 7 --dry-run --verbose
    python scripts/knowledge_ingester.py --pillar market --source hn --days 2 --dry-run
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import subprocess
import sys
import time
import uuid
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

logger = logging.getLogger(__name__)

from core.ontology import (
    OntologyManager,
    extract_concepts_from_text,
)

REGISTRY_PATH = ROOT / "registry.json"
ONTOLOGY_PATH = ROOT / "data" / "ontology.json"

# =========================================================================
# Pydantic v2 Schema — validates every item before registry merge
# =========================================================================


class IngestedItem(BaseModel):
    slug: str
    title: str
    pillar: str
    content_type: str = "research"
    tags: List[str] = Field(default_factory=list)
    description: str = ""
    body_html: str = ""
    category: str = "blog"
    language: str = "en"
    date_str: str = ""
    created_at: str = ""
    updated_at: str = ""
    author: str = "Leszek"
    source_url: str = ""
    source_breakdown: Dict[str, int] = Field(default_factory=dict)
    signals: Dict[str, Any] = Field(default_factory=dict)
    quality_metrics: Dict[str, Any] = Field(default_factory=dict)
    sqi: Optional[float] = None
    enriched: bool = False
    lineage: dict = Field(default_factory=dict)
    quality_flags: list = Field(default_factory=list)
    section_images: list = Field(default_factory=list)
    difficulty: str = ""


# =========================================================================
# Per-Pillar Configuration
# =========================================================================


@dataclass
class PillarConfig:
    slug_name: str
    label: str
    arxiv_categories: list[str]
    category_boosts: dict[str, float]  # cat_substring → boost amount
    keyword_patterns: dict[str, list[str]]  # tag → [regex patterns]
    hn_min_score: float = 0.20
    arxiv_min_score: float = 0.15


# ── AML / Financial Compliance ───────────────────────────────────────────

AML_TAGS: dict[str, list[str]] = {
    "aml": [
        r"\baml\b", r"\banti.money.launder", r"\bkyc\b", r"\bknow.your.customer\b",
        r"\bsanctions\b", r"\bfinancial.crime", r"\bmoney.launder", r"\bfiu\b",
        r"\bfatf\b", r"\bfincen\b", r"\bcdd\b", r"\bedd\b", r"\bpep\b",
        r"\bbeneficial.ownership", r"\bshell.company", r"\boffshore\b",
    ],
    "transaction-monitoring": [
        r"\btransaction.monitor", r"\bsuspicious.activity", r"\bsar\b",
        r"\bctr\b", r"\banomaly.detect", r"\bfraud.detect", r"\bpattern.recogni",
        r"\breal.time.monitor", r"\bscreening\b", r"\bwatchlist\b",
        r"\banomaly.detect", r"\binsider.trad", r"\bmarket.abuse",
        r"\badverse.selection", r"\bfinancial.anomaly", r"\boutlier.detect",
    ],
    "regtech": [
        r"\bregtech\b", r"\bregulatory.technol", r"\bcompliance.automat",
        r"\bsup.technol", r"\breporting.automat", r"\bnarrative.generation",
    ],
    "financial-intelligence": [
        r"\bfinancial.intelligence", r"\bintelligence.unit", r"\bstr.analysis",
        r"\badverse.media", r"\bpolitically.exposed", r"\bcorrespondent.bank",
    ],
    "crypto-aml": [
        r"\bcrypto.aml\b", r"\bvirtual.asset", r"\bvas[pe]\b", r"\btravel.rule",
        r"\bcrypto.compliance", r"\bblockchain.forensic", r"\bchainalysis",
        r"\btrace.analysis", r"\bde.fi\b", r"\bdefi.aml\b",
    ],
    "trade-finance-crime": [
        r"\btrade.based", r"\btrade.finance", r"\bexport.control",
        r"\btrade.sanctions", r"\bdual.use", r"\bstrategic.trade",
        r"\bmanipulation", r"\bmarket.manipul", r"\bprice.manipul",
    ],
    "risk-management": [
        r"\brisk.assess", r"\brisk.based.approach", r"\brisk.scoring",
        r"\brisk.indicat", r"\baml.risk\b", r"\bfinancial.risk\b",
        r"\brisk.manag", r"\bportfolio.risk", r"\bmodal.risk",
    ],
}

AML_CATEGORY_BOOSTS: dict[str, float] = {
    "cs.cr": 0.12, "cs.cy": 0.12, "cs.ir": 0.12, "cs.si": 0.12, "cs.gt": 0.12,
    "q-fin.gn": 0.15, "q-fin.rm": 0.15, "q-fin.pm": 0.15, "q-fin.ec": 0.15,
    "q-fin.st": 0.15, "q-fin.cp": 0.15, "q-fin.tr": 0.15, "q-fin.mf": 0.15,
}

# ── Data Engineering & DataOps ───────────────────────────────────────────

DATA_TAGS: dict[str, list[str]] = {
    "dataops": [
        r"\bdbt\b", r"\bdata.build.tool", r"\borchestration", r"\bdag\b",
        r"\bairflow\b", r"\bdagster\b", r"\bprefect\b", r"\bdataops\b",
        r"\bpipeline", r"\betl\b", r"\bdata.workflow", r"\bworkflow\b",
    ],
    "schema-governance": [
        r"\bdata.contract", r"\bschema.registry", r"\bschema.drift\b",
        r"\bdeclarative.schema", r"\bdata.lineage\b", r"\bdata.catalog\b",
        r"\bdata.mesh\b", r"\bdata.product\b", r"\bdata.governance\b",
        r"\bdata.model", r"\bdimensional.mod", r"\bstar.schema\b",
        r"\bsnowflake.schema", r"\bmetadata\b",
    ],
    "stream-processing": [
        r"\bstream\b", r"\bapache.flink", r"\bcdc\b", r"\bchange.data.capture",
        r"\bchange.capture", r"\bstateful\b", r"\bkafka\b",
        r"\breal.time\b", r"\bevent.driven\b", r"\bpub.sub\b",
    ],
    "data-lakehouse": [
        r"\bapache.iceberg", r"\bdelta.lake", r"\bapache.arrow",
        r"\bparquet\b", r"\bduckdb\b", r"\blakehouse\b", r"\bdata.lake\b",
        r"\bdatabase\b", r"\bstorage\b", r"\bcolumnar\b",
    ],
    "data-quality": [
        r"\bdata.quality", r"\bgreat.expectations", r"\bdata.observability",
        r"\bdata.lineage", r"\banomaly.detect", r"\bmonitoring\b",
        r"\bdata.valid", r"\bdata.profil", r"\bdata.clean\b",
    ],
    "distributed-systems": [
        r"\bdistributed\b", r"\bparallel\b", r"\bconsensus\b",
        r"\btransaction\b", r"\bconcurren", r"\bfault.tolerance",
        r"\breplication", r"\bshard\b", r"\bpartition",
    ],
    "query-optimization": [
        r"\bquery.optim", r"\bindex\b", r"\bmaterialized.view",
        r"\bquery.process", r"\bexecution.plan", r"\bcost.model",
        r"\bapproximate.query", r"\bcardinality.estimat",
    ],
}

DATA_CATEGORY_BOOSTS: dict[str, float] = {
    "cs.db": 0.15, "cs.dc": 0.15,
}

# ── Financial Markets & Macroeconomics ───────────────────────────────────

MARKET_TAGS: dict[str, list[str]] = {
    "market-microstructure": [
        r"\bmarket.microstructure", r"\border.book", r"\bliquidity\b",
        r"\bdark.pool", r"\border.flow", r"\bimbalance\b", r"\bexecution\b",
        r"\betf\b", r"\bexchange.traded", r"\bhft\b", r"\bhigh.frequency",
        r"\bmarket.maker", r"\bspread\b", r"\bquote\b",
    ],
    "systemic-risk": [
        r"\bsystemic.risk", r"\bcounterparty.risk", r"\bnbfi\b",
        r"\bnon.bank.financ", r"\bcontagion\b", r"\bfinancial.stability\b",
        r"\bcredit.risk\b", r"\bsystemically.important", r"\bsifi\b",
    ],
    "quantitative-modeling": [
        r"\bregime.switch", r"\bbayesian\b", r"\bcorrelation\b",
        r"\bvolatility\b", r"\barbitrage\b", r"\bcross.asset\b",
        r"\boption\b", r"\bderivative", r"\bportfolio\b", r"\bfactor.model",
        r"\bstochastic", r"\bmonte.carlo", r"\brisk.model",
    ],
    "macro-finance": [
        r"\bmacroeconomic\b", r"\bmonetary.polic", r"\binflation\b",
        r"\byield.curve\b", r"\bfiscal\b", r"\bcentral.bank\b",
        r"\binterest.rate", r"\bgdp\b", r"\bemployment\b",
        r"\bquantitative.easing", r"\bfinancial.market",
        r"\basset.price", r"\bcapital.market",
    ],
    "sec-filings": [
        r"\b10.k\b", r"\b10.q\b", r"\b8.k\b", r"\b6.k\b",
        r"\bn.csr\b", r"\bs.1\b", r"\b424b", r"\bpreliminary.pricing",
        r"\bpricing.supplement", r"\bprospectus", r"\bshareholder.report",
        r"\bform.k\b", r"\bform.q\b", r"\bsec.filing",
    ],
}

MARKET_CATEGORY_BOOSTS: dict[str, float] = {
    "q-fin.mf": 0.15, "q-fin.tr": 0.15, "econ.em": 0.15,
}

# =========================================================================
# Pillar registry
# =========================================================================

PILLAR_CONFIGS: dict[str, PillarConfig] = {
    "aml": PillarConfig(
        slug_name="aml",
        label="Financial Compliance",
        arxiv_categories=[
            "q-fin.GN", "q-fin.RM", "cs.CY", "cs.CR", "q-fin.PM", "q-fin.EC",
            "cs.IR", "stat.AP", "q-fin.ST", "cs.SI", "cs.MA", "cs.GT",
            "q-fin.MF", "q-fin.CP", "q-fin.TR",
        ],
        category_boosts=AML_CATEGORY_BOOSTS,
        keyword_patterns=AML_TAGS,
    ),
    "data": PillarConfig(
        slug_name="data",
        label="Data Engineering & DataOps",
        arxiv_categories=["cs.DB", "cs.DC", "cs.SE", "cs.CE"],
        category_boosts=DATA_CATEGORY_BOOSTS,
        keyword_patterns=DATA_TAGS,
    ),
    "market": PillarConfig(
        slug_name="market",
        label="Financial Markets & Macroeconomics",
        arxiv_categories=["q-fin.MF", "q-fin.PM", "q-fin.TR", "econ.EM", "q-fin.CP"],
        category_boosts=MARKET_CATEGORY_BOOSTS,
        keyword_patterns=MARKET_TAGS,
    ),
}

# Map ingester slug_name → registry pillar → URL segment
INGESTER_TO_PILLAR = {"aml": "aml", "data": "data-engineering", "market": "stock"}
from config import PILLAR_URL_MAP

# =========================================================================
# Shared Utilities
# =========================================================================

_SLUG_CLEAN = re.compile(r"[^a-z0-9-]+")
_MULTI_DASH = re.compile(r"-{2,}")


def _slugify(text: str, max_len: int = 60) -> str:
    s = text.lower()
    s = s.replace("'", "").replace('"', "")
    s = _SLUG_CLEAN.sub("-", s).strip("-")
    s = _MULTI_DASH.sub("-", s)
    return s[:max_len].rstrip("-")


_WORD_RE = re.compile(r"\b\w+\b")


def jaccard_similarity(a: str, b: str) -> float:
    """Token-level Jaccard similarity using word-boundary tokenization."""
    words1 = set(_WORD_RE.findall(a.lower()))
    words2 = set(_WORD_RE.findall(b.lower()))
    if not words1 or not words2:
        return 0.0
    return len(words1 & words2) / len(words1 | words2)


# =========================================================================
# Ontology Concept Extraction
# =========================================================================


def extract_and_store_concepts(
    items: list[dict[str, Any]],
    ontology: OntologyManager,
) -> int:
    """Extract ontology concepts from ingested items and store them.

    For each item, matches title + description + tags against known ontology
    concepts.  Returns the total number of concept associations found.
    """
    associations = 0
    for item in items:
        text = " ".join([
            item.get("title", ""),
            item.get("description", ""),
            " ".join(item.get("tags", [])),
        ])
        matches = extract_concepts_from_text(text, ontology, min_confidence=0.5)
        if matches:
            concept_ids = [c.id for c, _ in matches]
            item["extracted_concepts"] = concept_ids
            associations += len(concept_ids)
    return associations


# =========================================================================
# Relevance Scoring Engine
# =========================================================================


def score_pillar_relevance(
    text: str,
    config: PillarConfig,
    categories: list[str] | None = None,
) -> tuple[float, list[str]]:
    """Score text against a pillar's keyword matrix.

    Returns (score, detected_tags) where score ∈ [0.0, 1.0].
    """
    lower = text.lower()
    hits: int = 0
    detected: list[str] = []

    # Keyword matching
    for tag, patterns in config.keyword_patterns.items():
        for pattern_str in patterns:
            if re.search(pattern_str, lower):
                hits += 1
                if tag not in detected:
                    detected.append(tag)
                break

    # Category boost
    category_bonus = 0.0
    if categories:
        for cat in categories:
            cat_lower = cat.lower()
            boost = config.category_boosts.get(cat_lower, 0.0)
            if boost > category_bonus:
                category_bonus = boost

    if hits == 0 and category_bonus == 0.0:
        return 0.0, []

    word_count = len(lower.split())
    density = hits / max(word_count, 10)
    kw_score = min(1.0, density * 10)

    # If only category boost (no keyword hits), use reduced score
    if hits == 0:
        return min(1.0, category_bonus * 2), detected

    score = kw_score * 1.5 + category_bonus
    return min(1.0, score), detected


# =========================================================================
# Source Fetchers
# =========================================================================


def fetch_arxiv_for_pillar(
    config: PillarConfig,
    days_back: int = 7,
    max_results: int = 100,
    verbose: bool = False,
) -> list[dict[str, Any]]:
    """Fetch arXiv papers and score against a pillar config."""
    from core.fetch import fetch_arxiv

    papers = fetch_arxiv(since_hours=max(24, days_back * 24), max_results=max_results)
    if verbose:
        logger.debug(f"  arXiv returned {len(papers)} total papers")

    relevant: list[dict[str, Any]] = []
    for p in papers:
        title = p.get("title", "")
        abstract = p.get("abstract", "")
        cats = p.get("categories") or []
        score, tags = score_pillar_relevance(f"{title} {abstract}", config, cats)
        threshold = config.arxiv_min_score
        if score >= threshold:
            p["_relevance_score"] = round(score, 3)
            p["_detected_tags"] = tags
            p["_pillar"] = config.slug_name
            relevant.append(p)

    relevant.sort(key=lambda p: p["_relevance_score"], reverse=True)
    if verbose:
        logger.debug(f"  {config.slug_name}-relevant (score >= {threshold}): {len(relevant)}")
        for p in relevant[:3]:
            logger.debug(f"    [{p['_relevance_score']:.2f}] {p.get('title', '')[:70]}")
    return relevant


def fetch_hn_for_pillar(
    config: PillarConfig,
    days_back: int = 7,
    min_points: int = 3,
    max_hits: int = 200,
    verbose: bool = False,
) -> list[dict[str, Any]]:
    """Fetch HN stories and score against a pillar config."""
    from core.fetch import fetch_hn_stories

    stories = fetch_hn_stories(
        since_hours=max(24, days_back * 24),
        min_points=min_points,
        max_hits=max_hits,
    )
    if verbose:
        logger.debug(f"  HN returned {len(stories)} stories")

    relevant: list[dict[str, Any]] = []
    for s in stories:
        title = s.get("title", "")
        score, tags = score_pillar_relevance(title, config)
        threshold = config.hn_min_score
        if score >= threshold:
            s["_relevance_score"] = round(score, 3)
            s["_detected_tags"] = tags
            s["_pillar"] = config.slug_name
            relevant.append(s)

    relevant.sort(key=lambda s: s["_relevance_score"], reverse=True)
    if verbose:
        logger.debug(f"  {config.slug_name}-relevant (score >= {threshold}): {len(relevant)}")
    return relevant


# =========================================================================
# Source → Registry Item converters
# =========================================================================

# Default pillar tags inserted when no tags detected
_PILLAR_BASE_TAGS = {"aml": "aml", "data": "dataops", "market": "market-microstructure"}


def _source_to_item(
    source: dict,
    config: PillarConfig,
    *,
    source_key: str,
    title: str = "",
    url: str = "",
    date_str: str = "",
    summary: str = "",
    body_html: str = "",
    author: str = "",
    tags: list[str] | None = None,
    avg_sqi: float = 0.65,
    score: float = 0.70,
    signals_extra: dict | None = None,
    quality_extra: dict | None = None,
) -> dict[str, Any] | None:
    """Unified converter: source dict + pillar config → registry content item."""
    if not title:
        return None

    slug_date = date_str[:10] if date_str else datetime.now(timezone.utc).strftime("%Y-%m-%d")
    slug_base = _slugify(title)
    pillar = config.slug_name
    registry_pillar = INGESTER_TO_PILLAR.get(pillar, pillar)
    pillar_url = PILLAR_URL_MAP.get(registry_pillar, registry_pillar)
    slug = f"{pillar_url}/research/{slug_base}"

    if tags is None:
        tags = source.get("_detected_tags", [])

    # Insert base pillar tag if missing
    base_tag = _PILLAR_BASE_TAGS.get(pillar)
    if base_tag and base_tag not in tags:
        tags.insert(0, base_tag)
    tags = list(dict.fromkeys(tags))

    if not body_html:
        body_html = f"<p>{summary}</p>" if summary else ""
    if not summary:
        summary = title[:200]
    description = summary[:300].rstrip() + ("..." if len(summary) > 300 else "") if summary else title[:200]

    now_iso = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    signals = {
        "avg_sqi": avg_sqi,
        "count": 1,
        "domain_diversity": len(tags),
        "top_entities": [url] if url else [],
    }
    if signals_extra:
        signals.update(signals_extra)

    quality = {
        "score": score,
        "source_verified": True,
        "evidence_level": "Unknown",
        "trend_strength": 50.0,
        "adoption_level": "emerging",
    }
    if quality_extra:
        quality.update(quality_extra)

    return {
        "slug": slug,
        "title": title,
        "pillar": registry_pillar,
        "content_type": "research",
        "tags": tags,
        "description": description,
        "body_html": body_html,
        "category": "blog",
        "language": "en",
        "date_str": slug_date,
        "created_at": date_str or now_iso,
        "updated_at": now_iso,
        "author": author or "AcaciaFund",
        "source_url": url,
        "source_breakdown": {source_key: 1},
        "signals": signals,
        "quality_metrics": quality,
        "sqi": None,
        "enriched": False,
        "lineage": {},
        "quality_flags": [],
        "section_images": [],
        "difficulty": "",
    }


def _arxiv_to_item(paper: dict, config: PillarConfig) -> dict[str, Any] | None:
    """Convert arXiv paper dict into a registry content item."""
    title = (paper.get("title") or "").strip()
    abstract = (paper.get("abstract") or "").strip()
    url = (paper.get("url") or "").strip()
    published = (paper.get("published") or "").strip()

    if not title or not abstract:
        return None

    tags = paper.get("_detected_tags", [])
    if not tags:
        for cat in (paper.get("categories") or []):
            cat_lower = cat.lower()
            if config.slug_name == "data":
                if cat_lower == "cs.db": tags.append("database-systems")
                elif cat_lower == "cs.dc": tags.append("distributed-computing")
                elif cat_lower == "cs.se": tags.append("software-engineering")
            elif config.slug_name == "market":
                if cat_lower in ("q-fin.mf", "q-fin.tr"): tags.append("market-microstructure")
                elif cat_lower == "econ.em": tags.append("quantitative-modeling")
                elif cat_lower == "q-fin.cp": tags.append("computational-finance")

    return _source_to_item(
        paper, config, source_key="arxiv", title=title, url=url,
        date_str=published, summary=abstract, body_html=f"<p>{abstract}</p>",
        author="Leszek", tags=tags, avg_sqi=0.75, score=0.75,
    )


def _hn_to_item(story: dict, config: PillarConfig) -> dict[str, Any] | None:
    """Convert HN story dict into a registry content item."""
    title = (story.get("title") or "").strip()
    hn_url = (story.get("hn_url") or "").strip()
    url = (story.get("url") or "").strip()
    points = story.get("points", 0) or 0
    author = story.get("author", "anonymous")
    created_at = story.get("created_at", "")

    if not title:
        return None

    description = f"HackerNews discussion ({points} points) about {title[:120]}."
    body = f"<p>HackerNews discussion: <a href='{hn_url}'>{title}</a></p>"
    body += f"<p>Score: {points} points by {author}.</p>"
    if url and url != hn_url:
        body += f"<p>Source: <a href='{url}'>{url[:80]}</a></p>"

    return _source_to_item(
        story, config, source_key="hn", title=title, url=hn_url,
        date_str=created_at, summary=description, body_html=body,
        author=author, avg_sqi=0.55,
        score=min(0.95, 0.45 + (points / 1000)),
        signals_extra={"count": points, "total_score": points * 100, "avg_score": float(points)},
        quality_extra={"trend_strength": min(100.0, points)},
    )


# =========================================================================
# SEC EDGAR
# =========================================================================


def fetch_sec_edgar_for_pillar(
    config: PillarConfig,
    days_back: int = 7,
    verbose: bool = False,
) -> list[dict]:
    """Fetch SEC EDGAR filings and score against a pillar config."""
    from core.fetch import fetch_sec_edgar

    filings = fetch_sec_edgar(
        query=" OR ".join(list(config.keyword_patterns.keys())[:5]),
        days_back=days_back,
        max_results=50,
    )
    if verbose:
        logger.debug(f"  SEC EDGAR returned {len(filings)} filings")

    threshold = config.hn_min_score
    relevant: list[dict] = []
    for f in filings:
        title = f.get("title", "")
        summary = f.get("summary", "")
        score, tags = score_pillar_relevance(f"{title} {summary}", config)
        if score >= threshold:
            f["_relevance_score"] = round(score, 3)
            f["_detected_tags"] = tags
            f["_pillar"] = config.slug_name
            relevant.append(f)

    relevant.sort(key=lambda f: f["_relevance_score"], reverse=True)
    if verbose:
        logger.debug(f"  {config.slug_name}-relevant (score >= {threshold}): {len(relevant)}")
    return relevant


def _sec_edgar_to_item(filing: dict, config: PillarConfig) -> dict[str, Any] | None:
    """Convert SEC EDGAR filing dict into a registry content item."""
    title = (filing.get("title") or "").strip()
    url = (filing.get("url") or "").strip()
    published = (filing.get("published") or "")[:10]
    summary = (filing.get("summary") or "").strip()

    if not title:
        return None

    return _source_to_item(
        filing, config, source_key="sec-edgar", title=title, url=url,
        date_str=published, summary=summary,
        author="SEC EDGAR", avg_sqi=0.7, score=0.7,
        quality_extra={"evidence_level": "Official", "adoption_level": "established"},
    )


# =========================================================================
# SSRN
# =========================================================================


def fetch_ssrn_for_pillar(
    config: PillarConfig,
    days_back: int = 7,
    verbose: bool = False,
) -> list[dict]:
    """Fetch SSRN papers and score against a pillar config."""
    from core.fetch import fetch_ssrn

    papers = fetch_ssrn(days_back=days_back, max_results=50)
    if verbose:
        logger.debug(f"  SSRN returned {len(papers)} papers")

    threshold = config.hn_min_score
    relevant: list[dict] = []
    for p in papers:
        title = p.get("title", "")
        summary = p.get("summary", "")
        score, tags = score_pillar_relevance(f"{title} {summary}", config)
        if score >= threshold:
            p["_relevance_score"] = round(score, 3)
            p["_detected_tags"] = tags
            p["_pillar"] = config.slug_name
            relevant.append(p)

    relevant.sort(key=lambda p: p["_relevance_score"], reverse=True)
    if verbose:
        logger.debug(f"  {config.slug_name}-relevant (score >= {threshold}): {len(relevant)}")
    return relevant


def _ssrn_to_item(paper: dict, config: PillarConfig) -> dict[str, Any] | None:
    """Convert SSRN paper dict into a registry content item."""
    title = (paper.get("title") or "").strip()
    url = (paper.get("url") or "").strip()
    published = (paper.get("published") or "")[:10]
    summary = (paper.get("summary") or "").strip()

    if not title:
        return None

    return _source_to_item(
        paper, config, source_key="ssrn", title=title, url=url,
        date_str=published, summary=summary, author="SSRN",
        avg_sqi=0.75, score=0.75,
        quality_extra={"evidence_level": "Academic"},
    )


# =========================================================================
# NBER
# =========================================================================


def fetch_nber_for_pillar(
    config: PillarConfig,
    days_back: int = 7,
    verbose: bool = False,
) -> list[dict]:
    """Fetch NBER papers and score against a pillar config."""
    from core.fetch import fetch_nber

    papers = fetch_nber(days_back=days_back, max_results=50)
    if verbose:
        logger.debug(f"  NBER returned {len(papers)} papers")

    threshold = config.hn_min_score
    relevant: list[dict] = []
    for p in papers:
        title = p.get("title", "")
        summary = p.get("summary", "")
        score, tags = score_pillar_relevance(f"{title} {summary}", config)
        if score >= threshold:
            p["_relevance_score"] = round(score, 3)
            p["_detected_tags"] = tags
            p["_pillar"] = config.slug_name
            relevant.append(p)

    relevant.sort(key=lambda p: p["_relevance_score"], reverse=True)
    if verbose:
        logger.debug(f"  {config.slug_name}-relevant (score >= {threshold}): {len(relevant)}")
    return relevant


def _nber_to_item(paper: dict, config: PillarConfig) -> dict[str, Any] | None:
    """Convert NBER paper dict into a registry content item."""
    title = (paper.get("title") or "").strip()
    url = (paper.get("url") or "").strip()
    published = (paper.get("published") or "")[:10]
    summary = (paper.get("summary") or "").strip()

    if not title:
        return None

    return _source_to_item(
        paper, config, source_key="nber", title=title, url=url,
        date_str=published, summary=summary, author="NBER",
        avg_sqi=0.75, score=0.75,
        quality_extra={"evidence_level": "Academic"},
    )


# =========================================================================
# PubMed Fetcher
# =========================================================================

PUBMED_QUERIES: dict[str, list[str]] = {
    "aml": [
        "anti-money laundering", "know your customer", "financial crime",
        "sanctions compliance", "suspicious activity report",
        "beneficial ownership", "financial intelligence unit",
    ],
    "data": [
        "data pipeline", "data quality", "distributed systems",
        "machine learning infrastructure", "stream processing",
        "data engineering", "data governance",
    ],
    "market": [
        "market microstructure", "portfolio optimization", "financial risk",
        "behavioral finance", "options pricing", "asset allocation",
        "systemic risk",
    ],
}


def fetch_pubmed_for_pillar(
    config: PillarConfig,
    days_back: int = 7,
    verbose: bool = False,
) -> list[dict]:
    """Fetch PubMed papers and score against a pillar config."""
    from core.fetch import fetch_pubmed

    queries = PUBMED_QUERIES.get(config.slug_name, [])
    if not queries:
        return []

    since_hours = days_back * 24
    papers = fetch_pubmed(since_hours=since_hours, max_results=300)
    if verbose:
        logger.debug(f"  PubMed returned {len(papers)} papers")

    threshold = config.hn_min_score
    relevant: list[dict] = []
    for p in papers:
        title = p.get("title", "")
        summary = p.get("abstract", "")
        score, tags = score_pillar_relevance(f"{title} {summary}", config)
        if score >= threshold:
            p["_relevance_score"] = round(score, 3)
            p["_detected_tags"] = tags
            p["_pillar"] = config.slug_name
            relevant.append(p)

    relevant.sort(key=lambda p: p["_relevance_score"], reverse=True)
    if verbose:
        logger.debug(f"  {config.slug_name}-relevant (score >= {threshold}): {len(relevant)}")
    return relevant


def _pubmed_to_item(paper: dict, config: PillarConfig) -> dict[str, Any] | None:
    """Convert PubMed paper dict into a registry content item."""
    title = (paper.get("title") or "").strip()
    url = (paper.get("url") or "").strip()
    published = (paper.get("published") or "")[:10]
    abstract = (paper.get("abstract") or "").strip()

    if not title:
        return None

    return _source_to_item(
        paper, config, source_key="pubmed", title=title, url=url,
        date_str=published, summary=abstract,
        author=paper.get("author", "PubMed"),
        avg_sqi=0.70, score=0.70,
        quality_extra={"evidence_level": "Academic", "trend_strength": 40.0},
    )


# =========================================================================
# Semantic Scholar Fetcher
# =========================================================================

S2_QUERIES: dict[str, list[str]] = {
    "aml": [
        "anti-money laundering compliance",
        "financial crime regulation",
        "suspicious transaction detection",
        "know your customer verification",
    ],
    "data": [
        "data engineering pipeline",
        "distributed data processing",
        "real-time stream processing",
        "data quality monitoring",
    ],
    "market": [
        "market microstructure",
        "portfolio risk management",
        "algorithmic trading",
        "financial market volatility",
    ],
}


def fetch_s2_for_pillar(
    config: PillarConfig,
    days_back: int = 7,
    verbose: bool = False,
) -> list[dict]:
    """Fetch Semantic Scholar papers and score against a pillar config."""
    from core.fetch import fetch_semantic_scholar

    queries = S2_QUERIES.get(config.slug_name, [])
    if not queries:
        return []

    since_hours = days_back * 24
    papers = fetch_semantic_scholar(since_hours=since_hours, max_results=300)
    if verbose:
        logger.debug(f"  Semantic Scholar returned {len(papers)} papers")

    threshold = config.hn_min_score
    relevant: list[dict] = []
    for p in papers:
        title = p.get("title", "")
        abstract = p.get("abstract", "")
        score, tags = score_pillar_relevance(f"{title} {abstract}", config)
        if score >= threshold:
            p["_relevance_score"] = round(score, 3)
            p["_detected_tags"] = tags
            p["_pillar"] = config.slug_name
            relevant.append(p)

    relevant.sort(key=lambda p: p["_relevance_score"], reverse=True)
    if verbose:
        logger.debug(f"  {config.slug_name}-relevant (score >= {threshold}): {len(relevant)}")
    return relevant


def _s2_to_item(paper: dict, config: PillarConfig) -> dict[str, Any] | None:
    """Convert Semantic Scholar paper dict into a registry content item."""
    title = (paper.get("title") or "").strip()
    url = (paper.get("url") or "").strip()
    published = (paper.get("published") or "")[:10]
    abstract = (paper.get("abstract") or "").strip()
    venue = (paper.get("venue") or "").strip()

    if not title:
        return None

    return _source_to_item(
        paper, config, source_key="semantic-scholar", title=title, url=url,
        date_str=published, summary=abstract,
        author=paper.get("author", "Semantic Scholar"),
        avg_sqi=0.72, score=0.72,
        quality_extra={
            "evidence_level": "Academic",
            "trend_strength": 45.0,
            "citations": paper.get("citations", 0),
            "venue": venue,
        },
    )


# =========================================================================
# Deduplication (including Jaccard ≥0.93)
# =========================================================================


def _existing_slugs(registry_data: dict) -> set[str]:
    return {c.get("slug", "") for c in registry_data.get("content", []) if c.get("slug")}


def _existing_urls(registry_data: dict) -> set[str]:
    urls = set()
    for c in registry_data.get("content", []):
        if c.get("source_url"):
            urls.add(c["source_url"].rstrip("/"))
    return urls


def _existing_titles(registry_data: dict) -> list[str]:
    return [
        c.get("title", "").strip().lower()
        for c in registry_data.get("content", [])
        if c.get("title")
    ]


def deduplicate(items: list[dict], registry_data: dict) -> list[dict]:
    """Filter out items already in the registry.

    Checks:
      1. Slug match (set O(1))
      2. Source URL match (set O(1))
      3. Exact title match (set O(1))
      4. Word-overlap pre-check + Jaccard similarity >= 0.93 (near-duplicate title)
    """
    existing_slugs_set = _existing_slugs(registry_data)
    existing_urls_set = _existing_urls(registry_data)
    existing_titles_list = _existing_titles(registry_data)
    existing_titles_set = set(existing_titles_list)

    # Pre-compute word sets for existing titles (for fast overlap check)
    existing_word_sets = [
        (t, set(_WORD_RE.findall(t)))
        for t in existing_titles_list
    ]

    new_items: list[dict] = []
    seen_slugs: set[str] = set()
    duplicates = 0
    for item in items:
        slug = item.get("slug", "")
        source_url = item.get("source_url", "").rstrip("/")
        title = item.get("title", "").strip().lower()

        if slug in existing_slugs_set:
            duplicates += 1
            continue
        if source_url and source_url in existing_urls_set:
            duplicates += 1
            continue
        if title in existing_titles_set:
            duplicates += 1
            continue

        # Fast word-overlap pre-check before full Jaccard
        is_duplicate = False
        if title:
            title_words = set(_WORD_RE.findall(title))
            if len(title_words) < 2:
                pass  # too short to near-dup
            else:
                for et, et_words in existing_word_sets:
                    if not (title_words & et_words):
                        continue
                    overlap = len(title_words & et_words) / max(len(title_words | et_words), 1)
                    if overlap < 0.6:
                        continue
                    if jaccard_similarity(title, et) >= 0.93:
                        duplicates += 1
                        is_duplicate = True
                        break
        if is_duplicate:
            continue

        # Slug collision within batch (O(1) lookup)
        if slug in seen_slugs:
            uid = uuid.uuid4().hex[:6]
            item["slug"] = f"{slug}-{uid}"
            slug = item["slug"]

        seen_slugs.add(slug)
        new_items.append(item)

    if duplicates:
        logger.info(f"  Skipped {duplicates} duplicates (slug/URL/title/Jaccard>=0.93)")
    return new_items


# =========================================================================
# Registry I/O
# =========================================================================

from _registry_utils import load_registry, save_registry


def prune_and_archive_registry(
    registry_data: dict,
    max_active: int = 2000,
    max_age_months: int = 18,
) -> int:
    """Archive old items beyond max_active, keeping newest.

    Items older than max_age_months go to data/registry_archive/YYYY-MM.json.
    If still over limit after age pruning, oldest items are archived.
    Returns count of archived items.
    """
    from datetime import timedelta

    items = registry_data.get("content", [])
    if len(items) <= max_active:
        return 0

    cutoff = datetime.now(timezone.utc) - timedelta(days=max_age_months * 30)

    def _parse_date(d: str) -> datetime:
        try:
            return datetime.fromisoformat(d.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            return datetime.min.replace(tzinfo=timezone.utc)

    # Split by age
    active = []
    archive = []
    for item in items:
        created = _parse_date(item.get("created_at", ""))
        if created > cutoff:
            active.append(item)
        else:
            archive.append(item)

    # If still over limit, archive oldest from active
    if len(active) > max_active:
        active.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        archive.extend(active[max_active:])
        active = active[:max_active]

    if not archive:
        return 0

    # Write archive file
    archive_dir = ROOT / "data" / "registry_archive"
    archive_dir.mkdir(parents=True, exist_ok=True)
    today = datetime.now(timezone.utc).strftime("%Y-%m")
    archive_path = archive_dir / f"{today}.json"

    existing_archive = []
    if archive_path.exists():
        with open(archive_path) as f:
            existing_archive = json.load(f).get("items", [])

    existing_archive.extend(archive)
    with open(archive_path, "w") as f:
        json.dump({"items": existing_archive, "archived_at": datetime.now(timezone.utc).isoformat()}, f, indent=1)

    registry_data["content"] = active
    logger.info(f"  Archived {len(archive)} items to {archive_path.name} (active: {len(active)})")
    return len(archive)


# =========================================================================
# Per-pillar ingestion
# =========================================================================


def ingest_pillar(
    config: PillarConfig,
    source: str,
    days_back: int,
    verbose: bool,
    dry_run: bool,
    max_per_source: int = 0,
) -> list[dict]:
    """Fetch, score, convert items for one pillar. Returns new items."""
    items: list[dict] = []

    if verbose:
        logger.debug(f"\n  ── {config.label} ({config.slug_name}) ──")

    if source in ("arxiv", "all"):
        papers = fetch_arxiv_for_pillar(config, days_back, verbose=verbose)
        for p in papers:
            item = _arxiv_to_item(p, config)
            if item is not None:
                items.append(item)
        if verbose:
            logger.debug(f"  → {sum(1 for i in items if i.get('source_breakdown', {}).get('arxiv'))} arXiv items for {config.slug_name}")

    if source in ("hn", "all"):
        stories = fetch_hn_for_pillar(config, days_back, verbose=verbose)
        for s in stories:
            item = _hn_to_item(s, config)
            if item is not None:
                items.append(item)
        if verbose:
            hn_count = sum(1 for i in items if i.get('source_breakdown', {}).get('hn'))
            logger.debug(f"  → {hn_count} HN items for {config.slug_name}")

    if source in ("sec-edgar", "all"):
        filings = fetch_sec_edgar_for_pillar(config, days_back, verbose=verbose)
        for f in filings:
            item = _sec_edgar_to_item(f, config)
            if item is not None:
                items.append(item)
        if verbose:
            sec_count = sum(1 for i in items if i.get('source_breakdown', {}).get('sec-edgar'))
            logger.debug(f"  → {sec_count} SEC EDGAR items for {config.slug_name}")

    if source in ("ssrn", "all"):
        papers = fetch_ssrn_for_pillar(config, days_back, verbose=verbose)
        for p in papers:
            item = _ssrn_to_item(p, config)
            if item is not None:
                items.append(item)
        if verbose:
            ssrn_count = sum(1 for i in items if i.get('source_breakdown', {}).get('ssrn'))
            logger.debug(f"  → {ssrn_count} SSRN items for {config.slug_name}")

    if source in ("nber", "all"):
        papers = fetch_nber_for_pillar(config, days_back, verbose=verbose)
        for p in papers:
            item = _nber_to_item(p, config)
            if item is not None:
                items.append(item)
        if verbose:
            nber_count = sum(1 for i in items if i.get('source_breakdown', {}).get('nber'))
            logger.debug(f"  → {nber_count} NBER items for {config.slug_name}")

    if source in ("pubmed", "all"):
        papers = fetch_pubmed_for_pillar(config, days_back, verbose=verbose)
        for p in papers:
            item = _pubmed_to_item(p, config)
            if item is not None:
                items.append(item)
        if verbose:
            pubmed_count = sum(1 for i in items if i.get('source_breakdown', {}).get('pubmed'))
            logger.debug(f"  → {pubmed_count} PubMed items for {config.slug_name}")

    if source in ("semantic-scholar", "all"):
        papers = fetch_s2_for_pillar(config, days_back, verbose=verbose)
        for p in papers:
            item = _s2_to_item(p, config)
            if item is not None:
                items.append(item)
        if verbose:
            s2_count = sum(1 for i in items if i.get('source_breakdown', {}).get('semantic-scholar'))
            logger.debug(f"  → {s2_count} Semantic Scholar items for {config.slug_name}")

    return items


# =========================================================================
# Main
# =========================================================================


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Multi-Pillar Knowledge Ingestion Adapter",
    )
    parser.add_argument(
        "--pillar",
        choices=["aml", "data", "market", "all"],
        default="all",
        help="Which pillar to ingest (default: all)",
    )
    parser.add_argument(
        "--source",
        choices=["arxiv", "hn", "sec-edgar", "ssrn", "nber", "pubmed", "semantic-scholar", "all"],
        default="all",
        help="Which source to fetch from (default: all)",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Look back N days for content (default: 7)",
    )
    parser.add_argument(
        "--max-per-source",
        type=int,
        default=0,
        help="Override default per-source result limits (0 = use defaults)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview new items without writing to registry",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed per-item and per-pillar output",
    )
    parser.add_argument(
        "--enrich",
        action="store_true",
        help="Run enrich.py after ingestion",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(message)s")

    logger.info("=" * 60)
    logger.info("MULTI-PILLAR KNOWLEDGE INGESTION")
    logger.info("=" * 60)
    logger.info(f"Pillar: {args.pillar} | Source: {args.source} | Lookback: {args.days}d")
    if args.dry_run:
        logger.info("DRY RUN — no changes will be written")
    logger.info("")

    # Resolve pillars to process
    pillar_keys = list(PILLAR_CONFIGS) if args.pillar == "all" else [args.pillar]
    configs = [PILLAR_CONFIGS[k] for k in pillar_keys]

    # 1. Fetch for each pillar (parallel)
    all_new_items: list[dict] = []
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = {
            pool.submit(
                ingest_pillar, cfg, args.source, args.days, args.verbose, args.dry_run,
                args.max_per_source,
            ): cfg.slug_name
            for cfg in configs
        }
        for future in as_completed(futures):
            pillar_key = futures[future]
            try:
                items = future.result()
                all_new_items.extend(items)
            except Exception as e:
                logger.error(f"  [ERROR] {pillar_key}: {e}")

    if not all_new_items:
        logger.info("\nNo new content candidates found.")
        return 0

    logger.info(f"\nTotal raw candidates: {len(all_new_items)}")

    # 2. Deduplicate
    registry = load_registry()
    new_items = deduplicate(all_new_items, registry)

    logger.info(f"New items to ingest: {len(new_items)}")

    if not new_items:
        logger.info("\nNothing new to ingest.")
        return 0

    # 3. Validate via Pydantic schema
    validated: list[dict] = []
    errors = 0
    for item in new_items:
        try:
            IngestedItem(**item)
            validated.append(item)
        except Exception as e:
            errors += 1
            if args.verbose:
                logger.debug(f"  [schema error] {item.get('slug', '?')}: {e}")
    if errors:
        logger.info(f"  Schema validation: {errors} items dropped, {len(validated)} passed")

    if not validated:
        logger.info("\nNo items passed schema validation.")
        return 0

    # 4. Ontology concept extraction
    ontology = OntologyManager.load(ONTOLOGY_PATH)
    if ontology.concept_count() == 0:
        logger.info("  Seeding ontology with canonical concepts...")
        ontology.seed_all_pillars()
        ontology.seed_relations()
    associations = extract_and_store_concepts(validated, ontology)
    if associations:
        logger.info(f"  Ontology: {associations} concept associations extracted")

    # 4b. Cross-pillar analog auto-population
    if not args.dry_run:
        analogs = ontology.auto_populate_cross_pillar_analogs()
        if analogs:
            logger.info(f"  Cross-pillar analogs: {analogs} links populated")

    ontology.save(ONTOLOGY_PATH)

    # 5. Report
    if args.verbose or args.dry_run:
        logger.info("")
        logger.info("─" * 60)
        logger.info("NEW ITEMS PREVIEW")
        logger.info("─" * 60)
        for i, item in enumerate(validated, 1):
            sb = item.get("source_breakdown", {})
            src = "arxiv" if sb.get("arxiv") else "hn" if sb.get("hn") else "sec-edgar" if sb.get("sec-edgar") else "ssrn" if sb.get("ssrn") else "nber" if sb.get("nber") else "pubmed" if sb.get("pubmed") else "semantic-scholar"
            concepts = item.get("extracted_concepts", [])
            logger.debug(f"\n  [{i}] {item['slug']}")
            logger.debug(f"      Pillar: {item['pillar']} | Source: {src}")
            logger.debug(f"      Title: {item['title'][:80]}")
            logger.debug(f"      Tags:   {', '.join(item['tags'][:5])}")
            if concepts:
                logger.debug(f"      Concepts: {', '.join(concepts[:5])}")
            logger.debug(f"      URL:    {item.get('source_url', 'N/A')[:60]}")

    # 6. Ingest
    if not args.dry_run:
        content = registry.setdefault("content", [])
        content.extend(validated)

        # 6b. Prune + archive if over limit
        pruned = prune_and_archive_registry(registry)
        if pruned:
            logger.info(f"  Pruned {pruned} old items (archived to data/registry_archive/)")

        save_registry(registry)

        # Pillar counts
        pillar_counts: dict[str, int] = {}
        for c in content:
            p = c.get("pillar", "unknown")
            pillar_counts[p] = pillar_counts.get(p, 0) + 1

        logger.info("")
        logger.info("✓" * 60)
        logger.info(f"Ingested {len(validated)} new items into {REGISTRY_PATH}")
        logger.info("")
        logger.info("Pillar distribution:")
        total = len(content)
        for p in sorted(pillar_counts):
            pct = pillar_counts[p] / total * 100
            bar = "█" * int(pct / 2) + "░" * (50 - int(pct / 2))
            logger.info(f"  {p:20s} {pillar_counts[p]:3d} ({pct:5.1f}%) {bar}")
        logger.info(f"{'TOTAL':20s} {total:3d}")

        # 7. Run enrich.py if requested
        if args.enrich:
            logger.info("")
            logger.info("─" * 60)
            logger.info("Running enrichment pipeline...")
            enrich_script = ROOT / "scripts" / "enrich.py"
            if enrich_script.exists():
                result = subprocess.run(
                    [sys.executable, str(enrich_script)],
                    cwd=ROOT,
                    capture_output=True,
                    text=True,
                )
                logger.info(result.stdout)
                if result.returncode != 0:
                    logger.info(f"Enrichment warning: {result.stderr}")
            else:
                logger.info(f"  enrich.py not found at {enrich_script}")

        logger.info("")
        logger.info("Done. Run `python build.py` to rebuild the site.")
    else:
        logger.info("")
        logger.info("DRY RUN — no changes written.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
