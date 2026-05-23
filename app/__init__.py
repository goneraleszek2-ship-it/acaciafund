"""Compatibility shim so tests importing `app` find the real package.

This mirrors the top-level package `services.api.app` for legacy test imports.
"""
from importlib import import_module
import sys

_real = import_module("services.api.app")

try:
    _main = import_module("services.api.app.main")
    sys.modules.setdefault("app.main", _main)
    main = _main
except Exception:
    main = None

try:
    _db = import_module("services.api.app.db")
    sys.modules.setdefault("app.db", _db)
    db = _db
except Exception:
    db = None

__all__ = ["main", "db"]
