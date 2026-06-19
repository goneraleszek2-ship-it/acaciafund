"""
AcaciaFund Data Quality Module
Comprehensive data quality checks and monitoring.
"""

import pandas as pd
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
        E.col("title").str.lengths().is_between(1, 500),
        E.col("description").str.lengths().is_between(0, 5000),
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
    df = input_dataset.pandas()
    
    metrics = pd.DataFrame({
        "total_records": [len(df)],
        "null_source_ids": [df["source_id"].isnull().sum()],
        "null_titles": [df["title"].isnull().sum()],
        "null_descriptions": [df["description"].isnull().sum()],
        "unique_source_ids": [df["source_id"].nunique()],
        "unique_sources": [df["source_api"].nunique()],
        "unique_pillars": [df["pillar"].nunique()],
        "unique_tags": [df["tags"].explode().nunique() if df["tags"].explode().notnull().any() else 0],
        "avg_credibility": [df["credibility_score"].mean()],
        "std_credibility": [df["credibility_score"].std()],
        "avg_overall_quality": [df["overall_quality_score"].mean()],
        "std_overall_quality": [df["overall_quality_score"].std()],
        "avg_trend_strength": [df["trend_strength"].mean()],
        "std_trend_strength": [df["trend_strength"].std()],
        "q1_quality": [df["overall_quality_score"].quantile(0.25)],
        "median_quality": [df["overall_quality_score"].quantile(0.50)],
        "q3_quality": [df["overall_quality_score"].quantile(0.75)],
    })
    
    metrics["report_timestamp"] = datetime.now(timezone.utc)
    metrics["report_version"] = "v1.0"
    
    output.write_dataframe(metrics)


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
    df = input_dataset.pandas()
    
    total_records = len(df)
    null_source_ids = df["source_id"].isnull().sum()
    null_titles = df["title"].isnull().sum()
    avg_credibility = df["credibility_score"].mean()
    avg_overall_quality = df["overall_quality_score"].mean()
    avg_trend_strength = df["trend_strength"].mean()
    
    alerts = []
    
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
    
    if alerts:
        alerts_df = pd.DataFrame(alerts)
    else:
        alerts_df = pd.DataFrame({
            "alert_type": pd.Series([], dtype=str),
            "severity": pd.Series([], dtype=str),
            "message": pd.Series([], dtype=str),
            "current_value": pd.Series([], dtype=float),
            "threshold": pd.Series([], dtype=float),
        })
    
    alerts_df["alert_timestamp"] = datetime.now(timezone.utc)
    alerts_df["alert_version"] = "v1.0"
    
    output.write_dataframe(alerts_df)
