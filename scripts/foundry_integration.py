#!/usr/bin/env python3
"""
Palantir Foundry Integration for AcaciaFund

This module provides integration with Palantir Foundry to:
- Fetch datasets from Foundry
- Upload processed data back to Foundry
- Sync with the local registry

Usage:
    python scripts/foundry_integration.py fetch
    python scripts/foundry_integration.py push
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from foundry_dev_tools import FoundryContext, JWTTokenProvider, Config

# Foundry configuration
FOUNDRY_HOST = os.environ.get("FOUNDRY_HOST", "tierpalan.euw-3.palantirfoundry.co.uk")
FOUNDRY_TOKEN = os.environ.get("FOUNDRY_TOKEN")


def get_foundry_client() -> FoundryContext:
    """Create and return a Foundry context."""
    if not FOUNDRY_TOKEN:
        raise ValueError("FOUNDRY_TOKEN environment variable not set")
    
    token_provider = JWTTokenProvider(
        host=FOUNDRY_HOST,
        jwt=FOUNDRY_TOKEN
    )
    
    config = Config(
        requests_ca_bundle=None,
        debug=False
    )
    
    return FoundryContext(config=config, token_provider=token_provider)


def fetch_dataset_schema(ctx, dataset_path: str) -> dict | None:
    """Fetch and return the registered schema for a dataset."""
    try:
        if dataset_path.startswith("ri.foundry.main.dataset."):
            dataset_rid = dataset_path
        else:
            res = ctx.catalog.api_get_dataset(dataset_path)
            dataset_rid = res.json()['rid'] if hasattr(res, 'json') else res['rid']
        
        # Pull schema safely via REST client
        schema = ctx.foundry_rest_client.get_dataset_schema(dataset_rid=dataset_rid, branch="master")
        return schema
    except Exception as e:
        print(f"Error fetching schema for {dataset_path}: {e}")
        return None


def download_dataset_data(ctx, dataset_path: str, output_dir: str) -> list[str]:
    """Download raw files from a Foundry dataset to a local folder."""
    try:
        if dataset_path.startswith("ri.foundry.main.dataset."):
            dataset_rid = dataset_path
        else:
            res = ctx.catalog.api_get_dataset(dataset_path)
            dataset_rid = res.json()['rid'] if hasattr(res, 'json') else res['rid']
        
        os.makedirs(output_dir, exist_ok=True)
        files = ctx.foundry_rest_client.download_dataset_files(
            dataset_rid=dataset_rid,
            output_directory=output_dir,
            view="master"
        )
        return files
    except Exception as e:
        print(f"Error downloading data for {dataset_path}: {e}")
        return []


def push_file_to_foundry(ctx, dataset_path: str, local_file_path: str) -> bool:
    """Push a local file to a Foundry dataset via an atomic transaction."""
    try:
        from pathlib import Path
        if dataset_path.startswith("ri.foundry.main.dataset."):
            dataset_rid = dataset_path
        else:
            res = ctx.catalog.api_get_dataset(dataset_path)
            dataset_rid = res.json()['rid'] if hasattr(res, 'json') else res['rid']

        filename = os.path.basename(local_file_path)

        tx_res = ctx.catalog.api_start_transaction(dataset_rid=dataset_rid, branch_id="master")
        tx_data = tx_res.json() if hasattr(tx_res, "json") else tx_res
        tx_rid = tx_data["rid"]

        ctx.data_proxy.upload_dataset_file(
            dataset_rid=dataset_rid,
            transaction_rid=tx_rid,
            path=Path(local_file_path),
            path_in_foundry_dataset=filename
        )

        ctx.catalog.api_commit_transaction(dataset_rid=dataset_rid, transaction_rid=tx_rid)
        return True
    except Exception as e:
        print(f"Error pushing file {local_file_path} to {dataset_path}: {e}")
        try:
            if 'tx_rid' in locals():
                ctx.catalog.api_abort_transaction(dataset_rid=dataset_rid, transaction_rid=tx_rid)
        except:
            pass
        return False


def main():
    import sys
    if len(sys.argv) < 2:
        print("Usage: python foundry_integration.py [fetch|push|test]")
        print("  fetch <dataset_path> [output_dir]  - Verify schema and pull down dataset files")
        print("  push  <dataset_path> <local_file>  - Push a local file via atomic transaction")
        print("  test                               - Test Foundry client connection")
        sys.exit(1)

    command = sys.argv[1]

    try:
        from scripts.foundry_integration import get_foundry_client
        ctx = get_foundry_client()
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    if command == "test":
        print("Testing Foundry connection...")
        try:
            user_info = ctx.get_user_info()
            print(f"✓ Connected as: {user_info.username}")
            print(f"  Host: {ctx.host}")
        except Exception as e:
            print(f"✗ Connection failed: {e}")
            sys.exit(1)

    elif command == "fetch":
        if len(sys.argv) < 3:
            print("Usage: python foundry_integration.py fetch <dataset_path> [output_dir]")
            sys.exit(1)
        dataset_path = sys.argv[2]
        output_dir = sys.argv[3] if len(sys.argv) > 3 else "dist/fetched"
        
        print(f"Fetching schema for target dataset: {dataset_path}...")
        schema = fetch_dataset_schema(ctx, dataset_path)
        if schema:
            print("✓ Schema registration verified:")
            try:
                # Handle standard schema structure mappings if present
                fields = schema.get("fieldSchemaList", schema.get("schema", {}).get("fieldSchemaList", []))
                if fields:
                    for field in fields:
                        print(f"  - {field.get('name')}: {field.get('type')}")
                else:
                    print(f"  {schema}")
            except Exception:
                print(f"  {schema}")
        else:
            print("! Could not extract formal schema metadata (dataset may be raw/un-structured).")

        print(f"\nDownloading dataset files to local folder: '{output_dir}'...")
        files = download_dataset_data(ctx, dataset_path, output_dir)
        if files:
            print(f"✓ Download complete! Pulled {len(files)} file(s):")
            for f in files:
                print(f"  - {f}")
        else:
            print("✗ Fetch failed or target dataset contains no committed files.")

    elif command == "push":
        if len(sys.argv) != 4:
            print("Usage: python foundry_integration.py push <dataset_path> <local_file>")
            sys.exit(1)
        dataset_path = sys.argv[2]
        local_file = sys.argv[3]
        if not os.path.isfile(local_file):
            print(f"Local file not found: {local_file}")
            sys.exit(1)
        print(f"Pushing {local_file} to Foundry dataset {dataset_path}...")
        success = push_file_to_foundry(ctx, dataset_path, local_file)
        if success:
            print("✓ Push successful")
        else:
            print("✗ Push failed")
            sys.exit(1)
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == '__main__':
    main()
