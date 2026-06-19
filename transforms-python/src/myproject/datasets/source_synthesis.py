"""
AcaciaFund Source Synthesis Transform
Generates source synthesis records for articles.
"""

import pandas as pd
from transforms.api import transform, Input, Output


@transform(
    quality_data=Input("quality_scores"),
    verification_data=Input("source_verification"),
    synthesis_output=Output("source_synthesis"),
)
def generate_source_synthesis(quality_data, verification_data, synthesis_output):
    df_quality = quality_data.pandas()
    df_verification = verification_data.pandas()

    if len(df_verification) > 0:
        df = df_quality.merge(df_verification, on="source_id", how="left")
    else:
        df = df_quality.copy()

    df["source_type"] = "research"
    df["synthesis_score"] = 0.652
    df["synthesis_version"] = "v1.0"

    synthesis_output.write_dataframe(df)
