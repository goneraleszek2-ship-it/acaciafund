"""Visual management system for AcaciaFund — 3-tier: manifest, auto-fetch, SVG fallback."""

from .manifest import get_manifest_entry, load_manifest
from .templates import PILLAR_VISUALS, generate_fallback_svg

__all__ = [
    "load_manifest",
    "get_manifest_entry",
    "generate_fallback_svg",
    "PILLAR_VISUALS",
]
