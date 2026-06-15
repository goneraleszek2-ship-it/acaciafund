#!/usr/bin/env python3
"""Test Mem0 integration for AcaciaFund."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from services.mem0 import (
    init_db,
    save_conversation,
    get_conversation_history,
    save_deployment,
    get_deployment_history,
    save_insight,
    get_insights,
    start_session,
    end_session,
    get_active_session,
    extract_from_commit,
    log_deployment,
    query_sessions,
    query_insights_by_content,
)


def test_all():
    """Run all Mem0 tests."""
    print("=" * 60)
    print("Mem0 Integration Tests")
    print("=" * 60)
    
    # Test 1: DB initialization
    print("\n1. Database initialization...")
    init_db()
    print("   ✓ Database initialized")
    
    # Test 2: Save conversation
    print("\n2. Save conversation...")
    conv_id = save_conversation(
        user_id="developer_1",
        role="user",
        content="What did we do so far?",
        session_id="test_session_001",
    )
    print(f"   ✓ Saved conversation (id={conv_id})")
    
    conv_id2 = save_conversation(
        user_id="developer_1",
        role="assistant",
        content="We integrated Mem0 for context management.",
        session_id="test_session_001",
    )
    print(f"   ✓ Saved response (id={conv_id2})")
    
    # Test 3: Get conversation history
    print("\n3. Get conversation history...")
    history = get_conversation_history("developer_1", "test_session_001", limit=10)
    assert len(history) >= 2
    print(f"   ✓ Retrieved {len(history)} messages")
    
    # Test 4: Save deployment
    print("\n4. Save deployment...")
    dep_id = save_deployment(
        commit_hash="abc123def",
        branch="main",
        status="success",
        pages_generated=100,
        build_duration_ms=5000,
    )
    print(f"   ✓ Saved deployment (id={dep_id})")
    
    # Test 5: Get deployment history
    print("\n5. Get deployment history...")
    deployments = get_deployment_history(limit=10)
    assert len(deployments) >= 1
    print(f"   ✓ Retrieved {len(deployments)} deployments")
    
    # Test 6: Save insight
    print("\n6. Save insight...")
    insight_id = save_insight(
        user_id="developer_1",
        insight_type="bug_fix",
        title="Test bug fix",
        content="Fixed an issue in the build pipeline",
        tags=["test", "bug_fix"],
    )
    print(f"   ✓ Saved insight (id={insight_id})")
    
    # Test 7: Get insights
    print("\n7. Get insights...")
    insights = get_insights(user_id="developer_1", limit=10)
    assert len(insights) >= 1
    print(f"   ✓ Retrieved {len(insights)} insights")
    
    # Test 8: Session management
    print("\n8. Session management...")
    session_id = start_session(
        user_id="developer_1",
        task_description="Test session",
    )
    print(f"   ✓ Started session: {session_id}")
    
    active = get_active_session("developer_1")
    assert active is not None
    print(f"   ✓ Active session found")
    
    ended = end_session("developer_1", session_id, "Test completed", "completed")
    assert ended
    print(f"   ✓ Ended session")
    
    # Test 9: Extract from commit
    print("\n9. Extract from commit...")
    insight = extract_from_commit("fix: diagrams syntax errors")
    assert insight["type"] == "bug_fix"
    print(f"   ✓ Extracted type: {insight['type']}")
    
    # Test 10: Log deployment
    print("\n10. Log deployment (convenience)...")
    log_deployment("def456ghi", "success", 200, 8000)
    print(f"   ✓ Logged deployment")
    
    # Test 11: Query sessions
    print("\n11. Query sessions...")
    sessions = query_sessions("developer_1", "test", limit=10)
    print(f"   ✓ Found {len(sessions)} matching sessions")
    
    # Test 12: Query insights by content
    print("\n12. Query insights by content...")
    found = query_insights_by_content("developer_1", "build", limit=10)
    print(f"   ✓ Found {len(found)} matching insights")
    
    print("\n" + "=" * 60)
    print("✅ All tests passed!")
    print("=" * 60)


if __name__ == "__main__":
    test_all()
