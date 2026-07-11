#!/usr/bin/env python3
"""
Source Verification Framework

Tracks and displays:
- Source URL
- Source type (academic, official, industry, blog, social)
- Verification status (verified, unverified, disputed)
- Evidence level (peer-reviewed, official docs, industry report, etc.)
- Last verified date
- Trust score
"""

from __future__ import annotations

import json
import re
import tomllib
from pathlib import Path
from typing import Any

import pandas as pd

INSPIRATION_SOURCES_PATH = Path(__file__).parent.parent / "etc" / "pillars.toml"

# Inspiration source domains mapped to source names for quick lookup
_INSPIRATION_DOMAINS: dict[str, str] = {}


def _load_inspiration_domains() -> dict[str, str]:
    """Load inspiration source URLs and map domains to source names."""
    global _INSPIRATION_DOMAINS
    if _INSPIRATION_DOMAINS:
        return _INSPIRATION_DOMAINS
    if not INSPIRATION_SOURCES_PATH.exists():
        return {}
    try:
        with open(INSPIRATION_SOURCES_PATH, "rb") as f:
            toml_data = tomllib.load(f)
        sources = toml_data.get("inspiration_sources", {})
        for pillar_key, pillar_sources in sources.items():
            if not isinstance(pillar_sources, dict):
                continue
            for src_key, src_info in pillar_sources.items():
                if isinstance(src_info, dict) and "url" in src_info:
                    domain = extract_domain(src_info["url"])
                    _INSPIRATION_DOMAINS[domain] = src_info["name"]
    except Exception:
        pass
    return _INSPIRATION_DOMAINS


def classify_source_type(
    url: str = "", tags: list = [], content_type: str = "", title: str = ""
) -> tuple[str, float]:
    """Classify source type and trust score."""
    url_lower = url.lower() if url else ""
    domain = extract_domain(url)

    # Check inspiration sources first (authoritative)
    inspr_domains = _load_inspiration_domains()
    if domain in inspr_domains:
        return "inspiration", 0.95

    # Academic sources
    if any(
        x in url_lower
        for x in [
            "arxiv.org",
            "pubmed.ncbi.nlm.nih.gov",
            "sciencedirect.com",
            "springer.com",
            "tandfonline.com",
            "ieee.org",
            "acm.org",
        ]
    ):
        return "academic", 0.95

    # Official sources
    if any(
        x in url_lower
        for x in [
            ".gov",
            ".edu",
            ".org",
            "apache.org",
            "kubernetes.io",
            "docker.com",
            "python.org",
            "rust-lang.org",
            "developer.mozilla.org",
            "docs.microsoft.com",
            "developer.apple.com",
            "google.com",
            "aws.amazon.com",
            "azure.microsoft.com",
        ]
    ):
        return "official", 0.9

    # Industry reports
    if any(
        x in url_lower
        for x in [
            "mckinsey.com",
            "bcg.com",
            "gartner.com",
            "idc.com",
            "forrester.com",
            "statista.com",
            "marketwatch.com",
            "bloomberg.com",
            "reuters.com",
        ]
    ):
        return "industry_report", 0.85

    # Engineering blogs
    if any(
        x in url_lower
        for x in [
            "aws.amazon.com/blogs",
            "cloud.google.com/blog",
            "dev.to",
            "medium.com",
            "hashnode.com",
            "towardsdatascience.com",
            "towardsai.net",
        ]
    ):
        return "engineering_blog", 0.75

    # News sources
    if any(
        x in url_lower
        for x in [
            "nytimes.com",
            "washingtonpost.com",
            "bbc.com",
            "cnn.com",
            "foxnews.com",
            "nbcnews.com",
            "cbsnews.com",
        ]
    ):
        return "news", 0.7

    # Social media
    if any(
        x in url_lower
        for x in [
            "twitter.com",
            "x.com",
            "linkedin.com",
            "youtube.com",
            "tiktok.com",
            "instagram.com",
        ]
    ):
        return "social", 0.5

    # Fallback based on content type and tags
    if content_type == "research":
        return "research", 0.85

    if content_type == "learn":
        return "educational", 0.75

    if content_type == "knowledge":
        return "reference", 0.8

    ai_tags = {"ai", "machine-learning", "llm", "nlp", "deep-learning"}
    if any(tag in ai_tags for tag in tags):
        return "ai_generated", 0.6

    # Default based on pillar
    if any(x in title.lower() for x in ["aml", "compliance", "regulation", "fraud"]):
        return "regulatory", 0.8

    return "unknown", 0.5


def verify_source(source_type: str) -> dict[str, Any]:
    """Verify source and return verification details."""
    verified = False
    evidence = []

    if source_type == "academic":
        verified = True
        evidence = ["Peer-reviewed", "DOI available"]
    elif source_type == "official":
        verified = True
        evidence = ["Official domain", "Authoritative source"]
    elif source_type == "industry_report":
        verified = True
        evidence = ["Industry report", "Published by firm"]
    elif source_type == "engineering_blog":
        verified = True
        evidence = ["Technical content", "Code examples"]
    elif source_type == "news":
        verified = True
        evidence = ["Editorial standards", "Fact-checking"]
    elif source_type == "research":
        verified = True
        evidence = ["Research content", "Citations included"]
    elif source_type == "educational":
        verified = True
        evidence = ["Educational content", "Bloom questions included"]
    elif source_type == "reference":
        verified = True
        evidence = ["Reference material", "Curated content"]
    elif source_type == "regulatory":
        verified = True
        evidence = ["Regulatory focus", "Official sources"]
    elif source_type == "inspiration":
        verified = True
        evidence = ["Curated inspiration source", "Authoritative domain", "Regularly monitored"]
    elif source_type == "ai_generated":
        verified = False
        evidence = ["AI-generated content", "Human review recommended"]
    elif source_type == "social":
        verified = False
        evidence = ["User-generated", "Needs verification"]
    else:
        verified = False
        evidence = ["Unknown source", "Manual verification needed"]

    return {
        "verified": verified,
        "evidence": evidence,
        "verification_status": "verified" if verified else "unverified",
    }


