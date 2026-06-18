"""
AcaciaFund Enhanced Data Cleaning Transform
Advanced data cleaning with validation and enrichment.
"""

import polars as pl
from transforms.api import transform, Input, Output
from transforms import expectations as E


@transform(
    raw_data=Input("/TierPalan-95733d/Acacia/SOURCE_DATASET_PATH"),
    cleaned_data=Output("/TierPalan-95733d/Acacia/acacia_portal_clean_data"),
    expectations=E.expectations(
        E.col("source_id").is_not_null(),
        E.col("title").is_not_null(),
        E.primary_key("source_id"),
        E.col("pillar").is_in(["AML", "Markets", "Data Engineering"])
    )
)
def clean_portal_data(raw_data, cleaned_data):
    """
    Comprehensive data cleaning for AcaciaFund portal
    """
    df = raw_data.polars(lazy=True)
    
    df = df.unique(subset=["source_id"], keep="last")
    
    df = df.with_columns([
        pl.col("title").str.strip_chars().str.to_uppercase().alias("title"),
        pl.col("pillar").str.strip_chars().str.to_titlecase().alias("pillar"),
    ])
    
    df = df.with_columns([
        ((pl.col("credibility_score") * 0.25) +
         (pl.col("technical_accuracy_score") * 0.25) +
         (pl.col("practical_value_score") * 0.20) +
         (pl.col("freshness_score") * 0.15) +
         (pl.col("trend_relevance_score") * 0.10) +
         (pl.col("educational_quality_score") * 0.05))
        .alias("overall_quality_score"),
        
        pl.when(pl.col("trend_strength") >= 90).then("high_trend")
        .when(pl.col("trend_strength") >= 70).then("medium_trend")
        .otherwise("low_trend").alias("trend_category"),
    ])
    
    df = df.filter((pl.col("is_active") == True) & (pl.col("is_published") == True))
    
    cleaned_data.write_table(df)
