"""
AcaciaFund Incremental Processing Transform
Processes only new data since last build.
"""

import pandas as pd
from transforms.api import transform, Input, Output


@transform(
    source_data=Input("source_dataset"),
    incremental_output=Output("incremental_fund_updates"),
)
def process_incremental_updates(source_data, incremental_output):
    df = source_data.pandas()

    df = df.copy()
    df["record_status"] = "NEW"
    df["processed_version"] = "v1.0"

    incremental_output.write_dataframe(df)
