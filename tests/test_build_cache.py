"""Tests for core/build_cache.py."""

import json
from pathlib import Path

from core.build_cache import BuildCache


def test_cache_init_creates_empty_cache(tmp_path):
    cache = BuildCache(cache_file=tmp_path / ".build_cache.json")
    assert cache.cache == {}
    assert cache.templates_hash is None
    assert cache.content_templates_hash is None


def test_cache_save_and_load_round_trip(tmp_path):
    cache_file = tmp_path / ".build_cache.json"
    cache = BuildCache(cache_file=cache_file)
    cache.cache = {"foo": {"content_hash": "abc"}}
    cache.templates_hash = "tpl123"
    cache.content_templates_hash = "ctpl456"
    cache.save()

    restored = BuildCache(cache_file=cache_file)
    assert restored.cache == {"foo": {"content_hash": "abc"}}
    assert restored.templates_hash == "tpl123"
    assert restored.content_templates_hash == "ctpl456"


def test_cache_load_from_missing_file(tmp_path):
    cache_file = tmp_path / ".build_cache.json"
    cache = BuildCache(cache_file=cache_file)
    assert cache.cache == {}
    assert cache.templates_hash is None


def test_cache_load_ignores_different_version(tmp_path):
    cache_file = tmp_path / ".build_cache.json"
    cache_file.write_text(json.dumps({"version": "0.5", "entries": {"x": {}}}))
    cache = BuildCache(cache_file=cache_file)
    assert cache.cache == {}


def test_compute_content_hash_consistency():
    cache = BuildCache()
    h1 = cache.compute_content_hash("hello world")
    h2 = cache.compute_content_hash("hello world")
    h3 = cache.compute_content_hash("hello world!")
    assert h1 == h2
    assert h1 != h3


def test_compute_file_hash(tmp_path):
    f = tmp_path / "test.txt"
    f.write_text("hello")
    cache = BuildCache()
    h = cache.compute_file_hash(f)
    assert isinstance(h, str)
    assert len(h) == 64


def test_needs_rebuild_missing_key():
    cache = BuildCache()
    assert cache.needs_rebuild(Path("/nonexistent"))


def test_needs_rebuild_content_hash_changed(tmp_path):
    cache_file = tmp_path / ".build_cache.json"
    out = tmp_path / "out.html"
    out.write_text("original")
    cache = BuildCache(cache_file=cache_file)
    cache.cache[str(out)] = {"content_hash": cache.compute_content_hash("original")}
    cache.templates_hash = "stable"
    cache.content_templates_hash = "stable"

    assert not cache.needs_rebuild(out, content="original")
    assert cache.needs_rebuild(out, content="changed")


def test_needs_rebuild_templates_changed(tmp_path):
    cache_file = tmp_path / ".build_cache.json"
    out = tmp_path / "out.html"
    out.write_text("content")
    cache = BuildCache(cache_file=cache_file)
    cache.cache[str(out)] = {
        "content_hash": cache.compute_content_hash("content"),
        "templates_hash": "old_tpl",
    }
    cache.templates_hash = "new_tpl"

    assert cache.needs_rebuild(out, content="content")


def test_update_entry_sets_content_templates_hash(tmp_path):
    cache_file = tmp_path / ".build_cache.json"
    out = tmp_path / "out.html"
    cache = BuildCache(cache_file=cache_file)
    cache.templates_hash = "tpl"
    cache.content_templates_hash = "ctpl"
    cache.update_entry(out, content="hello", is_content=True)
    entry = cache.cache[str(out)]
    assert entry["content_templates_hash"] == "ctpl"
    assert entry["content_hash"] == cache.compute_content_hash("hello")


def test_update_entry_non_content_uses_templates_hash(tmp_path):
    cache_file = tmp_path / ".build_cache.json"
    out = tmp_path / "taxonomy.html"
    out.write_text("<html/>")
    cache = BuildCache(cache_file=cache_file)
    cache.templates_hash = "tpl"
    cache.update_entry(out, is_content=False)
    entry = cache.cache[str(out)]
    assert entry["templates_hash"] == "tpl"


def test_invalidate_all(tmp_path):
    cache_file = tmp_path / ".build_cache.json"
    cache = BuildCache(cache_file=cache_file)
    cache.cache = {"a": {}, "b": {}}
    count = cache.invalidate()
    assert count == 2
    assert cache.cache == {}


def test_invalidate_pattern(tmp_path):
    cache_file = tmp_path / ".build_cache.json"
    cache = BuildCache(cache_file=cache_file)
    cache.cache = {"dist/a.html": {}, "dist/b.html": {}, "other/c.html": {}}
    count = cache.invalidate(pattern="dist/")
    assert count == 2
    assert "other/c.html" in cache.cache


def test_get_cache_returns_instance():
    from core.build_cache import get_cache
    c = get_cache()
    assert isinstance(c, BuildCache)
