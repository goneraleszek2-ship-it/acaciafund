#!/usr/bin/env python3
"""Generate /api/articles.json — structured metadata for all daily posts."""

import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from core.bloom import classify_bloom_level, bloom_verb, level_index

BASE_DIR = Path(__file__).parent
CONTENT_DIR = BASE_DIR / "content" / "daily"
OUTPUT = BASE_DIR / "static" / "api" / "articles.json"
BLOOM_OUTPUT = BASE_DIR / "static" / "api" / "bloom.json"

TRENDING_RE = re.compile(
    r"^\d+\.\s+\[(.+?)\]\((https?://[^\s)]+)\)"
    r"(?:\s+\(\[dyskusja\]\((https?://[^\s)]+)\)\))?"
    r"\s+\(⭐(\d+)\)"
    r"(?:\s+[🟢🟡🔴](\d+\.\d+))?"
)


def parse_posts() -> list[dict]:
    articles = []
    for pillar_dir in sorted(CONTENT_DIR.iterdir()):
        if not pillar_dir.is_dir():
            continue
        pillar = pillar_dir.name
        for fpath in sorted(pillar_dir.glob("*.md")):
            content = fpath.read_text(encoding="utf-8")
            frontmatter_match = re.match(
                r"^---\n(.*?)\n---\n(.+)", content, re.DOTALL
            )
            if not frontmatter_match:
                continue

            raw_fm = frontmatter_match.group(1)
            body = frontmatter_match.group(2)

            fm = {}
            for line in raw_fm.splitlines():
                if ":" in line:
                    key, _, val = line.partition(":")
                    fm[key.strip()] = val.strip().strip('"').strip("'")

            date_str = fm.get("date", fpath.stem)
            tag_line = fm.get("tags", "[]")
            tags = (
                json.loads(tag_line)
                if tag_line.startswith("[")
                else [t.strip().strip('"') for t in tag_line.strip("[]").split(",") if t.strip()]
            )

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
                    title, url, hn_url, points, sqi = m.groups()
                    art = {
                        "title": title,
                        "url": url,
                        "hn_url": hn_url or "",
                        "points": int(points),
                    }
                    if sqi:
                        art["sqi"] = float(sqi)

                    bloom_lvl = classify_bloom_level(art)
                    art["bloom_level"] = bloom_lvl
                    art["bloom_verb"] = bloom_verb(bloom_lvl)

                    stories.append(art)
                elif stories and not stripped.startswith("1."):
                    break

            bloom_levels = list(dict.fromkeys(a["bloom_level"] for a in stories if a.get("bloom_level")))
            bloom_levels.sort(key=level_index)
            primary = bloom_levels[-1] if bloom_levels else "understand"

            articles.append({
                "date": date_str,
                "pillar": pillar,
                "title": fm.get("title", ""),
                "url": f"/daily/{pillar}/{date_str}/",
                "tags": tags,
                "bloom_levels": bloom_levels,
                "primary_bloom_level": primary,
                "articles": stories,
            })
    return articles


def build_bloom_overview(articles: list[dict]) -> dict:
    overview: dict[str, int] = {}
    by_pillar: dict[str, dict[str, int]] = {}
    recent: list[dict] = []

    for post in articles:
        pillar = post["pillar"]
        if pillar not in by_pillar:
            by_pillar[pillar] = {}
        for a in post.get("articles", []):
            lvl = a.get("bloom_level", "understand")
            overview[lvl] = overview.get(lvl, 0) + 1
            by_pillar[pillar][lvl] = by_pillar[pillar].get(lvl, 0) + 1

        recent.append({
            "date": post["date"],
            "pillar": pillar,
            "title": post["title"],
            "primary_bloom_level": post["primary_bloom_level"],
            "bloom_levels": post["bloom_levels"],
        })

    recent.sort(key=lambda p: p["date"], reverse=True)

    return {
        "generated": datetime.now(timezone.utc).isoformat(),
        "overview": overview,
        "by_pillar": by_pillar,
        "recent": recent[:30],
    }


def _pillars_from(articles: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for a in articles:
        pillar = a.get("pillar", "unknown")
        counts[pillar] = counts.get(pillar, 0) + 1
    return counts


def main():
    articles = parse_posts()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    posts_data = [
        {"date": p["date"], "pillar": p["pillar"], "title": p["title"],
         "url": p["url"], "tags": p["tags"],
         "bloom_levels": p["bloom_levels"],
         "primary_bloom_level": p["primary_bloom_level"]}
        for p in articles
    ]
    OUTPUT.write_text(
        json.dumps({
            "generated": datetime.now(timezone.utc).isoformat(),
            "count": len(articles),
            "posts": posts_data,
            "pillars": _pillars_from(articles),
        }, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    total_articles = sum(len(p["articles"]) for p in articles)
    print(f"[+] Metadata: {OUTPUT} ({len(articles)} postów, {total_articles} artykułów)")

    bloom_data = build_bloom_overview(articles)
    BLOOM_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    BLOOM_OUTPUT.write_text(
        json.dumps(bloom_data, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    print(f"[+] Bloom overview: {BLOOM_OUTPUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
