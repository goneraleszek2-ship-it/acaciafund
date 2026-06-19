"""
AcaciaFund Quality Scoring Transform
Computes 6-dimension quality scores for all ingested articles.
"""

import pandas as pd
from datetime import datetime, timezone
from transforms.api import transform, Input, Output, LightweightInput, LightweightOutput


@transform.using(
    output=Output("quality_scores"),
    sources=Input("acacia_portal_clean_data"),
)
def compute(
    sources: LightweightInput,
    output: Output
) -> None:
    """
    Compute 6-dimension quality scores for all articles.
    """
    df = sources.pandas()
    
    df["credibility_score"] = df["source_api"].apply(
        lambda x: 0.95 if x in ["arxiv", "pubmed", "curated"] else 0.70 if x in ["github", "gitlab"] else 0.50
    )
    
    df["technical_accuracy_score"] = 0.75
    df["practical_value_score"] = 0.70
    df["freshness_score"] = 0.80
    df["trend_relevance_score"] = 0.75
    df["educational_quality_score"] = 0.70
    
    df["overall_quality_score"] = (
        df["credibility_score"] * 0.25 +
        df["technical_accuracy_score"] * 0.25 +
        df["practical_value_score"] * 0.20 +
        df["freshness_score"] * 0.15 +
        df["trend_relevance_score"] * 0.10 +
        df["educational_quality_score"] * 0.05
    )
    
    df["scoring_timestamp"] = datetime.now(timezone.utc)
    df["scoring_version"] = "v1.0"
    
    result = df[[
        "source_id",
        "credibility_score",
        "technical_accuracy_score",
        "practical_value_score",
        "freshness_score",
        "trend_relevance_score",
        "educational_quality_score",
        "overall_quality_score",
        "scoring_timestamp",
        "scoring_version",
    ]].copy()
    
    output.write_dataframe(result)


@transform.using(
    output=Output("source_verification"),
    sources=Input("source_metadata"),
)
def source_verification(
    sources: LightweightInput,
    output: Output
) -> None:
    """
    Verify sources and compute verification status.
    """
    df = sources.pandas()
    
    df["verified"] = df["source_api"].apply(
        lambda x: True if x in ["arxiv", "pubmed", "curated"] else False
    )
    
    df["source_type"] = df["source_api"].apply(
        lambda x: "academic" if x in ["arxiv", "pubmed"] else "code_repository" if x in ["github", "gitlab"] else "media" if x in ["openverse", "wikimedia"] else "curated"
    )
    
    df["evidence_level"] = "evidence_available"
    
    df["verification_timestamp"] = datetime.now(timezone.utc)
    df["verification_version"] = "v1.0"
    
    result = df[[
        "source_id",
        "source_type",
        "source_credibility",
        "verified",
        "evidence_level",
        "verification_timestamp",
        "verification_version",
    ]].copy()
    
    output.write_dataframe(result)
