#!/usr/bin/env python3
"""Mem0 Query Tool - Command-line tool for AcaciaFund session context management.

Usage:
    python scripts/mem0_query.py <query>
    python scripts/mem0_query.py --deployments
    python scripts/mem0_query.py --sessions
    python scripts/mem0_query.py --insights
    python scripts/mem0_query.py --help
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from services.mem0 import (  # noqa: E402
    get_conversation_history,
    get_deployment_history,
    get_insights,
    query_insights_by_content,
    query_sessions,
    save_insight,
)


def format_deployment(dep: dict) -> str:
    """Format a deployment record for display."""
    status_emoji = {
        "success": "✅",
        "failed": "❌",
        "pending": "⏳",
    }.get(dep.get("status"), "❓")

    pages = dep.get("pages_generated") or dep.get("pages") or 0
    duration_ms = dep.get("build_duration_ms") or dep.get("duration_ms") or 0
    duration_s = duration_ms / 1000

    return (
        f"{status_emoji} [{dep.get('commit_hash', 'unknown')[:8]}] {dep.get('branch', 'main')} | "
        f"{pages} pages | {duration_s:.1f}s | {dep.get('created_at', 'N/A')}"
    )


def format_insight(insight: dict) -> str:
    """Format an insight record for display."""
    tags = json.loads(insight["tags"]) if insight["tags"] else []
    tag_str = f" [{', '.join(tags)}]" if tags else ""

    return (
        f"📌 [{insight['insight_type']}] {insight['title'] or 'No title'}{tag_str}\n"
        f"   {insight['content'][:100]}..."
    )


def format_session(session: dict) -> str:
    """Format a session record for display."""
    return (
        f"📝 [{session['session_id']}] {session['task_description'][:60]}...\n"
        f"   Status: {session['status']} | {session['start_time']}"
    )


def main():
    parser = argparse.ArgumentParser(
        description="Mem0 Query Tool - AcaciaFund Session Context Manager"
    )
    parser.add_argument("query", nargs="?", help="Search query for sessions/insights")
    parser.add_argument("--deployments", action="store_true", help="Show recent deployments")
    parser.add_argument("--sessions", action="store_true", help="Show recent sessions")
    parser.add_argument("--insights", action="store_true", help="Show all insights")
    parser.add_argument("--conversations", action="store_true", help="Show conversation history")
    parser.add_argument("--json", action="store_true", help="Output in JSON format")
    parser.add_argument(
        "--limit", type=int, default=10, help="Maximum number of results (default: 10)"
    )
    parser.add_argument("--add", help="Add a new insight (format: [type] title | content)")
    parser.add_argument("--type", dest="insight_type", help="Insight type for --add (bug_fix, decision, feature, pattern, architecture, performance)")
    parser.add_argument("--tags", help="Comma-separated tags for --add")

    args = parser.parse_args()

    # Default: show deployments if no specific flag
    if not any([args.query, args.deployments, args.sessions, args.insights, args.conversations, args.add]):
        args.deployments = True

    if args.deployments:
        deployments = get_deployment_history(limit=args.limit)
        if args.json:
            print(json.dumps(deployments, indent=2))
        else:
            for dep in deployments:
                print(format_deployment(dep))

    elif args.sessions:
        sessions = query_sessions(user_id="developer_1", query="", limit=args.limit)
        if args.json:
            print(json.dumps(sessions, indent=2))
        else:
            for session in sessions:
                print(format_session(session))

    elif args.insights:
        insights = get_insights(user_id="developer_1", limit=args.limit)
        if args.json:
            print(json.dumps(insights, indent=2))
        else:
            for insight in insights:
                print(format_insight(insight))

    elif args.conversations:
        history = get_conversation_history(user_id="developer_1", limit=args.limit)
        if args.json:
            print(json.dumps(history, indent=2))
        else:
            for msg in history:
                role = "👤" if msg["role"] == "user" else "🤖"
                print(f"{role} [{msg['created_at']}] {msg['content'][:80]}...")

    elif args.query:
        # Search across sessions and insights
        sessions = query_sessions(user_id="developer_1", query=args.query, limit=args.limit)
        insights = query_insights_by_content(
            user_id="developer_1", query=args.query, limit=args.limit
        )

        if args.json:
            result = {"sessions": sessions, "insights": insights}
            print(json.dumps(result, indent=2))
        else:
            print(f"🔍 Query: '{args.query}'")
            print()

            if sessions:
                print("📚 Sessions:")
                for session in sessions:
                    print(f"  {format_session(session)}")
                print()

            if insights:
                print("💡 Insights:")
                for insight in insights:
                    print(f"  {format_insight(insight)}")

            if not sessions and not insights:
                print("No results found.")

    elif args.add:
        # Parse insight format: [type] title | content
        import re

        insight_text = args.add.strip()

        # Extract type from brackets
        type_match = re.match(r'\[([^\]]+)\]\s*(.+)', insight_text)
        if type_match:
            insight_type = type_match.group(1)
            rest = type_match.group(2)
        else:
            insight_type = args.insight_type or "context"
            rest = insight_text

        # Split title and content
        if "|" in rest:
            title, content = rest.split("|", 1)
            title = title.strip()
            content = content.strip()
        else:
            title = rest.split("\n")[0].strip()
            content = rest.strip()

        # Parse tags
        tags = [t.strip() for t in (args.tags or "").split(",")] if args.tags else []

        # Save insight
        insight_id = save_insight(
            user_id="developer_1",
            insight_type=insight_type,
            title=title,
            content=content,
            tags=tags if tags else None
        )

        print(f"✅ Insight saved with ID: {insight_id}")
        print(f"   Type: {insight_type}")
        print(f"   Title: {title}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
