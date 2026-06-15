"""Mem0 Manager - Core business logic for AcaciaFund context management.

This module provides a clean API layer that encapsulates database operations,
separating business logic from the Flask application layer.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from services.mem0 import (
    get_conversation_history,
    get_deployment_history,
    get_insights,
    query_sessions,
    query_insights_by_content,
)


class Mem0Manager:
    """Manager class for Mem0 context and deployment tracking."""

    def __init__(self, user_id: str = "developer_1"):
        """Initialize Mem0Manager with user context.
        
        Args:
            user_id: User identifier for context isolation
        """
        self.user_id = user_id

    def get_deployments(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent deployments.
        
        Args:
            limit: Maximum number of deployments to return
            
        Returns:
            List of deployment records
        """
        return get_deployment_history(limit=limit)

    def get_sessions(self, query: str = "", limit: int = 10) -> List[Dict[str, Any]]:
        """Query sessions by keyword.
        
        Args:
            query: Search query for task description or context summary
            limit: Maximum number of results
            
        Returns:
            List of matching session records
        """
        return query_sessions(self.user_id, query=query, limit=limit)

    def get_insights(
        self,
        insight_type: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Query insights with filters.
        
        Args:
            insight_type: Optional type filter (bug_fix, decision, context, etc.)
            tags: Optional list of tags to match
            limit: Maximum number of results
            
        Returns:
            List of matching insight records
        """
        return get_insights(
            user_id=self.user_id,
            insight_type=insight_type,
            tags=tags,
            limit=limit,
        )

    def search(self, query: str, limit: int = 10) -> Dict[str, Any]:
        """Search across sessions and insights.
        
        Args:
            query: Search query
            limit: Maximum number of results per category
            
        Returns:
            Dict with 'sessions' and 'insights' lists
        """
        sessions = query_sessions(self.user_id, query=query, limit=limit)
        insights = query_insights_by_content(self.user_id, query=query, limit=limit)
        
        return {
            "query": query,
            "sessions": sessions,
            "insights": insights,
            "total": len(sessions) + len(insights),
        }

    def get_active_session(self) -> Optional[Dict[str, Any]]:
        """Get the current active session.
        
        Returns:
            Active session record or None
        """
        from services.mem0 import get_active_session
        return get_active_session(self.user_id)

    def start_session(self, task_description: str) -> str:
        """Start a new development session.
        
        Args:
            task_description: Description of current task
            
        Returns:
            Session ID
        """
        from services.mem0 import start_session
        return start_session(self.user_id, task_description)

    def end_session(self, context_summary: Optional[str] = None, status: str = "completed") -> bool:
        """End the current development session.
        
        Args:
            context_summary: Summary of session context
            status: 'completed', 'abandoned', etc.
            
        Returns:
            True if session was ended
        """
        from services.mem0 import get_active_session, end_session
        active = get_active_session(self.user_id)
        if not active:
            return False
        return end_session(self.user_id, active["session_id"], context_summary, status)

    def log_deployment(
        self,
        commit_hash: str,
        status: str,
        pages_generated: int = 0,
        build_duration_ms: int = 0,
        error_message: Optional[str] = None
    ) -> bool:
        """Log a deployment event.
        
        Args:
            commit_hash: Git commit hash
            status: 'success' or 'failed'
            pages_generated: Number of pages generated
            build_duration_ms: Build duration in milliseconds
            error_message: Optional error details
            
        Returns:
            True if logged successfully
        """
        from services.mem0 import log_deployment
        try:
            log_deployment(
                commit_hash=commit_hash,
                status=status,
                pages_generated=pages_generated,
                build_duration_ms=build_duration_ms,
                error_message=error_message,
            )
            return True
        except Exception:
            return False

    def get_conversation_history(self, session_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get conversation history for a session.
        
        Args:
            session_id: Session identifier
            limit: Maximum number of messages
            
        Returns:
            List of conversation records
        """
        return get_conversation_history(self.user_id, session_id=session_id, limit=limit)
