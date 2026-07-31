# AcaciaFund

A **static-first, cognitive learning platform** that synthesizes research from 32+ authoritative sources (arXiv, Hacker News, PubMed, SEC, FATF, Databricks, and more) into three pillar domains: **Compliance**, **Markets**, and **Data Engineering**.

AcaciaFund is not a traditional content site. It is a schema-building engine grounded in cognitive psychology: every article is classified by Bloom's taxonomy, mapped into an ontology of 192 cross-pillar concepts, connected through prerequisite learning paths, and supported by SM-2 spaced repetition for durable retention.

## Quick Facts

| Metric | Value |
|--------|-------|
| Generated pages | 2,505 |
| Content items | 195 (96 research, 83 learn, 16 knowledge) |
| Ontology concepts | 192 (58 compliance, 64 markets, 70 data) |
| Ontology relations | 434 across 10 relation types |
| Knowledge categories | 13 |
| Pillars | 3 (Compliance, Markets, Data Engineering) |
| Inspiration sources | 32 |
| Tests | 855 (847 Python + 8 JS) |
| Build time | ~76s full, incremental via content hashing |
| Deploy target | Cloudflare Pages (`https://www.acaciafund.org/`) |

## Quick Start

```bash
# Build the site (incremental — uses cache)
python3 build.py

# Full rebuild (clear cache and output)
rm -rf dist .build_cache.json && python3 build.py

# Run tests
python3 -m pytest tests/ -v

# Lint and type check
ruff check .
pyright

# Serve locally (static site + admin CMS on port 8000)
python3 scripts/serve_cms.py
```

## Repository Layout

```
build.py                  # Static site generator (~3,726 lines)
config.py                 # Single source of truth (pillars, URLs, quality thresholds)
core/                     # Business logic: ontology, schema builder, retention engine, etc.
templates/                # Jinja2 templates (layout, content types, admin, partials)
static/                   # CSS design system, JS modules, fonts, images
scripts/                  # Ingestion, enrichment, generation, validation, CMS server
content/                  # Source markdown (per-pillar)
registry.json             # Content registry / data catalog (195 items)
data/                     # Runtime JSON stores (ontology, graph, freshness, metadata)
dist/                     # Build output (static site)
docs/                     # Documentation (architecture, pipeline, testing, reference)
tests/                    # 37 Python test modules + 8 JS tests
```

## Documentation

| Document | Purpose |
|----------|---------|
| [`SYSTEM_ARCHITECTURE.md`](SYSTEM_ARCHITECTURE.md) | The complete system architecture (recommended first read) |
| [`AGENTS.md`](AGENTS.md) | Development guide: commands, invariants, troubleshooting |
| [`ONTOLOGY.md`](ONTOLOGY.md) | Ontology: concepts, relations, philosophical foundations |
| [`URL_STRUCTURE.md`](URL_STRUCTURE.md) | URL hierarchy, slug translation, redirect rules |
| [`CONTENT_ASSESSMENT.md`](CONTENT_ASSESSMENT.md) | Historical content/URL audit (July 2026, resolved) |
| [`docs/`](docs/index.md) | Sectional documentation: pipeline, content, search, testing, ops |

## Architecture in One Paragraph

External sources are ingested into `registry.json` (the content catalog). At build time, `build.py` validates the registry against Pydantic schemas, extracts ontology concepts from each item, renders every page through Jinja2 templates, and generates taxonomies (search index, tag pages, admin dashboards, Atom feed, sitemap). The result is a fully static site — no runtime backend — served from the Cloudflare edge with client-side search, a client-side SM-2 retention engine, and a client-side knowledge graph.

## Development

- Use `python3` (the platform `python` may lack dependencies).
- Read `AGENTS.md` before contributing — it encodes architecture invariants (e.g., *never redefine `PILLAR_URL_MAP` locally*).
- All admin templates must extend `admin/base.html`.
- Run the full test suite before committing: `bash scripts/run_tests.sh`.
