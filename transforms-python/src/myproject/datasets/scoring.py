"""
AcaciaFund Quality Scoring Transform
"""

import pandas as pd
from transforms.api import transform, Input, Output, TransformInput, TransformOutput
from myproject.config import DatasetPaths


@transform(
    clean_data=Input(DatasetPaths.CLEANED_DATA),
    scores_output=Output(DatasetPaths.QUALITY_SCORES),
)
def compute_scores(clean_data: TransformInput, scores_output: TransformOutput):
    df = clean_data.pandas()

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

    df["scoring_version"] = "v1.0"

    result = df[[
        "source_id", "credibility_score", "technical_accuracy_score",
        "practical_value_score", "freshness_score", "trend_relevance_score",
        "educational_quality_score", "overall_quality_score", "scoring_version",
    ]].copy()

    scores_output.write_dataframe(result)


@transform(
    source_meta=Input(DatasetPaths.SOURCE_METADATA),
    verification_output=Output(DatasetPaths.SOURCE_VERIFICATION),
)
def verify_sources(source_meta: TransformInput, verification_output: TransformOutput):
    df = source_meta.pandas()

    if len(df) == 0:
        df["verified"] = pd.Series([], dtype=bool)
        df["source_type"] = pd.Series([], dtype=str)
        df["evidence_level"] = pd.Series([], dtype=str)
        df["verification_version"] = pd.Series([], dtype=str)
        verification_output.write_dataframe(df)
        return

    df["verified"] = df["source_api"].apply(
        lambda x: True if x in ["arxiv", "pubmed", "curated"] else False
    )
    df["source_type"] = df["source_api"].apply(
        lambda x: "academic" if x in ["arxiv", "pubmed"] else "code_repository" if x in ["github", "gitlab"] else "curated"
    )
    df["evidence_level"] = "evidence_available"
    df["verification_version"] = "v1.0"

    result = df[[
        "source_id", "source_type", "source_credibility",
        "verified", "evidence_level", "verification_version",
    ]].copy()

    verification_output.write_dataframe(result)
