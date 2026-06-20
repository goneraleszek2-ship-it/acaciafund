import os
import sys
import time
import pandas as pd
from pathlib import Path

# Add the parent directory to path so we can import 'scripts'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.foundry_integration import get_foundry_client

dataset_rid = os.getenv("DATASET_RID", "ri.foundry.main.dataset.d006865d-edc1-4c84-87cd-38c6f0259036")

def run_ingestion():
    try:
        ctx = get_foundry_client()
        test_path = Path("upload.parquet")
        
        while True:
            print("Starting heartbeat batch...")
            pd.DataFrame({"status": ["active"], "ts": [time.time()]}).to_parquet(test_path)
            
            # Start transaction
            tx_res = ctx.catalog.api_start_transaction(dataset_rid=dataset_rid, branch_id="master", start_transaction_type="APPEND")
            tx_rid = tx_res.json()["rid"]
            
            try:
                ctx.data_proxy.upload_dataset_file(
                    dataset_rid=dataset_rid, transaction_rid=tx_rid,
                    path=test_path, path_in_foundry_dataset="heartbeat.parquet"
                )
                ctx.catalog.api_commit_transaction(dataset_rid=dataset_rid, transaction_rid=tx_rid)
                print(f"Successfully committed: {tx_rid}")
            except Exception as e:
                print(f"Upload/Commit failed: {e}")
                ctx.catalog.api_abort_transaction(dataset_rid=dataset_rid, transaction_rid=tx_rid)
            
            time.sleep(60) 
    except Exception as e:
        print(f"Initialization failed: {e}")

if __name__ == "__main__":
    run_ingestion()
