"""
AcaciaFund Fund Analytics Transform
"""

import pandas as pd
from transforms.api import transform, Input, Output
from myproject.config import DatasetPaths


@transform(
    cleaned_data=Input(DatasetPaths.CLEANED_DATA),
    analytics_output=Output(DatasetPaths.FUND_ANALYTICS),
)
def analyze_funds(cleaned_data, analytics_output):
    df = cleaned_data.pandas()
    pillar_col = "pillar_clean" if "pillar_clean" in df.columns else "pillar"

    pillar_analysis = df.groupby(pillar_col).agg({
        "source_id": "count",
        "overall_quality_score": "mean",
        "trend_strength": "mean",
        "credibility_score": "mean",
    }).reset_index()

    pillar_analysis.columns = ["pillar", "article_count", "avg_quality", "avg_trend", "avg_credibility"]
    pillar_analysis["market_share_pct"] = pillar_analysis["article_count"] / pillar_analysis["article_count"].sum() * 100

    trend_cat_col = "trend_category" if "trend_category" in df.columns else "pillar"
    trend_analysis = df.groupby(trend_cat_col).agg({
        "source_id": "count",
        "overall_quality_score": "mean",
        "trend_strength": "mean",
    }).reset_index()
    trend_analysis.columns = ["trend_category", "article_count", "avg_quality", "avg_trend"]

    top_articles = df.nlargest(10, "overall_quality_score")[["source_id", "overall_quality_score", "trend_strength"]]

    result = pd.DataFrame({
        "analysis_type": ["pillar", "trend", "top_articles"],
        "article_count": [pillar_analysis["article_count"].sum(), trend_analysis["article_count"].sum(), len(top_articles)],
        "avg_quality": [pillar_analysis["avg_quality"].mean(), trend_analysis["avg_quality"].mean(), top_articles["overall_quality_score"].mean()],
        "analytics_version": ["v1.0", "v1.0", "v1.0"],
    })

    analytics_output.write_dataframe(result)
