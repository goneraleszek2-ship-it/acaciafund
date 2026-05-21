import json
from datetime import datetime
from pathlib import Path

from .data import PILLARS, BASE_DIR, log
from .analyze import build_analysis


def generate_post(pillar_name: str, config: dict, pillar_stories: list[dict],
                  date: datetime | None = None,
                  all_pillar_stories: dict[str, list[dict]] | None = None) -> Path | None:
    date = date or datetime.now()
    date_str = date.strftime("%Y-%m-%d")
    filename = f"{date_str}.md"
    filepath = config["folder"] / filename

    if filepath.exists():
        log(f"Post już istnieje: {filename} dla {pillar_name} — pomijam")
        return None

    analysis = build_analysis(pillar_stories, pillar_name, all_pillar_stories)

    link_count = len(pillar_stories)

    trending_header = f"## 🔍 Trending (HackerNews, {date_str})"
    lines = [
        "---",
        f'title: "Synteza {config["emoji"]} {config["label"]} — {date_str}"',
        f"date: {date_str}",
        f'tags: {json.dumps(config["tags"])}',
        f'theme: "AcaciaFund — {config["description"]}"',
        "---",
        "",
        trending_header,
        "",
        analysis["trending"],
        "",
        '<div class="insight" style="border-left-color:#3B6999">',
        '<h3 style="font-size:.85rem;font-weight:700;text-transform:uppercase;letter-spacing:.04em;color:#3B6999;margin:0 0 8px">📊 Podsumowanie</h3>',
        analysis["metaanalysis"],
        "</div>",
        "",
        "---",
        f"*Raport wygenerowano {date_str}. Źródło: Algolia HN API. Klasyfikacja: AcaciaFund NLP.*",
    ]

    config["folder"].mkdir(parents=True, exist_ok=True)
    filepath.write_text("\n".join(lines) + "\n", encoding="utf-8")
    log(f"Wygenerowano: {filepath.relative_to(BASE_DIR)} ({link_count} linków)")
    return filepath
