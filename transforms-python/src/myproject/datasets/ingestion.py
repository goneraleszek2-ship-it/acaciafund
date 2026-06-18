"""
AcaciaFund Ingestion Transform
Collects and ingests articles from multiple sources into Foundry datasets.
"""

import polars as pl
from datetime import datetime, timezone
from transforms.api import transform, Input, Output, LightweightInput, LightweightOutput


@transform.using(
    output=Output("/TierPalan-95733d/Acacia/acaciafund-pipeline/acacia_portal_clean_data"),
    sources=Input("/TierPalan-95733d/Acacia/SOURCE_DATASET_PATH"),
)
def compute(
    sources: LightweightInput,
    output: LightweightOutput
) -> None:
    """
    Ingest articles from multiple sources into Foundry dataset.
    
    Sources:
    - arXiv (academic preprints)
    - PubMed (biomedical literature)
    - Semantic Scholar (academic papers)
    - GitHub/Stack Overflow (technical content)
    - HackerNews discussions
    """
    
    df = pl.DataFrame({
        "source_id": pl.Series([], dtype=pl.Utf8),
        "title": pl.Series([], dtype=pl.Utf8),
        "description": pl.Series([], dtype=pl.Utf8),
        "url": pl.Series([], dtype=pl.Utf8),
        "source_type": pl.Series([], dtype=pl.Utf8),
        "domain": pl.Series([], dtype=pl.Utf8),
        "tags": pl.Series([], dtype=pl.List(pl.Utf8)),
        "pillar": pl.Series([], dtype=pl.Utf8),
        "inferred_at": pl.Series([], dtype=pl.Datetime),
    })
    
    df = df.with_columns([
        pl.lit(datetime.now(timezone.utc)).alias("ingestion_timestamp"),
        pl.lit("v1.0").alias("ingestion_version"),
    ])
    
    output.write_table(df)


@transform.using(
    output=Output("/TierPalan-95733d/Acacia/acaciafund-pipeline/source_metadata"),
)
def source_metadata(output: Output) -> None:
    """
    Generate source metadata for all ingested articles.
    """
    df = pl.DataFrame({
        "source_id": pl.Series([], dtype=pl.Utf8),
        "source_api": pl.Series([], dtype=pl.Utf8),
        "source_url": pl.Series([], dtype=pl.Utf8),
        "source_title": pl.Series([], dtype=pl.Utf8),
        "source_domain": pl.Series([], dtype=pl.Utf8),
        "source_type": pl.Series([], dtype=pl.Utf8),
        "source_credibility": pl.Series([], dtype=pl.Float64),
        "source_verified": pl.Series([], dtype=pl.Boolean),
        "source_evidence": pl.Series([], dtype=pl.Utf8),
        "metadata_json": pl.Series([], dtype=pl.Utf8),
        "source_timestamp": pl.Series([], dtype=pl.Datetime),
    })
    
    output.write_table(df)
