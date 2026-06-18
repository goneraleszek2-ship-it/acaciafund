"""
AcaciaFund Incremental Processing Transform
Processes only new data since last build.
"""

import polars as pl
from datetime import datetime, timezone
from transforms.api import transform, Input, Output, incremental


@incremental()
@transform(
    source_data=Input("/TierPalan-95733d/Acacia/SOURCE_DATASET_PATH"),
    incremental_output=Output("incremental_fund_updates")
)
def process_incremental_updates(source_data, incremental_output):
    """Process only new data since last build"""
    df = source_data.polars('added')
    
    df = df.with_columns([
        pl.lit("NEW").alias("record_status"),
        pl.lit(datetime.now(timezone.utc)).alias("processed_timestamp"),
        pl.lit(pl.datetime.now()).alias("ingestion_timestamp"),
    ])
    
    incremental_output.write_table(df)
