"""
AcaciaFund Ingestion Transform
Collects and ingests articles from multiple sources into Foundry datasets.
"""

import polars as pl
from datetime import datetime, timezone
from transforms.api import transform, Input, Output, LightweightInput, LightweightOutput
from myproject.config import DatasetPaths


@transform.using(
    output=Output(DatasetPaths.CLEANED_DATA),
    sources=Input(DatasetPaths.SOURCE_DATASET),
)
def compute(
    sources: LightweightInput,
    output: LightweightOutput
) -> None:
    """
    Ingest articles from multiple sources into Foundry dataset.
    """
    try:
        df = sources.polars(lazy=True)
        
        df = df.with_columns([
            pl.lit(datetime.now(timezone.utc)).alias("ingestion_timestamp"),
            pl.lit("v2.0").alias("ingestion_version"),
        ])
        
        output.write_table(df)
        
        # Log success
        print(f"Ingestion completed: {df.select(pl.len()).collect()} records")
        
    except Exception as e:
        print(f"Error in ingestion: {str(e)}")
        raise


@transform.using(
    output=Output("source_metadata"),
)
def source_metadata(output: Output) -> None:
    """
    Generate source metadata for all ingested articles.
    """
    try:
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
        
    except Exception as e:
        print(f"Error in source_metadata: {str(e)}")
        raise
