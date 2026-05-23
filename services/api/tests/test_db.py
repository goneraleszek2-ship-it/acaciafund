# Import db from whichever location is available in this environment. Tests
# may run with different sys.path settings, so accept multiple import
# strategies.
try:
    from app import db
except Exception:
    try:
        from services.api.app import db
    except Exception:
        # Fallback: load module directly from file path
        import importlib.util
        from pathlib import Path

        db_path = Path(__file__).parent.parent / "app" / "db.py"
        spec = importlib.util.spec_from_file_location("db_fallback", str(db_path))
        db_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(db_mod)
        db = db_mod
from pathlib import Path


def test_init_and_crud(tmp_path: Path):
    p = tmp_path / "test.db"
    db.init_db(p)
    # upsert
    db.upsert_progress("/foo", True, 2, 12345)
    r = db.get_progress("/foo")
    assert r and r["done"]
    assert r["score"] == 2
    allp = db.list_progress()
    assert "/foo" in allp
