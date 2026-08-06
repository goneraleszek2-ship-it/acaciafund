#!/usr/bin/env python3
"""Content structure audit — validates body_html structure for all registry items.

Checks (hard errors, fail CI):
  - empty body_html
  - research items with fewer than MIN_H2_RESEARCH h2 headings
  - learn items with fewer than MIN_H2_LEARN h2 headings (except exempt slugs)
  - h2 headings immediately followed by another h2 with no content (empty section)
  - raw markdown residue leaking into HTML text (## / ** / *Also: patterns),
    ignoring <pre>/<code> regions
  - control characters in body_html

Checks (warnings, report only):
  - word count below per-content-type floor
  - title over 100 chars
  - description over 303 chars
  - consecutive duplicate heading text

Usage:
    python3 scripts/audit_content_structure.py [--registry registry.json]
                                               [--report dist/content-structure-report.json]
                                               [--fail-on-errors 0]

Exit codes:
    0 - error count <= --fail-on-errors
    1 - error count > --fail-on-errors
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parent.parent

MIN_H2_RESEARCH = 4
MIN_H2_LEARN = 3
WORD_FLOORS = {"research": 120, "learn": 120, "knowledge": 60}
TITLE_MAX = 100
DESCRIPTION_MAX = 303

# Non-prose pages exempt from the min-h2 rule (documented per slug).
EXEMPT_MIN_H2 = {
    "data/learn/learning-hub": "navigation hub page, not prose",
    "aml/learn/quiz-aml": "quiz page, not prose",
}

_HEADING_RE = re.compile(r"<h([23])[^>]*>(.*?)</h\1>", re.S)
_CODE_REGION_RE = re.compile(r"<(?:pre|code)\b[^>]*>.*?</(?:pre|code)>", re.S)
_CONTROL_CHARS_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")
_MARKDOWN_RESIDUE_RE = re.compile(r"\*\*[^*<>\n]{1,100}\*\*|(?:^|[\s>])##\s+[A-Z][^*\n]{0,80}|(?:^|[\s>])\*Also:[^*\n]{0,80}", re.M)


def count_words(text: str) -> int:
    return len(re.findall(r"\b\w+\b", re.sub(r"<[^>]+>", " ", text)))


def extract_headings(body: str) -> list[tuple[int, str]]:
    """Return (level, text) pairs for all h2/h3 headings in body_html."""
    return [(int(level), text.strip()) for level, text in _HEADING_RE.findall(body)]


def find_markdown_residue(body: str) -> list[str]:
    """Find raw markdown artifacts outside <pre>/<code> regions."""
    masked = _CODE_REGION_RE.sub(" ", body)
    return [m.group(0).strip() for m in _MARKDOWN_RESIDUE_RE.finditer(masked)]


def audit_item(item: dict) -> dict:
    slug = item.get("slug", "unknown")
    body = item.get("body_html", "") or ""
    content_type = item.get("content_type", "")
    errors: list[dict] = []
    warnings: list[dict] = []

    def error(rule: str, detail: str) -> None:
        errors.append({"slug": slug, "rule": rule, "detail": detail})

    def warning(rule: str, detail: str) -> None:
        warnings.append({"slug": slug, "rule": rule, "detail": detail})

    if not body.strip():
        error("empty_body", "body_html is empty or whitespace only")
        return {"slug": slug, "errors": errors, "warnings": warnings}

    words = count_words(re.sub(r"<[^>]+>", " ", body))
    if words < WORD_FLOORS.get(content_type, 60):
        warning("word_count", f"{words} words, floor is {WORD_FLOORS.get(content_type, 60)}")

    headings = extract_headings(body)
    h2_count = sum(1 for level, _ in headings if level == 2)

    if content_type == "research" and h2_count < MIN_H2_RESEARCH:
        error("min_h2", f"{h2_count} h2 headings, research requires >= {MIN_H2_RESEARCH}")
    elif content_type == "learn" and h2_count < MIN_H2_LEARN:
        if slug in EXEMPT_MIN_H2:
            warning("min_h2_exempt", f"{h2_count} h2 headings; exempt: {EXEMPT_MIN_H2[slug]}")
        else:
            error("min_h2", f"{h2_count} h2 headings, learn requires >= {MIN_H2_LEARN}")

    # Empty sections: h2 immediately followed by another h2 with < 5 words between.
    for idx, (level, text) in enumerate(headings):
        if level != 2:
            continue
        nxt = headings[idx + 1] if idx + 1 < len(headings) else None
        if nxt and nxt[0] == 2:
            gap = _gap_words(body, headings, idx)
            if gap < 5:
                error("empty_section", f"h2 '{text[:60]}' has no content before next h2 ({gap} words)")

    residue = find_markdown_residue(body)
    if residue:
        error("markdown_residue", f"{len(residue)} artifact(s), e.g. {residue[0][:80]!r}")

    if _CONTROL_CHARS_RE.search(body):
        error("control_chars", "control characters present in body_html")

    title = item.get("title", "")
    if len(title) > TITLE_MAX:
        warning("title_length", f"{len(title)} chars, max {TITLE_MAX}")

    description = item.get("description", "")
    if len(description) > DESCRIPTION_MAX:
        warning("description_length", f"{len(description)} chars, max {DESCRIPTION_MAX}")

    seen: list[str] = []
    for level, text in headings:
        lowered = text.lower()
        if lowered and seen and lowered == seen[-1]:
            warning("duplicate_heading", f"consecutive heading repeated: '{text[:60]}'")
        seen.append(lowered)

    return {"slug": slug, "errors": errors, "warnings": warnings}


def _gap_words(body: str, headings: list, idx: int) -> int:
    """Word count between heading idx and heading idx+1."""
    _, text = headings[idx]
    start = body.find(text) + len(text)
    _, next_text = headings[idx + 1]
    end = body.find(next_text, start)
    if end < 0:
        return 0
    return count_words(re.sub(r"<[^>]+>", " ", body[start:end]))


def load_registry(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit body_html structure of registry items")
    parser.add_argument("--registry", default=str(REPOSITORY_ROOT / "registry.json"))
    parser.add_argument("--report", default=str(REPOSITORY_ROOT / "dist" / "content-structure-report.json"))
    parser.add_argument("--fail-on-errors", type=int, default=0, help="exit 1 when error count exceeds this")
    args = parser.parse_args(argv)

    registry_path = Path(args.registry)
    if not registry_path.exists():
        print(f"ERROR: registry not found: {registry_path}")
        return 1

    registry = load_registry(registry_path)
    items = registry.get("content", [])
    results = [audit_item(item) for item in items]
    errors = [e for r in results for e in r["errors"]]
    warnings = [w for r in results for w in r["warnings"]]

    print(f"Structure audit: {len(items)} items")
    print(f"  ERRORS:   {len(errors)}")
    print(f"  WARNINGS: {len(warnings)}")
    for e in errors:
        print(f"    ERROR {e['slug']}: {e['rule']} — {e['detail']}")
    for w in warnings:
        print(f"    WARN  {w['slug']}: {w['rule']} — {w['detail']}")

    report = {
        "generated_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
        "total_items": len(items),
        "error_count": len(errors),
        "warning_count": len(warnings),
        "errors": errors,
        "warnings": warnings,
    }
    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Report written to {report_path}")

    if len(errors) > args.fail_on_errors:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
