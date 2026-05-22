from app import db
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
