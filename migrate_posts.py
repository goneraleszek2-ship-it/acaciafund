#!/usr/bin/env python3
"""Migrate all old-format daily posts to new format: Trending + Podsumowanie."""

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from core.data import PILLARS, BASE_DIR, log, KNOWN_ENTITIES, ALL_ENTITIES, extract_domain
from core.analyze import build_analysis, build_pillar_signals
from core.score import build_history

CONTENT_DIR = BASE_DIR / "content" / "daily"

TRENDING_RE = re.compile(
    r"^\d+\.\s+\[(.+?)\]\((https?://[^\s)]+)\)"
    r"(?:\s+\(\[dyskusja\]\((https?://[^\s)]+)\)\))?"
    r"\s+\(⭐(\d+)\)"
)


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Simple frontmatter parser (no deps)."""
    m = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if not m:
        return {}, text
    raw_fm = m.group(1)
    body = text[m.end():]
    fm = {}
    for line in raw_fm.splitlines():
        if ":" in line:
            key, _, val = line.partition(":")
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            fm[key] = val
    return fm, body


def parse_trending(body: str) -> list[dict]:
    stories = []
    in_trending = False
    for line in body.splitlines():
        stripped = line.strip()
        if "Trending" in stripped:
            in_trending = True
            continue
        if not in_trending:
            continue
        m = TRENDING_RE.match(stripped)
        if m:
            title, url, hn_url, points_str = m.groups()
            stories.append({
                "title": title,
                "url": url,
                "hn_url": hn_url or "",
                "points": int(points_str),
                "created_at": "",
                "author": "",
                "object_id": "",
            })
        elif stories:
            break
    return stories


def rebuild_post(filepath: Path) -> bool:
    content = filepath.read_text(encoding="utf-8")

    title_line = re.search(r'^title: (.+)$', content, re.MULTILINE)
    if title_line:
        val = title_line.group(1).strip()
        if val.startswith('"') and val.endswith('"') and '"' in val[1:-1]:
            pass
        elif "Synteza" not in val:
            return False

    fm, body = parse_frontmatter(content)
    stories = parse_trending(body)

    if not stories:
        log(f"Brak artykułów w {filepath.name} — pomijam", ok=False)
        return False

    date_str = fm.get("date", filepath.stem)
    try:
        date = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError:
        date = datetime.now(timezone.utc)

    pillar_name = None
    for pname, config in PILLARS.items():
        if config["folder"].resolve() == filepath.parent.resolve():
            pillar_name = pname
            break
    if not pillar_name:
        # try matching by tags
        tags_str = fm.get("tags", "")
        for pname in PILLARS:
            if pname in tags_str.lower():
                pillar_name = pname
                break
    if not pillar_name:
        log(f"Nie rozpoznano filaru dla {filepath.name}", ok=False)
        return False

    config = PILLARS[pillar_name]
    analysis = build_analysis(stories, pillar_name, None)

    top = stories[0] if stories else None
    if top:
        raw = top["title"]
        short = raw[:80].rsplit(" ", 1)[0] if len(raw) > 80 else raw
        page_title = f"{short} — {config['emoji']} {config['label']} {date_str}"
    else:
        page_title = f"Synteza {config['emoji']} {config['label']} — {date_str}"

    lines = [
        "---",
        f"title: {json.dumps(page_title, ensure_ascii=False)}",
        f"date: {date_str}",
        f"tags: {json.dumps(config['tags'])}",
        f'theme: "AcaciaFund — {config["description"]}"',
        "---",
        "",
        f"## 🔍 Trending (HackerNews, {date_str})",
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

    filepath.write_text("\n".join(lines) + "\n", encoding="utf-8")
    log(f"Przebudowano: {filepath.resolve().relative_to(BASE_DIR.resolve())} ({len(stories)} linków)")
    return True


def main():
    total = 0
    for pillar_name, config in PILLARS.items():
        folder = config["folder"]
        if not folder.exists():
            continue
        for fpath in sorted(folder.glob("*.md")):
            if rebuild_post(fpath):
                total += 1
    log(f"Migracja zakończona. Przebudowano {total} postów.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
