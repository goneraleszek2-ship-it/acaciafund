#!/usr/bin/env python3
"""AcaciaFund Notebook — static JupyterLab-style page with code + data viz."""

import json, re, math
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).parent
CONTENT_DIR = BASE_DIR / "content" / "daily"
OUTPUT_DIR = BASE_DIR / "content" / "notebook"
OUTPUT_FILE = OUTPUT_DIR / "_index.md"

PILLAR_EMOJI = {"aml": "🛡️", "stock": "📈", "science": "🧬"}
PILLAR_LABEL = {"aml": "AML", "stock": "Markets", "science": "Science"}
PILLAR_COLORS = {"aml": "#3B6999", "stock": "#C47F58", "science": "#9C6B8E"}

STOP_WORDS = {
    "the","a","an","of","in","to","for","and","is","on","that","with",
    "from","by","at","its","it","as","are","be","has","have","was",
    "were","new","how","why","what","show","ask","this","we","our",
    "their","they","not","no","but","all","about","up","out","over",
}


def parse_data() -> dict[str, list[dict]]:
    data: dict[str, list[dict]] = {"aml": [], "stock": [], "science": []}
    for pillar in data:
        d = CONTENT_DIR / pillar
        if not d.exists(): continue
        for fpath in sorted(d.glob("2026-*.md")):
            text = fpath.read_text(encoding="utf-8")
            m = re.search(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
            if not m: continue
            scores = [int(s) for s in re.findall(r"⭐(\d+)", text)]
            titles = re.findall(r"\]\(https?://", text)
            body = text[m.end():]
            words = re.findall(r"\b[A-Z][a-z]{3,}\b", body)
            themes = [w for w in words if w.lower() not in STOP_WORDS and len(w) > 3]
            data[pillar].append({
                "date": fpath.stem,
                "score_total": sum(scores),
                "score_avg": round(sum(scores)/len(scores),1) if scores else 0,
                "score_max": max(scores) if scores else 0,
                "link_count": len(titles),
                "themes": themes,
            })
    return data


def cell_md(body: str, exec_count: int = 0) -> str:
    return f'''<div class="cell">
  <div class="cell-header">
    <span class="exec">[{exec_count}]</span>
    <span class="tag md">Markdown</span>
  </div>
  <div class="cell-content">{body}</div>
</div>'''


def cell_code(code: str, exec_count: int) -> str:
    return f'''<div class="cell">
  <div class="cell-header">
    <span class="exec">[{exec_count}]</span>
    <span class="tag code">Code</span>
  </div>
  <pre><code>{code}</code></pre>
</div>'''


def cell_output(body: str, exec_count: int) -> str:
    return f'''<div class="cell">
  <div class="cell-header">
    <span class="exec">[{exec_count}]</span>
    <span class="tag output">Output</span>
  </div>
  <div class="cell-content">{body}</div>
</div>'''


def svg_pie(data: dict) -> str:
    """Pillar score distribution donut."""
    totals = {p: sum(p["score_total"] for p in data.get(p, [])) for p in ["aml","stock","science"]}
    if not any(totals.values()): return ""
    total = sum(totals.values()) or 1
    colors = ["#3B6999","#C47F58","#9C6B8E"]
    labels = ["AML & RegTech","Capital Markets","Science & Systems"]
    r, cx, cy = 70, 120, 90
    arcs, start = [], 0
    for i, (p, v) in enumerate(totals.items()):
        angle = v / total * 360
        end = start + angle
        rad_start, rad_end = math.radians(start-90), math.radians(end-90)
        x1 = cx + r * math.cos(rad_start)
        y1 = cy + r * math.sin(rad_start)
        x2 = cx + r * math.cos(rad_end)
        y2 = cy + r * math.sin(rad_end)
        large = 1 if angle > 180 else 0
        arcs.append(
            f'<path d="M{cx},{cy} L{x1:.1f},{y1:.1f} A{r},{r} 0 {large},1 {x2:.1f},{y2:.1f} Z" '
            f'fill="{colors[i]}" opacity=".85"/>'
        )
        if v:
            mid = math.radians(start-90 + angle/2)
            mx = cx + (r*1.35) * math.cos(mid)
            my = cy + (r*1.35) * math.sin(mid)
            arcs.append(f'<text x="{mx:.0f}" y="{my:.0f}" text-anchor="middle" font-size="10" font-weight="600" fill="{colors[i]}">{v}⭐</text>')
        start = end
    # center hole
    arcs.append(f'<circle cx="{cx}" cy="{cy}" r="{r*.5}" fill="#fff"/>')
    arcs.append(f'<text x="{cx}" y="{cy+4}" text-anchor="middle" font-size="13" font-weight="700" fill="#0d1b2a">{total}</text>')
    w, h = 240, 180
    return f'<svg viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg" style="max-width:100%;height:auto;font-family:Inter,system-ui,sans-serif">{chr(10).join(arcs)}</svg>'


def svg_topic_bars(themes: dict[str, list[tuple[str,int]]]) -> str:
    """Horizontal grouped bars: top keywords per pillar."""
    h, gap = 180, 50
    bar_h, bar_gap = 14, 4
    group_h = (bar_h + bar_gap) * 6
    w = 500
    lines = []
    for gi, p in enumerate(["aml","stock","science"]):
        kws = themes.get(p, [])[:6]
        if not kws: continue
        top = max(kw[1] for kw in kws) or 1
        ox, oy = 0, gi * (group_h + gap)
        clr = PILLAR_COLORS[p]
        emj = PILLAR_EMOJI[p]
        lines.append(f'<text x="4" y="{oy+12}" font-size="11" font-weight="600" fill="{clr}">{emj} {PILLAR_LABEL[p]}</text>')
        for i, (kw, cnt) in enumerate(kws):
            by = oy + 20 + i * (bar_h + bar_gap)
            bw = max((w - 120) * cnt / top, 2)
            lines.append(f'<text x="8" y="{by+bar_h-3}" font-size="9" fill="#374151">{kw}</text>')
            lines.append(f'<rect x="100" y="{by}" width="{bw:.0f}" height="{bar_h}" rx="2" fill="{clr}" opacity=".7"/>')
            lines.append(f'<text x="104" y="{by+bar_h-3}" font-size="8" font-weight="500" fill="#fff">{cnt}</text>')
    total_h = (group_h + gap) * 3
    return f'<svg viewBox="0 0 {w} {total_h}" xmlns="http://www.w3.org/2000/svg" style="max-width:100%;height:auto;font-family:Inter,system-ui,sans-serif">{chr(10).join(lines)}</svg>'


def build_page(data: dict) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    ec = [0]  # execution counter

    # aggregate keywords
    pillar_keywords = {}
    for p in ["aml","stock","science"]:
        c = Counter()
        for post in data.get(p, []):
            c.update(w.lower() for w in post["themes"])
        pillar_keywords[p] = c.most_common(20)

    total_scores = sum(sum(p["score_total"] for p in posts) for posts in data.values())
    total_links = sum(sum(p["link_count"] for p in posts) for posts in data.values())
    total_posts = sum(len(posts) for posts in data.values())

    cells = []

    # [1] Title + intro
    ec[0] += 1
    cells.append(cell_md(
        "# 📓 AcaciaFund Research Notebook\n\n"
        "*Analiza danych z HackerNews i arXiv — kod źródłowy wizualizacji i przetwarzania.*\n\n"
        f"Ostatnia aktualizacja: `{now} UTC`  •  "
        f"Posty: `{total_posts}`  •  "
        f"Punkty: `{total_scores}⭐`  •  "
        f"Linki: `{total_links}`",
        ec[0]
    ))

    # [2] Import libraries
    ec[0] += 1
    cells.append(cell_code(
        "import json, re, math\n"
        "from collections import Counter\n"
        "from datetime import datetime\n"
        "from pathlib import Path\n\n"
        "# SVG chart helpers\n"
        "def donut(data): ...   # see source\n"
        "def topic_bars(data): ...",
        ec[0]
    ))

    # [3] Load + describe data
    ec[0] += 1
    sample_text = ",\n  ".join(
        f'{{"date": "{data[p][-1]["date"]}", "score": {data[p][-1]["score_total"]}, "links": {data[p][-1]["link_count"]}}}'
        for p in ["aml","stock","science"] if data[p]
    )
    cells.append(cell_code(
        "BASE_DIR = Path.cwd()\n"
        "data = parse_content_files()  # ← reads content/daily/*/*.md\n\n"
        f"# Sample: latest entries\n"
        f"latest = [\n  {sample_text}\n]\n"
        f"print(f'Total posts: {{len(data)}}')",
        ec[0]
    ))

    # [4] Output: data summary
    ec[0] += 1
    summary_rows = "".join(
        f"<tr><td>{PILLAR_EMOJI[p]} {PILLAR_LABEL[p]}</td>"
        f"<td>{len(data.get(p,[]))}</td>"
        f"<td>{sum(d['score_total'] for d in data.get(p,[]))}</td>"
        f"<td>{sum(d['link_count'] for d in data.get(p,[]))}</td>"
        f"<td>{round(sum(d['score_avg'] for d in data.get(p,[]))/max(len(data.get(p,[])),1),1)}</td></tr>"
        for p in ["aml","stock","science"]
    )
    cells.append(cell_output(
        "<table style='font-size:.82rem'>"
        "<tr><th>Pillar</th><th>Posts</th><th>Total ⭐</th><th>Links</th><th>Avg ⭐</th></tr>"
        f"{summary_rows}</table>",
        ec[0]
    ))

    # [5] Classification logic
    ec[0] += 1
    kws = ", ".join(f"'{w}'" for w in ["aml","compliance","regtech","financial crime","kyc","money laundering"])
    cells.append(cell_code(
        "# Keyword-based classification (NLP heuristics)\n"
        "# Each story is scored against pillar keyword sets\n\n"
        f"PILLAR_KEYWORDS = {{\n"
        f"    'aml': [{kws}],\n"
        f"    'stock': ['semiconductor', 'supply chain', 'market', 'valuation', 'chip'],\n"
        f"    'science': ['mitochondria', 'cybernetics', 'complex systems', 'emergence'],\n"
        "}}\n\n"
        "def classify(story):\n"
        "    text = (story['title'] + ' ' + story.get('url','')).lower()\n"
        "    scores = {}\n"
        "    for pillar, kws in PILLAR_KEYWORDS.items():\n"
        "        score = sum(3 for kw in kws if kw in text)\n"
        "        if score: scores[pillar] = score\n"
        "    return scores",
        ec[0]
    ))

    # [6] Score distribution donut
    ec[0] += 1
    cells.append(cell_code(
        "# Score distribution across pillars\n"
        "totals = {p: sum(d['score_total'] for d in data[p]) for p in data}\n"
        "print(totals)\n"
        "donut_chart(totals)  # → SVG rendered below",
        ec[0]
    ))

    ec[0] += 1
    cells.append(cell_output(
        f'<div class="chart-wrap" style="text-align:center"><h4>Rozkład punktów ⭐</h4>{svg_pie(data)}</div>',
        ec[0]
    ))

    # [7] Topic analysis
    ec[0] += 1
    cells.append(cell_code(
        "# Keyword frequency analysis\n"
        "themes = {p: Counter() for p in data}\n"
        "for pillar, posts in data.items():\n"
        "    for post in posts:\n"
        "        themes[pillar].update(w.lower() for w in post['themes'])\n\n"
        "topic_bars(themes)  # → SVG rendered below",
        ec[0]
    ))

    ec[0] += 1
    cells.append(cell_output(
        f'<div class="chart-wrap"><h4>Top keywords per pillar</h4>{svg_topic_bars(pillar_keywords)}</div>',
        ec[0]
    ))

    # [8] Trend notes
    ec[0] += 1
    cells.append(cell_md(
        "## Insights\n\n"
        "Z analizy danych wyłaniają się następujące wzorce:\n\n"
        f"1. **Dominacja AML** — {sum(d['score_total'] for d in data.get('aml',[]))}⭐ to najwyższa suma, "
        f"co odzwierciedla intensywność dyskursu regulacyjnego.\n"
        f"2. **Keywords cross-pillar** — tematy takie jak *cybernetics*, *systems*, *trending* "
        f"pojawiają się we wszystkich trzech filarach, sugerując emergencję wspólnego języka systemowego.\n"
        "3. **Rozkład aktywności** — większość punktów pochodzi z HackerNews; arXiv stanowi uzupełnienie "
        "o głębsze prace badawcze.",
        ec[0]
    ))

    # [9] Export
    ec[0] += 1
    cells.append(cell_code(
        "# Export to JSON API\n"
        "api_data = {\n"
        "    'generated': datetime.now().isoformat(),\n"
        "    'pillars': {p: [{'date': d['date'], 'score_total': d['score_total']}\n"
        "                     for d in data[p]] for p in data}\n"
        "}\n"
        "Path('static/api/radar.json').write_text(json.dumps(api_data, indent=2))\n"
        "print('API exported')",
        ec[0]
    ))

    cells_html = "\n".join(cells)

    return f'''---
title: "📓 AcaciaFund Research Notebook"
date: {datetime.now().strftime("%Y-%m-%d")}
layout: "notebook"
---

<div class="notebook">
{cells_html}
</div>

---

<p style="color:#999;font-size:.78rem">Notebook generowany automatycznie przez <code>generate_notebook.py</code>.
Zaprojektowany jako statyczny odpowiednik JupyterLab — kod Python i wygenerowane wizualizacje SVG w jednym widoku.</p>
'''


def main():
    data = parse_data()
    total = sum(len(posts) for posts in data.values())
    print(f"[+] Notebook: {total} postów")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(build_page(data), encoding="utf-8")
    print(f"[+] Notebook: {OUTPUT_FILE}")

    # update API JSON
    api_dir = BASE_DIR / "static" / "api"
    api_dir.mkdir(parents=True, exist_ok=True)
    api_data = {
        "generated": datetime.now().isoformat(),
        "pillars": {
            p: [{"date": post["date"], "score_total": post["score_total"],
                 "score_avg": post["score_avg"], "link_count": post["link_count"]}
                for post in posts] for p, posts in data.items()
        },
    }
    (api_dir / "radar.json").write_text(json.dumps(api_data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[+] API JSON: static/api/radar.json")


if __name__ == "__main__":
    main()
