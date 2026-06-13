"""AcaciaFund Admin Panel — local Flask web app for image management.

Usage:
    pip install flask
    python app/admin.py
    # Open http://localhost:5555/admin
"""

from __future__ import annotations

import json
import os
import re
import shutil
import sys
import tempfile
import traceback
from pathlib import Path
from io import BytesIO
from typing import Any
from urllib.parse import quote, unquote

import requests

# ── Ensure project root is on sys.path ──
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import flask
from flask import Flask, render_template, request, jsonify, abort, redirect

# ── Import image-fetching machinery ──
from scripts.fetch_images import (
    build_section_query, expand_query, parse_sections,
    compute_break_points, score_result, CURATED_KNOWN,
    ALL_BACKENDS, _GLOBAL_CONTENT_HASHES,
    MAX_IMAGE_WIDTH, MIN_SCORE, NEGATIVE_KEYWORDS,
    PILLAR_KEYWORDS, SECTION_FALLBACK_QUERIES,
    PILLAR_VISUAL_KEYWORDS, SECTION_TYPES,
)

# Build a name→func dict from ALL_BACKENDS
BACKENDS: dict[str, callable] = {}
for name, func in ALL_BACKENDS:
    BACKENDS[name] = func
from core.images.manifest import load_manifest, get_manifest_entry, MANIFEST_PATH

# ── App setup ──
app = Flask(
    __name__,
    template_folder=str(PROJECT_ROOT / "templates"),
    static_folder=str(PROJECT_ROOT / "static"),
    static_url_path="/static",
)
app.config["TEMPLATES_AUTO_RELOAD"] = True

REGISTRY_PATH = PROJECT_ROOT / "registry.json"
IMAGES_DIR = PROJECT_ROOT / "static" / "images" / "generated"

# ── Cached data ──
_registry_data: dict[str, Any] | None = None
_articles: list[dict] | None = None
_image_index: dict[str, dict] | None = None  # path → ImageInfo
_manifest: dict | None = None

# ══════════════════════════════════════════════════════════════
# Data helpers
# ══════════════════════════════════════════════════════════════

def _load_registry() -> list[dict]:
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
    """Write current registry_data back to disk atomically."""
    if _registry_data is None:
        return
    tmp = REGISTRY_PATH.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(_registry_data, indent=2, ensure_ascii=False), encoding="utf-8")
    shutil.move(str(tmp), str(REGISTRY_PATH))


def _load_manifest_cache() -> dict:
    global _manifest
    if _manifest is None:
        _manifest = load_manifest()
    return _manifest


