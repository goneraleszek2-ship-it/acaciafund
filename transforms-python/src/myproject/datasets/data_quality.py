"""
AcaciaFund Data Quality Module
Comprehensive data quality checks and monitoring.
"""

import polars as pl
from datetime import datetime, timezone
from transforms.api import transform, Input, Output, LightweightInput, LightweightOutput
from transforms import expectations as E


def create_quality_expectations():
    """
    Create comprehensive data quality expectations.
    """
    return E.expectations(
        E.col("source_id").is_not_null(),
        E.col("source_id").is_unique(),
        E.primary_key("source_id"),
        E.col("title").is_not_null(),
        E.col("title").str_lengths().is_between(1, 500),
        E.col("description").str_lengths().is_between(0, 5000),
        E.col("url").is_not_null(),
        E.col("url").str.contains(r"^https?://"),
        E.col("source_api").is_not_null(),
        E.col("source_api").is_in(["arxiv", "pubmed", "curated", "github", "gitlab", "openverse", "wikimedia"]),
        E.col("pillar").is_in(["AML", "Markets", "Data Engineering"]),
        E.col("credibility_score").is_between(0.0, 1.0),
        E.col("overall_quality_score").is_between(0.0, 1.0),
        E.col("trend_strength").is_between(0, 100),
        E.col("is_active").is_not_null(),
        E.col("is_published").is_not_null(),
    )


@transform.using(
    output=Output("data_quality_report"),
    input_dataset=Input("acacia_portal_clean_data"),
)
def data_quality_report(
    input_dataset: LightweightInput,
    output: Output
) -> None:
    """
    Generate comprehensive data quality report.
    """
    df = input_dataset.polars(lazy=True)
    
    # Calculate quality metrics
    metrics = df.select([
        # Record counts
        pl.len().alias("total_records"),
        pl.col("source_id").is_null().sum().alias("null_source_ids"),
        pl.col("title").is_null().sum().alias("null_titles"),
        pl.col("description").is_null().sum().alias("null_descriptions"),
        
        # Unique counts
        pl.col("source_id").n_unique().alias("unique_source_ids"),
        pl.col("source_api").n_unique().alias("unique_sources"),
        pl.col("pillar").n_unique().alias("unique_pillars"),
        pl.col("tags").explode().n_unique().alias("unique_tags"),
        
        # Score metrics
        pl.col("credibility_score").mean().alias("avg_credibility"),
        pl.col("credibility_score").std().alias("std_credibility"),
        pl.col("overall_quality_score").mean().alias("avg_overall_quality"),
        pl.col("overall_quality_score").std().alias("std_overall_quality"),
        pl.col("trend_strength").mean().alias("avg_trend_strength"),
        pl.col("trend_strength").std().alias("std_trend_strength"),
        
        # Distribution metrics
        pl.col("overall_quality_score").quantile(0.25).alias("q1_quality"),
        pl.col("overall_quality_score").quantile(0.50).alias("median_quality"),
        pl.col("overall_quality_score").quantile(0.75).alias("q3_quality"),
    ])
    
    # Add timestamp and version
    metrics = metrics.with_columns([
        pl.lit(datetime.now(timezone.utc)).alias("report_timestamp"),
        pl.lit("v1.0").alias("report_version"),
    ])
    
    output.write_table(metrics)


@transform.using(
    output=Output("data_quality_alerts"),
    input_dataset=Input("acacia_portal_clean_data"),
)
def data_quality_alerts(
    input_dataset: LightweightInput,
    output: Output
) -> None:
    """
    Generate data quality alerts based on thresholds.
    """
    df = input_dataset.polars(lazy=True)
    
    # Calculate quality metrics
    metrics = df.select([
        pl.len().alias("total_records"),
        pl.col("source_id").is_null().sum().alias("null_source_ids"),
        pl.col("title").is_null().sum().alias("null_titles"),
        pl.col("credibility_score").mean().alias("avg_credibility"),
        pl.col("overall_quality_score").mean().alias("avg_overall_quality"),
        pl.col("trend_strength").mean().alias("avg_trend_strength"),
    ])
    
    # Collect metrics for threshold checking
    metrics_df = metrics.collect()
    total_records = metrics_df["total_records"][0]
    null_source_ids = metrics_df["null_source_ids"][0]
    null_titles = metrics_df["null_titles"][0]
    avg_credibility = metrics_df["avg_credibility"][0]
    avg_overall_quality = metrics_df["avg_overall_quality"][0]
    avg_trend_strength = metrics_df["avg_trend_strength"][0]
    
    # Generate alerts
    alerts = []
    
    # Null value alerts
    null_source_pct = (null_source_ids / total_records * 100) if total_records > 0 else 0
    if null_source_pct > 5:
        alerts.append({
            "alert_type": "HIGH_NULL_SOURCE_IDS",
            "severity": "WARNING",
            "message": f"High percentage of null source_ids: {null_source_pct:.2f}%",
            "current_value": null_source_pct,
            "threshold": 5.0,
        })
    
    null_title_pct = (null_titles / total_records * 100) if total_records > 0 else 0
    if null_title_pct > 5:
        alerts.append({
            "alert_type": "HIGH_NULL_TITLES",
            "severity": "WARNING",
            "message": f"High percentage of null titles: {null_title_pct:.2f}%",
            "current_value": null_title_pct,
            "threshold": 5.0,
        })
    
    # Quality score alerts
    if avg_credibility < 0.5:
        alerts.append({
            "alert_type": "LOW_CREDIBILITY_SCORE",
            "severity": "CRITICAL",
            "message": f"Average credibility score is below threshold: {avg_credibility:.2f}",
            "current_value": avg_credibility,
            "threshold": 0.5,
        })
    
    if avg_overall_quality < 0.6:
        alerts.append({
            "alert_type": "LOW_OVERALL_QUALITY",
            "severity": "CRITICAL",
            "message": f"Average overall quality score is below threshold: {avg_overall_quality:.2f}",
            "current_value": avg_overall_quality,
            "threshold": 0.6,
        })
    
    # Convert alerts to DataFrame
    if alerts:
        alerts_df = pl.DataFrame(alerts)
    else:
        alerts_df = pl.DataFrame({
            "alert_type": pl.Series([], dtype=pl.Utf8),
            "severity": pl.Series([], dtype=pl.Utf8),
            "message": pl.Series([], dtype=pl.Utf8),
            "current_value": pl.Series([], dtype=pl.Float64),
            "threshold": pl.Series([], dtype=pl.Float64),
        })
    
    # Add timestamp
    alerts_df = alerts_df.with_columns([
        pl.lit(datetime.now(timezone.utc)).alias("alert_timestamp"),
        pl.lit("v1.0").alias("alert_version"),
    ])
    
    output.write_table(alerts_df)
