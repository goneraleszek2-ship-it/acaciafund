#!/usr/bin/env python3
"""
Foundry SQI Pipeline - PySpark script for distributed SQI calculation

This script can be run in Foundry Code Workbooks for distributed computation.
It calculates Systemic Quality Index (SQI) using the same logic as core/score.py
but optimized for distributed processing.

Usage in Foundry Code Workbook:
1. Upload this file to Foundry
2. Run in a PySpark notebook
3. Export results to Parquet/Arrow

Local testing:
    python scripts/sqi_pipeline.py
"""

from __future__ import annotations

import json
import math
import re
from datetime import datetime, timezone, timedelta
from collections import Counter
from pathlib import Path
from typing import Any

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Load configuration
import sys
sys.path.insert(0, str(PROJECT_ROOT))

from core.data import (
    PILLARS, ALL_ENTITIES, SOURCE_TIERS, DOMAIN_PATTERNS, KEYWORD_PATTERNS,
    extract_domain, log, CONTENT_DIR,
)


def source_authority(url: str) -> float:
    """Calculate source authority score."""
    domain = extract_domain(url)
    for pattern, score in SOURCE_TIERS:
        if pattern.search(domain):
            return score
    return 0.2


def engagement_score(story: dict, now: datetime) -> float:
    """Calculate engagement score from points and velocity."""
    points = story.get("points", 0) or 0
    if points <= 0:
        return 0.0
    
    created_at = story.get("created_at", "")
    try:
        created = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        hours = max(0.1, (now - created).total_seconds() / 3600)
    except (ValueError, TypeError):
        hours = 48.0
    
    velocity = points / hours
    raw = points * (1 + math.log1p(velocity))
    return min(1.0, math.log1p(raw) / 8.0)


def _tokenize(text: str) -> set[str]:
    """Tokenize text for novelty calculation."""
    return set(re.findall(r"[a-z]\w{3,}", text.lower()))


def novelty_score(title: str, history: dict[str, set[str]]) -> float:
    """Calculate novelty score based on historical token overlap."""
    tokens = _tokenize(title)
    if not tokens:
        return 0.5
    
    max_sim = 0.0
    for hist_tokens in history.values():
        inters = tokens & hist_tokens
        union = tokens | hist_tokens
        sim = len(inters) / len(union) if union else 0
        if sim > max_sim:
            max_sim = sim
    
    return 1.0 - max_sim


def cross_pillar_count(title: str, url: str) -> int:
    """Count how many pillars this article is relevant to."""
    title_lower = title.lower()
    domain = extract_domain(url)
    count = 0
    
    for pname in PILLARS:
        score = 0
        for pat, s in DOMAIN_PATTERNS[pname]:
            if pat.search(domain):
                score += s
        for pat in KEYWORD_PATTERNS[pname]:
            if pat.search(title_lower):
                score += 3
        if score > 0:
            count += 1
    
    return count


def entity_density(title: str) -> float:
    """Calculate entity density in title."""
    title_lower = title.lower()
    entities = [e for e in ALL_ENTITIES if e.lower() in title_lower]
    if not entities:
        return 0.0
    return min(1.0, len(entities) / 5.0)


def compute_signal_score(
    story: dict,
    history: dict[str, set[str]] | None = None,
    now: datetime | None = None,
) -> dict:
    """Compute SQI for a single story (same logic as core/score.py)."""
    if now is None:
        now = datetime.now(timezone.utc)
    if history is None:
        history = build_history()

    title = story.get("title", "")
    url = story.get("url", "")

    eng = engagement_score(story, now)
    auth = source_authority(url)
    novel = novelty_score(title, history)

    age_hours = 48.0
    try:
        created = datetime.fromisoformat(
            story.get("created_at", "").replace("Z", "+00:00")
        )
        age_hours = (now - created).total_seconds() / 3600
    except (ValueError, TypeError):
        pass
    timeliness = max(0.0, 1.0 - (age_hours / 72.0))

    cp = cross_pillar_count(title, url)
    ent = entity_density(title)

    composite = (
        0.30 * eng
        + 0.20 * auth
        + 0.20 * novel
        + 0.10 * min(1.0, cp / 3.0)
        + 0.10 * timeliness
        + 0.10 * ent
    )

    return {
        "sqi": round(composite, 3),
        "engagement": round(eng, 3),
        "authority": round(auth, 3),
        "novelty": round(novel, 3),
        "timeliness": round(timeliness, 3),
        "cross_pillar": cp,
        "entity_density": round(ent, 3),
    }


