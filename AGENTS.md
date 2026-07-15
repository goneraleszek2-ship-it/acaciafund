# AGENTS.md — AcaciaFund Development Guide

## Quick Commands

```bash
# Build (full rebuild, clears cache)
rm -rf dist .build_cache.json && python3 build.py

# Build (incremental, uses cache)
python3 build.py

# Tests
python3 -m pytest tests/ -v

# Lint
ruff check .

# Type check
pyright

# Source freshness check (32 inspiration sources)
python3 scripts/check_source_freshness.py
python3 scripts/check_source_freshness.py --update-ontology

# Link check + SQI audit
python3 scripts/check_links_and_sqi.py --dist-dir dist

# Regenerate ontology
python3 -c "
from core.ontology import OntologyManager
m = OntologyManager()
m.seed_all_pillars()
m.seed_relations()
m.save('data/ontology.json')
"

# Regenerate glossaries
python3 scripts/generate_glossaries.py

# Regenerate learn modules
python3 scripts/generate_learn_modules.py

# Backfill SQI for all items missing it
python3 scripts/backfill_sqi.py

# Slug migration (dry-run / apply / check)
python3 scripts/migrate_slugs.py
python3 scripts/migrate_slugs.py --apply
python3 scripts/migrate_slugs.py --check

# Validate concept extraction (check for false positives)
python3 -c "
from core.ontology import OntologyManager, extract_concepts_from_text
m = OntologyManager.load('data/ontology.json')
tests = [
    ('streaming data pipeline', 'str should NOT match'),
    ('about our data', 'beneficial-ownership should NOT match'),
    ('Know Your Customer compliance', 'kyc SHOULD match'),
    ('suspicious transaction report filing', 'str SHOULD match'),
]
for text, desc in tests:
    result = extract_concepts_from_text(text, m)
    ids = [c.id for c, s in result]
    print(f'  {desc}: {ids}')
"

# Deploy to Cloudflare
python3 scripts/deploy_cloudflare.py
```

## System Evolution Summary

This codebase has been built in sequential sprints. Understanding what came before prevents rework.

| Sprint | What shipped |
|--------|-------------|
| 1-2 | Security, git hygiene, CI optimization, monolith decomposition |
| 3 | Registry dedup, SQI backfill, schema enforcement, tests |
| Pillar quality | Taxonomy, enrichment, content, templates |
| Build robustness | Dead code handling, paths, timeouts, encodings |
| URL restructure | AML→compliance, stock→markets, `PILLAR_URL_MAP` |
| Knowledge taxonomy | 11 knowledge categories with icons |
| Phase 1 | Ontology framework (`core/ontology.py`), concept badges, external references |
| Phase 2 | Source synthesis, glossary generation, SQI semantic bonus, weekly refresh |
| Phase 3 | Learn modules (56), concept explorer, pillar landing pages, graph filter |
| Phase 0 | Pillar normalization, model extensions, admin base template |
| Phase 1C-E | Ontology CRUD, telemetry export, source freshness |
| Search | Client-side fuzzy search with concept boosting |
| Foundation fixes | Concept extraction word-boundary fix, alias expansion, full category remapping, knowledge-to-pillar mapping, description backfill |
| Quality fixes | SQI backfill script, search recall improvement (threshold 0.35, body window 800), niche concept alias expansion |

**Current state:** ~280 registry items, ~810 pages, 3 clean pillars, 48 ontology concepts (all with valid PILLAR_SUBCATEGORIES), 32 inspiration sources. Quality gate: passing (all 263 items ≥ 0.65).

## Architecture

### Pillar System

Three pillars with internal keys and URL segments:

| Internal Key | URL Segment | Label | Items |
|---|---|---|---|
| `aml` | `compliance` | Compliance | 92 |
| `stock` | `markets` | Markets | 61 |
| `data-engineering` | `data` | Data Engineering | 107 |

**Single source of truth:** `config.py` → `PILLAR_URL_MAP`

Navigation shows only: Compliance, Markets, Data.

### URL Hierarchy

```
/{pillar_url}/research/{topic}     # 163 items
/{pillar_url}/learn/{topic}        # 54 items (18 per pillar)
/{pillar_url}/knowledge/{topic}    # 43 items
/{pillar_url}/glossary             # Auto-generated from ontology
/knowledge/{platform-page}         # Cross-pillar (12 pages)
/search/?q=query                   # Client-side search
/admin/*.html                      # 12 admin dashboard pages
/graph/                            # Cytoscape knowledge graph
```

### Content Categories

**Research** (163): External content ingestion from arXiv, HN, PubMed
**Learn** (54): Interactive modules with Bloom questions, flashcards, code examples
**Knowledge** (43): Platform docs, glossary, tutorials, methodology

