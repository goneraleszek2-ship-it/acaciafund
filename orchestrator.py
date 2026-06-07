#!/usr/bin/env python3.13
"""
Orchestrator for AcaciaFund: builds rich registry.json from ingest pipeline.
Runs the full pipeline: fetch -> classify -> score -> bloom -> generate -> registry.
"""
import argparse
import hashlib
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

import markdown2

from schemas import AcaciaContent, RegistryData, PipelineStage, MCPIntegration, PlannedFeature

sys.path.insert(0, str(Path(__file__).parent))
from core.data import PILLARS, log, extract_domain, extract_entities, extract_themes
from core.fetch import fetch_hn_stories, fetch_arxiv, fetch_pubmed
from core.analyze import classify_story
from core.score import compute_signal_score, build_history
from core.bloom import classify_bloom_level, generate_quiz_questions, generate_flashcards, level_label_en
from core.scraper import scrape_articles
from core.visuals import generate_thumbnail_svg, generate_og_image, PILLAR_COLORS

CONTENT_ROOT = Path("content")
REGISTRY_PATH = Path("registry.json")
STATIC_IMAGES_DIR = Path("static") / "images"


def slugify(text: str) -> str:
    text = text.lower().replace(" ", "-")
    return re.sub(r'[^a-z0-9-]', '', text)


def build_trending_section(stories: list[dict], date_str: str) -> str:
    lines = [f"## Trending (HackerNews, {date_str})", ""]
    for i, s in enumerate(stories[:10], 1):
        title = s.get("title", "")
        url = s.get("url", "")
        hn_url = s.get("hn_url", "")
        points = s.get("points", 0)
        if url and hn_url:
            lines.append(f'{i}. [{title}]({url}) ([discussion]({hn_url})) ({points} pts)')
        elif url:
            lines.append(f'{i}. [{title}]({url}) ({points} pts)')
        else:
            lines.append(f'{i}. {title} ({points} pts)')
    return "\n".join(lines)


def build_meta_analysis(stories: list[dict], signals: dict, pillar_name: str) -> str:
    top = stories[0] if stories else None
    if not top:
        return ""
    avg_sqi = signals.get("avg_sqi", 0)
    total_pts = signals.get("total_score", 0)
    top_pts = top.get("points", 0)
    outlier_ratio = signals.get("outlier_ratio", 1)

    lines = [
        "> **Summary**",
        f">Today in {pillar_name}, the top story is **\"{top.get('title', '')}\"**, "
        f"which gathered {top_pts} points on Hacker News"
    ]
    if outlier_ratio > 2:
        lines.append(f"> -- nearly {outlier_ratio:.0f}x higher than the average of other articles.")
    lines.append(f"> Total: {len(stories)} articles with {total_pts} points. "
                 f"Average SQI: {avg_sqi:.3f}.")
    return "\n\n".join(lines)


def build_deep_analysis(stories: list[dict], scraped: dict, pillar_name: str, signals: dict) -> str:
    top_entities = signals.get("top_entities", [])
    key_numbers = signals.get("key_numbers", [])
    sentences = []
    for key, entry in list(scraped.items())[:3]:
        text = entry.get("text", "")
        if text:
            first_sentences = re.split(r'(?<=[.!])\s+', text)[:2]
            sentences.extend(f for f in first_sentences if len(f) > 40)

    parts = []
    if top_entities:
        parts.append(f"**Key entities:** `{'` · `'.join(top_entities[:6])}`")
    if key_numbers:
        parts.append(f"**Key numbers:** {' · '.join(k[0] for k in key_numbers[:5])}")
    if sentences:
        parts.append("**From articles:**")
        for s in sentences[:3]:
            parts.append(f"- {s[:150]}")

    return "\n".join(parts) if parts else ""


def build_cross_pillar(stories: list[dict], all_pillar_stories: dict) -> str:
    from core.data import DOMAIN_PATTERNS, KEYWORD_PATTERNS, ALL_ENTITIES
    connections = []
    for pname, pstories in all_pillar_stories.items():
        for s in pstories:
            title_lower = s.get("title", "").lower()
            domain = extract_domain(s.get("url", ""))
            score = 0
            for pat, sval in DOMAIN_PATTERNS.get(pname, []):
                if pat.search(domain):
                    score += sval
            for pat in KEYWORD_PATTERNS.get(pname, []):
                if pat.search(title_lower):
                    score += 3
            if score > 0:
                connections.append((s.get("title", ""), pname, score))
    connections.sort(key=lambda x: -x[2])

    if not connections:
        return ""
    parts = ["### Cross-pillar connections"]
    for title, pname, score in connections[:5]:
        parts.append(f'- "{title[:60]}" has connections to **{pname.upper()}** (score: {score})')
    return "\n".join(parts)


