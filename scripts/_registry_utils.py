"""Shared registry load/save utilities for all scripts."""
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
REGISTRY_PATH = PROJECT_ROOT / "registry.json"


def load_registry(path: Path | str | None = None) -> dict:
    """Load registry.json. Exits on missing file."""
    p = Path(path) if path else REGISTRY_PATH
    if not p.exists():
        print(f"Error: {p} not found")
        sys.exit(1)
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def save_registry(reg: dict, path: Path | str | None = None) -> None:
    """Atomic save to registry.json via core.registry_io."""
    p = Path(path) if path else REGISTRY_PATH
    try:
        from core.registry_io import save_registry as _atomic_save
        _atomic_save(reg, p)
    except ImportError:
        with open(p, "w", encoding="utf-8") as f:
            json.dump(reg, f, indent=2, default=str)
