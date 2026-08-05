# Testing Overview

AcaciaFund has **1066 Python tests across 45 modules** plus **62 JS tests across 4 files** — covering core modules, the cognitive architecture (schema builder, retention, adaptive), research provenance, build output, redirects, taxonomy generation, and new test suites for bloom, brand, visuals, generate, source verification, and knowledge-module SQI guards.

> **Note:** Counts verified 2026-08-05 via `python3 -m pytest tests/ --co` (1066 collected across 45 modules) + 4 JS suites (62 tests). Full suite runs in ~28s.

## Test Files

### Core & Infrastructure

| File | Tests | Covers |
|------|-------|--------|
| `tests/test_ingestion.py` | 64 | Content ingestion pipeline |
| `tests/test_ontology.py` | 39 | Ontology models, manager, extraction, seeding |
| `tests/test_urls.py` | 34 | URL helpers, pillar mapping, slug conversion |
| `tests/test_metadata.py` | 28 | Manifest building, JSON utils, schema validation |
| `tests/test_contracts.py` | 24 | MOSA architecture contract tests |
| `tests/test_data.py` | 17 | Domain extraction, entity/theme extraction |
| `tests/test_content.py` | 11 | Content dataclass construction |
| `tests/test_build_cache.py` | 14 | Build cache, incremental builds |
| `tests/test_assets.py` | 15 | Asset pipeline |
| `tests/test_score.py` | 17 | Content scoring |
| `tests/test_smoke.py` | 9 | Registry validation, schema enforcement |
| `tests/test_build_smoke.py` | 22 | Build output verification |
| `tests/test_redirects.py` | 11 | Redirect rules validation |

### Cognitive Architecture

| File | Tests | Covers |
|------|-------|--------|
| `tests/test_schema_builder.py` | 29 | Prerequisite DAGs, learning paths, Bloom categorization |
| `tests/test_learning_paths.py` | 9 | Learning path generation |
| `tests/test_retention_engine.py` | 38 | SM-2, gap detection, interleaving, data generation |
| `tests/test_adaptive.py` | 31 | User profiling, difficulty, modality, ranking |
| `tests/test_sm2.py` | 13 | SM-2 algorithm |
| `tests/test_philosophy_integration.py` | 11 | Philosophical metadata integration |
| `tests/test_alpha_index.py` | 7 | A–Z index generation |

### Research Provenance

| File | Tests | Covers |
|------|-------|--------|
| `tests/test_source_trail.py` | 23 | Claim→citation mapping, SourceTrailManager |
| `tests/test_contradiction.py` | 40 | Negation/antonym/numeric detection, clustering |
| `tests/test_evidence_grade.py` | 24 | GRADE-style evidence scoring |
| `tests/test_export_research.py` | 14 | Research report export |

### Generation & Rendering

| File | Tests | Covers |
|------|-------|--------|
| `tests/test_generate_pages.py` | 40 | Headings, related, reading time, SQI badge, fingerprint |
| `tests/test_compositor.py` | 26 | SVG renderers (timeline, flow, comparisons, badges) |
| `tests/test_extractors.py` | 18 | Timeline/flow/comparison extraction |
| `tests/test_generate_learn_modules.py` | 17 | Learn module generation |
| `tests/test_learn_generation.py` | 14 | Learn module generation pipeline |

### Taxonomies, Sources & Agents

| File | Tests | Covers |
|------|-------|--------|
| `tests/test_build_taxonomies.py` | 51 | Taxonomy generation (admin, search, tag, pillar, feed) |
| `tests/test_check_source_freshness.py` | 8 | Source freshness staleness computation |
| `tests/test_check_entry_freshness.py` | 11 | Entry freshness validation (registry, review, verified dates) |
| `tests/test_source_synthesis.py` | 19 | Tag extraction, synthesis description, key insights |
| `tests/test_agent_tools.py` | 16 | Agent tool definitions |
| `tests/test_agents.py` | 22 | Agent pipeline |
| `tests/test_risk_engine.py` | 16 | Risk engine callbacks |
| `tests/test_llm_client.py` | 11 | LLM client abstraction |
| `tests/test_enrich.py` | 45 | Content enrichment |

### New Test Suites (August 2026)

