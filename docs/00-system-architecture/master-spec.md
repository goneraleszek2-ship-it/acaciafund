# AcaciaFund Master Specification

> **Version:** 1.1 (reconciled with live repo state on 2026-08-06)
> **Original brief:** Research Agent Specification v1.0 (2026-08-06)
> **Output target:** `https://www.acaciafund.org/` (static site, Cloudflare Pages)
> **Canonical repo facts:** see `../../AGENTS.md` (current state) and `../../SYSTEM_ARCHITECTURE.md`

This document is the single source of truth for task decomposition, implementation
decisions, and acceptance criteria. All metrics below were verified against the
repository on 2026-08-06; where the original brief was stale, the corrected value
is used and the tier checklist records actual status (done / partial / pending).

---

## 1. Project Goal & Mission

AcaciaFund is a static-first, cognitive learning platform that synthesizes research
from 32+ authoritative sources (arXiv, Hacker News, PubMed, SEC, FATF, Databricks,
and more) into three pillar domains: Compliance (AML/financial crime), Markets
(quantitative finance), and Data Engineering.

It is a schema-building engine grounded in cognitive psychology. Every article is
classified by Bloom's taxonomy, mapped into an ontology of cross-pillar concepts,
connected through prerequisite learning paths, and supported by SM-2 spaced
repetition for durable retention.

Core value proposition: "Invest in understanding, to build resilience." Three
pillars of modern finance — explained from first principles, in plain language,
with ideas you can hold on to.

## 2. System Architecture

### 2.1 Build Pipeline

Static site generator (`build.py`, 3,924 lines). No runtime backend.

```
Ingestion (32 sources) → registry.json → NLP Enrichment → Pydantic Validation → Jinja2 Templates → dist/ → Cloudflare Pages
```

Key files:
- `build.py` — static site generator
- `config.py` — single source of truth (pillars, URLs, quality thresholds)
- `registry.json` — content catalog
- `core/` — business logic: ontology engine, schema builder, retention engine
- `templates/` — Jinja2 templates (layout, content types, admin, partials)
- `static/` — CSS design system, JS modules, fonts, images
- `data/` — runtime JSON stores (ontology, graph, freshness, metadata)
- `content/` — source markdown (per-pillar)

### 2.2 Content Types (verified 2026-08-06)

| Type | Count | Purpose |
|---|---|---|
| Research | 102 | Synthesized academic papers, SEC filings, news, arXiv preprints |
| Learn | 83 | Interactive lessons, tutorials, quizzes (Bloom-classified) |
| Knowledge | 41 | Meta-content: glossaries, methodology, architecture docs |

Registry total: **226 items** (57 aml / 73 stock / 96 data-engineering).

### 2.3 Ontology & Taxonomy (verified)

- **199 concepts**, **447 relations** across 10 relation types
- Prerequisite learning paths (directed graph)
- Cross-pillar bridges (e.g., Data Pipeline → enables → AML Surveillance)
- All concepts carry philosophical metadata (epistemic status, lineage, etc.)

### 2.4 Quality System: SQI (Signal Quality Index)

Composite score weighting authority 35%, freshness 25%, consensus 25%, relevance
15%. Gate threshold **0.65** (`--fail-on-low-sqi 0`); the build backfills scores
and the deploy pipeline enforces the gate (all 2,827 pages ≥ 0.65).

### 2.5 Pedagogical Stack

1. **Bloom's Taxonomy** — Beginner (Remember/Understand), Intermediate
   (Apply/Analyze), Advanced (Evaluate/Create)
2. **Feynman Technique** — ELI5 → Analogy → Examples → Self-test → Build
3. **SM-2 Spaced Repetition** — client-side (`static/js/learning_hub.js`
   `SM2Scheduler` for flashcards, `static/js/retention_engine.js` for concepts),
   mirrored server-side in `core/retention_engine.py`

### 2.6 Atomic Design Architecture

| Stage | Location | Rule |
|---|---|---|
| Atom | `static/css/design-system.css` | Base tokens only (color, type, spacing) |
| Molecule | `templates/partials/` | Context-agnostic reusable components |
| Organism | `templates/` (page sections) | Compose molecules (header, study queue) |
| Template | `templates/layout.j2` etc. | Page skeletons |
| Page | `dist/` | Generated instances (2,827) |

Invariant: never hardcode page-specific logic in molecules; name by structure,
not context.

## 3. Current State Assessment (verified 2026-08-06)

### 3.1 Metrics

