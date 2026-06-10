"""Visual management system for AcaciaFund — 3-tier: manifest, auto-fetch, SVG fallback."""

from .manifest import load_manifest, get_manifest_entry
from .templates import generate_fallback_svg, PILLAR_VISUALS

__all__ = [
    "load_manifest", "get_manifest_entry",
    "generate_fallback_svg", "PILLAR_VISUALS",
]
