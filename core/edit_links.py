"""Edit-on-GitHub link resolution (Tier 6.1).

Resolves a content item to the most useful editable source file in the
repository:

1. A hand-authored markdown file under ``content/`` whose filename matches
   the item's topic (best effort — legacy files may not match).
2. Otherwise, the item's entry inside ``registry.json`` (the actual source
   of truth for synthesized content), anchored to its line number.

The registry line lookup is deterministic because registry.json is always
written with ``json.dump(indent=2)`` (same serializer the maintenance
scripts use), which keeps every key on its own line.
"""

from pathlib import Path
from typing import Any, Dict, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent
CONTENT_ROOT = REPO_ROOT / "content"
REGISTRY_PATH = REPO_ROOT / "registry.json"
GITHUB_REPO = "goneraleszek2-ship-it/acaciafund"
GITHUB_BASE = f"https://github.com/{GITHUB_REPO}/blob/main"


# Content directory names allowed per registry pillar key.
PILLAR_CONTENT_DIRS = {
    "aml": {"aml"},
    "stock": {"market"},
    "data-engineering": {"data", "data-engineering"},
    "knowledge": {"docs"},
}


def content_file_for_slug(
    slug: str,
    content_root: Path | None = None,
    pillar: Optional[str] = None,
) -> Optional[str]:
    """Return the relative content path (POSIX) matching a slug, or None.

    Matching is by topic stem: the final segment of the slug compared
    against every ``*.md`` filename in the pillar's content directory
    (case-insensitive, date-prefix-insensitive). Legacy content files may
    not match any slug.
    """
    topic = (slug or "").rsplit("/", 1)[-1].lower()
    if not topic:
        return None
    root = content_root or CONTENT_ROOT
    if not root.exists():
        return None
    allowed = PILLAR_CONTENT_DIRS.get((pillar or "").lower())
    search_dirs = [root / d for d in allowed] if allowed else [root]
    for directory in search_dirs:
        if not directory.exists():
            continue
        for path in sorted(directory.rglob("*.md")):
            stem = path.stem.lower()
            if stem == topic or stem.lstrip("0123456789-").strip("-") == topic:
                return path.relative_to(root).as_posix()
    return None


def registry_line_for_slug(slug: str, registry_path: Path | None = None) -> Optional[int]:
    """Return the 1-based line of the item's ``"slug"`` key in registry.json."""
    path = registry_path or REGISTRY_PATH
    if not path.exists():
        return None
    target = f'"slug": "{slug}"'
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if target in line:
            return line_no
    return None


def edit_url_for_item(item: Any, registry_path: Path | None = None) -> Optional[Dict[str, Any]]:
    """Build the edit link payload for a content item, or None.

    Returns ``{"url": ..., "path": ..., "label": ...}``. Prefers a matched
    markdown file under content/; falls back to the registry entry line.
    """
    slug = getattr(item, "slug", "") or ""
    if not slug:
        return None

    rel = content_file_for_slug(slug, pillar=getattr(item, "pillar", None))
    if rel:
        return {
            "url": f"{GITHUB_BASE}/content/{rel}",
            "path": f"content/{rel}",
            "label": f"Edit on GitHub — content/{rel}",
        }

    line = registry_line_for_slug(slug, registry_path)
    anchor = f"#L{line}" if line else ""
    return {
        "url": f"{GITHUB_BASE}/registry.json{anchor}",
        "path": "registry.json",
        "label": f"Edit this entry on GitHub{' (line ' + str(line) + ')' if line else ''}",
    }


def attach_edit_links(
    items: list[Any],
    registry_path: Path | None = None,
) -> int:
    """Attach ``edit_link`` payloads to content items. Returns count attached."""
    attached = 0
    for item in items:
        link = edit_url_for_item(item, registry_path)
        if link:
            item.edit_link = link
            attached += 1
        else:
            item.edit_link = None
    return attached


__all__ = [
    "attach_edit_links",
    "content_file_for_slug",
    "edit_url_for_item",
    "registry_line_for_slug",
]
