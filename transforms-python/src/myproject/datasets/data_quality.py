"""
AcaciaFund Data Quality Module
Comprehensive validation, anomaly detection, and data drift monitoring.
"""

import pandas as pd
from datetime import datetime, timezone
from transforms.api import transform, Input, Output, TransformInput, TransformOutput
from myproject.config import DatasetPaths, QualityThresholds


@transform(
    input_data=Input(DatasetPaths.CLEANED_DATA),
    report_output=Output(DatasetPaths.DATA_QUALITY_REPORT),
)
def generate_quality_report(input_data: TransformInput, report_output: TransformOutput):
    df = input_data.pandas()

    metrics = pd.DataFrame({
        "total_records": [len(df)],
        "null_source_ids": [df["source_id"].isnull().sum()],
        "null_titles": [df["title"].isnull().sum() if "title" in df.columns else 0],
        "null_descriptions": [df["description"].isnull().sum() if "description" in df.columns else 0],
        "null_urls": [df["url"].isnull().sum() if "url" in df.columns else 0],
        "unique_source_ids": [df["source_id"].nunique()],
        "unique_sources": [df["source_api"].nunique() if "source_api" in df.columns else 0],
        "unique_pillars": [df["pillar"].nunique() if "pillar" in df.columns else 0],
        "avg_credibility": [df["credibility_score"].mean() if "credibility_score" in df.columns else 0],
        "std_credibility": [df["credibility_score"].std() if "credibility_score" in df.columns else 0],
        "min_credibility": [df["credibility_score"].min() if "credibility_score" in df.columns else 0],
        "max_credibility": [df["credibility_score"].max() if "credibility_score" in df.columns else 0],
        "avg_overall_quality": [df["overall_quality_score"].mean() if "overall_quality_score" in df.columns else 0],
        "std_overall_quality": [df["overall_quality_score"].std() if "overall_quality_score" in df.columns else 0],
        "avg_trend_strength": [df["trend_strength"].mean() if "trend_strength" in df.columns else 0],
        "std_trend_strength": [df["trend_strength"].std() if "trend_strength" in df.columns else 0],
        "report_timestamp": [datetime.now(timezone.utc).isoformat()],
        "report_version": ["v2.0"],
    })

    report_output.write_dataframe(metrics)


