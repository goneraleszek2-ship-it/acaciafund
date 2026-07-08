"""Thread-safe atomic registry I/O with file locking.

Provides atomic save/load for registry.json using a temporary file + os.replace,
protected by fcntl.flock for concurrent access safety.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


LOCK_SUFFIX = ".lock"
TMP_SUFFIX = ".tmp"


def _lock_path(registry_path: Path) -> Path:
    return registry_path.with_suffix(registry_path.suffix + LOCK_SUFFIX)


def _acquire_lock(lock_path: Path) -> int | None:
    """Acquire an exclusive flock on the lock file. Returns fd or None."""
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


def load_registry(registry_path: str | Path) -> dict[str, Any]:
    """Load registry.json, returning {"content": []} if missing."""
    path = Path(registry_path)
    if not path.exists():
        return {"content": []}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_registry(reg: dict[str, Any], registry_path: str | Path) -> None:
    """Atomically save registry.json with file locking and fsync."""
    path = Path(registry_path)
    lock_p = _lock_path(path)
    tmp = path.with_suffix(path.suffix + TMP_SUFFIX)
    fd = _acquire_lock(lock_p)
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(reg, f, indent=2, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        if tmp.exists():
            tmp.unlink(missing_ok=True)
        _release_lock(fd)
