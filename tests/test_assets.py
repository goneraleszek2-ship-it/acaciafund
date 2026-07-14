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


class TestCreateAssetManager:
    def test_factory_returns_configured_instance(self, tmp_path):
        dist_static = tmp_path / "dist" / "static"
        dist_static.mkdir(parents=True)
        am = create_asset_manager(dist_static, build_hash="xyz789")
        assert isinstance(am, AssetManager)
        assert am.build_hash == "xyz789"
