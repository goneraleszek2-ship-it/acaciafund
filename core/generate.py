import json
from datetime import datetime
from pathlib import Path

from .data import PILLARS, BASE_DIR, log
from .analyze import build_analysis
from .bloom import (
    classify_bloom_level, level_label_pl, generate_quiz_questions, generate_flashcards,
)

PILLAR_CATEGORY = {"aml": "AML", "stock": "Markets", "science": "Science"}


def generate_post(pillar_name: str, config: dict, pillar_stories: list[dict],
                  date: datetime | None = None,
                  all_pillar_stories: dict[str, list[dict]] | None = None) -> Path | None:
    date = date or datetime.now()
    date_str = date.strftime("%Y-%m-%d")
    filename = f"{date_str}-{pillar_name}.md"
    filepath = config["folder"] / filename

    if filepath.exists():
        log(f"Post już istnieje: {filename} dla {pillar_name} — pomijam")
        return None

    analysis = build_analysis(pillar_stories, pillar_name, all_pillar_stories)

    link_count = len(pillar_stories)

    top_story = pillar_stories[0] if pillar_stories else None
    if top_story:
        raw = top_story["title"]
        short = raw[:80].rsplit(" ", 1)[0] if len(raw) > 80 else raw
        page_title = f"{short} — {config['emoji']} {config['label']} {date_str}"
    else:
        page_title = f"Synteza {config['emoji']} {config['label']} — {date_str}"

    # Sanitize title for YAML
    page_title = page_title.replace('"', '').replace("'", '').replace('\\', '')

    trending_header = f"## 🔍 Trending (HackerNews, {date_str})"
    bloom_levels = sorted(
        {classify_bloom_level(s) for s in pillar_stories},
        key=lambda l: ["remember", "understand", "apply", "analyze", "evaluate", "create"].index(l),
    )

    edu_questions = generate_quiz_questions(pillar_stories, config["label"])
    edu_flashcards = generate_flashcards(pillar_stories, config["label"])

    category = PILLAR_CATEGORY.get(pillar_name, pillar_name.upper())

    lines = [
        "---",
        f"title: \"{page_title}\"",
        f"date: {date_str}",
        "draft: false",
        "image: \"\"",
        "author: \"AcaciaFund\"",
        f"categories: [\"{category}\"]",
        f"tags: {json.dumps(config['tags'])}",
        "type: \"post\"",
        "---",
        "",
        trending_header,
        "",
        analysis["trending"],
        "",
        "> 📊 **Podsumowanie**",
        f">{analysis['metaanalysis'].replace(chr(10), chr(10)+'>')}",
        "",
    ]

    if edu_questions:
        lines.append("## 🧠 Pytania do refleksji")
        for i, q in enumerate(edu_questions, 1):
            lines.append(f"{i}. **{level_label_pl(q['bloom_level'])}**: {q['question']}")
        lines.append("")

    if edu_flashcards:
        lines.append("## 📚 Fiszki")
        for fcard in edu_flashcards:
            lines.append(f"- **{fcard['term']}**: {fcard['definition']}")
        lines.append("")

    lines += [
        "---",
        f"*Raport wygenerowano {date_str}. Źródło: Algolia HN API. Klasyfikacja: AcaciaFund NLP.*",
    ]

    config["folder"].mkdir(parents=True, exist_ok=True)
    filepath.write_text("\n".join(lines) + "\n", encoding="utf-8")
    log(f"Wygenerowano: {filepath.relative_to(BASE_DIR)} ({link_count} linków)")
    return filepath