@transform(
    input_data=Input(DatasetPaths.CLEANED_DATA),
    alerts_output=Output(DatasetPaths.DATA_QUALITY_ALERTS),
)
def generate_quality_alerts(input_data: TransformInput, alerts_output: TransformOutput):
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
        alerts_df["alert_version"] = "v2.0"
        alerts_output.write_dataframe(alerts_df)
        return

    null_source_ids = df["source_id"].isnull().sum()
    null_source_pct = (null_source_ids / total_records * 100)
    if null_source_pct > 5:
        alerts.append({
            "alert_type": "HIGH_NULL_SOURCE_IDS",
            "severity": "WARNING",
            "message": f"High null source_ids: {null_source_pct:.2f}%",
            "current_value": null_source_pct,
            "threshold": 5.0
        })

    null_title_pct = (df["title"].isnull().sum() / total_records * 100) if "title" in df.columns else 0
    if null_title_pct > 5:
        alerts.append({
            "alert_type": "HIGH_NULL_TITLES",
            "severity": "WARNING",
            "message": f"High null titles: {null_title_pct:.2f}%",
            "current_value": null_title_pct,
            "threshold": 5.0
        })

    avg_credibility = df["credibility_score"].mean() if "credibility_score" in df.columns else 0
    if avg_credibility < QualityThresholds.MIN_CREDIBILITY_SCORE:
        alerts.append({
            "alert_type": "LOW_CREDIBILITY_SCORE",
            "severity": "CRITICAL",
            "message": f"Low credibility: {avg_credibility:.2f}",
            "current_value": avg_credibility,
            "threshold": QualityThresholds.MIN_CREDIBILITY_SCORE
        })

    avg_quality = df["overall_quality_score"].mean() if "overall_quality_score" in df.columns else 0
    if avg_quality < QualityThresholds.MIN_OVERALL_QUALITY_SCORE:
        alerts.append({
            "alert_type": "LOW_OVERALL_QUALITY",
            "severity": "CRITICAL",
            "message": f"Low quality: {avg_quality:.2f}",
            "current_value": avg_quality,
            "threshold": QualityThresholds.MIN_OVERALL_QUALITY_SCORE
        })

    avg_trend = df["trend_strength"].mean() if "trend_strength" in df.columns else 0
    if avg_trend < QualityThresholds.MIN_TREND_STRENGTH:
        alerts.append({
            "alert_type": "LOW_TREND_STRENGTH",
            "severity": "WARNING",
            "message": f"Low trend strength: {avg_trend:.1f}",
            "current_value": avg_trend,
            "threshold": QualityThresholds.MIN_TREND_STRENGTH
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

    alerts_df["alert_timestamp"] = datetime.now(timezone.utc).isoformat()
    alerts_df["alert_version"] = "v2.0"
    alerts_output.write_dataframe(alerts_df)


@transform(
    input_data=Input(DatasetPaths.CLEANED_DATA),
    anomalies_output=Output("data_anomalies"),
)
def detect_anomalies(input_data: TransformInput, anomalies_output: TransformOutput):
    df = input_data.pandas()
    total_records = len(df)
    anomalies = []

    if total_records == 0:
        anomalies_df = pd.DataFrame({
            "anomaly_type": pd.Series([], dtype=str),
            "severity": pd.Series([], dtype=str),
            "message": pd.Series([], dtype=str),
            "affected_records": pd.Series([], dtype=int),
            "detected_at": pd.Series([], dtype=str),
        })
        anomalies_output.write_dataframe(anomalies_df)
        return

    if "credibility_score" in df.columns:
        credibility_mean = df["credibility_score"].mean()
        credibility_std = df["credibility_score"].std()
        if credibility_std > 0:
            z_scores = (df["credibility_score"] - credibility_mean) / credibility_std
            high_z = (z_scores > 3).sum()
            low_z = (z_scores < -3).sum()
            if high_z > 0:
                anomalies.append({
                    "anomaly_type": "HIGH_CREDIBILITY_OUTLIER",
                    "severity": "WARNING",
                    "message": f"{high_z} records with unusually high credibility scores",
                    "affected_records": int(high_z),
                    "detected_at": datetime.now(timezone.utc).isoformat()
                })
            if low_z > 0:
                anomalies.append({
                    "anomaly_type": "LOW_CREDIBILITY_OUTLIER",
                    "severity": "WARNING",
                    "message": f"{low_z} records with unusually low credibility scores",
                    "affected_records": int(low_z),
                    "detected_at": datetime.now(timezone.utc).isoformat()
                })

    if "overall_quality_score" in df.columns:
        quality_mean = df["overall_quality_score"].mean()
        quality_std = df["overall_quality_score"].std()
        if quality_std > 0:
            z_scores = (df["overall_quality_score"] - quality_mean) / quality_std
            low_quality = (z_scores < -2).sum()
            if low_quality > total_records * 0.1:
                anomalies.append({
                    "anomaly_type": "LOW_QUALITY_CLUSTER",
                    "severity": "CRITICAL",
                    "message": f"{low_quality} records with significantly low quality scores",
                    "affected_records": int(low_quality),
                    "detected_at": datetime.now(timezone.utc).isoformat()
                })

    if "trend_strength" in df.columns:
        trend_mean = df["trend_strength"].mean()
        trend_std = df["trend_strength"].std()
        if trend_std > 0:
            z_scores = (df["trend_strength"] - trend_mean) / trend_std
            high_trend = (z_scores > 3).sum()
            if high_trend > 0:
                anomalies.append({
                    "anomaly_type": "HIGH_TREND_OUTLIER",
                    "severity": "INFO",
                    "message": f"{high_trend} records with unusually high trend strength",
                    "affected_records": int(high_trend),
                    "detected_at": datetime.now(timezone.utc).isoformat()
                })

    if anomalies:
        anomalies_df = pd.DataFrame(anomalies)
    else:
        anomalies_df = pd.DataFrame({
            "anomaly_type": pd.Series([], dtype=str),
            "severity": pd.Series([], dtype=str),
            "message": pd.Series([], dtype=str),
            "affected_records": pd.Series([], dtype=int),
            "detected_at": pd.Series([], dtype=str),
        })

    anomalies_output.write_dataframe(anomalies_df)