def build_classification_confidence(all_stories: list, pillar_name: str,
                                     pillar_stories: list, unclassified: int) -> str:
    total = len(all_stories)
    classified = len(pillar_stories)
    pct = (classified / total * 100) if total > 0 else 0
    return (f"Classification: {pct:.0f}% ({classified}/{total}) "
            f"| Pillar share: {len(pillar_stories) / max(1, total) * 100:.0f}%")


def compute_pillar_signals(stories: list[dict]) -> dict:
    if not stories:
        return {}
    history = build_history()
    scores = [compute_signal_score(s, history) for s in stories]
    sqis = [s["sqi"] for s in scores]
    points = [s.get("points", 0) for s in stories]
    domains = [extract_domain(s.get("url", "")) for s in stories]

    from collections import Counter
    domain_counts = Counter(d for d in domains if d)
    top_domain = domain_counts.most_common(1)
    top_domain_name = top_domain[0][0] if top_domain else "other"
    top_domain_share = top_domain[0][1] / len(domains) if domains else 0

    max_pts = max(points) if points else 0
    avg_pts = sum(points) / len(points) if points else 0

    top_entities = Counter()
    title_text = " ".join(s.get("title", "") for s in stories)
    entities = extract_entities(title_text)
    for e in entities:
        top_entities[e] += 1

    key_numbers = []
    for s in stories[:10]:
        nums = re.findall(r'\$?(\d[\d,.]*(?:k|m|b|bn|tr)?)', s.get("title", ""))
        for n in nums[:2]:
            key_numbers.append([n, s.get("title", "")[:80]])

    return {
        "avg_sqi": round(sum(sqis) / len(sqis), 3) if sqis else 0,
        "count": len(stories),
        "total_score": sum(points),
        "max_score": max_pts,
        "avg_score": round(avg_pts, 2),
        "outlier_ratio": round(max_pts / max(1, avg_pts), 2) if avg_pts > 0 else 1,
        "score_skew": "outlier" if max_pts > 3 * avg_pts > 0 else "balanced",
        "domain_diversity": len(set(domains)),
        "top_domain": top_domain_name,
        "top_domain_share": round(top_domain_share, 2),
        "top_entities": [e for e, _ in top_entities.most_common(8)],
        "key_numbers": key_numbers[:5],
    }


