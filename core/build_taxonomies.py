#!/usr/bin/env python3
"""
Build Taxonomy System for AcaciaFund.
Separates dynamic tag/taxonomy page generation from core content builds.
These pages are generated AFTER core content and are NOT cached by the
content hash system — they always regenerate since they depend on
aggregate state (tag maps, stats, etc.) that changes across builds.
"""

import hashlib
import json
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
) -> int:
    """Generate all tag archive pages. Returns count of pages generated."""
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
    admin_username, admin_password = ("admin", "admin")
    if load_admin_credentials_fn:
        admin_username, admin_password = load_admin_credentials_fn()

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

    print(
        "  admin: login, dashboard, gallery, articles, manifest, pipeline, quality, coverage, sources, curated-test"
    )
    return pages_generated


def generate_search_pages(
    output_dir: Path,
    static_dst_dir: Path,
    all_content: List[Any],
    render_template,
    ctx_base: Dict[str, Any],
    _dummy,
) -> int:
    """Generate search index JSON and search page. Returns count of pages generated."""
    pages_generated = 0

    search_index = []
    for c in all_content:
        slug = getattr(c, "slug", None)
        if not slug:
            continue
        search_index.append(
            {
                "title": getattr(c, "title", ""),
                "description": (getattr(c, "description", None) or "")[:300],
                "slug": slug,
                "pillar": getattr(c, "pillar", None) or "",
                "content_type": getattr(c, "content_type", None) or "",
                "tags": getattr(c, "tags", None) or [],
                "date_str": getattr(c, "date_str", None) or "",
                "difficulty": getattr(c, "difficulty", None) or "",
            }
        )

    search_index_path = static_dst_dir / "search-index.json"
    search_index_path.write_text(
        json.dumps(search_index, ensure_ascii=False), encoding="utf-8"
    )
    print(f"  search: search-index.json ({len(search_index)} entries)")
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
    research_items: List[Any],
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
        is_future_post_fn = lambda c: False

    if canonical_path_fn is None:
        canonical_path_fn = lambda p: p

    if slug_to_path_fn is None:
        slug_to_path_fn = lambda s: s

    published_for_feed = [p for p in research_items if not is_future_post_fn(p)]
    feed_candidates = [p.created_at for p in published_for_feed[:20] if getattr(p, "created_at", None)]
    feed_updated = max(feed_candidates).isoformat() if feed_candidates else now.isoformat()

    feed_items = []
    for post in published_for_feed[:20]:
        path = canonical_path_fn(slug_to_path_fn(post.slug))
        desc = ((post.description or post.body_html[:200])[:300]) if getattr(post, "body_html", None) else ""
        post_updated = (post.created_at or now).isoformat()
        feed_items.append(f"""  <entry>
    <title>{post.title}</title>
    <link href="{site_url}/{path}" rel="alternate" type="text/html"/>
    <id>{site_url}/{path}</id>
    <updated>{post_updated}</updated>
    <summary>{desc}</summary>
  </entry>""")

    feed = f"""<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>{site_name} Research</title>
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
