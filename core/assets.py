"""Asset pipeline for AcaciaFund: fingerprinting, minification, and manifest management."""

import hashlib
import json
import re
from pathlib import Path
from typing import Dict, List


class AssetManager:
    """Manages asset processing: fingerprinting, minification, and manifest tracking."""

    def __init__(self, dist_static_dir: Path, manifest_path: Path, build_hash: str):
        """Initialize AssetManager.

        Args:
            dist_static_dir: Path to dist/static/ where processed assets will be placed
            manifest_path: Path to assets_manifest.json for tracking hashed filenames
            build_hash: Hash string to use for fingerprinting (first 8 chars recommended)
        """
        self.dist_static_dir = dist_static_dir
        self.manifest_path = manifest_path
        self.build_hash = build_hash[:8]  # Use first 8 chars for shorter filenames
        self.asset_map: Dict[str, str] = {}  # original_path -> hashed_path
        self.processed_files: List[Path] = []

    def _compute_file_hash(self, file_path: Path) -> str:
        """Compute MD5 hash of a file's contents."""
        content = file_path.read_bytes()
        return hashlib.md5(content).hexdigest()[:8]

    def _minify_css(self, content: str) -> str:
        """Minify CSS by removing whitespace and comments."""
        # Remove comments
        content = re.sub(r"/\*[\s\S]*?\*/", "", content)
        # Remove whitespace around punctuation
        content = re.sub(r"\s*([{};:,>+])\s*", r"\1", content)
        # Remove whitespace around selectors
        content = re.sub(r"\s*([^\S\n]+)\s*", r" ", content)
        # Remove leading/trailing whitespace
        content = content.strip()
        # Remove unnecessary semicolons
        content = re.sub(r";+}", "}", content)
        return content

    def _minify_js(self, content: str) -> str:
        """Minify JS by removing whitespace and comments."""
        # Remove single-line comments (but not URLs or regex)
        content = re.sub(r"//.*$", "", content, flags=re.MULTILINE)
        # Remove multi-line comments
        content = re.sub(r"/\*[\s\S]*?\*/", "", content)
        # Remove whitespace around punctuation
        content = re.sub(r"\s*([{};:,>+()[\].])\s*", r"\1", content)
        # Remove leading/trailing whitespace
        content = content.strip()
        return content

    def _get_minifier(self, ext: str):
        """Get the appropriate minifier function for a file extension."""
        if ext in (".css",):
            return self._minify_css
        elif ext in (".js",):
            return self._minify_js
        return None  # No minification for other file types

    def _get_hashed_filename(self, original_name: str, content_hash: str) -> str:
        """Generate hashed filename from original name."""
        path = Path(original_name)
        stem = path.stem
        suffix = path.suffix
        return f"{stem}.{content_hash}{suffix}"

    def process_directory(self, source_dir: Path) -> Dict[str, str]:
        """Process all CSS/JS files in a directory.

        Args:
            source_dir: Source directory containing static assets

        Returns:
            Dictionary mapping original paths to hashed paths
        """
        if not source_dir.exists():
            return {}

        # Clear existing processed files
        self.asset_map.clear()
        self.processed_files.clear()

        # Process CSS and JS files
        for pattern in ("**/*.css", "**/*.js"):
            for file_path in source_dir.glob(pattern):
                if not file_path.is_file():
                    continue

                rel_path = str(file_path.relative_to(source_dir))
                content_hash = self._compute_file_hash(file_path)
                hashed_name = self._get_hashed_filename(file_path.name, content_hash)
                rel_parent = str(Path(rel_path).parent)
                if rel_parent == ".":
                    rel_parent = ""
                hashed_path = self.dist_static_dir / rel_parent / hashed_name

                # Ensure parent directory exists
                hashed_path.parent.mkdir(parents=True, exist_ok=True)

                # Read, minify, and write the file
                content = file_path.read_text(encoding="utf-8")
                minifier = self._get_minifier(file_path.suffix)
                if minifier:
                    content = minifier(content)

                hashed_path.write_text(content, encoding="utf-8")
                self.processed_files.append(hashed_path)

                # Map original path to hashed path
                self.asset_map[rel_path] = str(hashed_path.relative_to(self.dist_static_dir))

        # Save manifest
        self._save_manifest()

        return self.asset_map

    def _save_manifest(self) -> None:
        """Save asset mapping to manifest file."""
        manifest_data = {
            "build_hash": self.build_hash,
            "assets": self.asset_map,
        }
        self.manifest_path.parent.mkdir(parents=True, exist_ok=True)
        self.manifest_path.write_text(
            json.dumps(manifest_data, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    def resolve_path(self, original_path: str) -> str:
        """Resolve original asset path to hashed path using manifest.

        Args:
            original_path: Original asset path (e.g., "css/style.css")

        Returns:
            Absolute root-relative hashed path (e.g., "/static/css/style.v123.css")
            or original if not found
        """
        resolved = self.asset_map.get(original_path, original_path)
        return f"/static/{resolved}"

    def file_exists_with_hash(self, original_path: str) -> bool:
        """Check if asset exists (with or without hash in path).

        Args:
            original_path: Original or hashed asset path

        Returns:
            True if the file exists in dist/static/
        """
        # resolve_path returns /static/... — strip it back for file lookup
        resolved = self.resolve_path(original_path)
        resolved_clean = resolved.removeprefix("/static/")
        resolved_full = self.dist_static_dir / resolved_clean
        if resolved_full.is_file():
            return True

        return False


def create_asset_manager(dist_static_dir: Path, build_hash: str) -> AssetManager:
    """Factory function to create an AssetManager.

    Args:
        dist_static_dir: Path to dist/static/ directory
        build_hash: Hash string for fingerprinting

    Returns:
        Configured AssetManager instance
    """
    manifest_path = dist_static_dir.parent / "assets_manifest.json"
    return AssetManager(dist_static_dir, manifest_path, build_hash)