def make_date_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def generate_post_content(pillar_name: str, config: dict, stories: list[dict],
                           all_pillar_stories: dict, all_stories: list,
                           unclassified: int, run_id: str) -> Optional[AcaciaContent]:
    date_str = make_date_str()
    signals = compute_pillar_signals(stories)
    top_story = stories[0] if stories else None
    page_title = f"{top_story['title'] if top_story else config['label']} -- {config['emoji']} {config['label']} {date_str}"

    bloom_levels = list(dict.fromkeys(classify_bloom_level(s) for s in stories))

    urls = [s.get("url", "") for s in stories if s.get("url")]
    scraped = scrape_articles(urls, max_scrape=120)

    edu_questions = generate_quiz_questions(stories, config["label"], scraped)
    edu_flashcards = generate_flashcards(stories, config["label"])

    trending_section = build_trending_section(stories, date_str)
    meta = build_meta_analysis(stories, signals, config["label"])
    deep = build_deep_analysis(stories, scraped, config["label"], signals)
    cross = build_cross_pillar(pillar_name, all_pillar_stories)
    confidence = build_classification_confidence(all_stories, pillar_name, stories, unclassified)

    thumb_svg = ""
    og_svg = ""
    if top_story:
        avg_sqi = signals.get("avg_sqi", 0.5)
        thumb_title = top_story["title"]
        pal = PILLAR_COLORS.get(pillar_name, PILLAR_COLORS["aml"])
        thumb_svg = generate_thumbnail_svg(thumb_title, pillar_name, {"sqi": avg_sqi})
        og_svg = generate_og_image(thumb_title, pillar_name, {"sqi": avg_sqi}, date_str)

    source_breakdown = {"hn": 0, "arxiv": 0, "pubmed": 0}
    for s in stories:
        src = s.get("source", "hn")
        if src in source_breakdown:
            source_breakdown[src] += 1
        else:
            source_breakdown[src] = source_breakdown.get(src, 0) + 1

    quality_metrics = {}
    if stories:
        source_scores = []
        for s in stories:
            src = s.get("source", "hn")
            points = s.get("points", 0)
            if src == "hn":
                source_scores.append(min(points / 50.0, 2.0))
            elif src == "arxiv":
                source_scores.append(1.5)
            elif src == "pubmed":
                source_scores.append(1.8)
            else:
                source_scores.append(1.0)
        quality_metrics["avg_source_score"] = round(sum(source_scores) / len(source_scores), 3) if source_scores else 0
        total = len(stories)
        if total > 0:
            proportions = [c/total for c in source_breakdown.values() if c > 0]
            sum_squares = sum(p*p for p in proportions)
            quality_metrics["source_diversity"] = round(1.0 - sum_squares, 3)
        else:
            quality_metrics["source_diversity"] = 0.0
        now = datetime.now(timezone.utc)
        recency_scores = []
        for s in stories:
            try:
                story_date = datetime.strptime(s.get("created_at", "")[:10], "%Y-%m-%d")
                story_date = story_date.replace(tzinfo=timezone.utc)
                hours_old = (now - story_date).total_seconds() / 3600
                if hours_old < 6:
                    recency_scores.append(1.0)
                elif hours_old < 24:
                    recency_scores.append(0.5)
                elif hours_old < 72:
                    recency_scores.append(0.1)
                else:
                    recency_scores.append(0.0)
            except (ValueError, IndexError):
                recency_scores.append(0.0)
        quality_metrics["recency_score"] = round(sum(recency_scores) / len(recency_scores), 3) if recency_scores else 0

    body_parts = [
        trending_section,
        "",
        meta,
        "",
    ]
    if deep:
        body_parts.extend(["## Analysis", "", deep, ""])
    if cross:
        body_parts.extend([cross, ""])
    if edu_questions:
        body_parts.append("## Bloom Taxonomy Questions")
        for i, q in enumerate(edu_questions, 1):
            body_parts.append(f"{i}. **{level_label_en(q['bloom_level'])}**: {q['question']}")
        body_parts.append("")
    if edu_flashcards:
        body_parts.append("## Flashcards")
        for fc in edu_flashcards[:8]:
            body_parts.append(f"- **{fc['term']}**: {fc['definition']}")
        body_parts.append("")
    if confidence:
        body_parts.extend(["## Classification quality", "", confidence, ""])
    body_parts.append(f"*Report generated {date_str}. Source: Algolia HN API. Classification: AcaciaFund NLP. SQI: {signals.get('avg_sqi', 0):.3f}.*")

    body_md = "\n".join(body_parts)
    body_html = markdown2.markdown(body_md, extras=['fenced-code-blocks', 'tables'])
    slug = f"blog/{date_str}-{pillar_name}"

    return AcaciaContent(
        slug=slug,
        language="en",
        title=page_title,
        description=meta.replace(">", "").strip()[:200] if meta else "",
        body_html=body_html,
        category="blog",
        tags=config.get("tags", []),
        pillar=pillar_name,
        date_str=date_str,
        thumbnail_svg=thumb_svg,
        og_svg=og_svg,
        trending_html=trending_section,
        analysis_html=deep,
        cross_pillar_html=cross,
        bloom_questions=[dict(q) for q in edu_questions],
        flashcards=[dict(fc) for fc in edu_flashcards],
        signals=signals,
        source_breakdown=source_breakdown,
        quality_metrics=quality_metrics,
        quality_flags=["has_trending" if signals.get("trending_topics") else "no_trending"],
    )


def walk_existing_content() -> list[AcaciaContent]:
    blog_root = CONTENT_ROOT / "en" / "blog"
    if not blog_root.exists():
        log("No content/en/blog/ directory found", ok=False)
        return []

    records = []
    for post_dir in sorted(blog_root.iterdir()):
        if not post_dir.is_dir() or post_dir.name.startswith("."):
            continue
        md_file = post_dir / "index.md"
        if not md_file.exists():
            continue
        try:
            raw = md_file.read_text(encoding="utf-8")
        except Exception:
            continue
        if not raw.startswith("---"):
            continue
        parts = raw.split("---", 2)
        if len(parts) < 3:
            continue
        frontmatter_text = parts[1]
        body = parts[2].strip()

        try:
            import yaml
            metadata = yaml.safe_load(frontmatter_text) or {}
        except Exception:
            metadata = {}
        if not isinstance(metadata, dict):
            metadata = {}

        title = str(metadata.get("title", ""))
        if not title:
            continue

        categories = metadata.get("categories", [])
        if isinstance(categories, str):
            categories = [categories]
        pillar_raw = categories[0].lower() if categories else ""
        pillar_map = {"aml": "aml", "markets": "stock", "science": "science", "stock": "stock"}
        pillar = pillar_map.get(pillar_raw, pillar_raw)

        tags = metadata.get("tags", [])
        if isinstance(tags, str):
            tags = [tags]

        date_val = metadata.get("date", "")
        date_str = str(date_val)[:10] if date_val else ""

        html = markdown2.markdown(body, extras=['fenced-code-blocks', 'tables'])
        plain = re.sub(r'<[^>]+>', '', html)
        description = plain.strip()[:200]

        slug = f"blog/{post_dir.name}"

        records.append(AcaciaContent(
            slug=slug,
            language="en",
            title=title,
            description=description,
            body_html=html,
            category="blog",
            tags=tags,
            pillar=pillar,
            date_str=date_str,
        ))

    return records


