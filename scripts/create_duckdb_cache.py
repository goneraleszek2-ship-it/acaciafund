#!/usr/bin/env python3
"""
DuckDB Local Cache - Creates optimized local database for fast queries

This script creates a DuckDB database with:
1. Articles table (main content)
2. Signals table (SQI scores)
3. Images table (image metadata)
4. Optimized views for common queries

Usage:
    python scripts/create_duckdb_cache.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import duckdb
import pandas as pd

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def load_registry() -> dict:
    """Load registry.json."""
    registry_path = PROJECT_ROOT / "registry.json"
    with open(registry_path) as f:
        return json.load(f)


def create_articles_table(conn: duckdb.DuckDBPyConnection, articles: list[dict]) -> None:
    """Create articles table from registry content."""
    # Flatten the data
    articles_data = []
    for item in articles:
        articles_data.append({
            "slug": item.get("slug", ""),
            "title": item.get("title", ""),
            "description": item.get("description", ""),
            "content_type": item.get("content_type", ""),
            "pillar": item.get("pillar", ""),
            "tags": json.dumps(item.get("tags", [])),
            "created_at": item.get("created_at", ""),
            "author": item.get("author", ""),
            "language": item.get("language", ""),
            "category": item.get("category", ""),
            "difficulty": item.get("difficulty", ""),
            "featured_image": item.get("featured_image", ""),
            "body_html": item.get("body_html", ""),
        })
    
    df = pd.DataFrame(articles_data)
    conn.execute("CREATE TABLE articles AS SELECT * FROM df")
    print(f"Created articles table: {len(df)} rows")


def create_signals_table(conn: duckdb.DuckDBPyConnection, articles: list[dict]) -> None:
    """Create signals table from registry content."""
    signals_data = []
    for item in articles:
        signals = item.get("signals", {})
        if signals:
            signals_data.append({
                "slug": item.get("slug", ""),
                "avg_sqi": signals.get("avg_sqi", 0),
                "avg_score": signals.get("avg_score", 0),
                "count": signals.get("count", 0),
                "domain_diversity": signals.get("domain_diversity", 0),
                "total_score": signals.get("total_score", 0),
            })
    
    df = pd.DataFrame(signals_data)
    conn.execute("CREATE TABLE signals AS SELECT * FROM df")
    print(f"Created signals table: {len(df)} rows")


def create_images_table(conn: duckdb.DuckDBPyConnection, articles: list[dict]) -> None:
    """Create images table from registry content."""
    images_data = []
    for item in articles:
        for si in item.get("section_images", []):
            images_data.append({
                "slug": item.get("slug", ""),
                "section_index": si.get("section_index"),
                "heading": si.get("heading", ""),
                "image_url": si.get("image_url", ""),
                "image_credit": si.get("image_credit", ""),
                "image_alt": si.get("image_alt", ""),
                "relevance_score": si.get("relevance_score", 0),
                "source_api": si.get("source_api", ""),
                "width": si.get("width", 0),
                "height": si.get("height", 0),
                "content_hash": si.get("content_hash", ""),
            })
    
    df = pd.DataFrame(images_data)
    conn.execute("CREATE TABLE images AS SELECT * FROM df")
    print(f"Created images table: {len(df)} rows")


def create_views(conn: duckdb.DuckDBPyConnection) -> None:
    """Create optimized views for common queries."""
    
    # View: Articles with SQI
    conn.execute("""
        CREATE VIEW articles_with_sqi AS
        SELECT 
            a.slug,
            a.title,
            a.content_type,
            a.pillar,
            a.tags,
            a.created_at,
            s.avg_sqi,
            s.avg_score
        FROM articles a
        LEFT JOIN signals s ON a.slug = s.slug
    """)
    print("Created view: articles_with_sqi")
    
    # View: Images with article info
    conn.execute("""
        CREATE VIEW images_with_articles AS
        SELECT 
            i.slug,
            i.section_index,
            i.heading,
            i.image_url,
            i.relevance_score,
            i.source_api,
            a.title as article_title,
            a.content_type,
            a.pillar
        FROM images i
        LEFT JOIN articles a ON i.slug = a.slug
    """)
    print("Created view: images_with_articles")
    
    # View: High quality articles (SQI >= 0.6)
    conn.execute("""
        CREATE VIEW high_quality_articles AS
        SELECT 
            a.slug,
            a.title,
            a.content_type,
            a.pillar,
            s.avg_sqi,
            s.avg_score
        FROM articles a
        LEFT JOIN signals s ON a.slug = s.slug
        WHERE s.avg_sqi >= 0.6
        ORDER BY s.avg_sqi DESC
    """)
    print("Created view: high_quality_articles")
    
    # View: Images by source
    conn.execute("""
        CREATE VIEW images_by_source AS
        SELECT 
            source_api,
            COUNT(*) as image_count,
            AVG(relevance_score) as avg_relevance
        FROM images
        GROUP BY source_api
        ORDER BY image_count DESC
    """)
    print("Created view: images_by_source")


def main():
    """Main entry point."""
    print("=" * 60)
    print("DuckDB Local Cache Creation")
    print("=" * 60)
    
    # Load registry
    registry = load_registry()
    content = registry.get("content", [])
    print(f"Loaded {len(content)} articles from registry.json")
    
    # Create DuckDB database
    output_path = PROJECT_ROOT / "dist" / "registry.duckdb"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Remove existing database
    if output_path.exists():
        output_path.unlink()
    
    conn = duckdb.connect(str(output_path))
    print(f"\nCreated DuckDB database: {output_path}")
    
    # Create tables
    print("\nCreating tables...")
    create_articles_table(conn, content)
    create_signals_table(conn, content)
    create_images_table(conn, content)
    
    # Create views
    print("\nCreating views...")
    create_views(conn)
    
    # Show statistics
    print("\nDatabase Statistics:")
    print(f"  Articles: {conn.execute('SELECT COUNT(*) FROM articles').fetchone()[0]}")
    print(f"  Signals: {conn.execute('SELECT COUNT(*) FROM signals').fetchone()[0]}")
    print(f"  Images: {conn.execute('SELECT COUNT(*) FROM images').fetchone()[0]}")
    
    # Verify views
    print("\nView Statistics:")
    print(f"  Articles with SQI: {conn.execute('SELECT COUNT(*) FROM articles_with_sqi').fetchone()[0]}")
    print(f"  High quality articles: {conn.execute('SELECT COUNT(*) FROM high_quality_articles').fetchone()[0]}")
    
    conn.close()
    
    print(f"\nDuckDB cache created: {output_path}")
    print("Use with: duckdb.connect('dist/registry.duckdb')")


if __name__ == "__main__":
    main()
