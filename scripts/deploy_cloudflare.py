#!/usr/bin/env python3
"""Trigger new Cloudflare Pages deployment via GitHub Actions API."""

import json
import os
import sys
import requests
from pathlib import Path

def trigger_workflow_dispatch(repo_owner: str, repo_name: str, branch: str, api_token: str):
    """Trigger GitHub Actions workflow_dispatch event."""
    
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    
    payload = {
        "ref": branch,
        "inputs": {}
    }
    
    response = requests.post(
        f"https://api.github.com/repos/{repo_owner}/{repo_name}/actions/workflows/deploy.yml/dispatches",
        headers=headers,
        json=payload,
    )
    
    if response.status_code != 204:
        print(f"Failed to trigger workflow: {response.status_code}")
        print(f"Response: {response.text[:500]}")
        sys.exit(1)
    
    print(f"✅ GitHub Actions workflow triggered!")
    print(f"   Repository: {repo_owner}/{repo_name}")
    print(f"   Branch: {branch}")
    
    return True

if __name__ == "__main__":
    REPO_OWNER = os.environ.get("REPO_OWNER", "goneraleszek2-ship-it")
    REPO_NAME = os.environ.get("REPO_NAME", "acaciafund")
    BRANCH = os.environ.get("BRANCH", "main")
    API_TOKEN = os.environ.get("GITHUB_TOKEN", os.environ.get("CLOUDFLARE_API_KEY", ""))
    
    success = trigger_workflow_dispatch(REPO_OWNER, REPO_NAME, BRANCH, API_TOKEN)
    print(f"\n🚀 Deployment workflow initiated")
