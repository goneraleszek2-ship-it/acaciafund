# AcaciaFund Architecture Blueprint

This document defines the fundamentals-first target architecture for a 2026-ready AcaciaFund platform.

## Goal

- Keep the public site static, fast, and cheap to serve.
- Make synthesis deterministic and reproducible.
- Treat metadata as a first-class product.
- Separate publishing from stateful services.
- Keep learning local-first by default, with optional sync.

## Current Lessons

- `ingest.py` is the correct entry point for scheduled synthesis.
- `core/analyze.py` and `core/score.py` are the right place for deterministic ranking and quality signals.
- `core/generate.py` should remain the final publish stage, not a mixed orchestration layer.
- `learning_hub.js` is a good local-first progress model.
- `layouts/` should stay thin and mostly presentational.
- `services/api/` is useful, but it must stay a separate runtime boundary.

## Target Stack

- Python + Jinja2 for the public site (no build framework).
- Python for ingestion, classification, and content generation.
- GitHub Actions for scheduled runs, validation, and deployment.
- Cloudflare Pages for static hosting.
- Cloudflare Workers for lightweight API and edge logic.
- Cloudflare D1 for progress, run state, and metadata registry.
- Cloudflare R2 for snapshots, archives, and generated assets.

Content is generated entirely by Python — no Hugo, no Astro, no build framework. The output is ready-to-serve static HTML.

## System Shape

```text
raw sources -> bronze -> silver -> gold -> publish
```

- Bronze: raw fetches from Hacker News, arXiv, and any future sources.
- Silver: normalized stories, lessons, entities, scores, and lineage records.
- Gold: static HTML pages, SVG images, search index, and user-facing artifacts.

## Data Contracts

Every generated object should carry explicit metadata.

- `content_id`
- `source_url`
- `canonical_url`
- `pillar`
- `tags`
- `bloom_level`
- `sqi`
- `entities`
- `topics`
- `created_at`
- `ingested_at`
- `published_at`
- `checksum`
- `version`
- `lineage`
- `quality_flags`

## Metadata Rules

- Every run must be uniquely identifiable.
- Every story bundle must be reproducible from source inputs.
- Every asset must have a checksum and a versioned path.
- Every generated page must reference its source record.
- Every manual override must be visible in lineage.

## Runtime Components

- Scheduler: triggers synthesis on a cadence and on demand.
- Fetch layer: pulls HN and arXiv, caches requests, and records source state.
- Analysis layer: classifies pillar, computes SQI, extracts entities, and detects trends.
- Generation layer: `generator.py` emits static HTML, SVG assets (fractal thumbnails, chart SVGs, OG images), and search index.
- Public site: Jinja2 renders static pages and vanilla JS handles search.
- Learning layer: renders lessons, quizzes, and Bayes demo.
- Sync layer: stores optional progress and future learner state.

## Deployment Topology

- `main` branch pushes rebuild the site.
- Scheduled workflows ingest new data and publish only when output changes.
- Preview builds validate content and layout before release.
- Static output goes to Cloudflare Pages.
- Small stateful endpoints go to Workers + D1.
- Large or historical artifacts go to R2.

## Migration Path

### Phase 1: Stabilize

- Freeze the current pillar taxonomy.
- Add metadata manifests for generated content.
- Fix route and build inconsistencies.
- Separate source data from generated output.

### Phase 2: Contract

- Introduce schema validation for stories, lessons, runs, and assets.
- Store run summaries in a registry.
- Make generation idempotent.
- Add quality flags for incomplete or low-confidence outputs.

### Phase 3: Scale

- Move sync/state to D1 or equivalent edge storage.
- Add branch previews and artifact versioning.
- Add observability for freshness, failure rate, and output volume.
- Make search and lesson progress resilient to offline use.

### Phase 4: Harden

- Add rollback by version.
- Keep secrets out of source and templates.
- Enforce schema checks in CI.
- Alert on pipeline failures and missing source feeds.

## Repository Blueprint

```text
./
├── core/               # visual engine (fractal, chart, topic overlays)
├── schemas.py          # Pydantic models for content contracts
├── registry.json       # content metadata catalog (51 entries)
├── generator.py        # main build pipeline: Jinja2 → static HTML
├── templates/          # Jinja2 templates (11 files)
├── static/             # CSS, JS, fonts (self-hosted)
├── content/            # source markdown for static pages
├── services/api/       # optional stateful service boundary
├── .github/workflows/  # CI/CD for API deployment
└── dist/               # generated output (60+ pages)
```

## Quality Gates

- Build must succeed from a clean checkout.
- Generated content must validate against schema.
- Site must render without missing required pages.
- Public pages must be responsive and accessible.
- Search index must match published content.
- Progress sync must fail safe when the API is unavailable.

## Current Deployment Problems To Solve

- Keep a single source of truth for environment configuration.
- Avoid mixing build artifacts with handwritten content paths.
- Remove duplicate or ambiguous backend routes.
- Avoid making the site depend on the API for core browsing.
- Avoid non-idempotent generation that creates drift between runs.

## Operating Principles

- Deterministic over clever.
- Metadata over implicit behavior.
- Static over dynamic unless the feature truly needs state.
- Small contracts over large hidden coupling.
- Reproducible over manual.

## Definition Of Done For The New Platform

- A run can be replayed from registry data.
- A page bundle can be traced to source records.
- A learner can use the site without signing in.
- A learner can optionally sync progress.
- The public site deploys independently from the state layer.
- The system scales by adding more source feeds, not by rewriting the stack.
