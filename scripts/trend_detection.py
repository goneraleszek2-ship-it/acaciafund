#!/usr/bin/env python3
"""
Trend Detection System

Detects and scores:
- AI/ML trends
- Technology adoption cycles
- Regulatory changes
- Market shifts
- Emerging technologies

Each trend is scored on:
- Trend Strength (0-100): How strong is the signal?
- Adoption Level: Experimental / Emerging / Mainstream / Legacy
- Impact Level: Low / Medium / High / Critical
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


# Trend keywords by category
TREND_KEYWORDS = {
    "ai_ml": {
        "keywords": ["ai", "llm", "genai", "gpt", "claude", "gemini", "transformer", "rag", "vector", "embeddings", "ml", "machine learning", "deep learning", "neural network", "nlp", "foundation model", "agent", "agentic"],
        "weight": 3.0,
    },
    "data_ops": {
        "keywords": ["dataops", "mlops", "llmops", "data platform", "lakehouse", "data mesh", "data fabric", "data catalog", "data quality", "data observability"],
        "weight": 2.5,
    },
    "cloud": {
        "keywords": ["cloud", "aws", "azure", "gcp", "kubernetes", "docker", "serverless", "terraform", "infrastructure as code", "iac"],
        "weight": 2.0,
    },
    "security": {
        "keywords": ["security", "privacy", "compliance", "regulation", "aml", "kyc", "gdpr", "encryption", "zero trust", "rbac", "iam"],
        "weight": 2.5,
    },
    "finance": {
        "keywords": ["fintech", "decentralized", "blockchain", "crypto", "defi", "stablecoin", "token", "web3", "digital asset", "aml crypto"],
        "weight": 2.0,
    },
    "infrastructure": {
        "keywords": ["database", "postgresql", "mysql", "mongodb", "redis", "kafka", "spark", "flink", "streaming", "event driven", "event sourcing"],
        "weight": 2.0,
    },
}

# Adoption cycle phases
ADOPTION_PHASES = {
    "experimental": {"years": 0, "score": 0.5},
    "emerging": {"years": 0, "score": 0.7},
    "mainstream": {"years": 0, "score": 0.9},
    "legacy": {"years": 0, "score": 0.3},
}

# Default years for each phase
ADOPTION_YEARS = {
    "experimental": 0,
    "emerging": 1,
    "mainstream": 3,
    "legacy": 5,
}


def extract_trend_keywords(text: str) -> list[tuple[str, float]]:
    """Extract trend keywords from text."""
    text_lower = text.lower()
    found_trends = []
    
    for category, config in TREND_KEYWORDS.items():
        for keyword in config["keywords"]:
            # Use word boundary matching
            pattern = rf'\b{re.escape(keyword)}\b'
            if re.search(pattern, text_lower):
                found_trends.append((category, config["weight"]))
                break  # Only count each category once
    
    return found_trends


def compute_trend_strength(found_trends: list[tuple[str, float]]) -> float:
    """Compute trend strength score (0-100)."""
    if not found_trends:
        return 0.0
    
    # Sum weights and normalize to 0-100
    total_weight = sum(weight for _, weight in found_trends)
    
    # Scale: max expected is ~3-4 keywords = 100
    strength = min(100, total_weight * 25)
    
    return strength


def determine_adoption_level(found_trends: list[tuple[str, float]], title: str, content_type: str) -> str:
    """Determine adoption level based on trends and content type."""
    if not found_trends:
        return "mainstream"  # Default for non-trending content
    
    # AI/ML content is often emerging
    ai_trends = [t for t in found_trends if t[0] == "ai_ml"]
    if ai_trends:
        if content_type == "research":
            return "experimental"
        return "emerging"
    
    # Data ops content
    data_trends = [t for t in found_trends if t[0] == "data_ops"]
    if data_trends:
        return "emerging"
    
    # Cloud content
    cloud_trends = [t for t in found_trends if t[0] == "cloud"]
    if cloud_trends:
        return "mainstream"
    
    # Security content
    security_trends = [t for t in found_trends if t[0] == "security"]
    if security_trends:
        return "mainstream"
    
    # Finance content
    finance_trends = [t for t in found_trends if t[0] == "finance"]
    if finance_trends:
        return "emerging"
    
    return "mainstream"


def compute_impact_level(found_trends: list[tuple[str, float]]) -> str:
    """Compute impact level based on trends."""
    if not found_trends:
        return "low"
    
    total_weight = sum(weight for _, weight in found_trends)
    
    if total_weight >= 6:
        return "critical"
    elif total_weight >= 4:
        return "high"
    elif total_weight >= 2:
        return "medium"
    else:
        return "low"


def analyze_article_trends(article: dict) -> dict[str, Any]:
    """Analyze trends in an article."""
    title = article.get("title", "")
    description = article.get("description", "")
    body_html = article.get("body_html", "")
    tags = article.get("tags", [])
    content_type = article.get("content_type", "")
    
    # Combine text sources
    text = f"{title} {description} {body_html}"
    
    # Extract keywords
    found_trends = extract_trend_keywords(text)
    
    # Also check tags
    all_tags = [t.lower() for t in tags]
    for category, config in TREND_KEYWORDS.items():
        for keyword in config["keywords"]:
            if any(keyword in tag for tag in all_tags):
                found_trends.append((category, config["weight"]))
                break
    
    # Deduplicate
    found_trends = list(set(found_trends))
    
    # Compute scores
    trend_strength = compute_trend_strength(found_trends)
    adoption_level = determine_adoption_level(found_trends, title, content_type)
    impact_level = compute_impact_level(found_trends)
    
    # Get trend categories
    trend_categories = list(set(cat for cat, _ in found_trends))
    
    return {
        "trend_strength": round(trend_strength, 1),
        "adoption_level": adoption_level,
        "impact_level": impact_level,
        "trend_categories": trend_categories,
        "found_keywords": len(found_trends),
    }


def main():
    """Main entry point."""
    print("=" * 60)
    print("Trend Detection System")
    print("=" * 60)
    
    # Load registry
    registry_path = Path(__file__).parent.parent / "registry.json"
    with open(registry_path) as f:
        registry = json.load(f)
    
    content = registry.get("content", [])
    print(f"\nLoaded {len(content)} articles")
    
    # Analyze trends
    print("\nAnalyzing trends...")
    results = []

    
    for article in content:
        trend_analysis = analyze_article_trends(article)
        results.append({
            "slug": article.get("slug", ""),
            "title": article.get("title", ""),
            "trend_strength": trend_analysis["trend_strength"],
            "adoption_level": trend_analysis["adoption_level"],
            "impact_level": trend_analysis["impact_level"],
            "trend_categories": ",".join(trend_analysis["trend_categories"]),
            "found_keywords": trend_analysis["found_keywords"],
        })
    
    df = pd.DataFrame(results)
    
    # Show statistics
    print("\nTrend Statistics:")
    print(f"  Mean trend strength: {df['trend_strength'].mean():.1f}")
    print(f"  Max trend strength: {df['trend_strength'].max():.1f}")
    
    # Show adoption distribution
    print("\nAdoption Level Distribution:")
    for level in df["adoption_level"].value_counts().index:
        count = (df["adoption_level"] == level).sum()
        pct = count / len(df) * 100
        print(f"  {level}: {count} ({pct:.1f}%)")
    
    # Show impact distribution
    print("\nImpact Level Distribution:")
    for level in df["impact_level"].value_counts().index:
        count = (df["impact_level"] == level).sum()
        pct = count / len(df) * 100
        print(f"  {level}: {count} ({pct:.1f}%)")
    
    # Show trend categories
    print("\nTrend Categories:")
    all_categories = []
    for cats in df["trend_categories"]:
        if cats:
            all_categories.extend(cats.split(","))
    for cat, count in sorted(pd.Series(all_categories).value_counts().items(), key=lambda x: -x[1]):
        pct = count / len(df) * 100
        print(f"  {cat}: {count} ({pct:.1f}%)")
    
    # Show highest trend articles
    print("\nHighest Trend Articles:")
    high_trend = df.nlargest(10, "trend_strength")
    for _, row in high_trend.iterrows():
        print(f"  {row['title'][:50]}: {row['trend_strength']:.1f} ({row['adoption_level']})")
    
    # Save results
    output_path = Path(__file__).parent.parent / "dist" / "trend_detection.parquet"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_path, index=False)
    print(f"\nSaved trend detection to {output_path}")
    
    # Save summary statistics
    stats = {
        "total_articles": len(df),
        "mean_trend_strength": float(df['trend_strength'].mean()),
        "max_trend_strength": float(df['trend_strength'].max()),
        "adoption_distribution": df["adoption_level"].value_counts().to_dict(),
        "impact_distribution": df["impact_level"].value_counts().to_dict(),
        "trend_category_distribution": pd.Series(all_categories).value_counts().to_dict(),
    }
    
    stats_path = Path(__file__).parent.parent / "dist" / "trend_detection_stats.json"
    with open(stats_path, 'w') as f:
        json.dump(stats, f, indent=2)
    print(f"Saved trend detection statistics to {stats_path}")


if __name__ == "__main__":
    main()
