"""
AcaciaFund Data Processing Transform
Processes and enriches data for the static site.
"""

import polars as pl
from datetime import datetime, timezone
from transforms.api import transform, Input, Output, LightweightInput, LightweightOutput
from myproject.config import DatasetPaths


@transform.using(
    output=Output(DatasetPaths.PROCESSED_DATA),
    quality=Input(DatasetPaths.QUALITY_SCORES),
    trends=Input(DatasetPaths.TREND_ANALYSIS),
    concepts=Input(DatasetPaths.ONTOLOGY_CONCEPTS),
)
def process(
    quality: LightweightInput,
    trends: LightweightInput,
    concepts: LightweightInput,
    output: Output
) -> None:
    """
    Process and enrich data for static site.
    """
    try:
        df_quality = quality.polars(lazy=True)
        df_trends = trends.polars(lazy=True)
        df_concepts = concepts.polars(lazy=True)
        
        df = df_quality.join(df_trends, on="source_id", how="left")
        
        concept_count = df_concepts.group_by("concept_type").agg(
            pl.len().alias("concept_count")
        )
        
        df = df.with_columns([
            pl.lit(datetime.now(timezone.utc)).alias("processed_timestamp"),
            pl.lit("v2.0").alias("processed_version"),
        ])
        
        output.write_table(df)
        
        print(f"Processing completed: {df.select(pl.len()).collect()} records")
        
    except Exception as e:
        print(f"Error in processing: {str(e)}")
        raise


@transform.using(
    output=Output(DatasetPaths.CONTENT_CLUSTERS),
    processed=Input(DatasetPaths.PROCESSED_DATA),
)
def content_clusters(processed: LightweightInput, output: Output) -> None:
    """
    Generate content clusters based on tags and topics.
    """
    try:
        df = processed.polars(lazy=True)
        
        df_clusters = df.group_by("pillar").agg([
            pl.len().alias("article_count"),
            pl.col("overall_quality_score").mean().alias("avg_quality"),
            pl.col("trend_strength").mean().alias("avg_trend"),
        ])
        
        df_clusters = df_clusters.with_columns([
            pl.lit(datetime.now(timezone.utc)).alias("cluster_timestamp"),
        ])
        
        output.write_table(df_clusters)
        
    except Exception as e:
        print(f"Error in content_clusters: {str(e)}")
        raise


@transform.using(
    output=Output(DatasetPaths.LEARNING_PATHS),
    processed=Input(DatasetPaths.PROCESSED_DATA),
)
def learning_paths(processed: LightweightInput, output: Output) -> None:
    """
    Generate learning paths based on content relationships.
    """
    try:
        df = processed.polars(lazy=True)
        
        df_paths = df.group_by("pillar").agg([
            pl.col("source_id").sort_by(pl.col("trend_strength"), descending=True).head(5).alias("top_articles"),
            pl.col("trend_strength").mean().alias("pillar_strength"),
        ])
        
        df_paths = df_paths.with_columns([
            pl.lit(datetime.now(timezone.utc)).alias("paths_timestamp"),
        ])
        
        output.write_table(df_paths)
        
    except Exception as e:
        print(f"Error in learning_paths: {str(e)}")
        raise
