"""
AcaciaFund Fund Analytics Transform
Multi-dimensional analysis of articles and sources.
"""

import polars as pl
from transforms.api import transform, Input, Output


@transform(
    cleaned_data=Input("/TierPalan-95733d/Acacia/acacia_portal_clean_data"),
    analytics=Output("/TierPalan-95733d/Acacia/fund_analytics")
)
def analyze_funds(cleaned_data, analytics):
    """Multi-dimensional fund analysis"""
    df = cleaned_data.polars(lazy=True)
    
    pillar_analysis = df.group_by("pillar").agg([
        pl.col("source_id").count().alias("article_count"),
        pl.col("overall_quality_score").mean().alias("avg_quality"),
        pl.col("overall_quality_score").std().alias("std_quality"),
        pl.col("trend_strength").mean().alias("avg_trend"),
        pl.col("credibility_score").mean().alias("avg_credibility"),
    ]).with_columns([
        (pl.col("article_count") / pl.col("article_count").sum() * 100).alias("market_share_pct")
    ])
    
    trend_analysis = df.group_by("trend_category").agg([
        pl.col("source_id").count().alias("article_count"),
        pl.col("overall_quality_score").mean().alias("avg_quality"),
        pl.col("trend_strength").mean().alias("avg_trend"),
    ])
    
    top_articles = df.sort("overall_quality_score", descending=True).head(10).select([
        "source_id", "title", "pillar", "overall_quality_score", "trend_strength"
    ])
    
    result = pl.DataFrame({
        "analysis_type": ["pillar", "trend", "top_articles"],
        "article_count": [pillar_analysis["article_count"].sum(), 
                          trend_analysis["article_count"].sum(),
                          len(top_articles)],
        "avg_quality": [pillar_analysis["avg_quality"].mean(),
                        trend_analysis["avg_quality"].mean(),
                        top_articles["overall_quality_score"].mean()],
    })
    
    analytics.write_table(result)