def _save_manifest() -> None:
    if _manifest is None:
        return
    tmp = MANIFEST_PATH.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(_manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    shutil.move(str(tmp), str(MANIFEST_PATH))


def _find_article(slug: str) -> dict | None:
    for a in _load_registry():
        if a.get("slug") == slug:
            return a
    return None


def _article_has_images(article: dict) -> bool:
    si = article.get("section_images", [])
    return any(s.get("image_url") for s in si)


def _article_low_score_sections(article: dict) -> list[dict]:
    """Return sections with relevance_score < 70."""
    low: list[dict] = []
    for s in article.get("section_images", []):
        score = s.get("relevance_score", 0)
        if score and score < 70:
            low.append(s)
    return low


def _article_needs_images(article: dict) -> bool:
    """True if any break-point section is missing an image."""
    sections = parse_sections(article)
    breaks = compute_break_points(sections, article)
    existing = {s["section_index"] for s in article.get("section_images", []) if s.get("image_url")}
    return any(b["section_index"] not in existing for b in breaks)


def _get_section_type_label(idx: int) -> str:
    labels = {
        0: "Overview", 1: "Key Findings", 2: "Applied Scenario",
        3: "Source Analysis", 4: "Domain Breakdown", 5: "Cross-Pillar",
        6: "Methodology",
    }
    return labels.get(idx, f"Section {idx}")


# ══════════════════════════════════════════════════════════════
# Image scanner
# ══════════════════════════════════════════════════════════════

def _scan_images() -> dict[str, dict]:
    """Build and return {relative_path: info} for all generated images."""
    global _image_index
    if _image_index is not None:
        return _image_index

    articles = _load_registry()
    idx: dict[str, dict] = {}

    # Build usage map: path → list of (slug, title, section_index, role)
    usage: dict[str, list[dict]] = {}
    for art in articles:
        slug = art.get("slug", "")
        title = art.get("title", "")
        fi = art.get("featured_image", "")
        if fi:
            rel = fi.lstrip("/")
            usage.setdefault(rel, []).append({"slug": slug, "title": title, "section_index": None, "role": "featured"})
        for si in art.get("section_images", []):
            iu = si.get("image_url", "")
            if iu:
                rel = iu.lstrip("/")
                usage.setdefault(rel, []).append({"slug": slug, "title": title, "section_index": si.get("section_index"), "role": "section_image"})

    if not IMAGES_DIR.exists():
        _image_index = idx
        return idx

    for root, _dirs, files in os.walk(str(IMAGES_DIR)):
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

            slug = None
            section_index = None
            is_manifest = False
            is_card = False

            stem = fpath.stem
            m = re.match(r'^manifest_(.+)_s(\d+)$', stem)
            if m:
                is_manifest = True
                slug = m.group(1)
                section_index = int(m.group(2))
            else:
                m = re.match(r'^(.+)_s(\d+)$', stem)
                if m:
                    slug = m.group(1)
                    section_index = int(m.group(2))
                elif stem.endswith("_card"):
                    is_card = True
                    slug = stem.replace("_card", "")
                else:
                    slug = stem

            fmt = fn.rsplit(".", 1)[-1].lower() if "." in fn else ""

            file_size = fpath.stat().st_size

            width = height = 0
            try:
                if fmt not in ("svg",):
                    from PIL import Image
                    with Image.open(fpath) as img:
                        width, height = img.size
            except Exception:
                pass

            source: str | None = None
            for art in articles:
                for si in art.get("section_images", []):
                    if si.get("image_url", "").lstrip("/") == rel:
                        source = si.get("source_api", None)
                        break
                if source:
                    break
            if source is None and is_manifest:
                source = "manifest"
            if source is None and fmt == "svg":
                source = "svg_fallback"

            idx[rel] = {
                "path": rel,
                "url": url,
                "filename": fn,
                "content_type": content_type,
                "slug": slug or "",
                "section_index": section_index,
                "is_manifest": is_manifest,
                "is_card": is_card,
                "format": fmt,
                "file_size": file_size,
                "width": width,
                "height": height,
                "source": source,
                "used_by": usage.get(rel, []),
            }

    _image_index = idx
    return idx


def _invalidate_cache() -> None:
    global _articles, _registry_data, _image_index, _manifest
    _articles = None
    _registry_data = None
    _image_index = None
    _manifest = None


# ══════════════════════════════════════════════════════════════
# Context processor (injects sidebar stats into all templates)
# ══════════════════════════════════════════════════════════════

@app.context_processor
def _inject_global_stats():
    images = _scan_images()
    articles = _load_registry()
    return {
        "image_count": len(images),
        "article_count": len(articles),
    }


# ══════════════════════════════════════════════════════════════
# Page routes
# ══════════════════════════════════════════════════════════════

@app.route("/admin/")
def dashboard():
    articles = _load_registry()
    images = _scan_images()

    total_articles = len(articles)
    with_images = sum(1 for a in articles if _article_has_images(a))
    without_images = total_articles - with_images

    # Low-score sections
    low_score_sections: list[dict] = []
    for a in articles:
        for s in a.get("section_images", []):
            score = s.get("relevance_score", 0)
            if score and score < 70:
                low_score_sections.append({
                    "slug": a.get("slug"),
                    "title": a.get("title"),
                    "section_index": s.get("section_index"),
                    "heading": s.get("heading", ""),
                    "score": score,
                    "source": s.get("source_api", ""),
                })
    low_score_sections.sort(key=lambda x: x["score"])

    # SVG fallback count
    svg_fallbacks = sum(
        1 for s in low_score_sections if s["source"] == "svg_fallback"
    )

    # Orphan images
    orphan_images = sum(1 for img in images.values() if not img["used_by"])

    # By content type
    by_type: dict[str, dict] = {}
    for a in articles:
        ct = a.get("content_type", "unknown")
        if ct not in by_type:
            by_type[ct] = {"type": ct, "total": 0, "with_images": 0, "without_images": 0}
        by_type[ct]["total"] += 1
        if _article_has_images(a):
            by_type[ct]["with_images"] += 1
        else:
            by_type[ct]["without_images"] += 1

    # By source
    source_counts: dict[str, int] = {}
    for a in articles:
        for s in a.get("section_images", []):
            src = s.get("source_api", "unknown")
            source_counts[src] = source_counts.get(src, 0) + 1

    stats = {
        "total_images": len(images),
        "total_articles": total_articles,
        "with_images": with_images,
        "without_images": without_images,
        "with_images_pct": round(with_images / total_articles * 100, 1) if total_articles else 0,
        "low_score": len(low_score_sections),
        "orphan_images": orphan_images,
        "svg_fallbacks": svg_fallbacks,
        "manifest_entries": len(_load_manifest_cache()),
        "by_type": list(by_type.values()),
        "by_source": sorted(source_counts.items(), key=lambda x: -x[1]),
        "low_score_sections": low_score_sections[:50],
    }

    return render_template("admin/dashboard.html", stats=stats, active_page="dashboard")


@app.route("/admin/gallery")
def gallery():
    images = _scan_images()
    orphan = sum(1 for img in images.values() if not img["used_by"])
    return render_template("admin/gallery.html", active_page="gallery",
                           stats={"total_images": len(images), "orphan_images": orphan})


@app.route("/admin/articles")
def article_list():
    articles = _load_registry()
    pillars = sorted(set(a.get("pillar", "") for a in articles if a.get("pillar")))
    needs_images = sum(1 for a in articles if _article_needs_images(a))

    rows = []
    for a in articles:
        sections = parse_sections(a)
        breaks = compute_break_points(sections, a)
        section_images = a.get("section_images", [])
        existing_count = sum(1 for s in section_images if s.get("image_url"))
        has_low = len(_article_low_score_sections(a)) > 0

        rows.append({
            "slug": a.get("slug"),
            "title": a.get("title"),
            "content_type": a.get("content_type"),
            "pillar": a.get("pillar"),
            "num_sections": len(breaks),
            "section_images_count": existing_count,
            "featured_image": a.get("featured_image"),
            "needs_images": _article_needs_images(a),
            "low_score": has_low and not _article_needs_images(a),
        })

    return render_template("admin/article_list.html", active_page="articles",
                           articles=rows, pillars=pillars, needs_images=needs_images)


@app.route("/admin/article/<path:slug>")
def article_detail(slug):
    article = _find_article(slug)
    if not article:
        abort(404, f"Article not found: {slug}")

    sections = parse_sections(article)
    breaks = compute_break_points(sections, article)

    # Build section list with image info
    section_data: list[dict] = []
    existing_map = {s["section_index"]: s for s in article.get("section_images", []) if s.get("image_url")}

    for s in sections:
        idx = s["section_index"]
        if any(b["section_index"] == idx for b in breaks):
            img = existing_map.get(idx)
            query = build_section_query(s, article)
            section_data.append({
                "section_index": idx,
                "heading": s["heading"],
                "section_type": _get_section_type_label(idx),
                "word_count": s["word_count"],
                "entities": s.get("entities", []),
                "query": query,
                "image": img,
            })

    return render_template("admin/article_detail.html", active_page="articles",
                           article=article, sections=section_data)


@app.route("/admin/image/<path:image_path>")
def image_detail(image_path):
    images = _scan_images()
    rel = image_path.lstrip("/")
    img = images.get(rel)
    if not img:
        abort(404, f"Image not found: {image_path}")

    # Enrich used_by entries with score and source from registry
    for a in _load_registry():
        for si in a.get("section_images", []):
            if si.get("image_url", "").lstrip("/") == rel:
                if not img["source"]:
                    img["source"] = si.get("source_api", None)
                # Find matching used_by entry and enrich it
                for use in img["used_by"]:
                    if use["slug"] == a.get("slug") and use.get("section_index") == si.get("section_index"):
                        use["relevance_score"] = si.get("relevance_score")
                        use["source_api"] = si.get("source_api")
                        break

    return render_template("admin/image_detail.html", active_page="gallery", img=img)


@app.route("/admin/manifest")
def manifest_editor():
    manifest = _load_manifest_cache()
    entries = []
    for key, entry in manifest.items():
        for sec in entry.get("sections", []):
            slug = key.split("/", 1)[-1] if "/" in key else key
            entries.append({
                "slug": slug,
                "section_index": sec.get("section_index"),
                "image_url": sec.get("image_url"),
            })
    entries.sort(key=lambda x: (x["slug"], x["section_index"]))
    return render_template("admin/manifest.html", active_page="manifest",
                           manifest=entries)


@app.route("/admin/curated-test")
def curated_tester():
    curated_list = sorted(CURATED_KNOWN.items(), key=lambda x: x[0])
    return render_template("admin/curated_tester.html", active_page="curated",
                           curated_entries=curated_list,
                           curated_count=len(curated_list))


# ══════════════════════════════════════════════════════════════
# Tier 1 — Pipeline Observability pages
# ══════════════════════════════════════════════════════════════

PIPELINE_RUNS_PATH = PROJECT_ROOT / "registry" / "image-pipeline-runs.json"


def _load_pipeline_runs() -> list[dict]:
    if not PIPELINE_RUNS_PATH.exists():
        return []
    try:
        return json.loads(PIPELINE_RUNS_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []


def _load_dlq_entries() -> list[dict]:
    dlq_dir = PROJECT_ROOT / ".dlq"
    if not dlq_dir.exists():
        return []
    entries = []
    for f in sorted(dlq_dir.glob("*.json"), reverse=True)[:100]:
        try:
            entries.append(json.loads(f.read_text(encoding="utf-8")))
        except Exception:
            pass
    return entries


@app.route("/admin/pipeline")
def pipeline():
    runs = _load_pipeline_runs()
    dlq = _load_dlq_entries()
    return render_template("admin/pipeline.html", active_page="pipeline",
                           runs=runs, dlq=dlq, dlq_count=len(dlq))


@app.route("/admin/quality")
def quality():
    articles = _load_registry()
    images = _scan_images()

    # Collect all scores
    all_scores: list[float] = []
    scores_by_source: dict[str, list[float]] = {}
    scores_by_section: dict[str, list[float]] = {}
    scores_by_type: dict[str, list[float]] = {}

    for a in articles:
        ct = a.get("content_type", "unknown")
        for s in a.get("section_images", []):
            score = s.get("relevance_score", 0)
            if score:
                all_scores.append(score)
                src = s.get("source_api", "unknown")
                scores_by_source.setdefault(src, []).append(score)
                stype = SECTION_TYPES.get(s.get("section_index", 0), "unknown")
                scores_by_section.setdefault(stype, []).append(score)
                scores_by_type.setdefault(ct, []).append(score)

    # Histogram buckets
    buckets = [0] * 10
    for s in all_scores:
        b = min(int(s / 10), 9)
        buckets[b] += 1

    # Per-source averages
    source_avgs = {src: round(sum(v) / len(v), 1) for src, v in sorted(scores_by_source.items(), key=lambda x: -sum(x[1]) / len(x[1]))}
    section_avgs = {stype: round(sum(v) / len(v), 1) for stype, v in sorted(scores_by_section.items(), key=lambda x: -sum(x[1]) / len(x[1]))}
    type_avgs = {ct: round(sum(v) / len(v), 1) for ct, v in sorted(scores_by_type.items(), key=lambda x: -sum(x[1]) / len(x[1]))}

    stats = {
        "total_scores": len(all_scores),
        "avg_score": round(sum(all_scores) / len(all_scores), 1) if all_scores else 0,
        "median_score": round(sorted(all_scores)[len(all_scores) // 2], 1) if all_scores else 0,
        "above_70": sum(1 for s in all_scores if s >= 70),
        "below_40": sum(1 for s in all_scores if s < 40),
        "buckets": buckets,
        "source_avgs": source_avgs,
        "section_avgs": section_avgs,
        "type_avgs": type_avgs,
    }

    return render_template("admin/quality.html", active_page="quality", stats=stats)


@app.route("/admin/coverage")
def coverage():
    articles = _load_registry()

    # Pillar × section_type heatmap
    heatmap: dict[str, dict[str, dict]] = {}  # pillar → section_type → {filled, total}
    coverage_by_type: dict[str, dict] = {}
    coverage_by_pillar: dict[str, dict] = {}

    for a in articles:
        pillar = a.get("pillar", "unknown")
        ct = a.get("content_type", "unknown")
        if pillar not in heatmap:
            heatmap[pillar] = {}
        if pillar not in coverage_by_pillar:
            coverage_by_pillar[pillar] = {"filled": 0, "total": 0}
        if ct not in coverage_by_type:
            coverage_by_type[ct] = {"filled": 0, "total": 0}

        sections = parse_sections(a)
        breaks = compute_break_points(sections, a)
        existing = {s["section_index"] for s in a.get("section_images", []) if s.get("image_url")}

        for s in sections:
            idx = s["section_index"]
            if not any(b["section_index"] == idx for b in breaks):
                continue
            stype = SECTION_TYPES.get(idx, f"section_{idx}")
            if stype not in heatmap[pillar]:
                heatmap[pillar][stype] = {"filled": 0, "total": 0}
            heatmap[pillar][stype]["total"] += 1
            coverage_by_pillar[pillar]["total"] += 1
            coverage_by_type[ct]["total"] += 1
            if idx in existing:
                heatmap[pillar][stype]["filled"] += 1
                coverage_by_pillar[pillar]["filled"] += 1
                coverage_by_type[ct]["filled"] += 1

    # Calculate percentages
    heatmap_pct: dict[str, dict[str, float]] = {}
    for pillar, sections in heatmap.items():
        heatmap_pct[pillar] = {}
        for stype, counts in sections.items():
            pct = round(counts["filled"] / max(counts["total"], 1) * 100, 0)
            heatmap_pct[pillar][stype] = pct

    return render_template("admin/coverage.html", active_page="coverage",
                           heatmap=heatmap_pct,
                           heatmap_raw=heatmap,
                           by_pillar=coverage_by_pillar,
                           by_type=coverage_by_type,
                           section_labels=["Overview", "Key Findings", "Applied Scenario",
                                           "Source Analysis", "Domain Breakdown", "Cross-Pillar",
                                           "Methodology"])


@app.route("/admin/sources")
def sources():
    from core.sources import registry
    source_list = registry.source_list()
    summaries = registry.summaries()
    # Merge source config with health summaries
    rows = []
    for s in source_list:
        summary = next((sm for sm in summaries if sm["name"] == s["name"]), {})
        rows.append({**s, **summary})
    return render_template("admin/sources.html", active_page="sources", sources=rows)


# ══════════════════════════════════════════════════════════════
# API — Images
# ══════════════════════════════════════════════════════════════

@app.route("/admin/api/images")
def api_images():
    images = _scan_images()
    q = request.args.get("q", "").strip().lower()
    img_type = request.args.get("type", "").strip().lower()
    source = request.args.get("source", "").strip().lower()
    section_str = request.args.get("section", "").strip()
    status = request.args.get("status", "").strip().lower()

    results = list(images.values())

    if q:
        results = [r for r in results if q in r["filename"].lower() or q in r["slug"].lower()]
    if img_type:
        results = [r for r in results if r["content_type"] == img_type]
    if source:
        if source == "svgs":
            results = [r for r in results if r["format"] == "svg"]
        else:
            results = [r for r in results if (r.get("source") or "") == source]
    if section_str:
        try:
            sec = int(section_str)
            results = [r for r in results if r["section_index"] == sec]
        except ValueError:
            pass
    if status == "used":
        results = [r for r in results if r["used_by"]]
    elif status == "orphan":
        results = [r for r in results if not r["used_by"]]

    # Sort: used first, then by file size desc
    results.sort(key=lambda r: (1 if r["used_by"] else 0, r.get("file_size", 0)), reverse=True)

    return jsonify({"images": results, "total": len(results)})


@app.route("/admin/api/stats")
def api_stats():
    articles = _load_registry()
    images = _scan_images()
    return jsonify({
        "total_images": len(images),
        "total_articles": len(articles),
    })


# ══════════════════════════════════════════════════════════════
# API — Articles
# ══════════════════════════════════════════════════════════════

@app.route("/admin/api/articles")
def api_articles():
    articles = _load_registry()
    rows = []
    for a in articles:
        rows.append({
            "slug": a.get("slug"),
            "title": a.get("title"),
            "pillar": a.get("pillar"),
            "content_type": a.get("content_type"),
            "needs_images": _article_needs_images(a),
            "featured_image": a.get("featured_image"),
        })
    return jsonify({"articles": rows})


@app.route("/admin/api/article/<path:slug>")
def api_article(slug):
    a = _find_article(slug)
    if not a:
        return jsonify({"error": "Not found"}), 404
    return jsonify({"article": a})


# ══════════════════════════════════════════════════════════════
# API — Image assignment mutations
# ══════════════════════════════════════════════════════════════

def _set_section_image(slug: str, section_index: int, image_url: str,
                       source: str = "admin", score: float = 100.0) -> dict:
    """Assign an image_url to a specific section of an article. Returns updated section entry."""
    article = _find_article(slug)
    if not article:
        raise ValueError(f"Article not found: {slug}")

    # Ensure section_images exists
    if "section_images" not in article:
        article["section_images"] = []

    # Build the entry
    entry = {
        "section_index": section_index,
        "image_url": image_url,
        "image_credit": f"Assigned via admin panel ({source})",
        "image_alt": "",
        "relevance_score": score,
        "source_api": source,
        "width": 0,
        "height": 0,
    }

    # Try to get dimensions
    local_path = PROJECT_ROOT / image_url.lstrip("/")
    if local_path.exists():
        try:
            from PIL import Image
            with Image.open(local_path) as img:
                entry["width"], entry["height"] = img.size
        except Exception:
            pass

    # Replace existing entry for this section, or append
    found = False
    for i, existing in enumerate(article["section_images"]):
        if existing.get("section_index") == section_index:
            article["section_images"][i] = entry
            found = True
            break
    if not found:
        article["section_images"].append(entry)

    _save_registry()
    return entry


def _remove_section_image(slug: str, section_index: int) -> None:
    article = _find_article(slug)
    if not article:
        raise ValueError(f"Article not found: {slug}")
    article["section_images"] = [
        s for s in article.get("section_images", [])
        if s.get("section_index") != section_index
    ]
    _save_registry()


@app.route("/admin/api/article/<path:slug>/assign-section-image", methods=["POST"])
def api_assign_section_image(slug):
    data = request.get_json(force=True)
    section_index = data.get("section_index")
    if section_index is None:
        return jsonify({"error": "section_index required"}), 400

    image_path = data.get("image_path")
    external_url = data.get("external_url")

    if image_path:
        # Assign from existing image in gallery
        url = "/" + image_path.lstrip("/")
        entry = _set_section_image(slug, section_index, url, source="admin_pick", score=100.0)
        return jsonify({"success": True, "entry": entry})
    elif external_url:
        # Smart suggest: download external image then assign
        source = data.get("source", "admin_suggest")
        score = data.get("score", 85.0)
        try:
            result = _download_and_save(slug, section_index, external_url, source)
            entry = _set_section_image(slug, section_index, result["url"],
                                       source=source, score=score)
            entry["width"] = result.get("width", 0)
            entry["height"] = result.get("height", 0)
            return jsonify({"success": True, "entry": entry})
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    else:
        return jsonify({"error": "image_path or external_url required"}), 400


@app.route("/admin/api/article/<path:slug>/remove-section-image", methods=["POST"])
def api_remove_section_image(slug):
    data = request.get_json(force=True)
    section_index = data.get("section_index")
    if section_index is None:
        return jsonify({"error": "section_index required"}), 400
    _remove_section_image(slug, section_index)
    return jsonify({"success": True})


@app.route("/admin/api/article/<path:slug>/set-featured", methods=["POST"])
def api_set_featured(slug):
    article = _find_article(slug)
    if not article:
        return jsonify({"error": "Not found"}), 404
    data = request.get_json(force=True)
    image_path = data.get("image_path", "")
    url = "/" + image_path.lstrip("/")
    article["featured_image"] = url
    _save_registry()
    return jsonify({"success": True, "featured_image": url})


@app.route("/admin/api/article/<path:slug>/remove-featured", methods=["POST"])
def api_remove_featured(slug):
    article = _find_article(slug)
    if not article:
        return jsonify({"error": "Not found"}), 404
    article.pop("featured_image", None)
    _save_registry()
    return jsonify({"success": True})


@app.route("/admin/api/article/<path:slug>/re-fetch-section", methods=["POST"])
def api_refetch_section(slug):
    """Re-run the fetch pipeline for a single section."""
    from scripts.fetch_images import fetch_section_images
    article = _find_article(slug)
    if not article:
        return jsonify({"error": "Not found"}), 404
    data = request.get_json(force=True)
    section_index = data.get("section_index")
    if section_index is None:
        return jsonify({"error": "section_index required"}), 400

    # Run the fetch pipeline for this article
    sections = compute_break_points(parse_sections(article), article)
    target = next((s for s in sections if s["section_index"] == section_index), None)
    if not target:
        return jsonify({"error": f"Section {section_index} not in break points"}), 400

    from scripts.fetch_images import fetch_section_images, download_image

    try:
        result = fetch_section_images(article)
        if result:
            _save_registry()
            return jsonify({"success": True, "section_images": result})
        return jsonify({"error": "No images found"}), 404
    except Exception as e:
        return jsonify({"error": str(e), "traceback": traceback.format_exc()}), 500


@app.route("/admin/api/article/<path:slug>/re-fetch-all", methods=["POST"])
def api_refetch_all(slug):
    """Re-fetch section images for ALL sections of an article."""
    article = _find_article(slug)
    if not article:
        return jsonify({"error": "Not found"}), 404
    from scripts.fetch_images import fetch_section_images
    try:
        result = fetch_section_images(article)
        _save_registry()
        return jsonify({"success": True, "message": f"Fetched {len(result)} section images"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ══════════════════════════════════════════════════════════════
# API — Smart Suggest
# ══════════════════════════════════════════════════════════════

@app.route("/admin/api/article/<path:slug>/suggest", methods=["POST"])
def api_suggest(slug):
    """Search backends for candidate images for a section, return top results."""
    article = _find_article(slug)
    if not article:
        return jsonify({"error": "Not found"}), 404
    data = request.get_json(force=True)
    section_index = data.get("section_index")
    if section_index is None:
        return jsonify({"error": "section_index required"}), 400

    # Build sections and find the target
    parsed = parse_sections(article)
    target = next((s for s in parsed if s["section_index"] == section_index), None)
    if not target:
        return jsonify({"error": f"Section {section_index} not found"}), 400

    # Build the query using existing pipeline
    query = build_section_query(target, article)
    query_terms = set(query.split())

    # Search backends
    candidates: list[dict] = []
    used_urls: set[str] = set()

    for backend_name, backend_fn in BACKENDS.items():
        try:
            results = backend_fn(query)
            for r in (results or []):
                url = r.get("url", "")
                if not url or url in used_urls:
                    continue
                used_urls.add(url)
                score = score_result(
                    r, query_terms,
                    backend=backend_name,
                    width=r.get("width", 0),
                    height=r.get("height", 0),
                )
                if score >= MIN_SCORE:
                    candidates.append({
                        "url": url,
                        "thumbnail": r.get("thumbnail") or r.get("url", ""),
                        "title": r.get("title", ""),
                        "source": backend_name,
                        "score": round(score, 1),
                        "width": r.get("width", 0),
                        "height": r.get("height", 0),
                    })
        except Exception:
            continue

    # Sort by score desc, dedup by URL, return top 10
    seen_urls: set[str] = set()
    unique: list[dict] = []
    for c in sorted(candidates, key=lambda x: -x["score"]):
        if c["url"] not in seen_urls:
            seen_urls.add(c["url"])
            unique.append(c)
            if len(unique) >= 10:
                break

    return jsonify({"candidates": unique, "query": query})


# ══════════════════════════════════════════════════════════════
# API — Manifest
# ══════════════════════════════════════════════════════════════

@app.route("/admin/api/manifest", methods=["GET"])
def api_get_manifest():
    m = _load_manifest_cache()
    entries = []
    for key, entry in m.items():
        for sec in entry.get("sections", []):
            entries.append({
                "key": key,
                "slug": key.split("/", 1)[-1] if "/" in key else key,
                "section_index": sec.get("section_index"),
                "image_url": sec.get("image_url"),
                "image_credit": sec.get("image_credit", ""),
                "note": entry.get("note", ""),
            })
    return jsonify({"manifest": entries})


@app.route("/admin/api/manifest", methods=["POST"])
def api_add_manifest():
    data = request.get_json(force=True)
    slug = data.get("slug", "").strip()
    section_index = data.get("section_index")
    image_url = data.get("image_url", "").strip()

    if not slug or section_index is None or not image_url:
        return jsonify({"error": "slug, section_index, image_url required"}), 400

    # Determine content type from slug
    content_type = "blog"
    if slug.startswith("learn/"):
        content_type = "learn"
        slug = slug[6:]
    elif slug.startswith("knowledge/"):
        content_type = "knowledge"
        slug = slug[10:]

    key = f"{content_type}/{slug}"
    m = _load_manifest_cache()
    if key not in m:
        m[key] = {"note": "", "sections": []}

    # Replace or append section
    found = False
    for i, sec in enumerate(m[key]["sections"]):
        if sec.get("section_index") == section_index:
            m[key]["sections"][i] = {"section_index": section_index, "image_url": image_url}
            found = True
            break
    if not found:
        m[key]["sections"].append({"section_index": section_index, "image_url": image_url})

    _save_manifest()
    _manifest = m
    return jsonify({"success": True, "key": key})


@app.route("/admin/api/manifest/<path:entry_key>", methods=["DELETE"])
def api_delete_manifest(entry_key):
    # entry_key is "{slug}_{section_index}"
    # Find and remove the entry
    m = _load_manifest_cache()
    for key in list(m.keys()):
        slug = key.split("/", 1)[-1] if "/" in key else key
        entry_slug = entry_key.rsplit("_", 1)[0]
        if slug == entry_slug:
            del m[key]
            _save_manifest()
            _manifest = m
            return jsonify({"success": True, "removed": key})
    return jsonify({"error": "Not found"}), 404


# ══════════════════════════════════════════════════════════════
# API — Curated Tester
# ══════════════════════════════════════════════════════════════

@app.route("/admin/api/curated-test", methods=["POST"])
def api_curated_test():
    data = request.get_json(force=True)
    slug = (data.get("slug") or "").strip()
    raw_text = (data.get("raw_text") or "").strip()
    show_all = data.get("show_all") == "1"

    if slug:
        article = _find_article(slug)
        if not article:
            return jsonify({"error": f"Article not found: {slug}"}), 404
        title = article.get("title", "")
        tags = " ".join(article.get("tags", []))
        desc = article.get("description", "")
        body = article.get("body_html", "")
        haystack = (title + " " + tags + " " + desc).lower()
        body_text = re.sub(r'<[^>]+>', '', body).lower()
    elif raw_text:
        parts = [p.strip() for p in raw_text.split(",")]
        haystack = parts[0].lower() if len(parts) > 0 else ""
        body_text = parts[3].lower() if len(parts) > 3 else haystack
        if len(parts) > 1:
            haystack += " " + parts[1].lower()
        if len(parts) > 2:
            haystack += " " + parts[2].lower()
    else:
        return jsonify({"error": "Provide slug or raw_text"}), 400

    matches = []
    for phrase, filename in CURATED_KNOWN.items():
        keywords = phrase.split()
        in_haystack = all(kw in haystack for kw in keywords)
        in_body = all(kw in body_text for kw in keywords)
        if in_haystack or in_body:
            matched_in = "haystack" if in_haystack else ""
            if in_body:
                matched_in += (" + " if matched_in else "") + "body"
            matches.append({"phrase": phrase, "filename": filename, "matched_in": matched_in})

    if show_all:
        non_matches = [
            {"phrase": p, "filename": f, "matched_in": ""}
            for p, f in CURATED_KNOWN.items()
            if not any(m["phrase"] == p for m in matches)
        ]
        return jsonify({"matches": matches, "non_matches": non_matches, "total": len(CURATED_KNOWN)})

    return jsonify({"matches": matches, "total": len(CURATED_KNOWN)})


# ══════════════════════════════════════════════════════════════
# Tier 1 — API: Pipeline / Quality / Coverage
# ══════════════════════════════════════════════════════════════

@app.route("/admin/api/pipeline/runs")
def api_pipeline_runs():
    runs = _load_pipeline_runs()
    return jsonify({"runs": runs, "total": len(runs)})


@app.route("/admin/api/pipeline/dlq")
def api_pipeline_dlq():
    dlq = _load_dlq_entries()
    return jsonify({"entries": dlq, "total": len(dlq)})


@app.route("/admin/api/quality/distribution")
def api_quality_distribution():
    articles = _load_registry()
    all_scores = []
    by_source: dict[str, list[float]] = {}
    by_section: dict[str, list[float]] = {}
    by_type: dict[str, list[float]] = {}

    for a in articles:
        ct = a.get("content_type", "unknown")
        for s in a.get("section_images", []):
            score = s.get("relevance_score", 0)
            if score:
                all_scores.append(score)
                src = s.get("source_api", "unknown")
                by_source.setdefault(src, []).append(score)
                stype = SECTION_TYPES.get(s.get("section_index", 0), "unknown")
                by_section.setdefault(stype, []).append(score)
                by_type.setdefault(ct, []).append(score)

    buckets = [0] * 10
    for s in all_scores:
        buckets[min(int(s / 10), 9)] += 1

    return jsonify({
        "total": len(all_scores),
        "avg": round(sum(all_scores) / len(all_scores), 1) if all_scores else 0,
        "median": round(sorted(all_scores)[len(all_scores) // 2], 1) if all_scores else 0,
        "above_70": sum(1 for s in all_scores if s >= 70),
        "below_40": sum(1 for s in all_scores if s < 40),
        "buckets": buckets,
        "by_source": {k: {"avg": round(sum(v) / len(v), 1), "count": len(v)} for k, v in sorted(by_source.items(), key=lambda x: -len(x[1]))},
        "by_section": {k: {"avg": round(sum(v) / len(v), 1), "count": len(v)} for k, v in sorted(by_section.items(), key=lambda x: -len(x[1]))},
        "by_type": {k: {"avg": round(sum(v) / len(v), 1), "count": len(v)} for k, v in sorted(by_type.items(), key=lambda x: -len(x[1]))},
    })


@app.route("/admin/api/coverage/heatmap")
def api_coverage_heatmap():
    articles = _load_registry()
    heatmap: dict[str, dict[str, dict]] = {}

    for a in articles:
        pillar = a.get("pillar", "unknown")
        if pillar not in heatmap:
            heatmap[pillar] = {}
        sections = parse_sections(a)
        breaks = compute_break_points(sections, a)
        existing = {s["section_index"] for s in a.get("section_images", []) if s.get("image_url")}
        for s in sections:
            idx = s["section_index"]
            if not any(b["section_index"] == idx for b in breaks):
                continue
            stype = SECTION_TYPES.get(idx, f"section_{idx}")
            if stype not in heatmap[pillar]:
                heatmap[pillar][stype] = {"filled": 0, "total": 0}
            heatmap[pillar][stype]["total"] += 1
            if idx in existing:
                heatmap[pillar][stype]["filled"] += 1

    return jsonify({"heatmap": heatmap})


@app.route("/admin/api/coverage/summary")
def api_coverage_summary():
    articles = _load_registry()
    by_pillar: dict[str, dict] = {}
    by_type: dict[str, dict] = {}

    for a in articles:
        pillar = a.get("pillar", "unknown")
        ct = a.get("content_type", "unknown")
        if pillar not in by_pillar:
            by_pillar[pillar] = {"filled": 0, "total": 0}
        if ct not in by_type:
            by_type[ct] = {"filled": 0, "total": 0}
        sections = parse_sections(a)
        breaks = compute_break_points(sections, a)
        existing = {s["section_index"] for s in a.get("section_images", []) if s.get("image_url")}
        for s in sections:
            idx = s["section_index"]
            if not any(b["section_index"] == idx for b in breaks):
                continue
            by_pillar[pillar]["total"] += 1
            by_type[ct]["total"] += 1
            if idx in existing:
                by_pillar[pillar]["filled"] += 1
                by_type[ct]["filled"] += 1

    return jsonify({
        "by_pillar": {k: {"filled": v["filled"], "total": v["total"], "pct": round(v["filled"] / max(v["total"], 1) * 100, 1)} for k, v in by_pillar.items()},
        "by_type": {k: {"filled": v["filled"], "total": v["total"], "pct": round(v["filled"] / max(v["total"], 1) * 100, 1)} for k, v in by_type.items()},
    })


# ══════════════════════════════════════════════════════════════
# API — Sources
# ══════════════════════════════════════════════════════════════

@app.route("/admin/api/sources")
def api_sources():
    from core.sources import registry
    source_list = registry.source_list()
    summaries = registry.summaries()
    rows = []
    for s in source_list:
        summary = next((sm for sm in summaries if sm["name"] == s["name"]), {})
        rows.append({**s, **summary})
    return jsonify({"sources": rows})


@app.route("/admin/api/sources/<name>/health")
def api_source_health(name):
    from core.sources.base import load_health_records
    records = load_health_records().get(name, [])
    return jsonify({"name": name, "records": records[-50:], "total": len(records)})


@app.route("/admin/api/sources/<name>/refresh", methods=["POST"])
def api_source_refresh(name):
    from core.sources import registry
    fetcher = registry.get(name)
    if not fetcher:
        return jsonify({"error": f"Source not found: {name}"}), 404
    import time
    t0 = time.time()
    result = fetcher.fetch(since_hours=24)
    duration = round(time.time() - t0, 1)
    return jsonify({
        "success": result.success,
        "item_count": result.item_count,
        "latency_ms": result.latency_ms,
        "duration_s": duration,
        "error": result.error,
    })


# ══════════════════════════════════════════════════════════════
# Helper: download external image and save locally
# ══════════════════════════════════════════════════════════════

def _download_and_save(slug: str, section_index: int, url: str, source: str) -> dict:
    """Download an external image, save to generated directory, return local info."""
    resp = requests.get(url, timeout=30, stream=True)
    resp.raise_for_status()

    content = resp.content
    if len(content) > 10 * 1024 * 1024:
        raise ValueError("Image too large (>10MB)")

    # Determine format
    ct = resp.headers.get("content-type", "")
    if "jpeg" in ct or "jpg" in ct:
        ext = ".jpg"
    elif "png" in ct:
        ext = ".png"
    elif "gif" in ct:
        ext = ".gif"
    elif "webp" in ct:
        ext = ".webp"
    else:
        ext = ".jpg"

    # Save to blog/ directory by default
    rel_dir = f"static/images/generated/blog"
    out_dir = PROJECT_ROOT / rel_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    fname = f"{slug}_s{section_index}{ext}"
    out_path = out_dir / fname

    out_path.write_bytes(content)

    # Try to convert to WebP
    try:
        from PIL import Image
        img = Image.open(BytesIO(content))
        if img.mode == "RGBA":
            img = img.convert("RGB")
        if img.width > MAX_IMAGE_WIDTH:
            ratio = MAX_IMAGE_WIDTH / img.width
            img = img.resize((MAX_IMAGE_WIDTH, int(img.height * ratio)), Image.LANCZOS)
        webp_path = out_path.with_suffix(".webp")
        img.save(str(webp_path), format="WEBP", quality=85, method=6)
        # Remove the original
        if webp_path != out_path:
            out_path.unlink(missing_ok=True)
            out_path = webp_path
            fname = f"{slug}_s{section_index}.webp"
    except Exception:
        pass

    rel_path = f"{rel_dir}/{fname}"
    url_path = "/" + rel_path
    width = height = 0
    try:
        from PIL import Image
        with Image.open(out_path) as img:
            width, height = img.size
    except Exception:
        pass

    return {"url": url_path, "path": rel_path, "width": width, "height": height}


# ══════════════════════════════════════════════════════════════
# Main
# ══════════════════════════════════════════════════════════════

def main():
    print(f"  AcaciaFund Admin Panel")
    print(f"  ─────────────────────")
    print(f"  Registry: {REGISTRY_PATH}")
    print(f"  Images:   {IMAGES_DIR}")
    print(f"")
    articles = _load_registry()
    images = _scan_images()
    print(f"  Articles: {len(articles)}")
    print(f"  Images:   {len(images)}")
    print(f"")
    print(f"  Open http://localhost:5555/admin")
    app.run(host="0.0.0.0", port=5555, debug=True, use_reloader=True)


if __name__ == "__main__":
    main()
