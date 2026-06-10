"""Single source of truth for AcaciaFund environment configuration.

All paths are relative to this file's directory (project root).
Import this from build.py and anywhere else config values are needed.
"""
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent

# Site identity
SITE_URL = "https://www.acaciafund.org"
SITE_NAME = "AcaciaFund"
SITE_DESCRIPTION = (
    "AcaciaFund — research synthesis & experimental learning platform. "
    "Automated classification of HackerNews + arXiv content using Bloom taxonomy. "
    "Static-first, privacy-preserving."
)
PLAUSIBLE_DOMAIN = ""

# Paths (source)
REGISTRY_PATH = PROJECT_ROOT / "registry.json"
TEMPLATE_DIR = PROJECT_ROOT / "templates"
PIPELINE_STATIC_DIR = PROJECT_ROOT / "static"
CONTENT_DIR = PROJECT_ROOT / "content"

# Paths (build output)
OUTPUT_DIR = PROJECT_ROOT / "dist"
STATIC_DST_DIR = OUTPUT_DIR / "static"

# Quality thresholds
SQI_THRESHOLD_MIN = 0.65       # minimum SQI for quality gate pass
SQI_BADGE_HIGH = 0.6           # SQI above this → green badge
SQI_BADGE_MED = 0.35           # SQI above this → amber badge (below → red)
SQI_DEFAULT = 0.5              # fallback when signal missing

# Interest score weights
INTEREST_SQI_WEIGHT = 0.6
INTEREST_RECENCY_WEIGHT = 0.4
INTEREST_RECENCY_DAYS = 180