### Pillar Content Distribution

Each pillar has subcategories defined in `config.py` → `PILLAR_SUBCATEGORIES`:
- Compliance: 14 subcategories (risk-assessment, cdd-kyc, sar-str, regtech, sanctions, etc.)
- Data Engineering: 14 subcategories (pipeline-architecture, streaming, batch-processing, etc.)
- Markets: 14 subcategories (market-microstructure, volatility-analysis, trading-strategies, etc.)

### Knowledge Categories

13 knowledge categories defined in `build.py` → `KNOWLEDGE_CATEGORIES`: platform, guide, reference, architecture, foundations, advanced-techniques, best-practices, regulations, industry-analysis, market-analysis, strategies, methodology, tutorial-code.

| Category | Icon | Description |
|---|---|---|
| `platform` | ⚙️ | About AcaciaFund — mission, team, contact, operations |
| `guide` | 🧭 | Methodology, taxonomy, and how-to guides |
| `reference` | 📖 | Glossaries, tool landscapes, technical terminology |
| `architecture` | 🔗 | System design, pipeline architecture, DataOps |
| `foundations` | 📚 | Core concepts and theoretical frameworks |
| `advanced-techniques` | 🔬 | Specialized algorithms and advanced implementations |
| `best-practices` | ✅ | Practical guides, optimization strategies |
| `regulations` | 📋 | Regulatory frameworks and compliance analysis |
| `industry-analysis` | 📊 | Market trends, industry reports, sector analysis |
| `market-analysis` | 📈 | Market dynamics, volatility, financial analysis |
| `strategies` | 🎯 | Trading and investment strategies |
| `methodology` | 🧪 | Research methods, backtesting frameworks |
| `tutorial-code` | 💻 | Step-by-step tutorials with executable code |

Knowledge items use cross-pillar categories. To resolve them to pillar-specific subcategories, use `config.py` → `KNOWLEDGE_TO_PILLAR_CATEGORY`. This maps each knowledge category to the appropriate pillar subcategory for breadcrumb/navigation display.

### Content Pipeline

```
scripts/knowledge_ingester.py  →  registry.json  →  build.py  →  dist/
                                                          |
                                              core/build_taxonomies.py (admin, search, tags, pillar pages)
                                              core/build_cache.py (incremental builds)
                                              core/ontology.py (concept extraction)
                                              scripts/generate_learn_modules.py (learn content)
                                              scripts/generate_glossaries.py (glossary pages)
```

### Key Files

| File | Purpose |
|---|---|
| `config.py` | `PILLAR_URL_MAP`, `PILLAR_URL_REVERSE`, `PILLAR_SUBCATEGORIES`, `PILLAR_EMOJIS`, `PILLAR_NAMES`, site config |
| `build.py` | Main build (~3394 lines) — content rendering, graph, admin, search, feed, cross-pillar synthesis |
| `core/urls.py` | Pure URL helpers (`slug_to_path`, `slug_to_fspath`, `canonical_path`, `slug_to_url`, `pillar_to_url`, `url_to_pillar`) |
| `core/ontology.py` | Ontology framework: Concept, Relation, ResourceLink, InspirationSource models; OntologyManager; concept extraction; Cytoscape export |
| `core/build_taxonomies.py` | Taxonomy generation: admin pages, search index, tag pages, pillar pages, feed, ontology admin |
| `core/build_cache.py` | Incremental build cache with parallel_map support |
| `schemas.py` | Pydantic models for registry validation (`RegistryData`) |
| `registry.json` | Content registry (260 items) |
| `seed_learn.py` | Learn module prerequisites and curated relations |
| `scripts/check_source_freshness.py` | HTTP HEAD checker for 32 inspiration sources |
| `scripts/check_links_and_sqi.py` | Broken link checker + SQI audit + external reference inventory |
| `scripts/backfill_sqi.py` | SQI backfill for all items missing quality scores |
| `scripts/knowledge_ingester.py` | Multi-pillar knowledge ingestion (arXiv, HN, PubMed) with ontology concept extraction |
| `scripts/source_synthesis.py` | Source synthesis with inspiration source matching and concept provenance |
| `scripts/source_verification.py` | Source verification with inspiration domain recognition |
| `scripts/generate_glossaries.py` | Auto-generate per-pillar glossary pages from ontology concepts |
| `scripts/generate_learn_modules.py` | Auto-generate interactive learn modules with Bloom questions, flashcards, code examples |
| `scripts/fetch_images.py` | Unsplash image fetching (imported by `core/build_taxonomies.py` as `CURATED_KNOWN`) |
| `scripts/deploy_cloudflare.py` | Cloudflare Pages deployment trigger |
| `etc/pillars.toml` | Pillar definitions + `[inspiration_sources]` (32 authoritative sources per pillar) |
| `data/ontology.json` | Persisted ontology (48 concepts, 47 relations) |
| `data/source_health.json` | Persistent freshness data (32 sources) |
| `.github/workflows/source-refresh.yml` | Weekly Monday 04:00 UTC refresh — ontology, glossary, freshness, build, deploy |

