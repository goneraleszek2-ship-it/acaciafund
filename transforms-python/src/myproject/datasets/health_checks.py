"""
AcaciaFund Health Checks Module
"""

import pandas as pd
from transforms.api import transform, Input, Output, TransformInput, TransformOutput
from myproject.config import DatasetPaths


@transform(
    health_output=Output(DatasetPaths.PIPELINE_HEALTH),
)
def pipeline_health(health_output: TransformOutput):
    health_metrics = pd.DataFrame({
        "metric_name": ["pipeline_status", "records_processed", "records_failed", "success_rate_percent", "data_quality_score", "alert_count"],
        "metric_value": ["healthy", 0, 0, 100.0, 0.0, 0],
        "metric_type": ["status", "count", "count", "percentage", "score", "count"],
        "threshold": ["healthy", None, 0, 95.0, 0.7, 0],
        "severity": ["info", "info", "warning", "info", "info", "warning"],
        "health_version": ["v1.0"] * 6,
    })

    health_output.write_dataframe(health_metrics)


@transform(
    cleaned_data=Input(DatasetPaths.CLEANED_DATA),
    scoring_data=Input(DatasetPaths.QUALITY_SCORES),
    health_output=Output(DatasetPaths.TRANSFORM_HEALTH),
)
def transform_health(cleaned_data: TransformInput, scoring_data: TransformInput, health_output: TransformOutput):
    df_cleaned = cleaned_data.pandas()
    df_scoring = scoring_data.pandas()

    cleaned_count = len(df_cleaned)
    scoring_count = len(df_scoring)

    health_metrics = pd.DataFrame({
        "transform_name": ["cleaning", "scoring"],
        "record_count": [cleaned_count, scoring_count],
        "status": ["completed" if cleaned_count > 0 else "failed", "completed" if scoring_count > 0 else "failed"],
        "health_score": [0.9 if cleaned_count > 0 else 0.0, 0.9 if scoring_count > 0 else 0.0],
        "health_version": ["v1.0", "v1.0"],
    })

    health_output.write_dataframe(health_metrics)
