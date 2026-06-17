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


def fetch_datasets(ctx: FoundryContext) -> list[dict]:
    """Fetch dataset information from Foundry using ctx.compass."""
    # Use compass to search for all projects
    try:
        # Get all projects from compass
        projects = list(ctx.compass.search_projects())
        
        datasets = []
        for project in projects:
            try:
                resource = project.get('resource', {})
                datasets.append({
                    "rid": resource.get('rid', ''),
                    "path": resource.get('path', []),
                    "name": resource.get('name', ''),
                    "type": 'project',
                })
            except Exception as e:
                print(f"Error fetching project: {e}")
        
        return datasets
    except Exception as e:
        print(f"Error fetching resources: {e}")
        return []


def fetch_project_datasets(ctx: FoundryContext, project_rid: str) -> list[dict]:
    """Fetch datasets within a project using ctx.catalog."""
    try:
        # Use catalog to get datasets in the project
        datasets = ctx.catalog.api_get_dataset_paths() or []
        
        dataset_list = []
        for path in datasets:
            try:
                dataset_rid = ctx.catalog.api_get_dataset_rid(path)
                dataset_info = ctx.catalog.api_get_dataset(dataset_rid)
                dataset_list.append({
                    "path": path,
                    "rid": dataset_rid,
                    "name": dataset_info.get('name', path),
                    "type": dataset_info.get('type', 'unknown'),
                })
            except Exception as e:
                print(f"Error fetching dataset {path}: {e}")
        
        return dataset_list
    except Exception as e:
        print(f"Error fetching project datasets: {e}")
        return []


def fetch_dataset_data(ctx: FoundryContext, path: list[str]) -> list[dict]:
    """Fetch dataset data from Foundry using ctx.catalog."""
    try:
        # Get dataset rid from path
        dataset_rid = ctx.catalog.api_get_dataset(path[-1])['rid']
        
        # Use SQL query to fetch data
        query = "SELECT * FROM this LIMIT 100"
        result = ctx.catalog.api_request(
            method="POST",
            path=f"/foundry-api/catalog/datasets/{dataset_rid}/sql",
            json={"query": query}
        )
        return result.get("data", [])
    except Exception as e:
        print(f"Error fetching data for {path}: {e}")
        return []


def push_data_to_foundry(
    ctx: FoundryContext, 
    path: list[str], 
    data: list[dict]
) -> bool:
    """Push data to a Foundry dataset using ctx.catalog."""
    try:
        # Get dataset rid from path
        dataset_rid = ctx.catalog.api_get_dataset(path[-1])['rid']
        
        # Create a temporary CSV file
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            if data:
                import csv
                writer = csv.DictWriter(f, fieldnames=data[0].keys())
                writer.writeheader()
                writer.writerows(data)
            temp_path = f.name
        
        # Upload the file using catalog API
        with open(temp_path, 'rb') as f:
            ctx.catalog.api_upload_dataset_file(dataset_rid, f, "data.csv")
        
        # Clean up
        os.unlink(temp_path)
        
        return True
    except Exception as e:
        print(f"Error pushing data to {path}: {e}")
        return False


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python foundry_integration.py [fetch|push|test]")
        print("  fetch  - Fetch datasets from Foundry")
        print("  push   - Push data to Foundry")
        print("  test   - Test Foundry connection")
        sys.exit(1)
    
    command = sys.argv[1]
    
    try:
        ctx = get_foundry_client()
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    
    if command == "test":
        print("Testing Foundry connection...")
        try:
            user_info = ctx.get_user_info()
            print(f"✓ Connected as: {user_info.username}")
            print(f"  Organization: {getattr(user_info, 'organization', 'unknown')}")
            print(f"  Host: {ctx.host}")
        except Exception as e:
            print(f"✗ Connection failed: {e}")
            sys.exit(1)
    
    elif command == "fetch":
        print("Fetching datasets from Foundry...")
        datasets = fetch_datasets(ctx)
        print(f"Found {len(datasets)} datasets")
        for ds in datasets:
            print(f"  - {ds['path']}")
    
    elif command == "push":
        print("Pushing data to Foundry...")
        # TODO: Implement push logic
        print("Push not yet implemented")
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
