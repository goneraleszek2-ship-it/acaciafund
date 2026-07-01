#!/usr/bin/env python3
"""Mem0 Admin UI - Simple web interface for browsing Mem0 data.

Usage:
    pip install flask
    python scripts/mem0_admin.py
    # Open http://localhost:5000/mem0
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from flask import Flask, jsonify, render_template, request  # noqa: E402

from services.mem0_manager import Mem0Manager  # noqa: E402

app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True


@app.route("/mem0/")
def index():
    """Show Mem0 dashboard."""
    manager = Mem0Manager()

    try:
        deployments = manager.get_deployments(limit=5)
        insights = manager.get_insights(limit=5)
        sessions = manager.get_sessions(limit=5)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return render_template(
        "mem0/dashboard.html",
        deployments=deployments,
        insights=insights,
        sessions=sessions,
    )


@app.route("/mem0/api/deployments")
def api_deployments():
    """Get deployments API."""
    limit = int(request.args.get("limit", 10))
    manager = Mem0Manager()

    try:
        deployments = manager.get_deployments(limit=limit)
        return jsonify(deployments)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/mem0/api/insights")
def api_insights():
    """Get insights API."""
    user_id = request.args.get("user_id", "developer_1")
    itype = request.args.get("type")
    tags = request.args.get("tags")
    limit = int(request.args.get("limit", 20))

    tags_list = tags.split(",") if tags else None

    manager = Mem0Manager(user_id=user_id)

    try:
        insights = manager.get_insights(
            insight_type=itype,
            tags=tags_list,
            limit=limit,
        )
        return jsonify(insights)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/mem0/api/sessions")
def api_sessions():
    """Get sessions API."""
    user_id = request.args.get("user_id", "developer_1")
    query = request.args.get("q", "")
    limit = int(request.args.get("limit", 10))

    manager = Mem0Manager(user_id=user_id)

    try:
        sessions = manager.get_sessions(query=query, limit=limit)
        return jsonify(sessions)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/mem0/api/search")
def api_search():
    """Search across sessions and insights."""
    user_id = request.args.get("user_id", "developer_1")
    query = request.args.get("q", "")
    limit = int(request.args.get("limit", 10))

    manager = Mem0Manager(user_id=user_id)

    try:
        results = manager.search(query=query, limit=limit)
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/mem0/deployments")
def deployments():
    """Show deployments page."""
    manager = Mem0Manager()

    try:
        deployments = manager.get_deployments(limit=50)
        return render_template("mem0/deployments.html", deployments=deployments)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/mem0/insights")
def mem0_insights():
    """Show insights page."""
    manager = Mem0Manager()

    try:
        insights = manager.get_insights(limit=100)
        return render_template("mem0/insights.html", insights=insights)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/mem0/sessions")
def mem0_sessions():
    """Show sessions page."""
    manager = Mem0Manager()

    try:
        sessions = manager.get_sessions(limit=50)
        return render_template("mem0/sessions.html", sessions=sessions)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
