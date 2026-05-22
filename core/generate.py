import json
from datetime import datetime
from pathlib import Path
from collections import Counter

from .data import PILLARS, BASE_DIR, log
from .analyze import (
    build_analysis, classify_bloom_level_enhanced, detect_trending_topics,
    build_pillar_signals, compute_cross_pillar_scores,
)
from .bloom import (
    level_label_pl, generate_quiz_questions, generate_flashcards,
)
from .scraper import scrape_articles, _url_key

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
                  _unclassified: int = 0) -> Path | None:
    """Generate an enhanced post with deep analysis sections."""
    date = date or datetime.now()
    date_str = date.strftime("%Y-%m-%d")
    filename = f"{date_str}-{pillar_name}.md"
    filepath = config["folder"] / filename

    if filepath.exists():
        log(f"Post juz istnieje: {filename} dla {pillar_name} -- pomijam")
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

    lines = [
        "---",
        f'title: "{page_title}"',
        f"date: {date_str}",
        "draft: false",
        "author: \"AcaciaFund\"",
        f"categories: [\"{category}\"]",
        f"tags: {json.dumps(config['tags'])}",
        "type: \"post\"",
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

    config["folder"].mkdir(parents=True, exist_ok=True)
    filepath.write_text("\n".join(lines) + "\n", encoding="utf-8")
    log(f"Wygenerowano: {filepath.relative_to(BASE_DIR)} ({link_count} linkow, SQI={signals.get('avg_sqi', 0):.3f})")
    return filepath