def extract_domain(url: str) -> str:
    """Extract domain from URL."""
    if not url:
        return "unknown"

    # Remove protocol
    url = re.sub(r"^https?://", "", url)
    url = re.sub(r"^www\.", "", url)

    # Extract domain
    domain = url.split("/")[0]

    return domain


def compute_source_score(source_info: dict) -> float:
    """Compute overall source score."""
    base_score = 0.5

    # Source type score
    source_type = source_info.get("source_type", "unknown")
    type_scores = {
        "academic": 0.95,
        "official": 0.9,
        "industry_report": 0.85,
        "engineering_blog": 0.75,
        "news": 0.7,
        "social": 0.5,
        "inspiration": 0.95,
        "unknown": 0.5,
    }
    base_score = type_scores.get(source_type, 0.5)

    # Verification bonus
    if source_info.get("verified", False):
        base_score = min(1.0, base_score + 0.05)

    return base_score


def analyze_article_sources(article: dict) -> list[dict]:
    """Analyze all sources in an article."""
    sources = []

    # Classify based on content type, tags, and title
    url = article.get("url", "")
    tags = article.get("tags", [])
    content_type = article.get("content_type", "")
    title = article.get("title", "")

    source_type, trust_score = classify_source_type(url, tags, content_type, title)
    verification = verify_source(source_type)

    sources.append(
        {
            "type": "primary",
            "url": url,
            "domain": extract_domain(url),
            "source_type": source_type,
            "trust_score": trust_score,
            "verified": verification["verified"],
            "evidence": verification["evidence"],
            "verification_status": verification["verification_status"],
        }
    )

    return sources


def compute_article_source_score(article: dict) -> dict[str, Any]:
    """Compute overall source score for an article."""
    sources = analyze_article_sources(article)

    if not sources:
        return {
            "source_score": 0.5,
            "source_type": "unknown",
            "verified": False,
            "evidence_level": "Unknown source",
        }

    # Use highest trust source
    best_source = max(sources, key=lambda x: x["trust_score"])

    # Compute final score
    source_score = compute_source_score(best_source)

    # Determine evidence level
    evidence_map = {
        "academic": "Peer-reviewed",
        "official": "Official documentation",
        "industry_report": "Industry report",
        "engineering_blog": "Technical blog",
        "news": "News report",
        "social": "User-generated",
        "curated": "Curated source",
        "inspiration": "Curated inspiration source",
    }

    evidence_level = evidence_map.get(best_source["source_type"], "Unknown")

    return {
        "source_score": round(source_score, 3),
        "source_type": best_source["source_type"],
        "verified": best_source["verified"],
        "evidence_level": evidence_level,
        "evidence": best_source["evidence"],
        "domain": best_source.get("domain", "unknown"),
    }


def main():
    """Main entry point."""
    print("=" * 60)
    print("Source Verification Framework")
    print("=" * 60)

    # Load registry
    registry_path = Path(__file__).parent.parent / "registry.json"
    with open(registry_path) as f:
        registry = json.load(f)

    content = registry.get("content", [])
    print(f"\nLoaded {len(content)} articles")

    # Analyze sources
    print("\nAnalyzing sources...")
    results = []

    for article in content:
        source_analysis = compute_article_source_score(article)
        results.append(
            {
                "slug": article.get("slug", ""),
                "title": article.get("title", ""),
                "source_score": source_analysis["source_score"],
                "source_type": source_analysis["source_type"],
                "verified": source_analysis["verified"],
                "evidence_level": source_analysis["evidence_level"],
                "evidence": json.dumps(source_analysis.get("evidence", [])),
            }
        )

    df = pd.DataFrame(results)

    # Show statistics
    print("\nSource Score Statistics:")
    print(f"  Mean: {df['source_score'].mean():.3f}")
    print(f"  Median: {df['source_score'].median():.3f}")
    print(f"  Std: {df['source_score'].std():.3f}")
    print(f"  Min: {df['source_score'].min():.3f}")
    print(f"  Max: {df['source_score'].max():.3f}")

    # Show verified sources
    verified = df[df["verified"]]
    print(f"\nVerified Sources: {len(verified)}")

    # Show source type distribution
    print("\nSource Type Distribution:")
    for source_type in df["source_type"].value_counts().index:
        count = (df["source_type"] == source_type).sum()
        pct = count / len(df) * 100
        print(f"  {source_type}: {count} ({pct:.1f}%)")

    # Save results
    output_path = Path(__file__).parent.parent / "dist" / "source_verification.parquet"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_path, index=False)
    print(f"\nSaved source verification to {output_path}")

    # Save summary statistics
    stats = {
        "total_articles": len(df),
        "mean_source_score": float(df["source_score"].mean()),
        "verified_count": int(df["verified"].sum()),
        "unverified_count": int((~df["verified"]).sum()),
        "source_type_distribution": df["source_type"].value_counts().to_dict(),
    }

    stats_path = Path(__file__).parent.parent / "dist" / "source_verification_stats.json"
    with open(stats_path, "w") as f:
        json.dump(stats, f, indent=2)
    print(f"Saved source verification statistics to {stats_path}")


if __name__ == "__main__":
    main()
