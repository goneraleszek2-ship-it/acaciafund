"""
AcaciaFund Source Synthesis Transform
Generates source synthesis records for articles.
"""

import pandas as pd
from datetime import datetime, timezone
from transforms.api import transform, Input, Output, LightweightInput, LightweightOutput


@transform.using(
    output=Output("source_synthesis"),
    quality=Input("quality_scores"),
    verification=Input("source_verification"),
)
def source_synthesis(
    quality: LightweightInput,
    verification: LightweightInput,
    output: Output
) -> None:
    """
    Generate source synthesis records for all articles.
    """
    df_quality = quality.pandas()
    df_verification = verification.pandas()
    
    df = df_quality.merge(df_verification, on="source_id", how="left")
    
    df["source_type"] = "research"
    df["synthesis_score"] = 0.652
    df["synthesis_timestamp"] = datetime.now(timezone.utc)
    
    output.write_dataframe(df)
