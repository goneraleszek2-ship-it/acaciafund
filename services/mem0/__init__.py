"""Mem0 Manager for AcaciaFund - Session Context & Deployment Tracking.

This module provides a unified interface for:
- Storing and querying conversation sessions
- Tracking deployments and build events
- Auto-extracting insights from Git commits and PRs
- Managing session state across development sessions
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# Try to import mem0ai, fall back to pure SQLite if not available
try:
    from mem0 import MemoryClient
    MEM0_AVAILABLE = True
except ImportError:
    MEM0_AVAILABLE = False

BASE_DIR = Path(__file__).parent.parent
MEM0_DIR = BASE_DIR / "services" / "mem0"
DB_PATH = MEM0_DIR / "mem0.db"

# Ensure directory exists
MEM0_DIR.mkdir(parents=True, exist_ok=True)


def get_connection() -> sqlite3.Connection:
    """Get database connection with row factory."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Initialize SQLite database with required tables."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        
        # Conversations table - store chat sessions
        cur.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                session_id TEXT,
                role TEXT NOT NULL,  -- 'user' or 'assistant'
                content TEXT NOT NULL,
                metadata TEXT,
                created_at TEXT NOT NULL
            )
        """)
        
        # Deployments table - track build/deployment events
        cur.execute("""
            CREATE TABLE IF NOT EXISTS deployments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                commit_hash TEXT,
                branch TEXT,
                status TEXT NOT NULL,  -- 'success', 'failed', 'pending'
                pages_generated INTEGER,
                build_duration_ms INTEGER,
                error_message TEXT,
                metadata TEXT,
                created_at TEXT NOT NULL
            )
        """)
        
        # Insights table - store technical insights
        cur.execute("""
            CREATE TABLE IF NOT EXISTS insights (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                insight_type TEXT NOT NULL,  -- 'bug_fix', 'decision', 'task', 'context'
                title TEXT,
                content TEXT NOT NULL,
                tags TEXT,
                related_files TEXT,
                related_slugs TEXT,
                created_at TEXT NOT NULL
            )
        """)
        
        # Sessions table - track development sessions
        cur.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                session_id TEXT UNIQUE,
                task_description TEXT,
                status TEXT NOT NULL,  -- 'active', 'completed', 'abandoned'
                context_summary TEXT,
                start_time TEXT NOT NULL,
                end_time TEXT,
                created_at TEXT NOT NULL
            )
        """)
        
        # Index for faster queries
        cur.execute("CREATE INDEX IF NOT EXISTS idx_conversations_user ON conversations(user_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_conversations_session ON conversations(session_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_deployments_commit ON deployments(commit_hash)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_insights_type ON insights(insight_type)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_insights_tags ON insights(tags)")
        
        conn.commit()
    finally:
        conn.close()


