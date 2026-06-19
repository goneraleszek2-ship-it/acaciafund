"""
AcaciaFund Export Transform
Static site exports with JSON API support.
"""

import pandas as pd
from datetime import datetime, timezone
from transforms.api import transform, Input, Output, TransformInput, TransformOutput
from myproject.config import DatasetPaths


@transform(
    scoring_data=Input(DatasetPaths.QUALITY_SCORES),
    analysis_data=Input(DatasetPaths.TREND_ANALYSIS),
    export_output=Output(DatasetPaths.EXPORT_QUALITY_METRICS),
)
def export_quality_metrics(scoring_data: TransformInput, analysis_data: TransformInput, export_output: TransformOutput):
    df_scoring = scoring_data.pandas()
    df_analysis = analysis_data.pandas()

    df = df_scoring.merge(df_analysis, on="source_id", how="left")
    df["source_type"] = "curated"
    df["export_version"] = "v2.0"

    export_output.write_dataframe(df)


@transform(
    scoring_data=Input(DatasetPaths.QUALITY_SCORES),
    analysis_data=Input(DatasetPaths.TREND_ANALYSIS),
    radar_output=Output(DatasetPaths.EXPORT_TECHNOLOGY_RADAR),
)
def export_technology_radar(scoring_data: TransformInput, analysis_data: TransformInput, radar_output: TransformOutput):
    df_scoring = scoring_data.pandas()
    df_analysis = analysis_data.pandas()

    df = df_scoring.merge(df_analysis, on="source_id", how="left")

    def get_recommendation(row):
        if row["overall_quality_score"] >= 0.8 and row["trend_strength"] >= 50:
            return "adopt"
        elif row["overall_quality_score"] >= 0.6 and row["trend_strength"] >= 30:
            return "trial"
        elif row["overall_quality_score"] >= 0.5:
            return "assess"
        else:
            return "hold"

    df["recommendation"] = df.apply(get_recommendation, axis=1)
    df["radar_name"] = "AcaciaFund Technology Radar - Q2 2026"
    df["radar_version"] = "v2.0"

    radar_output.write_dataframe(df)


@transform(
    scoring_data=Input(DatasetPaths.QUALITY_SCORES),
    verification_data=Input(DatasetPaths.SOURCE_VERIFICATION),
    synthesis_output=Output(DatasetPaths.EXPORT_SOURCE_SYNTHESIS),
)
def export_source_synthesis(scoring_data: TransformInput, verification_data: TransformInput, synthesis_output: TransformOutput):
    df_scoring = scoring_data.pandas()
    df_verification = verification_data.pandas()

    if len(df_verification) > 0:
        df = df_scoring.merge(df_verification, on="source_id", how="left")
    else:
        df = df_scoring.copy()

    df["source_type"] = "research"
    df["synthesis_score"] = 0.652
    df["synthesis_version"] = "v2.0"

    synthesis_output.write_dataframe(df)


@transform(
    scoring_data=Input(DatasetPaths.QUALITY_SCORES),
    analysis_data=Input(DatasetPaths.TREND_ANALYSIS),
    anomalies_data=Input("data_anomalies"),
    json_export_output=Output("static_site_json"),
)
def export_static_site_json(scoring_data: TransformInput, analysis_data: TransformInput, anomalies_data: TransformInput, json_export_output: TransformOutput):
    df_scoring = scoring_data.pandas()
    df_analysis = analysis_data.pandas()

    df = df_scoring.merge(df_analysis, on="source_id", how="left")

    def get_recommendation(row):
        if row["overall_quality_score"] >= 0.8 and row["trend_strength"] >= 50:
            return "adopt"
        elif row["overall_quality_score"] >= 0.6 and row["trend_strength"] >= 30:
            return "trial"
        elif row["overall_quality_score"] >= 0.5:
            return "assess"
        else:
            return "hold"

    df["recommendation"] = df.apply(get_recommendation, axis=1)
    df["export_timestamp"] = datetime.now(timezone.utc).isoformat()
    df["export_version"] = "v2.0"

    anomalies_df = anomalies_data.pandas()
    anomalies_summary = {
        "total_anomalies": len(anomalies_df),
        "critical_anomalies": len(anomalies_df[anomalies_df["severity"] == "CRITICAL"]) if len(anomalies_df) > 0 else 0,
        "warning_anomalies": len(anomalies_df[anomalies_df["severity"] == "WARNING"]) if len(anomalies_df) > 0 else 0,
        "last_detection": anomalies_df["detected_at"].max() if len(anomalies_df) > 0 else None,
    }

    export_data = {
        "metadata": {
            "portal_name": "AcaciaFund Technology Radar",
            "portal_version": "v2.0",
            "export_timestamp": datetime.now(timezone.utc).isoformat(),
            "data_quality": {
                "total_records": len(df),
                "avg_overall_quality": float(df["overall_quality_score"].mean()) if len(df) > 0 else 0,
                "avg_trend_strength": float(df["trend_strength"].mean()) if len(df) > 0 else 0,
            },
            "anomalies": anomalies_summary,
        },
        "articles": df[[
            "source_id", "title", "description", "url", "source_api",
            "pillar", "credibility_score", "overall_quality_score",
            "trend_strength", "trend_category", "adoption_level",
            "impact_level", "recommendation", "export_timestamp",
        ]].to_dict(orient="records"),
    }

    export_df = pd.DataFrame([{
        "export_type": "static_site",
        "export_version": "v2.0",
        "export_timestamp": datetime.now(timezone.utc).isoformat(),
        "total_articles": len(df),
        "export_metadata": str(export_data["metadata"]),
    }])

    json_export_output.write_dataframe(export_df)
