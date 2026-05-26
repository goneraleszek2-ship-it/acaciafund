import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path

from .data import PILLARS, BASE_DIR, log, STATIC_DIR
from .analyze import (
    build_analysis, classify_bloom_level_enhanced, detect_trending_topics,
    build_pillar_signals, compute_cross_pillar_scores,
)
from .metadata import (
    build_asset_manifest, build_story_manifest, write_json, iso_utc,
)
from .bloom import (
    level_label_pl, generate_quiz_questions, generate_flashcards,
)
from .scraper import scrape_articles, _url_key
from .visuals import (
    generate_thumbnail_svg, generate_og_image, generate_signal_meter,
    _pick_subtopic, TOPIC_ICONS, PILLAR_COLORS,
)
import urllib.request
import urllib.error

PILLAR_CATEGORY = {"aml": "AML", "stock": "Markets", "science": "Science"}


def _build_content_deep_analysis(pillar_stories: list[dict],
                                 scraped: dict[str, dict],
                                 pillar_name: str,
                                 signals: dict) -> str:
    """Generate a deep analysis section using scraped article content."""
    lines: list[str] = []
    entities = signals.get("top_entities", [])
    key_nums = signals.get("key_numbers", [])
    trending = signals.get("trending_topics", [])

    if entities:
        ent_str = " \u00b7 ".join(f"`{e}`" for e in entities[:6])
        lines.append(f"**Kluczowe podmioty:** {ent_str}")
    if key_nums:
        num_str = " \u00b7 ".join(f"{n[0]}" for n in key_nums[:4])
        lines.append(f"**Kluczowe liczby:** {num_str}")
    if trending:
        tr_str = " \u00b7 ".join(f"{t['word']} ({t['ratio']}x)" for t in trending[:4])
        lines.append(f"**Trendy:** {tr_str}")

    # Scraped insights from top stories
    content_sentences: list[str] = []
    for i, s in enumerate(pillar_stories[:5]):
        key = _url_key(s.get("url", ""))
        cached = scraped.get(key, {})
        facts = cached.get("facts", {})
        if facts:
            sentences = facts.get("sentences", [])
            names = facts.get("names", [])
            if sentences:
                best = max(sentences[:5], key=len)[:120]
                content_sentences.append(f"- {best}")
            if names:
                pass

    if content_sentences:
        lines.append("**Z artykułów:**")
        lines.extend(content_sentences[:3])

    return "\n".join(lines) if lines else ""


def _build_cross_pillar_section(pillar_name: str,
                                all_pillar_stories: dict[str, list[dict]]) -> str:
    """Find cross-pillar connections for today's stories."""
    if not all_pillar_stories:
        return ""

    connections: list[str] = []
    this_pillar_stories = all_pillar_stories.get(pillar_name, [])
    other_pillars = {p: s for p, s in all_pillar_stories.items() if p != pillar_name}

    for s in this_pillar_stories:
        cross = compute_cross_pillar_scores(s, all_pillar_stories)
        for p, score in cross.items():
            if score >= 4:
                label = PILLARS[p]["label"]
                connections.append(f"- \"{s['title'][:60]}\" ma powiązania z **{label}** (punkty: {score})")

    if connections:
        return "### 🔗 Połączenia międzyfilarowe\n" + "\n".join(connections[:4])
    return ""


def _build_classification_confidence(stories: list[dict], pillar_name: str,
                                     pillar_stories: list[dict],
                                     unclassified: int) -> str:
    """Compute and format classification confidence."""
    total = len(stories) + len(pillar_stories) + unclassified
    if total == 0:
        return ""
    classified = total - unclassified
    rate = classified / total * 100 if total > 0 else 0
    pillar_share = len(pillar_stories) / max(1, classified) * 100
    return f"Klasyfikacja: {rate:.0f}% ({classified}/{total}) | Udział filara: {pillar_share:.0f}%"


def _build_trending_section(pillar_stories: list[dict], signals: dict) -> str:
    """Build the trending articles section with SQI scores."""
    lines = []
    for i, s in enumerate(pillar_stories[:7]):
        line = f"{i+1}. [{s['title']}]({s['url']})"
        if s.get("hn_url") and s["hn_url"] != s["url"]:
            line += f" ([dyskusja]({s['hn_url']}))"
        line += f" (pkt {s['points']})"
        lines.append(line)
    return "\n".join(lines)