def utc_now() -> str:
    """Get current UTC timestamp in ISO format."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def save_conversation(
    user_id: str,
    role: str,
    content: str,
    session_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> int:
    """Save a conversation message to the database.
    
    Args:
        user_id: Unique identifier for the user/developer
        role: 'user' or 'assistant'
        content: Message content
        session_id: Optional session identifier
        metadata: Optional JSON-serializable metadata
        
    Returns:
        The ID of the inserted record
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO conversations (user_id, role, content, session_id, metadata, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                role,
                content,
                session_id,
                json.dumps(metadata) if metadata else None,
                utc_now()
            )
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def get_conversation_history(
    user_id: str,
    session_id: Optional[str] = None,
    limit: int = 20
) -> List[Dict[str, Any]]:
    """Get conversation history for a user/session.
    
    Args:
        user_id: User identifier
        session_id: Optional session filter
        limit: Maximum number of messages to return
        
    Returns:
        List of conversation records
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        if session_id:
            cur.execute(
                """
                SELECT * FROM conversations 
                WHERE user_id = ? AND session_id = ?
                ORDER BY created_at DESC LIMIT ?
                """,
                (user_id, session_id, limit)
            )
        else:
            cur.execute(
                """
                SELECT * FROM conversations 
                WHERE user_id = ?
                ORDER BY created_at DESC LIMIT ?
                """,
                (user_id, limit)
            )
        
        rows = cur.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def save_deployment(
    commit_hash: str,
    branch: str,
    status: str,
    pages_generated: int = 0,
    build_duration_ms: int = 0,
    error_message: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> int:
    """Log a deployment/build event.
    
    Args:
        commit_hash: Git commit hash
        branch: Git branch
        status: 'success', 'failed', or 'pending'
        pages_generated: Number of pages generated
        build_duration_ms: Build duration in milliseconds
        error_message: Optional error details
        metadata: Optional JSON-serializable metadata
        
    Returns:
        The ID of the inserted record
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO deployments 
            (commit_hash, branch, status, pages_generated, build_duration_ms, error_message, metadata, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                commit_hash,
                branch,
                status,
                pages_generated,
                build_duration_ms,
                error_message,
                json.dumps(metadata) if metadata else None,
                utc_now()
            )
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def get_deployment_history(limit: int = 10) -> List[Dict[str, Any]]:
    """Get recent deployments.
    
    Args:
        limit: Maximum number of deployments to return
        
    Returns:
        List of deployment records
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT * FROM deployments 
            ORDER BY created_at DESC LIMIT ?
            """,
            (limit,)
        )
        
        rows = cur.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def save_insight(
    user_id: str,
    insight_type: str,
    content: str,
    title: Optional[str] = None,
    tags: Optional[List[str]] = None,
    related_files: Optional[List[str]] = None,
    related_slugs: Optional[List[str]] = None
) -> int:
    """Save a technical insight.
    
    Args:
        user_id: User identifier
        insight_type: 'bug_fix', 'decision', 'task', 'context', etc.
        content: Insight details
        title: Optional title
        tags: List of tags for filtering
        related_files: List of related file paths
        related_slugs: List of related content slugs
        
    Returns:
        The ID of the inserted record
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO insights 
            (user_id, insight_type, title, content, tags, related_files, related_slugs, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                insight_type,
                title,
                content,
                json.dumps(tags) if tags else None,
                json.dumps(related_files) if related_files else None,
                json.dumps(related_slugs) if related_slugs else None,
                utc_now()
            )
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def get_insights(
    user_id: Optional[str] = None,
    insight_type: Optional[str] = None,
    tags: Optional[List[str]] = None,
    limit: int = 20
) -> List[Dict[str, Any]]:
    """Query insights with filters.
    
    Args:
        user_id: Optional user filter
        insight_type: Optional type filter
        tags: Optional list of tags to match
        limit: Maximum number of results
        
    Returns:
        List of matching insight records
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        query = "SELECT * FROM insights WHERE 1=1"
        params = []
        
        if user_id:
            query += " AND user_id = ?"
            params.append(user_id)
        
        if insight_type:
            query += " AND insight_type = ?"
            params.append(insight_type)
        
        if tags:
            # Match any of the provided tags
            tag_conditions = " OR ".join(["tags LIKE ?" for _ in tags])
            query += f" AND ({tag_conditions})"
            params.extend([f"%{tag}%" for tag in tags])
        
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        
        cur.execute(query, params)
        rows = cur.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def start_session(
    user_id: str,
    task_description: str,
    session_id: Optional[str] = None
) -> str:
    """Start a new development session.
    
    Args:
        user_id: User identifier
        task_description: Description of current task
        session_id: Optional session ID (auto-generated if not provided)
        
    Returns:
        Session ID
    """
    if not session_id:
        import uuid
        session_id = f"session_{uuid.uuid4().hex[:8]}"
    
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO sessions 
            (user_id, session_id, task_description, status, start_time, created_at)
            VALUES (?, ?, ?, 'active', ?, ?)
            """,
            (user_id, session_id, task_description, utc_now(), utc_now())
        )
        conn.commit()
        return session_id
    finally:
        conn.close()


def end_session(
    user_id: str,
    session_id: str,
    context_summary: Optional[str] = None,
    status: str = "completed"
) -> bool:
    """End a development session.
    
    Args:
        user_id: User identifier
        session_id: Session to end
        context_summary: Summary of session context
        status: 'completed', 'abandoned', etc.
        
    Returns:
        True if session was ended
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE sessions 
            SET status = ?, end_time = ?, context_summary = ?
            WHERE user_id = ? AND session_id = ?
            """,
            (status, utc_now(), context_summary, user_id, session_id)
        )
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def get_active_session(user_id: str) -> Optional[Dict[str, Any]]:
    """Get the current active session for a user.
    
    Args:
        user_id: User identifier
        
    Returns:
        Session record or None
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT * FROM sessions 
            WHERE user_id = ? AND status = 'active'
            ORDER BY start_time DESC LIMIT 1
            """,
            (user_id,)
        )
        row = cur.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def extract_from_commit(message: str) -> Dict[str, Any]:
    """Extract structured insights from a Git commit message.
    
    Args:
        message: Raw commit message
        
    Returns:
        Dict with extracted type, title, content, and tags
    """
    # Common patterns
    patterns = {
        "bug_fix": [r"fix", r"bug", r"error", r"syntax", r"broken"],
        "feature": [r"add", r"new", r"feature", r"implement"],
        "refactor": [r"refactor", r"restructure", r"cleanup"],
        "documentation": [r"doc", r"readme", r"comment"],
        "deployment": [r"deploy", r"ci", r"workflow"],
        "configuration": [r"config", r"setup", r"env"],
    }
    
    type_map = {
        "fix": "bug_fix",
        "bug": "bug_fix",
        "error": "bug_fix",
        "syntax": "bug_fix",
        "broken": "bug_fix",
        "add": "feature",
        "new": "feature",
        "feature": "feature",
        "implement": "feature",
        "refactor": "refactor",
        "restructure": "refactor",
        "cleanup": "refactor",
        "doc": "documentation",
        "readme": "documentation",
        "comment": "documentation",
        "deploy": "deployment",
        "ci": "deployment",
        "workflow": "deployment",
        "config": "configuration",
        "setup": "configuration",
        "env": "configuration",
    }
    
    message_lower = message.lower()
    
    # Detect type
    detected_type = "context"
    for keyword, itype in type_map.items():
        if keyword in message_lower:
            detected_type = itype
            break
    
    # Extract files if mentioned
    files = []
    if ":" in message:
        parts = message.split(":")
        if len(parts) > 1:
            file_part = parts[-1].strip()
            if "," in file_part or " " in file_part:
                # Try to extract filenames
                import re
                files = re.findall(r'[a-zA-Z0-9_/.-]+\.(py|md|json|toml|yml|yaml|sql)', file_part)
    
    # Extract tags from keywords
    tags = []
    for keyword in type_map.keys():
        if keyword in message_lower:
            tags.append(keyword)
    
    return {
        "type": detected_type,
        "title": message.split("\n")[0] if "\n" in message else message,
        "content": message,
        "tags": tags,
        "related_files": files,
    }


def log_deployment(
    commit_hash: str,
    status: str,
    pages_generated: int = 0,
    build_duration_ms: int = 0,
    error_message: Optional[str] = None
) -> None:
    """Convenience function to log a deployment event.
    
    Args:
        commit_hash: Git commit hash
        status: 'success' or 'failed'
        pages_generated: Number of pages generated
        build_duration_ms: Build duration in milliseconds
        error_message: Optional error details
    """
    save_deployment(
        commit_hash=commit_hash,
        branch="main",
        status=status,
        pages_generated=pages_generated,
        build_duration_ms=build_duration_ms,
        error_message=error_message,
        metadata={"source": "build.py"}
    )


def query_sessions(
    user_id: str,
    query: str,
    limit: int = 5
) -> List[Dict[str, Any]]:
    """Query session context using keyword matching.
    
    Args:
        user_id: User identifier
        query: Search query
        limit: Maximum results
        
    Returns:
        List of matching sessions
    """
    query_lower = query.lower()
    
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT * FROM sessions 
            WHERE user_id = ? 
            AND (task_description LIKE ? OR context_summary LIKE ?)
            ORDER BY start_time DESC LIMIT ?
            """,
            (user_id, f"%{query_lower}%", f"%{query_lower}%", limit)
        )
        rows = cur.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def query_insights_by_content(
    user_id: str,
    query: str,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """Query insights by content search.
    
    Args:
        user_id: User identifier
        query: Search query
        limit: Maximum results
        
    Returns:
        List of matching insights
    """
    query_lower = query.lower()
    
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT * FROM insights 
            WHERE user_id = ? 
            AND (content LIKE ? OR title LIKE ?)
            ORDER BY created_at DESC LIMIT ?
            """,
            (user_id, f"%{query_lower}%", f"%{query_lower}%", limit)
        )
        rows = cur.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


# Initialize on module import
init_db()
