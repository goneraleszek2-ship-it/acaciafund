"""AcaciaFund Admin Panel - Enhanced with quality scoring, search, filtering, and batch operations."""

from __future__ import annotations

import json
import os
import re
import shutil
import sys
import tempfile
import time
import traceback
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import quote, unquote

import flask
from flask import Flask, render_template, request, jsonify, abort, redirect, session

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import flask
from flask import Flask, render_template, request, jsonify, abort, redirect

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.fetch_images import (
    build_section_query, expand_query, parse_sections,
    compute_break_points, score_result, ALL_BACKENDS,
    MAX_IMAGE_WIDTH, MIN_SCORE, PILLAR_KEYWORDS,
    PILLAR_VISUAL_KEYWORDS, SECTION_TYPES, SECTION_FALLBACK_QUERIES,
)

from core.images.manifest import load_manifest, get_manifest_entry, MANIFEST_PATH
from core.visuals import TOPIC_ICONS, _pick_subtopic, SUBTOPIC_CATEGORIES

app = Flask(__name__, secret_key='acaciafund-admin-secret-key-2026')
app.config["TEMPLATES_AUTO_RELOAD"] = True

REGISTRY_PATH = PROJECT_ROOT / "registry.json"
IMAGES_DIR = PROJECT_ROOT / "static" / "images" / "generated"
TAGS_PATH = PROJECT_ROOT / "registry" / "image-tags.json"
QUALITY_SCORES_PATH = PROJECT_ROOT / "registry" / "image-quality.json"

# Session timeout: 30 minutes
app.config['PERMANENT_SESSION_LIFETIME'] = 1800

# Quality scoring weights
QUALITY_WEIGHTS = {
    "relevance": 0.40,      # How relevant to article content
    "resolution": 0.25,     # Image resolution quality
    "completeness": 0.20,   # Metadata completeness
    "visual_score": 0.15,   # Visual appeal (blur, noise)
}

# Pillar categories for filtering
PILLARS = ["aml", "stock", "data-engineering", "knowledge", "learn"]
DIFFICULTIES = ["beginner", "intermediate", "advanced", "all"]
QUALITY_TIERS = ["high", "medium", "low", "all"]

# Backend sources
BACKENDS = {name: func for name, func in ALL_BACKENDS}


# ══════════════════════════════════════════════════════════════
# Session & Authentication
# ══════════════════════════════════════════════════════════════

def _require_auth():
    """Require user to be logged in."""
    if 'user_id' not in session:
        return jsonify({"error": "Authentication required"}), 401
    return None


def _get_user_info():
    """Get user information from session."""
    user_id = session.get('user_id')
    if not user_id:
        return {"id": "admin", "name": "Admin"}
    return {"id": user_id, "name": f"User {user_id}"}


# ══════════════════════════════════════════════════════════════
# Data Loading & Caching
# ══════════════════════════════════════════════════════════════

_registry_data: dict[str, Any] | None = None
_articles: list[dict] | None = None
_image_index: dict[str, dict] | None = None
_manifest: dict | None = None
_quality_scores: dict[str, dict] | None = None


def _load_registry() -> list[dict]:
    """Load articles from registry.json."""
    global _registry_data, _articles
    if _articles is not None:
        return _articles
    if not REGISTRY_PATH.exists():
        _articles = []
        return _articles
    try:
        raw = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
        _registry_data = raw
        _articles = raw.get("content", [])
    except (json.JSONDecodeError, OSError):
        _articles = []
    return _articles


def _save_registry() -> None:
    """Write registry atomically."""
    if _registry_data is None:
        return
    tmp = REGISTRY_PATH.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(_registry_data, indent=2, ensure_ascii=False), encoding="utf-8")
    shutil.move(str(tmp), str(REGISTRY_PATH))


def _load_quality_scores() -> dict:
    """Load quality scores for images."""
    global _quality_scores
    if _quality_scores is not None:
        return _quality_scores
    if not QUALITY_SCORES_PATH.exists():
        _quality_scores = {}
        return _quality_scores
    try:
        raw = json.loads(QUALITY_SCORES_PATH.read_text(encoding="utf-8"))
        _quality_scores = raw
    except:
        _quality_scores = {}
    return _quality_scores


