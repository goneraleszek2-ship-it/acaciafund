"""
AcaciaFund Export Transform
"""

import pandas as pd
from transforms.api import transform, Input, Output
from myproject.config import DatasetPaths


@transform(
    scoring_data=Input(DatasetPaths.QUALITY_SCORES),
    analysis_data=Input(DatasetPaths.TREND_ANALYSIS),
    export_output=Output(DatasetPaths.EXPORT_QUALITY_METRICS),
)
def export_quality_metrics(scoring_data, analysis_data, export_output):
    df_scoring = scoring_data.pandas()
    df_analysis = analysis_data.pandas()

    df = df_scoring.merge(df_analysis, on="source_id", how="left")
    df["source_type"] = "curated"
    df["export_version"] = "v1.0"

    export_output.write_dataframe(df)


@transform(
    scoring_data=Input(DatasetPaths.QUALITY_SCORES),
    analysis_data=Input(DatasetPaths.TREND_ANALYSIS),
    radar_output=Output(DatasetPaths.EXPORT_TECHNOLOGY_RADAR),
)
def export_technology_radar(scoring_data, analysis_data, radar_output):
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
    df["radar_version"] = "v1.0"

    radar_output.write_dataframe(df)


@transform(
    scoring_data=Input(DatasetPaths.QUALITY_SCORES),
    verification_data=Input(DatasetPaths.SOURCE_VERIFICATION),
    synthesis_output=Output(DatasetPaths.EXPORT_SOURCE_SYNTHESIS),
)
def export_source_synthesis(scoring_data, verification_data, synthesis_output):
    df_scoring = scoring_data.pandas()
    df_verification = verification_data.pandas()

    if len(df_verification) > 0:
        df = df_scoring.merge(df_verification, on="source_id", how="left")
    else:
        df = df_scoring.copy()

    df["source_type"] = "research"
    df["synthesis_score"] = 0.652
    df["synthesis_version"] = "v1.0"

    synthesis_output.write_dataframe(df)
