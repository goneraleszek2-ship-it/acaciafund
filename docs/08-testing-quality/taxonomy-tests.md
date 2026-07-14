# Taxonomy Tests

`tests/test_build_taxonomies.py` provides **20 tests** covering all 5 public functions in `core/build_taxonomies.py`.

## Test Structure

```
TestGenerateTagPages (4 tests)
├── test_generates_tag_index_and_pages
├── test_empty_tag_items_returns_zero
├── test_slug_sanitization_handles_special_chars
└── test_thin_tags_get_noindex

TestGenerateAdminPages (2 tests)
├── test_generates_all_admin_pages
└── test_admin_pages_use_render_template

TestGenerateSearchPages (4 tests)
├── test_generates_search_index_json
├── test_search_index_has_correct_fields
├── test_search_index_handles_empty_items
└── test_search_page_rendered

TestGenerateFeed (4 tests)
├── test_generates_feed_xml
├── test_feed_handles_empty_items
├── test_feed_render_called
└── test_feed_content_is_xml

TestGeneratePillarPages (2 tests)
├── test_generates_pillar_index_pages
└── test_pillar_page_render_called

TestLiveBuildTaxonomies (2 tests)
├── test_tag_pages_generate_with_live_registry
└── test_search_index_with_live_registry

TestBuildTaxonomiesPerformance (2 tests)
├── test_admin_page_generation_speed
└── test_tag_generation_speed
```

## Testing Approach

### Mocking

The build functions accept `render_template` as a callable, which is mocked:

```python
from unittest.mock import MagicMock

@pytest.fixture
def mock_render():
    return MagicMock(return_value="<html>Rendered</html>")
```

### Temporary Files

Tests use `tmp_path` (pytest built-in fixture) for output:

```python
def test_something(tmp_dist, mock_render):
    result = generate_something(tmp_dist, ..., mock_render, ...)
    assert (tmp_dist / "output.html").exists()
```

### Fixtures (`conftest.py`)

```python
@pytest.fixture
def tmp_dist(tmp_path):
    d = tmp_path / "dist"
    d.mkdir()
    return d

@pytest.fixture
def ctx_base():
    return {
        "site_name": "AcaciaFund",
        "site_url": "https://example.com",
        "site_description": "Test",
        "build_timestamp": "2026-07-13T12:00:00+00:00",
    }
```

### Test Data

Items are created as `SimpleNamespace` objects:

```python
from types import SimpleNamespace

def _make_item(slug, title, **kwargs):
    return SimpleNamespace(
        slug=slug, title=title, content_type="research", pillar="aml",
        description="Test description", body_html="<p>Test</p>",
        tags=["test"], date_str="2026-07-13", difficulty="beginner",
        reading_time=3, sqi=0.85, author="Test", language="en",
        signals={"avg_sqi": 0.85},
        created_at=datetime(2026, 7, 13, 12, 0, 0, tzinfo=timezone.utc),
        **kwargs
    )
```

## Live Registry Tests

Two tests (marked `TestLiveBuildTaxonomies`) use actual `registry.json` data:

- `test_tag_pages_generate_with_live_registry` — Tests tag page generation with real data (first 50 items)
- `test_search_index_with_live_registry` — Tests search index with all registry items

These tests skip automatically if `registry.json` doesn't exist.

## Performance Tests

Two tests measure generation speed:

- `test_admin_page_generation_speed` — Admin pages should generate in <5s
- `test_tag_generation_speed` — Tag pages should generate in <3s

These verify the functions complete within reasonable time bounds.

> **See also:** [Test Overview](test-overview.md), [CI Integration](ci-integration.md)