def _save_quality_scores() -> None:
    """Save quality scores atomically."""
    if _quality_scores is None:
        return
    tmp = QUALITY_SCORES_PATH.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(_quality_scores, indent=2, ensure_ascii=False), encoding="utf-8")
    shutil.move(str(tmp), str(QUALITY_SCORES_PATH))


def _load_tags() -> dict[str, list[str]]:
    """Load image tags."""
    if not TAGS_PATH.exists():
        return {}
    try:
        return json.loads(TAGS_PATH.read_text(encoding="utf-8"))
    except:
        return {}


def _save_tags(tags: dict) -> None:
    """Save image tags."""
    tmp = TAGS_PATH.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(tags, indent=2, ensure_ascii=False), encoding="utf-8")
    shutil.move(str(tmp), str(TAGS_PATH))


def _find_article(slug: str) -> dict | None:
    """Find article by slug."""
    for a in _load_registry():
        if a.get("slug") == slug:
            return a
    return None


def _get_article_by_id(article_id: str) -> dict | None:
    """Find article by ID."""
    for a in _load_registry():
        if a.get("id") == article_id:
            return a
    return None


# ══════════════════════════════════════════════════════════════
# Quality Scoring System
# ══════════════════════════════════════════════════════════════

def compute_image_quality(image_info: dict, article: dict) -> dict:
    """
    Compute quality score (0-100) for an image.
    
    Returns dict with:
    - total_score: 0-100
    - breakdown: per-component scores
    - tier: "high" (80-100), "medium" (50-79), "low" (0-49)
    """
    weights = QUALITY_WEIGHTS
    breakdown = {}
    total = 0.0
    
    # 1. Relevance score (from image metadata)
    relevance = image_info.get("relevance_score", 0)
    if relevance:
        relevance = min(100, relevance * 100)  # Normalize to 0-100
        breakdown["relevance"] = relevance
        total += relevance * weights["relevance"]
    
    # 2. Resolution quality
    width = image_info.get("width", 0)
    height = image_info.get("height", 0)
    resolution_score = 0
    if width and height:
        if width >= 1920 and height >= 1080:
            resolution_score = 100
        elif width >= 1200 and height >= 600:
            resolution_score = 80
        elif width >= 800 and height >= 400:
            resolution_score = 60
        elif width >= 600 and height >= 300:
            resolution_score = 40
        else:
            resolution_score = 20
    breakdown["resolution"] = resolution_score
    total += resolution_score * weights["resolution"]
    
    # 3. Completeness (metadata)
    metadata_fields = ["source", "title", "description", "copyright", "license", "url"]
    present = sum(1 for f in metadata_fields if image_info.get(f))
    completeness = (present / len(metadata_fields)) * 100
    breakdown["completeness"] = completeness
    total += completeness * weights["completeness"]
    
    # 4. Visual score (file size, format)
    file_size = image_info.get("file_size", 0)
    file_format = image_info.get("format", "").lower()
    visual_score = 50  # Base score
    
    # File size bonus
    if file_size > 500000:  # > 500KB
        visual_score += 20
    elif file_size > 200000:  # > 200KB
        visual_score += 10
    
    # Format bonus
    if file_format in ("webp", "avif"):
        visual_score += 15
    elif file_format == "jpg":
        visual_score += 10
    
    breakdown["visual"] = visual_score
    total += visual_score * weights["visual_score"]
    
    # Normalize to 0-100
    total_score = min(100, max(0, total))
    
    # Determine tier
    if total_score >= 80:
        tier = "high"
    elif total_score >= 50:
        tier = "medium"
    else:
        tier = "low"
    
    return {
        "total_score": round(total_score, 1),
        "breakdown": breakdown,
        "tier": tier,
        "timestamp": datetime.now().isoformat()
    }


