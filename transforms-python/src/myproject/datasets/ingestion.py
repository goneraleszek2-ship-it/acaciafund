"""
AcaciaFund Ingestion Transform
"""

import pandas as pd
# Added 'lightweight' and 'LightweightOutput' for consistency if you migrate this file later,
# but keeping standard transform classes for now.
from transforms.api import transform, Input, Output, TransformInput, TransformOutput
from myproject.config import DatasetPaths


@transform(
    # 1. Update the input to look at your newly created mock source path instead of the real one
    source_data=Input("/TierPalan-95733d/Acacia/acaciafund-pipeline/mock_source_data"),
    # 2. Redirect the output to a temporary preview path to kill the collision with lightweight_transform.py
    ingested_output=Output("/TierPalan-95733d/Acacia/acaciafund-pipeline/preview_ingested_data"),
)
def ingest_articles(source_data: TransformInput, ingested_output: TransformOutput):
    df = source_data.pandas()
    df = df.copy()
    df["ingestion_version"] = "v2.0"
    ingested_output.write_dataframe(df)


@transform(
    metadata_output=Output(DatasetPaths.SOURCE_METADATA),
)
def create_source_metadata(metadata_output: TransformOutput):
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
