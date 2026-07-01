#!/usr/bin/env python3
"""Commit message for testing Mem0 integration."""

from __future__ import annotations

import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent


def main():
    """Create a test commit and extract insights."""
    # Create a test file
    test_file = PROJECT_ROOT / "services" / "mem0" / "test_commit.txt"
    test_file.write_text("Test commit content\n")

    # Stage the file
    subprocess.run(
        ["git", "add", str(test_file.relative_to(PROJECT_ROOT))],
        cwd=str(PROJECT_ROOT),
        check=True,
    )

    # Commit with a message that should trigger bug_fix extraction
    subprocess.run(
        [
            "git",
            "commit",
            "-m",
            "test: add commit message for Mem0 testing\n\nThis commit tests the extract_from_commit function.",
        ],
        cwd=str(PROJECT_ROOT),
        check=True,
    )

    # Get the commit hash
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        check=True,
    )
    commit_hash = result.stdout.strip()

    print(f"✅ Created test commit: {commit_hash[:8]}")
    print("   Message: 'test: add commit message for Mem0 testing'")

    # Clean up test file
    test_file.unlink()
    subprocess.run(
        ["git", "add", str(test_file.relative_to(PROJECT_ROOT))],
        cwd=str(PROJECT_ROOT),
        check=True,
    )
    subprocess.run(
        ["git", "commit", "-m", "chore: cleanup test file"],
        cwd=str(PROJECT_ROOT),
        check=True,
    )


if __name__ == "__main__":
    main()
