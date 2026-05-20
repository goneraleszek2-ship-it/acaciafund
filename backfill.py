#!/usr/bin/env python3
"""AcaciaFund — backfill historical daily posts."""

import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

BASE_DIR = Path(__file__).parent
CONTENT_DIR = BASE_DIR / "content" / "daily"

ALGOLIA_URL = "https://hn.algolia.com/api/v1/search"
USER_AGENT = "AcaciaFund/2.0"
HN_DISCUSSION_URL = "https://news.ycombinator.com/item?id={}"

PILLARS = {
    "aml": {
        "label": "AML",
        "emoji": "🛡️",
        "folder": CONTENT_DIR / "aml",
        "tags": ["aml", "compliance", "regtech", "financial-crime"],
        "description": "Ewolucja systemów odpornościowych w sektorze finansowym",
        "keywords": [
            "aml", "anti-money laundering", "compliance", "regtech",
            "financial crime", "sanctions", "money laundering",
            "know your customer", "kyc", "counter-terrorism financing",
            "ctf", "financial action task force", "fatf", "beneficial ownership",
            "shell company", "offshore", "fraud detection", "transaction monitoring",
            "sar", "suspicious activity", "banking regulation", "basel",
            "fintech", "psd2", "gdpr", "data privacy", "data breach",
            "cybersecurity", "cyber security", "ransomware", "phishing",
            "payment", "payment system", "central bank digital currency",
            "cbdc", "sovereign payment", "digital euro", "open banking",
            "financial inclusion", "anti-fraud", "identity theft",
            "credit card fraud", "bank fraud", "insider trading",
            "market manipulation", "securities fraud", "crypto regulation",
            "cryptocurrency regulation", "digital asset regulation",
            "sec", "financial conduct", "consumer financial protection",
            "bank secrecy", "patriot act", "trade surveillance",
        ],
        "domain_scores": {
            "fincen.gov": 10, "fatf-gafi.org": 10, "fca.org.uk": 8,
            "occ.gov": 8, "bis.org": 7, "ec.europa.eu": 6,
            "cointelegraph.com": 4, "coindesk.com": 4,
        },
    },
    "stock": {
        "label": "STOCK",
        "emoji": "📈",
        "folder": CONTENT_DIR / "stock",
        "tags": ["markets", "stocks", "semiconductors", "hardware"],
        "description": "Analiza rynków kapitałowych i półprzewodników",
        "keywords": [
            "semiconductor", "nvidia", "tsmc", "asml", "intel", "amd",
            "chip", "chips", "microchip", "foundry", "fab",
            "valuation", "earnings", "stock market", "nasdaq", "s&p 500",
            "supply chain", "hardware", "processor", "gpu", "asic",
            "arm", "risc-v", "apple silicon", "quantum computing",
            "venture capital", "startup funding", "ipo", "spac",
            "institutional investor", "hedge fund", "activist investor",
        ],
        "domain_scores": {
            "nvidia.com": 10, "tsmc.com": 10, "asml.com": 10,
            "intel.com": 8, "amd.com": 8, "semiengineering.com": 9,
            "anandtech.com": 7, "tomshardware.com": 7,
            "bloomberg.com": 5, "reuters.com": 5, "wsj.com": 5,
            "ft.com": 5, "seekingalpha.com": 6,
        },
    },
    "science": {
        "label": "SCIENCE",
        "emoji": "🧬",
        "folder": CONTENT_DIR / "science",
        "tags": ["science", "systems", "cybernetics", "complexity"],
        "description": "Nauka, systemy złożone i ewolucja poznawcza",
        "keywords": [
            "cybernetics", "mitochondria", "bioenergetics", "systems theory",
            "complexity", "emergence", "self-organization", "autopoiesis",
            "antifragile", "antifragility", "black swan", "taleb",
            "cognitive science", "neuroscience", "consciousness",
            "artificial life", "origin of life", "evolutionary biology",
            "epigenetics", "crispr", "gene therapy", "longevity",
            "mitochondrial", "cellular metabolism", "biohacking",
            "network theory", "graph theory", "scale-free",
        ],
        "domain_scores": {
            "nature.com": 10, "science.org": 10, "cell.com": 9,
            "pnas.org": 9, "biorxiv.org": 8, "arxiv.org": 7,
            "sciencedirect.com": 7, "scientificamerican.com": 8,
            "quantamagazine.org": 9, "nautil.us": 7, "aeon.co": 6,
        },
    },
}

STOP_WORDS = {
    "the", "a", "an", "of", "in", "to", "for", "and", "is", "on",
    "that", "with", "from", "by", "at", "its", "it", "as", "are",
    "be", "has", "have", "was", "were", "new", "how", "why", "what",
    "show", "ask", "tell", "this", "we", "our", "their", "they",
    "not", "no", "but", "all", "about", "up", "out", "over",
    "after", "into", "than", "then", "also", "just", "more",
}


def log(msg: str, ok: bool = True) -> None:
    prefix = "[+]" if ok else "[-]"
    print(f"{prefix} {msg}", file=sys.stderr)


