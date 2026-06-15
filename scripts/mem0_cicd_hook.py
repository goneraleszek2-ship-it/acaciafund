#!/usr/bin/env python3
"""Mem0 CI/CD Hook - Log deployments from CI/CD workflows.

This script should be called from GitHub Actions workflows.

Usage in .github/workflows/deploy-pages.yml:
    - name: Log deployment to Mem0
      run: python3 scripts/mem0_cicd_hook.py
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from services.mem0 import log_deployment, save_insight


def main():
    # Get Git info from environment (set by GitHub Actions)
    commit_hash = os.environ.get("GITHUB_SHA", "unknown")
    branch = os.environ.get("GITHUB_REF_NAME", "main")
    
    # Get deployment status from environment
    job_status = os.environ.get("GITHUB_JOB_STATUS", "success")
    
    # Get build metrics from artifact if available
    pages_generated = 0
    build_duration_ms = 0
    
    build_meta_path = PROJECT_ROOT / "dist" / "build-meta.json"
    if build_meta_path.exists():
        try:
            with open(build_meta_path) as f:
                build_meta = json.load(f)
                pages_generated = build_meta.get("pages", 0)
                # Estimate duration from build time if available
                build_duration_ms = build_meta.get("build_time_ms", 0)
        except Exception:
            pass
    
    # Log deployment
    log_deployment(
        commit_hash=commit_hash,
        branch=branch,
        status=job_status,
        pages_generated=pages_generated,
        build_duration_ms=build_duration_ms,
    )
    
    print(f"✅ Mem0: Logged deployment {commit_hash[:8]} | {pages_generated} pages")
    
    # Save insight if this is a fix
    commit_msg = os.environ.get("GITHUB_COMMIT_MESSAGE", "")
    if "fix" in commit_msg.lower():
        save_insight(
            user_id="developer_1",
            insight_type="bug_fix",
            title=f"Deployment fix: {commit_msg[:50]}",
            content=f"Fixed in commit {commit_hash[:8]}: {commit_msg}",
            tags=["deployment", "fix"],
        )


if __name__ == "__main__":
    main()
