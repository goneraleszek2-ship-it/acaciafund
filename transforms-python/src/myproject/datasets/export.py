"""
AcaciaFund Export Transform
Generates static outputs for the website.
"""

import polars as pl
from datetime import datetime, timezone
from transforms.api import transform, Input, Output, LightweightInput, LightweightOutput
from myproject.config import DatasetPaths


@transform.using(
    output=Output(DatasetPaths.EXPORT_QUALITY_METRICS),
    scoring=Input(DatasetPaths.QUALITY_SCORES),
    analysis=Input(DatasetPaths.TREND_ANALYSIS),
)
def quality_metrics(
    scoring: LightweightInput,
    analysis: LightweightInput,
    output: Output
) -> None:
    """
    Export quality metrics for static site consumption.
    """
    df_scoring = scoring.polars(lazy=True)
    df_analysis = analysis.polars(lazy=True)
    
    df = df_scoring.join(df_analysis, on="source_id", how="left")
    
    df = df.with_columns([
        pl.lit("curated").alias("source_type"),
        pl.col("verified").fill_null(pl.lit(True)).alias("source_verified"),
        pl.lit(datetime.now(timezone.utc)).alias("export_timestamp"),
    ])
    
    output.write_table(df)


@transform.using(
    output=Output(DatasetPaths.EXPORT_TECHNOLOGY_RADAR),
    scoring=Input(DatasetPaths.QUALITY_SCORES),
    analysis=Input(DatasetPaths.TREND_ANALYSIS),
)
def technology_radar(
    scoring: LightweightInput,
    analysis: LightweightInput,
    output: Output
) -> None:
    """
    Export technology radar recommendations.
    """
    df_scoring = scoring.polars(lazy=True)
    df_analysis = analysis.polars(lazy=True)
    
    df = df_scoring.join(df_analysis, on="source_id", how="left")
    
    df = df.with_columns([
        pl.when((pl.col("overall_quality_score") >= 0.8) & (pl.col("trend_strength") >= 50))
        .then(pl.lit("adopt"))
        .when((pl.col("overall_quality_score") >= 0.6) & (pl.col("trend_strength") >= 30))
        .then(pl.lit("trial"))
        .when(pl.col("overall_quality_score") >= 0.5)
        .then(pl.lit("assess"))
        .otherwise(pl.lit("hold"))
        .alias("recommendation"),
    ])
    
    df = df.with_columns([
        pl.lit("AcaciaFund Technology Radar - Q2 2026").alias("radar_name"),
        pl.lit(datetime.now(timezone.utc).strftime("%Y-%m-%d")).alias("radar_date"),
        pl.lit(datetime.now(timezone.utc)).alias("export_timestamp"),
    ])
    
    output.write_table(df)


@transform.using(
    output=Output(DatasetPaths.EXPORT_SOURCE_SYNTHESIS),
    scoring=Input(DatasetPaths.QUALITY_SCORES),
    verification=Input(DatasetPaths.SOURCE_VERIFICATION),
)
def source_synthesis(
    scoring: LightweightInput,
    verification: LightweightInput,
    output: Output
) -> None:
    """
    Export source synthesis records.
    """
    df_scoring = scoring.polars(lazy=True)
    df_verification = verification.polars(lazy=True)
    
    df = df_scoring.join(df_verification, on="source_id", how="left")
    
    df = df.with_columns([
        pl.lit("research").alias("source_type"),
        pl.lit(0.652).alias("synthesis_score"),
        pl.lit(datetime.now(timezone.utc)).alias("synthesis_timestamp"),
    ])
    
    output.write_table(df)