def build_history(window_days: int = 7) -> dict[str, set[str]]:
    """Build history of article tokens for novelty calculation."""
    history: dict[str, set[str]] = {}
    now = datetime.now(timezone.utc)
    
    for i in range(1, window_days + 1):
        date = now - timedelta(days=i)
        date_str = date.strftime("%Y-%m-%d")
        all_titles: list[str] = []
        
        for pname, config in PILLARS.items():
            fpath = config["folder"] / f"{date_str}.md"
            if fpath.exists():
                all_titles.extend(_extract_article_titles(fpath))
        
        if all_titles:
            tokens: set[str] = set()
            for t in all_titles:
                tokens.update(_tokenize(t))
            history[date_str] = tokens
    
    return history


def _extract_article_titles(fpath: Path) -> list[str]:
    """Extract article titles from markdown file."""
    content = fpath.read_text(encoding="utf-8")
    titles = []
    for line in content.splitlines():
        m = re.match(r"^\d+\.\s+\[(.+?)\]\(https?://", line.strip())
        if m:
            titles.append(m.group(1))
    return titles


# PySpark-compatible version for Foundry Code Workbooks
def compute_sqi_pandas(df: pd.DataFrame, now: datetime | None = None) -> pd.DataFrame:
    """Compute SQI for a pandas DataFrame (PySpark-compatible logic)."""
    if now is None:
        now = datetime.now(timezone.utc)
    
    history = build_history()
    
    results = []
    for _, row in df.iterrows():
        story = {
            "title": row.get("title", ""),
            "url": row.get("url", ""),
            "points": row.get("points", 0),
            "created_at": row.get("created_at", ""),
        }
        
        sqi = compute_signal_score(story, history, now)
        
        results.append({
            "slug": row.get("slug", ""),
            "title": row.get("title", ""),
            "sqi": sqi["sqi"],
            "engagement": sqi["engagement"],
            "authority": sqi["authority"],
            "novelty": sqi["novelty"],
            "timeliness": sqi["timeliness"],
            "cross_pillar": sqi["cross_pillar"],
            "entity_density": sqi["entity_density"],
        })
    
    return pd.DataFrame(results)


def main():
    """Main entry point."""
    print("=" * 60)
    print("Foundry SQI Pipeline - PySpark Compatible")
    print("=" * 60)
    
    # Load registry
    registry_path = PROJECT_ROOT / "registry.json"
    with open(registry_path) as f:
        registry = json.load(f)
    
    content = registry.get("content", [])
    print(f"Loaded {len(content)} articles from registry.json")
    
    # Convert to DataFrame
    articles_data = []
    for item in content:
        articles_data.append({
            "slug": item.get("slug", ""),
            "title": item.get("title", ""),
            "url": item.get("url", ""),
            "points": item.get("points", 0),
            "created_at": item.get("created_at", ""),
        })
    
    df = pd.DataFrame(articles_data)
    print(f"Created DataFrame: {len(df)} rows")
    
    # Compute SQI
    print("\nComputing SQI scores...")
    sqi_df = compute_sqi_pandas(df)
    print(f"Computed SQI for {len(sqi_df)} articles")
    
    # Show statistics
    print("\nSQI Statistics:")
    print(f"  Mean: {sqi_df['sqi'].mean():.3f}")
    print(f"  Median: {sqi_df['sqi'].median():.3f}")
    print(f"  Std: {sqi_df['sqi'].std():.3f}")
    print(f"  Min: {sqi_df['sqi'].min():.3f}")
    print(f"  Max: {sqi_df['sqi'].max():.3f}")
    
    # Save to Parquet
    output_path = PROJECT_ROOT / "dist" / "sqi_scores.parquet"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sqi_df.to_parquet(output_path, index=False)
    print(f"\nSaved SQI scores to {output_path}")
    
    # Save summary statistics
    stats = {
        "total_articles": len(sqi_df),
        "mean_sqi": float(sqi_df['sqi'].mean()),
        "median_sqi": float(sqi_df['sqi'].median()),
        "std_sqi": float(sqi_df['sqi'].std()),
        "min_sqi": float(sqi_df['sqi'].min()),
        "max_sqi": float(sqi_df['sqi'].max()),
        "high_sqi_count": int((sqi_df['sqi'] >= 0.6).sum()),
        "medium_sqi_count": int(((sqi_df['sqi'] >= 0.35) & (sqi_df['sqi'] < 0.6)).sum()),
        "low_sqi_count": int((sqi_df['sqi'] < 0.35).sum()),
    }
    
    stats_path = PROJECT_ROOT / "dist" / "sqi_stats.json"
    with open(stats_path, 'w') as f:
        json.dump(stats, f, indent=2)
    print(f"Saved SQI statistics to {stats_path}")
    
    print("\nPipeline complete!")


if __name__ == "__main__":
    main()
