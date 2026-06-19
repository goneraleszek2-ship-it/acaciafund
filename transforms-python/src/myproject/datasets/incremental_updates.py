"""
AcaciaFund Incremental Processing Transform
Processes only new data since last build.
"""

import pandas as pd
from datetime import datetime, timezone
from transforms.api import transform, Input, Output, incremental


@incremental()
@transform(
    source_data=Input("source_dataset"),
    incremental_output=Output("incremental_fund_updates")
)
def process_incremental_updates(source_data, incremental_output):
    """Process only new data since last build"""
    df = source_data.pandas()
    
    df = df.copy()
    df["record_status"] = "NEW"
    df["processed_timestamp"] = datetime.now(timezone.utc)
    df["ingestion_timestamp"] = datetime.now(timezone.utc)
    
    incremental_output.write_dataframe(df)
