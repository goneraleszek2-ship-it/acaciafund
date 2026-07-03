"""Data loader module - loads and parses registry data."""

import json
from pathlib import Path
from typing import Any, Dict, List

from schemas import RegistryData


def load_registry(registry_path: Path) -> RegistryData:
    """Load and parse the registry.json file.

    Args:
        registry_path: Path to the registry.json file

    Returns:
        RegistryData object with parsed content
    """
    with open(registry_path, "r", encoding="utf-8") as f:
        registry_data = json.load(f)
    return RegistryData(**registry_data)


def get_content_by_type(registry: RegistryData, content_type: str) -> List[Any]:
    """Filter content by type.

    Args:
        registry: RegistryData object
        content_type: One of 'research', 'learn', 'knowledge'

    Returns:
        List of content items matching the type
    """
    return [c for c in registry.content if c.content_type == content_type]


def load_enrichment_data(output_dir: Path) -> Dict[str, Any]:
    """Load pre-computed enrichment data from dist/.

    Args:
        output_dir: Path to the dist/ directory

    Returns:
        Dictionary with enrichment data (trend_detection, source_verification, etc.)
    """
    import pandas as pd  # type: ignore[import-untyped]

    enrichment = {}

    # Trend detection
    trend_path = output_dir / "trend_detection.parquet"
    if trend_path.exists():
        df = pd.read_parquet(trend_path)
        enrichment["trend_detection"] = {row["slug"]: row for _, row in df.iterrows()}

    # Source verification
    source_path = output_dir / "source_verification.parquet"
    if source_path.exists():
        df = pd.read_parquet(source_path)
        source_verification = {}
        for _, row in df.iterrows():
            evidence = row.get("evidence", [])
            if isinstance(evidence, str):
                try:
                    evidence = json.loads(evidence)
                except Exception:
                    evidence = []
            source_verification[row["slug"]] = {
                "source_score": row["source_score"],
                "source_type": row["source_type"],
                "verified": row["verified"],
                "evidence_level": row["evidence_level"],
                "evidence": evidence,
            }
        enrichment["source_verification"] = source_verification

    # Source synthesis
    synthesis_path = output_dir / "source_synthesis.parquet"
    if synthesis_path.exists():
        df = pd.read_parquet(synthesis_path)
        source_synthesis = {}
        for slug, group in df.groupby("article_slug"):
            records = group.to_dict("records")
            for rec in records:
                if (
                    "key_insights" in rec
                    and hasattr(rec["key_insights"], "__iter__")
                    and not isinstance(rec["key_insights"], str)
                ):
                    rec["key_insights"] = list(rec["key_insights"])
            source_synthesis[slug] = records
        enrichment["source_synthesis"] = source_synthesis

    # Quality scores
    quality_path = output_dir / "quality_scores.parquet"
    if quality_path.exists():
        df = pd.read_parquet(quality_path)
        slug_col = "article_slug" if "article_slug" in df.columns else "slug"
        enrichment["quality_scores"] = {row[slug_col]: row for _, row in df.iterrows()}

    return enrichment
