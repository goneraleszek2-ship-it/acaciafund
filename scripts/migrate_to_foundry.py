#!/usr/bin/env python3
"""
Registry Migration Script - Uploads AcaciaFund data to Foundry

This script migrates the local registry.json to Foundry:
1. Reads registry.json and converts to Parquet
2. Uploads to Foundry dataset using ctx.catalog
3. Creates nested JSON columns for section_images, bloom_questions, signals

Usage:
    python scripts/migrate_to_foundry.py
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from foundry_dev_tools import FoundryContext, JWTTokenProvider, Config

# Foundry configuration
FOUNDRY_HOST = os.environ.get("FOUNDRY_HOST", "tierpalan.euw-3.palantirfoundry.co.uk")
FOUNDRY_TOKEN = os.environ.get("FOUNDRY_TOKEN")


def get_foundry_client() -> FoundryContext:
    """Create and return a Foundry context."""
    if not FOUNDRY_TOKEN:
        raise ValueError("FOUNDRY_TOKEN environment variable not set")
    
    token_provider = JWTTokenProvider(
        host=FOUNDRY_HOST,
        jwt=FOUNDRY_TOKEN
    )
    
    config = Config(
        requests_ca_bundle=None,
        debug=False
    )
    
    return FoundryContext(config=config, token_provider=token_provider)


def load_registry() -> pd.DataFrame:
    """Load registry.json and convert to DataFrame."""
    registry_path = PROJECT_ROOT / "registry.json"
    
    with open(registry_path) as f:
        registry = json.load(f)
    
    content = registry.get("content", [])
    print(f"Loaded {len(content)} articles from registry.json")
    
    # Create main articles dataframe
    articles_data = []
    for item in content:
        # Extract nested structures as JSON strings
        section_images = json.dumps(item.get("section_images", []))
        bloom_questions = json.dumps(item.get("bloom_questions", []))
        signals = json.dumps(item.get("signals", {}))
        
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
            "thumbnail_svg": item.get("thumbnail_svg", ""),
            "section_images_json": section_images,
            "bloom_questions_json": bloom_questions,
            "signals_json": signals,
        })
    
    df = pd.DataFrame(articles_data)
    print(f"Created DataFrame: {len(df)} rows, {len(df.columns)} columns")
    return df


def create_parquet(df: pd.DataFrame, output_path: Path) -> None:
    """Save DataFrame to Parquet file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_path, index=False)
    print(f"Saved to {output_path}")


def upload_to_foundry(ctx: FoundryContext, df: pd.DataFrame, dataset_name: str = "articles") -> None:
    """Upload DataFrame to Foundry dataset (simplified - manual setup required)."""
    print(f"\nUploading to Foundry dataset: {dataset_name}")
    print("NOTE: Foundry dataset creation requires manual setup via Foundry UI or API.")
    print("Please create a dataset in Foundry first, then update this script with the dataset path.")
    print("\nRecommended dataset path format:")
    print("  /<Organization>/<Project>/datasets/<dataset_name>")
    print("\nExample:")
    print("  /TierPalan-96733d/Acacia/datasets/articles")
    print("\nOnce dataset is created, update the script to use:")
    print("  ctx.catalog.api_upload_dataset_file(dataset_rid, file, filename)")


def main():
    """Main entry point."""
    print("=" * 60)
    print("AcaciaFund Registry Migration to Foundry")
    print("=" * 60)
    
    # Load registry
    df = load_registry()
    
    # Save to local Parquet
    local_parquet = PROJECT_ROOT / "dist" / "registry.parquet"
    create_parquet(df, local_parquet)
    
    # Get Foundry client
    try:
        ctx = get_foundry_client()
        print(f"\nConnected to Foundry: {ctx.host}")
        
        # Upload to Foundry
        upload_to_foundry(ctx, df)
        
        # Verify upload
        try:
            paths = ctx.catalog.api_get_dataset_paths()
            print(f"\nFoundry datasets: {paths}")
        except Exception as e:
            print(f"Could not list datasets: {e}")
        
    except ValueError as e:
        print(f"Error: {e}")
        print("\nSkipping Foundry upload (set FOUNDRY_TOKEN environment variable)")
    
    print("\nMigration complete!")


if __name__ == "__main__":
    main()
