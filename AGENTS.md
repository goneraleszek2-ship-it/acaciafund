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

# Enrich ontology with philosophical foundations metadata
python3 scripts/enrich_philosophy.py

# Philosophy tests (check all concepts have epistemic_status, lineage, etc.)
python3 -u -m pytest tests/test_philosophy_integration.py -v

# Validate cross-pillar analogs (bidirectional check + auto-fix)
python3 scripts/validate_cross_pillar.py
python3 scripts/validate_cross_pillar.py --fix             # auto-add missing reciprocal mappings
python3 scripts/validate_cross_pillar.py --format json

# Audit concept coverage across all content
python3 scripts/audit_concept_coverage.py                  # full re-extraction
python3 scripts/audit_concept_coverage.py --cached         # use build-persisted cache
python3 scripts/audit_concept_coverage.py --fail-on-orphans 5   # CI gate

# Cluster concepts by philosophical lineage
python3 scripts/audit_philosophical_lineage.py
python3 scripts/audit_philosophical_lineage.py --min-cluster 3

# Deploy to Cloudflare
python3 scripts/deploy_cloudflare.py

# Retention Engine — generate concept review data
python3 -c "
from core.ontology import OntologyManager
from core.retention_engine import generate_concept_review_json, save_concept_review_json
mgr = OntologyManager.load('data/ontology.json')
items = generate_concept_review_json(mgr)
save_concept_review_json(items, 'dist/static/review_concepts.json')
print(f'Generated {len(items)} concept review items')
"

# Retention Engine — run tests
python3 -u -m pytest tests/test_retention_engine.py -v
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

**Current state:** ~420 registry items, ~1213 pages, 3 clean pillars, 72 ontology concepts (all with philosophical metadata), 32 inspiration sources. Quality gate: passing. 507 Python tests + 8 JS tests passing.

## Cognitive Architecture (Phase 4)

The portal is being restructured from a *content repository* into a *schema-building engine* grounded in cognitive psychology:

### Framework Principles

| Principle | Source | Portal Mechanism |
|-----------|--------|------------------|
| **Cognitive Load Theory** | Sweller (1988) | Progressive disclosure, worked examples, reduced split attention |
| **Dual Coding** | Paivio (1969) | Visual abstracts + verbal summaries, consistent icon→concept mapping |
| **Schema Theory** | Bartlett (1932), Piaget, Anderson | Learning paths, concept prerequisites, interleaved cross-pillar practice |
| **Spaced Retrieval** | Ebbinghaus, Leitner, SM-2 | Portal-wide review queue, expanding intervals, mastery tracking |
| **Testing Effect** | Roediger & Karpicke | Bloom questions on every page, active recall before passive review |
| **Desirable Difficulties** | Bjork (1994) | Interleaved pillars, graduated difficulty, retrieval-before-exposure |

### Five-Phase Implementation Plan

| Phase | Focus | Key Deliverables | Cognitive Principle |
|-------|-------|------------------|---------------------|
| **1** | Schema Builder & Dual Coding | `core/schema_builder.py`, visual abstracts, concept maps, progressive disclosure JS | Schema formation, dual coding, CLT |
| **2** | Knowledge Structure Reformulation | Learning path DAGs, cross-pillar synthesis views, multi-resolution hierarchy | Schema elaboration, germane load |
| **3** | Retrieval & Retention Engine | Portal-wide SM-2, interleaved practice, gap detection, concept mastery dashboard | Spaced retrieval, testing effect |
| **4** | Research-Grade Features | Source trails, contradiction detection, evidence grading, hypothesis workspace | Metacognition, critical thinking |
| **5** | Adaptive Presentation | Difficulty/interest/modality adaptation, personalized recommendations | Individual differences, expertise reversal |

### Gap Analysis: Current vs Target

