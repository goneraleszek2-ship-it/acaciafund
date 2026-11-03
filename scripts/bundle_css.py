#!/usr/bin/env python3
"""Inline vendor CSS imports and lint the design system stylesheet.

The build writes a bundled stylesheet to ``static/css/build/design-system.css``
so the browser never has to process runtime ``@import`` chains. Layer-scoped
imports are wrapped in ``@layer x { ... }``; leaving vendor CSS unlayered would
let it beat every layered rule.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATIC = ROOT / "static"
SOURCE = STATIC / "css" / "design-system.css"
OUTPUT = STATIC / "css" / "build" / "design-system.css"

IMPORT_RE = re.compile(
    r"@import\s+url\(\s*(['\"]?)([^'\")]+)\1\s*\)\s+layer\(\s*([a-zA-Z0-9_-]+)\s*\)\s*;",
    re.I,
)
URL_RE = re.compile(r"url\(\s*(['\"]?)([^'\")]+)\1\s*\)", re.I)


def _strip_comments_and_strings(text: str) -> str:
    out: list[str] = []
    i = 0
    quote = ""
    while i < len(text):
        ch = text[i]
        nxt = text[i + 1] if i + 1 < len(text) else ""
        if quote:
            if ch == "\\":
                i += 2
                continue
            if ch == quote:
                quote = ""
            i += 1
            continue
        if ch == "/" and nxt == "*":
            end = text.find("*/", i + 2)
            i = len(text) if end == -1 else end + 2
            continue
        if ch in ("'", '"'):
            quote = ch
            i += 1
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def lint_css(text: str, name: str = "css") -> list[str]:
    """Return a list of structural errors (empty means valid enough to ship)."""
    cleaned = _strip_comments_and_strings(text)
    errors: list[str] = []

    depth = 0
    for index, ch in enumerate(cleaned):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth < 0:
                line = cleaned[: index + 1].count("\n") + 1
                errors.append(f"{name}: unmatched }} at line {line}")
                depth = 0
    if depth != 0:
        errors.append(f"{name}: {depth} unclosed block(s)")

    top_level = re.sub(r"@layer\s+[a-zA-Z0-9_,\s-]+;", "", cleaned)
    seen_rule = False
    for match in re.finditer(r"@import\b|[{]", top_level):
        token = match.group(0)
        if token == "@import":
            if seen_rule:
                line = top_level[: match.start()].count("\n") + 1
                errors.append(f"{name}: @import after a rule block at line {line}")
        else:
            seen_rule = True

    for match in IMPORT_RE.finditer(text):
        if not match.group(3):
            errors.append(f"{name}: unlayered @import {match.group(2)}")
    return errors


def _rewrite_urls(css: str, source_path: Path) -> str:
    def repl(match: re.Match) -> str:
        target = match.group(2).strip()
        if target.startswith(("data:", "http:", "https:", "//", "#", "/")):
            return match.group(0)
        resolved = (source_path.parent / target).resolve()
        try:
            rel = resolved.relative_to(STATIC).as_posix()
        except ValueError:
            return match.group(0)
        return f"url('/static/{rel}')"

    return URL_RE.sub(repl, css)


def bundle_css(source: Path = SOURCE, output: Path = OUTPUT) -> str:
    text = source.read_text(encoding="utf-8")
    errors = lint_css(text, source.name)
    if errors:
        raise ValueError("; ".join(errors))

    def repl(match: re.Match) -> str:
        target = (source.parent / match.group(2)).resolve()
        layer = match.group(3)
        vendor = target.read_text(encoding="utf-8")
        vendor = _rewrite_urls(vendor, target)
        return f"@layer {layer} {{\n{vendor}\n}}"

    bundled = IMPORT_RE.sub(repl, text)
    if "@import" in bundled:
        raise ValueError("unresolved @import remains after bundling")
    errors = lint_css(bundled, output.name)
    if errors:
        raise ValueError("; ".join(errors))

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(bundled, encoding="utf-8")
    return str(output)


def main() -> int:
    parser = argparse.ArgumentParser(description="Bundle and lint design-system CSS")
    parser.add_argument("--check", action="store_true", help="lint only")
    parser.add_argument("--source", default=str(SOURCE))
    parser.add_argument("--output", default=str(OUTPUT))
    args = parser.parse_args()
    if args.check:
        errors = lint_css(Path(args.source).read_text(encoding="utf-8"), Path(args.source).name)
        if errors:
            print("\n".join(errors))
            return 1
        print("css lint: PASS")
        return 0
    path = bundle_css(Path(args.source), Path(args.output))
    print(f"css bundle: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
