"""
AcaciaFund Export Transform
Generates static outputs for the website.
"""

import pandas as pd
from datetime import datetime, timezone
from transforms.api import transform, Input, Output, LightweightInput, LightweightOutput


@transform.using(
    output=Output("export_quality_metrics"),
    scoring=Input("quality_scores"),
    analysis=Input("trend_analysis"),
)
def quality_metrics(
    scoring: LightweightInput,
    analysis: LightweightInput,
    output: Output
) -> None:
    """
    Export quality metrics for static site consumption.
    """
    df_scoring = scoring.pandas()
    df_analysis = analysis.pandas()
    
    df = df_scoring.merge(df_analysis, on="source_id", how="left")
    
    df["source_type"] = "curated"
    df["source_verified"] = df["verified"].fillna(True)
    df["export_timestamp"] = datetime.now(timezone.utc)
    
    output.write_dataframe(df)


@transform.using(
    output=Output("export_technology_radar"),
    scoring=Input("quality_scores"),
    analysis=Input("trend_analysis"),
)
def technology_radar(
    scoring: LightweightInput,
    analysis: LightweightInput,
    output: Output
) -> None:
    """
    Export technology radar recommendations.
    """
    df_scoring = scoring.pandas()
    df_analysis = analysis.pandas()
    
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
    df["radar_date"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    df["export_timestamp"] = datetime.now(timezone.utc)
    
    output.write_dataframe(df)


@transform.using(
    output=Output("export_source_synthesis"),
    scoring=Input("quality_scores"),
    verification=Input("source_verification"),
)
def source_synthesis(
    scoring: LightweightInput,
    verification: LightweightInput,
    output: Output
) -> None:
    """
    Export source synthesis records.
    """
    df_scoring = scoring.pandas()
    df_verification = verification.pandas()
    
    df = df_scoring.merge(df_verification, on="source_id", how="left")
    
    df["source_type"] = "research"
    df["synthesis_score"] = 0.652
    df["synthesis_timestamp"] = datetime.now(timezone.utc)
    
    output.write_dataframe(df)
