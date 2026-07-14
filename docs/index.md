# AcaciaFund Documentation

AcaciaFund is a **static-first content platform** that synthesizes research from 32+ authoritative sources into three pillar domains: **Compliance**, **Markets**, and **Data Engineering**. It uses a Bloom-taxonomy-driven content model (Research → Learn → Knowledge), an ontology-backed knowledge graph, and a privacy-preserving client-side search system.

## Quick Links

| Section | Description |
|---------|------------|
| [01 — Architecture](01-architecture/overview.md) | System design, pillars, data model, data flow |
| [02 — Build Pipeline](02-build-pipeline/build-overview.md) | Build phases, incremental cache, taxonomy generation |
| [03 — Content System](03-content-system/registry-schema.md) | Registry, content types, SQI quality gates, learn modules |
| [04 — Ontology & Knowledge Graph](04-ontology-knowledge-graph/ontology-model.md) | Ontology models, concept extraction, Cytoscape graph |
| [05 — Search & Discovery](05-search-discovery/client-side-search.md) | Client-side fuzzy search, facets, concept boosting |
| [06 — Admin & Observability](06-admin-observability/admin-dashboard.md) | 12 admin pages, quality, telemetry, Plausible events |
| [07 — Deployment & Ops](07-deployment-ops/cloudflare-deploy.md) | Cloudflare Pages, weekly refresh, redirects, monitoring |
| [08 — Testing & Quality](08-testing-quality/test-overview.md) | 143 tests, pytest, ruff, pyright, CI integration |
| [Reference](reference/config-reference.md) | Config constants, CLI commands, templates, schemas |
| [Diagrams](diagrams/architecture.mmd) | Mermaid architecture and flow diagrams |

## Key Stats

| Metric | Value |
|--------|-------|
| Total pages | ~810 |
| Registry items | ~280 |
| Pillars | 3 (Compliance, Markets, Data) |
| Ontology concepts | 48 |
| Ontology relations | 47 |
| Inspiration sources | 32 |
| Learn modules | 54 (18/pillar) |
| Knowledge categories | 11 × 3 pillars = 33 buckets |
| Tests | 163+ across 8 test files |
| Deploy target | Cloudflare Pages (`https://www.acaciafund.org/`) |

## Development Quick Start

```bash
# Build
python3 build.py

# Build (full rebuild, no cache)
rm -rf dist .build_cache.json && python3 build.py

# Run tests
python3 -m pytest tests/ -v

# Lint
ruff check .

# Type check
pyright
```

> **See also:** [Build Pipeline Overview](02-build-pipeline/build-overview.md) for detailed build phases and [CLI Commands](reference/cli-commands.md) for the full script reference.
