"""
AcaciaFund Lightweight Transform
Clean and standardize AcaciaFund portal data.
"""

import pandas as pd
from transforms.api import transform, Input, Output, TransformInput, TransformOutput
from myproject.config import DatasetPaths


@transform(
    raw_data=Input(DatasetPaths.SOURCE_DATASET),
    cleaned_data=Output(DatasetPaths.CLEANED_DATA),
)
def clean_and_standardize(raw_data: TransformInput, cleaned_data: TransformOutput):
    df = raw_data.pandas()

    required_columns = ["source_id", "title", "description", "url", "source_api"]
    missing_columns = set(required_columns) - set(df.columns.tolist())
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")

    df["source_id_valid"] = ~df["source_id"].isnull()
    df["title_valid"] = ~(df["title"].isnull() | (df["title"].str.len() == 0))
    df["title_clean"] = df["title"].str.strip().str.title()
    df["pillar_clean"] = df["pillar"].str.strip().str.title()

    df = df[df["is_active"] == True]
    df = df[df["is_published"] == True]

    df["overall_quality_score"] = (
        df["credibility_score"] * 0.25 +
        df["technical_accuracy_score"] * 0.25 +
        df["practical_value_score"] * 0.20 +
        df["freshness_score"] * 0.15 +
        df["trend_relevance_score"] * 0.10 +
        df["educational_quality_score"] * 0.05
    )

    def categorize_trend(x):
        if x >= 90:
            return "high_trend"
        elif x >= 70:
            return "medium_trend"
        else:
            return "low_trend"

    df["trend_category"] = df["trend_strength"].apply(categorize_trend)
    df["cleaning_version"] = "v2.0"

    result = df[[
        "source_id", "title_clean", "description", "url", "source_api",
        "domain", "tags", "pillar_clean", "credibility_score",
        "technical_accuracy_score", "practical_value_score", "freshness_score",
        "trend_relevance_score", "educational_quality_score", "overall_quality_score",
        "trend_strength", "trend_category", "adoption_level", "impact_level",
        "inferred_at", "last_updated", "is_active", "is_published",
        "source_id_valid", "title_valid", "cleaning_version",
    ]].copy()

    cleaned_data.write_dataframe(result)


@transform(
    raw_data=Input(DatasetPaths.SOURCE_DATASET),
    metrics_output=Output(DatasetPaths.CLEANING_QUALITY_METRICS),
)
def cleaning_quality_metrics(raw_data: TransformInput, metrics_output: TransformOutput):
    df = raw_data.pandas()

    metrics = pd.DataFrame({
        "total_records": [len(df)],
        "null_source_ids": [df["source_id"].isnull().sum()],
        "null_titles": [df["title"].isnull().sum()],
        "avg_title_length": [df["title"].str.len().mean()],
        "unique_sources": [df["source_api"].nunique()],
        "unique_pillars": [df["pillar"].nunique()],
        "avg_credibility": [df["credibility_score"].mean()],
        "metric_version": ["v1.0"],
    })

    metrics_output.write_dataframe(metrics)
