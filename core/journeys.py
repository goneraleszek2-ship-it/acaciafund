"""Formal cross-pillar journeys (Task 3.3).

Three curated, linear study journeys that cross all three pillars. Each
journey is an ordered sequence of existing learn modules; the build renders
a hub page (``/journeys/``) plus one page per journey with linear prev/next
navigation and per-step completion tracking (localStorage).
"""

from __future__ import annotations

from typing import Any

from core.urls import slug_to_fspath

JOURNEYS: list[dict[str, Any]] = [
    {
        "slug": "fiat-to-crypto-compliance-arc",
        "title": "From Fiat to Crypto: The Compliance Arc",
        "tagline": "How digital assets move, and how compliance keeps pace.",
        "description": "Start where value is created in traditional markets, then follow the compliance controls that govern money movement — ending with the data plumbing that makes monitoring possible.",
        "accent_pillar": "aml",
        "items": [
            "markets/learn/how-stock-markets-work",
            "markets/learn/market-fundamentals",
            "aml/learn/aml-basics",
            "aml/learn/kyc-cdd-workflows",
            "aml/learn/crypto-aml",
            "data/learn/data-pipeline-architectures",
        ],
    },
    {
        "slug": "data-driven-trading-operation",
        "title": "Building a Data-Driven Trading Operation",
        "tagline": "From raw data to measured risk.",
        "description": "Lay the data foundation, then layer quantitative method and volatility analytics on top — and close with the control framework a real trading desk needs.",
        "accent_pillar": "stock",
        "items": [
            "data/learn/data-engineering-basics",
            "data/learn/sql-for-data-engineers",
            "data/learn/building-pipelines-dbt-dagster",
            "markets/learn/quantitative-methods-intro",
            "markets/learn/volatility-analysis",
            "aml/learn/designing-aml-program",
        ],
    },
    {
        "slug": "suspicious-activity-to-sar",
        "title": "From Suspicious Activity to SAR",
        "tagline": "Quality data, sharp screening, timely filing.",
        "description": "Follow a suspicious transaction end-to-end: understand the data quality that makes detection trustworthy, master screening and trade-based typologies, file the SAR correctly, and see the market mechanics that create the signals.",
        "accent_pillar": "aml",
        "items": [
            "data/learn/data-quality-basics",
            "data/learn/data-quality-observability-cost",
            "aml/learn/sanctions-screening",
            "aml/learn/trade-based-ml-sanctions",
            "aml/learn/sar-filing-scenarios",
            "markets/learn/market-microstructure",
        ],
    },
]


def pillar_of(slug: str) -> str:
    """Map a registry slug back to its internal pillar key."""
    first = slug.split("/", 1)[0]
    return {"compliance": "aml", "markets": "stock", "data": "data-engineering"}.get(first, first)


def build_journey_pages(registry_items: list[Any], journeys: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    """Resolve each journey's item slugs against the registry into page context.

    Returns one dict per journey with resolved ``steps`` (slug, title,
    description, pillar, difficulty, url) plus prev/next linkage, pillar
    span, and per-step pillar metadata for coloring.
    """
    by_slug = {}
    for raw in registry_items:
        item = raw if isinstance(raw, dict) else (raw.model_dump() if hasattr(raw, "model_dump") else {})
        if item.get("slug"):
            by_slug[item["slug"]] = item

    pages: list[dict[str, Any]] = []
    for journey in journeys or JOURNEYS:
        steps = []
        for slug in journey["items"]:
            item = by_slug.get(slug)
            if not item:
                continue
            url = f"/{slug_to_fspath(slug)}/"
            steps.append({
                "slug": slug,
                "title": item.get("title", slug),
                "description": item.get("description", ""),
                "pillar": pillar_of(slug),
                "difficulty": item.get("difficulty", ""),
                "url": url,
            })
        for index, step in enumerate(steps):
            step["position"] = index
            step["total"] = len(steps)
            step["prev"] = steps[index - 1] if index > 0 else None
            step["next"] = steps[index + 1] if index < len(steps) - 1 else None
        pillar_span = {step["pillar"] for step in steps}
        pages.append({
            "slug": journey["slug"],
            "title": journey["title"],
            "tagline": journey["tagline"],
            "description": journey["description"],
            "accent_pillar": journey.get("accent_pillar", "aml"),
            "steps": steps,
            "step_count": len(steps),
            "pillar_span": sorted(pillar_span),
            "span_count": len(pillar_span),
        })
    return pages


def build_journeys_index(pages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Build the hub-page context: one card per journey."""
    return [
        {
            "slug": page["slug"],
            "title": page["title"],
            "tagline": page["tagline"],
            "description": page["description"],
            "step_count": page["step_count"],
            "span_count": page["span_count"],
            "pillar_span": page["pillar_span"],
            "accent_pillar": page["accent_pillar"],
            "first_url": page["steps"][0]["url"] if page["steps"] else f"/journeys/{page['slug']}/",
        }
        for page in pages
    ]
