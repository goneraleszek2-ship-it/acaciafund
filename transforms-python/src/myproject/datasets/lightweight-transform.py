"""
AcaciaFund Lightweight Transform
Clean and standardize AcaciaFund portal data with comprehensive validation.
"""

import polars as pl
from datetime import datetime, timezone
from transforms.api import transform, Input, Output, LightweightInput, LightweightOutput


@transform.using(
    input_dataset=Input("SOURCE_DATASET_PATH"),
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
        # Read input data
        df = input_dataset.polars(lazy=True)

        # Validate required columns exist
        required_columns = ["source_id", "title", "description", "url", "source_api"]
        current_columns = df.columns

        missing_columns = set(required_columns) - set(current_columns)
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")

        # Data Quality Checks with Expectations
        # Note: These expectations will be validated during pipeline execution
        df = df.with_columns([
            # Ensure source_id is not null
            pl.when(pl.col("source_id").is_null())
            .then(pl.lit(False))
            .otherwise(pl.lit(True))
            .alias("source_id_valid"),

            # Ensure title is not null or empty
            pl.when(pl.col("title").is_null() | (pl.col("title").str.lengths() == 0))
            .then(pl.lit(False))
            .otherwise(pl.lit(True))
            .alias("title_valid"),

            # Standardize title case
            pl.col("title").str.strip_chars().str.to_titlecase().alias("title_clean"),

            # Standardize pillar values
            pl.col("pillar").str.strip_chars().str.to_titlecase().alias("pillar_clean"),
        ])

        # Apply business rules
        df = df.filter(
            (pl.col("is_active") == True) &
            (pl.col("is_published") == True)
        )

        # Calculate overall quality score
        df = df.with_columns([
            ((pl.col("credibility_score") * 0.25) +
             (pl.col("technical_accuracy_score") * 0.25) +
             (pl.col("practical_value_score") * 0.20) +
             (pl.col("freshness_score") * 0.15) +
             (pl.col("trend_relevance_score") * 0.10) +
             (pl.col("educational_quality_score") * 0.05))
            .alias("overall_quality_score"),

            # Categorize trend strength
            pl.when(pl.col("trend_strength") >= 90).then("high_trend")
            .when(pl.col("trend_strength") >= 70).then("medium_trend")
            .otherwise("low_trend").alias("trend_category"),
        ])

        # Add processing metadata
        df = df.with_columns([
            pl.lit(datetime.now(timezone.utc)).alias("cleaned_timestamp"),
            pl.lit("v2.0").alias("cleaning_version"),
        ])

        # Select final columns
        df = df.select([
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
        ])

        # Write output
        output_dataset.write_table(df)

        # Log success
        print(f"Successfully processed {df.select(pl.len()).collect()} records")

    except Exception as e:
        print(f"Error in lightweight-transform: {str(e)}")
        raise


# Additional transform for data quality monitoring
@transform.using(
    output=Output("cleaning_quality_metrics"),
    input_dataset=Input("SOURCE_DATASET_PATH"),
)
def cleaning_quality_metrics(
    input_dataset: LightweightInput,
    output: Output
) -> None:
    """
    Generate data quality metrics for the cleaning process.
    """
    df = input_dataset.polars(lazy=True)

    # Calculate quality metrics
    metrics = df.select([
        pl.len().alias("total_records"),
        pl.col("source_id").is_null().sum().alias("null_source_ids"),
        pl.col("title").is_null().sum().alias("null_titles"),
        pl.col("title").str.lengths().mean().alias("avg_title_length"),
        pl.col("source_api").n_unique().alias("unique_sources"),
        pl.col("pillar").n_unique().alias("unique_pillars"),
        pl.col("credibility_score").mean().alias("avg_credibility"),
        pl.col("overall_quality_score").mean().alias("avg_overall_quality"),
    ])

    # Add timestamp and version
    metrics = metrics.with_columns([
        pl.lit(datetime.now(timezone.utc)).alias("metric_timestamp"),
        pl.lit("v1.0").alias("metric_version"),
    ])

    output.write_table(metrics)
