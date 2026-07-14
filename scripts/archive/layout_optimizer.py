#!/usr/bin/env python3
"""
Advanced Layout Optimizer - Uses Foundry data to improve site layout

This script analyzes content patterns and generates layout improvements:
1. Content clustering for related articles
2. Personalized navigation paths
3. Performance optimization recommendations
4. Responsive design enhancements
5. Accessibility improvements
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pandas as pd


def load_data() -> tuple[dict, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load all data sources."""
    # Load registry
    registry_path = Path(__file__).parent.parent / "registry.json"
    with open(registry_path) as f:
        registry = json.load(f)

    # Load quality scores
    quality_path = Path(__file__).parent.parent / "dist" / "quality_scores.parquet"
    quality_df = pd.read_parquet(quality_path) if quality_path.exists() else pd.DataFrame()

    # Load source verification
    source_path = Path(__file__).parent.parent / "dist" / "source_verification.parquet"
    source_df = pd.read_parquet(source_path) if source_path.exists() else pd.DataFrame()

    # Load trend detection
    trend_path = Path(__file__).parent.parent / "dist" / "trend_detection.parquet"
    trend_df = pd.read_parquet(trend_path) if trend_path.exists() else pd.DataFrame()

    return registry, quality_df, source_df, trend_df


def analyze_content_patterns(registry: dict) -> dict[str, Any]:
    """Analyze content patterns for layout optimization."""
    content = registry.get("content", [])

    # Group by pillar
    pillar_content = {}
    for item in content:
        pillar = item.get("pillar", "unknown")
        if pillar not in pillar_content:
            pillar_content[pillar] = []
        pillar_content[pillar].append(item)

    # Analyze content types per pillar
    pillar_types = {}
    for pillar, items in pillar_content.items():
        types = {}
        for item in items:
            ct = item.get("content_type", "unknown")
            types[ct] = types.get(ct, 0) + 1
        pillar_types[pillar] = types

    # Find related content (shared tags)
    tag_cooccurrence = {}
    for item in content:
        tags = item.get("tags", [])
        for i, tag1 in enumerate(tags):
            for tag2 in tags[i + 1 :]:
                pair = tuple(sorted([tag1, tag2]))
                tag_cooccurrence[pair] = tag_cooccurrence.get(pair, 0) + 1

    # Find most related tags
    related_tags = {}
    for (tag1, tag2), count in sorted(tag_cooccurrence.items(), key=lambda x: -x[1])[:50]:
        if tag1 not in related_tags:
            related_tags[tag1] = []
        if tag2 not in related_tags:
            related_tags[tag2] = []
        related_tags[tag1].append((tag2, count))
        related_tags[tag2].append((tag1, count))

    return {
        "pillar_content": pillar_content,
        "pillar_types": pillar_types,
        "related_tags": related_tags,
    }


def generate_content_clusters(registry: dict, quality_df: pd.DataFrame) -> list[dict]:
    """Generate content clusters for related articles display."""
    content = registry.get("content", [])

    # Merge quality scores
    quality_dict = {}
    if not quality_df.empty:
        if "article_slug" in quality_df.columns:
            quality_dict = {row["article_slug"]: row for _, row in quality_df.iterrows()}
        elif "slug" in quality_df.columns:
            quality_dict = {row["slug"]: row for _, row in quality_df.iterrows()}

    # Create clusters based on tags and content type
    clusters = []
    tag_groups = {}

    for item in content:
        tags = item.get("tags", [])
        for tag in tags:
            if tag not in tag_groups:
                tag_groups[tag] = []
            tag_groups[tag].append(item)

    # Convert to clusters
    for tag, items in sorted(tag_groups.items(), key=lambda x: -len(x[1]))[:20]:
        if len(items) >= 3:  # Only clusters with 3+ articles
            quality_scores = [
                quality_dict.get(item["slug"], {}).get("quality_score", 0) for item in items
            ]
            avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0

            clusters.append(
                {
                    "tag": tag,
                    "article_count": len(items),
                    "avg_quality": round(avg_quality, 2),
                    "articles": [item["slug"] for item in items[:6]],  # Top 6
                }
            )

    return clusters


