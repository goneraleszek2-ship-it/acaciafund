#!/usr/bin/env python3
"""One-time content structure remediation for registry.json.

Fixes structure issues found by scripts/audit_content_structure.py:
  - converts raw markdown residue in body_html to HTML
    (core/markdown_utils.fix_markdown_residue)
  - sectionizes research items that have no h2 headings by promoting
    <strong> lead-ins to <h2> sections and prefixing <h2>Overview</h2>

Usage:
    python3 scripts/remediate_content_structure.py [--dry-run]

Exit codes:
    0 - completed (or dry run clean)
    1 - registry write failed / no items changed
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPOSITORY_ROOT))

from core.markdown_utils import fix_markdown_residue  # noqa: E402

REGISTRY_PATH = REPOSITORY_ROOT / "registry.json"
BACKUP_PATH = REPOSITORY_ROOT / "registry.pre-audit-fix.json"

# Slugs whose bodies contain raw markdown headings (## ...) inside paragraphs.
MARKDOWN_RESIDUE_SLUGS = [
    "data/knowledge/cybernetic-foundations",
]

# Research items with no h2 headings at all; sectionized via strong lead-ins.
NO_H2_RESEARCH_SLUGS = [
    "data/research/sqlite-in-production-optimizing-wal-mode-concurrency-and-vfs",
    "data/research/choose-duckdb-rather-than-sqlite",
    "data/research/the-development-pipeline-is-a-production-system",
    "data/research/show-hn-a-local-merge-queue-for-parallel-claude-code-agents",
]

_STRONG_LEAD_RE = re.compile(r"<p><strong>([^<]{3,120}?)</strong>(.*?)</p>", re.S)


def strip_leading_title(body: str, title: str) -> str:
    """Remove a duplicate document title from the top of a body.

    The template renders its own `<h1>` from the registry title; bodies that
    also embed the title (as `<h1>` or as a markdown `# heading` paragraph)
    render a duplicated heading and should have it stripped.
    """
    b = body
    for pattern in (
        rf"<h1[^>]*>\s*{re.escape(title)}\s*</h1>",
        rf"<p>#\s+{re.escape(title)}</p>",
    ):
        b = re.sub(pattern, "", b, count=1, flags=re.S)
    return b


def sectionize_body(body: str) -> str:
    """Add h2 structure to a body with no headings.

    Prefixes `<h2>Overview</h2>` before the first paragraph and promotes
    paragraphs starting with a `<strong>Lead.</strong>` label into
    `<h2>Lead</h2>` sections. Trailing content after the last labelled
    section (e.g. a source citation) is preserved as a paragraph.
    """
    body = body.strip()
    if not body:
        return body
    parts = _STRONG_LEAD_RE.split(body)
    out: list[str] = []
    first_para = (parts[0] or "").strip()
    if first_para:
        out.append("<h2>Overview</h2>")
        out.append(first_para if first_para.startswith("<p>") else f"<p>{first_para}</p>")
    i = 1
    while i < len(parts):
        lead = (parts[i] or "").strip().rstrip(".").strip()
        content = (parts[i + 1] or "").strip() if i + 1 < len(parts) else ""
        if lead:
            out.append(f"<h2>{lead}</h2>")
            if content:
                out.append(f"<p>{content}</p>")
        elif content:
            out.append(f"<p>{content}</p>")
        i += 3
    if len(parts) >= 4:
        trail = (parts[-1] or "").strip()
        if trail:
            out.append(trail if trail.startswith("<p>") else f"<p>{trail}</p>")
    return "\n\n".join(out)


def remediate_registry(registry: dict) -> list[dict]:
    """Apply fixes, returning a list of {slug, fix} changes."""
    changes: list[dict] = []
    for item in registry.get("content", []):
        slug = item.get("slug", "")
        body = item.get("body_html", "")
        if slug in MARKDOWN_RESIDUE_SLUGS and body:
            fixed = strip_leading_title(body, item.get("title", ""))
            fixed = fix_markdown_residue(fixed)
            fixed = re.sub(r"^\s*(?:<br\s*/?>)+", "", fixed).strip()
            if fixed != body:
                item["body_html"] = fixed
                changes.append({"slug": slug, "fix": "markdown_residue"})
        if slug in NO_H2_RESEARCH_SLUGS and body and not re.search(r"<h2[ >]", body):
            fixed = sectionize_body(body)
            if fixed != body:
                item["body_html"] = fixed
                changes.append({"slug": slug, "fix": "sectionize"})
    return changes


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Remediate structure issues in registry.json")
    parser.add_argument("--dry-run", action="store_true", help="report changes without writing")
    args = parser.parse_args(argv)

    if not REGISTRY_PATH.exists():
        print(f"ERROR: registry not found: {REGISTRY_PATH}")
        return 1

    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    changes = remediate_registry(registry)
    print(f"Remediation: {len(changes)} change(s)")
    for c in changes:
        print(f"  {c['fix']:15} {c['slug']}")

    if not changes:
        return 0
    if args.dry_run:
        return 0

    if not BACKUP_PATH.exists():
        BACKUP_PATH.write_text(json.dumps(json.loads(REGISTRY_PATH.read_text(encoding="utf-8")), indent=2), encoding="utf-8")
        print(f"Backup written to {BACKUP_PATH}")
    registry["last_updated"] = __import__("datetime").date.today().isoformat()
    REGISTRY_PATH.write_text(json.dumps(registry, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Registry updated: {REGISTRY_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
