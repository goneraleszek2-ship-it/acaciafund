from __future__ import annotations

import json
import os
import sqlite3
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Optional

LOCK_SUFFIX = ".lock"
TMP_SUFFIX = ".tmp"

COLUMN_FIELDS = frozenset({
    "slug", "title", "pillar", "content_type", "tags",
    "body_html", "description", "source_url", "source_breakdown",
    "author", "date_str", "created_at", "updated_at",
    "sqi", "enriched", "difficulty", "signals", "quality_metrics",
})

JSON_TEXT_FIELDS = frozenset({"tags", "source_breakdown", "signals", "quality_metrics"})

INT_FIELDS = frozenset({"enriched"})

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS registry_items (
    slug TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    pillar TEXT NOT NULL,
    content_type TEXT NOT NULL DEFAULT 'research',
    tags TEXT DEFAULT '[]',
    body_html TEXT DEFAULT '',
    description TEXT DEFAULT '',
    source_url TEXT DEFAULT '',
    source_breakdown TEXT DEFAULT '{}',
    author TEXT DEFAULT '',
    date_str TEXT DEFAULT '',
    created_at TEXT DEFAULT '',
    updated_at TEXT DEFAULT '',
    sqi REAL DEFAULT NULL,
    enriched INTEGER DEFAULT 0,
    difficulty TEXT DEFAULT '',
    signals TEXT DEFAULT '{}',
    quality_metrics TEXT DEFAULT '{}',
    json_data TEXT DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS idx_registry_pillar ON registry_items(pillar);
CREATE INDEX IF NOT EXISTS idx_registry_content_type ON registry_items(content_type);
CREATE INDEX IF NOT EXISTS idx_registry_created_at ON registry_items(created_at);
CREATE INDEX IF NOT EXISTS idx_registry_sqi ON registry_items(sqi);
CREATE TABLE IF NOT EXISTS registry_meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""


def _item_to_row(item: dict) -> dict:
    row: dict[str, Any] = {
        "json_data": json.dumps(item, ensure_ascii=False, default=str),
    }
    for key in COLUMN_FIELDS:
        value = item.get(key)
        if value is None:
            row[key] = None
        elif key in JSON_TEXT_FIELDS:
            row[key] = json.dumps(value, ensure_ascii=False, default=str)
        elif key in INT_FIELDS:
            row[key] = 1 if value else 0
        else:
            row[key] = value
    return row


def _row_to_item(row: dict) -> dict:
    item: dict[str, Any] = {}
    raw = row.get("json_data")
    if raw and isinstance(raw, str):
        try:
            item = json.loads(raw)
        except json.JSONDecodeError:
            item = {}
    for key in COLUMN_FIELDS:
        val = row.get(key)
        if val is not None:
            if key in JSON_TEXT_FIELDS:
                if isinstance(val, str):
                    try:
                        val = json.loads(val)
                    except json.JSONDecodeError:
                        val = []
            elif key in INT_FIELDS:
                val = bool(val)
            item[key] = val
    return item


def _lock_path(registry_path: Path) -> Path:
    return registry_path.with_suffix(registry_path.suffix + LOCK_SUFFIX)


def _acquire_lock(lock_path: Path) -> int | None:
    try:
        import fcntl
        fd = os.open(str(lock_path), os.O_CREAT | os.O_RDWR, 0o644)
        fcntl.flock(fd, fcntl.LOCK_EX)
        return fd
    except (ImportError, OSError):
        return None


def _release_lock(fd: int | None) -> None:
    if fd is not None:
        try:
            import fcntl
            fcntl.flock(fd, fcntl.LOCK_UN)
            os.close(fd)
        except (ImportError, OSError):
            os.close(fd)


class RegistryStore(ABC):
    @abstractmethod
    def load(self) -> dict:
        ...

    @abstractmethod
    def save(self, reg: dict) -> None:
        ...

    @abstractmethod
    def get_item(self, slug: str) -> Optional[dict]:
        ...

    @abstractmethod
    def get_items(
        self,
        pillar: Optional[str] = None,
        content_type: Optional[str] = None,
        limit: int = 0,
        offset: int = 0,
    ) -> list[dict]:
        ...

    @abstractmethod
    def count(self, pillar: Optional[str] = None) -> int:
        ...

    @abstractmethod
    def close(self) -> None:
        ...


class JsonRegistryStore(RegistryStore):
    def __init__(self, path: Path) -> None:
        self.path = Path(path)

    def load(self) -> dict:
        if not self.path.exists():
            return {"content": []}
        with open(self.path, "r", encoding="utf-8") as f:
            return json.load(f)

    def save(self, reg: dict) -> None:
        lock_p = _lock_path(self.path)
        tmp = self.path.with_suffix(self.path.suffix + TMP_SUFFIX)
        fd = _acquire_lock(lock_p)
        try:
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(reg, f, indent=2, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp, self.path)
        finally:
            if tmp.exists():
                tmp.unlink(missing_ok=True)
            _release_lock(fd)

    def get_item(self, slug: str) -> Optional[dict]:
        reg = self.load()
        for item in reg.get("content", []):
            if item.get("slug") == slug:
                return item
        return None

    def get_items(
        self,
        pillar: Optional[str] = None,
        content_type: Optional[str] = None,
        limit: int = 0,
        offset: int = 0,
    ) -> list[dict]:
        reg = self.load()
        items = list(reg.get("content", []))
        if pillar is not None:
            items = [i for i in items if i.get("pillar") == pillar]
        if content_type is not None:
            items = [i for i in items if i.get("content_type") == content_type]
        items.sort(key=lambda i: i.get("created_at", ""), reverse=True)
        if offset:
            items = items[offset:]
        if limit > 0:
            items = items[:limit]
        return items

    def count(self, pillar: Optional[str] = None) -> int:
        reg = self.load()
        items = reg.get("content", [])
        if pillar is not None:
            items = [i for i in items if i.get("pillar") == pillar]
        return len(items)

    def close(self) -> None:
        pass


class SqliteRegistryStore(RegistryStore):
    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self._conn: Optional[sqlite3.Connection] = None
        self._connect()

    def _connect(self) -> None:
        self._conn = sqlite3.connect(str(self.path))
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA synchronous=NORMAL")
        self._conn.executescript(SCHEMA_SQL)
        self._conn.commit()

    @property
    def conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._connect()
        assert self._conn is not None
        return self._conn

    def load(self) -> dict:
        reg: dict[str, Any] = {"content": []}
        cursor = self.conn.execute("SELECT key, value FROM registry_meta")
        for row in cursor:
            key = row["key"]
            val = row["value"]
            if key == "content":
                continue
            try:
                reg[key] = json.loads(val)
            except (json.JSONDecodeError, TypeError):
                reg[key] = val
        cursor = self.conn.execute("SELECT * FROM registry_items ORDER BY created_at DESC")
        items = []
        for row in cursor:
            items.append(_row_to_item(dict(row)))
        reg["content"] = items
        return reg

    def save(self, reg: dict) -> None:
        conn = self.conn
        conn.execute("DELETE FROM registry_meta")
        for key, value in reg.items():
            if key == "content":
                continue
            conn.execute(
                "INSERT OR REPLACE INTO registry_meta (key, value) VALUES (?, ?)",
                (key, json.dumps(value, ensure_ascii=False, default=str)),
            )
        conn.execute("DELETE FROM registry_items")
        items = reg.get("content", [])
        placeholders = ", ".join("?" for _ in COLUMN_FIELDS | {"json_data"})
        columns = list(COLUMN_FIELDS | {"json_data"})
        col_list = ", ".join(columns)
        stmt = f"INSERT INTO registry_items ({col_list}) VALUES ({placeholders})"
        for item in items:
            row = _item_to_row(item)
            vals = [row.get(c) for c in columns]
            conn.execute(stmt, vals)
        conn.commit()

    def get_item(self, slug: str) -> Optional[dict]:
        cursor = self.conn.execute(
            "SELECT * FROM registry_items WHERE slug = ?", (slug,)
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return _row_to_item(dict(row))

    def get_items(
        self,
        pillar: Optional[str] = None,
        content_type: Optional[str] = None,
        limit: int = 0,
        offset: int = 0,
    ) -> list[dict]:
        where_clauses: list[str] = []
        params: list[Any] = []
        if pillar is not None:
            where_clauses.append("pillar = ?")
            params.append(pillar)
        if content_type is not None:
            where_clauses.append("content_type = ?")
            params.append(content_type)
        where = ""
        if where_clauses:
            where = "WHERE " + " AND ".join(where_clauses)
        query = f"SELECT * FROM registry_items {where} ORDER BY created_at DESC"
        if limit > 0:
            query += " LIMIT ?"
            params.append(limit)
        if offset > 0:
            query += " OFFSET ?"
            params.append(offset)
        cursor = self.conn.execute(query, params)
        return [_row_to_item(dict(row)) for row in cursor]

    def count(self, pillar: Optional[str] = None) -> int:
        if pillar is not None:
            cursor = self.conn.execute(
                "SELECT COUNT(*) AS cnt FROM registry_items WHERE pillar = ?",
                (pillar,),
            )
        else:
            cursor = self.conn.execute("SELECT COUNT(*) AS cnt FROM registry_items")
        row = cursor.fetchone()
        return row["cnt"] if row else 0

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None


class RegistryStoreFactory:
    @staticmethod
    def create(backend: str = "json", path: Optional[Path] = None) -> RegistryStore:
        if path is None:
            path = Path("registry.json")
        path = Path(path)
        if backend == "auto":
            suffix = path.suffix.lower()
            if suffix == ".db" or suffix == ".sqlite":
                backend = "sqlite"
            else:
                backend = "json"
        if backend == "sqlite":
            return SqliteRegistryStore(path)
        return JsonRegistryStore(path)

    @staticmethod
    def migrate(
        source: RegistryStore,
        target: RegistryStore,
        batch_size: int = 100,
        verbose: bool = False,
    ) -> dict:
        start = time.time()
        reg = source.load()
        items = reg.get("content", [])
        total = len(items)
        if verbose:
            print(f"Migrating {total} items (batch size: {batch_size})...")
        target_reg = {k: v for k, v in reg.items() if k != "content"}
        target_reg["content"] = items
        target.save(target_reg)
        elapsed = time.time() - start
        stats = {
            "items": total,
            "elapsed_s": round(elapsed, 3),
            "items_per_sec": round(total / elapsed, 1) if elapsed > 0 else 0,
            "source_type": type(source).__name__,
            "target_type": type(target).__name__,
        }
        if verbose:
            print(f"Done. {total} items in {elapsed:.2f}s ({stats['items_per_sec']}/s)")
        return stats
