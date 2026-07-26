#!/usr/bin/env python3
"""
Build Taxonomy System for AcaciaFund.
Separates dynamic tag/taxonomy page generation from core content builds.
These pages are generated AFTER core content and are NOT cached by the
content hash system — they always regenerate since they depend on
aggregate state (tag maps, stats, etc.) that changes across builds.
"""

import json
import os
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


def generate_tag_pages(
    output_dir: Path,
    tag_items: Dict[str, List[Any]],
    render_template,
    ctx_base: Dict[str, Any],
    _dummy,
    site_url: str = "",
    pillar_url_map: Optional[Dict[str, str]] = None,
) -> int:
    """Generate all tag archive pages. Returns count of pages generated."""
    from collections import defaultdict

    tags_dir = output_dir / "tags"
    tags_dir.mkdir(parents=True, exist_ok=True)

    pages_generated = 0

    for tag_slug, tag_posts in sorted(tag_items.items()):
        tag_slug_clean = re.sub(r"[^a-z0-9]+", "-", tag_slug.lower()).strip("-")
        if not tag_slug_clean:
            continue

        thin = len(tag_posts) < 3

        tag_out = tags_dir / tag_slug_clean / "index.html"
        tag_out.parent.mkdir(parents=True, exist_ok=True)

        html = render_template(
            "tag_index.j2",
            content=_dummy(f"Tag: {tag_slug}", "tag"),
            tag=tag_slug,
            items=tag_posts,
            is_index=False,
            page_path=f"tags/{tag_slug_clean}/",
            robots_noindex=thin,
            **ctx_base,
        )
        tag_out.write_text(html, encoding="utf-8")
        pages_generated += 1

    if tag_items:
        tag_out = tags_dir / "index.html"
        html = render_template(
            "tag_index.j2",
            content=_dummy("Tags", "tag"),
            tag="",
            items=[],
            all_tags=sorted(tag_items.keys()),
            is_index=False,
            page_path="tags/",
            **ctx_base,
        )
        tag_out.write_text(html, encoding="utf-8")
        pages_generated += 1

    # Per-pillar tag pages
    if pillar_url_map:
        pillar_tag_items: Dict[str, Dict[str, list]] = defaultdict(lambda: defaultdict(list))
        for tag_slug, tag_posts in tag_items.items():
            for p in tag_posts:
                pillar = getattr(p, "pillar", None) or ""
                if pillar:
                    pillar_tag_items[pillar][tag_slug].append(p)

        for pillar_key, tags_dict in pillar_tag_items.items():
            pillar_url = pillar_url_map.get(pillar_key, pillar_key)
            pillar_tags_dir = output_dir / pillar_url / "tags"
            pillar_tags_dir.mkdir(parents=True, exist_ok=True)

            for tag_slug, tag_posts in sorted(tags_dict.items()):
                tag_slug_clean = re.sub(r"[^a-z0-9]+", "-", tag_slug.lower()).strip("-")
                if not tag_slug_clean:
                    continue

                tag_out = pillar_tags_dir / tag_slug_clean / "index.html"
                tag_out.parent.mkdir(parents=True, exist_ok=True)

                html = render_template(
                    "tag_index.j2",
                    content=_dummy(f"{tag_slug} — {pillar_key}", "tag"),
                    tag=tag_slug,
                    items=tag_posts,
                    is_index=False,
                    page_path=f"{pillar_url}/tags/{tag_slug_clean}/",
                    **ctx_base,
                )
                tag_out.write_text(html, encoding="utf-8")
                pages_generated += 1

    return pages_generated


def _compute_dashboard_stats(all_content: List[Any]) -> Dict[str, Any]:
    """Compute dashboard statistics from content items."""
    article_count = len(all_content)
    articles_with_images = sum(1 for c in all_content if getattr(c, "featured_image", None))

    low_score_sections = 0
    for c in all_content:
        signals = getattr(c, "signals", None) or {}
        avg_score = signals.get("avg_score", 100) if isinstance(signals, dict) else 100
        if avg_score < 70:
            low_score_sections += 1

    by_type_dict: Dict[str, Dict[str, int]] = defaultdict(lambda: {"total": 0, "with_images": 0, "without_images": 0})
    for c in all_content:
        ct = getattr(c, "content_type", None) or "unknown"
        by_type_dict[ct]["total"] += 1
        if getattr(c, "featured_image", None):
            by_type_dict[ct]["with_images"] += 1
        else:
            by_type_dict[ct]["without_images"] += 1
    by_type_list = [
        {"type": ct, "total": data["total"], "with_images": data["with_images"], "without_images": data["without_images"]}
        for ct, data in sorted(by_type_dict.items())
    ]

    by_source_dict: Dict[str, int] = defaultdict(int)
    for c in all_content:
        sb = getattr(c, "source_breakdown", None) or {}
        for src, count in sb.items():
            by_source_dict[src] += count

    return {
        "total_images": 0,
        "total_articles": article_count,
        "with_images": articles_with_images,
        "without_images": article_count - articles_with_images,
        "with_images_pct": round(articles_with_images / article_count * 100, 1) if article_count > 0 else 0,
        "low_score": low_score_sections,
        "low_score_sections": low_score_sections,
        "orphan_images": 0,
        "svg_fallbacks": 0,
        "manifest_entries": 0,
        "by_type": by_type_list,
        "by_source": dict(by_source_dict),
    }


