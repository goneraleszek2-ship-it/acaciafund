#!/usr/bin/env python3
"""AcaciaFund Radar — McKinsey dashboard + Biecek-style SVG charts."""

import json
import re
import math
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).parent
CONTENT_DIR = BASE_DIR / "content" / "daily"
OUTPUT_DIR = BASE_DIR / "content" / "radar"
OUTPUT_FILE = OUTPUT_DIR / "_index.md"

PILLAR_EMOJI = {"aml": "🛡️", "stock": "📈", "science": "🧬"}
PILLAR_LABEL = {"aml": "AML & RegTech", "stock": "Capital Markets", "science": "Science & Systems"}
PILLAR_COLORS = {"aml": "#3B6999", "stock": "#C47F58", "science": "#9C6B8E"}
PILLAR_COLORS_LIGHT = {"aml": "#d6e3ef", "stock": "#edd9c8", "science": "#dccdd8"}
PLOT_BG = "#f8f8f8"

STOP_WORDS = {
    "the","a","an","of","in","to","for","and","is","on","that","with",
    "from","by","at","its","it","as","are","be","has","have","was",
    "were","new","how","why","what","show","ask","this","we","our",
    "their","they","not","no","but","all","about","up","out","over",
    "after","into","than","then","also","just","more","these","those",
    "can","will","does","been","some","them","than","very","when",
    "are","but","not","the","you","all","can","had","her","was",
    "one","our","out","has","have","been","some","them","than",
    "very","just","also","more","these","those","now","over",
}


def parse_content_files() -> dict[str, list[dict[str, Any]]]:
    data: dict[str, list[dict]] = {"aml": [], "stock": [], "science": []}
    for pillar in data:
        pillar_dir = CONTENT_DIR / pillar
        if not pillar_dir.exists():
            continue
        for fpath in sorted(pillar_dir.glob("2026-*.md")):
            text = fpath.read_text(encoding="utf-8")
            m = re.search(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
            if not m:
                continue
            fm = dict(re.findall(r'^(\w+):\s*(.+)$', m.group(1), re.MULTILINE))
            date_str = fm.get("date", fpath.stem)
            scores = [int(s) for s in re.findall(r"⭐(\d+)", text)]
            titles = re.findall(r"\]\(https?://", text)
            link_count = len(titles)
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
                        "pillars": f"{PILLAR_EMOJI.get(p1,'')} + {PILLAR_EMOJI.get(p2,'')}",
                        "keywords": list(shared)[:5],
                        "count": len(shared),
                    })
    return connections


# ── SVG chart helpers (Biecek/ggplot2 aesthetic) ──

def svg_trend_chart(data: dict) -> str:
    """Biecek-style line chart: small multiples for each pillar."""
    all_dates = sorted({p["date"] for posts in data.values() for p in posts})
    if not all_dates:
        return ""
    n = len(all_dates)
    panel_w, panel_h = 240, 140
    gap = 40
    total_w = panel_w * 3 + gap * 2
    total_h = panel_h + 60
    labels_y = panel_h + 24

    tops = {}
    for p in ["aml", "stock", "science"]:
        tops[p] = max(
            (sum(post["score_total"] for post in data[p] if post["date"] == d)
             for d in all_dates), default=1
        )

    def make_panel(pillar: str, idx: int):
        posts = data.get(pillar, [])
        ox = idx * (panel_w + gap)
        clr = PILLAR_COLORS[pillar]
        clr_light = PILLAR_COLORS_LIGHT[pillar]
        lab = PILLAR_LABEL[pillar]
        emj = PILLAR_EMOJI.get(pillar, "")
        top = tops[pillar]
        vals = [sum(p["score_total"] for p in posts if p["date"] == d) for d in all_dates]
        scale_y = (panel_h - 24) / max(top, 1)

        lines = [f'<g transform="translate({ox},0)">']
        # background
        lines.append(f'<rect x="0" y="0" width="{panel_w}" height="{panel_h}" fill="{PLOT_BG}" rx="4"/>')
        # horizontal grid
        for g in range(0, 5):
            gy = panel_h - 16 - g * ((panel_h - 24) / 4)
            lines.append(f'<line x1="8" y1="{gy:.0f}" x2="{panel_w-8}" y2="{gy:.0f}" stroke="#e0e0e0" stroke-width="1"/>')
        # area fill
        if len(vals) > 1:
            pts = " ".join(
                f"{(panel_w-16)*i/(n-1)+8:.0f},{panel_h-16-v*scale_y:.0f}"
                for i, v in enumerate(vals)
            )
            lines.append(f'<polygon points="{(panel_w-16)*0/(n-1)+8:.0f},{panel_h-16} {pts} {(panel_w-16)*(n-1)/(n-1)+8:.0f},{panel_h-16}" fill="{clr_light}" opacity=".6"/>')
        # line
        if len(vals) > 1:
            pts = " ".join(
                f"{(panel_w-16)*i/(n-1)+8:.0f},{panel_h-16-v*scale_y:.0f}"
                for i, v in enumerate(vals)
            )
            lines.append(f'<polyline points="{pts}" fill="none" stroke="{clr}" stroke-width="2" stroke-linejoin="round"/>')
        # dots
        for i, v in enumerate(vals):
            x = (panel_w - 16) * i / (n - 1) + 8 if n > 1 else panel_w // 2
            y = panel_h - 16 - v * scale_y
            r = 3 if v > 0 else 0
            if r:
                lines.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r}" fill="{clr}" stroke="#fff" stroke-width="1.5"/>')
        # label
        lines.append(f'<text x="{panel_w//2}" y="{labels_y}" text-anchor="middle" font-size="11" font-weight="600" fill="{clr}">{emj} {lab}</text>')
        lines.append("</g>")
        return "\n".join(lines)

    panels = "\n".join(make_panel(p, i) for i, p in enumerate(["aml", "stock", "science"]))
    return f'''<svg viewBox="0 0 {total_w} {total_h+16}" xmlns="http://www.w3.org/2000/svg" style="max-width:100%;height:auto;font-family:Inter,system-ui,sans-serif">
  {panels}
  <text x="{total_w//2}" y="{total_h+8}" text-anchor="middle" font-size="10" fill="#999">Dzień</text>
</svg>'''


