"""Shared fixtures for AcaciaFund test suite."""

import json
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="session")
def project_root():
    """Path to the AcaciaFund project root."""
    return PROJECT_ROOT


@pytest.fixture(scope="session")
def registry_path():
    """Path to registry.json."""
    return PROJECT_ROOT / "registry.json"


@pytest.fixture(scope="session")
def full_registry():
    """Load the full live registry."""
    return json.loads((PROJECT_ROOT / "registry.json").read_text(encoding="utf-8"))


@pytest.fixture
def sample_registry():
    """Load the fixture registry (5 test items)."""
    fixture = PROJECT_ROOT / "tests" / "fixtures" / "fixture_registry.json"
    return json.loads(fixture.read_text(encoding="utf-8"))


@pytest.fixture
def sample_content_items(sample_registry):
    """Return the content items list from the fixture registry."""
    return sample_registry["content"]


@pytest.fixture
def tmp_dist(tmp_path):
    """Create a temporary dist directory and return its path."""
    d = tmp_path / "dist"
    d.mkdir()
    return d


@pytest.fixture
def dist_dir():
    """Path to the live dist/ directory (for post-build smoke tests)."""
    d = PROJECT_ROOT / "dist"
    if not d.exists():
        pytest.skip("dist/ not found — run build.py first")
    return d