| Metric | Value |
|---|---|
| Generated pages | 2,827 |
| Registry items | 226 (102 research / 83 learn / 41 knowledge) |
| Ontology concepts / relations | 199 / 447 |
| Tests | 1,273 total (1,173 Python / 52 modules + 106 JS / 4 suites) |
| Build time | ~98–131 s full, incremental via content hashing |
| Deploy target | Cloudflare Pages via GitHub Actions |

### 3.2 Strengths

- Interdisciplinary coherence: Compliance–Markets–Data triangle is integrated
- Pedagogical rigor: Bloom + Feynman + SM-2 baked into the content schema
- Static-site performance: fast loads, edge deployment
- Transparent methodology: SQI weights, source feeds, CI gates documented
- Atomic design alignment: template system scales without proportional cost

### 3.3 Issue Status (original brief vs. reality)

| # | Brief claim | Status 2026-08-06 |
|---|---|---|
| 1 | `/data-engineering/` fails to load | **Fixed.** Real URL is `/data/` (`PILLAR_URL_MAP`); `/data-engineering/*` redirects to `/data/*` (301); all 3 pillars return 200 |
| 2 | No build-time link validation | **Fixed.** `scripts/check_links_and_sqi.py` + internal-link CI gate (zero 404s required) |
| 3 | SM-2 engine invisible | **Partial.** `/review/` dashboard + `/review/queue/` exist; queue page has a broken flashcard component dependency (fixed in Tier 2.1); no global Study Queue entry point |
| 4 | Knowledge graph invisible | **Fixed/partial.** `/graph/` (Cytoscape), 199 `/concepts/{id}/` pages, per-concept concept-map partial exist; no per-page D3 prerequisite graph |
| 5 | No progress tracking | **Fixed.** Learning-path progress bars (localStorage) + concept mastery dashboard |
| 6 | Limited interactivity | **Done.** SQLite-wasm SQL exercises, Pyodide/Polars sandbox, KYC + SAR compliance simulators (Tier 4) |
| 7 | Citation depth lacking | **Fixed/partial.** DOI links + BibTeX/RIS export + copy buttons shipped; OpenAlex "Cited by" pending |
| 8 | Content provenance ambiguity | **Fixed.** Provenance badges (Verified / Synthesized / Curated) on all articles |

## 4. Target State Vision

AcaciaFund evolves from a content library into a learning ecosystem like:
- **Elicit** (research synthesis with provenance)
- **Duolingo** (guided linear paths with spaced repetition)
- **DataCamp** (hands-on browser-based exercises)
- **Khan Academy** (visual knowledge map with prerequisite unlocking)

User journey: homepage → pillar or diagnostic quiz → Bloom-level placement on a
guided track → thematic units (ELI5 → analogy → examples → exercise) → SM-2
review in a visible Study Queue → knowledge-graph exploration → portfolio
artifact + credential.

## 5. Task Execution Plan & Status

Execute in priority order; do not proceed to Tier N+1 until Tier N is stable.

### Tier 1: Reliability & Trust — DONE

| Task | Status | Notes |
|---|---|---|
| 1.1 Fix `/data-engineering/` landing | **Done** | Real URL `/data/`; redirects; build asserts pillar index; all pillars 200 |
| 1.2 Build-time link/route checking | **Done** | `check_links_and_sqi.py`, CI gate, 7 tests |
| 1.3 Content provenance badging | **Done** | `provenance` field + `provenance_badge.j2`; every article badged |

### Tier 2: Pedagogical UX — DONE

| Task | Status | Notes |
|---|---|---|
| 2.1 Surface SM-2 Study Queue | **Done** | Header bell w/ due count, `/study/` merged queue (flashcards + concepts), fix broken flashcard dependency on queue pages; reuse existing `SM2Scheduler`/`RetentionEngine` |
| 2.2 Auto-generate flashcards | **Done** | Build-time backfill: learn items with quizzes but <3 flashcards get cards from `bloom_questions`; 5 hand-authored modules got a 3rd authored card — all 83 learn items yield ≥3 SM-2 cards |
| 2.3 Progress tracking | **Done** | Learning-path progress bars + concept mastery dashboard (localStorage) |
| 2.4 Diagnostic placement quiz | **Done** | `/diagnostic/` page, 9 per-pillar questions (1 B / 1 I / 1 E per pillar), local scoring → placement writes `acacia_learning_mode` + `acacia_diagnostic_done` |

### Tier 3: Knowledge Graph Visualization — PARTIAL

