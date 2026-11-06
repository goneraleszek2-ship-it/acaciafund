#!/usr/bin/env python3
"""Trim registry descriptions to the content-audit limit.

Usage:
    python3 scripts/trim_descriptions.py --dry-run
    python3 scripts/trim_descriptions.py --apply

Trimming prefers the last complete sentence inside the limit, then the last
word boundary, and appends an ellipsis only when a sentence had to be cut.
"""

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REGISTRY_PATH = PROJECT_ROOT / "registry.json"
BACKUP_PATH = PROJECT_ROOT / "registry.pre-description-trim.json"
DEFAULT_MAX = 303


def trim_description(text: str, max_len: int = DEFAULT_MAX) -> str:
    """Return a description at most ``max_len`` chars, preferring sentences."""
    text = (text or "").strip()
    if len(text) <= max_len:
        return text

    window = text[: max_len + 1]
    sentences = list(re.finditer(r"[.!?](?=\s|$)", window))
    sentence_cut = sentences[-1].end() if sentences else 0
    word_cut = text.rfind(" ", 0, max_len)
    if word_cut < max_len * 0.6:
        word_cut = max_len
    # Prefer a complete sentence unless that would discard most of the budget.
    cut = sentence_cut if sentence_cut >= max_len * 0.6 else word_cut

    trimmed = text[:cut].rstrip()
    if cut >= len(text):
        return trimmed[:max_len]
    if not trimmed.endswith((".", "!", "?")):
        trimmed = trimmed.rstrip(",;:—- ") + "…"
    if len(trimmed) > max_len:
        trimmed = trimmed[: max_len - 1].rstrip() + "…"
    return trimmed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="write registry.json")
    parser.add_argument("--dry-run", action="store_true", help="report only (default)")
    parser.add_argument("--max", type=int, default=DEFAULT_MAX)
    args = parser.parse_args(argv)

    data = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    changed = []
    for item in data.get("content", []):
        original = item.get("description") or ""
        trimmed = trim_description(original, args.max)
        if trimmed != original:
            changed.append((item.get("slug", ""), len(original), len(trimmed)))
            if args.apply and not args.dry_run:
                item["description"] = trimmed

    print(f"{len(changed)} description(s) over {args.max} chars")
    for slug, before, after in changed[:20]:
        print(f"  {slug}: {before} -> {after}")
    if len(changed) > 20:
        print(f"  … {len(changed) - 20} more")

    if not args.apply or args.dry_run:
        print("Dry run — pass --apply to write registry.json")
        return 0

    if REGISTRY_PATH.exists():
        shutil.copy2(REGISTRY_PATH, BACKUP_PATH)
    REGISTRY_PATH.write_text(
        json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"Wrote {REGISTRY_PATH} (backup: {BACKUP_PATH.name})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
