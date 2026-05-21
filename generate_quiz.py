#!/usr/bin/env python3
"""Generate static/api/quiz.json — all quiz questions from all posts."""

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from core.bloom import generate_quiz_questions

BASE_DIR = Path(__file__).parent
CONTENT_DIR = BASE_DIR / "content" / "daily"
OUTPUT = BASE_DIR / "static" / "api" / "quiz.json"

TRENDING_RE = re.compile(
    r"^\d+\.\s+\[(.+?)\]\((https?://[^\s)]+)\)"
    r"(?:\s+\(\[dyskusja\]\((https?://[^\s)]+)\)\))?"
    r"\s+\(⭐(\d+)\)"
    r"(?:\s+[🟢🟡🔴](\d+\.\d+))?"
)


def parse_articles_from_post(content: str) -> list[dict]:
    stories = []
    in_trending = False
    for line in content.splitlines():
        stripped = line.strip()
        if "Trending" in stripped:
            in_trending = True
            continue
        if not in_trending:
            continue
        m = TRENDING_RE.match(stripped)
        if m:
            title, url, hn_url, points, _ = m.groups()
            stories.append({
                "title": title,
                "url": url,
                "hn_url": hn_url or "",
                "points": int(points),
            })
        elif stories and not stripped.startswith("1."):
            break
    return stories


def main():
    all_questions = []
    for pillar_dir in sorted(CONTENT_DIR.iterdir()):
        if not pillar_dir.is_dir():
            continue
        pillar = pillar_dir.name
        for fpath in sorted(pillar_dir.glob("*.md")):
            content = fpath.read_text(encoding="utf-8")
            fm_match = re.match(r"^---\n(.*?)\n---\n(.+)", content, re.DOTALL)
            if not fm_match:
                continue

            raw_fm = fm_match.group(1)
            body = fm_match.group(2)

            fm = {}
            for line in raw_fm.splitlines():
                if ":" in line:
                    key, _, val = line.partition(":")
                    fm[key.strip()] = val.strip().strip('"').strip("'")

            date_str = fm.get("date", fpath.stem)
            articles = parse_articles_from_post(body)

            if not articles:
                continue

            questions = generate_quiz_questions(articles, pillar)
            for q in questions:
                q["post_url"] = f"/daily/{pillar}/{date_str}/"
                q["pillar"] = pillar
                q["date"] = date_str
                all_questions.append(q)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps({
            "generated": datetime.now(timezone.utc).isoformat(),
            "count": len(all_questions),
            "questions": all_questions,
        }, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"[+] Quiz: {OUTPUT} ({len(all_questions)} pytań)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
