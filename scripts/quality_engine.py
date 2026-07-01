#!/usr/bin/env python3
"""
Knowledge Quality Engine - 6-dimension quality scoring system

Dimensions (weighted):
- Source Credibility: 25%
- Technical Accuracy: 25%
- Practical Value: 20%
- Freshness: 15%
- Trend Relevance: 10%
- Educational Quality: 5%

Final result: Knowledge Quality Score (0-100)
Only high-scoring content becomes featured.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


def load_registry() -> dict:
    """Load registry.json."""
    registry_path = Path(__file__).parent.parent / "registry.json"
    with open(registry_path) as f:
        return json.load(f)


def compute_source_credibility(article: dict) -> float:
    """Compute source credibility score (25% weight)."""
    url = article.get("url", "")
    source_api = article.get("source_api", "")

    # High credibility sources
    high_credibility = {
        "arxiv": 1.0,
        "pubmed": 1.0,
        "openverse": 0.8,
        "wikimedia": 0.8,
        "nasa": 1.0,
        "loc": 0.9,
        "curated": 0.95,
    }

    if source_api in high_credibility:
        return high_credibility[source_api]

    # Check domain for credibility
    domain = url.lower()
    if any(x in domain for x in ["mit.edu", "stanford.edu", "harvard.edu", "oxford.edu"]):
        return 0.95
    if any(x in domain for x in ["arxiv.org", "pubmed.ncbi.nlm.nih.gov"]):
        return 1.0
    if any(x in domain for x in ["github.com", "gitlab.com"]):
        return 0.7

    # Default for unknown sources
    return 0.5


def compute_technical_accuracy(article: dict) -> float:
    """Compute technical accuracy score (25% weight)."""
    body_html = article.get("body_html", "")
    article.get("title", "")

    score = 0.5  # Base score

    # Check for technical depth indicators
    if any(x in body_html.lower() for x in ["architecture", "implementation", "pattern", "design"]):
        score += 0.15
    if any(x in body_html.lower() for x in ["example", "code", "implementation"]):
        score += 0.1
    if any(x in body_html.lower() for x in ["comparison", "benchmark", "performance"]):
        score += 0.1
    if any(x in body_html.lower() for x in ["trade-off", "tradeoff", "tradeoffs"]):
        score += 0.1

    # Check for references to official sources
    if any(x in body_html.lower() for x in ["documentation", "specification", "rfc", "standard"]):
        score += 0.15

    return min(1.0, score)


def compute_practical_value(article: dict) -> float:
    """Compute practical value score (20% weight)."""
    body_html = article.get("body_html", "")
    title = article.get("title", "")

    score = 0.5  # Base score

    # Check for practical indicators
    if any(x in body_html.lower() for x in ["how to", "tutorial", "guide", "step-by-step"]):
        score += 0.15
    if any(x in body_html.lower() for x in ["example", "code", "implementation"]):
        score += 0.1
    if any(x in body_html.lower() for x in ["best practice", "recommendation", "avoid"]):
        score += 0.1
    if any(x in title.lower() for x in ["practical", "guide", "tutorial", "how"]):
        score += 0.1

    # Check for actionable content
    if any(x in body_html.lower() for x in ["recommend", "suggest", "should", "avoid"]):
        score += 0.1

    return min(1.0, score)


def compute_freshness(article: dict) -> float:
    """Compute freshness score (15% weight)."""
    created_at = article.get("created_at", "")
    now = datetime.now(timezone.utc)

    try:
        created = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        age_days = (now - created).total_seconds() / 86400

        # Decay function: newer = higher score
        if age_days < 30:
            return 1.0
        elif age_days < 90:
            return 0.8
        elif age_days < 180:
            return 0.6
        elif age_days < 365:
            return 0.4
        else:
            return 0.2
    except (ValueError, TypeError):
        return 0.5  # Default if date unknown


def compute_trend_relevance(article: dict) -> float:
    """Compute trend relevance score (10% weight)."""
    title = article.get("title", "").lower()
    tags = article.get("tags", [])
    body_html = article.get("body_html", "").lower()

    score = 0.5  # Base score

    # Check for trending keywords
    trending_keywords = {
        "ai": 0.3,
        "llm": 0.3,
        "genai": 0.3,
        "llama": 0.2,
        "gpt": 0.2,
        "transformer": 0.2,
        "rag": 0.2,
        "vector": 0.2,
        "embeddings": 0.2,
        "ml": 0.2,
        "machine learning": 0.2,
    }

    for keyword, boost in trending_keywords.items():
        if keyword in title or keyword in body_html:
            score += boost
            break  # Only add boost once

    # Check for AI/ML tags
    ai_tags = {"ai", "machine-learning", "llm", "nlp", "deep-learning"}
    if any(tag in ai_tags for tag in tags):
        score += 0.2

    return min(1.0, score)


def compute_educational_quality(article: dict) -> float:
    """Compute educational quality score (5% weight)."""
    bloom_questions = article.get("bloom_questions", [])
    body_html = article.get("body_html", "")

    score = 0.5  # Base score

    # Check for educational content
    if len(bloom_questions) > 0:
        score += 0.3
    if any(x in body_html.lower() for x in ["summary", "key point", "takeaway", "conclusion"]):
        score += 0.1
    if any(x in body_html.lower() for x in ["example", "exercise", "practice"]):
        score += 0.1

    return min(1.0, score)


def compute_quality_score(article: dict) -> dict:
    """Compute all quality dimensions and final score."""
    source_credibility = compute_source_credibility(article)
    technical_accuracy = compute_technical_accuracy(article)
    practical_value = compute_practical_value(article)
    freshness = compute_freshness(article)
    trend_relevance = compute_trend_relevance(article)
    educational_quality = compute_educational_quality(article)

    # Weighted sum
    final_score = (
        0.25 * source_credibility
        + 0.25 * technical_accuracy
        + 0.20 * practical_value
        + 0.15 * freshness
        + 0.10 * trend_relevance
        + 0.05 * educational_quality
    )

    return {
        "source_credibility": round(source_credibility, 3),
        "technical_accuracy": round(technical_accuracy, 3),
        "practical_value": round(practical_value, 3),
        "freshness": round(freshness, 3),
        "trend_relevance": round(trend_relevance, 3),
        "educational_quality": round(educational_quality, 3),
        "quality_score": round(final_score, 3),
    }


def main():
    """Main entry point."""
    print("=" * 60)
    print("Knowledge Quality Engine")
    print("=" * 60)

    # Load registry
    registry = load_registry()
    content = registry.get("content", [])
    print(f"\nLoaded {len(content)} articles")

    # Compute quality scores
    print("\nComputing quality scores...")
    results = []

    for article in content:
        scores = compute_quality_score(article)
        results.append(
            {
                "slug": article.get("slug", ""),
                "title": article.get("title", ""),
                "quality_score": scores["quality_score"],
                "source_credibility": scores["source_credibility"],
                "technical_accuracy": scores["technical_accuracy"],
                "practical_value": scores["practical_value"],
                "freshness": scores["freshness"],
                "trend_relevance": scores["trend_relevance"],
                "educational_quality": scores["educational_quality"],
            }
        )

    df = pd.DataFrame(results)

    # Show statistics
    print("\nQuality Score Statistics:")
    print(f"  Mean: {df['quality_score'].mean():.3f}")
    print(f"  Median: {df['quality_score'].median():.3f}")
    print(f"  Std: {df['quality_score'].std():.3f}")
    print(f"  Min: {df['quality_score'].min():.3f}")
    print(f"  Max: {df['quality_score'].max():.3f}")

    # Show high quality articles (score >= 0.7)
    high_quality = df[df["quality_score"] >= 0.7].sort_values("quality_score", ascending=False)
    print(f"\nHigh Quality Articles (score >= 0.7): {len(high_quality)}")
    print(high_quality.head(10).to_string(index=False))

    # Show low quality articles (score < 0.5)
    low_quality = df[df["quality_score"] < 0.5].sort_values("quality_score")
    print(f"\nLow Quality Articles (score < 0.5): {len(low_quality)}")
    print(low_quality.head(5).to_string(index=False))

    # Save results
    output_path = Path(__file__).parent.parent / "dist" / "quality_scores.parquet"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_path, index=False)
    print(f"\nSaved quality scores to {output_path}")

    # Save summary statistics
    stats = {
        "total_articles": len(df),
        "mean_score": float(df["quality_score"].mean()),
        "median_score": float(df["quality_score"].median()),
        "std_score": float(df["quality_score"].std()),
        "high_quality_count": int((df["quality_score"] >= 0.7).sum()),
        "medium_quality_count": int(
            ((df["quality_score"] >= 0.5) & (df["quality_score"] < 0.7)).sum()
        ),
        "low_quality_count": int((df["quality_score"] < 0.5).sum()),
    }

    stats_path = Path(__file__).parent.parent / "dist" / "quality_stats.json"
    with open(stats_path, "w") as f:
        json.dump(stats, f, indent=2)
    print(f"Saved quality statistics to {stats_path}")


if __name__ == "__main__":
    main()
