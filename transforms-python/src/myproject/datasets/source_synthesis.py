"""
AcaciaFund Source Synthesis Transform
"""

import pandas as pd
from transforms.api import transform, Input, Output, TransformInput, TransformOutput
from myproject.config import DatasetPaths


@transform(
    quality_data=Input(DatasetPaths.QUALITY_SCORES),
    verification_data=Input(DatasetPaths.SOURCE_VERIFICATION),
    synthesis_output=Output(DatasetPaths.SOURCE_SYNTHESIS),
)
def generate_source_synthesis(quality_data: TransformInput, verification_data: TransformInput, synthesis_output: TransformOutput):
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
