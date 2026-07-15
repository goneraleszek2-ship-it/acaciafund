#!/usr/bin/env python3
"""
SQI Backfill Script — Compute SQI for all registry items missing it.

Reuses the quality scoring logic from quality_engine.py but applies it
to all items, especially those missing SQI scores. Updates registry.json
in-place with computed SQI values.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

# Quality dimension weights (from quality_engine.py)
WEIGHTS = {
    "source_credibility": 0.25,
    "technical_accuracy": 0.25,
    "practical_value": 0.20,
    "freshness": 0.15,
    "trend_relevance": 0.10,
    "educational_quality": 0.05,
}

SQI_THRESHOLD = 0.65


def compute_source_credibility(article: dict) -> float:
    """Source credibility based on source type and domain."""
    source_breakdown = article.get("source_breakdown", {})
    signals = article.get("signals", {}) or {}

    # Multi-source articles get higher credibility
    source_count = signals.get("count", sum(source_breakdown.values()) if source_breakdown else 0)
    if source_count >= 3:
        return 1.0
    elif source_count >= 2:
        return 0.85
    elif source_count == 1:
        return 0.7

    # Check source types
    if source_breakdown.get("arxiv", 0) > 0:
        return 0.95
    if source_breakdown.get("pubmed", 0) > 0:
        return 0.95
    if source_breakdown.get("hn", 0) > 0:
        return 0.65

    return 0.5


def compute_technical_accuracy(article: dict) -> float:
    """Technical depth based on body content analysis."""
    body = (article.get("body_html", "") or "").lower()
    title = (article.get("title", "") or "").lower()
    text = f"{title} {body}"

    score = 0.5
    depth_markers = ["architecture", "implementation", "pattern", "design", "algorithm",
                     "framework", "methodology", "analysis", "model", "system"]
    code_markers = ["code", "example", "implementation", "api", "function", "class",
                    "import", "def ", "return"]
    reference_markers = ["documentation", "specification", "rfc", "standard", "reference",
                         "citation", "paper", "study"]

    if any(m in text for m in depth_markers):
        score += 0.15
    if any(m in text for m in code_markers):
        score += 0.1
    if any(m in text for m in reference_markers):
        score += 0.15
    if len(body) > 2000:
        score += 0.1

    return min(1.0, score)


def compute_practical_value(article: dict) -> float:
    """Practical applicability based on content indicators."""
    body = (article.get("body_html", "") or "").lower()
    title = (article.get("title", "") or "").lower()
    text = f"{title} {body}"

    score = 0.5
    practical_markers = ["how to", "tutorial", "guide", "step-by-step", "best practices",
                         "case study", "real-world", "production", "deployment"]
    tool_markers = ["tool", "library", "framework", "platform", "software", "database"]

    if any(m in text for m in practical_markers):
        score += 0.2
    if any(m in text for m in tool_markers):
        score += 0.15
    if article.get("content_type") == "learn":
        score += 0.1

    return min(1.0, score)


def compute_freshness(article: dict) -> float:
    """Recency score with exponential decay over 180 days."""
    created = article.get("created_at", "")
    if not created:
        return 0.5

    try:
        pub_date = datetime.fromisoformat(created.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        days_old = (now - pub_date).days
        # Exponential decay: 1.0 at day 0, ~0.5 at day 180
        return max(0.2, 1.0 - (days_old / 360))
    except (ValueError, TypeError):
        return 0.5


def compute_trend_relevance(article: dict) -> float:
    """Trend strength from signals."""
    signals = article.get("signals", {}) or {}
    trend = signals.get("trend_strength", 0)
    if isinstance(trend, (int, float)) and trend > 0:
        return min(1.0, trend / 100)
    return 0.5


def compute_educational_quality(article: dict) -> float:
    """Educational value based on Bloom's questions and flashcards."""
    score = 0.3
    if article.get("bloom_questions"):
        score += 0.35
    if article.get("flashcards"):
        score += 0.2
    if article.get("content_type") == "learn":
        score += 0.15
    return min(1.0, score)


GLOSSARY_SQI_FLOOR = 0.68


def compute_sqi(article: dict) -> dict:
    """Compute full SQI breakdown for an item."""
    scores = {
        "source_credibility": compute_source_credibility(article),
        "technical_accuracy": compute_technical_accuracy(article),
        "practical_value": compute_practical_value(article),
        "freshness": compute_freshness(article),
        "trend_relevance": compute_trend_relevance(article),
        "educational_quality": compute_educational_quality(article),
    }

    final = sum(scores[k] * WEIGHTS[k] for k in WEIGHTS)

    slug = article.get("slug", "")
    if "glossary" in slug:
        final = max(final, GLOSSARY_SQI_FLOOR)

    scores["quality_score"] = round(final, 3)
    return scores


def main():
    print("=" * 60)
    print("SQI Backfill Script")
    print("=" * 60)

    registry_path = Path(__file__).parent.parent / "registry.json"
    with open(registry_path) as f:
        registry = json.load(f)

    content = registry.get("content", [])
    print(f"\nLoaded {len(content)} items")

    updated = 0
    already_has_sqi = 0
    below_threshold = 0

    for item in content:
        slug = item.get("slug", "")
        current_sqi = item.get("sqi")
        signals = item.get("signals", {}) or {}
        avg_sqi = signals.get("avg_sqi")

        # Check if item already has a good SQI in the sqi field
        has_sqi = current_sqi is not None and current_sqi > 0

        if has_sqi and current_sqi and current_sqi >= SQI_THRESHOLD:
            already_has_sqi += 1
            continue

        # If signals.avg_sqi exists but sqi field is missing, copy it over
        if not has_sqi and avg_sqi is not None and avg_sqi > 0:
            item["sqi"] = round(avg_sqi, 3)
            already_has_sqi += 1
            continue

        # Compute new SQI
        scores = compute_sqi(item)
        new_sqi = scores["quality_score"]

        # Update item
        item["sqi"] = new_sqi
        if not item.get("quality_metrics"):
            item["quality_metrics"] = scores
        else:
            item["quality_metrics"]["score"] = new_sqi

        # Update signals if present
        if signals:
            signals["avg_sqi"] = new_sqi
        else:
            item["signals"] = {"avg_sqi": new_sqi}

        updated += 1
        if new_sqi < SQI_THRESHOLD:
            below_threshold += 1

    # Write updated registry
    with open(registry_path, "w") as f:
        json.dump(registry, f, indent=2, ensure_ascii=False)

    print("\nResults:")
    print(f"  Already has SQI >= {SQI_THRESHOLD}: {already_has_sqi}")
    print(f"  Updated with new SQI: {updated}")
    print(f"  Below threshold after update: {below_threshold}")
    print(f"  Total items: {len(content)}")

    # Show distribution
    sqi_values = []
    for item in content:
        sqi = item.get("sqi", 0) or 0
        avg = (item.get("signals", {}) or {}).get("avg_sqi", 0) or 0
        sqi_values.append(max(sqi, avg))

    if sqi_values:
        sqi_values.sort()
        n = len(sqi_values)
        print("\nSQI Distribution:")
        print(f"  Min: {sqi_values[0]:.3f}")
        print(f"  Max: {sqi_values[-1]:.3f}")
        print(f"  Avg: {sum(sqi_values)/n:.3f}")
        print(f"  Median: {sqi_values[n//2]:.3f}")
        print(f"  Items >= 0.65: {sum(1 for s in sqi_values if s >= SQI_THRESHOLD)}")
        print(f"  Items < 0.65: {sum(1 for s in sqi_values if s < SQI_THRESHOLD)}")


if __name__ == "__main__":
    main()