def _compute_quality_stats(all_content: List[Any]) -> Dict[str, Any]:
    """Compute quality statistics from content section_images."""
    all_scores = []
    scores_by_source: Dict[str, List[float]] = {}
    scores_by_section: Dict[int, List[float]] = {}
    scores_by_type: Dict[str, List[float]] = {}

    for c in all_content:
        ct = getattr(c, "content_type", None) or "unknown"
        for s in getattr(c, "section_images", None) or []:
            score = s.get("relevance_score", 0)
            if score:
                all_scores.append(score)
                src = s.get("source_api", "unknown")
                scores_by_source.setdefault(src, []).append(score)
                stype = s.get("section_index", 0)
                scores_by_section.setdefault(stype, []).append(score)
                scores_by_type.setdefault(ct, []).append(score)

    buckets = [0] * 10
    for s in all_scores:
        buckets[min(int(s / 10), 9)] += 1

    source_avgs = (
        {src: round(sum(v) / len(v), 1) for src, v in sorted(scores_by_source.items(), key=lambda x: -sum(x[1]) / len(x[1]))}
        if scores_by_source
        else {}
    )
    section_avgs = (
        {str(k): round(sum(v) / len(v), 1) for k, v in sorted(scores_by_section.items(), key=lambda x: -sum(x[1]) / len(x[1]))}
        if scores_by_section
        else {}
    )
    type_avgs = (
        {k: round(sum(v) / len(v), 1) for k, v in sorted(scores_by_type.items(), key=lambda x: -sum(x[1]) / len(x[1]))}
        if scores_by_type
        else {}
    )

    total_scores = len(all_scores)
    return {
        "total_scores": total_scores,
        "avg_score": round(sum(all_scores) / len(all_scores), 1) if all_scores else 0,
        "median_score": round(sorted(all_scores)[len(all_scores) // 2], 1) if all_scores else 0,
        "above_70": sum(1 for s in all_scores if s >= 70),
        "below_40": sum(1 for s in all_scores if s < 40),
        "buckets": buckets,
        "source_avgs": source_avgs,
        "section_avgs": section_avgs,
        "type_avgs": type_avgs,
    }


def _compute_coverage_data(all_content: List[Any], section_types: Dict[int, str]) -> Dict[str, Any]:
    """Compute image coverage heatmap data."""
    coverage_by_type: Dict[str, Dict[str, int]] = {}
    coverage_by_pillar: Dict[str, Dict[str, int]] = {}
    heatmap: Dict[str, Dict[str, Dict[str, int]]] = {}

    for c in all_content:
        pillar = getattr(c, "pillar", None) or "unknown"
        ct = getattr(c, "content_type", None) or "unknown"
        if pillar not in coverage_by_pillar:
            coverage_by_pillar[pillar] = {"filled": 0, "total": 0}
        if pillar not in heatmap:
            heatmap[pillar] = {}
        if ct not in coverage_by_type:
            coverage_by_type[ct] = {"filled": 0, "total": 0}

        for s in getattr(c, "section_images", None) or []:
            section_idx = s.get("section_index", 0)
            section_type = section_types.get(section_idx, f"section_{section_idx}")
            if section_type not in heatmap[pillar]:
                heatmap[pillar][section_type] = {"filled": 0, "total": 0}

            coverage_by_pillar[pillar]["total"] += 1
            coverage_by_type[ct]["total"] += 1
            heatmap[pillar][section_type]["total"] += 1

            if s.get("image_url"):
                coverage_by_pillar[pillar]["filled"] += 1
                coverage_by_type[ct]["filled"] += 1
                heatmap[pillar][section_type]["filled"] += 1

    heatmap_pct: Dict[str, Dict[str, float]] = {}
    for pillar, sections in heatmap.items():
        heatmap_pct[pillar] = {}
        for section_type, data in sections.items():
            pct = round(data["filled"] / data["total"] * 100, 0) if data["total"] else 0
            heatmap_pct[pillar][section_type] = pct

    return {
        "heatmap": heatmap_pct,
        "by_pillar": coverage_by_pillar,
        "by_type": coverage_by_type,
    }


# ── Telemetry Data Collectors ───────────────────────────────────────────

def _compute_tag_telemetry(all_content: List[Any]) -> Dict[str, Any]:
    """Tag distribution, co-occurrence, and pillar crossover statistics."""
    tag_counts: Dict[str, int] = {}
    tag_by_pillar: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
    tag_cooccurrence: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
    tag_content_types: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
    tag_first_seen: Dict[str, str] = {}
    tag_last_seen: Dict[str, str] = {}

    for c in all_content:
        tags = list(dict.fromkeys(t.lower() for t in (getattr(c, "tags", None) or [])))
        pillar = getattr(c, "pillar", None) or "unknown"
        ct = getattr(c, "content_type", None) or "unknown"
        ds = getattr(c, "date_str", None) or ""

        for t in tags:
            tag_counts[t] = tag_counts.get(t, 0) + 1
            tag_by_pillar[t][pillar] += 1
            tag_content_types[t][ct] += 1
            if ds:
                tag_first_seen.setdefault(t, ds)
                if ds > tag_last_seen.get(t, ""):
                    tag_last_seen[t] = ds

        for i, t1 in enumerate(tags):
            for t2 in tags[i + 1:]:
                if t1 < t2:
                    tag_cooccurrence[t1][t2] += 1
                else:
                    tag_cooccurrence[t2][t1] += 1

    # Tags with pillar crossover (appear in 2+ pillars)
    crossover_tags = {
        t: dict(pillars)
        for t, pillars in tag_by_pillar.items()
        if len(pillars) >= 2
    }

    # Co-occurrence edges for network graph
    cooc_edges = []
    for t1, neighbors in tag_cooccurrence.items():
        for t2, count in neighbors.items():
            if count >= 2:  # filter noise
                cooc_edges.append({"source": t1, "target": t2, "weight": count})

    # Token co-occurrence data for network viz
    cooc_nodes = [{"id": t, "frequency": tag_counts[t]} for t in tag_counts]

    top_tags_sorted = sorted(tag_counts.items(), key=lambda x: -x[1])

    edges_sorted = sorted(cooc_edges, key=lambda x: -x["weight"])[:200]
    return {
        "total_tags": len(tag_counts),
        "total_assignments": sum(tag_counts.values()),
        "top_tags": top_tags_sorted[:20],
        "top_tags_max_count": top_tags_sorted[0][1] if top_tags_sorted else 1,
        "crossover_tags": dict(list(crossover_tags.items())[:20]),
        "crossover_count": len(crossover_tags),
        "cooccurrence_nodes": cooc_nodes,
        "cooccurrence_max_freq": max(cooc_nodes, key=lambda n: n["frequency"]).get("frequency", 1) if cooc_nodes else 1,
        "cooccurrence_edges": edges_sorted,
        "cooccurrence_max_weight": max(e["weight"] for e in edges_sorted) if edges_sorted else 1,
        "tag_by_pillar": {t: dict(p) for t, p in tag_by_pillar.items()},
    }


def _compute_sqi_telemetry(all_content: List[Any]) -> Dict[str, Any]:
    """SQI distribution and per-pillar averages."""
    sqi_values: list[float] = []
    sqi_by_pillar: Dict[str, list[float]] = defaultdict(list)
    sqi_by_content_type: Dict[str, list[float]] = defaultdict(list)

    for c in all_content:
        # sqi may be a direct attribute or in signals
        sqi = getattr(c, "sqi", None)
        if sqi is None:
            signals = getattr(c, "signals", None) or {}
            sqi = signals.get("avg_sqi", 0.5) if isinstance(signals, dict) else 0.5
        sqi = float(sqi) if sqi else 0.5
        sqi = max(0.0, min(1.0, sqi))
        sqi_values.append(sqi)

        pillar = getattr(c, "pillar", None) or "unknown"
        sqi_by_pillar[pillar].append(sqi)

        ct = getattr(c, "content_type", None) or "unknown"
        sqi_by_content_type[ct].append(sqi)

    # Distribution deciles
    deciles = [0.0] * 10
    for s in sqi_values:
        idx = min(int(s * 10), 9)
        deciles[idx] += 1

    pillar_avgs = {
        p: {"avg": round(sum(v) / len(v), 3), "count": len(v), "min": round(min(v), 3), "max": round(max(v), 3)}
        for p, v in sorted(sqi_by_pillar.items())
    }

    type_avgs = {
        t: {"avg": round(sum(v) / len(v), 3), "count": len(v)}
        for t, v in sorted(sqi_by_content_type.items())
    }

    return {
        "count": len(sqi_values),
        "avg": round(sum(sqi_values) / len(sqi_values), 3) if sqi_values else 0,
        "min": round(min(sqi_values), 3) if sqi_values else 0,
        "max": round(max(sqi_values), 3) if sqi_values else 0,
        "deciles": deciles,
        "decile_max": max(deciles) if deciles else 1,
        "pillar_avgs": pillar_avgs,
        "type_avgs": type_avgs,
        "above_08": sum(1 for s in sqi_values if s >= 0.8),
        "below_05": sum(1 for s in sqi_values if s < 0.5),
    }


def _compute_enrichment_telemetry(all_content: List[Any]) -> Dict[str, Any]:
    """Enrichment source tracking — LLM vs deterministic tags."""
    llm_item_count = 0
    det_item_count = 0
    total_enriched = 0
    tag_sources: Dict[str, int] = defaultdict(int)

    for c in all_content:
        enriched = getattr(c, "enriched", False) or getattr(c, "enriched_at", None) is not None
        if enriched:
            total_enriched += 1

        tags = getattr(c, "tags", None) or []
        # Items with 5+ specific tags likely LLM-enriched; fewer generic tags likely deterministic
        if len(tags) >= 4:
            llm_item_count += 1
        else:
            det_item_count += 1

        for t in tags:
            tag_sources[t] += 1

    total = len(all_content)
    return {
        "total_enriched": total_enriched,
        "total_enriched_pct": round(total_enriched / total * 100, 1) if total else 0,
        "llm_likely": llm_item_count,
        "deterministic_likely": det_item_count,
        "llm_pct": round(llm_item_count / total * 100, 1) if total else 0,
        "det_pct": round(det_item_count / total * 100, 1) if total else 0,
    }


def _compute_velocity_telemetry(all_content: List[Any]) -> Dict[str, Any]:
    """Content publishing velocity — items over time."""
    monthly: Dict[str, int] = defaultdict(int)
    weekly: Dict[str, int] = defaultdict(int)

    for c in all_content:
        dt = getattr(c, "created_at", None)
        if dt and hasattr(dt, "strftime"):
            try:
                month_key = dt.strftime("%Y-%m")
                weekly_key = dt.strftime("%Y-W%W")
                monthly[month_key] += 1
                weekly[weekly_key] += 1
            except Exception:
                pass

    monthly_sorted = sorted(monthly.items())
    weekly_sorted = sorted(weekly.items())

    monthly_list = [{"period": k, "count": v} for k, v in monthly_sorted]
    return {
        "monthly": monthly_list,
        "monthly_max": max((m["count"] for m in monthly_list), default=1),
        "weekly": [{"period": k, "count": v} for k, v in weekly_sorted],
        "total_months": len(monthly),
        "total_weeks": len(weekly),
    }


def _compute_source_telemetry(all_content: List[Any]) -> Dict[str, Any]:
    """Source breakdown telemetry — HN, ArXiv, PubMed distribution."""
    source_totals: Dict[str, int] = defaultdict(int)
    source_by_pillar: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
    items_with_sources = 0

    for c in all_content:
        sb = getattr(c, "source_breakdown", None) or {}
        if sb:
            items_with_sources += 1
            pillar = getattr(c, "pillar", None) or "unknown"
            for src, count in sb.items():
                source_totals[src] += count
                source_by_pillar[pillar][src] += count

    return {
        "source_totals": dict(source_totals),
        "source_by_pillar": dict(source_by_pillar),
        "items_with_sources": items_with_sources,
        "items_wo_sources": len(all_content) - items_with_sources,
    }


def _compute_telemetry(all_content: List[Any]) -> Dict[str, Any]:
    """Compute all telemetry data at once."""
    return {
        "tag": _compute_tag_telemetry(all_content),
        "sqi": _compute_sqi_telemetry(all_content),
        "enrichment": _compute_enrichment_telemetry(all_content),
        "velocity": _compute_velocity_telemetry(all_content),
        "source": _compute_source_telemetry(all_content),
    }


def generate_admin_pages(
    output_dir: Path,
    all_content: List[Any],
    static_dst_dir: Path,
    render_template,
    ctx_base: Dict[str, Any],
    _dummy,
    load_admin_credentials_fn=None,
    load_manifest_fn=None,
    project_root: Optional[Path] = None,
    section_types: Optional[Dict[int, str]] = None,
    ontology=None,
) -> int:
    """Generate all admin panel pages. Returns count of pages generated."""
    admin_dir = output_dir / "admin"
    admin_dir.mkdir(parents=True, exist_ok=True)

    pages_generated = 0
    stats = _compute_dashboard_stats(all_content)
    image_count = len(list(static_dst_dir.glob("images/generated/**/*.webp")))

    # Dashboard
    html = render_template(
        "admin/dashboard.html",
        content=_dummy("Admin Dashboard", "admin"),
        active_page="dashboard",
        image_count=image_count,
        article_count=stats["total_articles"],
        stats_total_images=stats["total_images"],
        stats_total_articles=stats["total_articles"],
        stats_with_images=stats["with_images"],
        stats_without_images=stats["without_images"],
        stats_with_images_pct=stats["with_images_pct"],
        stats_low_score=stats["low_score"],
        stats_orphan_images=stats["orphan_images"],
        stats_svg_fallbacks=stats["svg_fallbacks"],
        stats_manifest_entries=stats["manifest_entries"],
        stats_by_type=stats["by_type"],
        stats_by_source=stats["by_source"],
        **ctx_base,
    )
    (admin_dir / "dashboard.html").write_text(html, encoding="utf-8")
    pages_generated += 1

    # Gallery
    gallery_images = []
    if load_manifest_fn:
        manifest = load_manifest_fn()
        for key, entry in manifest.items():
            for sec in entry.get("sections", []):
                img_url = sec.get("image_url", "")
                if img_url:
                    gallery_images.append(
                        {
                            "url": img_url,
                            "slug": key.split("/", 1)[-1] if "/" in key else key,
                            "section_index": sec.get("section_index"),
                        }
                    )

    html = render_template(
        "admin/gallery.html",
        content=_dummy("Image Gallery", "admin"),
        active_page="gallery",
        image_count=image_count,
        article_count=stats["total_articles"],
        stats_total_images=len(gallery_images),
        stats_orphan_images=0,
        gallery_images=gallery_images,
        **ctx_base,
    )
    (admin_dir / "gallery.html").write_text(html, encoding="utf-8")
    pages_generated += 1

    # Articles
    html = render_template(
        "admin/article_list.html",
        content=_dummy("Articles", "admin"),
        active_page="articles",
        image_count=image_count,
        article_count=stats["total_articles"],
        articles=all_content,
        **ctx_base,
    )
    (admin_dir / "articles.html").write_text(html, encoding="utf-8")
    pages_generated += 1

    # Credentials + index redirect
    admin_username = "admin"
    admin_password = "admin"
    if load_admin_credentials_fn:
        admin_username, admin_password = load_admin_credentials_fn()
    else:
        admin_username = os.environ.get("ADMIN_USERNAME", "")
        admin_password = os.environ.get("ADMIN_PASSWORD", "")

    redirect_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="refresh" content="0;url=login">
    <title>Redirecting...</title>
</head>
<body>
    <p>Redirecting to login page...</p>
    <script>
        window.location.href = 'login';
    </script>
</body>
</html>"""
    (admin_dir / "index.html").write_text(redirect_html, encoding="utf-8")

    # Login
    html = render_template(
        "admin/login.html",
        content=_dummy("Admin Login", "admin"),
        admin_username=admin_username,
        admin_password=admin_password,
        **ctx_base,
    )
    (admin_dir / "login.html").write_text(html, encoding="utf-8")
    pages_generated += 1

    # Manifest
    if load_manifest_fn:
        manifest = load_manifest_fn()
        manifest_entries = []
        for key, entry in manifest.items():
            for sec in entry.get("sections", []):
                manifest_entries.append(
                    {
                        "key": key,
                        "slug": key.split("/", 1)[-1] if "/" in key else key,
                        "section_index": sec.get("section_index"),
                        "image_url": sec.get("image_url"),
                        "image_credit": sec.get("image_credit", ""),
                        "note": entry.get("note", ""),
                    }
                )
        manifest_entries.sort(key=lambda x: (x["slug"], x["section_index"]))
    else:
        manifest_entries = []

    html = render_template(
        "admin/manifest.html",
        content=_dummy("Manifest", "admin"),
        active_page="manifest",
        manifest_entries=manifest_entries,
        **ctx_base,
    )
    (admin_dir / "manifest.html").write_text(html, encoding="utf-8")
    pages_generated += 1

    # Pipeline
    pipeline_runs = []
    dlq_entries = []
    if project_root:
        pipeline_runs_path = project_root / "registry" / "image-pipeline-runs.json"
        if pipeline_runs_path.exists():
            try:
                pipeline_runs = json.loads(pipeline_runs_path.read_text())
            except Exception:
                pass
        dlq_dir = project_root / ".dlq"
        if dlq_dir.exists():
            for f in sorted(dlq_dir.glob("*.json"), reverse=True)[:100]:
                try:
                    dlq_entries.append(json.loads(f.read_text()))
                except Exception:
                    pass

    html = render_template(
        "admin/pipeline.html",
        content=_dummy("Pipeline", "admin"),
        active_page="pipeline",
        runs=pipeline_runs,
        dlq=dlq_entries,
        dlq_count=len(dlq_entries),
        **ctx_base,
    )
    (admin_dir / "pipeline.html").write_text(html, encoding="utf-8")
    pages_generated += 1

    # Quality
    qstats = _compute_quality_stats(all_content)
    html = render_template(
        "admin/quality.html",
        content=_dummy("Quality", "admin"),
        active_page="quality",
        stats_total_scores=qstats["total_scores"],
        stats_avg_score=qstats["avg_score"],
        stats_median_score=qstats["median_score"],
        stats_above_70=qstats["above_70"],
        stats_below_40=qstats["below_40"],
        stats_buckets=qstats["buckets"],
        stats_source_avgs=qstats["source_avgs"],
        stats_section_avgs=qstats["section_avgs"],
        stats_type_avgs=qstats["type_avgs"],
        **ctx_base,
    )
    (admin_dir / "quality.html").write_text(html, encoding="utf-8")
    pages_generated += 1

    # Coverage
    cov_section_types = section_types or {
        0: "overview", 1: "key_findings", 2: "applied_scenario",
        3: "source_analysis", 4: "domain_breakdown", 5: "cross_pillar", 6: "methodology",
    }
    coverage = _compute_coverage_data(all_content, cov_section_types)
    html = render_template(
        "admin/coverage.html",
        content=_dummy("Coverage", "admin"),
        active_page="coverage",
        heatmap=coverage["heatmap"],
        by_pillar=coverage["by_pillar"],
        by_type=coverage["by_type"],
        **ctx_base,
    )
    (admin_dir / "coverage.html").write_text(html, encoding="utf-8")
    pages_generated += 1

    # Sources
    sources = []
    try:
        from core.sources import registry as source_registry
        source_list = source_registry.source_list()
        summaries = source_registry.summaries()
        for s in source_list:
            summary = next((sm for sm in summaries if sm["name"] == s["name"]), {})
            sources.append({**s, **summary})
    except Exception:
        pass

    # Fallback: load inspiration sources from pillars.toml
    if not sources and project_root:
        try:
            import tomllib
            toml_path = project_root / "etc" / "pillars.toml"
            if toml_path.exists():
                with open(toml_path, "rb") as _tf:
                    _toml = tomllib.load(_tf)
                for _pk, _ps in _toml.get("inspiration_sources", {}).items():
                    if not isinstance(_ps, dict):
                        continue
                    for _sk, _si in _ps.items():
                        if isinstance(_si, dict) and "url" in _si:
                            sources.append({
                                "name": _si.get("name", _sk),
                                "url": _si["url"],
                                "type": "inspiration",
                                "pillar": _pk,
                                "relevance": _si.get("relevance", 0.5),
                            })
        except Exception:
            pass

    # Merge source freshness data if available
    source_health_path = None
    if project_root:
        for candidate in [project_root / "data" / "source_health.json", project_root / "dist" / "source_health.json"]:
            if candidate.exists():
                source_health_path = candidate
                break
    freshness_map = {}
    health_data = None
    if source_health_path and source_health_path.exists():
        try:
            health_data = json.loads(source_health_path.read_text(encoding="utf-8"))
            for entry in health_data.get("sources", []):
                freshness_map[entry.get("name", "")] = entry
        except Exception:
            pass
    for s in sources:
        name = s.get("name", "")
        if name in freshness_map:
            s["status"] = freshness_map[name].get("status", "unknown")
            s["last_verified"] = freshness_map[name].get("last_verified")
            s["http_status"] = freshness_map[name].get("http_status")
            s["freshness_pct"] = health_data.get("freshness_pct", 0) if health_data else 0

    html = render_template(
        "admin/sources.html",
        content=_dummy("Sources", "admin"),
        active_page="sources",
        sources=sources,
        **ctx_base,
    )
    (admin_dir / "sources.html").write_text(html, encoding="utf-8")
    pages_generated += 1

    # Curated Tester
    curated_list = []
    try:
        from scripts.fetch_images import CURATED_KNOWN
        curated_list = sorted(CURATED_KNOWN.items(), key=lambda x: x[0])
    except Exception:
        pass

    html = render_template(
        "admin/curated_tester.html",
        content=_dummy("Curated Tester", "admin"),
        active_page="curated",
        curated_entries=curated_list,
        curated_count=len(curated_list),
        **ctx_base,
    )
    (admin_dir / "curated-test.html").write_text(html, encoding="utf-8")
    pages_generated += 1

    # Telemetry
    telemetry = _compute_telemetry(all_content)
    html = render_template(
        "admin/telemetry.html",
        content=_dummy("Telemetry — AcaciaFund", "admin"),
        active_page="telemetry",
        image_count=image_count,
        article_count=stats["total_articles"],
        telemetry=telemetry,
        **ctx_base,
    )
    (admin_dir / "telemetry.html").write_text(html, encoding="utf-8")
    pages_generated += 1

    # Ontology Curation
    if ontology and hasattr(ontology, '_concepts'):
        pillar_colors = {"aml": "#c97d3e", "stock": "#3a7d5c", "data-engineering": "#6366f1"}
        pillar_labels = {"aml": "Compliance", "stock": "Markets", "data-engineering": "Data Engineering"}

        concepts_by_pillar = {}
        for concept in ontology._concepts.values():
            p = concept.pillar or "aml"
            concepts_by_pillar.setdefault(p, []).append(concept)

        relations_data = []
        for r in ontology._relations:
            relations_data.append({
                "source": r.source_id,
                "target": r.target_id,
                "relation_type": r.relation_type,
                "weight": r.strength,
            })

        cross_pillar_count = sum(1 for r in ontology._relations
                                 if ontology._concepts.get(r.source_id, None)
                                 and ontology._concepts.get(r.target_id, None)
                                 and ontology._concepts[r.source_id].pillar != ontology._concepts[r.target_id].pillar)

        html = render_template(
            "admin/ontology.html",
            content=_dummy("Ontology Curation", "admin"),
            active_page="ontology",
            concept_count=ontology.concept_count(),
            relation_count=ontology.relation_count(),
            pillar_count=len(concepts_by_pillar),
            cross_pillar_count=cross_pillar_count,
            concepts_by_pillar=concepts_by_pillar,
            pillar_colors=pillar_colors,
            pillar_labels=pillar_labels,
            relations=relations_data,
            **ctx_base,
        )
        (admin_dir / "ontology.html").write_text(html, encoding="utf-8")
        pages_generated += 1

    # Feynman Metadata Quality Dashboard
    if ontology and hasattr(ontology, '_concepts'):
        feynman_path = project_root / "data" / "feynman_metadata.json" if project_root else Path("data/feynman_metadata.json")
        hand_crafted_ids = set()
        if feynman_path.exists():
            try:
                with open(feynman_path) as f:
                    hand_crafted_ids = set(json.load(f).keys())
            except Exception:
                pass

        pillar_colors = {"aml": "#ef4444", "stock": "#f59e0b", "data-engineering": "#3b82f6"}
        pillar_labels = {"aml": "Compliance", "stock": "Markets", "data-engineering": "Data Engineering"}

        per_pillar = {}
        total_analogs = 0
        total_diagram = 0

        for concept in ontology._concepts.values():
            p = concept.pillar or "aml"
            if p not in per_pillar:
                per_pillar[p] = {
                    "label": pillar_labels.get(p, p),
                    "count": 0,
                    "hand_crafted": 0,
                    "difficulty_sum": 0,
                    "quality_sum": 0.0,
                    "has_diagram": 0,
                    "difficulty_distribution": {str(i): 0 for i in range(1, 6)},
                    "concepts": [],
                }
            pd = per_pillar[p]
            pd["count"] += 1
            hc = concept.id in hand_crafted_ids
            if hc:
                pd["hand_crafted"] += 1
            diff = getattr(concept, "feynman_difficulty", 1)
            quality = getattr(concept, "explanation_quality", 0.0)
            pd["difficulty_sum"] += diff
            pd["quality_sum"] += quality
            diff_str = str(min(5, max(1, diff)))
            pd["difficulty_distribution"][diff_str] = pd["difficulty_distribution"].get(diff_str, 0) + 1
            dia = bool(getattr(concept, "feynman_diagram", None))
            if dia:
                pd["has_diagram"] += 1
            analogs = getattr(concept, "cross_pillar_analogs", []) or []
            pd["concepts"].append({
                "id": concept.id,
                "category": concept.category,
                "difficulty": diff,
                "quality": quality,
                "has_diagram": dia,
                "hand_crafted": hc,
                "analog_count": len(analogs),
            })
            total_analogs += len(analogs)
            if dia:
                total_diagram += 1

        total_concepts = len(ontology._concepts)
        total_hand_crafted = sum(pd["hand_crafted"] for pd in per_pillar.values())

        for pd in per_pillar.values():
            if pd["count"] > 0:
                pd["avg_difficulty"] = pd["difficulty_sum"] / pd["count"]
                pd["avg_quality"] = round(pd["quality_sum"] / pd["count"], 2)
            else:
                pd["avg_difficulty"] = 0.0
                pd["avg_quality"] = 0.0
            del pd["difficulty_sum"]
            del pd["quality_sum"]

        html = render_template(
            "admin/feynman.html",
            content=_dummy("Feynman QA — AcaciaFund", "admin"),
            active_page="feynman",
            per_pillar=per_pillar,
            total_concepts=total_concepts,
            total_hand_crafted=total_hand_crafted,
            total_analogs=total_analogs,
            total_diagram=total_diagram,
            **ctx_base,
        )
        (admin_dir / "feynman.html").write_text(html, encoding="utf-8")
        pages_generated += 1

    print(
        "  admin: login, dashboard, gallery, articles, manifest, pipeline, quality, coverage, sources, curated-test, telemetry, ontology, feynman"
    )
    return pages_generated


def generate_search_pages(
    output_dir: Path,
    static_dst_dir: Path,
    all_content: List[Any],
    render_template,
    ctx_base: Dict[str, Any],
    _dummy,
    ontology=None,
    concept_cache: Dict[str, set] | None = None,
) -> int:
    """Generate search index JSON and search page. Returns count of pages generated."""
    pages_generated = 0

    # Build concept→label map for search enrichment
    concept_labels = {}
    if ontology and hasattr(ontology, '_concepts'):
        concept_labels = {c.id: c.label for c in ontology._concepts.values()}

    search_index = []
    for c in all_content:
        slug = getattr(c, "slug", None)
        if not slug:
            continue

        entry = {
            "title": getattr(c, "title", ""),
            "description": (getattr(c, "description", None) or "")[:300],
            "slug": slug,
            "pillar": getattr(c, "pillar", None) or "",
            "content_type": getattr(c, "content_type", None) or "",
            "tags": getattr(c, "tags", None) or [],
            "date_str": getattr(c, "date_str", None) or "",
            "difficulty": getattr(c, "difficulty", None) or "",
        }

        # Include SQI for quality-aware search
        sqi_val = getattr(c, "sqi", 0.0) or 0.0
        signals = getattr(c, "signals", None) or {}
        signals_avg = signals.get("avg_sqi", 0.0) if isinstance(signals, dict) else 0.0
        entry["avg_sqi"] = max(sqi_val, signals_avg)

        # Enrich with ontology concepts for boosted search
        if concept_cache and slug in concept_cache:
            concept_ids = concept_cache[slug]
            concept_names = [concept_labels.get(cid, cid) for cid in concept_ids]
            entry["ontology_concepts"] = concept_names
            entry["concept_boost"] = min(len(concept_names) * 0.1, 1.0)
        else:
            entry["ontology_concepts"] = []
            entry["concept_boost"] = 0.0

        search_index.append(entry)

    search_index_path = static_dst_dir / "search-index.json"
    search_index_path.write_text(
        json.dumps(search_index, ensure_ascii=False), encoding="utf-8"
    )
    print(f"  search: search-index.json ({len(search_index)} entries)")

    # Generate per-pillar search index chunks for faster initial loads
    for pillar_key in ("aml", "stock", "data-engineering"):
        pillar_entries = [e for e in search_index if e.get("pillar") == pillar_key]
        if pillar_entries:
            chunk_path = static_dst_dir / f"search-index.{pillar_key}.json"
            chunk_path.write_text(
                json.dumps(pillar_entries, ensure_ascii=False), encoding="utf-8"
            )
            print(f"  search: search-index.{pillar_key}.json ({len(pillar_entries)} entries)")

    pages_generated += 1

    search_dir = output_dir / "search"
    search_dir.mkdir(parents=True, exist_ok=True)
    html = render_template(
        "search.j2",
        content=_dummy("Search — AcaciaFund", "search"),
        is_index=False,
        page_path="search/",
        **ctx_base,
    )
    (search_dir / "index.html").write_text(html, encoding="utf-8")
    print("  search: search/index.html")
    pages_generated += 1

    return pages_generated


def generate_feed(
    output_dir: Path,
    all_content: List[Any],
    render_template,
    ctx_base: Dict[str, Any],
    site_url: str = "",
    site_name: str = "",
    now: Optional[datetime] = None,
    is_future_post_fn=None,
    canonical_path_fn=None,
    slug_to_path_fn=None,
) -> int:
    """Generate Atom RSS feed. Returns 1 if generated."""
    if now is None:
        now = datetime.now(timezone.utc)

    if is_future_post_fn is None:
        def _is_future_post_fn(c): return False
        is_future_post_fn = _is_future_post_fn

    if canonical_path_fn is None:
        def _canonical_path_fn(p): return p
        canonical_path_fn = _canonical_path_fn

    if slug_to_path_fn is None:
        def _slug_to_path_fn(s): return s
        slug_to_path_fn = _slug_to_path_fn

    published_for_feed = [p for p in all_content if not is_future_post_fn(p)]
    feed_candidates = [p.created_at for p in published_for_feed[:30] if getattr(p, "created_at", None)]
    feed_updated = max(feed_candidates).isoformat() if feed_candidates else now.isoformat()

    def _clean_feed_desc(post):
        """Strip HTML tags and markdown headings from description for clean feed output."""
        import re as _re
        desc = post.description or ""
        if not desc and getattr(post, "body_html", None):
            desc = post.body_html[:300]
        # Strip HTML tags
        desc = _re.sub(r"<[^>]+>", "", desc)
        # Strip markdown headings
        desc = _re.sub(r"^#+\s*", "", desc, flags=_re.MULTILINE)
        # Collapse whitespace
        desc = _re.sub(r"\s+", " ", desc).strip()
        return desc[:300]

    feed_items = []
    for post in published_for_feed[:30]:
        path = canonical_path_fn(slug_to_path_fn(post.slug))
        desc = _clean_feed_desc(post)
        post_updated = (post.created_at or now).isoformat()
        ct = getattr(post, "content_type", "") or ""
        pillar = getattr(post, "pillar", "") or ""
        tags_list = getattr(post, "tags", []) or []
        tag_xml = "".join(f"\n    <category term=\"{t}\"/>" for t in tags_list[:5])
        ct_xml = f'\n    <category term="type:{ct}"/>' if ct else ""
        pillar_xml = f'\n    <category term="pillar:{pillar}"/>' if pillar else ""
        feed_items.append(f"""  <entry>
    <title>{post.title}</title>
    <link href="{site_url}/{path}" rel="alternate" type="text/html"/>
    <id>{site_url}/{path}</id>
    <updated>{post_updated}</updated>
    <summary>{desc}</summary>{pillar_xml}{ct_xml}{tag_xml}
  </entry>""")

    feed = f"""<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>{site_name}</title>
  <link href="{site_url}/feed.xml" rel="self" type="application/atom+xml"/>
  <link href="{site_url}/" rel="alternate" type="text/html"/>
  <id>{site_url}/feed.xml</id>
  <updated>{feed_updated}</updated>
  <author><name>{site_name}</name></author>
{chr(10).join(feed_items)}
</feed>"""
    (output_dir / "feed.xml").write_text(feed, encoding="utf-8")
    print("  feed: feed.xml")
    return 1


def generate_pillar_pages(
    output_dir: Path,
    pillar_groups: Dict[str, List[Any]],
    render_template,
    ctx_base: Dict[str, Any],
) -> int:
    """Generate pillar index pages. Returns count of pages generated."""
    pages_generated = 0

    for pillar, items in pillar_groups.items():
        pillar_dir = output_dir / pillar
        pillar_dir.mkdir(parents=True, exist_ok=True)

        html = render_template(
            "pillar_index.j2",
            pillar=pillar,
            items=items,
            **ctx_base,
        )
        (pillar_dir / "index.html").write_text(html, encoding="utf-8")
        pages_generated += 1

    return pages_generated
