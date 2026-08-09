"""Quality and SQI utilities extracted from build.py.

SQI badge generation, SQI computation, quality scoring, interest scoring,
and content hashing for the AcaciaFund build pipeline.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from config import (
    INTEREST_RECENCY_DAYS,
    INTEREST_RECENCY_WEIGHT,
    INTEREST_SQI_WEIGHT,
    SQI_BADGE_HIGH,
    SQI_BADGE_MED,
)
from core.build_utils import _dt_utc

_SQI_WEIGHTS = {
    "source_credibility": 0.25,
    "technical_accuracy": 0.25,
    "practical_value": 0.20,
    "freshness": 0.15,
    "trend_relevance": 0.10,
    "educational_quality": 0.05,
}


def generate_sqi_badge(sqi: float) -> str:
    color = "#22c55e" if sqi >= SQI_BADGE_HIGH else "#d97706" if sqi >= SQI_BADGE_MED else "#ef4444"
    w = 160
    bar_w = int(min(1.0, max(0, sqi)) * w)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="20" viewBox="0 0 {w} 20">'
        f'<rect width="{w}" height="8" y="6" rx="4" fill="#e2e8f0"/>'
        f'<rect width="{bar_w}" height="8" y="6" rx="4" fill="{color}"/>'
        f'<circle cx="{max(8, bar_w)}" cy="10" r="6" fill="{color}"/>'
        f'<text x="{w + 6}" y="14" fill="#64748b" font-size="11" font-family="system-ui,sans-serif">{sqi:.3f}</text>'
        f"</svg>"
    )


def _compute_sqi_for_item(item) -> float:
    """Lightweight SQI computation for items missing it (matches backfill_sqi.py)."""
    body = (item.body_html or "").lower()
    title = (item.title or "").lower()
    text = f"{title} {body}"

    source_cred = 0.5
    sb = item.source_breakdown or {}
    signals = item.signals or {}
    sc = signals.get("count", sum(sb.values()) if sb else 0)
    if sc >= 3:
        source_cred = 1.0
    elif sc >= 2:
        source_cred = 0.85
    elif sc == 1:
        source_cred = 0.7

    tech_acc = 0.5
    depth = ["architecture", "implementation", "pattern", "design", "algorithm",
             "framework", "methodology", "analysis", "model", "system"]
    code = ["code", "example", "implementation", "api", "function", "class", "import", "def ", "return"]
    ref = ["documentation", "specification", "rfc", "standard", "reference", "citation", "paper", "study"]
    if any(m in text for m in depth):
        tech_acc += 0.15
    if any(m in text for m in code):
        tech_acc += 0.1
    if any(m in text for m in ref):
        tech_acc += 0.15
    if len(body) > 2000:
        tech_acc += 0.1
    tech_acc = min(1.0, tech_acc)

    practical = 0.5
    pmarks = ["how to", "tutorial", "guide", "step-by-step", "best practices",
              "case study", "real-world", "production", "deployment"]
    tmarks = ["tool", "library", "framework", "platform", "software", "database"]
    if any(m in text for m in pmarks):
        practical += 0.2
    if any(m in text for m in tmarks):
        practical += 0.15
    if item.content_type == "learn":
        practical += 0.1
    practical = min(1.0, practical)

    fresh = 0.5
    if item.created_at:
        try:
            days_old = (datetime.now(timezone.utc) - item.created_at).days
            fresh = max(0.2, 1.0 - (days_old / 360))
        except (ValueError, TypeError):
            pass

    trend = 0.5
    ts = signals.get("trend_strength", 0)
    if isinstance(ts, (int, float)) and ts > 0:
        trend = min(1.0, ts / 100)

    edu = 0.3
    if item.bloom_questions:
        edu += 0.35
    if item.content_type == "learn":
        edu += 0.15
    edu = min(1.0, edu)

    scores = {
        "source_credibility": source_cred,
        "technical_accuracy": tech_acc,
        "practical_value": practical,
        "freshness": fresh,
        "trend_relevance": trend,
        "educational_quality": edu,
    }
    final = sum(scores[k] * _SQI_WEIGHTS[k] for k in _SQI_WEIGHTS)
    slug = item.slug or ""
    if "glossary" in slug:
        final = max(final, 0.68)
    return round(final, 3)


def _get_quality_metrics_with_fail_safes(metrics: dict) -> dict:
    """Apply fail-safes for quality metrics to avoid zeroed values."""
    if metrics.get("authority", 0) == 0.0:
        metrics["authority"] = 0.74
    if metrics.get("diversity", 0) == 0.0:
        metrics["diversity"] = 0.68

    if "authority" not in metrics:
        metrics["authority"] = 0.74
    if "diversity" not in metrics:
        metrics["diversity"] = 0.68

    return metrics


def _compute_quality(quality_scores: dict, slug: str, extra_bonus: float = 0.0) -> tuple[float, str, dict]:
    """Compute quality score, badge stars, and metrics dict for an item.
    extra_bonus: additional SQI boost for items with ontology annotations / inspiration sources."""
    metrics = _get_quality_metrics_with_fail_safes(quality_scores.get(slug, {}))
    score = metrics.get("quality_score", 0)
    if extra_bonus > 0:
        score = min(1.0, score + extra_bonus)
        metrics["quality_score"] = score
        metrics["semantic_bonus"] = round(extra_bonus, 3)
    if score >= 0.8:
        badge = "\u2605\u2605\u2605\u2605\u2605"
    elif score >= 0.7:
        badge = "\u2605\u2605\u2605\u2605\u2606"
    elif score >= 0.6:
        badge = "\u2605\u2605\u2605\u2606\u2606"
    elif score >= 0.5:
        badge = "\u2605\u2605\u2606\u2606\u2606"
    else:
        badge = "\u2605\u2606\u2606\u2606\u2606"
    return score, badge, metrics


def interest_score(post, now: datetime) -> float:
    sqi = post.signals.get("avg_sqi", 0.0) if post.signals else 0.0
    created = _dt_utc(getattr(post, "created_at", None))
    age_days = (now - created).days if created else 365
    age_days = max(0, age_days)
    recency = max(0.1, 1.0 - age_days / INTEREST_RECENCY_DAYS)
    return sqi * INTEREST_SQI_WEIGHT + recency * INTEREST_RECENCY_WEIGHT


def _get_content_hash(content_item: Any) -> str:
    """Generate a hash fingerprint for a content item to detect source changes.

    Only hashes source-level fields from the registry, NOT injected/processed
    content (body_html, trending_html, etc.) which are computed during build.
    This ensures the cache skip works correctly on incremental builds.
    """
    data = {
        "slug": getattr(content_item, "slug", ""),
        "title": getattr(content_item, "title", ""),
        "content_type": getattr(content_item, "content_type", ""),
        "pillar": getattr(content_item, "pillar", ""),
        "description": getattr(content_item, "description", ""),
        "tags": sorted(getattr(content_item, "tags", []) or []),
        "bloom_questions": getattr(content_item, "bloom_questions", []),
        "flashcards": getattr(content_item, "flashcards", []),
        "quality_flags": getattr(content_item, "quality_flags", []),
        "knowledge_category": getattr(content_item, "knowledge_category", ""),
        "difficulty": getattr(content_item, "difficulty", ""),
        "date_str": getattr(content_item, "date_str", ""),
        "sandbox_exercises": getattr(content_item, "sandbox_exercises", []),
    }

    json_str = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(json_str.encode()).hexdigest()[:16]
