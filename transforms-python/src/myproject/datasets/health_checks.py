"""
AcaciaFund Health Checks Module
Pipeline health monitoring and alerting.
"""

import pandas as pd
from datetime import datetime, timezone
from transforms.api import transform, Input, Output, LightweightInput, LightweightOutput


@transform.using(
    output=Output("pipeline_health"),
)
def pipeline_health(output: Output) -> None:
    """
    Generate pipeline health metrics.
    """
    health_metrics = pd.DataFrame({
        "metric_name": [
            "pipeline_status",
            "last_run_timestamp",
            "last_run_duration_seconds",
            "records_processed",
            "records_failed",
            "success_rate_percent",
            "data_quality_score",
            "alert_count",
        ],
        "metric_value": [
            "healthy",
            datetime.now(timezone.utc).isoformat(),
            0.0,
            0,
            0,
            100.0,
            0.0,
            0,
        ],
        "metric_type": [
            "status",
            "timestamp",
            "duration",
            "count",
            "count",
            "percentage",
            "score",
            "count",
        ],
        "threshold": [
            "healthy",
            None,
            300,
            None,
            0,
            95.0,
            0.7,
            0,
        ],
        "severity": [
            "info",
            "info",
            "info",
            "info",
            "warning",
            "info",
            "info",
            "warning",
        ],
    })
    
    output.write_dataframe(health_metrics)


@transform.using(
    output=Output("transform_health"),
    cleaned_data=Input("acacia_portal_clean_data"),
    scoring_data=Input("quality_scores"),
)
def transform_health(
    cleaned_data: LightweightInput,
    scoring_data: LightweightInput,
    output: Output
) -> None:
    """
    Generate health metrics for individual transforms.
    """
    df_cleaned = cleaned_data.pandas()
    df_scoring = scoring_data.pandas()
    
    cleaned_count = len(df_cleaned)
    scoring_count = len(df_scoring)
    
    current_time = datetime.now(timezone.utc)
    
    health_metrics = pd.DataFrame({
        "transform_name": [
            "cleaning",
            "scoring",
        ],
        "last_run_timestamp": [
            current_time.isoformat(),
            current_time.isoformat(),
        ],
        "record_count": [
            cleaned_count,
            scoring_count,
        ],
        "status": [
            "completed" if cleaned_count > 0 else "failed",
            "completed" if scoring_count > 0 else "failed",
        ],
        "data_freshness_minutes": [
            0.0,
            0.0,
        ],
        "health_score": [
            0.9 if cleaned_count > 0 else 0.0,
            0.9 if scoring_count > 0 else 0.0,
        ],
    })
    
    output.write_dataframe(health_metrics)