def main():
    parser = argparse.ArgumentParser(description="AcaciaFund Orchestrator")
    parser.add_argument("--ingest", action="store_true", help="Run ingest pipeline (fetch HN/arXiv)")
    parser.add_argument("--from-content", action="store_true", help="Build registry from existing content/")
    args = parser.parse_args()

    print("Starting AcaciaFund orchestrator...")
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    content_list: List[AcaciaContent] = []

    if args.ingest:
        print("Running ingest pipeline...")
        all_stories = fetch_hn_stories(since_hours=48, min_points=2)
        log(f"Fetched {len(all_stories)} stories from HN")

        if not all_stories:
            log("No data from HN -- exiting", ok=False)
            return 1

        pillar_stories: dict[str, list[dict]] = {p: [] for p in PILLARS}
        unclassified = 0
        for story in all_stories:
            classifications = classify_story(story)
            if not classifications:
                unclassified += 1
                continue
            best = max(classifications, key=lambda x: x[1])
            pillar_stories[best[0]].append(story)

        log(f"AML={len(pillar_stories['aml'])}, STOCK={len(pillar_stories['stock'])}, "
            f"SCIENCE={len(pillar_stories['science'])}, unclassified={unclassified}")

        arxiv_papers = fetch_arxiv(since_hours=72)
        log(f"Fetched {len(arxiv_papers)} arXiv papers")
        for paper in arxiv_papers:
            p = paper["pillar"]
            pillar_stories[p].append({
                "title": paper["title"], "url": paper["url"], "hn_url": "",
                "points": 0, "created_at": paper["published"],
                "author": "arXiv", "object_id": "", "source": "arxiv"
            })

        for p in PILLARS:
            hn = [s for s in pillar_stories[p] if s.get("points", 0) > 0]
            arx = [s for s in pillar_stories[p] if s.get("points", 0) == 0]
            hn.sort(key=lambda s: s["points"], reverse=True)
            pillar_stories[p] = hn[:25] + arx[:5]

        for pillar_name, config in PILLARS.items():
            content = generate_post_content(
                pillar_name, config, pillar_stories[pillar_name],
                pillar_stories, all_stories, unclassified, run_id
            )
            if content:
                content_list.append(content)

    if args.from_content or not args.ingest:
        existing = walk_existing_content()
        content_list.extend(existing)
        log(f"Loaded {len(existing)} items from existing content/")
    if args.ingest:
        existing = walk_existing_content()
        existing_slugs = {c.slug for c in content_list}
        for c in existing:
            if c.slug not in existing_slugs:
                content_list.append(c)
        log(f"Appended {len(existing)} existing items (deduplicated)")

    if not content_list:
        log("No content generated -- exiting", ok=False)
        return 1

    registry = RegistryData(
        last_run=datetime.now(timezone.utc),
        content=content_list,
        pipeline_stages=[
            PipelineStage(id="bronze", title="Bronze Layer", description="Raw data ingestion from external sources."),
            PipelineStage(id="silver", title="Silver Layer", description="Cleaned and validated data ready for analysis."),
            PipelineStage(id="gold", title="Gold Layer", description="Actionable insights and final products."),
        ],
        mcp_integrations=[
            MCPIntegration(name="GitHub", status="active", description="Version control and collaboration."),
            MCPIntegration(name="Hugging Face", status="active", description="Access to AI models and datasets."),
            MCPIntegration(name="Weaviate", status="planned", description="Vector storage for semantic search."),
        ],
        planned_features=[
            PlannedFeature(name="AI Research Assistant", description="An AI agent to help navigate and synthesize research."),
            PlannedFeature(name="Real-time Alerts", description="Get notified when new signals are detected."),
        ],
    )

    with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
        json.dump(registry.model_dump() if hasattr(registry, 'model_dump') else registry.dict(), f, indent=2, default=str)
    log(f"Registry written to {REGISTRY_PATH} with {len(content_list)} items")

    if args.ingest:
        for content in content_list:
            if content.thumbnail_svg:
                thumb_path = STATIC_IMAGES_DIR / f"thumb_{hashlib.md5(content.title.encode()).hexdigest()[:12]}.svg"
                thumb_path.parent.mkdir(parents=True, exist_ok=True)
                thumb_path.write_text(content.thumbnail_svg, encoding="utf-8")
            if content.og_svg:
                og_path = STATIC_IMAGES_DIR / f"og_{hashlib.md5(content.title.encode()).hexdigest()[:12]}.svg"
                og_path.parent.mkdir(parents=True, exist_ok=True)
                og_path.write_text(content.og_svg, encoding="utf-8")

    return 0


if __name__ == "__main__":
    exit(main())
