"""
AcaciaFund Ingestion Transform
Collects and ingests articles from multiple sources into Foundry datasets.
"""

import pandas as pd
from datetime import datetime, timezone
from transforms.api import transform, Input, Output, LightweightInput, LightweightOutput


@transform.using(
    output=Output("acacia_portal_clean_data"),
    sources=Input("source_dataset"),
)
def compute(
    sources: LightweightInput,
    output: LightweightOutput
) -> None:
    """
    Ingest articles from multiple sources into Foundry dataset.
    """
    try:
        df = sources.pandas()
        
        df = df.copy()
        df["ingestion_timestamp"] = datetime.now(timezone.utc)
        df["ingestion_version"] = "v2.0"
        
        output.write_dataframe(df)
        
        print(f"Ingestion completed: {len(df)} records")
        
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
        df = pd.DataFrame({
            "source_id": pd.Series([], dtype=str),
            "source_api": pd.Series([], dtype=str),
            "source_url": pd.Series([], dtype=str),
            "source_title": pd.Series([], dtype=str),
            "source_domain": pd.Series([], dtype=str),
            "source_type": pd.Series([], dtype=str),
            "source_credibility": pd.Series([], dtype=float),
            "source_verified": pd.Series([], dtype=bool),
            "source_evidence": pd.Series([], dtype=str),
            "metadata_json": pd.Series([], dtype=str),
            "source_timestamp": pd.Series([], dtype="datetime64[ns, UTC]"),
        })
        
        output.write_dataframe(df)
        
    except Exception as e:
        print(f"Error in source_metadata: {str(e)}")
        raise