def extract_domain(url: str) -> str:
    m = re.search(r"https?://([^/]+)", url)
    return m.group(1).lower() if m else ""


def classify_story(story: dict) -> list[tuple[str, int]]:
    title = story.get("title", "").lower()
    url = story.get("url", "")
    domain = extract_domain(url)
    scores: list[tuple[str, int]] = []
    for pillar_name, config in PILLARS.items():
        score = 0
        for dom_pattern, dom_score in config["domain_scores"].items():
            if dom_pattern in domain:
                score += dom_score
        for kw in config["keywords"]:
            pattern = r"\b" + re.escape(kw.lower()) + r"\b"
            if re.search(pattern, title):
                score += 3
        if score > 0:
            scores.append((pillar_name, score))
    return scores


def fetch_stories_for_date(target_date: datetime, min_points: int = 2, max_hits: int = 1000) -> list[dict]:
    day_start = int(target_date.replace(hour=0, minute=0, second=0, tzinfo=timezone.utc).timestamp())
    day_end = int((target_date.replace(hour=23, minute=59, second=59, tzinfo=timezone.utc)).timestamp())
    params = {
        "query": "",
        "tags": "story",
        "hitsPerPage": max_hits,
        "numericFilters": f"created_at_i>={day_start},created_at_i<={day_end}",
    }
    url = f"{ALGOLIA_URL}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode())
    except (urllib.error.URLError, json.JSONDecodeError, OSError) as e:
        log(f"Błąd pobierania HN dla {target_date.date()}: {e}", ok=False)
        return []
    stories = []
    for hit in data.get("hits", []):
        title = (hit.get("title") or "").strip()
        if not title:
            continue
        points = hit.get("points", 0) or 0
        if points < min_points:
            continue
        object_id = hit.get("objectID", "")
        hn_url = HN_DISCUSSION_URL.format(object_id) if object_id else ""
        raw_url = hit.get("url") or hn_url
        stories.append({
            "title": title,
            "url": raw_url,
            "hn_url": hn_url,
            "points": points,
            "created_at": hit.get("created_at", ""),
            "author": hit.get("author", ""),
            "object_id": object_id,
        })
    stories.sort(key=lambda s: s["points"], reverse=True)
    return stories


def extract_themes(titles: list[str]) -> list[str]:
    words = []
    for t in titles:
        cleaned = re.sub(r"[^a-z\s]", " ", t.lower())
        words.extend(w for w in cleaned.split() if len(w) > 3 and w not in STOP_WORDS)
    counts = Counter(words)
    return [w.capitalize() for w, _ in counts.most_common(5)]


def build_analysis(stories: list[dict], pillar_name: str) -> dict[str, str]:
    if not stories:
        date_str = "(unknown)"
        return {
            "trending": f"*Brak doniesień z tego okresu dla tego obszaru.*\n\n*Pipeline AcaciaFund kontynuuje skanowanie.*",
            "metaanalysis": "Brak danych do analizy w tym oknie czasowym.",
            "systems_lens": "Brak sygnałów. Z punktu widzenia teorii systemów, brak informacji to również informacja.",
            "connections": "Brak korelacji w tym oknie czasowym.",
        }
    titles = [s["title"] for s in stories]
    scores = [s["points"] for s in stories]
    avg_score = sum(scores) / len(scores)
    top = max(stories, key=lambda s: s["points"])
    top3 = sorted(stories, key=lambda s: s["points"], reverse=True)[:3]
    themes = extract_themes([s["title"] for s in top3])
    trending_lines = []
    for i, s in enumerate(stories[:7]):
        link_text = s["title"]
        extra = ""
        if s["hn_url"] and s["hn_url"] != s["url"]:
            extra = f" ([dyskusja]({s['hn_url']}))"
        trending_lines.append(f"{i+1}. [{link_text}]({s['url']}){extra} (⭐{s['points']})")
    trending = "\n".join(trending_lines)
    pillar_desc = PILLARS[pillar_name]["description"].lower()
    if avg_score > 300:
        intensity = "silne zainteresowanie społeczności"
    elif avg_score > 80:
        intensity = "umiarkowane zainteresowanie"
    else:
        intensity = "niski, ale wyspecjalizowany ruch"
    themes_str = ", ".join(themes[:3]) if themes else "różnorodne tematy"
    top3_titles = "; ".join(f"_{s['title']}_" for s in top3)
    metaanalysis = (
        f"W tym oknie w obszarze {pillar_desc} obserwujemy **{intensity}**. "
        f"Top 3 najwyżej ocenione:\n\n{top3_titles}\n\n"
        f"Dominujące wątki: **{themes_str}**. "
        f"Średnia punktacja: {avg_score:.0f} ⭐, "
        f"najwyższa: {top['points']} ⭐."
    )
    systems_lens_templates = [
        "Z punktu widzenia sprzężeń zwrotnych, dominujące narracje w tym oknie wskazują na dążenie do redukcji entropii wewnątrzsystemowej kosztem delegowania ryzyk na warstwy peryferyjne. Wyraźnie widać to w wątkach dotyczących **{themes}**.",
        "Analizowane trendy ujawniają mechanizmy antykruchości: systemy adaptują się przez zwiększanie redundancji kosztem efektywności krótkoterminowej. Najbardziej wyraziste w: _{top}_.",
        "Perspektywa cybernetyczna uwidacznia pętle sprzężenia zwrotnego między innowacją a regulacją. W filarze **{pillar}** obserwujemy wzmacnianie się pętli stabilizujących przy jednoczesnym wzroście szumów informacyjnych w obszarze {themes}.",
        "Systemy złożone w domenie {pillar} wykazują cechy samoorganizacji: lokalne interakcje ({themes}) prowadzą do emergencji globalnych wzorców bez centralnego sterowania.",
    ]
    idx = hash(frozenset(s["title"] for s in stories)) % len(systems_lens_templates)
    systems_lens = systems_lens_templates[idx].format(themes=themes_str, top=top["title"], pillar=pillar_name.upper())
    conn_templates = [
        "Ewolucja struktur technologicznych ({themes}) determinuje możliwości adaptacyjne modeli poznawczych. Synergia z pozostałymi domenami AcaciaFund widoczna w warstwie systemowej.",
        "Przekrój tematyczny wskazuje na korelację między rozwojem w obszarze {themes} a zmianami w architekturze ryzyka systemowego. Wątek rezonuje z analizami w pozostałych filarach.",
        "Przepływy informacji w tym oknie czasowym ujawniają ukryte powiązania między domenami: {themes}. Z perspektywy multi-domenowej AcaciaFund, są to przejawy tego samego zjawiska na różnych warstwach abstrakcji.",
    ]
    idx = hash(frozenset(s["url"] for s in stories)) % len(conn_templates)
    connections = conn_templates[idx].format(themes=themes_str)
    return {
        "trending": trending,
        "metaanalysis": metaanalysis,
        "systems_lens": systems_lens,
        "connections": connections,
    }