#### Already Exists ✓
- SM-2 spaced repetition in `learning_hub.js` + `review.j2` (dashboard) + `review_queue.j2` (flashcard queue)
- Concept detail pages at `/concepts/{id}/` via `concept_detail.j2`
- Knowledge graph at `/graph/` via `graph.j2` (Cytoscape, pillar/relation/layout filters)
- Ontology with directed relations (`requires`, `part_of`, `enables`, `influences`, `detects`, `supersedes`, `regulates`, `measures`)
- Bloom taxonomy questions on learn/knowledge pages
- Visual article fingerprints (tartan SVG patterns)
- Pillar badge macros (`templates/macros/pillar_badge.html`)
- Source freshness checker (32 weekly HTTP checks)
- Cross-pillar content connections (`find_cross_pillar()` in `build.py`)
- Schema builder (prerequisite→path DAG) | `core/schema_builder.py` | P1 ✓
- Visual abstract (SVG + 3-bullet summary) | `templates/partials/visual_abstract.j2` | P1 ✓
- Per-article concept map | `templates/partials/concept_map.j2` | P1 ✓
- Progressive disclosure JS | `static/js/progressive_disclosure.js` | P1 ✓
- **Cognitive Load Amputation**: Simplified homepage (pillar-grid, 3 items each), collapsible pillar sections (`<details>`), reduced article headers (3 elements max), collapsible metadata section | Phase 1.5 ✓
- **Retrieval-First Architecture**: Pre-test gate (`pretest_gate.js`) requires quiz attempt before content | Phase 1.5 ✓
- **Generation Flashcards**: `data-generate` attribute on `<acacia-flashcard>` enables write-before-flip mode | Phase 1.5 ✓

#### Now Exists ✓ (Phase 2B — July 2026)
- **Philosophical foundations layer** integrated into Knowledge content type (not a separate section)
- **Concept model** extended with 10 philosophical metadata fields: `philosophical_lineage`, `epistemic_status`, `normative_basis`, `ontological_commitment`, `temporal_ontology`, `uncertainty_class`, `governance_model`, `semantic_contract_type`, `philosophical_sources`, `cross_pillar_analogs`
- **`scripts/enrich_philosophy.py`** — reads `data/philosophy_metadata.json`, merges into ontology
- **72 ontology concepts** enriched with philosophical metadata (all have `epistemic_status`)
- **4 new template partials**: `philosophical_lineage.j2` (expandable genealogy), `epistemic_badge.j2` (inline epistemic role indicator), `normative_basis.j2` (inline normative theory display), `cross_pillar_philosophy.j2` ("Same pattern in other pillars")
- **`concept_detail.j2`** — shows philosophical lineage, epistemic badge, normative basis, primary sources, cross-pillar analogs
- **`knowledge.j2`** — Concept Explorer shows epistemic badges, lineage tags (up to 3), cross-pillar analog links for each extracted concept
- **11 tests** for philosophy integration (`tests/test_philosophy_integration.py`): model fields, ontology enrichment, pipeline, cross-pillar validation

| File | Purpose |
|------|---------|
| `data/philosophy_metadata.json` | Concept→philosophical metadata mapping (71 concepts) |
| `scripts/enrich_philosophy.py` | Merge philosophy metadata into ontology.json |
| `templates/partials/philosophical_lineage.j2` | Expandable genealogy tree (thinker → concept → technique) |
| `templates/partials/epistemic_badge.j2` | Inline badge: "Constitutive", "Instrumental", "Regulatory", etc. |
| `templates/partials/normative_basis.j2` | "Kantian duty", "Utilitarian", "Rawlsian" indicator |
| `templates/partials/cross_pillar_philosophy.j2` | "Same epistemic pattern in other pillars" section |
| `tests/test_philosophy_integration.py` | 11 tests for philosophical foundations |

#### Now Exists ✓ (Phase 3 — July 2026)
- **Portal-wide concept review** via `RetentionEngine` in `retention_engine.js` — reviews all 72 ontology concepts with SM-2 scheduling
- **Gap detection** (`core/retention_engine.py` + JS) — identifies unseen, overdue (7+ days), and low-mastery (<0.3) concepts
- **Interleaved practice scheduler** — automatically mixes concepts across all 3 pillars, prioritizing due and unseen items
- **Concept mastery dashboard** — rendered dynamically in `review.j2` via `concept-mastery-dashboard` container; shows per-pillar mastery bars, gap reports, and interleaved session trigger
- **`static/review_concepts.json`** — auto-generated at build time from ontology (72 concepts with metadata)
- **38 tests** for retention engine (`tests/test_retention_engine.py`): SM-2 algorithm, mastery scoring, gap detection, interleaving, data generation

