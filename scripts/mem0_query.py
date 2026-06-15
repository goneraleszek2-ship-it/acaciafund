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

from services.mem0 import (
    get_deployment_history,
    get_insights,
    query_sessions,
    query_insights_by_content,
    get_conversation_history,
)


def format_deployment(dep: dict) -> str:
    """Format a deployment record for display."""
    status_emoji = {
        "success": "✅",
        "failed": "❌",
        "pending": "⏳",
    }.get(dep["status"], "❓")
    
    duration_s = dep["build_duration_ms"] / 1000 if dep["build_duration_ms"] else 0
    pages = dep["pages_generated"] or 0
    
    return (
        f"{status_emoji} [{dep['commit_hash'][:8]}] {dep['branch']} | "
        f"{pages} pages | {duration_s:.1f}s | {dep['created_at']}"
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
    parser.add_argument(
        "query",
        nargs="?",
        help="Search query for sessions/insights"
    )
    parser.add_argument(
        "--deployments",
        action="store_true",
        help="Show recent deployments"
    )
    parser.add_argument(
        "--sessions",
        action="store_true",
        help="Show recent sessions"
    )
    parser.add_argument(
        "--insights",
        action="store_true",
        help="Show all insights"
    )
    parser.add_argument(
        "--conversations",
        action="store_true",
        help="Show conversation history"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output in JSON format"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Maximum number of results (default: 10)"
    )
    
    args = parser.parse_args()
    
    # Default: show deployments if no specific flag
    if not any([args.query, args.deployments, args.sessions, args.insights, args.conversations]):
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
        insights = query_insights_by_content(user_id="developer_1", query=args.query, limit=args.limit)
        
        if args.json:
            result = {
                "sessions": sessions,
                "insights": insights
            }
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
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