def generate_navigation_paths(registry: dict, trend_df: pd.DataFrame) -> dict[str, Any]:
    """Generate intelligent navigation paths based on trends."""
    content = registry.get("content", [])

    # Merge trend data
    trend_dict = {}
    if not trend_df.empty:
        # Support both 'source_id' and 'slug' column names
        id_col = "source_id" if "source_id" in trend_df.columns else "slug"
        trend_dict = {row[id_col]: row for _, row in trend_df.iterrows()}

    # Find trending content
    trending_items = []
    for item in content:
        slug = item.get("slug", "")
        if slug in trend_dict:
            trend = trend_dict[slug]
            if trend.get("trend_strength", 0) > 50:
                trending_items.append(
                    {
                        "slug": slug,
                        "title": item.get("title", ""),
                        "trend_strength": trend.get("trend_strength", 0),
                        "adoption_level": trend.get("adoption_level", ""),
                        "impact_level": trend.get("impact_level", ""),
                    }
                )

    # Sort by trend strength
    trending_items.sort(key=lambda x: -x["trend_strength"])

    # Create learning paths
    learning_paths = {
        "data-engineering": {
            "label": "Data Engineering Path",
            "steps": [
                {"title": "Data Engineering Basics", "slug": "learn/data-engineering-basics"},
                {
                    "title": "Data Pipeline Architectures",
                    "slug": "learn/data-pipeline-architectures",
                },
                {
                    "title": "Building Pipelines with dbt and Dagster",
                    "slug": "learn/building-pipelines-dbt-dagster",
                },
                {
                    "title": "Data Quality & Observability",
                    "slug": "learn/data-quality-observability-cost",
                },
            ],
        },
        "aml": {
            "label": "Compliance Path",
            "steps": [
                {"title": "AML & Compliance Glossary", "slug": "compliance/learn/aml-compliance-glossary"},
                {
                    "title": "Money Laundering Mechanisms",
                    "slug": "compliance/learn/money-laundering-mechanisms",
                },
                {"title": "AML Enforcement Cases", "slug": "compliance/learn/aml-enforcement-cases"},
                {"title": "Designing AML Program", "slug": "compliance/learn/designing-aml-program"},
            ],
        },
        "markets": {
            "label": "Markets Analysis Path",
            "steps": [
                {"title": "Market Analysis Methods", "slug": "learn/market-analysis-methods"},
                {
                    "title": "Sector Competitive Analysis",
                    "slug": "learn/sector-competitive-analysis",
                },
                {"title": "Applying Market Analysis", "slug": "learn/applying-market-analysis"},
            ],
        },
    }

    return {
        "trending_items": trending_items[:10],
        "learning_paths": learning_paths,
    }


def generate_performance_recommendations(registry: dict) -> dict[str, Any]:
    """Generate performance optimization recommendations."""
    content = registry.get("content", [])

    # Analyze page sizes and complexity
    recommendations = {
        "image_optimization": [],
        "lazy_loading": [],
        "code_splitting": [],
    }

    for item in content:
        body_html = item.get("body_html", "")
        title = item.get("title", "")

        # Check for images
        img_count = len(re.findall(r"<img[^>]+>", body_html))
        if img_count > 3:
            recommendations["image_optimization"].append(
                {
                    "slug": item.get("slug", ""),
                    "title": title,
                    "image_count": img_count,
                    "recommendation": "Consider lazy loading for images",
                }
            )

        # Check for code blocks
        code_count = len(re.findall(r"<pre[^>]*>", body_html))
        if code_count > 2:
            recommendations["code_splitting"].append(
                {
                    "slug": item.get("slug", ""),
                    "title": title,
                    "code_blocks": code_count,
                    "recommendation": "Consider code highlighting and collapsible sections",
                }
            )

    return recommendations