| File | Purpose |
|------|---------|
| `core/retention_engine.py` | SM-2 algorithm, gap detection, interleaved scheduling, concept review data generation |
| `static/js/retention_engine.js` | Client-side retention engine: concept review cards, mastery dashboard, interleaved sessions |
| `templates/review.j2` | Updated with concept mastery dashboard section + retention_engine.js |
| `static/review_concepts.json` | Build-generated concept review data (72 concepts, camelCase keys) |
| `tests/test_retention_engine.py` | 38 tests for all retention engine components |

#### Partially Exists ⚠️
- **Learning paths**: `seed_learn.py` has bare prerequisites (`PREREQUISITES` dict with 3 entries)
- **Cross-pillar synthesis**: `find_cross_pillar()` in `build.py` returns concept-shared content, but no matrix/timeline/comparison views

#### Now Improved ✓ (Phase 2 Deepening — July 2026)
- **Learning path template** (`templates/learning_path.j2`): Now includes interactive progress tracking (localStorage checkboxes per node), concept detail page links on every flow node, "Review on Dashboard" button per concept, bloom level badges with cognitive-skill tooltip descriptions, and a progress bar at the top
- **Pillar synthesis template** (`templates/pillar_synthesis.j2`): Now includes cross-pillar analog matrix table showing epistemic-status mapping between concepts in different pillars, enriched bridge cards with per-pillar expandable content lists, bridge count + analog count in header, and review dashboard link
- **`core/learning_paths.py`**: `generate_cross_pillar_synthesis()` now accepts optional `ontology` param; returns `analog_matrix` (concepts → analogs with epistemic status) and `enriched_bridges` (bridges with per-pillar content breakdown)
- **15 learning path pages** + **3 pillar synthesis pages** — all enhanced at build time
- **Cross-pillar analog matrix** leverages the 39 ontology concepts with `cross_pillar_analogs` data

#### Now Exists ✓
| Component | File | Priority |
|-----------|------|----------|
| Source trail (claim→citation mapping) | `core/source_trail.py` | P4 ✓ |
| Contradiction detection | `core/contradiction.py` | P4 ✓ |
| Evidence grading (GRADE-style) | `core/evidence_grade.py` | P4 ✓ |
| Hypothesis workspace | `templates/research_workspace.j2` | P4 ✓ |
| Research export (MD/JSON) | `scripts/export_research.py` | P4 ✓ |
| Adaptive difficulty/interest/modality | `core/adaptive.py` | P5 ✓ |
| | **Build integration** | `build.py` §2866 — source trails, contradictions, evidence grades, adaptive profiles built from content |

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
| `core/schema_builder.py` | **NEW** Schema builder: prerequisite graphs, learning paths, Bloom categorization |
| `static/js/progressive_disclosure.js` | **NEW** Collapsible article sections (Cognitive Load Theory) |
| `templates/partials/visual_abstract.j2` | **NEW** Dual-coded article summary partial (visual abstract) |
| `templates/partials/concept_map.j2` | **NEW** Per-article concept neighborhood map partial |
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
| `partials/visual_abstract.j2` | **NEW** Dual-coded article summary (included in research/learn/knowledge) |
| `partials/concept_map.j2` | **NEW** Prerequisite/dependent concept map (included in concept_detail) |

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
| `tests/test_extractors.py` | **19** | core/extractors.py: timeline, flow, comparison extraction from text |
| `tests/test_check_source_freshness.py` | **8** | scripts/check_source_freshness.py: compute_staleness contract tests |
| `tests/test_source_synthesis.py` | **18** | scripts/source_synthesis.py: extract_tags, synthesis_description, key_insights |
| `tests/test_data.py` | 15 | core/data.py: domain extraction, entity/theme extraction, DLQ writing, logging |
| `tests/test_content.py` | 11 | core/content.py: Content dataclass construction, defaults, dict parsing |
| `tests/test_metadata.py` | 28 | core/metadata.py: manifest building, JSON utils, schema validation |
| `tests/test_contracts.py` | **24** | MOSA architecture contract tests (config schema, module interfaces, signature validation) |
| `tests/test_schema_builder.py` | **19** | core/schema_builder.py: prerequisite graph, learning paths, Bloom categorization |
| `tests/test_progressive_disclosure.js` | **8** | static/js/progressive_disclosure.js: parseSections, toggleSection pure functions |
| `tests/test_retention_engine.py` | **38** | core/retention_engine.py: SM-2, gap detection, interleaving, data generation |
| `tests/test_source_trail.py` | **23** | core/source_trail.py: claim→citation mapping, SourceTrailManager, extraction, verification |
| `tests/test_contradiction.py` | **40** | core/contradiction.py: negation/antonym/numeric contradiction detection, ContradictionDetector, clustering |
| `tests/test_evidence_grade.py` | **24** | core/evidence_grade.py: GRADE-style evidence quality scoring, EvidenceGrader, downgrade/upgrade criteria |
| `tests/test_export_research.py` | **14** | scripts/export_research.py: Markdown/JSON report generation from trails, contradictions, grades |
| `tests/test_adaptive.py` | **31** | core/adaptive.py: user profiling, difficulty adaptation, modality suggestion, content ranking |

