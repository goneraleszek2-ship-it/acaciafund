#!/usr/bin/env python3
"""
Foundry Workflow Orchestration Script

This script orchestrates the Foundry intelligence workflows:
1. Ingestion: Collect technology intelligence from authoritative sources
2. Scoring: Score source credibility and evidence quality
3. Analysis: Detect emerging trends and technology adoption patterns
4. Ontology: Maintain technology ontology and concept relationships
5. Export: Generate validated outputs for static site consumption

Usage:
    python scripts/foundry_workflow.py ingest
    python scripts/foundry_workflow.py score
    python scripts/foundry_workflow.py analyze
    python scripts/foundry_workflow.py ontology
    python scripts/foundry_workflow.py export
    python scripts/foundry_workflow.py sync
    python scripts/foundry_workflow.py full

Environment Variables:
    FOUNDRY_TOKEN: Foundry bearer token
    FOUNDRY_HOST: Foundry host (default: tierpalan.euw-3.palantirfoundry.co.uk)
"""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Local modules
from scripts.quality_engine import compute_quality_score
from scripts.source_verification import compute_article_source_score
from scripts.trend_detection import analyze_article_trends


def print_header(title: str) -> None:
    """Print a formatted header."""
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print('=' * 70)


def load_registry() -> dict:
    """Load registry.json."""
    registry_path = PROJECT_ROOT / "registry.json"
    with open(registry_path) as f:
        return json.load(f)


def save_parquet(df: pd.DataFrame, filename: str) -> Path:
    """Save DataFrame to dist/ directory."""
    output_path = PROJECT_ROOT / "dist" / filename
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_path, index=False)
    print(f"  Saved: {output_path}")
    return output_path


def save_json(data: dict | list, filename: str) -> Path:
    """Save data to dist/ directory."""
    output_path = PROJECT_ROOT / "dist" / filename
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"  Saved: {output_path}")
    return output_path


# ── Ingestion Workflow ───────────────────────────────────────────────────────

def run_ingestion() -> None:
    """Run ingestion workflow - collect technology intelligence."""
    print_header("Ingestion Workflow")
    
    print("\nIngestion workflow simulates data collection from authoritative sources.")
    print("In production, this would:")
    print("  - Crawl academic repositories (arXiv, PubMed)")
    print("  - Fetch official documentation (GitHub, GitLab)")
    print("  - Download industry reports (Gartner, Forrester)")
    print("  - Monitor engineering blogs (AWS, Google Cloud)")
    print("  - Track regulatory filings (SEC, FATF)")
    
    # Simulate ingestion metadata
    registry = load_registry()
    content = registry.get("content", [])
    
    print(f"\nIngested {len(content)} articles from registry.json")
    
    # Create ingestion metadata dataset
    ingestion_data = []
    for item in content:
        ingestion_data.append({
            "source_id": item.get("slug", ""),
            "url": item.get("url", ""),
            "title": item.get("title", ""),
            "published_date": item.get("created_at", ""),
            "source_type": "curated",
            "domain": "acaciafund.org",
            "ingestion_timestamp": datetime.now(timezone.utc).isoformat(),
            "metadata_json": json.dumps({
                "tags": item.get("tags", []),
                "content_type": item.get("content_type", ""),
                "pillar": item.get("pillar", ""),
            }),
        })
    
    df = pd.DataFrame(ingestion_data)
    save_parquet(df, "foundry_ingestion.parquet")


# ── Scoring Workflow ─────────────────────────────────────────────────────────