def svg_score_bars(data: dict) -> str:
    """Biecek-style horizontal bar chart: total score per pillar."""
    totals = {}
    for p in ["aml", "stock", "science"]:
        totals[p] = max(sum(post["score_total"] for post in data.get(p, [])), 0)
    if not any(totals.values()):
        return ""

    max_val = max(totals.values()) or 1
    bar_h, gap = 28, 12
    h = len(totals) * (bar_h + gap) + 30
    w = 380
    left_lab = 90

    bars = []
    for i, (p, v) in enumerate(totals.items()):
        y = 20 + i * (bar_h + gap)
        bw = max((w - left_lab - 60) * v / max_val, 2) if v else 0
        clr = PILLAR_COLORS[p]
        emj = PILLAR_EMOJI[p]
        lab = PILLAR_LABEL[p].split("&")[0].strip()
        bars.append(f'<text x="4" y="{y+bar_h//2+4}" font-size="11" font-weight="500" fill="#374151">{emj} {lab}</text>')
        bars.append(f'<rect x="{left_lab}" y="{y}" width="{bw:.0f}" height="{bar_h}" rx="3" fill="{clr}" opacity=".85"/>')
        bars.append(f'<text x="{left_lab+6}" y="{y+bar_h//2+4}" font-size="10" font-weight="600" fill="#fff">{v}</text>')
    return f'''<svg viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg" style="max-width:100%;height:auto;font-family:Inter,system-ui,sans-serif">
  {chr(10).join(bars)}
</svg>'''


def svg_weekly_sparklines(data: dict) -> str:
    """Small multiples — link count per day, faceted by pillar."""
    all_dates = sorted({p["date"] for posts in data.values() for p in posts})
    if not all_dates:
        return ""
    n = len(all_dates)
    if n < 2:
        return ""

    panel_w, panel_h = 260, 60
    total_w = panel_w + 60
    total_h = panel_h * 3 + 8

    def spark(pillar: str, idx: int):
        posts = data.get(pillar, [])
        vals = [sum(p["link_count"] for p in posts if p["date"] == d) for d in all_dates]
        top = max(vals) or 1
        clr = PILLAR_COLORS[pillar]
        emj = PILLAR_EMOJI[pillar]
        lab = PILLAR_LABEL[pillar].split("&")[0].strip()
        scale_y = (panel_h - 16) / top
        pts = " ".join(
            f"{8+(panel_w-16)*i/(n-1):.0f},{panel_h-8-v*scale_y:.0f}"
            for i, v in enumerate(vals)
        )
        return f'''<g transform="translate(0,{idx*(panel_h+4)})">
  <text x="0" y="{panel_h//2+4}" font-size="11" font-weight="500" fill="{clr}">{emj} {lab}</text>
  <rect x="54" y="0" width="{panel_w}" height="{panel_h}" fill="{PLOT_BG}" rx="3"/>
  <polyline points="{pts}" fill="none" stroke="{clr}" stroke-width="1.5" stroke-linejoin="round"/>
</g>'''

    return f'''<svg viewBox="0 0 {total_w} {total_h}" xmlns="http://www.w3.org/2000/svg" style="max-width:100%;height:auto;font-family:Inter,system-ui,sans-serif">
  {chr(10).join(spark(p, i) for i, p in enumerate(["aml", "stock", "science"]))}
</svg>'''