JS tests run via `node tests/test_progressive_disclosure.js` (no npm/playwright needed).

**Total: 639 Python tests + 8 JS tests.**

### Phase 1.5 Files (Cognitive Load Amputation — July 2026)

| File | Purpose |
|------|---------|
| `templates/index.j2` | Simplified homepage: pillar cards (3 items each), Learn/Knowledge sections, Featured |
| `templates/pillar_index.j2` | Collapsible sections via `<details>` (Key Terms, Lessons, Concepts) |
| `templates/learn.j2` | Reduced header (3 elements), pre-test gate, generation flashcards, collapsible metadata |
| `templates/blog_post.j2` | Reduced header (3 elements), collapsible metadata section |
| `templates/knowledge.j2` | Reduced header (3 elements), collapsible metadata section |
| `templates/partials/article_metadata.j2` | Reusable collapsible metadata partial (tags + concepts + SQI) |
| `templates/partials/pretest_gate.j2` | Pre-test gate partial (retrieval before exposure) |
| `static/js/pretest_gate.js` | JS for pre-test gate: renders first quiz question, hides body until attempted |
| `static/js/learning_hub.js` | Added `data-generate` attribute for write-before-flip flashcards |
| `static/css/custom.css` | CSS for generation flashcards and collapsible details sections |

### Running Phase 1 Tests

```bash
# Schema builder (Python)
python3 -u -m pytest tests/test_schema_builder.py -v > /tmp/test_sb.log 2>&1

# Progressive disclosure (JS)
node tests/test_progressive_disclosure.js

# All core tests (excludes build-dependent tests that may hang)
python3 -u -m pytest tests/test_schema_builder.py tests/test_ontology.py tests/test_compositor.py tests/test_extractors.py tests/test_contracts.py tests/test_urls.py tests/test_data.py tests/test_content.py tests/test_metadata.py tests/test_learn_generation.py tests/test_build_cache.py tests/test_generate_pages.py tests/test_check_source_freshness.py tests/test_source_synthesis.py tests/test_smoke.py -v > /tmp/test_core.log 2>&1
``` Tests use `python3 -m pytest tests/ -v`. Target: 80% line coverage across core/ and scripts/ (currently at ~55%).

### Testing Strategy

- **Core modules** (`core/urls.py`, `core/ontology.py`) are well-tested.
- **`build.py` and `core/build_taxonomies.py`** are tested via smoke tests only (build output inspection).
- **Scripts** are tested indirectly via workflow integration.
- **Fully tested**: `core/compositor.py` (26), `core/generate_pages.py` (40), `core/extractors.py` (19), `scripts/check_source_freshness.py` (8), `scripts/source_synthesis.py` (18)
- **No unit tests** for: `core/generate.py`, `core/score.py`, `core/visuals.py`, `core/bloom.py`, `core/brand.py`, `core/assets.py`, `scripts/source_verification.py`.

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

## Next Steps — Phase 1: Schema Builder & Dual Coding

The gap analysis at the top of this file shows all components that need to be built. Phase 1 focuses on the four highest-ROI pieces. **Do not proceed to Phase 2 until all Phase 1 deliverables pass their tests, render in the build, and linter/typecheck are clean.**

### Phase 1 Deliverables (priority order)

#### 1. Schema builder (`core/schema_builder.py`) — NEW
Build a module that transforms `ontology.py` prerequisite relations into a learning-path DAG.