def run_scoring() -> None:
    """Run scoring workflow - score source credibility and evidence quality."""
    print_header("Scoring Workflow")
    
    registry = load_registry()
    content = registry.get("content", [])
    
    print(f"Scoring {len(content)} articles...")
    
    scoring_data = []
    for item in content:
        # Quality score
        quality = compute_quality_score(item)
        
        # Source verification
        source = compute_article_source_score(item)
        
        scoring_data.append({
            "source_id": item.get("slug", ""),
            "credibility_score": quality["source_credibility"],
            "technical_accuracy_score": quality["technical_accuracy"],
            "practical_value_score": quality["practical_value"],
            "freshness_score": quality["freshness"],
            "trend_relevance_score": quality["trend_relevance"],
            "educational_quality_score": quality["educational_quality"],
            "overall_quality_score": quality["quality_score"],
            "evidence_level": source["evidence_level"],
            "verification_status": "verified" if source["verified"] else "unverified",
            "verification_evidence": json.dumps(source["evidence"]),
            "scoring_timestamp": datetime.now(timezone.utc).isoformat(),
            "scoring_model_version": "1.0.0",
        })
    
    df = pd.DataFrame(scoring_data)
    output_path = save_parquet(df, "foundry_scoring.parquet")
    
    # Show statistics
    print(f"\nScoring Statistics:")
    print(f"  Mean quality score: {df['overall_quality_score'].mean():.3f}")
    print(f"  Verified sources: {(df['verification_status'] == 'verified').sum()}")
    print(f"  Unverified sources: {(df['verification_status'] == 'unverified').sum()}")
    
    return output_path


# ── Analysis Workflow ────────────────────────────────────────────────────────

def run_analysis() -> None:
    """Run analysis workflow - detect emerging trends and technology adoption."""
    print_header("Analysis Workflow")
    
    registry = load_registry()
    content = registry.get("content", [])
    
    print(f"Analyzing {len(content)} articles...")
    
    analysis_data = []
    for item in content:
        trend = analyze_article_trends(item)
        
        analysis_data.append({
            "source_id": item.get("slug", ""),
            "trend_strength": trend["trend_strength"],
            "adoption_level": trend["adoption_level"],
            "impact_level": trend["impact_level"],
            "trend_categories": json.dumps(trend["trend_categories"]),
            "detected_keywords": json.dumps(trend["found_keywords"]),
            "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
            "analysis_model_version": "1.0.0",
        })
    
    df = pd.DataFrame(analysis_data)
    output_path = save_parquet(df, "foundry_analysis.parquet")
    
    # Show statistics
    print(f"\nAnalysis Statistics:")
    print(f"  Mean trend strength: {df['trend_strength'].mean():.1f}")
    print(f"  Max trend strength: {df['trend_strength'].max():.1f}")
    
    return output_path


# ── Ontology Workflow ────────────────────────────────────────────────────────

def run_ontology() -> None:
    """Run ontology workflow - maintain technology ontology and concept relationships."""
    print_header("Ontology Workflow")
    
    registry = load_registry()
    content = registry.get("content", [])
    
    print("Extracting concepts from articles...")
    
    # Collect all tags as concepts
    all_tags = set()
    for item in content:
        all_tags.update(item.get("tags", []))
    
    print(f"  Found {len(all_tags)} unique tags/concepts")
    
    # Extract pillar relationships
    pillars = set()
    for item in content:
        if item.get("pillar"):
            pillars.add(item["pillar"])
    
    print(f"  Found {len(pillars)} pillars")
    
    # Build concept hierarchy
    concepts_data = []
    concept_id = 0
    
    # Add pillars as top-level concepts
    for pillar in sorted(pillars):
        concept_id += 1
        concepts_data.append({
            "concept_id": f"CON_{concept_id:04d}",
            "concept_name": pillar,
            "concept_type": "pillar",
            "description": f"AcaciaFund {pillar} pillar",
            "parent_concept_id": None,
            "child_concepts": json.dumps([]),
            "related_concepts": json.dumps([]),
            "synonyms": json.dumps([pillar.replace("-", " ")]),
            "domain_coverage": 1.0,
            "last_updated": datetime.now(timezone.utc).isoformat(),
        })
    
    # Add tags as concepts
    for tag in sorted(all_tags):
        concept_id += 1
        concepts_data.append({
            "concept_id": f"CON_{concept_id:04d}",
            "concept_name": tag,
            "concept_type": "technology",
            "description": f"Technology concept: {tag}",
            "parent_concept_id": None,  # Could be inferred from tags
            "child_concepts": json.dumps([]),
            "related_concepts": json.dumps([]),
            "synonyms": json.dumps([tag.replace("-", " ")]),
            "domain_coverage": 0.0,  # Will be calculated
            "last_updated": datetime.now(timezone.utc).isoformat(),
        })
    
    df = pd.DataFrame(concepts_data)
    output_path = save_parquet(df, "foundry_ontology_concepts.parquet")
    
    # Build relationships (co-occurrence-based)
    relationships_data = []
    rel_id = 0
    
    # Simple co-occurrence: tags that appear together in same article
    for item in content:
        tags = item.get("tags", [])
        if len(tags) > 1:
            for i, tag1 in enumerate(tags):
                for tag2 in tags[i+1:]:
                    rel_id += 1
                    relationships_data.append({
                        "relationship_id": f"REL_{rel_id:04d}",
                        "source_concept_id": f"CON_{tag1.replace('-', '_').upper()}_0001",
                        "target_concept_id": f"CON_{tag2.replace('-', '_').upper()}_0001",
                        "relationship_type": "cooccurs_with",
                        "strength": 0.5,
                        "evidence_sources": json.dumps([item["slug"]]),
                        "created_at": datetime.now(timezone.utc).isoformat(),
                    })
    
    df_rel = pd.DataFrame(relationships_data)
    save_parquet(df_rel, "foundry_ontology_relationships.parquet")
    
    # Export to JSON for static site
    ontology_json = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0",
        "concepts": concepts_data,
        "relationships": relationships_data,
    }
    save_json(ontology_json, "foundry_ontology.json")
    
    print(f"\nOntology Statistics:")
    print(f"  Concepts: {len(concepts_data)}")
    print(f"  Relationships: {len(relationships_data)}")
    
    return output_path


