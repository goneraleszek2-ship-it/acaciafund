"""Content validation for AcaciaFund build pipeline.

This module provides a validate_content() function that checks the integrity
of the content registry before page generation begins.
"""

import json
import logging
from typing import Any

from config import PROJECT_ROOT

logger = logging.getLogger(__name__)

# Valid image extensions (in order of preference)
VALID_IMAGE_EXTENSIONS = [".webp", ".jpg", ".jpeg", ".png", ".svg"]

MANDATORY_FIELDS = {"title", "slug"}
ALLOWED_CONTENT_TYPES = {"research", "learn", "knowledge"}

# Asset manifest (loaded at runtime)
_asset_manifest: dict = {}


def _load_asset_manifest() -> dict:
    """Load asset manifest if it exists."""
    global _asset_manifest
    if not _asset_manifest:
        manifest_path = PROJECT_ROOT / "dist" / "assets_manifest.json"
        if manifest_path.exists():
            try:
                _asset_manifest = json.loads(manifest_path.read_text())
            except Exception:
                _asset_manifest = {}
    return _asset_manifest


def _resolve_asset_path(original_path: str) -> str:
    """Resolve original asset path to hashed path using manifest."""
    manifest = _load_asset_manifest()
    assets = manifest.get("assets", {})
    result = assets.get(original_path, original_path)
    return result if isinstance(result, str) else original_path


def _get_attr(item: Any, name: str, default: Any = None) -> Any:
    """Get attribute from item, handling both dict and object."""
    if isinstance(item, dict):
        return item.get(name, default)
    return getattr(item, name, default)


def _image_exists_with_any_extension(img_url: str) -> bool:
    """Check if image exists with any valid extension.

    If the expected extension (e.g., .webp) is missing, check other valid extensions.
    This makes the validator extension-agnostic while maintaining strictness.
    """
    # Resolve to hashed path if in manifest
    resolved_path = _resolve_asset_path(img_url.lstrip("/"))
    img_path = PROJECT_ROOT / resolved_path.lstrip("/")

    # First check the exact path with the expected extension
    if img_path.is_file():
        return True

    # If not found, try other valid extensions
    for ext in VALID_IMAGE_EXTENSIONS:
        alt_path = img_path.with_suffix(ext)
        if alt_path.is_file():
            return True

    return False


def validate_content(content_items: list[Any]) -> tuple[bool, list[str]]:
    """Validate content items before build.

    Args:
        content_items: List of content items (dict or object).

    Returns:
        Tuple of (is_valid, errors) where is_valid is True if all items pass,
        and errors is a list of error messages.
    """
    errors: list[str] = []
    seen_slugs: set[str] = set()

    for item in content_items:
        slug = _get_attr(item, "slug", "")
        title = _get_attr(item, "title", "")

        # Check mandatory fields
        if not slug:
            error_msg = "Missing or empty 'slug' in item"
            errors.append(error_msg)
            logger.error(error_msg)
        if not title:
            error_msg = f"Missing or empty 'title' for slug '{slug}'"
            errors.append(error_msg)
            logger.error(error_msg)

        # Check slug uniqueness
        if slug in seen_slugs:
            error_msg = f"Duplicate slug '{slug}' found"
            errors.append(error_msg)
            logger.error(error_msg)
        seen_slugs.add(slug)

        # Check content_type if present
        content_type = _get_attr(item, "content_type", "")
        if content_type and content_type not in ALLOWED_CONTENT_TYPES:
            error_msg = f"Invalid content_type '{content_type}' for slug '{slug}'"
            errors.append(error_msg)
            logger.error(error_msg)

        # Check referenced assets (featured_image)
        featured_image = _get_attr(item, "featured_image", "")
        if featured_image:
            if not _image_exists_with_any_extension(featured_image):
                error_msg = f"Referenced image not found: {featured_image} for slug '{slug}'"
                errors.append(error_msg)
                logger.error(error_msg)

        # Check section_images if present
        section_images = _get_attr(item, "section_images", [])
        if isinstance(section_images, list):
            for sec_img in section_images:
                if isinstance(sec_img, dict):
                    img_url = sec_img.get("image_url", "")
                    if img_url:
                        if not _image_exists_with_any_extension(img_url):
                            error_msg = (
                                f"Referenced section image not found: {img_url} for slug '{slug}'"
                            )
                            errors.append(error_msg)
                            logger.error(error_msg)

        # Check signals if present
        signals = _get_attr(item, "signals", {})
        if signals and isinstance(signals, dict):
            avg_sqi = signals.get("avg_sqi")
            if avg_sqi is not None:
                try:
                    avg_sqi_val = float(avg_sqi)
                    if not (0 <= avg_sqi_val <= 1):
                        error_msg = (
                            f"Invalid avg_sqi value {avg_sqi} (must be 0-1) for slug '{slug}'"
                        )
                        errors.append(error_msg)
                        logger.error(error_msg)
                except (ValueError, TypeError):
                    error_msg = f"Invalid avg_sqi type for slug '{slug}'"
                    errors.append(error_msg)
                    logger.error(error_msg)

    return len(errors) == 0, errors
