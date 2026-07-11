#!/usr/bin/env python3
"""AML Content Ingestion Drive — automated staging pipeline.

Fetches AML-specific content from arXiv and HackerNews, generates structured
content items matching the registry.json schema, deduplicates against existing
items, and merges new entries into the registry.

Usage:
    python3 scripts/aml_ingester.py                     # Full run
    python3 scripts/aml_ingester.py --dry-run           # Preview only
    python3 scripts/aml_ingester.py --source arxiv      # Only arXiv
    python3 scripts/aml_ingester.py --source hn         # Only HN
    python3 scripts/aml_ingester.py --days 14           # Look back 14 days
    python3 scripts/aml_ingester.py --enrich            # Also run enrich.py after
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

REGISTRY_PATH = ROOT / "registry.json"

# ── AML Keyword Inventory ──────────────────────────────────────────────

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

ALL_AML_KEYWORDS: list[str] = sorted({
    kw for kw_list in AML_TAGS.values()
    for p in kw_list
    for kw in p.replace(r"\b", "").split(r"\b")
    if kw and len(kw) > 2
})

# ── Slug Helpers ───────────────────────────────────────────────────────

_SLUG_CLEAN = re.compile(r"[^a-z0-9-]+")
_MULTI_DASH = re.compile(r"-{2,}")


def _slugify(text: str, max_len: int = 60) -> str:
    s = text.lower()
    s = s.replace("'", "").replace('"', "")
    s = _SLUG_CLEAN.sub("-", s).strip("-")
    s = _MULTI_DASH.sub("-", s)
    return s[:max_len].rstrip("-")


def _existing_slugs(registry_data: dict) -> set[str]:
    return {c.get("slug", "") for c in registry_data.get("content", []) if c.get("slug")}


def _existing_urls(registry_data: dict) -> set[str]:
    """Collect all source URLs from existing content items."""
    urls = set()
    for c in registry_data.get("content", []):
        if c.get("source_url"):
            urls.add(c["source_url"].rstrip("/"))
        for s in (c.get("signals") or {}).get("top_entities", []):
            if s.startswith("http"):
                urls.add(s.rstrip("/"))
    return urls


# ── AML Relevance Scoring ──────────────────────────────────────────────


def _score_aml_relevance(
    text: str,
    categories: list[str] | None = None,
) -> float:
    """Score text for AML relevance (0.0–1.0).

    Combines:
      - Category-based score: arXiv categories in q-fin.*/cs.CR get a baseline
      - Keyword density: AML keyword hits normalized by text length
    """
    lower = text.lower()
    hits = 0
    for tag, patterns in AML_TAGS.items():
        for p in patterns:
            if re.search(p, lower):
                hits += 1

    # Category baseline for arXiv papers (only contributes if keywords present)
    category_bonus = 0.0
    if categories:
        aml_cats = {"cr", "cy", "ir", "si", "gt"}
        fin_cats = {"q-fin.gn", "q-fin.rm", "q-fin.pm", "q-fin.ec",
                     "q-fin.st", "q-fin.cp", "q-fin.tr", "q-fin.mf"}
        for cat in categories:
            cat_lower = cat.lower()
            if cat_lower in aml_cats:
                category_bonus = max(category_bonus, 0.12)
            if cat_lower in fin_cats:
                category_bonus = max(category_bonus, 0.15)

    if hits == 0:
        return 0.0

    word_count = len(lower.split())
    density = hits / max(word_count, 10)
    kw_score = min(1.0, density * 10)

    # Keyword score dominates; category provides a small boost
    score = kw_score * 1.5 + category_bonus
    return min(1.0, score)


def _detect_aml_tags(title: str, description: str) -> list[str]:
    """Detect AML-specific tags from title + description."""
    combined = f"{title} {description}".lower()
    detected: list[str] = []
    for tag, patterns in AML_TAGS.items():
        for p in patterns:
            if re.search(p, combined):
                detected.append(tag)
                break

    # Always include base "aml" if any tag matched
    if detected and "aml" not in detected:
        detected.insert(0, "aml")

    return detected[:6]


# ── ArXiv → Content Item ───────────────────────────────────────────────


def _arxiv_to_item(paper: dict, source_date: str) -> dict[str, Any] | None:
    """Convert an arXiv paper dict into a registry content item."""
    title = (paper.get("title") or "").strip()
    abstract = (paper.get("abstract") or "").strip()
    url = (paper.get("url") or "").strip()
    published = (paper.get("published") or source_date).strip()

    if not title or not abstract:
        return None

    categories = paper.get("categories") or []
    aml_score = _score_aml_relevance(f"{title} {abstract}", categories)
    if aml_score < 0.15:
        return None

    slug_date = published[:10] if published else datetime.now(timezone.utc).strftime("%Y-%m-%d")
    slug_base = _slugify(title)
    slug = f"aml/research/{slug_base}"

    tags = ["aml"] + _detect_aml_tags(title, abstract)
    tags = list(dict.fromkeys(tags))  # deduplicate preserving order

    # Build body_html from abstract
    body_html = f"<p>{abstract}</p>"
    description = abstract[:300].rstrip() + ("..." if len(abstract) > 300 else "")

    now_iso = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    item: dict[str, Any] = {
        "slug": slug,
        "language": "en",
        "title": title,
        "description": description,
        "body_html": body_html,
        "category": "blog",
        "content_type": "research",
        "tags": tags,
        "pillar": "aml",
        "date_str": slug_date,
        "created_at": published,
        "updated_at": now_iso,
        "author": paper.get("author", "Leszek"),
        "source_url": url,
        "source_breakdown": {"arxiv": 1},
        "signals": {
            "avg_sqi": 0.75,
            "count": 1,
            "total_score": 0,
            "avg_score": 0,
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

    # Generate unique slug if slug already exists (will be checked later)
    return item


# ── HackerNews → Content Item ──────────────────────────────────────────


def _hn_to_item(story: dict) -> dict[str, Any] | None:
    """Convert an HN story dict into a registry content item."""
    title = (story.get("title") or "").strip()
    url = (story.get("url") or "").strip()
    hn_url = (story.get("hn_url") or "").strip()
    points = story.get("points", 0) or 0
    author = story.get("author", "anonymous")
    created_at = story.get("created_at", "")
    object_id = story.get("object_id", "")

    if not title:
        return None

    aml_score = _score_aml_relevance(title)
    if aml_score < 0.20:
        return None

    slug_date = created_at[:10] if created_at else datetime.now(timezone.utc).strftime("%Y-%m-%d")
    slug_base = _slugify(title)
    slug = f"aml/research/{slug_base}"

    tags = ["aml"] + _detect_aml_tags(title, "")
    tags = list(dict.fromkeys(tags))

    description = f"HackerNews discussion ({points} points) about {title[:120]}."
    body_html = f"<p>HackerNews discussion: <a href='{hn_url}'>{title}</a></p>"
    body_html += f"<p>Score: {points} points by {author}.</p>"
    if url and url != hn_url:
        body_html += f"<p>Source: <a href='{url}'>{url[:80]}</a></p>"

    now_iso = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    item: dict[str, Any] = {
        "slug": slug,
        "language": "en",
        "title": title,
        "description": description,
        "body_html": body_html,
        "category": "blog",
        "content_type": "research",
        "tags": tags,
        "pillar": "aml",
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

    return item


# ── Fetch Sources ──────────────────────────────────────────────────────


def fetch_arxiv_aml(
    days_back: int = 7,
    max_results: int = 80,
) -> list[dict[str, Any]]:
    """Fetch arXiv papers classified under AML and filter for AML relevance."""
    from core.fetch import fetch_arxiv, ARXIV_CATEGORIES

    print(f"  Fetching arXiv (categories: {ARXIV_CATEGORIES['aml']})...")
    papers = fetch_arxiv(since_hours=days_back * 24, max_results=max_results)
    print(f"  arXiv returned {len(papers)} total papers")

    # Score ALL papers for AML relevance (arXiv's own pillar classifier is noisy
    # — many cs.CR/cs.CY papers get tagged as AML but have zero AML content)
    relevant = []
    for p in papers:
        title = p.get("title", "")
        abstract = p.get("abstract", "")
        cats = p.get("categories") or []
        aml_score = _score_aml_relevance(f"{title} {abstract}", cats)
        if aml_score >= 0.15:
            p["aml_score"] = round(aml_score, 3)
            p["pillar"] = "aml"  # Override pillar to AML
            relevant.append(p)

    relevant.sort(key=lambda p: p["aml_score"], reverse=True)
    print(f"  AML-relevant (score >= 0.15): {len(relevant)}")
    for p in relevant[:3]:
        print(f"    [{p.get('aml_score', 0):.2f}] {p.get('title', '')[:70]}")
    return relevant


def fetch_hn_aml(
    days_back: int = 7,
    min_points: int = 3,
    max_hits: int = 200,
) -> list[dict[str, Any]]:
    """Fetch HN stories and filter for AML/financial crime keywords."""
    from core.fetch import fetch_hn_stories

    print(f"  Fetching HN (last {days_back} days, min {min_points} pts)...")
    stories = fetch_hn_stories(
        since_hours=days_back * 24,
        min_points=min_points,
        max_hits=max_hits,
    )
    print(f"  HN returned {len(stories)} stories")

    # AML keyword filter
    aml_keywords_lower = [kw.lower() for kw in ALL_AML_KEYWORDS if len(kw) > 3]
    relevant = []
    for s in stories:
        title = s.get("title", "")
        aml_score = _score_aml_relevance(title)
        if aml_score >= 0.20:
            s["aml_score"] = round(aml_score, 3)
            relevant.append(s)

    relevant.sort(key=lambda s: s["aml_score"], reverse=True)
    print(f"  AML-relevant (score >= 0.20): {len(relevant)}")
    return relevant


# ── Deduplication ──────────────────────────────────────────────────────


def find_duplicates(items: list[dict], existing: dict) -> list[dict]:
    """Filter out items that already exist in the registry.

    Checks by:
      1. slug match
      2. source_url match
      3. title similarity (exact title match)
    """
    existing_slugs = _existing_slugs(existing)
    existing_urls = _existing_urls(existing)
    existing_titles = {
        c.get("title", "").strip().lower()
        for c in existing.get("content", [])
        if c.get("title")
    }

    new_items: list[dict] = []
    duplicates = 0
    for item in items:
        slug = item.get("slug", "")
        source_url = item.get("source_url", "").rstrip("/")
        title = item.get("title", "").strip().lower()

        if slug in existing_slugs:
            duplicates += 1
            continue
        if source_url and source_url in existing_urls:
            duplicates += 1
            continue
        if title and title in existing_titles:
            duplicates += 1
            continue

        # Unique slug — but if there's a slug collision, add a suffix
        if slug in {i.get("slug") for i in new_items}:
            uid = uuid.uuid4().hex[:6]
            slug = f"{slug}-{uid}"
            item["slug"] = slug

        new_items.append(item)

    if duplicates:
        print(f"  Skipped {duplicates} duplicates (already in registry)")
    return new_items


# ── Registry I/O ───────────────────────────────────────────────────────


def load_registry() -> dict:
    if not REGISTRY_PATH.exists():
        print(f"Error: {REGISTRY_PATH} not found")
        sys.exit(1)
    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_registry(reg: dict) -> None:
    from core.registry_io import save_registry as _atomic_save
    _atomic_save(reg, REGISTRY_PATH)


# ── Merge ──────────────────────────────────────────────────────────────


def merge_items(
    registry: dict,
    new_items: list[dict],
) -> int:
    """Append new items to registry content list."""
    content = registry.setdefault("content", [])
    content.extend(new_items)
    return len(new_items)


# ── Main ───────────────────────────────────────────────────────────────


def main() -> int:
    parser = argparse.ArgumentParser(
        description="AML Content Ingestion Drive — automated staging pipeline",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview new items without writing to registry",
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
        "--min-score",
        type=float,
        default=0.15,
        help="Minimum AML relevance score (default: 0.15)",
    )
    parser.add_argument(
        "--enrich",
        action="store_true",
        help="Run enrich.py after ingestion",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed per-item output",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("AML CONTENT INGESTION DRIVE")
    print("=" * 60)
    print(f"Lookback: {args.days} days | Source: {args.source}")
    if args.dry_run:
        print("DRY RUN — no changes will be written")
    print()

    # 1. Fetch
    all_candidates: list[dict] = []
    items: list[dict] = []

    if args.source in ("arxiv", "all"):
        arxiv_papers = fetch_arxiv_aml(days_back=args.days)
        for p in arxiv_papers:
            item = _arxiv_to_item(p, "")
            if item is not None:
                items.append(item)
        print(f"  → {len(items)} arXiv items generated")

    if args.source in ("hn", "all"):
        hn_stories = fetch_hn_aml(days_back=args.days)
        hn_items_before = len(items)
        for s in hn_stories:
            item = _hn_to_item(s)
            if item is not None:
                items.append(item)
        print(f"  → {len(items) - hn_items_before} HN items generated")

    if not items:
        print("\nNo new AML content candidates found.")
        return 0

    print()
    print(f"Total candidates: {len(items)}")

    # 2. Deduplicate against registry
    registry = load_registry()
    new_items = find_duplicates(items, registry)

    print(f"New items to ingest: {len(new_items)}")

    if not new_items:
        print("\nNothing new to ingest.")
        return 0

    # 3. Report
    if args.verbose or args.dry_run:
        print()
        print("─" * 60)
        print("NEW ITEMS PREVIEW")
        print("─" * 60)
        for i, item in enumerate(new_items, 1):
            print(f"\n  [{i}] {item['slug']}")
            print(f"      Title: {item['title'][:80]}")
            print(f"      Tags:   {', '.join(item['tags'])}")
            print(f"      Source: {item.get('source_url', 'N/A')[:70]}")
            print(f"      Date:   {item['date_str']}")

    # 4. Ingest
    if not args.dry_run:
        merged_count = merge_items(registry, new_items)
        save_registry(registry)

        # Pillar counts
        content = registry.get("content", [])
        pillar_counts: dict[str, int] = {}
        for c in content:
            p = c.get("pillar", "unknown")
            pillar_counts[p] = pillar_counts.get(p, 0) + 1

        print()
        print("✓" * 60)
        print(f"Ingested {merged_count} new AML items into {REGISTRY_PATH}")
        print()
        print("Pillar distribution:")
        total = len(content)
        for p in sorted(pillar_counts):
            pct = pillar_counts[p] / total * 100
            bar = "█" * int(pct / 2) + "░" * (50 - int(pct / 2))
            print(f"  {p:20s} {pillar_counts[p]:3d} ({pct:5.1f}%) {bar}")
        print(f"{'TOTAL':20s} {total:3d}")

        # 5. Run enrich.py if requested
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