```
core/schema_builder.py
├── build_prerequisite_graph(manager) → nx.DiGraph
│   - Directed edges: `requires` relations only
│   - Each node: Concept(id, label, pillar)
│   - Rejects cycles (log warning, skip edge)
├── compute_learning_paths(graph, start_concept_id, depth=3) → List[LearningPath]
│   - BFS from start concept, limited to `depth` hops
│   - Returns ordered list of LearningPath dataclass:
│     │   LearningPath = {
│     │       concepts: List[Concept],
│     │       total_depth: int,
│     │       pillar_span: int,  # how many pillars covered
│     │       start: str,
│     │       end: str,
│     │   }
│   - Multiple paths per start concept (one per viable terminal node)
├── categorize_by_bloom(concept_id, manager) → BloomLevel
    - Maps concept position in DAG to Bloom level:
    │   root/leaf → Remember/Understand
    │   mid-chain → Apply/Analyze
    │   deep → Evaluate/Create
    Return str: "remember" | "understand" | "apply" | "analyze" | "evaluate" | "create"
```

**Tests** (`tests/test_schema_builder.py`):
- Build graph from acyclic seed relations → valid DAG
- Build graph with intentional cycle → no error, edge skipped, warning logged
- Compute learning path: start concept A, depth 2 → path with A→B concepts
- Compute learning path: start concept with no outgoing edges → empty list
- Categorize by bloom: root concept → "remember"
- Categorize by bloom: deep node (depth 3+) → "evaluate" or "create"

**Integration**: The schema builder is a pure computation module. It will be called at build time from `build.py` (or later from `scripts/generate_learning_paths.py`) to generate per-concept learning paths. No template changes yet — we build the data layer first.

#### 2. Visual abstract partial (`templates/partials/visual_abstract.j2`) — NEW
A Jinja2 partial for dual-coded article summaries (dual coding theory). Included at the top of every `research.j2`, `learn.j2`, `knowledge.j2` page.

```
{# templates/partials/visual_abstract.j2 #}
Usage: {% include 'partials/visual_abstract.j2' %}  {# passed article, concept, pillar_config #}

Renders:
┌────────────────────────────────┐
│ 🧩 visual_abstract            │
│ ┌────────────────────────────┐ │
│ │  SVG icon (article type)   │ │
│ └────────────────────────────┘ │
│ 📌 3-bullet summary           │
│   • Key insight 1             │
│   • Key insight 2             │
│   • Key insight 3             │
│ 🏷️ Concept badges             │
│ 📊 bloom level indicator      │
└────────────────────────────────┘

Accepts variables:
- article (dict with title, description, difficulty, content_type)
- concept (dict with id, label for the article's concept)
- pillar_config (dict with color, emoji for the pillar)

SVG icons: Use a simple inline SVG matching the content_type:
  research → book-open icon
  learn → academic-cap icon  
  knowledge → light-bulb icon
Use pillar color for accent.

3-bullet summary: Auto-extract from article.description (split on '.', take first 3 sentences).
Fallback: If description has < 3 sentences, use truncated description + "..." placeholder.
```

**Tests**: No unit tests for a template. Visual verification during build: render at least one article of each type and inspect the partial output.

#### 3. Concept map partial (`templates/partials/concept_map.j2`) — NEW
A Jinja2 partial showing the immediate neighborhood of a concept (prerequisites + dependents).

```
{# templates/partials/concept_map.j2 #}
Usage: {% include 'partials/concept_map.j2' %}  {# passed concept, related_concepts, pillar_config #}

Renders:
┌──────────────────────────────────────────┐
│ 📖 Concept Map                          │
│                                         │
│     [prerequisite A] ← [THIS CONCEPT] → [dependent X] │
│     [prerequisite B] ←                   → [dependent Y] │
│                                         │
│ Legend: ← requires  → enables           │
└──────────────────────────────────────────┘

Accepts:
- concept (Concept dict with id, label, description)
- related_concepts (list of {id, label, relation_type} for all direct relations)
- pillar_config (dict with color)

Layout:
- Top line: "Requires" prerequisites (relation_type="requires") on the left
- Middle: Current concept centered, bold, with pillar color accent
- Bottom line: "Enables" dependents (relation_type="enables") on the right
- If no prerequisites or dependents, show "None" text in muted color
- Show up to 6 concepts per side (truncate with "+N more" if exceeded)

Use arrow CSS or simple text arrows (← / →) for direction.
```

