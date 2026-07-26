"""Bundle JS files into optimized entry points.

Entry points:
  app.js       → main.js + search.js + progressive_disclosure.js (always loaded)
  learning.js  → learning_hub.js + pretest_gate.js + feynman_synthesis.js (learn pages)
  retention.js → retention_engine.js (review pages)

Usage:
  python3 scripts/bundle_js.py [--dev] [--out static/dist/js]
"""

import argparse
import os
import re
import shutil
from pathlib import Path

STATIC_JS = Path(__file__).resolve().parent.parent / "static" / "js"

BUNDLES = {
    "app.js": [
        "main.js",
        "search.js",
        "progressive_disclosure.js",
    ],
    "learning.js": [
        "pretest_gate.js",
        "feynman_synthesis.js",
        "learning_hub.js",
    ],
    "retention.js": [
        "retention_engine.js",
    ],
}


def strip_comments(content: str) -> str:
    """Remove single and multi-line comments."""
    content = re.sub(r'//.*$', '', content, flags=re.MULTILINE)
    content = re.sub(r'/\*[\s\S]*?\*/', '', content)
    return content


def bundle(dev: bool = True, out_dir: str | None = None) -> dict[str, Path]:
    if out_dir is None:
        out_dir = str(STATIC_JS)
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    result = {}
    for bundle_name, sources in BUNDLES.items():
        parts: list[str] = []
        for src in sources:
            src_path = STATIC_JS / src
            if not src_path.exists():
                print(f"  WARN: {src} not found, skipping")
                continue
            content = src_path.read_text(encoding="utf-8")
            header = f"/* {src} */"
            parts.append(f"\n{header}\n{content}")

        bundled = "\n".join(parts)

        # In dev mode, write with line breaks preserved
        # In prod, strip comments and whitespace
        if not dev:
            bundled = strip_comments(bundled)
            bundled = re.sub(r'\s+', ' ', bundled)
            bundled = bundled.strip()

        out_file = out_path / bundle_name
        out_file.write_text(bundled, encoding="utf-8")
        result[bundle_name] = out_file
        print(f"  → {out_file} ({len(bundled)} bytes)")

    return result


def main():
    parser = argparse.ArgumentParser(description="Bundle JS files")
    parser.add_argument("--prod", action="store_true", help="Minify output")
    parser.add_argument(
        "--out", default=str(STATIC_JS),
        help="Output directory (default: static/js)"
    )
    args = parser.parse_args()

    print("JS Bundler")
    print(f"  Source: {STATIC_JS}")
    print(f"  Mode:  {'PROD' if args.prod else 'DEV'}")
    print(f"  Out:   {args.out}")
    print()

    files = bundle(dev=not args.prod, out_dir=args.out)

    print(f"\nDone: {len(files)} bundles written")
    return 0


if __name__ == "__main__":
    exit(main())
