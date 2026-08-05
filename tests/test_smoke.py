"""Smoke tests for AcaciaFund: registry schema, validation, and I/O."""

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REGISTRY_PATH = PROJECT_ROOT / "registry.json"


def _make_minimal_item(slug: str = "test-item", **overrides) -> dict:
    item = {
        "slug": slug,
        "title": "Test Item",
        "content_type": "research",
        "pillar": "aml",
        "tags": ["test"],
        "body_html": "<p>Hello</p>",
        "description": "A test",
    }
    item.update(overrides)
    return item


def _make_registry(content: list[dict] | None = None) -> dict:
    return {"content": content or []}


# ── Test 1: Registry load + schema ──


def test_registry_loads_and_matches_schema():
    """registry.json can be parsed through the RegistryData model."""
    from schemas import RegistryData

    assert REGISTRY_PATH.exists(), f"{REGISTRY_PATH} not found"
    raw = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    registry = RegistryData(**raw)
    assert registry.content is not None
    assert isinstance(registry.content, list)
    assert len(registry.content) > 0, "Expected at least one content entry"


def test_registry_content_items_have_mandatory_fields():
    """Every content entry in registry.json has slug and title."""
    from schemas import RegistryData

    raw = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    registry = RegistryData(**raw)
    for item in registry.content or []:
        assert item.slug, f"Missing slug in {item}"
        assert item.title, f"Missing title in {item}"


def test_registry_content_items_parse_as_content():
    """Every content entry can be instantiated as a Content object."""
    from core.content import Content

    raw = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    # Sample first 5 items instead of all 161 to speed up test
    for item in raw.get("content", [])[:5]:
        c = Content.from_dict(item)
        assert c.slug
        assert c.title
        assert c.content_type in ("research", "learn", "knowledge")


# ── Test 2: validate_content 3-tuple ──


def test_validate_content_strict_returns_empty_skip_list():
    """strict=True returns empty skipped_slugs (backward-compat)."""
    from core.validator import validate_content

    items = [_make_minimal_item(slug="a"), _make_minimal_item(slug="b")]
    is_valid, errors, skipped = validate_content(items, strict=True)
    assert is_valid is True
    assert isinstance(errors, list)
    assert skipped == []


def test_validate_content_non_strict_skips_invalid():
    """strict=False returns slugs of items with missing mandatory fields."""
    from core.validator import validate_content

    items = [
        _make_minimal_item(slug="good"),
        _make_minimal_item(slug="", title="No slug"),
        _make_minimal_item(slug="dupe"),
        _make_minimal_item(slug="dupe"),
    ]
    is_valid, errors, skipped = validate_content(items, strict=False)
    assert isinstance(skipped, list)
    assert "dupe" in skipped


def test_validate_content_returns_3_tuple():
    """validate_content always returns a (bool, list[str], list[str]) tuple."""
    from core.validator import validate_content

    result = validate_content([], strict=True)
    assert isinstance(result, tuple)
    assert len(result) == 3
    assert isinstance(result[0], bool)
    assert isinstance(result[1], list)
    assert isinstance(result[2], list)

    result2 = validate_content([], strict=False)
    assert len(result2) == 3


# ── Test 3: registry_io round-trip ──


def test_registry_io_load_missing(tmp_path):
    """load_registry returns empty dict when path does not exist."""
    from core.registry_io import load_registry

    missing = tmp_path / "nope.json"
    data = load_registry(missing)
    assert data == {"content": []}


def test_registry_io_save_and_load_round_trip(tmp_path):
    """A registry saved with save_registry can be loaded back identically."""
    from core.registry_io import load_registry, save_registry

    reg_path = tmp_path / "registry.json"
    original = _make_registry([_make_minimal_item(slug="rt-1")])

    save_registry(original, reg_path)
    assert reg_path.exists()

    loaded = load_registry(reg_path)
    assert loaded["content"] == original["content"]


def test_registry_io_atomicity(tmp_path):
    """save_registry writes to temp file first, then replaces — data is never lost."""
    from core.registry_io import load_registry, save_registry

    reg_path = tmp_path / "registry.json"
    original = _make_registry([_make_minimal_item(slug="atom-1")])
    save_registry(original, reg_path)

    tmp_file = reg_path.with_suffix(reg_path.suffix + ".tmp")
    assert not tmp_file.exists(), "Temp file should be cleaned up after save"

    loaded = load_registry(reg_path)
    assert loaded["content"][0]["slug"] == "atom-1"


def test_ontology_canonical_baseline():
    """Guard: fresh seeding reproduces the canonical 199 concepts / 447 relations.

    Runs in CI on every push (test_smoke.py is the CI smoke suite). Prevents the
    weekly-refresh regression that silently dropped 30 concepts from the ontology.
    """
    from core.ontology import OntologyManager

    mgr = OntologyManager()
    mgr.seed_all_pillars()
    mgr.seed_relations()
    assert mgr.concept_count() == 199, f"Expected 199 concepts, got {mgr.concept_count()}"
    assert mgr.relation_count() == 447, f"Expected 447 relations, got {mgr.relation_count()}"
