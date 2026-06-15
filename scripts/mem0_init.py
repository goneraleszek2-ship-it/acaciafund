#!/usr/bin/env python3
"""Mem0 Session Manager - Initialize and manage Mem0 for AcaciaFund.

Usage:
    python scripts/mem0_init.py
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from services.mem0 import (
    init_db,
    start_session,
    save_insight,
    save_deployment,
    get_insights,
)


def seed_initial_context() -> None:
    """Seed initial context from current session."""
    print("Seeding initial Mem0 context...")
    
    # Save current session
    session_id = start_session(
        user_id="developer_1",
        task_description="Integrate Mem0 for session context management",
    )
    print(f"  ✓ Started session: {session_id}")
    
    # Save deployment history (simulated)
    save_deployment(
        commit_hash="006d1e0",
        branch="main",
        status="success",
        pages_generated=376,
        build_duration_ms=12000,
    )
    print("  ✓ Logged deployment: 006d1e0")
    
    # Save key insights from current session
    insights = [
        {
            "type": "decision",
            "title": "Mem0 Integration Strategy",
            "content": "Use self-hosted SQLite for Mem0 storage (no API costs, full control). "
                      "Implement hybrid approach: auto-extract from Git commits + manual logging for context not in Git.",
            "tags": ["mem0", "architecture", "decision"],
        },
        {
            "type": "context",
            "title": "Current Task: Diagrams Rebuild",
            "content": "Fix syntax errors in diagrams 1, 3, 10. Fixed .mmd files (removed emojis, collapsed multi-line nodes). "
                      "HTML generation pipeline needs update to embed fixed .mmd content.",
            "tags": ["diagrams", "mermaid", "syntax"],
        },
        {
            "type": "bug_fix",
            "title": "Mermaid Syntax Errors",
            "content": "Fixed by: stripping mermaid fences, removing emojis, collapsing multi-line node labels, "
                      "replacing Unicode ∈→in, →→-",
            "tags": ["mermaid", "syntax", "fix"],
        },
        {
            "type": "context",
            "title": "Project Stack",
            "content": "Python 3.13 + Jinja2 static site. Cloudflare Pages auto-deploy from main. "
                      "Static-first, no build framework. 376 pages generated in ~12s.",
            "tags": ["stack", "architecture"],
        },
    ]
    
    for insight in insights:
        save_insight(
            user_id="developer_1",
            insight_type=insight["type"],
            title=insight["title"],
            content=insight["content"],
            tags=insight["tags"],
        )
        print(f"  ✓ Saved insight: {insight['type']}")
    
    print(f"\n✅ Seeded {len(insights)} insights")


def main():
    parser = argparse.ArgumentParser(
        description="Initialize Mem0 for AcaciaFund"
    )
    parser.add_argument(
        "--seed",
        action="store_true",
        help="Seed initial context"
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Reset database (deletes mem0.db)"
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show Mem0 status"
    )
    
    args = parser.parse_args()
    
    if args.reset:
        import os
        db_path = Path(__file__).parent.parent / "services" / "mem0" / "mem0.db"
        if db_path.exists():
            db_path.unlink()
        print(f"✓ Deleted {db_path}")
        init_db()
        print("✓ Reinitialized database")
        return
    
    if args.status:
        insights = get_insights(user_id="developer_1", limit=10)
        print(f"Mem0 Status:")
        print(f"  Insights: {len(insights)}")
        return
    
    # Default: init + seed
    init_db()
    print("✓ Initialized Mem0 database")
    
    if args.seed:
        seed_initial_context()


if __name__ == "__main__":
    main()