def generate_post(pillar_name: str, config: dict, pillar_stories: list[dict],
                  date: datetime | None = None,
                  all_pillar_stories: dict[str, list[dict]] | None = None,
                  _all_stories: list[dict] | None = None,
                  _unclassified: int = 0,
                  run_id: str | None = None) -> Path | None:
    """Generate an enhanced post with deep analysis sections."""
    date = date or datetime.now()
    date_str = date.strftime("%Y-%m-%d")
    # Use a Hugo Page Bundle for each post so images can be page resources
    bundle_name = f"{date_str}-{pillar_name}"
    post_dir = config["folder"] / bundle_name
    filepath = post_dir / "index.md"
    manifest_path = post_dir / "manifest.json"

    if filepath.exists() or post_dir.exists():
        log(f"Post juz istnieje: {bundle_name} dla {pillar_name} -- pomijam")
        return None

    # Scrape top articles for deep analysis
    urls_to_scrape = [s["url"] for s in pillar_stories[:6] if s.get("url")]
    scraped = scrape_articles(urls_to_scrape, max_scrape=6)

    analysis = build_analysis(pillar_stories, pillar_name, all_pillar_stories, scraped)
    signals = analysis.get("signals", {})

    link_count = len(pillar_stories)

    top_story = pillar_stories[0] if pillar_stories else None
    if top_story:
        raw = top_story["title"]
        short = raw[:80].rsplit(" ", 1)[0] if len(raw) > 80 else raw
        page_title = f"{short} -- {config['emoji']} {config['label']} {date_str}"
    else:
        page_title = f"Synteza {config['emoji']} {config['label']} -- {date_str}"

    page_title = page_title.replace('"', '').replace("'", '').replace("\\", '')

    category = PILLAR_CATEGORY.get(pillar_name, pillar_name.upper())

    # Bloom levels used today
    bloom_levels = sorted(
        {classify_bloom_level_enhanced(s) for s in pillar_stories},
        key=lambda l: ["remember", "understand", "apply", "analyze", "evaluate", "create"].index(l),
    )

    edu_questions = generate_quiz_questions(pillar_stories, config["label"], scraped)
    edu_flashcards = generate_flashcards(pillar_stories, config["label"])

    # Build sections
    trending_section = _build_trending_section(pillar_stories, signals)
    meta = analysis.get("metaanalysis", "")
    confidence = _build_classification_confidence(
        _all_stories or [], pillar_name, pillar_stories, _unclassified
    )

    # Generate visuals (before frontmatter so we can reference the thumbnail path)
    thumb_filename = ""
    og_filename = ""
    try:
        avg_sqi = signals.get("avg_sqi", 0.5)
        thumb_title = top_story["title"] if top_story else page_title
        # Thumbnail SVG
        thumb_svg = generate_thumbnail_svg(thumb_title, pillar_name, {"sqi": avg_sqi})
        thumb_key = hashlib.md5(thumb_title.encode()).hexdigest()[:12]
        thumb_filename = f"thumb_{thumb_key}.svg"
        # write thumbnail into the page bundle so Hugo can treat it as a Page Resource
        post_dir.mkdir(parents=True, exist_ok=True)
        thumb_path = post_dir / thumb_filename
        thumb_path.write_text(thumb_svg, encoding="utf-8")
        # OG Image SVG (also written into the bundle)
        og_svg = generate_og_image(thumb_title, pillar_name, {"sqi": avg_sqi}, date_str)
        og_key = hashlib.md5(f"og_{thumb_title}".encode()).hexdigest()[:12]
        og_filename = f"og_{og_key}.svg"
        og_path = post_dir / og_filename
        og_path.write_text(og_svg, encoding="utf-8")
        log(f"Wizualizacje (bundle): {post_dir}/{thumb_filename}, {og_filename}")
    except Exception as e:
        log(f"Blad generowania wizualizacji: {e}", ok=False)
        avg_sqi = signals.get("avg_sqi", 0.5)

    # When using page bundles, reference the resource by filename (Hugo Page Resource)
    thumbnail_url = f"{thumb_filename}" if thumb_filename else ""

    def _download_image(url: str, dest: Path) -> bool:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "AcaciaFund/3.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = resp.read()
            dest.write_bytes(data)
            return True
        except (urllib.error.HTTPError, urllib.error.URLError, OSError):
            return False

    lines = [
        "---",
        f'title: "{page_title}"',
        f"date: {date_str}",
        "draft: false",
        "author: \"AcaciaFund\"",
        f"categories: [\"{category}\"]",
        f"tags: {json.dumps(config['tags'])}",
        "type: \"post\"",
    ]
    if thumbnail_url:
        lines.append(f'thumbnail: "{thumbnail_url}"')
    if og_filename:
        lines.append(f'og_image: "{og_filename}"')
    lines += [
        "---",
        "",
        f"## \U0001f50d Trending (HackerNews, {date_str})",
        "",
        trending_section,
        "",
        "> **Podsumowanie**",
        f">{meta.replace(chr(10), chr(10)+'>')}",
        "",
    ]

    # Deep analysis section
    deep = _build_content_deep_analysis(pillar_stories, scraped, pillar_name, signals)
    if deep:
        lines.extend([
            "## \U0001f4ca Analiza",
            "",
            deep,
            "",
        ])

    # Cross-pillar section
    cross = _build_cross_pillar_section(pillar_name, all_pillar_stories)
    if cross:
        lines.extend([cross, ""])

    # Trending topics
    trending = signals.get("trending_topics", [])
    if trending:
        lines.append("## \U0001f4c8 Trendy")
        for t in trending:
            lines.append(f"- **{t['word']}**: {t['ratio']}x wiecej niz srednia ({t['avg_daily']}/dzien)")
        lines.append("")

    # Bloom taxonomy questions
    if edu_questions:
        lines.append("## \U0001f9e0 Pytania Bloom Taxonomy")
        for i, q in enumerate(edu_questions, 1):
            lines.append(f"{i}. **{level_label_pl(q['bloom_level'])}**: {q['question']}")
        lines.append("")

    # Flashcards
    if edu_flashcards:
        lines.append("## \U0001f4da Fiszki")
        for fcard in edu_flashcards[:8]:
            lines.append(f"- **{fcard['term']}**: {fcard['definition']}")
        lines.append("")

    # Embedded thumbnail in post body (Hugo will resolve Page Resources)
    if thumbnail_url:
        lines.extend([
            "> ![](" + thumbnail_url + ")",
            "",
        ])

    # If we scraped an explicit image for the top_story, try to download it into the bundle
    if top_story:
        key = _url_key(top_story.get("url", ""))
        scraped_entry = scraped.get(key, {})
        img_url = scraped_entry.get("image") if scraped_entry else None
        if img_url:
            # Handle relative URLs by making them absolute using the article's domain
            if img_url.startswith('/'):
                from urllib.parse import urlparse
                article_url = top_story.get("url", "")
                if article_url:
                    parsed = urlparse(article_url)
                    base_url = f"{parsed.scheme}://{parsed.netloc}"
                    img_url = base_url + img_url
                else:
                    # If we can't determine the base URL, skip the download
                    log(f"Skipping image download: no base URL for relative path {img_url}", ok=False)
                    img_url = None
            
            if img_url:  # Only proceed if we have a valid URL
                # determine extension
                ext = ".jpg"
                if img_url.lower().endswith(".png"):
                    ext = ".png"
                elif img_url.lower().endswith(".webp"):
                    ext = ".webp"
                elif img_url.lower().endswith(".gif"):
                    ext = ".gif"
                feat_name = f"featured{ext}"
                feat_path = post_dir / feat_name
                ok = _download_image(img_url, feat_path)
                if ok:
                    # insert featured_image into frontmatter before the closing '---'
                    # find the second '---' which marks end of frontmatter
                    try:
                        # skip the first '---' at index 0
                        second_idx = next(i for i, v in enumerate(lines) if v == '---' and i != 0)
                    except StopIteration:
                        second_idx = 0
                    if second_idx:
                        lines.insert(second_idx, f'featured_image: "{feat_name}"')

    # Emit metadata alongside the page bundle.
    assets = []
    content_id = bundle_name
    source_urls = [s.get("url", "") for s in pillar_stories if s.get("url")]
    
    # Calculate source breakdown
    source_breakdown = {"hn": 0, "arxiv": 0, "pubmed": 0}
    for story in pillar_stories:
        source = story.get("source", "hn")  # Default to HN for backward compatibility
        if source in source_breakdown:
            source_breakdown[source] += 1
        else:
            # Handle any unexpected sources
            source_breakdown[source] = source_breakdown.get(source, 0) + 1
    
    # Calculate quality metrics
    quality_metrics = {}
    if pillar_stories:
        # Calculate average source score (simplified)
        source_scores = []
        for story in pillar_stories:
            source = story.get("source", "hn")
            # Simple scoring: HN points normalized, arXiv/PubMed get base scores
            if source == "hn":
                points = story.get("points", 0)
                score = min(points / 50.0, 2.0)  # Normalize HN points to 0-2 range
            elif source == "arxiv":
                score = 1.5  # arXiv gets high base score
            elif source == "pubmed":
                score = 1.8  # PubMed gets highest base score (peer-reviewed)
            else:
                score = 1.0
            source_scores.append(score)
        quality_metrics["avg_source_score"] = sum(source_scores) / len(source_scores) if source_scores else 0
        
        # Source diversity (entropy-like measure)
        total = len(pillar_stories)
        if total > 0:
            proportions = [count/total for count in source_breakdown.values() if count > 0]
            # Simple diversity: 1 - (sum of squares) - ranges 0 to ~0.67 for 3 sources
            sum_squares = sum(p*p for p in proportions)
            quality_metrics["source_diversity"] = 1.0 - sum_squares
        else:
            quality_metrics["source_diversity"] = 0.0
            
        # Recency score (how recent are the sources)
        now = datetime.now(timezone.utc)
        recency_scores = []
        for story in pillar_stories:
            try:
                # Parse the date string (assuming YYYY-MM-DD format)
                story_date = datetime.strptime(story.get("created_at", ""), "%Y-%m-%d")
                story_date = story_date.replace(tzinfo=timezone.utc)
                hours_old = (now - story_date).total_seconds() / 3600
                # Score: 1.0 for <6h, 0.5 for 6-24h, 0.1 for 24-72h, 0.0 for >72h
                if hours_old < 6:
                    recency_scores.append(1.0)
                elif hours_old < 24:
                    recency_scores.append(0.5)
                elif hours_old < 72:
                    recency_scores.append(0.1)
                else:
                    recency_scores.append(0.0)
            except:
                recency_scores.append(0.0)  # Default if date parsing fails
        
        quality_metrics["recency_score"] = sum(recency_scores) / len(recency_scores) if recency_scores else 0
    else:
        quality_metrics = {"avg_source_score": 0, "source_diversity": 0, "recency_score": 0}
    
    if thumb_filename:
        assets.append(build_asset_manifest(content_id, "thumbnail", post_dir / thumb_filename, top_story.get("url", "") if top_story else ""))
    if og_filename:
        assets.append(build_asset_manifest(content_id, "og_image", post_dir / og_filename, top_story.get("url", "") if top_story else ""))
    if top_story:
        key = _url_key(top_story.get("url", ""))
        scraped_entry = scraped.get(key, {})
        img_url = scraped_entry.get("image") if scraped_entry else None
        if img_url:
            ext = ".jpg"
            if img_url.lower().endswith(".png"):
                ext = ".png"
            elif img_url.lower().endswith(".webp"):
                ext = ".webp"
            elif img_url.lower().endswith(".gif"):
                ext = ".gif"
            feat_name = f"featured{ext}"
            feat_path = post_dir / feat_name
            if feat_path.exists():
                assets.append(build_asset_manifest(content_id, "featured_image", feat_path, img_url))

    story_manifest = build_story_manifest(
        content_id=content_id,
        pillar=pillar_name,
        title=page_title,
        date=date_str,
        source_urls=source_urls,
        story_count=len(pillar_stories),
        signals=signals,
        bloom_levels=bloom_levels,
        questions_count=len(edu_questions),
        flashcards_count=len(edu_flashcards),
        assets=assets,
        lineage={
            "run_id": run_id or "",
            "top_story_url": top_story.get("url", "") if top_story else "",
            "source_count": len(_all_stories or []),
            "unclassified": _unclassified,
        },
        quality_flags=["has_trending" if signals.get("trending_topics") else "no_trending"],
        published_at=iso_utc(),
        source_breakdown=source_breakdown,
        quality_metrics=quality_metrics,
    )

    # Classification info
    if confidence:
        lines.extend([
            "## \U0001f9ea Jakosc klasyfikacji",
            "",
            confidence,
            "",
        ])

    lines += [
        "---",
        f"*Raport wygenerowano {date_str}. Zrodlo: Algolia HN API. Klasyfikacja: AcaciaFund NLP. SQI: {signals.get('avg_sqi', 0):.3f}.*",
    ]

    # Ensure folder exists (post_dir already created when writing images)
    config["folder"].mkdir(parents=True, exist_ok=True)
    filepath.write_text("\n".join(lines) + "\n", encoding="utf-8")
    write_json(manifest_path, story_manifest)
    log(f"Wygenerowano: {filepath.relative_to(BASE_DIR)} ({link_count} linkow, SQI={signals.get('avg_sqi', 0):.3f})")
    return filepath
