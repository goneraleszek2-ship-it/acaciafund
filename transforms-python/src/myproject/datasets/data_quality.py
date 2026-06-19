"""
AcaciaFund Data Quality Module
Comprehensive data quality checks and monitoring.
"""

import pandas as pd
from transforms.api import transform, Input, Output


@transform(
    input_data=Input("acacia_portal_clean_data"),
    report_output=Output("data_quality_report"),
)
def generate_quality_report(input_data, report_output):
    df = input_data.pandas()

    metrics = pd.DataFrame({
        "total_records": [len(df)],
        "null_source_ids": [df["source_id"].isnull().sum()],
        "null_titles": [df["title"].isnull().sum() if "title" in df.columns else 0],
        "null_descriptions": [df["description"].isnull().sum() if "description" in df.columns else 0],
        "unique_source_ids": [df["source_id"].nunique()],
        "unique_sources": [df["source_api"].nunique() if "source_api" in df.columns else 0],
        "unique_pillars": [df["pillar"].nunique() if "pillar" in df.columns else 0],
        "avg_credibility": [df["credibility_score"].mean() if "credibility_score" in df.columns else 0],
        "std_credibility": [df["credibility_score"].std() if "credibility_score" in df.columns else 0],
        "avg_overall_quality": [df["overall_quality_score"].mean() if "overall_quality_score" in df.columns else 0],
        "std_overall_quality": [df["overall_quality_score"].std() if "overall_quality_score" in df.columns else 0],
        "avg_trend_strength": [df["trend_strength"].mean() if "trend_strength" in df.columns else 0],
        "report_version": ["v1.0"],
    })

    report_output.write_dataframe(metrics)


@transform(
    input_data=Input("acacia_portal_clean_data"),
    alerts_output=Output("data_quality_alerts"),
)
def generate_quality_alerts(input_data, alerts_output):
    df = input_data.pandas()

    total_records = len(df)
    alerts = []

    if total_records == 0:
        alerts_df = pd.DataFrame({
            "alert_type": pd.Series([], dtype=str),
            "severity": pd.Series([], dtype=str),
            "message": pd.Series([], dtype=str),
            "current_value": pd.Series([], dtype=float),
            "threshold": pd.Series([], dtype=float),
        })
        alerts_df["alert_version"] = "v1.0"
        alerts_output.write_dataframe(alerts_df)
        return

    null_source_ids = df["source_id"].isnull().sum()
    null_source_pct = (null_source_ids / total_records * 100)
    if null_source_pct > 5:
        alerts.append({
            "alert_type": "HIGH_NULL_SOURCE_IDS",
            "severity": "WARNING",
            "message": f"High percentage of null source_ids: {null_source_pct:.2f}%",
            "current_value": null_source_pct,
            "threshold": 5.0,
        })

    null_titles = df["title"].isnull().sum() if "title" in df.columns else 0
    null_title_pct = (null_titles / total_records * 100)
    if null_title_pct > 5:
        alerts.append({
            "alert_type": "HIGH_NULL_TITLES",
            "severity": "WARNING",
            "message": f"High percentage of null titles: {null_title_pct:.2f}%",
            "current_value": null_title_pct,
            "threshold": 5.0,
        })

    avg_credibility = df["credibility_score"].mean() if "credibility_score" in df.columns else 0
    if avg_credibility < 0.5:
        alerts.append({
            "alert_type": "LOW_CREDIBILITY_SCORE",
            "severity": "CRITICAL",
            "message": f"Average credibility score is below threshold: {avg_credibility:.2f}",
            "current_value": avg_credibility,
            "threshold": 0.5,
        })

    avg_overall_quality = df["overall_quality_score"].mean() if "overall_quality_score" in df.columns else 0
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

    alerts_df["alert_version"] = "v1.0"

    alerts_output.write_dataframe(alerts_df)
