#!/usr/bin/env python3
"""
Daily Sync Script - Synchronizes Foundry data with local workspace

This script runs daily to:
1. Pull latest data from Foundry datasets
2. Update local registry.duckdb cache
3. Update local registry.json backup
4. Generate checksums for verification

Usage:
    python scripts/daily_sync.py [--foundry-only] [--local-only]

Environment Variables:
    FOUNDRY_TOKEN: Foundry bearer token
    FOUNDRY_HOST: Foundry host (default: tierpalan.euw-3.palantirfoundry.co.uk)

Schedule (cron):
    0 6 * * * cd /root/acaciafund && python scripts/daily_sync.py
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import duckdb
import pandas as pd

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from foundry_dev_tools import FoundryContext, JWTTokenProvider, Config


def get_foundry_client() -> FoundryContext | None:
    """Create and return a Foundry context if token is available."""
    token = os.environ.get("FOUNDRY_TOKEN")
    if not token:
        print("FOUNDRY_TOKEN not set, skipping Foundry sync")
        return None
    
    host = os.environ.get("FOUNDRY_HOST", "tierpalan.euw-3.palantirfoundry.co.uk")
    
    token_provider = JWTTokenProvider(
        host=host,
        jwt=token
    )
    
    config = Config(
        requests_ca_bundle=None,
        debug=False
    )
    
    return FoundryContext(config=config, token_provider=token_provider)


def compute_file_checksum(filepath: Path) -> str:
    """Compute SHA256 checksum of a file."""
    sha256 = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            sha256.update(chunk)
    return sha256.hexdigest()


def update_registry_json() -> None:
    """Update local registry.json from DuckDB cache (partial data only)."""
    print("\nUpdating registry.json from DuckDB cache...")
    
    registry_path = PROJECT_ROOT / "registry.json"
    duckdb_path = PROJECT_ROOT / "dist" / "registry.duckdb"
    
    if not duckdb_path.exists():
        print("  DuckDB cache not found, skipping")
        return
    
    conn = duckdb.connect(str(duckdb_path))
    
    # Get all articles (basic fields only - DuckDB doesn't have section_images, bloom_questions, signals)
    articles = conn.execute("""
        SELECT 
            slug,
            title,
            description,
            content_type,
            pillar,
            tags,
            created_at,
            author,
            language,
            category,
            difficulty,
            featured_image,
            body_html
        FROM articles
    """).fetchall()
    
    conn.close()
    
    # Convert to list of dicts
    articles_list = []
    for row in articles:
        articles_list.append({
            "slug": row[0],
            "title": row[1],
            "description": row[2],
            "content_type": row[3],
            "pillar": row[4],
            "tags": json.loads(row[5]) if row[5] else [],
            "created_at": row[6],
            "author": row[7],
            "language": row[8],
            "category": row[9],
            "difficulty": row[10],
            "featured_image": row[11],
            "body_html": row[12],
        })
    
    # Update registry (partial update - only basic fields)
    with open(registry_path) as f:
        registry = json.load(f)
    
    # Merge: keep section_images, bloom_questions, signals from original
    for i, item in enumerate(registry.get("content", [])):
        if i < len(articles_list):
            # Update basic fields from DuckDB
            for key in articles_list[i]:
                if key not in ['section_images', 'bloom_questions', 'signals', 'curated_relations', 'prerequisites', 'thumbnail_svg']:
                    item[key] = articles_list[i][key]
    
    registry["last_run"] = datetime.now(timezone.utc).isoformat()
    
    with open(registry_path, 'w') as f:
        json.dump(registry, f, indent=2)
    
    print(f"  Updated {len(articles_list)} articles in registry.json (preserved section_images, bloom_questions, signals)")


def update_duckdb_cache() -> None:
    """Update DuckDB cache from local registry.json."""
    print("\nUpdating DuckDB cache from registry.json...")
    
    registry_path = PROJECT_ROOT / "registry.json"
    duckdb_path = PROJECT_ROOT / "dist" / "registry.duckdb"
    
    if not registry_path.exists():
        print("  registry.json not found, skipping")
        return
    
    with open(registry_path) as f:
        registry = json.load(f)
    
    content = registry.get("content", [])
    
    # Create DuckDB database
    if duckdb_path.exists():
        duckdb_path.unlink()
    
    conn = duckdb.connect(str(duckdb_path))
    
    # Articles table
    articles_data = []
    for item in content:
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
    
    # Signals table
    signals_data = []
    for item in content:
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
    
    # Images table
    images_data = []
    for item in content:
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
    
    conn.close()
    
    print(f"  Created DuckDB cache with {len(content)} articles, {len(signals_data)} signals, {len(images_data)} images")


def generate_checksums() -> None:
    """Generate checksums for all output files."""
    print("\nGenerating checksums...")
    
    checksums = {}
    
    output_dir = PROJECT_ROOT / "dist"
    for filename in ["registry.json", "registry.parquet", "registry.duckdb", 
                     "sqi_scores.parquet", "sqi_stats.json", "ontology.json"]:
        filepath = output_dir / filename
        if filepath.exists():
            checksums[filename] = compute_file_checksum(filepath)
    
    checksums_path = output_dir / "checksums.json"
    with open(checksums_path, 'w') as f:
        json.dump(checksums, f, indent=2)
    
    print(f"  Generated checksums for {len(checksums)} files")
    print(f"  Saved to {checksums_path}")


def main():
    """Main entry point."""
    print("=" * 60)
    print("Daily Sync - AcaciaFund Foundry Integration")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 60)
    
    # Check command line arguments
    foundry_only = "--foundry-only" in sys.argv
    local_only = "--local-only" in sys.argv
    
    # Update DuckDB cache from registry.json
    if not foundry_only:
        update_duckdb_cache()
    
    # Get Foundry client
    ctx = get_foundry_client()
    
    # Sync from Foundry
    if ctx and not local_only:
        print("\nSyncing from Foundry...")
        # TODO: Implement Foundry data pull
        print("  Foundry sync not yet implemented")
    
    # Update registry.json from DuckDB
    if not foundry_only:
        update_registry_json()
    
    # Generate checksums
    generate_checksums()
    
    print("\n" + "=" * 60)
    print("Sync complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