def build_html(data: dict) -> str:
    connections = find_connections(data)
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    # keywords
    pillar_keywords = {}
    for p, posts in data.items():
        c = Counter()
        for post in posts:
            c.update(w.lower() for w in post["themes"])
        pillar_keywords[p] = c.most_common(20)

    # metrics
    total_scores = sum(sum(post["score_total"] for post in posts) for posts in data.values())
    total_links = sum(sum(post["link_count"] for post in posts) for posts in data.values())
    total_posts = sum(len(posts) for posts in data.values())
    total_connections = len(connections)

    lines = [
        "---",
        'title: "📊 Acacia Radar — Dashboard Trendów"',
        f'date: {datetime.now().strftime("%Y-%m-%d")}',
        'layout: "radar"',
        "---",
        "",
        f"<p style='color:#6b7280;font-size:.85rem;margin-bottom:24px'>Ostatnia aktualizacja: {now} UTC</p>",
        "",
        "## 📋 Podsumowanie",
        "",
        '<div class="metrics">',
        f'<div class="metric gold"><div class="value">{total_scores}</div><div class="label">⭐ Suma punktów</div></div>',
        f'<div class="metric"><div class="value">{total_links}</div><div class="label">🔗 Linki</div></div>',
        f'<div class="metric"><div class="value">{total_posts}</div><div class="label">📄 Syntezy</div></div>',
        f'<div class="metric"><div class="value">{total_connections}</div><div class="label">🔗 Połączenia</div></div>',
        "</div>",
        "",
        "## 📈 Trend aktywności (facet Biecek)",
        "",
        "<p style='color:#6b7280;font-size:.85rem'>Całkowita suma punktów (⭐) dziennie w podziale na filary. Każdy panel to osobny filar — skala dostosowana do maksimum.</p>",
        f'<div class="chart-wrap"><h4>📈 Trend dzienny — suma punktów</h4>{svg_trend_chart(data)}</div>',
        "",
        "## 📊 Łączna aktywność",
        "",
        "<p style='color:#6b7280;font-size:.85rem'>Suma punktów od początku zbierania danych.</p>",
        f'<div class="chart-wrap"><h4>📊 Ranking filarów</h4>{svg_score_bars(data)}</div>',
        "",
        "## 🔗 Cross-Pillar Atlas",
        "",
        "<p style='color:#6b7280;font-size:.85rem'>Dni, w których ten sam temat pojawił się w dwóch lub trzech filarach jednocześnie — <strong>wykrywanie emergentnych połączeń</strong>.</p>",
        "",
    ]

    if connections:
        lines.append("<table>")
        lines.append("<tr><th>Data</th><th>Połączenie</th><th>Wspólne tematy</th></tr>")
        for c in connections[:10]:
            kw = ", ".join(c["keywords"][:4])
            lines.append(f"<tr><td>{c['date']}</td><td>{c['pillars']}</td><td>{kw}</td></tr>")
        lines.append("</table>")
    else:
        lines.append("<p>Brak wykrytych połączeń — zbyt mało danych.</p>")

    lines.extend([
        "",
        '<div class="insight">',
        '<span class="label">💡 Insight</span>',
        "<p><strong>Cross-pillar connections</strong> wskazują na tematy, które rezonują przez różne domeny. "
        "To sygnał emergentnych wzorców — tematów, które mogą mieć znaczenie systemowe wykraczające poza pojedynczy filar.</p>",
        "</div>",
        "",
        "## 🔍 Aktywność linków (sparklines)",
        "",
        "<p style='color:#6b7280;font-size:.85rem'>Liczba linków dziennie — małe wykresy (sparklines) w stylu <em>small multiples</em>.</p>",
        f'<div class="chart-wrap"><h4>🔗 Linki dziennie</h4>{svg_weekly_sparklines(data)}</div>',
        "",
        "## 🏷️ Dominujące tematy",
        "",
        "<p style='color:#6b7280;font-size:.85rem'>Najczęściej występujące słowa kluczowe w każdym filarze.</p>",
    ])

    for p in ["aml", "stock", "science"]:
        kw = pillar_keywords[p][:15]
        if not kw:
            continue
        lines.append(f"<h3>{PILLAR_EMOJI[p]} {PILLAR_LABEL[p]}</h3>")
        tags = " ".join(f'<span class="tag">{w}</span>' for w, _ in kw)
        lines.append(f"<p>{tags}</p>")

    lines.extend([
        "",
        "---",
        "",
        "<p style='color:#999;font-size:.78rem'>"
        "Radar generowany automatycznie przez <code>generate_radar.py</code>. "
        "Styl wizualizacji: Biecek / ggplot2. "
        "UX: McKinsey.</p>",
    ])

    return "\n".join(lines) + "\n"


def main():
    data = parse_content_files()
    total = sum(len(posts) for posts in data.values())
    print(f"[+] Radar: {total} postów ({', '.join(f'{p}={len(v)}' for p,v in data.items())})")

    html = build_html(data)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(html, encoding="utf-8")
    print(f"[+] Radar: {OUTPUT_FILE}")

    # JSON API
    api_dir = BASE_DIR / "static" / "api"
    api_dir.mkdir(parents=True, exist_ok=True)
    api_data = {
        "generated": datetime.now().isoformat(),
        "connections": find_connections(data),
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
