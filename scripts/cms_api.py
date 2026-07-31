"""CMS API — CRUD operations on registry.json for content management.

Usage:
    python3 -c "from scripts.cms_api import CMS; c = CMS(); print(len(c.list()))"
"""
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
REGISTRY_PATH = ROOT / "registry.json"
REGISTRY_BACKUP_DIR = ROOT / ".registry_backups"
VERSIONS_DIR = ROOT / ".registry_versions"
BUILD_SCRIPT = ROOT / "build.py"
ONTOLOGY_PATH = ROOT / "data" / "ontology.json"

PILLARS = {"aml": "Compliance", "stock": "Markets", "data-engineering": "Data"}
CONTENT_TYPES = {"research": "Research", "learn": "Learn", "knowledge": "Knowledge"}
DIFFICULTIES = {"beginner": "Beginner", "intermediate": "Intermediate", "advanced": "Advanced"}


class CMS:
    def __init__(self, registry_path: Optional[Path] = None):
        self.registry_path = registry_path or REGISTRY_PATH
        self._data: Optional[Dict[str, Any]] = None
        self._dirty = False

    def _load(self) -> Dict[str, Any]:
        if self._data is None:
            with open(self.registry_path) as f:
                self._data = json.load(f)
        assert self._data is not None
        return self._data

    def _save(self):
        if not self._dirty:
            return
        REGISTRY_BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        shutil.copy2(self.registry_path, REGISTRY_BACKUP_DIR / f"registry_{stamp}.json")
        with open(self.registry_path, "w") as f:
            json.dump(self._data, f, indent=1, ensure_ascii=False)
        self._dirty = False

    def _commit(self):
        self._data = None

    def list(
        self,
        pillar: Optional[str] = None,
        content_type: Optional[str] = None,
        search: Optional[str] = None,
        sort_by: str = "date_str",
        sort_desc: bool = True,
        limit: int = 200,
        offset: int = 0,
    ) -> Tuple[List[Dict[str, Any]], int]:
        data = self._load()
        items = data.get("content", [])
        q = search.lower().strip() if search else ""

        filtered = []
        for item in items:
            if pillar and item.get("pillar") != pillar:
                continue
            if content_type and item.get("content_type") != content_type:
                continue
            if q:
                haystack = (
                    (item.get("title") or "")
                    + " "
                    + (item.get("description") or "")
                    + " "
                    + " ".join(item.get("tags", []))
                    + " "
                    + (item.get("slug") or "")
                ).lower()
                if q not in haystack:
                    continue
            filtered.append(item)

        total = len(filtered)
        reverse = sort_desc

        def sort_key(item):
            val = item.get(sort_by, "")
            if not val:
                return ""
            return val

        filtered.sort(key=sort_key, reverse=reverse)
        page = filtered[offset : offset + limit]
        return page, total

    def get(self, slug: str) -> Optional[Dict[str, Any]]:
        data = self._load()
        for item in data.get("content", []):
            if item.get("slug") == slug:
                return item
        return None

    def create(self, item: Dict[str, Any]) -> Dict[str, Any]:
        data = self._load()
        items = data.setdefault("content", [])
        slug = item.get("slug", "")
        existing = self.get(slug)
        if existing:
            raise ValueError(f"Slug '{slug}' already exists")
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        entry = {
            "slug": slug,
            "title": item.get("title", "Untitled"),
            "description": item.get("description", ""),
            "body_html": item.get("body_html", ""),
            "pillar": item.get("pillar", "aml"),
            "content_type": item.get("content_type", "research"),
            "tags": item.get("tags", []),
            "date_str": item.get("date_str", datetime.now().strftime("%Y-%m-%d")),
            "created_at": now,
            "updated_at": now,
            "author": item.get("author", "AcaciaFund"),
            "difficulty": item.get("difficulty"),
            "language": "en",
        }
        items.append(entry)
        self._dirty = True
        self._save()
        self._commit()
        return entry

    def update(self, slug: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        data = self._load()
        for item in data.get("content", []):
            if item.get("slug") == slug:
                self._save_version(slug, dict(item))
                for key, value in updates.items():
                    if value is not None:
                        item[key] = value
                item["updated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                self._dirty = True
                self._save()
                self._commit()
                return item
        return None

    def _save_version(self, slug: str, item: Dict[str, Any]):
        safe_slug = slug.replace("/", "_").replace("\\", "_")
        version_dir = VERSIONS_DIR / safe_slug
        version_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        version_file = version_dir / f"{stamp}.json"
        entry = {
            "timestamp": stamp,
            "datetime": datetime.now(timezone.utc).isoformat(),
            "slug": slug,
            "data": item,
        }
        with open(version_file, "w") as f:
            json.dump(entry, f, indent=1, ensure_ascii=False)

    def list_versions(self, slug: str) -> List[Dict[str, Any]]:
        safe_slug = slug.replace("/", "_").replace("\\", "_")
        version_dir = VERSIONS_DIR / safe_slug
        if not version_dir.exists():
            return []
        versions = []
        for f in sorted(version_dir.iterdir(), reverse=True):
            if f.suffix == ".json":
                try:
                    with open(f) as fh:
                        versions.append(json.load(fh))
                except (json.JSONDecodeError, OSError):
                    continue
        return versions

    def restore_version(self, slug: str, timestamp: str) -> Optional[Dict[str, Any]]:
        safe_slug = slug.replace("/", "_").replace("\\", "_")
        version_file = VERSIONS_DIR / safe_slug / f"{timestamp}.json"
        if not version_file.exists():
            return None
        with open(version_file) as f:
            entry = json.load(f)
        item_data = entry.get("data", {})
        if not item_data.get("slug"):
            return None
        data = self._load()
        for i, existing in enumerate(data.get("content", [])):
            if existing.get("slug") == slug:
                self._save_version(slug, dict(existing))
                data["content"][i] = item_data
                data["content"][i]["updated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                data["content"][i]["restored_from"] = timestamp
                self._dirty = True
                self._save()
                self._commit()
                return data["content"][i]
        return None

    def delete(self, slug: str) -> bool:
        data = self._load()
        items = data.get("content", [])
        before = len(items)
        data["content"] = [i for i in items if i.get("slug") != slug]
        if len(data["content"]) < before:
            self._dirty = True
            self._save()
            self._commit()
            return True
        return False

    def stats(self) -> Dict[str, Any]:
        data = self._load()
        items = data.get("content", [])
        total = len(items)
        by_type: Dict[str, int] = {}
        by_pillar: Dict[str, int] = {}
        by_difficulty: Dict[str, int] = {}
        with_body = 0
        with_tags = 0
        for item in items:
            ct = item.get("content_type", "unknown")
            by_type[ct] = by_type.get(ct, 0) + 1
            p = item.get("pillar", "unknown")
            by_pillar[p] = by_pillar.get(p, 0) + 1
            d = item.get("difficulty") or "none"
            by_difficulty[d] = by_difficulty.get(d, 0) + 1
            if item.get("body_html", "").strip():
                with_body += 1
            if item.get("tags"):
                with_tags += 1
        return {
            "total": total,
            "by_type": by_type,
            "by_pillar": by_pillar,
            "by_difficulty": by_difficulty,
            "with_body": with_body,
            "with_tags": with_tags,
            "last_run": data.get("last_run", ""),
            "last_updated": data.get("last_updated", ""),
        }

    def build(self) -> Dict[str, Any]:
        result = subprocess.run(
            ["python3", str(BUILD_SCRIPT)],
            capture_output=True,
            text=True,
            timeout=300,
        )
        return {
            "returncode": result.returncode,
            "stdout": result.stdout[-2000:],
            "stderr": result.stderr[-2000:],
        }

    def list_concepts(self, pillar: Optional[str] = None) -> List[Dict[str, Any]]:
        if not ONTOLOGY_PATH.exists():
            return []
        with open(ONTOLOGY_PATH) as f:
            onto = json.load(f)
        concepts = onto.get("concepts", [])
        if pillar:
            concepts = [c for c in concepts if c.get("pillar") == pillar]
        return sorted(concepts, key=lambda c: c.get("label", ""))


if __name__ == "__main__":
    import sys

    cms = CMS()
    if len(sys.argv) > 1 and sys.argv[1] == "stats":
        s = cms.stats()
        print(json.dumps(s, indent=2))
    elif len(sys.argv) > 2 and sys.argv[1] == "get":
        item = cms.get(sys.argv[2])
        if item:
            print(json.dumps(item, indent=2))
        else:
            print(f"Not found: {sys.argv[2]}")
    elif len(sys.argv) > 1 and sys.argv[1] == "list":
        items, total = cms.list(search=sys.argv[2] if len(sys.argv) > 2 else None)
        print(f"Total: {total}")
        for item in items:
            print(f"  {item.get('slug','?'):50s} {item.get('title','?'):40s}")
    else:
        s = cms.stats()
        print(f"CMS ready — {s['total']} content items, {s['with_body']} with body")
