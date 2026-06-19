#!/usr/bin/env python3
"""
Export metrics from Foundry dataset to local JSON.
If Foundry dataset not available, fall back to local Parquet files.
Usage:
    python scripts/export_metrics.py
"""
import json
import os
from pathlib import Path

try:
    from foundry_dev_tools import FoundryContext, JWTTokenProvider, Config
    FOUNDRY_AVAILABLE = True
except Exception:
    FOUNDRY_AVAILABLE = False

def get_foundry_client():
    host = os.environ.get("FOUNDRY_HOST", "tierpalan.euw-3.palantirfoundry.co.uk")
    token = os.environ.get("FOUNDRY_TOKEN")
    if not token:
        raise ValueError("FOUNDRY_TOKEN environment variable not set")
    token_provider = JWTTokenProvider(host=host, jwt=token)
    config = Config(requests_ca_bundle=None, debug=False)
    return FoundryContext(config=config, token_provider=token_provider)

def main():
    # Try to get from Foundry
    if FOUNDRY_AVAILABLE:
        try:
            ctx = get_foundry_client()
            base_path = "/TierPalan-96733d/Acacia"
            candidates = ["default", "metrics", "quality_scores", "foundry_metrics"]
            dataset_rid = None
            used_path = None
            for ds in candidates:
                ds_path = f"{base_path}/{ds}"
                try:
                    info = ctx.catalog.api_get_dataset(ds_path)
                    dataset_rid = info['rid']
                    used_path = ds_path
                    print(f"Found dataset at {used_path}")
                    break
                except Exception:
                    continue
            if dataset_rid is not None:
                query = "SELECT * FROM this LIMIT 1000"
                result = ctx.catalog.api_request(
                    method="POST",
                    path=f"/foundry-api/catalog/datasets/{dataset_rid}/sql",
                    json={"query": query}
                )
                data = result.get("data", [])
                print(f"Exported {len(data)} rows from Foundry dataset {used_path}")
            else:
                raise RuntimeError("Dataset not found")
        except Exception as e:
            print(f"Foundry fetch failed: {e}. Falling back to local data.")
            data = []
    else:
        print("Foundry dev tools not installed. Using local data.")
        data = []

    # If no data from Foundry, load local parquet
    if not data:
        # Prefer quality_scores.parquet (from sync step)
        local_path = Path("dist") / "quality_scores.parquet"
        if local_path.exists():
            try:
                import pandas as pd
                df = pd.read_parquet(local_path)
                data = df.to_dict(orient="records")
                print(f"Loaded {len(data)} rows from {local_path}")
            except Exception as e:
                print(f"Failed to read {local_path}: {e}")
                data = []
        else:
            # fallback to foundry_scoring.parquet
            local_path = Path("dist") / "foundry_scoring.parquet"
            if local_path.exists():
                try:
                    import pandas as pd
                    df = pd.read_parquet(local_path)
                    data = df.to_dict(orient="records")
                    print(f"Loaded {len(data)} rows from {local_path}")
                except Exception as e:
                    print(f"Failed to read {local_path}: {e}")
                    data = []
            else:
                data = []

    # Ensure output directory
    out_dir = Path("dist") / "data"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "foundry_metrics.json"
    with open(out_file, "w") as f:
        json.dump(data, f, indent=2)
    print(f"Saved {len(data)} rows to {out_file}")

if __name__ == "__main__":
    main()

if __name__ == "__main__":
    main()