def generate_accessibility_improvements(registry: dict) -> dict[str, Any]:
    """Generate accessibility improvement recommendations."""
    content = registry.get("content", [])

    improvements = {
        "contrast_issues": [],
        "alt_text_missing": [],
        "heading_structure": [],
    }

    for item in content:
        body_html = item.get("body_html", "")
        title = item.get("title", "")

        # Check for heading hierarchy
        h1_count = len(re.findall(r"<h1[^>]*>", body_html))
        len(re.findall(r"<h2[^>]*>", body_html))

        if h1_count > 1:
            improvements["heading_structure"].append(
                {
                    "slug": item.get("slug", ""),
                    "title": title,
                    "issue": "Multiple H1 tags",
                }
            )

        # Check for images without alt text
        img_tags = re.findall(r"<img[^>]*>", body_html)
        for img in img_tags:
            if "alt=" not in img:
                improvements["alt_text_missing"].append(
                    {
                        "slug": item.get("slug", ""),
                        "title": title,
                        "issue": "Image without alt text",
                    }
                )

    return improvements


def generate_layout_config(
    registry: dict, quality_df: pd.DataFrame, trend_df: pd.DataFrame
) -> dict[str, Any]:
    """Generate comprehensive layout configuration."""
    content_patterns = analyze_content_patterns(registry)
    content_clusters = generate_content_clusters(registry, quality_df)
    navigation_paths = generate_navigation_paths(registry, trend_df)
    performance_recs = generate_performance_recommendations(registry)
    accessibility_improvements = generate_accessibility_improvements(registry)

    return {
        "generated_at": pd.Timestamp.now().isoformat(),
        "content_patterns": content_patterns,
        "content_clusters": content_clusters,
        "navigation_paths": navigation_paths,
        "performance_recommendations": performance_recs,
        "accessibility_improvements": accessibility_improvements,
    }


def main():
    """Main entry point."""
    print("=" * 70)
    print("Advanced Layout Optimizer - Foundry-Powered Improvements")
    print("=" * 70)

    # Load data
    print("\nLoading data sources...")
    registry, quality_df, source_df, trend_df = load_data()
    print(f"  Registry: {len(registry.get('content', []))} articles")
    print(f"  Quality scores: {len(quality_df)} records")
    print(f"  Source verification: {len(source_df)} records")
    print(f"  Trend detection: {len(trend_df)} records")

    # Generate layout config
    print("\nAnalyzing content patterns...")
    layout_config = generate_layout_config(registry, quality_df, trend_df)

    # Save configuration
    output_path = Path(__file__).parent.parent / "dist" / "layout_config.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(layout_config, f, indent=2)
    print(f"\nSaved layout configuration to {output_path}")

    # Print summary
    print("\n" + "=" * 70)
    print("Layout Optimization Summary")
    print("=" * 70)

    print("\n1. Content Clusters:")
    for cluster in layout_config["content_clusters"][:5]:
        print(
            f"  - #{cluster['tag']}: {cluster['article_count']} articles (avg quality: {cluster['avg_quality']})"
        )

    print("\n2. Trending Content:")
    for item in layout_config["navigation_paths"]["trending_items"][:5]:
        print(
            f"  - {item['title'][:50]}: strength={item['trend_strength']}, adoption={item['adoption_level']}"
        )

    print("\n3. Learning Paths:")
    for path_name, path_data in layout_config["navigation_paths"]["learning_paths"].items():
        print(f"  - {path_data['label']}: {len(path_data['steps'])} steps")

    print("\n4. Performance Recommendations:")
    print(
        f"  - Image optimization: {len(layout_config['performance_recommendations']['image_optimization'])} articles"
    )
    print(
        f"  - Code splitting: {len(layout_config['performance_recommendations']['code_splitting'])} articles"
    )

    print("\n5. Accessibility Improvements:")
    print(
        f"  - Contrast issues: {len(layout_config['accessibility_improvements']['contrast_issues'])} articles"
    )
    print(
        f"  - Alt text missing: {len(layout_config['accessibility_improvements']['alt_text_missing'])} images"
    )


if __name__ == "__main__":
    main()
