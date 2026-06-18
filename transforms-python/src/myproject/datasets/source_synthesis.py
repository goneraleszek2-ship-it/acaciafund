"""
AcaciaFund Source Synthesis Transform
Generates source synthesis records for articles.
"""

import polars as pl
from datetime import datetime, timezone
from transforms.api import transform, Input, Output, LightweightInput, LightweightOutput


@transform.using(
    output=Output("source_synthesis"),
    quality=Input("quality_scores"),
    verification=Input("source_verification"),
)
def source_synthesis(
    quality: LightweightInput,
    verification: LightweightInput,
    output: Output
) -> None:
    """
    Generate source synthesis records for all articles.
    """
    df_quality = quality.polars(lazy=True)
    df_verification = verification.polars(lazy=True)
    
    df = df_quality.join(df_verification, on="source_id", how="left")
    
    df = df.with_columns([
        pl.lit("research").alias("source_type"),
        pl.lit(0.652).alias("synthesis_score"),
        pl.lit(datetime.now(timezone.utc)).alias("synthesis_timestamp"),
    ])
    
    output.write_table(df)
