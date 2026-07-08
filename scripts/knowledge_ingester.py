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
import math
import re
import subprocess
import sys
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

REGISTRY_PATH = ROOT / "registry.json"

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
    ],
    "systemic-risk": [
        r"\bsystemic.risk", r"\bcounterparty.risk", r"\bnbfi\b",
        r"\bnon.bank.financ", r"\bcontagion\b", r"\bfinancial.stability\b",
    ],
    "quantitative-modeling": [
        r"\bregime.switch", r"\bbayesian\b", r"\bcorrelation\b",
        r"\bvolatility\b", r"\barbitrage\b", r"\bcross.asset\b",
    ],
    "macro-finance": [
        r"\bmacroeconomic\b", r"\bmonetary.polic", r"\binflation\b",
        r"\byield.curve\b", r"\bfiscal\b", r"\bcentral.bank\b",
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


def jaccard_similarity(a: str, b: str) -> float:
    """Token-level Jaccard similarity using word-boundary tokenization."""
    words1 = set(re.findall(r"\b\w+\b", a.lower()))
    words2 = set(re.findall(r"\b\w+\b", b.lower()))
    if not words1 or not words2:
        return 0.0
    return len(words1 & words2) / len(words1 | words2)


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
        print(f"  arXiv returned {len(papers)} total papers")

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
        print(f"  {config.slug_name}-relevant (score >= {threshold}): {len(relevant)}")
        for p in relevant[:3]:
            print(f"    [{p['_relevance_score']:.2f}] {p.get('title', '')[:70]}")
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
        print(f"  HN returned {len(stories)} stories")

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
        print(f"  {config.slug_name}-relevant (score >= {threshold}): {len(relevant)}")
    return relevant


# =========================================================================
# Source → Registry Item converters
# =========================================================================


def _arxiv_to_item(paper: dict, config: PillarConfig) -> dict[str, Any] | None:
    """Convert arXiv paper dict into a registry content item."""
    title = (paper.get("title") or "").strip()
    abstract = (paper.get("abstract") or "").strip()
    url = (paper.get("url") or "").strip()
    published = (paper.get("published") or "").strip()

    if not title or not abstract:
        return None

    slug_date = published[:10] or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    slug_base = _slugify(title)
    slug = f"blog/{slug_date}-{slug_base}"

    pillar = config.slug_name
    tags = paper.get("_detected_tags", [])

    # Category-based fallback tags when keyword detection misses
    if not tags:
        cats = paper.get("categories") or []
        for cat in cats:
            cat_lower = cat.lower()
            if pillar == "data":
                if cat_lower == "cs.db":
                    tags.append("database-systems")
                elif cat_lower == "cs.dc":
                    tags.append("distributed-computing")
                elif cat_lower == "cs.se":
                    tags.append("software-engineering")
            elif pillar == "market":
                if cat_lower in ("q-fin.mf", "q-fin.tr"):
                    tags.append("market-microstructure")
                elif cat_lower == "econ.em":
                    tags.append("quantitative-modeling")
                elif cat_lower == "q-fin.cp":
                    tags.append("computational-finance")

    # Ensure base pillar tag exists
    if pillar == "aml" and "aml" not in tags:
        tags.insert(0, "aml")
    elif pillar == "data" and "dataops" not in tags:
        tags.insert(0, "dataops")
    elif pillar == "market" and "market-microstructure" not in tags:
        tags.insert(0, "market-microstructure")

    tags = list(dict.fromkeys(tags))

    body_html = f"<p>{abstract}</p>"
    description = abstract[:300].rstrip() + ("..." if len(abstract) > 300 else "")

    now_iso = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    return {
        "slug": slug,
        "title": title,
        "pillar": pillar,
        "content_type": "research",
        "tags": tags,
        "description": description,
        "body_html": body_html,
        "category": "blog",
        "language": "en",
        "date_str": slug_date,
        "created_at": published,
        "updated_at": now_iso,
        "author": "Leszek",
        "source_url": url,
        "source_breakdown": {"arxiv": 1},
        "signals": {
            "avg_sqi": 0.75,
            "count": 1,
            "domain_diversity": len(tags),
            "top_entities": [url],
        },
        "quality_metrics": {
            "score": 0.75,
            "source_verified": True,
            "evidence_level": "Unknown",
            "trend_strength": 50.0,
            "adoption_level": "emerging",
        },
        "sqi": None,
        "enriched": False,
        "lineage": {},
        "quality_flags": [],
        "section_images": [],
        "difficulty": "",
    }


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

    slug_date = created_at[:10] or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    slug_base = _slugify(title)
    slug = f"blog/{slug_date}-{slug_base}"

    pillar = config.slug_name
    tags = story.get("_detected_tags", [])
    if pillar == "aml" and "aml" not in tags:
        tags.insert(0, "aml")
    elif pillar == "data" and "dataops" not in tags:
        tags.insert(0, "dataops")
    elif pillar == "market" and "market-microstructure" not in tags:
        tags.insert(0, "market-microstructure")
    tags = list(dict.fromkeys(tags))

    description = f"HackerNews discussion ({points} points) about {title[:120]}."
    body_html = f"<p>HackerNews discussion: <a href='{hn_url}'>{title}</a></p>"
    body_html += f"<p>Score: {points} points by {author}.</p>"
    if url and url != hn_url:
        body_html += f"<p>Source: <a href='{url}'>{url[:80]}</a></p>"

    now_iso = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    return {
        "slug": slug,
        "title": title,
        "pillar": pillar,
        "content_type": "research",
        "tags": tags,
        "description": description,
        "body_html": body_html,
        "category": "blog",
        "language": "en",
        "date_str": slug_date,
        "created_at": created_at or now_iso,
        "updated_at": now_iso,
        "author": author,
        "source_url": hn_url,
        "source_breakdown": {"hn": 1},
        "signals": {
            "avg_sqi": 0.55,
            "count": points,
            "total_score": points * 100,
            "avg_score": float(points),
            "domain_diversity": len(tags),
            "top_entities": [hn_url],
        },
        "quality_metrics": {
            "score": min(0.95, 0.45 + (points / 1000)),
            "source_verified": True,
            "evidence_level": "Unknown",
            "trend_strength": min(100.0, points),
            "adoption_level": "emerging",
        },
        "sqi": None,
        "enriched": False,
        "lineage": {},
        "quality_flags": [],
        "section_images": [],
        "difficulty": "",
    }


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
      1. Slug match
      2. Source URL match
      3. Exact title match
      4. Jaccard similarity ≥ 0.93 (near-duplicate title)
    """
    existing_slugs_set = _existing_slugs(registry_data)
    existing_urls_set = _existing_urls(registry_data)
    existing_titles_list = _existing_titles(registry_data)

    new_items: list[dict] = []
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
        if title and title in existing_titles_list:
            duplicates += 1
            continue

        # Jaccard similarity check against all existing titles
        is_duplicate = False
        if title:
            for et in existing_titles_list:
                if jaccard_similarity(title, et) >= 0.93:
                    duplicates += 1
                    is_duplicate = True
                    break
        if is_duplicate:
            continue

        # Slug collision within batch
        if slug in {i.get("slug") for i in new_items}:
            uid = uuid.uuid4().hex[:6]
            item["slug"] = f"{slug}-{uid}"

        new_items.append(item)

    if duplicates:
        print(f"  Skipped {duplicates} duplicates (slug/URL/title/Jaccard≥0.93)")
    return new_items


# =========================================================================
# Registry I/O
# =========================================================================


def load_registry() -> dict:
    if not REGISTRY_PATH.exists():
        print(f"Error: {REGISTRY_PATH} not found")
        sys.exit(1)
    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_registry(reg: dict) -> None:
    from core.registry_io import save_registry as _atomic_save
    _atomic_save(reg, REGISTRY_PATH)


# =========================================================================
# Per-pillar ingestion
# =========================================================================


def ingest_pillar(
    config: PillarConfig,
    source: str,
    days_back: int,
    verbose: bool,
    dry_run: bool,
) -> list[dict]:
    """Fetch, score, convert items for one pillar. Returns new items."""
    items: list[dict] = []

    if verbose:
        print(f"\n  ── {config.label} ({config.slug_name}) ──")

    if source in ("arxiv", "all"):
        papers = fetch_arxiv_for_pillar(config, days_back, verbose=verbose)
        for p in papers:
            item = _arxiv_to_item(p, config)
            if item is not None:
                items.append(item)
        if verbose:
            print(f"  → {sum(1 for i in items if i.get('source_breakdown', {}).get('arxiv'))} arXiv items for {config.slug_name}")

    if source in ("hn", "all"):
        stories = fetch_hn_for_pillar(config, days_back, verbose=verbose)
        for s in stories:
            item = _hn_to_item(s, config)
            if item is not None:
                items.append(item)
        if verbose:
            hn_count = sum(1 for i in items if i.get('source_breakdown', {}).get('hn'))
            print(f"  → {hn_count} HN items for {config.slug_name}")

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
        choices=["arxiv", "hn", "all"],
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

    print("=" * 60)
    print("MULTI-PILLAR KNOWLEDGE INGESTION")
    print("=" * 60)
    print(f"Pillar: {args.pillar} | Source: {args.source} | Lookback: {args.days}d")
    if args.dry_run:
        print("DRY RUN — no changes will be written")
    print()

    # Resolve pillars to process
    pillar_keys = list(PILLAR_CONFIGS) if args.pillar == "all" else [args.pillar]
    configs = [PILLAR_CONFIGS[k] for k in pillar_keys]

    # 1. Fetch for each pillar
    all_new_items: list[dict] = []
    for cfg in configs:
        items = ingest_pillar(cfg, args.source, args.days, args.verbose, args.dry_run)
        all_new_items.extend(items)

    if not all_new_items:
        print("\nNo new content candidates found.")
        return 0

    print(f"\nTotal raw candidates: {len(all_new_items)}")

    # 2. Deduplicate
    registry = load_registry()
    new_items = deduplicate(all_new_items, registry)

    print(f"New items to ingest: {len(new_items)}")

    if not new_items:
        print("\nNothing new to ingest.")
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
                print(f"  [schema error] {item.get('slug', '?')}: {e}")
    if errors:
        print(f"  Schema validation: {errors} items dropped, {len(validated)} passed")

    if not validated:
        print("\nNo items passed schema validation.")
        return 0

    # 4. Report
    if args.verbose or args.dry_run:
        print()
        print("─" * 60)
        print("NEW ITEMS PREVIEW")
        print("─" * 60)
        for i, item in enumerate(validated, 1):
            src = "arxiv" if item.get("source_breakdown", {}).get("arxiv") else "hn"
            print(f"\n  [{i}] {item['slug']}")
            print(f"      Pillar: {item['pillar']} | Source: {src}")
            print(f"      Title: {item['title'][:80]}")
            print(f"      Tags:   {', '.join(item['tags'][:5])}")
            print(f"      URL:    {item.get('source_url', 'N/A')[:60]}")

    # 5. Ingest
    if not args.dry_run:
        content = registry.setdefault("content", [])
        content.extend(validated)
        save_registry(registry)

        # Pillar counts
        pillar_counts: dict[str, int] = {}
        for c in content:
            p = c.get("pillar", "unknown")
            pillar_counts[p] = pillar_counts.get(p, 0) + 1

        print()
        print("✓" * 60)
        print(f"Ingested {len(validated)} new items into {REGISTRY_PATH}")
        print()
        print("Pillar distribution:")
        total = len(content)
        for p in sorted(pillar_counts):
            pct = pillar_counts[p] / total * 100
            bar = "█" * int(pct / 2) + "░" * (50 - int(pct / 2))
            print(f"  {p:20s} {pillar_counts[p]:3d} ({pct:5.1f}%) {bar}")
        print(f"{'TOTAL':20s} {total:3d}")

        # 6. Run enrich.py if requested
        if args.enrich:
            print()
            print("─" * 60)
            print("Running enrichment pipeline...")
            enrich_script = ROOT / "scripts" / "enrich.py"
            if enrich_script.exists():
                result = subprocess.run(
                    [sys.executable, str(enrich_script)],
                    cwd=ROOT,
                    capture_output=True,
                    text=True,
                )
                print(result.stdout)
                if result.returncode != 0:
                    print(f"Enrichment warning: {result.stderr}")
            else:
                print(f"  enrich.py not found at {enrich_script}")

        print()
        print("Done. Run `python build.py` to rebuild the site.")
    else:
        print()
        print("DRY RUN — no changes written.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
