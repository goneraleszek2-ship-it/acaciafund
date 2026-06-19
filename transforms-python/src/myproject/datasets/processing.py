"""
AcaciaFund Data Processing Transform
"""

import pandas as pd
from transforms.api import transform, Input, Output, TransformInput, TransformOutput
from myproject.config import DatasetPaths


@transform(
    quality_data=Input(DatasetPaths.QUALITY_SCORES),
    trends_data=Input(DatasetPaths.TREND_ANALYSIS),
    concepts_data=Input(DatasetPaths.ONTOLOGY_CONCEPTS),
    processed_output=Output(DatasetPaths.PROCESSED_DATA),
)
def process_data(quality_data: TransformInput, trends_data: TransformInput, concepts_data: TransformInput, processed_output: TransformOutput):
    df_quality = quality_data.pandas()
    df_trends = trends_data.pandas()

    df = df_quality.merge(df_trends, on="source_id", how="left")
    df["processed_version"] = "v1.0"

    processed_output.write_dataframe(df)


@transform(
    processed_data=Input(DatasetPaths.PROCESSED_DATA),
    clusters_output=Output(DatasetPaths.CONTENT_CLUSTERS),
)
def generate_clusters(processed_data: TransformInput, clusters_output: TransformOutput):
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
    processed_data=Input(DatasetPaths.PROCESSED_DATA),
    paths_output=Output(DatasetPaths.LEARNING_PATHS),
)
def generate_learning_paths(processed_data: TransformInput, paths_output: TransformOutput):
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