| Task | Status | Notes |
|---|---|---|
| 3.1 Concept Hub pages | **Done** | 199 pages at `/concepts/{id}/` with related articles, prerequisites, Bloom distribution |
| 3.2 Prerequisite path visualization | **Partial** | Cytoscape `/graph/` + per-page concept map exist; lightweight per-concept D3 graph pending |
| 3.3 Cross-pillar journey paths | **Done** | 15 learning-path pages + 3 pillar-synthesis pages + `/journeys/` hub with 3 curated linear journeys (6 steps each, all 3 pillars) with localStorage progress + next-step nav |

### Tier 4: Hands-On Interactivity — DONE

| Task | Notes |
|---|---|
| 4.1 SQLite-wasm SQL exercises | **Done** | 3 beginner AML lessons ship an in-browser SQLite sandbox (sql.js via CDN): CTR flagging (aml-basics), structuring detection (money-laundering-mechanisms), sanctions name screening (sanctions-screening-global-regimes). Shared `acacia_aml` dataset, answer checking + hints, zero data egress |
| 4.2 Pyodide Python/Polars exercises | **Done** | Polars transaction-flow pipeline tutorial on sql-for-data-engineers (Pyodide + Polars via CDN, reference-output comparison) |
| 4.3 Compliance simulation exercises | **Done** | KYC onboarding workflow simulator (kyc-cdd-workflows, 3-step decision flow with EDD rationale) + SAR filing form simulator (sar-filing-scenarios, red-flag checklist + narrative validation, HTML/CSS/JS only) |
| 4.4 Exercise platform plumbing | **Done** | `data/exercises.json` + `core/exercises.py` slug-matched attachment; sandbox partials + CSS; build-cache hash now covers sandbox exercises and missing outputs force rebuild |

### Tier 5: Research Rigor & Reference — PARTIAL

| Task | Status | Notes |
|---|---|---|
| 5.1 Citation enrichment | **Partial** | DOI + BibTeX/RIS shipped (incl. arXiv vN stripping + doi.org validation); OpenAlex "Cited by" pending |
| 5.2 Structured extraction tables | **Pending** | Key-variable tables + PRISMA-style audit trail for systematic reviews |
| 5.3 Expert curation layer | **Done** | `data/editor_notes.json` + `editor_note.j2` (4 notes shipped) |

### Tier 6: Community & Ecosystem — PARTIAL

| Task | Status | Notes |
|---|---|---|
| 6.1 "Edit on GitHub" links | **Pending** | Link molecule per article |
| 6.2 Public design-system docs | **Pending** | `/design-system/` with live component examples |
| 6.3 Structured data (Schema.org) | **Done** | JSON-LD injected via `layout.j2` (LearningResource / ScholarlyArticle / FAQPage) |

## 6. Atomic Design Task Mapping

Follow the stage hierarchy in §2.6 for every UI change. Molecules must be
context-agnostic; name patterns by structure (`card`, not `product-card`).

> **Design reference:** the canonical UI/UX specification (v1.0 with adaptation
> notes) is `docs/00-system-architecture/ui-ux-spec.md`. Check it before any
> template/CSS change; new components must trace to an atom/molecule/organism there.

## 7. Testing & Quality Gates (per change)

1. Full test suite: `bash scripts/run_tests.sh` — **1,173 Python + 106 JS must pass**
2. Build: `python3 build.py` completes without errors (`dist/build_errors.log` empty)
3. Link check: zero internal 404s (`scripts/check_links_and_sqi.py --dist-dir dist`)
4. Pydantic validation: `registry.json` passes schema
5. Lint: `ruff check .` clean; type check via CI (pyright, non-blocking)

CI pipeline (deploy job, in order): install → cache restore → ingestion → enrich →
build → post-build smoke tests → full pytest → structure audit → quality gate →
internal links + SQI → external reference liveness → topic currency triage → deploy.

## 8. Reference Context

- Elicit (elicit.com), Perplexity, Duolingo, Khan Academy, DataCamp, Coursera
- Atomic Design by Brad Frost

## 9. Success Metrics

| Metric | Current (2026-08-06) | Target (6 months) |
|---|---|---|
| Pillar landing page uptime | 100% (3/3) | 100% |
| Internal 404s | 0 | 0 |
| SM-2 active users | 0 (hidden) | 30% of returning visitors |
| Concept hub pages | 199 (100%) | 199 (100%) |
| Interactive exercises | 0 | 15 (5 SQL + 5 Python + 5 Compliance sim) |
| Avg. session duration | Baseline | +40% |
| Return visitor rate | Baseline | +25% |
| Study Queue entry point | 0 | 1 visible, with due-count badge |
| Diagnostic quiz | 0 | 3 (one per pillar) |
