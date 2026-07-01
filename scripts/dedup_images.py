"""Clean duplicate featured/section images and reset registry for re-fetch."""

import hashlib
import json
from collections import defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
REGISTRY_PATH = PROJECT_ROOT / "registry.json"
IMAGES_DIR = PROJECT_ROOT / "static" / "images" / "generated"


def file_hash(path: Path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest()


def is_ref_file(path: Path) -> bool:
    """Check if a file is a REF: pointer file (dedup symlink)."""
    try:
        return path.read_bytes()[:4] == b"REF:"
    except Exception:
        return False


def main():
    # 1. Find duplicate featured images by content hash
    featured_hashes: dict[str, list[str]] = defaultdict(list)
    for f in sorted(IMAGES_DIR.rglob("*")):
        if (
            f.is_file()
            and f.suffix in (".webp", ".jpg", ".jpeg", ".png")
            and "_card" not in f.name
            and not is_ref_file(f)
        ):
            h = file_hash(f)
            featured_hashes[h].append(str(f.relative_to(IMAGES_DIR)))

    print("=== Duplicate images ===")
    dup_count = 0
    to_delete = []
    for h, paths in featured_hashes.items():
        if len(paths) > 1:
            dup_count += 1
            print(f"\nDuplicate hash {h[:12]}:")
            for p in paths:
                sz = (IMAGES_DIR / p).stat().st_size
                print(f"  {p} ({sz} bytes)")
            # Keep first, delete rest
            for p in paths[1:]:
                to_delete.append(IMAGES_DIR / p)

    print(f"\nTotal duplicate groups: {dup_count}")
    print(f"Files to delete: {len(to_delete)}")

    # 2. Load registry and find articles referencing duplicate files
    reg = json.loads(REGISTRY_PATH.read_text())
    content = reg["content"]

    # Build map: filename -> article slugs that reference it
    file_to_slugs: dict[str, list[str]] = defaultdict(list)
    for a in content:
        fi = a.get("featured_image", "")
        if fi:
            rel = fi.replace("/static/images/generated/", "")
            file_to_slugs[rel].append(a["slug"])

    # Find referenced files that are duplicates (will be deleted)
    slugs_to_clear = set()
    for h, paths in featured_hashes.items():
        if len(paths) > 1:
            # All but the first (kept) need their articles cleared
            for p in paths[1:]:
                slug_key = str(p)
                if slug_key in file_to_slugs:
                    for slug in file_to_slugs[slug_key]:
                        slugs_to_clear.add(slug)

    print(f"\nArticles with duplicate featured_image to clear: {len(slugs_to_clear)}")
    for s in sorted(slugs_to_clear):
        print(f"  {s}")

    # 3. Clear featured_image in registry for affected articles
    cleared = 0
    for a in content:
        if a["slug"] in slugs_to_clear:
            a.get("featured_image", "")
            a["featured_image"] = ""
            cleared += 1

    # 4. Delete duplicate files from disk
    for f in to_delete:
        if f.exists():
            f.unlink()
            print(f"  Deleted: {f}")

    # 5. Also delete associated card thumbnails
    card_deleted = 0
    for f in IMAGES_DIR.rglob("*_card.*"):
        if f.exists():
            f.unlink()
            card_deleted += 1
    print(f"  Deleted {card_deleted} card thumbnails (will regenerate)")

    # 6. Write updated registry
    REGISTRY_PATH.write_text(json.dumps(reg, indent=2, ensure_ascii=False))
    print(f"\nRegistry updated: {cleared} articles cleared, {len(to_delete)} files deleted")
    print("Run fetch_images.py to get new unique images for cleared articles")


if __name__ == "__main__":
    main()