### Admin Dashboard

12 admin pages at `/admin/*.html`, all extending `admin/base.html`:
- **Overview**: dashboard, quality, coverage, telemetry
- **Content**: articles, gallery, manifest, pipeline
- **Intelligence**: sources, ontology

`admin/base.html` extends `layout.j2` and provides shared sidebar navigation. All admin templates MUST use `{% extends "admin/base.html" %}` and fill `{% block admin_content %}`.

### Templates

| Template | Purpose |
|---|---|
| `layout.j2` | Base site layout (header, footer, dark mode, nav) |
| `admin/base.html` | Admin layout with sidebar (extends `layout.j2`) |
| `research.j2` | Research article pages |
| `learn.j2` | Learn module pages with flashcards, Bloom questions |
| `knowledge.j2` | Knowledge pages with concept badges, Further Reading |
| `blog_post.j2` | Cross-pillar connections, ontology concepts, external references |
| `pillar_index.j2` | Pillar landing pages with Key Terms, Concept Cloud |
| `search.j2` | Search page with styled input, results container |
| `graph.j2` | Cytoscape knowledge graph with pillar filter |
| `tag_index.j2` | Tag archive pages |
| `admin/*.html` | 12 admin dashboard pages |

### Search System

Client-side fuzzy search via `static/js/search.js`:
- Fetches `static/search-index.json` at page load
- Scores by title (+10), ontology_concepts (+6), tags (+4), description (+2)
- Concept boost from `concept_boost` field
- **Facet filters**: Pillar (Compliance/Markets/Data), Type (Research/Learn/Knowledge), Difficulty (Beginner/Intermediate/Advanced) with URL sync and reset button
- **Keyboard navigation**: `/` to focus search, `↑/↓` to select results, `Enter` to open, `Esc` to clear/blur
- Renders result cards with pillar pill, content type, difficulty, date, SQI badge, concept badges, tags
- URL sync via `?q=` parameter (200ms debounce) and `?f_pillar=`, `?f_type=`, `?f_difficulty=` for filters

### Source Freshness

32 inspiration sources from `etc/pillars.toml` are HTTP-checked weekly:
- `scripts/check_source_freshness.py` — HEADs each source, writes `dist/source_health.json` + `data/source_health.json`
- Admin sources page shows freshness badge and per-source status
- `--update-ontology` flag merges freshness data into `data/ontology.json`
- Status categories: active (2xx-3xx), degraded (4xx), error (5xx/timeout)

### Ontology Framework

`core/ontology.py` — Pydantic v2 models:

- **Concept**: id, label, pillar, category, aliases, confidence_score, source_inspiration
- **Relation**: source_id, target_id, relation_type, strength, pillar (directed)
- **ResourceLink**: concept_id, url, status, last_verified, http_status
- **InspirationSource**: url, name, frequency, relevance, pillar, status, last_verified, http_status

**OntologyManager**: add_concept, get_concept, resolve_alias, find_concepts, concepts_by_pillar, add_relation, relations_for, related_concepts, to_dict/from_dict, save/load, to_cytograph_nodes/edges, merge_into_cytograph, seed_pillar, seed_all_pillars, seed_relations

**Concept extraction**: `extract_concepts_from_text(text, manager)` — keyword matching against labels and aliases

**Cytoscape integration**: Concepts exported as `ont:{id}` nodes (teal), relations as `ont-rel:{i}` edges

## Invariants

1. **Never redefine `PILLAR_URL_MAP` locally.** Always `from config import PILLAR_URL_MAP`. Scripts that redefine it create divergence with the build.

2. **Slugs in `registry.json` use internal keys.** The build translates them via `slug_to_fspath()` in `core/urls.py`. Slug format: `{pillar}/{content_type}/{topic}`.

3. **`core/urls.py` has no heavy dependencies.** It only imports from `config.py`. This makes it safe for tests to import without triggering pandas/jinja2/PIL.

4. **Platform knowledge pages stay at `/knowledge/`.** Only domain-specific knowledge gets pillar prefixes.

