"""
AcaciaFund Data Processing Transform
Processes and enriches data for the static site.
"""

import polars as pl
from datetime import datetime, timezone
from transforms.api import transform, Input, Output, LightweightInput, LightweightOutput


@transform.using(
    output=Output("/TierPalan-95733d/Acacia/acaciafund-pipeline/processed_data"),
    quality=Input("/TierPalan-95733d/Acacia/acaciafund-pipeline/quality_scores"),
    trends=Input("/TierPalan-95733d/Acacia/acaciafund-pipeline/trend_analysis"),
    concepts=Input("/TierPalan-95733d/Acacia/acaciafund-pipeline/ontology_concepts"),
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
    df_quality = quality.polars(lazy=True)
    df_trends = trends.polars(lazy=True)
    df_concepts = concepts.polars(lazy=True)
    
    # Join quality and trends
    df = df_quality.join(df_trends, on="source_id", how="left")
    
    # Add concept count
    concept_count = df_concepts.group_by("concept_type").agg(
        pl.len().alias("concept_count")
    )
    
    df = df.with_columns([
        pl.lit(datetime.now(timezone.utc)).alias("processed_timestamp"),
        pl.lit("v1.0").alias("processed_version"),
    ])
    
    output.write_table(df)


@transform.using(
    output=Output("/TierPalan-95733d/Acacia/acaciafund-pipeline/content_clusters"),
    processed=Input("/TierPalan-95733d/Acacia/acaciafund-pipeline/processed_data"),
)
def content_clusters(processed: LightweightInput, output: Output) -> None:
    """
    Generate content clusters based on tags and topics.
    """
    df = processed.polars(lazy=True)
    
    # Group by pillar for content clusters
    df_clusters = df.group_by("pillar").agg([
        pl.len().alias("article_count"),
        pl.col("overall_quality_score").mean().alias("avg_quality"),
        pl.col("trend_strength").mean().alias("avg_trend"),
    ])
    
    df_clusters = df_clusters.with_columns([
        pl.lit(datetime.now(timezone.utc)).alias("cluster_timestamp"),
    ])
    
    output.write_table(df_clusters)


@transform.using(
    output=Output("/TierPalan-95733d/Acacia/acaciafund-pipeline/learning_paths"),
    processed=Input("/TierPalan-95733d/Acacia/acaciafund-pipeline/processed_data"),
)
def learning_paths(processed: LightweightInput, output: Output) -> None:
    """
    Generate learning paths based on content relationships.
    """
    df = processed.polars(lazy=True)
    
    # Create learning paths based on trend strength
    df_paths = df.group_by("pillar").agg([
        pl.col("source_id").sort_by(pl.col("trend_strength"), descending=True).head(5).alias("top_articles"),
        pl.col("trend_strength").mean().alias("pillar_strength"),
    ])
    
    df_paths = df_paths.with_columns([
        pl.lit(datetime.now(timezone.utc)).alias("paths_timestamp"),
    ])
    
    output.write_table(df_paths)
