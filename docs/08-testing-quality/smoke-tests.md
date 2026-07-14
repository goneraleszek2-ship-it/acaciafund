# Smoke Tests

Smoke tests verify build output integrity and registry schema compliance without testing the build logic itself.

## Build Smoke Tests (`test_build_smoke.py` — 12 tests)

These tests run against the built output in `dist/` and verify:

### Output Existence

| Test | Verifies |
|------|----------|
| `test_dist_dir_exists` | `dist/` directory is present |
| `test_index_html_exists` | `dist/index.html` exists |
| `test_admin_dir_exists` | `dist/admin/` directory exists |
| `test_static_dir_exists` | `dist/static/` directory exists |
| `test_search_index_exists` | `dist/static/search-index.json` exists |

### Content Validation

| Test | Verifies |
|------|----------|
| `test_search_index_is_json` | Search index parses as valid JSON |
| `test_search_index_has_entries` | Search index is non-empty |
| `test_build_meta_exists` | `dist/build-meta.json` exists and has required fields |
| `test_no_build_errors` | `build_errors.log` is 0 bytes |

### Template Integrity

| Test | Verifies |
|------|----------|
| `test_admin_pages_are_html` | All admin pages contain valid HTML |

## Registry Smoke Tests (`test_smoke.py` — 34 tests)

These tests validate `registry.json` against the schema:

### Schema Validation (26 tests)

Each field is checked for:
- Presence (required fields)
- Type correctness
- Value constraints

### Data Integrity (8 tests)

| Test | Verifies |
|------|----------|
| `test_no_duplicate_slugs` | All slugs are unique |
| `test_slug_format` | Slugs match `{pillar}/{content_type}/{topic}` |
| `test_pillar_integrity` | All pillars are in `PILLAR_URL_MAP` |
| `test_content_type_integrity` | All content_types are `research`/`learn`/`knowledge` |
| `test_difficulty_integrity` | All difficulties are `beginner`/`intermediate`/`advanced` |
| `test_sqi_in_range` | All SQI values are 0.0–1.0 |
| `test_reading_time_positive` | Reading times are > 0 |

## Running Smoke Tests

```bash
# All smoke tests
python3 -m pytest tests/test_smoke.py tests/test_build_smoke.py -v

# Only build smoke tests
python3 -m pytest tests/test_build_smoke.py -v
```

> **See also:** [Test Overview](test-overview.md), [CI Integration](ci-integration.md)
