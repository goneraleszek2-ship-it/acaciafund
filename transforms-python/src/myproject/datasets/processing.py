"""
AcaciaFund Data Processing Transform
Processes and enriches data for the static site.
"""

import pandas as pd
from transforms.api import transform, Input, Output


@transform(
    quality_data=Input("quality_scores"),
    trends_data=Input("trend_analysis"),
    concepts_data=Input("ontology_concepts"),
    processed_output=Output("processed_data"),
)
def process_data(quality_data, trends_data, concepts_data, processed_output):
    df_quality = quality_data.pandas()
    df_trends = trends_data.pandas()

    df = df_quality.merge(df_trends, on="source_id", how="left")

    df["processed_version"] = "v1.0"

    processed_output.write_dataframe(df)


@transform(
    processed_data=Input("processed_data"),
    clusters_output=Output("content_clusters"),
)
def generate_clusters(processed_data, clusters_output):
    df = processed_data.pandas()

    if "pillar" in df.columns:
        df_clusters = df.groupby("pillar").agg({
            "source_id": "count",
            "overall_quality_score": "mean",
            "trend_strength": "mean",
        }).reset_index()
        df_clusters.columns = ["pillar", "article_count", "avg_quality", "avg_trend"]
    else:
        df_clusters = pd.DataFrame({
            "pillar": pd.Series([], dtype=str),
            "article_count": pd.Series([], dtype=int),
            "avg_quality": pd.Series([], dtype=float),
            "avg_trend": pd.Series([], dtype=float),
        })

    clusters_output.write_dataframe(df_clusters)


@transform(
    processed_data=Input("processed_data"),
    paths_output=Output("learning_paths"),
)
def generate_learning_paths(processed_data, paths_output):
    df = processed_data.pandas()

    if "pillar" in df.columns:
        df_paths = df.groupby("pillar").agg({
            "source_id": "count",
            "trend_strength": "mean",
        }).reset_index()
        df_paths.columns = ["pillar", "article_count", "pillar_strength"]
    else:
        df_paths = pd.DataFrame({
            "pillar": pd.Series([], dtype=str),
            "article_count": pd.Series([], dtype=int),
            "pillar_strength": pd.Series([], dtype=float),
        })

    paths_output.write_dataframe(df_paths)
