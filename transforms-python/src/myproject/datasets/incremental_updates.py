"""
AcaciaFund Incremental Processing Transform
"""

import pandas as pd
from transforms.api import transform, Input, Output, TransformInput, TransformOutput
from myproject.config import DatasetPaths


@transform(
    source_data=Input(DatasetPaths.SOURCE_DATASET),
    incremental_output=Output(DatasetPaths.INCREMENTAL_UPDATES),
)
def process_incremental_updates(source_data: TransformInput, incremental_output: TransformOutput):
    df = source_data.pandas()
    df = df.copy()
    df["record_status"] = "NEW"
    df["processed_version"] = "v1.0"
    incremental_output.write_dataframe(df)
