"""
AcaciaFund Enhanced Data Cleaning Transform
"""

import pandas as pd
from transforms.api import transform, Input, Output, TransformInput, TransformOutput
from myproject.config import DatasetPaths


@transform(
    raw_data=Input(DatasetPaths.SOURCE_DATASET),
    cleaned_data=Output(DatasetPaths.CLEANED_DATA_ENHANCED),
)
def clean_portal_data(raw_data: TransformInput, cleaned_data: TransformOutput):
    df = raw_data.pandas()
    df = df.drop_duplicates(subset=["source_id"], keep="last")
    df["title"] = df["title"].str.strip().str.title()
    df["pillar"] = df["pillar"].str.strip().str.title()

    df["overall_quality_score"] = (
        df["credibility_score"] * 0.25 +
        df["technical_accuracy_score"] * 0.25 +
        df["practical_value_score"] * 0.20 +
        df["freshness_score"] * 0.15 +
        df["trend_relevance_score"] * 0.10 +
        df["educational_quality_score"] * 0.05
    )

    df["trend_category"] = pd.cut(
        df["trend_strength"],
        bins=[0, 70, 90, 100],
        labels=["low_trend", "medium_trend", "high_trend"]
    )

    df = df[df["is_active"] == True]
    df = df[df["is_published"] == True]

    cleaned_data.write_dataframe(df)
