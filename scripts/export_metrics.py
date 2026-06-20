#!/usr/bin/env python3
"""
Export metrics from Foundry dataset to local JSON.
If Foundry dataset not available, fall back to local Parquet files.
Add build_timestamp, deduplicate, filter columns, and error handling.
Usage:
    python scripts/export_metrics.py
"""
import json
import os
import sys
from pathlib import Path
from datetime import datetime, timezone

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

def send_notification(message):
    """Optional: send to Discord/Slack webhook via curl if env var set."""
    webhook = os.environ.get("EXPORT_ERROR_WEBHOOK")
    if webhook:
        import subprocess
        try:
            subprocess.run([
                "curl", "-X", "POST", "-H", "Content-Type: application/json",
                "-d", json.dumps({"content": message}),
                webhook
            ], check=False, capture_output=True)
        except Exception:
            pass

def main():
    out_dir = Path("dist") / "data"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "foundry_metrics.json"
    data = []
    generated_at = datetime.now(timezone.utc).isoformat()
    try:
        # Try to get from Foundry
        if FOUNDRY_AVAILABLE:
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
                # Select only needed columns to reduce payload
                query = """
                SELECT article_slug, quality_score, source_credibility, technical_accuracy,
                       practical_value, freshness, trend_relevance, educational_quality
                FROM this
                """
                result = ctx.catalog.api_request(
                    method="POST",
                    path=f"/foundry-api/catalog/datasets/{dataset_rid}/sql",
                    json={"query": query}
                )
                data = result.get("data", [])
                print(f"Exported {len(data)} rows from Foundry dataset {used_path}")
            else:
                raise RuntimeError("Dataset not found")
        else:
            print("Foundry dev tools not installed. Using local data.")
            data = []
    except Exception as e:
        err_msg = f"Foundry export failed: {e}"
        print(err_msg)
        send_notification(err_msg)
        data = []

    # If no data from Foundry, load local parquet
    if not data:
        # Prefer quality_scores.parquet (from sync step)
        local_path = Path("dist") / "quality_scores.parquet"
        if local_path.exists():
            try:
                import pandas as pd
                df = pd.read_parquet(local_path)
                # Keep only needed columns
                cols = ["article_slug", "quality_score", "source_credibility", "technical_accuracy",
                        "practical_value", "freshness", "trend_relevance", "educational_quality"]
                # Ensure columns exist
                cols = [c for c in cols if c in df.columns]
                df = df[cols]
                # Deduplicate: keep latest per article_slug if there's a timestamp column, else first
                if "generated_at" in df.columns:
                    df = df.sort_values("generated_at", ascending=False)
                df = df.drop_duplicates(subset=["article_slug"], keep="first")
                data = df.to_dict(orient="records")
                print(f"Loaded {len(data)} rows from {local_path}")
            except Exception as e:
                err_msg = f"Failed to read {local_path}: {e}"
                print(err_msg)
                send_notification(err_msg)
                data = []
        else:
            # fallback to foundry_scoring.parquet
            local_path = Path("dist") / "foundry_scoring.parquet"
            if local_path.exists():
                try:
                    import pandas as pd
                    df = pd.read_parquet(local_path)
                    cols = ["article_slug", "quality_score", "source_credibility", "technical_accuracy",
                            "practical_value", "freshness", "trend_relevance", "educational_quality"]
                    cols = [c for c in cols if c in df.columns]
                    df = df[cols]
                    if "generated_at" in df.columns:
                        df = df.sort_values("generated_at", ascending=False)
                    df = df.drop_duplicates(subset=["article_slug"], keep="first")
                    data = df.to_dict(orient="records")
                    print(f"Loaded {len(data)} rows from {local_path}")
                except Exception as e:
                    err_msg = f"Failed to read {local_path}: {e}"
                    print(err_msg)
                    send_notification(err_msg)
                    data = []
            else:
                data = []

    # Add build_timestamp to each record
    for record in data:
        record["generated_at"] = generated_at

    # Prepare final output with metadata
    output = {
        "generated_at": generated_at,
        "data": data
    }

    with open(out_file, "w") as f:
        json.dump(output, f, indent=2)
    print(f"Saved {len(data)} rows to {out_file}")

if __name__ == "__main__":
    main()

if __name__ == "__main__":
    main()