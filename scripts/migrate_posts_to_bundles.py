#!/usr/bin/env python3
"""Migration script: convert flat posts under content/pl/blog/*.md into Hugo page bundles.

Usage:
  python scripts/migrate_posts_to_bundles.py --dry-run
  python scripts/migrate_posts_to_bundles.py --apply

Behavior:
  - For each YYYY-MM-DD-*.md file in content/pl/blog, create folder content/pl/blog/YYYY-MM-DD-*/ and move the .md to index.md
  - Attempts to rewrite image references that point to /images/... or relative paths to point to the bundle-local path.
  - Dry-run prints actions without changing files.
"""

from pathlib import Path
import re
import shutil
import argparse

ROOT = Path(__file__).parent.parent
BLOG = ROOT / "content" / "pl" / "blog"


def find_posts():
    return sorted([p for p in BLOG.glob("*.md") if p.is_file()])


def migrate_post(md_path: Path, apply: bool = False) -> None:
    name = md_path.stem
    bundle_dir = md_path.parent / name
    new_md = bundle_dir / "index.md"
    print(f"Post: {md_path.name} -> bundle: {bundle_dir}/")
    if apply:
        bundle_dir.mkdir(parents=True, exist_ok=True)
        # read and rewrite image paths (best-effort)
        txt = md_path.read_text(encoding="utf-8")
        # move /images/... to local folder references (note: does not move files)
        txt2 = re.sub(r"/images/([\w\-_.]+)", r"\1", txt)
        new_md.write_text(txt2, encoding="utf-8")
        # move file
        md_path.unlink()
        print(f"  migrated -> {new_md}")
    else:
        print(f"  dry-run: would create {bundle_dir}/ and move {md_path.name} -> index.md")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="Apply changes")
    args = parser.parse_args()

    posts = find_posts()
    print(f"Found {len(posts)} posts to consider")
    for p in posts:
        migrate_post(p, apply=args.apply)


if __name__ == "__main__":
    main()
