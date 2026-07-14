#!/usr/bin/env python3
"""
Deterministic asset resolver for article images.
- Reads registry.json and data/image_assets_matrix.json
- For each entry lacking an image, selects a fallback SVG based on category
- Copies the fallback SVG to static/img/generated/<slug>.svg
- Updates registry entry with the generated image path
- Writes updated registry back to registry.json
"""

import json
import shutil
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
REGISTRY_PATH = BASE_DIR / "registry.json"
MATRIX_PATH = BASE_DIR / "data" / "image_assets_matrix.json"
GENERATED_DIR = BASE_DIR / "static" / "img" / "generated"


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(data, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def ensure_dir(path):
    path.mkdir(parents=True, exist_ok=True)


def main():
    print("Loading registry and asset matrix...")
    registry = load_json(REGISTRY_PATH)
    matrix = load_json(MATRIX_PATH)

    ensure_dir(GENERATED_DIR)

    updated = 0
    for entry in registry.get("content", []):
        # Skip if image already set
        if entry.get("image"):
            continue

        category = entry.get("category", "page")
        # Get category config or default to page
        cat_conf = matrix.get(
            category,
            matrix.get(
                "page",
                {
                    "query_modifiers": ["illustration", "concept"],
                    "fallback_image": "static/img/generated/page-default.svg",
                },
            ),
        )

        fallback_rel = cat_conf["fallback_image"]  # relative to BASE_DIR
        fallback_path = BASE_DIR / fallback_rel
        if not fallback_path.exists():
            # fallback to a generic placeholder if missing
            fallback_path = BASE_DIR / "static/img/generated/page-default.svg"
            fallback_rel = "static/img/generated/page-default.svg"

        # Ensure fallback exists; if not, create a simple SVG
        if not fallback_path.exists():
            fallback_path.parent.mkdir(parents=True, exist_ok=True)
            fallback_path.write_text(
                '<svg xmlns="http://www.w3.org/2000/svg" width="800" height="600">'
                '<rect width="100%" height="100%" fill="#f0f0f0"/>'
                '<text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" '
                'fill="#666" font-size="24">Image</text>'
                "</svg>"
            )
            fallback_rel = str(Path("static/img/generated") / fallback_path.name).replace("\\", "/")

        # Determine target filename
        slug = entry.get("slug", "unknown")
        target_name = f"{slug}.svg"
        target_path = GENERATED_DIR / target_name
        ensure_dir(target_path.parent)
        # Copy fallback to target (avoid overwriting if same)
        if not target_path.exists() or not target_path.samefile(fallback_path):
            shutil.copy2(fallback_path, target_path)

        # Set image path relative to site root (static/...)
        entry["image"] = f"/img/generated/{target_name}"
        updated += 1

    print(f"Updated {updated} entries with deterministic image paths.")
    save_json(registry, REGISTRY_PATH)
    print("Registry saved.")


if __name__ == "__main__":
    main()
