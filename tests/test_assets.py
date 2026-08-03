"""Tests for core/assets.py — AssetManager, fingerprinting, minification."""

import json
from pathlib import Path

import pytest

from core.assets import AssetManager, create_asset_manager


@pytest.fixture
def asset_manager(tmp_path):
    dist_static = tmp_path / "dist" / "static"
    dist_static.mkdir(parents=True)
    manifest = tmp_path / "assets_manifest.json"
    return AssetManager(dist_static, manifest, build_hash="abc12345")


class TestAssetManagerInit:
    def test_hash_truncated_to_8_chars(self):
        am = AssetManager(Path("/tmp/d"), Path("/tmp/m"), build_hash="abcdefghij")
        assert am.build_hash == "abcdefgh"


class TestComputeFileHash:
    def test_md5_hash_returns_string(self, asset_manager, tmp_path):
        f = tmp_path / "test.css"
        f.write_text("body { color: red; }")
        h = asset_manager._compute_file_hash(f)
        assert isinstance(h, str)
        assert len(h) == 8


class TestMinifyCSS:
    def test_removes_comments(self, asset_manager):
        result = asset_manager._minify_css("/* comment */ a { color: red; }")
        assert "comment" not in result

    def test_removes_excess_whitespace(self, asset_manager):
        result = asset_manager._minify_css("a   {   color:   red;   }")
        assert result == "a{color:red}"


class TestMinifyJS:
    def test_removes_single_line_comments(self, asset_manager):
        result = asset_manager._minify_js("// comment\nvar x = 1;")
        assert "comment" not in result

    def test_removes_multi_line_comments(self, asset_manager):
        result = asset_manager._minify_js("/* block */ var x = 1;")
        assert "block" not in result


class TestProcessDirectory:
    def test_nonexistent_dir_returns_empty(self, asset_manager):
        assert asset_manager.process_directory(Path("/nonexistent")) == {}

    def test_processes_css_files(self, asset_manager, tmp_path):
        src = tmp_path / "static"
        src.mkdir()
        (src / "style.css").write_text("body { color: red; }")
        result = asset_manager.process_directory(src)
        assert "style.css" in result
        assert result["style.css"].endswith(".css")

    def test_processes_js_files(self, asset_manager, tmp_path):
        src = tmp_path / "static"
        src.mkdir()
        (src / "app.js").write_text("var x = 1;")
        result = asset_manager.process_directory(src)
        assert "app.js" in result

    def test_saves_manifest(self, asset_manager, tmp_path):
        src = tmp_path / "static"
        src.mkdir()
        (src / "test.css").write_text("a { color: blue; }")
        asset_manager.process_directory(src)
        assert asset_manager.manifest_path.exists()
        manifest = json.loads(asset_manager.manifest_path.read_text())
        assert "build_hash" in manifest
        assert "assets" in manifest


class TestResolvePath:
    def test_known_asset_returns_hashed(self, asset_manager, tmp_path):
        src = tmp_path / "static"
        src.mkdir()
        (src / "style.css").write_text("body { color: red; }")
        asset_manager.process_directory(src)
        resolved = asset_manager.resolve_path("style.css")
        assert resolved.startswith("/static/")
        assert "abc123" in resolved or resolved != "/static/style.css"

    def test_unknown_asset_returns_original(self, asset_manager):
        resolved = asset_manager.resolve_path("nonexistent.css")
        assert resolved == "/static/nonexistent.css"


class TestFileExistsWithHash:
    def test_existing_file_returns_true(self, asset_manager, tmp_path):
        src = tmp_path / "static"
        src.mkdir()
        (src / "test.css").write_text("a { color: green; }")
        asset_manager.process_directory(src)
        assert asset_manager.file_exists_with_hash("test.css") is True

    def test_nonexistent_file_returns_false(self, asset_manager):
        assert asset_manager.file_exists_with_hash("nope.css") is False


class TestPruneStaleHashedFiles:
    def test_removes_old_hashed_file(self, asset_manager, tmp_path):
        src = tmp_path / "static"
        src.mkdir()
        (src / "app.js").write_text("var x = 1;")
        asset_manager.process_directory(src)
        stale = asset_manager.dist_static_dir / "app.deadbeef.js"
        stale.write_text("var old = 2;")
        pruned = asset_manager.prune_stale_hashed_files()
        assert pruned == 1
        assert not stale.exists()

    def test_keeps_current_hashed_and_plain_files(self, asset_manager, tmp_path):
        src = tmp_path / "static"
        src.mkdir()
        (src / "app.js").write_text("var x = 1;")
        asset_manager.process_directory(src)
        current = asset_manager.dist_static_dir / asset_manager.asset_map["app.js"]
        plain = asset_manager.dist_static_dir / "app.js"
        plain.write_text("var x = 1;")
        pruned = asset_manager.prune_stale_hashed_files()
        assert pruned == 0
        assert current.exists()
        assert plain.exists()

    def test_keeps_unmanaged_hashed_looking_files(self, asset_manager, tmp_path):
        src = tmp_path / "static"
        src.mkdir()
        (src / "app.js").write_text("var x = 1;")
        asset_manager.process_directory(src)
        vendor = asset_manager.dist_static_dir / "vendor" / "lib.12345678.js"
        vendor.parent.mkdir(parents=True)
        vendor.write_text("var lib = 1;")
        pruned = asset_manager.prune_stale_hashed_files()
        assert pruned == 0
        assert vendor.exists()

    def test_prunes_nested_dir_files(self, asset_manager, tmp_path):
        src = tmp_path / "static"
        src.mkdir()
        js_dir = src / "js"
        js_dir.mkdir()
        (js_dir / "app.js").write_text("var x = 1;")
        asset_manager.process_directory(src)
        stale = asset_manager.dist_static_dir / "js" / "app.deadbeef.js"
        stale.write_text("var old = 2;")
        pruned = asset_manager.prune_stale_hashed_files()
        assert pruned == 1
        assert not stale.exists()
        assert (asset_manager.dist_static_dir / asset_manager.asset_map["js/app.js"]).exists()

    def test_prunes_during_process_directory(self, asset_manager, tmp_path):
        src = tmp_path / "static"
        src.mkdir()
        (src / "app.js").write_text("var x = 1;")
        stale = asset_manager.dist_static_dir / "app.12345678.js"
        stale.write_text("var old = 2;")
        asset_manager.process_directory(src)
        assert asset_manager.pruned_count == 1
        assert not stale.exists()
        assert asset_manager.dist_static_dir / asset_manager.asset_map["app.js"] is not None


class TestCreateAssetManager:
    def test_factory_returns_configured_instance(self, tmp_path):
        dist_static = tmp_path / "dist" / "static"
        dist_static.mkdir(parents=True)
        am = create_asset_manager(dist_static, build_hash="xyz789")
        assert isinstance(am, AssetManager)
        assert am.build_hash == "xyz789"
