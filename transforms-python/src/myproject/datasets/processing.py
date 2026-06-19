"""
AcaciaFund Data Processing Transform
Processes and enriches data for the static site.
"""

import pandas as pd
from datetime import datetime, timezone
from transforms.api import transform, Input, Output, LightweightInput, LightweightOutput


@transform.using(
    output=Output("processed_data"),
    quality=Input("quality_scores"),
    trends=Input("trend_analysis"),
    concepts=Input("ontology_concepts"),
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
    df_quality = quality.pandas()
    df_trends = trends.pandas()
    df_concepts = concepts.pandas()
    
    df = df_quality.merge(df_trends, on="source_id", how="left")
    
    concept_count = df_concepts.groupby("concept_type").size().reset_index(name="concept_count")
    
    df["processed_timestamp"] = datetime.now(timezone.utc)
    df["processed_version"] = "v1.0"
    
    output.write_dataframe(df)


@transform.using(
    output=Output("content_clusters"),
    processed=Input("processed_data"),
)
def content_clusters(processed: LightweightInput, output: Output) -> None:
    """
    Generate content clusters based on tags and topics.
    """
    df = processed.pandas()
    
    df_clusters = df.groupby("pillar").agg({
        "source_id": "count",
        "overall_quality_score": "mean",
        "trend_strength": "mean",
    }).reset_index()
    df_clusters.columns = ["pillar", "article_count", "avg_quality", "avg_trend"]
    
    df_clusters["cluster_timestamp"] = datetime.now(timezone.utc)
    
    output.write_dataframe(df_clusters)


@transform.using(
    output=Output("learning_paths"),
    processed=Input("processed_data"),
)
def learning_paths(processed: LightweightInput, output: Output) -> None:
    """
    Generate learning paths based on content relationships.
    """
    df = processed.pandas()
    
    df_paths = df.groupby("pillar").agg({
        "source_id": lambda x: list(x.nlargest(5)),
        "trend_strength": "mean",
    }).reset_index()
    df_paths.columns = ["pillar", "top_articles", "pillar_strength"]
    
    df_paths["paths_timestamp"] = datetime.now(timezone.utc)
    
    output.write_dataframe(df_paths)