# ── Export Workflow ──────────────────────────────────────────────────────────

def run_export() -> None:
    """Run export workflow - generate validated outputs for static site."""
    print_header("Export Workflow")
    
    # Load pre-computed data
    scoring_path = PROJECT_ROOT / "dist" / "foundry_scoring.parquet"
    analysis_path = PROJECT_ROOT / "dist" / "foundry_analysis.parquet"
    
    if not scoring_path.exists() or not analysis_path.exists():
        print("  Running scoring and analysis first...")
        run_scoring()
        run_analysis()
    
    scoring_df = pd.read_parquet(scoring_path)
    analysis_df = pd.read_parquet(analysis_path)
    
    # Merge scoring and analysis
    merged = scoring_df.merge(analysis_df, on="source_id", how="left")
    
    # Export quality metrics for static site
    quality_metrics = []
    for _, row in merged.iterrows():
        quality_metrics.append({
            "article_slug": row["source_id"],
            "quality_score": row["overall_quality_score"],
            "source_credibility": row["credibility_score"],
            "technical_accuracy": row["technical_accuracy_score"],
            "practical_value": row["practical_value_score"],
            "freshness": row["freshness_score"],
            "trend_relevance": row["trend_relevance_score"],
            "educational_quality": row["educational_quality_score"],
            "source_type": "curated",
            "source_verified": row["verification_status"] == "verified",
            "evidence_level": row["evidence_level"],
            "trend_strength": row["trend_strength"],
            "adoption_level": row["adoption_level"],
            "impact_level": row["impact_level"],
            "export_timestamp": datetime.now(timezone.utc).isoformat(),
        })
    
    df = pd.DataFrame(quality_metrics)
    save_parquet(df, "quality_scores.parquet")
    
    # Export technology radar
    radar_entries = []
    for _, row in merged.iterrows():
        # Determine recommendation based on scores
        if row["overall_quality_score"] >= 0.8 and row["trend_strength"] >= 50:
            recommendation = "adopt"
        elif row["overall_quality_score"] >= 0.6 and row["trend_strength"] >= 30:
            recommendation = "trial"
        elif row["overall_quality_score"] >= 0.5:
            recommendation = "assess"
        else:
            recommendation = "hold"
        
        radar_entries.append({
            "concept_name": row["source_id"],
            "adoption_level": row["adoption_level"],
            "impact_level": row["impact_level"],
            "trend_strength": row["trend_strength"],
            "recommendation": recommendation,
            "rationale": f"Quality score: {row['overall_quality_score']:.2f}, Trend: {row['trend_strength']:.1f}",
            "evidence_count": 1,  # Could be enhanced with source count
            "quality_score": row["overall_quality_score"],
        })
    
    radar_data = {
        "radar_name": "AcaciaFund Technology Radar - Q2 2026",
        "radar_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "entries": radar_entries,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "exported_to_static": True,
    }
    
    save_json(radar_data, "technology_radar.json")
    
    print(f"\nExport Statistics:")
    print(f"  Quality metrics: {len(quality_metrics)}")
    print(f"  Radar entries: {len(radar_entries)}")
    
    # Show recommendations distribution
    recommendations = [e["recommendation"] for e in radar_entries]
    for rec in ["adopt", "trial", "assess", "hold"]:
        count = recommendations.count(rec)
        print(f"  {rec.upper()}: {count}")


