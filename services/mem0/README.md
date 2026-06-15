# AcaciaFund Mem0 Integration

This directory contains the Mem0 context management system for AcaciaFund.

## Overview

Mem0 provides automatic session context tracking, deployment logging, and insight extraction across development sessions.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    DEVELOPER WORKFLOW                            │
│  (This Chat Session)                                            │
│       ↓                                                          │
│  Mem0 Manager (services/mem0_manager.py)                       │
│       ↓                                                          │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  SQLite Database (services/mem0/mem0.db)                 │   │
│  │  - conversations  - deployments  - insights  - sessions   │   │
│  └──────────────────────────────────────────────────────────┘   │
│         ↓                              ↓                         │
│  Git Commits                      CI/CD Workflow               │
│       ↓                              ↓                         │
│  Auto-extract insights            Auto-log deployments         │
└─────────────────────────────────────────────────────────────────┘
```

## Database Schema

### `conversations`
- Stores chat session messages
- Fields: `id`, `user_id`, `session_id`, `role`, `content`, `metadata`, `created_at`

### `deployments`
- Tracks build/deployment events
- Fields: `id`, `commit_hash`, `branch`, `status`, `pages_generated`, `build_duration_ms`, `error_message`, `metadata`, `created_at`

### `insights`
- Technical insights from commits, PRs, manual logging
- Fields: `id`, `user_id`, `insight_type`, `title`, `content`, `tags`, `related_files`, `related_slugs`, `created_at`

### `sessions`
- Development sessions with context
- Fields: `id`, `user_id`, `session_id`, `task_description`, `status`, `context_summary`, `start_time`, `end_time`, `created_at`

## Usage

### Query Tool

```bash
# Show recent deployments
python scripts/mem0_query.py --deployments

# Search sessions and insights
python scripts/mem0_query.py "diagrams rebuild"

# Show all insights
python scripts/mem0_query.py --insights

# JSON output
python scripts/mem0_query.py --json
```

### Deployment Logging

```bash
# Called automatically by build.py
python scripts/mem0_log_deployment.py

# Manual logging
python scripts/mem0_log_deployment.py --commit abc123 --pages 376 --duration 12000
```

### Commit Insight Extraction

```bash
# From commit hash
python scripts/mem0_extract_insights.py --commit abc123

# From message
python scripts/mem0_extract_insights.py "fix: diagrams syntax errors"
```

## Git Hook Integration

Add to `.git/hooks/commit-msg`:

```bash
#!/bin/bash
# Auto-extract insights from commit messages
python3 scripts/mem0_git_hook.py "$1"
```

## CI/CD Integration

Add to `.github/workflows/deploy-pages.yml`:

```yaml
- name: Log deployment to Mem0
  run: python3 scripts/mem0_log_deployment.py
```

## API Reference

### `Mem0Manager(user_id="developer_1")`

#### `get_deployments(limit=10)`
Get recent deployments.

#### `get_sessions(query="", limit=10)`
Query sessions by keyword.

#### `get_insights(insight_type=None, tags=None, limit=20)`
Query insights with filters.

#### `search(query, limit=10)`
Search across sessions and insights.

#### `get_active_session()`
Get the current active session.

#### `start_session(task_description)`
Start a new development session.

#### `end_session(context_summary=None, status="completed")`
End the current development session.

#### `log_deployment(commit_hash, status, pages_generated, build_duration_ms, error_message)`
Log a deployment event.

#### `get_conversation_history(session_id, limit=20)`
Get conversation history for a session.

## File Structure

```
services/mem0/
├── __init__.py          # Core Mem0 API
├── mem0.db              # SQLite database (auto-created)
└── README.md            # This file

services/mem0_manager.py  # Business logic layer

scripts/
├── mem0_query.py        # Query tool CLI
├── mem0_log_deployment.py  # Deployment logger
├── mem0_extract_insights.py  # Commit parser
├── mem0_admin.py        # Admin web UI
├── mem0_init.py         # Initialization script
├── mem0_git_hook.py     # Git hook wrapper
└── mem0_cicd_hook.py    # CI/CD hook

templates/mem0/
├── dashboard.html       # Admin dashboard
├── deployments.html     # Deployments list
├── insights.html        # Insights list
└── sessions.html        # Sessions list
```

## Migration from AGENTS.md

The Mem0 system replaces the manual `AGENTS.md` session tracking with automatic context capture:

- **Before**: Manual `AGENTS.md` updates
- **After**: Automatic session logging via `start_session()`/`end_session()`

- **Before**: No deployment history
- **After**: Automatic logging via `log_deployment()`

- **Before**: No insight extraction
- **After**: Auto-extract from commits via `extract_from_commit()`

## Future Enhancements

- [ ] Web UI for browsing Mem0 data
- [ ] GitHub Actions webhook integration
- [ ] Slack/Teams notifications for deployments
- [ ] Mem0 API cloud sync (optional)
- [ ] AI-powered insight clustering