def generate_post(pillar_name: str, config: dict, pillar_stories: list[dict], date: datetime) -> Path | None:
    date_str = date.strftime("%Y-%m-%d")
    filename = f"{date_str}.md"
    filepath = config["folder"] / filename
    if filepath.exists():
        log(f"Post już istnieje: {filename} dla {pillar_name} — pomijam")
        return None
    analysis = build_analysis(pillar_stories, pillar_name)
    total_score = sum(s["points"] for s in pillar_stories)
    avg_score = round(total_score / len(pillar_stories), 1) if pillar_stories else 0
    max_score = max((s["points"] for s in pillar_stories), default=0)
    link_count = len(pillar_stories)
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
        "</div>",
        "",
        f"## 🔍 Trending (HackerNews, {date_str})",
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
        "---",
        f"*Raport wygenerowano {date_str}. Źródło: Algolia HN API. Klasyfikacja: AcaciaFund NLP.*",
    ]
    config["folder"].mkdir(parents=True, exist_ok=True)
    filepath.write_text("\n".join(lines) + "\n", encoding="utf-8")
    log(f"Wygenerowano: {filepath.relative_to(BASE_DIR)} ({link_count} linków)")
    return filepath


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Backfill historical AcaciaFund posts")
    parser.add_argument("--days", type=int, default=30, help="Liczba dni wstecz (domyślnie 30)")
    args = parser.parse_args()

    today = datetime.now(timezone.utc)
    print("=" * 55, file=sys.stderr)
    log(f"AcaciaFund Backfill — {args.days} dni wstecz od {today.strftime('%Y-%m-%d')}")
    print("=" * 55, file=sys.stderr)

    total_generated = 0
    for day_offset in range(args.days, 0, -1):
        target_date = today - timedelta(days=day_offset)
        date_str = target_date.strftime("%Y-%m-%d")
        log(f"\n--- Przetwarzanie: {date_str} ---")

        stories = fetch_stories_for_date(target_date, min_points=2)
        if not stories:
            log(f"Brak danych dla {date_str} — pomijam", ok=False)
            continue
        log(f"Pobrano {len(stories)} stories dla {date_str}")

        pillar_stories: dict[str, list[dict]] = {p: [] for p in PILLARS}
        unclassified = 0
        for story in stories:
            classifications = classify_story(story)
            if not classifications:
                unclassified += 1
                continue
            best_pillar = max(classifications, key=lambda x: x[1])
            pillar_stories[best_pillar[0]].append(story)

        log(f"Skategoryzowano: AML={len(pillar_stories['aml'])}, STOCK={len(pillar_stories['stock'])}, SCIENCE={len(pillar_stories['science'])}, nieskategoryzowane={unclassified}")

        for pillar, config in PILLARS.items():
            ps = pillar_stories[pillar]
            ps.sort(key=lambda s: s["points"], reverse=True)
            pillar_stories[pillar] = ps[:30]
            result = generate_post(pillar, config, pillar_stories[pillar], target_date)
            if result:
                total_generated += 1

    print("=" * 55, file=sys.stderr)
    log(f"Backfill zakończony. Wygenerowano {total_generated} nowych postów.")
    print("=" * 55, file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