5. **URL_STRUCTURE_VERSION in `config.py` must be bumped** when slug structure changes (forces full cache rebuild). Currently `"3.0"`.

6. **All admin templates MUST extend `admin/base.html`** and fill `{% block admin_content %}`. Do NOT use `layout.j2` directly for admin pages.

7. **Ontology models use Pydantic v2** (`BaseModel`, `Field`, `model_dump()`). Concept uses `label` (not `name`) for display. Relation uses `strength` (not `weight`).

8. **`OntologyManager.load()` is a `@classmethod`**, not a regular method. `extract_concepts_from_text()` is a standalone function.

9. **`build.py` imports from `core/build_taxonomies.py`** for admin, search, tag, pillar, and feed generation. These functions take `render_template`, `ctx_base`, `output_dir` as arguments.

10. **External dependencies**: pandas, jinja2, Pillow, pydantic (core). yfinance, polars, dedupe (pillar-specific). Core deps only needed for `build.py`; `core/urls.py` and `core/ontology.py` are lightweight.

11. **Use `python3` everywhere.** The platform `python` may lack dependencies.

12. **Registry items use `content_type` field** with values: `research`, `learn`, `knowledge`. Items have `pillar` with internal keys (`aml`, `stock`, `data-engineering`).

## Pillar-Specific Python Libraries

### Compliance/AML (`aml` pillar)

| Library | Use Case | Import |
|---------|----------|--------|
| **dedupe** (3.0.3) | Entity resolution, fuzzy matching, deduplication for KYC/CDD | `import dedupe` |
| **spaCy** (3.8.13) | NLP entity extraction, adverse media screening | `import spacy` |
| **NetworkX** | Graph analytics for fund flow tracing, network analysis | `import networkx as nx` |

```python
# Entity resolution example
import dedupe
fields = [
    {'field': 'name', 'type': 'String'},
    {'field': 'address', 'type': 'String'},
    {'field': 'company', 'type': 'String'},
]
deduper = dedupe.Dedupe(fields)
```

### Markets/Stock (`stock` pillar)

| Library | Use Case | Import |
|---------|----------|--------|
| **yfinance** (1.5.1) | Yahoo Finance data (stocks, ETFs, indices) | `import yfinance as yf` |
| **polars** (1.42.1) | Fast DataFrame processing (5-50x faster than pandas) | `import polars as pl` |

```python
# Market data example
import yfinance as yf
ticker = yf.Ticker('AAPL')
hist = ticker.history(period='1mo')
print(hist[['Close', 'Volume']])

# Fast processing example
import polars as pl
df = pl.scan_parquet('data/*.parquet')
result = df.filter(pl.col('price') > 100).collect()
```

### Data Engineering (`data-engineering` pillar)

| Library | Use Case | Import |
|---------|----------|--------|
| **polars** (1.42.1) | Fast DataFrame for ETL pipelines | `import polars as pl` |
| **pyarrow** (24.0) | Parquet/columnar storage | `import pyarrow as pa` |
| **SQLAlchemy** (2.0.51) | Database toolkit | `from sqlalchemy import create_engine` |

## Known Issues & Tech Debt

### Critical
- **`services/mem0/` does not exist.** 6 mem0 scripts archived in `scripts/archive/`. `build.py` wraps the import in try/except (line 99-104).
- **`scripts/execute_fixes.py`** depends on external LLM APIs. Now archived in `scripts/archive/execute_fixes.py`.

### Warning
- **`config.py` vs `build.py`** — `PILLAR_CONFIG`, `PILLAR_EMOJIS`, `PILLAR_NAMES`, `PILLAR_COLORS`, `PILLAR_FINGERPRINT_COLORS` all live in `config.py` now. `build.py` imports from config. **No duplication.**
- **Concept extraction threshold**: `build.py` uses `>= 0.35` for concept cache and inline extraction. `extract_concepts_from_text()` default is `>= 0.5`. If extraction is too strict/loose, adjust these thresholds.

## Testing

### Test Files

| File | Tests | Coverage |
|---|---|---|---|
| `tests/test_ontology.py` | 39 | Ontology models, manager, extraction, seeding |
| `tests/test_learn_generation.py` | 14 | Learn module generation pipeline |
| `tests/test_urls.py` | 18 | URL helpers, pillar mapping, slug conversion |
| `tests/test_build_cache.py` | 18 | Build cache, incremental builds |
| `tests/test_smoke.py` | 34 | Registry validation, schema enforcement |
| `tests/test_build_smoke.py` | 12 | Build output verification |
| `tests/test_redirects.py` | 8 | Redirect rules validation |
| `tests/test_build_taxonomies.py` | 51 | Taxonomy generation (all 5 generators) |
| `tests/test_compositor.py` | **26** | core/compositor.py: SVG renderers (timeline, flow, comparisons, badges, numbers, connections) |
| `tests/test_generate_pages.py` | **40** | core/generate_pages.py: extract_headings, find_related, reading_time, sanitize, SQI badge, fingerprint |
| `tests/test_data.py` | 15 | core/data.py: domain extraction, entity/theme extraction, DLQ writing, logging |
| `tests/test_content.py` | 11 | core/content.py: Content dataclass construction, defaults, dict parsing |
| `tests/test_metadata.py` | 28 | core/metadata.py: manifest building, JSON utils, schema validation |

