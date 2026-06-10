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
- Inline `<script>` in templates handles quiz engine, progress tracking, and flashcard interactions — no external JS dependencies for learning features.
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
- Generation layer: `build.py` emits static HTML, SVG assets (fractal thumbnails, chart SVGs, OG images), and search index.
- Visual management system (`core/images/`): 3-tier image pipeline ensuring every article section has a visual — manifests (editorial override) → auto-fetch (Openverse/Wikimedia/NASA/LoC APIs) → inline SVG fallback (pillar-colored with section-type icons). Deterministic fallback, zero gaps.
- Public site: Jinja2 renders static pages and vanilla JS handles search.
- Learning layer: renders lessons (difficulty-grouped), quizzes (Bloom taxonomy with live scoring), flashcards (CSS 3D flip), progress tracking (localStorage), spaced repetition tracking, and interleaved practice (shuffle).
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
├── config.py           # Single source of truth: SITE_URL, paths, env constants
├── core/
│   ├── visuals.py      # fractal / chart / OG image SVG engine
│   └── images/         # 3-tier visual management system
│       ├── manifest.py     # Tier 1: editorial overrides (manifest.json)
│       ├── manifest.json   # Hand-picked image overrides per section
│       └── templates.py    # Tier 3: pillar-colored inline SVGs
├── schemas.py          # Pydantic models for content contracts
├── registry.json       # content metadata catalog (59 entries)
├── build.py            # main build pipeline: Jinja2 → static HTML (233 pages)
├── templates/          # Jinja2 templates (11 files)
├── static/             # CSS, JS, fonts (self-hosted)
├── content/            # source markdown for static pages
├── tests/              # smoke tests for build output
├── services/api/       # optional stateful service boundary
├── .github/workflows/  # CI/CD for API deployment
├── wrangler.toml       # Cloudflare Pages config
└── dist/               # generated output (233 pages, gitignored)
```

## Visual Management System (3-Tier Pattern)

The image pipeline uses a **deterministic fallback chain** — a pattern that recurs across the codebase:

| Tier | Layer | Mechanism | Guarantee |
|------|-------|-----------|-----------|
| 1 | Editorial manifest (`manifest.json`) | Hand-picked Unsplash/Commons URLs per section | Editorial control, no auto-fetch |
| 2 | Auto-fetch backends (Openverse, NASA, Wikimedia, LoC) | Keyword-scored parallel queries | Best-effort algorithmic match |
| 3 | Inline SVG fallback (`templates.py`) | Pillar-colored SVG with section-type icon | 100% coverage, network-independent |

**Properties:**
- **Policy over algorithm** — Tier 1 wins when it exists, Tier 2 fills gaps, Tier 3 guarantees no empty spaces.
- **Zero-gap invariant** — Every `<h2>` section always has a `<figure>` or `<svg>`; never an empty container.
- **No network dependency for fallback** — Tier 3 produces inline SVGs with zero fetch, zero storage, zero bandwidth.
- **Human-debuggable** — Failed auto-fetch is visible in the ETL report; manifest additions are a JSON edit away.

This is the same architectural philosophy applied in quality scoring (SQI override → deterministic formula → default minimum) and classification (manual reassignment → keyword/regex → `Uncategorized`). The invariant is: **explicit over implicit, deterministic over clever, always a visible fallback.**

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
