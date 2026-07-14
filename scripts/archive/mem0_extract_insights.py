#!/usr/bin/env python3
"""Mem0 Commit Extractor - Auto-extract insights from Git commit messages.

Usage:
    # Called from git hook
    python scripts/mem0_extract_insights.py "fix: diagrams syntax errors"

    # Or manually
    python scripts/mem0_extract_insights.py --message "fix: diagrams syntax errors"
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from services.mem0 import extract_from_commit, save_insight  # noqa: E402


def get_commit_message(commit_hash: str) -> str:
    """Get commit message for a hash."""
    try:
        return subprocess.check_output(
            ["git", "log", "-1", "--format=%B", commit_hash], cwd=str(PROJECT_ROOT), text=True
        ).strip()
    except Exception:
        return ""


def main():
    parser = argparse.ArgumentParser(description="Extract insights from Git commit messages")
    parser.add_argument("message", nargs="?", help="Commit message to parse")
    parser.add_argument("--commit", help="Git commit hash to extract message from")
    parser.add_argument("--json", action="store_true", help="Output parsed insight as JSON")

    args = parser.parse_args()

    # Get commit message
    if args.commit:
        message = get_commit_message(args.commit)
    elif args.message:
        message = args.message
    else:
        parser.error("Either --commit or message argument required")
        sys.exit(1)

    if not message:
        print("No commit message found", file=sys.stderr)
        sys.exit(1)

    # Extract insight
    insight = extract_from_commit(message)

    if args.json:
        print(json.dumps(insight, indent=2))
    else:
        print("Extracted insight from commit:")
        print(f"  Type: {insight['type']}")
        print(f"  Title: {insight['title']}")
        print(f"  Tags: {', '.join(insight['tags'])}")
        print(
            f"  Files: {', '.join(insight['related_files']) if insight['related_files'] else 'None'}"
        )

    # Save to Mem0
    save_insight(
        user_id="developer_1",
        insight_type=insight["type"],
        title=insight["title"],
        content=insight["content"],
        tags=insight["tags"],
        related_files=insight["related_files"],
    )

    print(f"✅ Saved to Mem0: {insight['type']}")


if __name__ == "__main__":
    main()