**Total: ~361 tests.** Tests use `python3 -m pytest tests/ -v`.

### Testing Strategy

- **Core modules** (`core/urls.py`, `core/ontology.py`) are well-tested.
- **`build.py` and `core/build_taxonomies.py`** are tested via smoke tests only (build output inspection).
- **Scripts** are tested indirectly via workflow integration.
- **No unit tests** for: `core/compositor.py`, `core/generate.py`, `core/generate_pages.py`, `core/score.py`, `core/visuals.py`, `core/bloom.py`, `core/brand.py`, `core/assets.py`, `scripts/check_source_freshness.py`, `scripts/source_synthesis.py`, `scripts/source_verification.py`.

### Running Tests

```bash
# Run all tests (redirect to file to avoid Python 3.14 pipe buffering)
bash scripts/run_tests.sh

# Run specific test file
bash scripts/run_tests.sh tests/test_ontology.py -v

# Or manually (always redirect to file)
python3 -u -m pytest tests/ -v > /tmp/test_results.log 2>&1
```

## Troubleshooting

### Build skips all items (incremental build not picking up changes)
- Check `.build_cache.json` — if version doesn't match, cache auto-clears
- Delete `.build_cache.json` and rebuild: `rm -rf dist .build_cache.json && python3 build.py`

### Tests timeout importing `build.py`
- `build.py` imports pandas/jinja2/PIL. Tests should import from `core/urls.py` instead.
- Use `python3` (not `python`) — the platform `python` may lack dependencies.
- If tests hang, use `timeout 300 python3 -m pytest tests/ -v`.

### Stale `/aml/` paths in output
- Check that `scripts/migrate_slugs.py`, `scripts/generate_content.py`, and `scripts/knowledge_ingester.py` import from `config` (not local redefinition).
- Rebuild after fixing: `rm -rf dist .build_cache.json && python3 build.py`

### Slug collisions
- Run `python3 scripts/migrate_slugs.py --check` to validate
- The migration script auto-resolves collisions with numeric suffixes

### Search index is empty
- `dist/static/search-index.json` is generated by `core/build_taxonomies.py` → `generate_search_pages()` during build
- Run a full rebuild: `rm -rf dist .build_cache.json && python3 build.py`
- Check `dist/build-meta.json` for `search_index_entries` count

### Admin pages not rendering
- All admin templates must extend `admin/base.html` (not `layout.j2` directly)
- Admin context requires `active_page` variable for sidebar highlighting
- Build generates admin pages via `generate_admin_pages()` in `core/build_taxonomies.py`

### Source freshness data missing
- Run `python3 scripts/check_source_freshness.py --update-ontology`
- Check `data/source_health.json` exists and has `sources` array
- Admin sources page reads from `dist/source_health.json` merged during build

### Build errors in logs
- Check `dist/build_errors.log` — should be 0 bytes (empty = no errors)
- If non-empty, check for Jinja2 template errors, missing registry fields, or import failures

## Deployment

- **Platform**: GitHub Actions → Cloudflare Pages at `https://www.acaciafund.org/`
- **Deploy script**: `python3 scripts/deploy_cloudflare.py` triggers `workflow_dispatch`
- **Weekly refresh**: `.github/workflows/source-refresh.yml` — Monday 04:00 UTC
  - Regenerates ontology, glossaries
  - Runs source synthesis + verification
  - Checks source freshness (32 sources)
  - Full rebuild
  - Links check + SQI audit
  - Uploads artifacts (30-day retention)
  - Commits `data/ontology.json`, `registry.json`, `data/source_health.json`

## Next Steps (Priority Order)

1. **Graph visualization enhancements** — Relation-type filter, layout toggle (force vs hierarchical), cross-pillar edge styling
2. **Add tests** — `core/generate.py` helpers, `scripts/check_source_freshness.py` compute_staleness, `scripts/source_synthesis.py` pure functions
3. **Knowledge ingestion run** — `knowledge_ingester.py --pillar aml --source all --days 7` for latest AML content
