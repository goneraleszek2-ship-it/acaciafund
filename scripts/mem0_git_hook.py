#!/usr/bin/env python3
"""Mem0 Git Hooks - Auto-extract insights from commits.

This script should be called from .git/hooks/commit-msg

Usage:
    # In .git/hooks/commit-msg:
    #!/bin/bash
    python3 scripts/mem0_git_hook.py "$1"
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from services.mem0 import extract_from_commit, save_insight  # noqa: E402


def main():
    if len(sys.argv) < 2:
        print("Usage: mem0_git_hook.py <commit_hash>", file=sys.stderr)
        sys.exit(1)

    commit_hash = sys.argv[1]

    # Get commit message
    import subprocess

    try:
        message = subprocess.check_output(
            ["git", "log", "-1", "--format=%B", commit_hash], cwd=str(PROJECT_ROOT), text=True
        ).strip()
    except Exception as e:
        print(f"Error getting commit message: {e}", file=sys.stderr)
        sys.exit(1)

    if not message:
        print("No commit message found", file=sys.stderr)
        sys.exit(1)

    # Extract insight
    insight = extract_from_commit(message)

    # Save to Mem0
    save_insight(
        user_id="developer_1",
        insight_type=insight["type"],
        title=insight["title"],
        content=insight["content"],
        tags=insight["tags"],
        related_files=insight["related_files"],
    )

    print(f"✅ Mem0: Extracted {insight['type']} from {commit_hash[:8]}")


if __name__ == "__main__":
    main()
