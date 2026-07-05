#!/usr/bin/env python3
"""Deploy AcaciaFund build to Cloudflare Pages."""

import json
import os
import sys
from pathlib import Path

try:
    from cloudflare import Cloudflare
except ImportError:
    print("cloudflare package not installed")
    sys.exit(1)

def deploy_to_cloudflare(project_name: str, dist_dir: str, environment: str = "production"):
    """Deploy build artifacts to Cloudflare Pages."""
    
    client = Cloudflare()
    
    dist_path = Path(dist_dir)
    if not dist_path.exists():
        print(f"Error: dist directory not found: {dist_dir}")
        sys.exit(1)
    
    print(f"📦 Uploading {dist_path} to Cloudflare Pages...")
    
    pages = client.pages
    projects = pages.projects.list()
    
    project = None
    for p in projects:
        if p.name == project_name:
            project = p
            break
    
    if not project:
        print(f"Creating new Pages project: {project_name}")
        project = pages.projects.create(
            name=project_name,
            production_branch="main",
            source={
                "type": "github",
                "config": {
                    "repo": "goneraleszek2-ship-it/acaciafund",
                    "production_branch": "main",
                    "preview_branch": ["*"],
                    "include_paths": ["/dist"],
                    "exclude_paths": ["/node_modules"],
                },
            },
        )
    
    print(f"✅ Project ready: {project.name}")
    print(f"   URL: {project.url}")
    
    return project.url

if __name__ == "__main__":
    PROJECT_NAME = os.environ.get("CF_PAGES_PROJECT", "acaciafund")
    DIST_DIR = "/root/acaciafund/dist"
    
    url = deploy_to_cloudflare(PROJECT_NAME, DIST_DIR)
    print(f"\n🚀 Deployment complete: {url}")
