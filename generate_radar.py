#!/usr/bin/env python3
"""AcaciaFund Radar — generuje dashboard trendów + Atlas połączeń między filarami."""

import json
import re
import os
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).parent
CONTENT_DIR = BASE_DIR / "content" / "daily"
OUTPUT_DIR = BASE_DIR / "content" / "radar"
OUTPUT_FILE = OUTPUT_DIR / "_index.md"

PILLAR_EMOJI = {"aml": "🛡️", "stock": "📈", "science": "🧬"}
PILLAR_LABEL = {"aml": "AML", "stock": "Markets", "science": "Science"}

STOP_WORDS = {
    "the","a","an","of","in","to","for","and","is","on","that","with",
    "from","by","at","its","it","as","are","be","has","have","was",
    "were","new","how","why","what","show","ask","this","we","our",
    "their","they","not","no","but","all","about","up","out","over",
    "after","into","than","then","also","just","more","these","those",
    "can","will","does","been","some","them","than","very","when",
}


def parse_content_files() -> dict[str, list[dict[str, Any]]]:
    """Read all synthesis markdown files and extract metadata."""
    data: dict[str, list[dict]] = {"aml": [], "stock": [], "science": []}

    for pillar in data:
        pillar_dir = CONTENT_DIR / pillar
        if not pillar_dir.exists():
            continue
        for fpath in sorted(pillar_dir.glob("2026-*.md")):
            text = fpath.read_text(encoding="utf-8")
            # extract frontmatter
            m = re.search(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
            if not m:
                continue
            fm = dict(re.findall(r'^(\w+):\s*(.+)$', m.group(1), re.MULTILINE))
            date_str = fm.get("date", fpath.stem)
            # extract links with scores
            scores = [int(s) for s in re.findall(r"⭐(\d+)", text)]
            # extract titles
            titles = re.findall(r"\]\(https?://", text)
            link_count = len(titles)
            # extract thematic words
            body = text[m.end():]
            words = re.findall(r"\b[A-Z][a-z]{3,}\b", body)
            themes = [w for w in words if w.lower() not in STOP_WORDS and len(w) > 3]

            data[pillar].append({
                "date": date_str,
                "score_avg": round(sum(scores) / len(scores), 1) if scores else 0,
                "score_max": max(scores) if scores else 0,
                "score_total": sum(scores),
                "link_count": link_count,
                "themes": themes,
                "slug": fpath.stem,
            })

    return data


def find_connections(data: dict) -> list[dict]:
    """Find days where same keyword appears in multiple pillars."""
    dates: dict[str, dict[str, set]] = {}
    for pillar, posts in data.items():
        for p in posts:
            d = p["date"]
            if d not in dates:
                dates[d] = {}
            dates[d][pillar] = set(w.lower() for w in p["themes"])

    connections = []
    for date_str, pillars in sorted(dates.items()):
        pillars_list = list(pillars.keys())
        for i in range(len(pillars_list)):
            for j in range(i + 1, len(pillars_list)):
                p1, p2 = pillars_list[i], pillars_list[j]
                shared = pillars[p1] & pillars[p2]
                if shared:
                    connections.append({
                        "date": date_str,
                        "pillars": f"{PILLAR_EMOJI.get(p1,p1)} + {PILLAR_EMOJI.get(p2,p2)}",
                        "keywords": list(shared)[:5],
                        "count": len(shared),
                    })
    return connections


def build_html(data: dict) -> str:
    connections = find_connections(data)
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Prepare Chart.js datasets
    all_dates = sorted({p["date"] for posts in data.values() for p in posts})
    chart_data = {
        "labels": all_dates,
        "datasets": [
            {
                "label": f'{PILLAR_EMOJI[p]} {PILLAR_LABEL[p]}',
                "data": [sum(
                    post["score_total"] for post in posts if post["date"] == d
                ) for d in all_dates],
                "borderColor": ["#2E86AB", "#F18F01", "#A23B72"][i],
                "backgroundColor": ["#2E86AB20", "#F18F0120", "#A23B7220"][i],
                "fill": True,
                "tension": 0.3,
            }
            for i, (p, posts) in enumerate(data.items()) if posts
        ],
    }

    # Build keyword tables per pillar
    pillar_keywords = {}
    for p, posts in data.items():
        c = Counter()
        for post in posts:
            c.update(w.lower() for w in post["themes"])
        pillar_keywords[p] = c.most_common(20)

    lines = [
        "---",
        'title: "📊 Acacia Radar — Trendy i Połączenia"',
        f'date: {datetime.now().strftime("%Y-%m-%d")}',
        'layout: "radar"',
        "---",
        "",
        f"*Ostatnia aktualizacja: {now} UTC*",
        "",
        "## 📈 Aktywność w czasie",
        "",
        "Suma punktów (⭐) ze wszystkich znalezisk HackerNews w podziale na filary.",
        "",
        '<canvas id="trendChart" width="800" height="350"></canvas>',
        "",
        "## 🔗 Połączenia między filarami (Atlas)",
        "",
        "Dni, w których ten sam temat pojawił się w dwóch lub trzech filarach jednocześnie.",
        "",
    ]

    if connections:
        lines.append('<table style="width:100%;border-collapse:collapse">')
        lines.append("<tr><th style='text-align:left;padding:8px;border-bottom:2px solid #1a1a2e'>Data</th><th style='text-align:left;padding:8px;border-bottom:2px solid #1a1a2e'>Połączenie</th><th style='text-align:left;padding:8px;border-bottom:2px solid #1a1a2e'>Wspólne tematy</th></tr>")
        for c in connections[:10]:
            kw = ", ".join(c["keywords"][:4])
            lines.append(f"<tr><td style='padding:8px;border-bottom:1px solid #ddd'>{c['date']}</td><td style='padding:8px;border-bottom:1px solid #ddd'>{c['pillars']}</td><td style='padding:8px;border-bottom:1px solid #ddd'>{kw}</td></tr>")
        lines.append("</table>")
    else:
        lines.append("*Brak wykrytych połączeń — zbyt mało danych.*")

    lines.append("")
    lines.append("## 🏷️ Dominujące tematy (ostatnie 30 dni)")
    lines.append("")

    for p in ["aml", "stock", "science"]:
        kw = pillar_keywords[p][:12]
        if not kw:
            continue
        lines.append(f"### {PILLAR_EMOJI[p]} {PILLAR_LABEL[p]}")
        tags = " ".join(f'<span class="tag" style="margin:2px;display:inline-block">{w}</span>' for w, _ in kw)
        lines.append(f"<p>{tags}</p>")
        lines.append("")

    # Embed chart data + Chart.js
    lines.extend([
        '<script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>',
        "<script>",
        "const ctx = document.getElementById('trendChart').getContext('2d');",
        f"const data = {json.dumps(chart_data)};",
        "new Chart(ctx, {",
        "  type: 'line',",
        "  data: data,",
        "  options: {",
        "    responsive: true,",
        "    plugins: { legend: { position: 'top' } },",
        "    scales: {",
        "      x: { ticks: { maxTicksLimit: 10 } },",
        "      y: { beginAtZero: true, title: { display: true, text: '⭐ suma punków' } }",
        "    }",
        "  }",
        "});",
        "</script>",
        "",
        "---",
        "*Radar generowany automatycznie przez `generate_radar.py`.*",
    ])

    return "\n".join(lines) + "\n"


def main():
    data = parse_content_files()
    total = sum(len(posts) for posts in data.values())
    print(f"[+] Radar: odczytano {total} postów ({', '.join(f'{p}={len(v)}' for p,v in data.items())})")

    html = build_html(data)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(html, encoding="utf-8")
    print(f"[+] Radar wygenerowany: {OUTPUT_FILE}")

    # also write JSON for API
    api_dir = BASE_DIR / "static" / "api"
    api_dir.mkdir(parents=True, exist_ok=True)
    api_data = {
        "generated": datetime.now().isoformat(),
        "connections": find_connections(data),
        "pillars": {
            p: [
                {"date": post["date"], "score_total": post["score_total"],
                 "score_avg": post["score_avg"], "link_count": post["link_count"]}
                for post in posts
            ] for p, posts in data.items()
        },
    }
    (api_dir / "radar.json").write_text(json.dumps(api_data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[+] API JSON: static/api/radar.json")


if __name__ == "__main__":
    main()