def score_all_images(articles: list[dict]) -> dict:
    """Score quality for all images in articles."""
    scores = {}
    for article in articles:
        slug = article.get("slug", "")
        if not slug:
            continue
        
        # Featured image
        fi = article.get("featured_image", "")
        if fi:
            scores[fi] = compute_image_quality(
                {"source": "featured", "url": fi},
                article
            )
        
        # Section images
        for si in article.get("section_images", []):
            iu = si.get("image_url", "")
            if iu:
                scores[iu] = compute_image_quality(
                    {
                        "source": "section",
                        "url": iu,
                        "section_index": si.get("section_index"),
                        "relevance_score": si.get("relevance_score", 0)
                    },
                    article
                )
    
    return scores


# ══════════════════════════════════════════════════════════════
# Image Index & Scanning
# ══════════════════════════════════════════════════════════════

def _scan_images() -> dict[str, dict]:
    """Build index of all images."""
    global _image_index
    if _image_index is not None:
        return _image_index
    
    articles = _load_registry()
    idx: dict[str, dict] = {}
    usage: dict[str, list[dict]] = defaultdict(list)
    
    # Build usage map
    for art in articles:
        slug = art.get("slug", "")
        title = art.get("title", "")
        pillar = art.get("pillar", "aml")
        difficulty = art.get("difficulty", "beginner")
        
        # Featured image
        fi = art.get("featured_image", "")
        if fi:
            rel = fi.lstrip("/")
            usage[rel].append({
                "slug": slug, "title": title,
                "pillar": pillar, "difficulty": difficulty,
                "role": "featured"
            })
        
        # Section images
        for si in art.get("section_images", []):
            iu = si.get("image_url", "")
            if iu:
                rel = iu.lstrip("/")
                usage[rel].append({
                    "slug": slug, "title": title,
                    "pillar": pillar, "difficulty": difficulty,
                    "section_index": si.get("section_index"),
                    "role": "section_image"
                })
    
    # Scan filesystem
    if not IMAGES_DIR.exists():
        _image_index = idx
        return idx
    
    for root, dirs, files in os.walk(str(IMAGES_DIR)):
        for fn in files:
            if fn.startswith("."):
                continue
            fpath = Path(root) / fn
            rel = str(fpath.relative_to(PROJECT_ROOT))
            url = "/" + rel
            
            parts = rel.split(os.sep)
            content_type = ""
            for p in parts:
                if p in ("blog", "learn", "knowledge"):
                    content_type = p
                    break
            
            info = {
                "relative_path": rel,
                "url": url,
                "content_type": content_type,
                "filename": fn,
                "usage": usage.get(rel, []),
                "quality": _quality_scores.get(rel, {}).get("total_score", 0)
            }
            
            # Extract dimensions from filename if available
            if "manifest" in rel:
                info["is_section_image"] = True
            else:
                info["is_section_image"] = False
            
            _image_index[rel] = info
    
    _image_index = idx
    return idx


# ══════════════════════════════════════════════════════════════
# Admin Routes
# ══════════════════════════════════════════════════════════════

@app.route('/')
def index():
    """Admin dashboard."""
    user = _get_user_info()
    articles = _load_registry()
    images = _scan_images()
    quality_scores = _load_quality_scores()
    
    # Dashboard stats
    total_articles = len(articles)
    total_images = len(images)
    
    # Count by pillar
    pillar_counts = defaultdict(int)
    for img in images.values():
        for usage in img.get("usage", []):
            pillar_counts[usage.get("pillar", "unknown")] += 1
    
    # Count by quality tier
    tier_counts = {"high": 0, "medium": 0, "low": 0}
    for img in images.values():
        score = img.get("quality", 0)
        if score >= 80:
            tier_counts["high"] += 1
        elif score >= 50:
            tier_counts["medium"] += 1
        else:
            tier_counts["low"] += 1
    
    # Find articles without images
    articles_without_images = sum(1 for a in articles if not a.get("featured_image") and not a.get("section_images"))
    
    return render_template(
        "admin/index.html",
        user=user,
        total_articles=total_articles,
        total_images=total_images,
        pillar_counts=dict(pillar_counts),
        tier_counts=tier_counts,
        articles_without_images=articles_without_images,
        quality_scores=quality_scores,
        images=images,
        articles=articles
    )


