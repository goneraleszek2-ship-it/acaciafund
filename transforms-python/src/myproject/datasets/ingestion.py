"""
AcaciaFund Ingestion Transform
"""

import pandas as pd
from transforms.api import transform, Input, Output
from myproject.config import DatasetPaths


@transform(
    source_data=Input(DatasetPaths.SOURCE_DATASET),
    ingested_output=Output(DatasetPaths.CLEANED_DATA),
)
def ingest_articles(source_data, ingested_output):
    df = source_data.pandas()
    df = df.copy()
    df["ingestion_version"] = "v2.0"
    ingested_output.write_dataframe(df)


@transform(
    metadata_output=Output(DatasetPaths.SOURCE_METADATA),
)
def create_source_metadata(metadata_output):
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
    })
    metadata_output.write_dataframe(df)