| File | Tests | Covers |
|------|-------|--------|
| `tests/test_bloom.py` | 36 | Bloom taxonomy classification (6 levels), keyword matching, points thresholds, bigram extraction |
| `tests/test_brand.py` | 46 | Brand tokens, logo/domain/micro/section icons, patterns, sparklines |
| `tests/test_visuals.py` | 29 | Topic icon registry, subtopic picking, topic words, color helpers, thumbnail/OG SVG |
| `tests/test_generate.py` | 14 | Deep analysis, cross-pillar, classification confidence, trending sections |
| `tests/test_source_verification.py` | 38 | Source classification, verification, scoring, domain extraction, article-level analysis |
| `tests/test_check_entry_freshness.py` | 11 | Entry freshness validation (registry, review, verified dates) |

### JavaScript

| File | Tests | Covers |
|------|-------|--------|
| `tests/test_progressive_disclosure.js` | 8 | `parseSections`, `toggleSection` pure functions |
| `tests/test_toc.js` | 12 | `createItems`, `linkClass` pure functions |
| `tests/test_adaptive_ui.js` | 19 | Density modes, difficulty/modality helpers |
| `tests/test_search_discovery.js` | 23 | `didYouMean`, `bestCorrection`, `buildVocabulary`, scoring |

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

# Coverage (core + scripts)
python3 -m pytest tests/ -q --cov=core --cov=scripts --cov-report=term-missing
```

## Coverage Baseline (2026-08-03)

| Scope | Statements | Covered | Coverage |
|-------|-----------:|--------:|---------:|
| `core/` | 4,048 | 3,061 | 75% |
| `core/build_taxonomies.py` | 527 | 390 | 74% |
| `scripts/` | 5,426 | 1,211 | 22% |
| **Combined** | 15,105 | 9,474 | **37%** |

Target: 80% line coverage across `core/` and `scripts/`. Core modules are near target; the combined figure is dragged down by scripts with no direct tests (`scripts/serve_cms.py` 389 stmts, `scripts/fix_orphan_tags.py` 326, `scripts/cms_api.py` 204, `scripts/run_agentic_pipeline.py` 200, `scripts/backfill_content.py` 196). Measure with: `python3 -m pytest tests/ -q --cov=core --cov=scripts --cov-report=term-missing` (takes ~50s).

## Testing Strategy

| Layer | Approach | Tools |
|-------|----------|-------|
| Core modules | Unit tests with mocks | pytest, SimpleNamespace |
| Cognitive architecture | Pure-function tests (schema builder, SM-2, adaptive) | pytest |
| Research provenance | Detection tests (claims, contradictions, grading) | pytest |
| Build pipeline | Smoke tests on output | Path I/O, subprocess |
| Templates | Minimal (snapshot-like assertions) | String matching |
| Content | Registry validation | Pydantic schema validation |
| Scripts | Integration tests (where feasible) | Direct import + mock |
| JS | Pure-function tests via Node (no npm/playwright) | `node tests/test_*.js` (all 4 suites via `run_tests.sh`) |

## Key Patterns

### Mocking `render_template`

Used in `test_build_taxonomies.py`:

```python
from unittest.mock import MagicMock
mock_render = MagicMock(return_value="<html>Rendered</html>")
```

### Testing Bloom Classification

In `test_bloom.py`:

```python
from core.bloom import classify_bloom_level, BLOOM_LEVELS

def test_classify_bloom_level_all_levels():
    for level in BLOOM_LEVELS:
        result = classify_bloom_level(level)
        assert result == level
```

### Testing Brand Tokens

In `test_brand.py`:

```python
from core.brand import resolve_brand_token

def test_resolve_brand_token_logo():
    assert resolve_brand_token("logo", "aml") == "shield-check"
```

### Testing Visuals

In `test_visuals.py`:

```python
from core.visuals import resolve_topic_icon

def test_resolve_topic_icon_subtopic_priority():
    result = resolve_topic_icon("aml", "kyc")
    assert result == "shield"  # brand subtopic icon takes priority
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
| `core/schema_builder.py` | networkx, `core/ontology.py` | ✅ Yes |
| `core/retention_engine.py` | Python stdlib + pydantic | ✅ Yes |
| `core/adaptive.py` | Python stdlib | ✅ Yes |
| `core/build_taxonomies.py` | `config.py`, `core/urls.py` | ✅ Yes |
| `core/build_cache.py` | Python stdlib | ✅ Yes |
| `build.py` | pandas, Jinja2, PIL | ❌ No (slow imports) |

> **See also:** [Unit Tests](unit-tests.md), [Taxonomy Tests](taxonomy-tests.md), [CI Integration](ci-integration.md)