@app.route('/api/images')
def api_images():
    """API: Get all images with filters."""
    _require_auth()
    
    images = _scan_images()
    pillar = request.args.get('pillar')
    difficulty = request.args.get('difficulty')
    quality_tier = request.args.get('quality_tier')
    search = request.args.get('q', '')
    
    filtered = []
    for path, info in images.items():
        # Apply filters
        if pillar and pillar != 'all':
            matches_pillar = any(
                u.get("pillar") == pillar for u in info.get("usage", [])
            )
            if not matches_pillar:
                continue
        
        if difficulty and difficulty != 'all':
            matches_diff = any(
                u.get("difficulty") == difficulty for u in info.get("usage", [])
            )
            if not matches_diff:
                continue
        
        if quality_tier and quality_tier != 'all':
            score = info.get("quality", 0)
            if quality_tier == "high" and score < 80:
                continue
            if quality_tier == "medium" and (score < 50 or score >= 80):
                continue
            if quality_tier == "low" and score >= 50:
                continue
        
        # Search filter
        if search:
            search_lower = search.lower()
            matches_search = (
                search_lower in info.get("filename", "").lower() or
                any(search_lower in u.get("title", "").lower() for u in info.get("usage", []))
            )
            if not matches_search:
                continue
        
        filtered.append(info)
    
    return jsonify(filtered)


@app.route('/api/images/<path:path>')
def api_image_info(path):
    """API: Get info for specific image."""
    _require_auth()
    
    images = _scan_images()
    if path not in images:
        return jsonify({"error": "Image not found"}), 404
    
    info = images[path]
    quality_scores = _load_quality_scores()
    
    # Compute quality if not cached
    if path not in quality_scores:
        for usage in info.get("usage", []):
            article = _find_article(usage.get("slug"))
            if article:
                quality_scores[path] = compute_image_quality(info, article)
                _save_quality_scores()
                break
    
    result = dict(info)
    result["quality"] = quality_scores.get(path, {})
    
    return jsonify(result)


@app.route('/api/articles/<slug>/images', methods=['GET', 'POST'])
def api_article_images(slug):
    """API: Manage images for specific article."""
    _require_auth()
    
    article = _find_article(slug)
    if not article:
        return jsonify({"error": "Article not found"}), 404
    
    if request.method == 'GET':
        # List images for article
        images = []
        for path, info in _scan_images().items():
            for usage in info.get("usage", []):
                if usage.get("slug") == slug:
                    images.append({
                        "path": path,
                        "url": info["url"],
                        "role": usage.get("role"),
                        "quality": info.get("quality", 0)
                    })
        return jsonify(images)
    
    elif request.method == 'POST':
        # Set or remove featured image
        data = request.get_json()
        action = data.get("action")
        image_url = data.get("image_url", "")
        
        if action == "set_featured":
            article["featured_image"] = image_url
            _save_registry()
            return jsonify({"success": True, "featured_image": image_url})
        elif action == "clear_featured":
            article["featured_image"] = ""
            _save_registry()
            return jsonify({"success": True, "featured_image": ""})
        elif action == "set_section":
            section_index = data.get("section_index")
            if section_index is None:
                return jsonify({"error": "section_index required"}), 400
            
            existing = article.get("section_images", [])
            # Remove existing at this index
            existing = [s for s in existing if s.get("section_index") != section_index]
            # Add new
            existing.append({
                "section_index": section_index,
                "image_url": image_url,
                "relevance_score": data.get("relevance_score", 0)
            })
            article["section_images"] = existing
            _save_registry()
            return jsonify({"success": True, "section_images": existing})
        elif action == "clear_section":
            article["section_images"] = []
            _save_registry()
            return jsonify({"success": True, "section_images": []})
        
        return jsonify({"error": "Invalid action"}), 400