**Tests**: Same — template, verified by rendering one concept page during build.

#### 4. Progressive disclosure JS (`static/js/progressive_disclosure.js`) — NEW
JavaScript for collapsible article sections (Cognitive Load Theory — reduces extraneous load).

```
Applies to: All article pages (research, learn, knowledge, blog_post)

Behavior:
- On page load, find all <section> elements with class "prose-section"
- Each gets a clickable header bar with:
  │ [▶/▼] Section Title
- First section auto-expanded, all others collapsed
- Click toggles collapse/expand with smooth animation (CSS transition)
- Saves section open/close state to sessionStorage per-page

Implementation:
- Vanilla JS, no dependencies
- Targets: document.querySelectorAll('section.prose-section')
- Each section must have a <h2> or <h3> as first child for the title
- Toggle: class "is-collapsed" on the section (CSS: .is-collapsed > *:not(.section-header) { display: none })
- Smooth transition via max-height animation
- Session state key: `acacia_disclosure_{page_slug}`

CSS (add to existing post.css or main.css):
- .section-header { cursor: pointer; user-select: none; display: flex; align-items: center; gap: 0.5rem; }
- .section-header::before { content: '▶'; transition: transform 0.2s; }
- .section-header.is-expanded::before { content: '▼'; }
- .prose-section.is-collapsed { max-height: 3rem; overflow: hidden; transition: max-height 0.3s ease; }
- .prose-section { max-height: none; transition: max-height 0.3s ease; }
```

**Tests** (`tests/test_progressive_disclosure.py`):
- HTML fixture with 3 sections → JS should collapse all but first
- `sessionStorage` state is read on page load
- Click on collapsed section header → section expands
- Click on expanded section header → section collapses
- State persists across page reload (sessionStorage read)

Use Playwright or simple DOM testing. If Playwright setup is heavy, write the test as a pure function test:
```
parse_sections(html_string) → sections: List[Dict]
toggle_section(sections, index) → new_sections: List[Dict]
```
Then test the pure functions.

### Agent Instructions

For any agent working on this codebase:

1. **Always read AGENTS.md first** — it contains architecture invariants, build commands, and testing requirements
2. **Phase 1 end-to-end**: Implement items 1-4 above in order. Each must have tests before moving to the next.
3. **Test first**: Write tests in `tests/test_schema_builder.py` and `tests/test_progressive_disclosure.py` before implementing modules. For templates, verify during build.
4. **No new dependencies**: Schema builder uses only `networkx` (already installed). JS uses vanilla JS. Templates use Jinja2 (already installed).
5. **Verify after each item**:
   ```bash
   # Run Phase 1 tests
   python3 -u -m pytest tests/test_schema_builder.py tests/test_progressive_disclosure.py -v > /tmp/test_phase1.log 2>&1
   # Lint
   ruff check core/schema_builder.py static/js/progressive_disclosure.js templates/partials/
   # Typecheck
   pyright core/schema_builder.py
   # Build test (verify partials render)
   python3 build.py 2>&1 | tail -20
   ```
6. **Credit**: Add yourself to `AGENTS.md` credits after completing Phase 1.

### Credits

Contributors who completed Phase 1 (Schema Builder & Dual Coding):
- **opencode (big-pickle)** — core/schema_builder.py implementation (build_prerequisite_graph, compute_learning_paths, categorize_by_bloom, Feynman learning path system)
- **opencode (big-pickle)** — core/source_trail.py implementation (claim→citation mapping, SourceTrailManager, claim extraction, URL matching)
- **opencode (big-pickle)** — core/contradiction.py implementation (negation/antonym/numeric contradiction detection, ContradictionDetector, contradiction clustering)
- **opencode (big-pickle)** — core/evidence_grade.py implementation (GRADE-style evidence quality scoring, EvidenceGrader, downgrade/upgrade criteria with contradiction integration)
- **opencode (big-pickle)** — templates/research_workspace.j2 (hypothesis workspace template with claim/contradiction/evidence views)
- **opencode (big-pickle)** — scripts/export_research.py (Markdown/JSON research report export from source trails, contradictions, and grades)
- **opencode (big-pickle)** — core/adaptive.py (adaptive presentation engine: UserProfile, difficulty adaptation, modality suggestion, content ranking)
