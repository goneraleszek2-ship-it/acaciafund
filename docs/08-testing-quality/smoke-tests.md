# Smoke Tests

Smoke tests verify build output integrity and registry schema compliance without testing the build logic itself.

## Build Smoke Tests (`test_build_smoke.py` — 22 tests)

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

## Registry Smoke Tests (`test_smoke.py` — 9 tests)

These tests validate `registry.json` against the schema:

### Schema & Validation

| Test | Verifies |
|------|----------|
| `test_registry_loads_and_matches_schema` | Registry parses as `RegistryData` |
| `test_registry_content_items_have_mandatory_fields` | Required fields present on all items |
| `test_registry_content_items_parse_as_content` | Items construct as `Content` objects |
| `test_validate_content_strict_returns_empty_skip_list` | Strict validation passes clean registry |
| `test_validate_content_non_strict_skips_invalid` | Non-strict mode skips (not crashes) |
| `test_validate_content_returns_3_tuple` | Validator returns `(items, errors, warnings)` |

### Registry I/O

| Test | Verifies |
|------|----------|
| `test_registry_io_load_missing` | Loading a missing file raises cleanly |
| `test_registry_io_save_and_load_round_trip` | Save/load roundtrip preserves data |
| `test_registry_io_atomicity` | Writes are atomic (no partial file) |

## Running Smoke Tests

```bash
# All smoke tests
python3 -m pytest tests/test_smoke.py tests/test_build_smoke.py -v

# Only build smoke tests
python3 -m pytest tests/test_build_smoke.py -v
```

> **See also:** [Test Overview](test-overview.md), [CI Integration](ci-integration.md)