@app.route('/api/images/<path:path>/tags', methods=['GET', 'POST', 'DELETE'])
def api_image_tags(path):
    """API: Manage tags for image."""
    _require_auth()
    
    tags_path = PROJECT_ROOT / "registry" / "image-tags.json"
    if not tags_path.exists():
        return jsonify({"error": "Tags file not found"}), 404
    
    tags = json.loads(tags_path.read_text(encoding="utf-8"))
    
    if request.method == 'GET':
        return jsonify(tags.get(path, []))
    
    elif request.method == 'POST':
        data = request.get_json()
        tag = data.get("tag")
        if not tag:
            return jsonify({"error": "tag required"}), 400
        
        if path not in tags:
            tags[path] = []
        if tag not in tags[path]:
            tags[path].append(tag)
            tags_path.write_text(json.dumps(tags, indent=2), encoding="utf-8")
        return jsonify({"success": True, "tags": tags[path]})
    
    elif request.method == 'DELETE':
        data = request.get_json()
        tag = data.get("tag")
        if not tag:
            return jsonify({"error": "tag required"}), 400
        
        if path in tags and tag in tags[path]:
            tags[path].remove(tag)
            tags_path.write_text(json.dumps(tags, indent=2), encoding="utf-8")
        return jsonify({"success": True, "tags": tags.get(path, [])})


# ══════════════════════════════════════════════════════════════
# Batch Operations
# ══════════════════════════════════════════════════════════════

@app.route('/api/batch/fetch-images', methods=['POST'])
def api_batch_fetch_images():
    """API: Fetch images for multiple articles."""
    _require_auth()
    
    data = request.get_json()
    article_ids = data.get("article_ids", [])
    
    results = {"fetched": 0, "failed": 0, "articles": []}
    
    for article_id in article_ids:
        article = _get_article_by_id(article_id)
        if not article:
            results["failed"] += 1
            results["articles"].append({"id": article_id, "error": "Not found"})
            continue
        
        # Fetch images for this article
        try:
            from scripts.fetch_images import fetch_featured_image
            feat = article.get("featured_image", "")
            if not feat:
                fi = fetch_featured_image(article)
                if fi:
                    article["featured_image"] = fi
                    results["fetched"] += 1
            
            # Fetch section images
            sections = parse_sections(article)
            breaks = compute_break_points(sections, article)
            existing = {s["section_index"] for s in article.get("section_images", []) if s.get("image_url")}
            
            for break_point in breaks:
                if break_point["section_index"] not in existing:
                    # Fetch image for this section
                    query = build_section_query(
                        article, break_point["section_index"]
                    )
                    # ... fetch logic would go here
            results["fetched"] += 1
        except Exception as e:
            results["failed"] += 1
            results["articles"].append({
                "id": article_id,
                "error": str(e)
            })
    
    return jsonify(results)


@app.route('/api/batch/clear-images', methods=['POST'])
def api_batch_clear_images():
    """API: Clear images for multiple articles."""
    _require_auth()
    
    data = request.get_json()
    article_ids = data.get("article_ids", [])
    
    cleared = 0
    for article_id in article_ids:
        article = _get_article_by_id(article_id)
        if article:
            article["featured_image"] = ""
            article["section_images"] = []
            _save_registry()
            cleared += 1
    
    return jsonify({"success": True, "cleared": cleared})


# ══════════════════════════════════════════════════════════════
# Login/Logout
# ══════════════════════════════════════════════════════════════

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Admin login."""
    if request.method == 'POST':
        data = request.get_json()
        username = data.get("username", "")
        password = data.get("password", "")
        
        # Simple auth (replace with real auth)
        if username and password:
            session.permanent = True
            session['user_id'] = username
            session['logged_in'] = True
            return jsonify({"success": True, "user": _get_user_info()})
        
        return jsonify({"error": "Invalid credentials"}), 401
    
    return render_template("admin/login.html")


@app.route('/logout')
def logout():
    """Admin logout."""
    session.clear()
    return redirect('/')


# ══════════════════════════════════════════════════════════════
# Error Handlers
# ══════════════════════════════════════════════════════════════

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Not found"}), 404


@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Internal server error"}), 500


# ══════════════════════════════════════════════════════════════
# Initialize
# ══════════════════════════════════════════════════════════════

if __name__ == '__main__':
    # Ensure directories exist
    (PROJECT_ROOT / "registry").mkdir(parents=True, exist_ok=True)
    
    print("Starting AcaciaFund Admin Panel...")
    print("Open http://localhost:5555/admin")
    
    app.run(host='0.0.0.0', port=5555, debug=True)
