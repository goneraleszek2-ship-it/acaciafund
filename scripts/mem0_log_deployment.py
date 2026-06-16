#!/usr/bin/env python3
"""Mem0 Deployment Logger - Hook into build.py for automatic deployment logging.

Usage:
    # Called automatically by build.py
    python scripts/mem0_log_deployment.py
    
    # Or manually
    python scripts/mem0_log_deployment.py --commit abc123 --pages 376 --duration 12000
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from services.mem0 import log_deployment, save_insight


def get_git_info() -> dict:
    """Get current Git commit information."""
    try:
        commit_hash = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=str(PROJECT_ROOT),
            text=True
        ).strip()
        
        branch = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=str(PROJECT_ROOT),
            text=True
        ).strip()
        
        return {
            "commit_hash": commit_hash,
            "branch": branch,
        }
    except Exception:
        return {
            "commit_hash": "unknown",
            "branch": "unknown",
        }


def main():
    parser = argparse.ArgumentParser(
        description="Log deployment to Mem0"
    )
    parser.add_argument(
        "--commit",
        help="Git commit hash (auto-detected if not provided)"
    )
    parser.add_argument(
        "--branch",
        default="main",
        help="Git branch (default: main)"
    )
    parser.add_argument(
        "--pages",
        type=int,
        default=0,
        help="Number of pages generated"
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=0,
        help="Build duration in milliseconds"
    )
    parser.add_argument(
        "--status",
        choices=["success", "failed", "pending"],
        default="success",
        help="Deployment status"
    )
    parser.add_argument(
        "--error",
        help="Error message (if failed)"
    )
    parser.add_argument(
        "--json",
        help="JSON file with deployment data"
    )
    
    args = parser.parse_args()
    
    # Load from JSON file if provided
    if args.json:
        try:
            with open(args.json) as f:
                data = json.load(f)
                commit = data.get("commit", args.commit)
                pages = data.get("pages", args.pages)
                duration = data.get("duration", args.duration)
                status = data.get("status", args.status)
                error = data.get("error", args.error)
        except Exception as e:
            print(f"Error loading JSON: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        commit = args.commit
        pages = args.pages
        duration = args.duration
        status = args.status
        error = args.error
    
    # Auto-detect Git info if commit not provided
    if not commit:
        git_info = get_git_info()
        commit = git_info["commit_hash"]
    
    # Log deployment
    log_deployment(
        commit_hash=commit,
        status=status,
        pages_generated=pages,
        build_duration_ms=duration,
        error_message=error,
    )
    
    print(f"✅ Logged deployment: {commit[:8]} | {pages} pages | {duration/1000:.1f}s")
    
    # Save insight if this is a fix
    if status == "success" and "fix" in (error or "").lower():
        save_insight(
            user_id="developer_1",
            insight_type="bug_fix",
            title=f"Deployment fix: {error[:50] if error else 'Unknown'}",
            content=f"Fixed in commit {commit[:8]}: {error or 'Unknown error'}",
            tags=["deployment", "fix"],
        )


if __name__ == "__main__":
    main()
