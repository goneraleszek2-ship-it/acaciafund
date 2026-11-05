"""Tests for core/build_images.py responsive image helpers."""

from pathlib import Path

from core.build_images import responsive_srcset


class TestResponsiveSrcset:
    def test_svg_has_no_width_variants(self):
        assert responsive_srcset("/static/images/hero.svg") == ""
        assert responsive_srcset("https://www.acaciafund.org/static/images/hero.svg") == ""

    def test_missing_variants_returns_empty(self, tmp_path):
        (tmp_path / "static/images").mkdir(parents=True)
        (tmp_path / "static/images/hero.webp").write_bytes(b"x")
        assert responsive_srcset("/static/images/hero.webp", roots=[tmp_path]) == ""

    def test_existing_variants_return_srcset(self, tmp_path):
        img_dir = tmp_path / "static/images"
        img_dir.mkdir(parents=True)
        (img_dir / "hero.webp").write_bytes(b"x")
        (img_dir / "hero_400w.webp").write_bytes(b"x")
        (img_dir / "hero_800w.webp").write_bytes(b"x")
        srcset = responsive_srcset("/static/images/hero.webp", roots=[tmp_path])
        assert srcset == (
            "/static/images/hero_400w.webp 400w, "
            "/static/images/hero_800w.webp 800w, "
            "/static/images/hero.webp 1200w"
        )

    def test_absolute_url_variant_lookup(self, tmp_path):
        img_dir = tmp_path / "static/images"
        img_dir.mkdir(parents=True)
        for name in ("hero.jpg", "hero_400w.jpg", "hero_800w.jpg"):
            (img_dir / name).write_bytes(b"x")
        srcset = responsive_srcset(
            "https://www.acaciafund.org/static/images/hero.jpg", roots=[tmp_path]
        )
        assert "/static/images/hero_400w.jpg 400w" in srcset
