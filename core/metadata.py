from __future__ import annotations

import hashlib
import json
import mimetypes
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).parent.parent
SCHEMA_DIR = BASE_DIR / "schemas"
REGISTRY_DIR = BASE_DIR / "registry"
RUNS_DIR = REGISTRY_DIR / "runs"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso_utc(value: datetime | None = None) -> str:
    dt = value or utc_now()
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def payload_checksum(payload: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def load_schema(name: str) -> dict[str, Any]:
    path = SCHEMA_DIR / name
    data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return data


def _type_ok(value: Any, expected: str) -> bool:
    mapping = {
        "string": str,
        "integer": int,
        "number": (int, float),
        "boolean": bool,
        "object": dict,
        "array": list,
    }
    py = mapping.get(expected)
    if py is None:
        return True
    return isinstance(value, py)  # type: ignore[arg-type]


def validate_manifest(payload: dict[str, Any], schema_name: str) -> None:
    schema = load_schema(schema_name)
    required = schema.get("required", [])
    missing = [field for field in required if field not in payload]
    if missing:
        raise ValueError(f"Missing required manifest fields: {', '.join(missing)}")

    props = schema.get("properties", {})
    for key, rules in props.items():
        if key not in payload:
            continue
        if "const" in rules and payload[key] != rules["const"]:
            raise ValueError(f"Invalid constant for {key}: expected {rules['const']}")
        if "type" in rules and not _type_ok(payload[key], rules["type"]):
            raise ValueError(f"Invalid type for {key}: expected {rules['type']}")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def read_json(path: Path) -> dict[str, Any] | None:
    try:
        data: dict[str, Any] | None = json.loads(path.read_text(encoding="utf-8"))
        return data
    except (json.JSONDecodeError, OSError):
        return None


def _asset_mime(path: Path) -> str:
    guess, _ = mimetypes.guess_type(str(path))
    return guess or "application/octet-stream"


def build_asset_manifest(
    content_id: str, asset_type: str, path: Path, source_url: str = ""
) -> dict[str, Any]:
    data = path.read_bytes()
    manifest = {
        "manifest_type": "asset",
        "asset_id": f"{content_id}:{asset_type}:{path.name}",
        "content_id": content_id,
        "asset_type": asset_type,
        "path": str(path.relative_to(BASE_DIR)),
        "source_url": source_url,
        "mime_type": _asset_mime(path),
        "bytes": len(data),
        "checksum": "",
        "created_at": iso_utc(),
        "version": 1,
    }
    manifest["checksum"] = payload_checksum({k: v for k, v in manifest.items() if k != "checksum"})
    validate_manifest(manifest, "asset-manifest.schema.json")
    return manifest


def build_story_manifest(**kwargs: Any) -> dict[str, Any]:
    manifest = {
        "manifest_type": "story",
        "content_id": kwargs["content_id"],
        "pillar": kwargs["pillar"],
        "title": kwargs["title"],
        "date": kwargs["date"],
        "source_urls": kwargs.get("source_urls", []),
        "story_count": kwargs.get("story_count", 0),
        "signals": kwargs.get("signals", {}),
        "bloom_levels": kwargs.get("bloom_levels", []),
        "questions_count": kwargs.get("questions_count", 0),
        "flashcards_count": kwargs.get("flashcards_count", 0),
        "assets": kwargs.get("assets", []),
        "lineage": kwargs.get("lineage", {}),
        "created_at": iso_utc(),
        "published_at": kwargs.get("published_at", kwargs.get("date", iso_utc())),
        "version": 1,
        "quality_flags": kwargs.get("quality_flags", []),
        "source_breakdown": kwargs.get("source_breakdown", {}),
        "quality_metrics": kwargs.get("quality_metrics", {}),
        "checksum": "",
    }
    manifest["checksum"] = payload_checksum({k: v for k, v in manifest.items() if k != "checksum"})
    validate_manifest(manifest, "story-manifest.schema.json")
    return manifest


def build_run_manifest(**kwargs: Any) -> dict[str, Any]:
    manifest = {
        "manifest_type": "run",
        "run_id": kwargs["run_id"],
        "started_at": kwargs["started_at"],
        "ended_at": kwargs["ended_at"],
        "status": kwargs.get("status", "ok"),
        "source_counts": kwargs.get("source_counts", {}),
        "generated_pages": kwargs.get("generated_pages", []),
        "output_count": kwargs.get("output_count", 0),
        "notes": kwargs.get("notes", []),
        "created_at": iso_utc(),
        "version": 1,
        "checksum": "",
    }
    manifest["checksum"] = payload_checksum({k: v for k, v in manifest.items() if k != "checksum"})
    validate_manifest(manifest, "run-manifest.schema.json")
    return manifest


def _manifest_files(root: Path, pattern: str) -> list[Path]:
    if not root.exists():
        return []
    return sorted(root.glob(pattern))


def _safe_read_manifest(path: Path) -> dict[str, Any] | None:
    try:
        data = read_json(path)
    except (OSError, json.JSONDecodeError):
        return None
    if data is None or not isinstance(data, dict):
        return None
    return data


def _to_iso_string(value: Any) -> str:
    """Convert date/datetime objects to ISO string."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def _story_manifest_summary(path: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    date_val = manifest.get("date", "")
    created_val = manifest.get("created_at", "")
    published_val = manifest.get("published_at", "")

    return {
        "content_id": manifest.get("content_id", ""),
        "pillar": manifest.get("pillar", ""),
        "title": manifest.get("title", ""),
        "date": _to_iso_string(date_val),
        "path": str(path.relative_to(BASE_DIR)),
        "post_path": str((path.parent / "index.md").relative_to(BASE_DIR)),
        "checksum": manifest.get("checksum", ""),
        "story_count": manifest.get("story_count", 0),
        "questions_count": manifest.get("questions_count", 0),
        "flashcards_count": manifest.get("flashcards_count", 0),
        "bloom_levels": manifest.get("bloom_levels", []),
        "created_at": _to_iso_string(created_val),
        "published_at": _to_iso_string(published_val),
        "quality_flags": manifest.get("quality_flags", []),
    }


def _run_manifest_summary(path: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    return {
        "run_id": manifest.get("run_id", ""),
        "started_at": manifest.get("started_at", ""),
        "ended_at": manifest.get("ended_at", ""),
        "status": manifest.get("status", ""),
        "path": str(path.relative_to(BASE_DIR)),
        "checksum": manifest.get("checksum", ""),
        "output_count": manifest.get("output_count", 0),
        "source_counts": manifest.get("source_counts", {}),
        "created_at": manifest.get("created_at", ""),
    }


def _extract_frontmatter(path: Path) -> dict[str, Any] | None:
    """Extract YAML front-matter from a markdown file."""
    try:
        content = path.read_text(encoding="utf-8")
    except OSError:
        return None

    import re
    fm_match = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)", content, re.DOTALL)
    if not fm_match:
        return None

    import yaml
    try:
        frontmatter = yaml.safe_load(fm_match.group(1))
    except yaml.YAMLError:
        return None

    if not isinstance(frontmatter, dict):
        return None

    return frontmatter


def _md_path_to_content_id(path: Path) -> str:
    """Convert markdown file path to content_id (slug)."""
    stem = path.stem
    # Remove date prefix if present (e.g., 2026-06-29- -> )
    import re
    stem = re.sub(r"^\d{4}-\d{2}-\d{2}-", "", stem)
    return stem


def _pillar_from_path(path: Path) -> str:
    """Extract pillar name from content directory path."""
    parts = path.parts
    for i, part in enumerate(parts):
        if part == "content" and i + 1 < len(parts):
            return parts[i + 1]
    return "unknown"


def build_registry_index() -> dict[str, Any]:
    run_root = RUNS_DIR

    # Scan actual content directories with markdown files
    content_dirs = [
        BASE_DIR / "content" / "aml",
        BASE_DIR / "content" / "docs",
        BASE_DIR / "content" / "knowledge",
        BASE_DIR / "content" / "blog",
        BASE_DIR / "content" / "learn",
    ]

    pages: list[dict[str, Any]] = []
    page_by_id: dict[str, dict[str, Any]] = {}
    latest_by_pillar: dict[str, dict[str, Any]] = {}
    pillar_counts: dict[str, int] = {}

    for content_dir in content_dirs:
        if not content_dir.exists():
            continue
        for md_path in content_dir.rglob("*.md"):
            frontmatter = _extract_frontmatter(md_path)
            if not frontmatter:
                import sys
                print(f"WARNING: Could not parse front-matter from {md_path}", file=sys.stderr)
                continue

            # Skip files without required fields
            slug = frontmatter.get("slug") or _md_path_to_content_id(md_path)
            pillar = frontmatter.get("pillar") or _pillar_from_path(md_path)
            title = frontmatter.get("title", "")

            if not slug:
                continue

            # Build story manifest from front-matter
            manifest = {
                "manifest_type": "story",
                "content_id": slug,
                "pillar": pillar,
                "title": title,
                "date": frontmatter.get("date", ""),
                "created_at": iso_utc(),
                "published_at": frontmatter.get("date", iso_utc()),
                "checksum": payload_checksum({"slug": slug, "title": title, "pillar": pillar}),
            }

            page = _story_manifest_summary(md_path, manifest)
            pages.append(page)
            content_id = page["content_id"]
            if content_id:
                page_by_id[content_id] = page
            pillar_counts[pillar] = pillar_counts.get(pillar, 0) + 1
            previous = latest_by_pillar.get(pillar)
            if not previous or page.get("published_at", "") >= previous.get("published_at", ""):
                latest_by_pillar[pillar] = page

    runs: list[dict[str, Any]] = []
    run_by_id: dict[str, dict[str, Any]] = {}
    for path in _manifest_files(run_root, "*.json"):
        manifest = _safe_read_manifest(path)
        if not manifest or manifest.get("manifest_type") != "run":
            continue
        run = _run_manifest_summary(path, manifest)
        runs.append(run)
        run_id = run["run_id"]
        if run_id:
            run_by_id[run_id] = run

    runs.sort(key=lambda r: r.get("started_at", ""))
    pages.sort(key=lambda p: (p.get("published_at", ""), p.get("content_id", "")))

    index = {
        "manifest_type": "registry-index",
        "generated_at": iso_utc(),
        "latest_run_id": runs[-1]["run_id"] if runs else "",
        "counts": {
            "runs": len(runs),
            "pages": len(pages),
            "pillars": pillar_counts,
        },
        "latest_by_pillar": {
            pillar: page.get("content_id", "")
            for pillar, page in latest_by_pillar.items()
            if page.get("content_id")
        },
        "runs": runs,
        "pages": pages,
        "by_content_id": page_by_id,
        "by_run_id": run_by_id,
        "checksum": "",
    }

    index["checksum"] = payload_checksum({k: v for k, v in index.items() if k != "checksum"})
    validate_manifest(index, "registry-index.schema.json")
    return index


def write_registry_index(path: Path | None = None) -> Path:
    index_path = path or (REGISTRY_DIR / "index.json")
    index = build_registry_index()
    write_json(index_path, index)
    return index_path


def load_registry_index(path: Path | None = None) -> dict[str, Any]:
    index_path = path or (REGISTRY_DIR / "index.json")
    if index_path.exists():
        data = read_json(index_path)
        if data is not None:
            return data
    return build_registry_index()


def get_story_manifest(content_id: str) -> dict[str, Any] | None:
    index = load_registry_index()
    by_content_id: dict[str, dict[str, Any]] = index.get("by_content_id", {})
    return by_content_id.get(content_id)


def get_latest_story_manifest(pillar: str) -> dict[str, Any] | None:
    index = load_registry_index()
    by_pillar: dict[str, str] = index.get("latest_by_pillar", {})
    content_id = by_pillar.get(pillar)
    if not content_id:
        return None
    by_content_id: dict[str, dict[str, Any]] = index.get("by_content_id", {})
    return by_content_id.get(content_id)


def get_run_manifest(run_id: str) -> dict[str, Any] | None:
    index = load_registry_index()
    by_run_id: dict[str, dict[str, Any]] = index.get("by_run_id", {})
    return by_run_id.get(run_id)
