#!/usr/bin/env python3
"""Generate /api/articles.json — structured metadata for all daily posts."""

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).parent
CONTENT_DIR = BASE_DIR / "content" / "daily"
OUTPUT = BASE_DIR / "static" / "api" / "articles.json"

TRENDING_RE = re.compile(
    r"^\d+\.\s+\[(.+?)\]\((https?://[^\s)]+)\)"
    r"(?:\s+\(\[dyskusja\]\((https?://[^\s)]+)\)\))?"
    r"\s+\(⭐(\d+)\)"
    r"(?:\s+[🟢🟡🔴]\d+\.\d+)?"
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
                    title, url, hn_url, points = m.groups()
                    stories.append({
                        "title": title,
                        "url": url,
                        "hn_url": hn_url or "",
                        "points": int(points),
                    })
                elif stories and not stripped.startswith("1."):
                    break

            articles.append({
                "date": date_str,
                "pillar": pillar,
                "title": fm.get("title", ""),
                "url": f"/daily/{pillar}/{date_str}/",
                "tags": tags,
                "articles": stories,
            })
    return articles


def main():
    articles = parse_posts()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps({"generated": datetime.now(timezone.utc).isoformat(), "count": len(articles), "posts": articles}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"[+] Metadata: {OUTPUT} ({len(articles)} postów, {sum(len(p['articles']) for p in articles)} artykułów)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
