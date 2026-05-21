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

    total_score = sum(s["points"] for s in pillar_stories)
    avg_score = round(total_score / len(pillar_stories), 1) if pillar_stories else 0
    max_score = max((s["points"] for s in pillar_stories), default=0)
    link_count = len(pillar_stories)

    sqi_val = analysis.get("avg_sqi", 0)

    trending_header = f"## 🔍 Trending (HackerNews, {date_str})"
    lines = [
        "---",
        f'title: "Synteza {config["emoji"]} {config["label"]} — {date_str}"',
        f"date: {date_str}",
        f'tags: {json.dumps(config["tags"])}',
        f'theme: "AcaciaFund — {config["description"]}"',
        "---",
        "",
        '<div class="metrics">',
        f'<div class="metric gold"><div class="value">{total_score}</div><div class="label">⭐ Suma</div></div>',
        f'<div class="metric"><div class="value">{avg_score}</div><div class="label">📊 Średnia</div></div>',
        f'<div class="metric"><div class="value">{max_score}</div><div class="label">🏆 Max</div></div>',
        f'<div class="metric"><div class="value">{link_count}</div><div class="label">🔗 Linki</div></div>',
        f'<div class="metric"><div class="value">{sqi_val:.2f}</div><div class="label">📡 SQI</div></div>',
        "</div>",
        "",
        trending_header,
        "",
        analysis["trending"],
        "",
        '<div class="insight" style="border-left-color:var(--gold)">',
        '<h3 style="font-size:.85rem;font-weight:700;text-transform:uppercase;letter-spacing:.04em;color:var(--gold);margin:0 0 8px">⚡ Kluczowe</h3>',
        f"<p>{max_score} ⭐ to najwyższa ocena w tym oknie. Średnia: {avg_score} ⭐. Łącznie {total_score} ⭐ z {link_count} linków.</p>",
        "</div>",
        "",
        '<div class="insight" style="border-left-color:#3B6999">',
        '<h3 style="font-size:.85rem;font-weight:700;text-transform:uppercase;letter-spacing:.04em;color:#3B6999;margin:0 0 8px">📊 Metaanaliza</h3>',
        analysis["metaanalysis"],
        "</div>",
        "",
        '<div class="insight">',
        '<h3 style="font-size:.85rem;font-weight:700;text-transform:uppercase;letter-spacing:.04em;color:var(--gold);margin:0 0 8px">🧠 Systems Thinking</h3>',
        analysis["systems_lens"],
        "</div>",
        "",
        '<div class="insight" style="border-left-color:var(--navy-mid)">',
        '<h3 style="font-size:.85rem;font-weight:700;text-transform:uppercase;letter-spacing:.04em;color:var(--navy-mid);margin:0 0 8px">🔗 Cross-Pillar Atlas</h3>',
        analysis["connections"],
        "</div>",
        "",
        '<div class="insight" style="border-left-color:var(--gold)">',
        '<h3 style="font-size:.85rem;font-weight:700;text-transform:uppercase;letter-spacing:.04em;color:var(--gold);margin:0 0 8px">📡 Signal Quality Index</h3>',
        analysis["signal_quality"],
        "</div>",
        "",
        "---",
        f"*Raport wygenerowano {date_str}. Źródło: Algolia HN API. Klasyfikacja: AcaciaFund NLP.*",
    ]

    config["folder"].mkdir(parents=True, exist_ok=True)
    filepath.write_text("\n".join(lines) + "\n", encoding="utf-8")
    log(f"Wygenerowano: {filepath.relative_to(BASE_DIR)} ({link_count} linków)")
    return filepath
