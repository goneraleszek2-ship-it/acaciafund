#!/usr/bin/env python3
"""Content gap filler for AcaciaFund.

Generates learn/knowledge content for underserved pillar slots
using either LLM inference or deterministic templates.

Usage:
    python3 scripts/generate_content.py                          # Template mode
    python3 scripts/generate_content.py --infer                  # LLM mode (requires NVIDIA_API_KEY)
    python3 scripts/generate_content.py --infer --dry-run        # Preview only
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import random
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger("acaciafund.generate")
logging.basicConfig(level=logging.WARNING, format="%(levelname)s:%(name)s:%(message)s")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

REGISTRY_PATH = ROOT / "registry.json"

# Pillar URL mapping (internal key → URL segment)
from config import PILLAR_URL_MAP

# Target counts per (type, pillar) after generation
TARGETS: dict[tuple[str, str], int] = {
    ("learn", "aml"): 15,
    ("learn", "data-engineering"): 15,
    ("learn", "stock"): 15,
    ("knowledge", "aml"): 12,
    ("knowledge", "data-engineering"): 15,
    ("knowledge", "stock"): 10,
}

# ── Pillar metadata for generation ──
PILLAR_INFO: dict[str, dict[str, Any]] = {
    "aml": {
        "label": "Compliance & Financial Crime",
        "topics": [
            "beneficial ownership transparency",
            "SAR filing best practices",
            "transaction monitoring optimization",
            "AI in AML compliance",
            "regulatory technology landscape",
            "cross-border financial intelligence",
            "cryptocurrency AML challenges",
            "trade-based money laundering detection",
        ],
        "keywords": [
            "aml", "financial-crime", "compliance", "regtech",
            "transaction-monitoring", "financial-intelligence",
        ],
    },
    "data-engineering": {
        "label": "Data Engineering & Infrastructure",
        "topics": [
            "data pipeline orchestration",
            "real-time streaming architectures",
            "data quality frameworks",
            "data lakehouse patterns",
            "schema evolution strategies",
            "event-driven data mesh",
            "observability in data systems",
        ],
        "keywords": [
            "dataops", "data-architecture", "streaming", "orchestration",
            "data-governance", "observability",
        ],
    },
    "stock": {
        "label": "Markets & Industry",
        "topics": [
            "semiconductor supply chain analysis",
            "AI hardware trends",
            "market volatility patterns",
            "commodity trading strategies",
            "earnings analysis frameworks",
            "industrial automation trends",
        ],
        "keywords": [
            "markets", "risk-management", "supply-chain", "manufacturing",
            "corporate-finance", "macro-economics",
        ],
    },
}

CONTENT_TYPE_TOPIC_ADJECTIVES: dict[str, list[str]] = {
    "learn": ["introduction to", "guide to", "understanding", "mastering", "practical"],
    "knowledge": ["deep dive into", "reference: ", "the complete guide to", "foundations of", "encyclopedia entry: "],
}

CONTENT_TYPE_SECTIONS: dict[str, list[str]] = {
    "learn": [
        "Introduction",
        "Core Concepts",
        "Step-by-Step Approach",
        "Best Practices",
        "Common Pitfalls",
        "Summary",
    ],
    "knowledge": [
        "Overview",
        "Key Principles",
        "Detailed Analysis",
        "Real-World Applications",
        "Related Concepts",
        "References",
    ],
}


def load_registry() -> dict:
    if not REGISTRY_PATH.exists():
        print(f"Error: {REGISTRY_PATH} not found.")
        sys.exit(1)
    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_registry(reg: dict) -> None:
    from core.registry_io import save_registry as _atomic_save
    _atomic_save(reg, REGISTRY_PATH)


def _pillar_topic_slug(topic: str) -> str:
    """Convert a topic phrase to a URL-safe slug segment."""
    s = topic.lower().strip()
    s = re.sub(r"[^a-z0-9\s-]", "", s)
    s = re.sub(r"\s+", "-", s)
    s = re.sub(r"-+", "-", s)
    return s[:40].rstrip("-")


def _tag_slug(tag: str) -> str:
    """Ensure tag is valid kebab-case."""
    s = tag.lower().strip()
    s = re.sub(r"[^a-z0-9-]", "-", s)
    s = re.sub(r"-+", "-", s)
    return s.strip("-")


def _generate_deterministic_item(
    content_type: str,
    pillar: str,
    topic: str,
    seed_item: dict | None = None,
) -> dict:
    """Generate a content item using deterministic templates."""
    info = PILLAR_INFO[pillar]
    adjectives = CONTENT_TYPE_TOPIC_ADJECTIVES[content_type]
    sections = CONTENT_TYPE_SECTIONS[content_type]
    adjective = random.choice(adjectives)

    if content_type == "knowledge" and ":" in adjective:
        title = f"{adjective.replace(': ', '')}{topic.title()}"
    else:
        title = f"{adjective.title()} {topic.title()}"

    slug_base = _pillar_topic_slug(topic)
    pillar_url = PILLAR_URL_MAP.get(pillar, pillar)
    slug = f"{pillar_url}/{content_type}/{slug_base}"

    description = (
        f"A {content_type} article exploring {topic} within the "
        f"{info['label']} domain. Covers core concepts, practical "
        f"applications, and key considerations."
    )

    body_parts: list[str] = []
    for i, section in enumerate(sections):
        body_parts.append(f"<h2>{section}</h2>")
        if i == 0:
            body_parts.append(
                f"<p>This {content_type} provides an overview of {topic} "
                f"in the context of {info['label']}. "
                f"Understanding these concepts is essential for practitioners "
                f"working in this domain.</p>"
            )
        else:
            body_parts.append(
                f"<p>Content about {section.lower()} for {topic}. "
                f"This section covers the key aspects and considerations "
                f"relevant to {pillar} professionals.</p>"
            )
            body_parts.append(
                f"<p>Practical implications include improved decision-making, "
                f"better risk assessment, and enhanced operational efficiency.</p>"
            )

    tags = list(info["keywords"])
    if seed_item:
        for t in (seed_item.get("tags") or []):
            st = _tag_slug(t)
            if st not in tags:
                tags.append(st)
    tags = tags[:10]

    item = {
        "slug": slug,
        "title": title,
        "description": description,
        "body_html": "\n".join(body_parts),
        "content_type": content_type,
        "pillar": pillar,
        "tags": tags,
        "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "date_str": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "enriched": False,
        "citations": [],
    }
    return item


def _generate_with_llm(
    content_type: str,
    pillar: str,
    topic: str,
    seed_item: dict | None,
    llm_client: Any,
    model: str,
) -> dict | None:
    """Generate a content item using LLM."""
    info = PILLAR_INFO[pillar]
    seed_context = ""
    if seed_item:
        seed_context = (
            f"Seed title: {seed_item.get('title', '')}\n"
            f"Seed description: {seed_item.get('description', '')}\n"
            f"Seed tags: {', '.join(seed_item.get('tags', [])[:8])}\n"
        )

    system_prompt = (
        "You are a subject matter expert creating educational content "
        f"for a {pillar} knowledge base. Generate a {content_type} article. "
        "Respond with ONLY valid JSON containing: "
        "title, description (2-3 sentences), body_html (with <h2> sections), "
        "and tags (3-8 kebab-case tags). "
        "Body must be structured with <h2>Introduction</h2>, "
        "<h2>Core Concepts</h2>, <h2>Key Takeaways</h2> and other relevant sections."
    )

    user_prompt = (
        f"Generate a {content_type} article about {topic} "
        f"for the {info['label']} pillar.\n\n"
        f"{seed_context}"
        "Return JSON: {\"title\": str, \"description\": str, "
        "\"body_html\": str, \"tags\": [str, ...]}"
    )

    try:
        response = llm_client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.6,
            max_tokens=1200,
            timeout=60,
        )
        raw = response.choices[0].message.content or ""
        cleaned = raw.strip()
        cleaned = re.sub(r"```(?:json)?\s*", "", cleaned).strip()
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start == -1 or end == -1:
            return None
        parsed = json.loads(cleaned[start:end+1])

        slug_base = _pillar_topic_slug(topic)
        pillar_url = PILLAR_URL_MAP.get(pillar, pillar)
        slug = f"{pillar_url}/{content_type}/{slug_base}"

        return {
            "slug": slug,
            "title": parsed.get("title", topic.title()),
            "description": parsed.get("description", ""),
            "body_html": parsed.get("body_html", ""),
            "content_type": content_type,
            "pillar": pillar,
            "tags": [_tag_slug(t) for t in (parsed.get("tags") or [])][:10],
            "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "date_str": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "enriched": False,
            "citations": [],
        }
    except Exception as e:
        logger.warning("LLM generation failed for %s/%s/%s: %s", content_type, pillar, topic, e)
        return None


def main() -> int:
    parser = argparse.ArgumentParser(description="AcaciaFund Content Gap Filler")
    parser.add_argument("--infer", action="store_true", help="Use LLM inference")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing")
    parser.add_argument("--verbose", "-v", action="store_true", help="Detailed output")
    args = parser.parse_args()

    reg = load_registry()
    items: list[dict] = reg.get("content", [])
    print(f"Loaded {len(items)} items")

    # Count current distribution
    counts: dict[tuple[str, str], int] = Counter()
    for item in items:
        t = item.get("content_type", "")
        p = item.get("pillar", "")
        counts[(t, p)] += 1

    print(f"\nCurrent distribution:")
    for (t, p), c in sorted(counts.items()):
        print(f"  {t:12s} / {p:20s}: {c}")

    # Determine gaps
    gaps: list[tuple[str, str, int]] = []
    for (t, p), target in sorted(TARGETS.items()):
        have = counts.get((t, p), 0)
        if have < target:
            gaps.append((t, p, target - have))

    if not gaps:
        print("\nNo gaps to fill!")
        return 0

    print(f"\nGaps to fill: {sum(d for _, _, d in gaps)} items")
    for t, p, delta in gaps:
        print(f"  {t:12s} / {p:20s}: +{delta} (have {counts.get((t,p), 0)}, target {TARGETS[(t,p)]})")

    # Initialize LLM if requested
    llm_client = None
    llm_model = None
    if args.infer:
        api_key = os.environ.get("NVIDIA_API_KEY") or os.environ.get("OPENAI_API_KEY") or ""
        if api_key:
            try:
                from openai import OpenAI
                llm_client = OpenAI(api_key=api_key, base_url="https://integrate.api.nvidia.com/v1")
                llm_model = "meta/llama-3.1-70b-instruct"
                print("\nLLM mode enabled")
            except ImportError:
                print("\nWarning: openai package not installed, falling back to deterministic")
                args.infer = False
        else:
            print("\nWarning: No API key found, falling back to deterministic")
            args.infer = False

    # Find good seed items per pillar (high SQI research)
    pillar_seeds: dict[str, list[dict]] = {}
    for item in items:
        p = item.get("pillar", "")
        if item.get("content_type") == "research" and item.get("sqi", 0) and item["sqi"] >= 0.7:
            pillar_seeds.setdefault(p, []).append(item)
    for p in pillar_seeds:
        pillar_seeds[p].sort(key=lambda x: x.get("sqi", 0), reverse=True)

    # Generate content for each gap
    generated: list[dict] = []
    seen_slugs = {item["slug"] for item in items}

    for content_type, pillar, needed in gaps:
        info = PILLAR_INFO[pillar]
        seeds = pillar_seeds.get(pillar, [])
        made = 0
        topic_index = 0

        while made < needed:
            if topic_index >= len(info["topics"]) * 3:
                break
            topic = info["topics"][topic_index % len(info["topics"])]
            topic_index += 1

            seed = seeds[made % len(seeds)] if seeds else None

            if args.infer and llm_client:
                item = _generate_with_llm(content_type, pillar, topic, seed, llm_client, llm_model)
            else:
                item = _generate_deterministic_item(content_type, pillar, topic, seed)

            if not item:
                continue
            if item["slug"] in seen_slugs:
                item["slug"] = item["slug"] + f"-{made+1}"
            if item["slug"] in seen_slugs:
                continue

            seen_slugs.add(item["slug"])
            generated.append(item)
            items.append(item)
            made += 1

            if args.verbose:
                tags_str = ", ".join(item["tags"][:4])
                print(f"  + {item['slug']} ({tags_str})")

    # Summary
    print(f"\n{'='*60}")
    print("CONTENT GENERATION REPORT")
    print("="*60)
    print(f"Total generated: {len(generated)}")

    # Update counts
    new_counts: dict[tuple[str, str], int] = Counter()
    for item in items:
        t = item.get("content_type", "")
        p = item.get("pillar", "")
        new_counts[(t, p)] += 1

    for (t, p), target in sorted(TARGETS.items()):
        final = new_counts.get((t, p), 0)
        status = "✓" if final >= target else "✗"
        print(f"  {status} {t:12s} / {p:20s}: {final} (target {target})")

    # Save
    if not args.dry_run and generated:
        reg["last_content_generated"] = (
            datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        )
        save_registry(reg)
        print(f"\n  Written to {REGISTRY_PATH}")
    elif args.dry_run:
        print("\n  DRY RUN — no changes written")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
