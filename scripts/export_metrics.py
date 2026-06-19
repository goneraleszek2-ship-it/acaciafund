#!/usr/bin/env python3
"""
Export metrics from Foundry dataset to local JSON.
Usage:
    python scripts/export_metrics.py
"""
import json
import os
from pathlib import Path

from foundry_dev_tools import FoundryContext, JWTTokenProvider, Config

def get_foundry_client():
    host = os.environ.get("FOUNDRY_HOST", "tierpalan.euw-3.palantirfoundry.co.uk")
    token = os.environ.get("FOUNDRY_TOKEN")
    if not token:
        raise ValueError("FOUNDRY_TOKEN environment variable not set")
    token_provider = JWTTokenProvider(host=host, jwt=token)
    config = Config(requests_ca_bundle=None, debug=False)
    return FoundryContext(config=config, token_provider=token_provider)

def main():
    ctx = get_foundry_client()
    # Example: query dataset /TierPalan-96733d/Acacia for latest metrics
    dataset_path = "/TierPalan-96733d/Acacia"  # adjust as needed
    # Get dataset rid
    dataset_info = ctx.catalog.api_get_dataset(dataset_path)
    dataset_rid = dataset_info['rid']
    # Query data (limit 1000 rows)
    query = "SELECT * FROM this LIMIT 1000"
    result = ctx.catalog.api_request(
        method="POST",
        path=f"/foundry-api/catalog/datasets/{dataset_rid}/sql",
        json={"query": query}
    )
    data = result.get("data", [])
    # Ensure output directory
    out_dir = Path("dist") / "data"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "foundry_metrics.json"
    with open(out_file, "w") as f:
        json.dump(data, f, indent=2)
    print(f"Exported {len(data)} rows to {out_file}")

if __name__ == "__main__":
    main()