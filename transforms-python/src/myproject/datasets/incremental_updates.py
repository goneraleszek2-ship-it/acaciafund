"""
AcaciaFund Incremental Processing Transform
Processes only new data since last build.
"""

import polars as pl
from datetime import datetime, timezone
from transforms.api import transform, Input, Output, incremental
from myproject.config import DatasetPaths


@incremental()
@transform(
    source_data=Input(DatasetPaths.SOURCE_DATASET),
    incremental_output=Output(DatasetPaths.INCREMENTAL_UPDATES)
)
def process_incremental_updates(source_data, incremental_output):
    """Process only new data since last build"""
    try:
        df = source_data.polars('added')
        
        df = df.with_columns([
            pl.lit("NEW").alias("record_status"),
            pl.lit(datetime.now(timezone.utc)).alias("processed_timestamp"),
            pl.lit(pl.datetime.now()).alias("ingestion_timestamp"),
        ])
        
        incremental_output.write_table(df)
        
        print(f"Incremental updates completed: {df.select(pl.len()).collect()} records")
        
    except Exception as e:
        print(f"Error in incremental_updates: {str(e)}")
        raise