# ── Sync Workflow ────────────────────────────────────────────────────────────

def run_sync() -> None:
    """Run sync workflow - synchronize with local workspace."""
    print_header("Sync Workflow")
    
    print("\nSyncing Foundry exports with local workspace...")
    
    # Export quality metrics
    run_export()
    
    # Update registry.json with quality metrics
    registry_path = PROJECT_ROOT / "registry.json"
    with open(registry_path) as f:
        registry = json.load(f)
    
    quality_path = PROJECT_ROOT / "dist" / "quality_scores.parquet"
    df = pd.read_parquet(quality_path)
    
    # Add quality metrics to registry
    quality_dict = {row["article_slug"]: row for _, row in df.iterrows()}
    
    for item in registry.get("content", []):
        slug = item.get("slug", "")
        if slug in quality_dict:
            item["quality_metrics"] = {
                "score": quality_dict[slug]["quality_score"],
                "source_verified": quality_dict[slug]["source_verified"],
                "evidence_level": quality_dict[slug]["evidence_level"],
                "trend_strength": quality_dict[slug]["trend_strength"],
                "adoption_level": quality_dict[slug]["adoption_level"],
            }
    
    with open(registry_path, 'w') as f:
        json.dump(registry, f, indent=2)
    
    print(f"  Updated registry.json with quality metrics for {len(quality_dict)} articles")
    
    # Generate checksums
    import hashlib
    checksums = {}
    for parquet_file in PROJECT_ROOT.glob("dist/*.parquet"):
        with open(parquet_file, 'rb') as f:
            checksums[parquet_file.name] = hashlib.sha256(f.read()).hexdigest()
    
    save_json(checksums, "checksums.json")
    
    print("  Generated checksums for verification")


# ── Full Workflow ────────────────────────────────────────────────────────────

def run_full() -> None:
    """Run full Foundry workflow pipeline."""
    print_header("Full Foundry Workflow Pipeline")
    
    start_time = time.time()
    
    print("\nStep 1: Ingestion")
    run_ingestion()
    
    print("\nStep 2: Scoring")
    run_scoring()
    
    print("\nStep 3: Analysis")
    run_analysis()
    
    print("\nStep 4: Ontology")
    run_ontology()
    
    print("\nStep 5: Export")
    run_export()
    
    elapsed = time.time() - start_time
    print(f"\n{'=' * 70}")
    print(f"  Full workflow completed in {elapsed:.1f} seconds")
    print('=' * 70)


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python foundry_workflow.py [command]")
        print("\nCommands:")
        print("  ingest  - Run ingestion workflow (collect technology intelligence)")
        print("  score   - Run scoring workflow (source credibility & quality)")
        print("  analyze - Run analysis workflow (trends & adoption patterns)")
        print("  ontology - Run ontology workflow (concept relationships)")
        print("  export  - Run export workflow (generate static outputs)")
        print("  sync    - Run sync workflow (update local workspace)")
        print("  full    - Run full workflow pipeline")
        print("  status  - Show workflow status")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "ingest":
        run_ingestion()
    elif command == "score":
        run_scoring()
    elif command == "analyze":
        run_analysis()
    elif command == "ontology":
        run_ontology()
    elif command == "export":
        run_export()
    elif command == "sync":
        run_sync()
    elif command == "full":
        run_full()
    elif command == "status":
        print_header("Foundry Workflow Status")
        print("\nFoundry Integration Status:")
        print("  - Ingestion: Ready (requires data sources)")
        print("  - Scoring: Ready (uses quality_engine.py)")
        print("  - Analysis: Ready (uses trend_detection.py)")
        print("  - Ontology: Ready (extracts from registry)")
        print("  - Export: Ready (generates static outputs)")
        print("\nLocal Workspace Status:")
        for f in PROJECT_ROOT.glob("dist/*.parquet"):
            print(f"  - {f.name}: {f.stat().st_size:,} bytes")
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
