# Testing Overview

AcaciaFund has **163+ tests** across 8 test files, covering core modules, build output, redirects, and taxonomy generation.

## Test Files

| File | Tests | Covers |
|------|-------|--------|
| `tests/test_ontology.py` | 39 | Ontology models, manager, extraction, seeding |
| `tests/test_learn_generation.py` | 14 | Learn module generation pipeline |
| `tests/test_urls.py` | 18 | URL helpers, pillar mapping, slug conversion |
| `tests/test_build_cache.py` | 18 | Build cache, incremental builds |
| `tests/test_smoke.py` | 34 | Registry validation, schema enforcement |
| `tests/test_build_smoke.py` | 12 | Build output verification |
| `tests/test_redirects.py` | 8 | Redirect rules validation |
| `tests/test_build_taxonomies.py` | 20 | Taxonomy generation (all 5 functions) |

## Test Configuration

`pyproject.toml`:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
```

## Running Tests

```bash
# All tests
python3 -m pytest tests/ -v

# Specific file
python3 -m pytest tests/test_ontology.py -v

# With timeout (prevents hanging)
timeout 300 python3 -m pytest tests/ -v --timeout=60

# Specific test
python3 -m pytest tests/test_urls.py::test_pillar_to_url -v
```

## Testing Strategy

| Layer | Approach | Tools |
|-------|----------|-------|
| Core modules | Unit tests with mocks | pytest, SimpleNamespace |
| Build pipeline | Smoke tests on output | Path I/O, subprocess |
| Templates | Minimal (snapshot-like assertions) | String matching |
| Content | Registry validation | Pydantic schema validation |
| Scripts | Integration tests (where feasible) | Direct import + mock |

## Key Patterns

### Mocking `render_template`

Used in `test_build_taxonomies.py`:

```python
from unittest.mock import MagicMock
mock_render = MagicMock(return_value="<html>Rendered</html>")
```

### Temporary Directories

Using `tmp_path` fixture:

```python
def test_something(tmp_path):
    output_dir = tmp_path / "dist"
    output_dir.mkdir()
    # ... run function with tmp_path
    assert (output_dir / "output.html").exists()
```

### Skipping Live Tests

Tests that require `registry.json` use `pytest.skip`:

```python
if not registry_path.exists():
    pytest.skip("registry.json not found")
```

## Test Dependencies

| Module | Dependencies | Import Safe for Tests? |
|--------|-------------|----------------------|
| `core/urls.py` | Only `config.py` | ✅ Yes (fast, no heavy deps) |
| `core/ontology.py` | Pydantic, `config.py` | ✅ Yes |
| `core/build_taxonomies.py` | `config.py`, `core/urls.py` | ✅ Yes |
| `core/build_cache.py` | Python stdlib | ✅ Yes |
| `build.py` | pandas, Jinja2, PIL | ❌ No (slow imports) |

> **See also:** [Unit Tests](unit-tests.md), [Taxonomy Tests](taxonomy-tests.md), [CI Integration](ci-integration.md)
