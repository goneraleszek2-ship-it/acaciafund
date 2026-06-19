"""
AcaciaFund Lightweight Transform
Clean and standardize AcaciaFund portal data with comprehensive validation.
"""

import pandas as pd
from datetime import datetime, timezone
from transforms.api import transform, Input, Output, LightweightInput, LightweightOutput


@transform.using(
    input_dataset=Input("source_dataset"),
    output_dataset=Output("acacia_portal_clean_data"),
)
def clean_and_standardize(
    input_dataset: LightweightInput,
    output_dataset: Output
) -> None:
    """
    Clean and standardize AcaciaFund portal data.

    This transform:
    - Validates input data schema
    - Handles missing and invalid values
    - Standardizes data formats
    - Applies business rules
    - Generates quality metrics
    """
    try:
        df = input_dataset.pandas()

        required_columns = ["source_id", "title", "description", "url", "source_api"]
        current_columns = df.columns.tolist()

        missing_columns = set(required_columns) - set(current_columns)
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

        df["cleaned_timestamp"] = datetime.now(timezone.utc)
        df["cleaning_version"] = "v2.0"

        result = df[[
            "source_id",
            "title_clean",
            "description",
            "url",
            "source_api",
            "domain",
            "tags",
            "pillar_clean",
            "credibility_score",
            "technical_accuracy_score",
            "practical_value_score",
            "freshness_score",
            "trend_relevance_score",
            "educational_quality_score",
            "overall_quality_score",
            "trend_strength",
            "adoption_level",
            "impact_level",
            "inferred_at",
            "last_updated",
            "is_active",
            "is_published",
            "source_id_valid",
            "title_valid",
            "cleaned_timestamp",
            "cleaning_version",
        ]].copy()

        output_dataset.write_dataframe(result)

        print(f"Successfully processed {len(result)} records")

    except Exception as e:
        print(f"Error in lightweight-transform: {str(e)}")
        raise


@transform.using(
    output=Output("cleaning_quality_metrics"),
    input_dataset=Input("source_dataset"),
)
def cleaning_quality_metrics(
    input_dataset: LightweightInput,
    output: Output
) -> None:
    """
    Generate data quality metrics for the cleaning process.
    """
    df = input_dataset.pandas()

    metrics = pd.DataFrame({
        "total_records": [len(df)],
        "null_source_ids": [df["source_id"].isnull().sum()],
        "null_titles": [df["title"].isnull().sum()],
        "avg_title_length": [df["title"].str.len().mean()],
        "unique_sources": [df["source_api"].nunique()],
        "unique_pillars": [df["pillar"].nunique()],
        "avg_credibility": [df["credibility_score"].mean()],
        "avg_overall_quality": [df["overall_quality_score"].mean()],
    })

    metrics["metric_timestamp"] = datetime.now(timezone.utc)
    metrics["metric_version"] = "v1.0"

    output.write_dataframe(metrics)
