# AcaciaFund — Repository & Guardrails Telemetry Report

> **Audit method:** read-only inspection (no application logic modified).
> **Date:** 2026-08-29 · **GIT HEAD:** `49981d83` (main)
>
> **Resolution update (2026-10-31):** repo-wide `ruff check` passes; 1,321
> Python tests + 15 JS suites pass; docs metrics reconciled (260 items /
> 2,929 pages / 199 concepts / 447 relations). The cold `earnings-analysis`
> topic was refreshed with a current S-1 item and the dated digest was marked
> timeless. Remaining known issues: 69 advisory pluralistic-validation rejects
> and local branch divergence from `origin/main`.

---

## 1. Core Tech Stack & Runtime

| Layer | Technology | Notes |
|---|---|---|
| **Language (build)** | Python ≥3.10, **runtime 3.14.4** (system Python) | GitHub CI uses `3.14`; pyproject targets `py3.10` |
| **Language (client)** | Vanilla ES (ES2022 target, `jsconfig.json`) | No framework; no npm build step for production JS |
| **Static site generator** | Custom monolith **`build.py` (4,014 lines)** | Renders all 2,929 pages from `registry.json` + Jinja2 |
| **Templating** | Jinja2 (`*.j2`, `*.html` under `templates/`) | `layout.j2` base + `admin/base.html` admin layout |
| **Data validation** | Pydantic v2 (`schemas.py`, `core/ontology.py`) | `RegistryData`, `Concept`, `Relation` models |
| **Ontology graph** | NetworkX (transient) → `data/ontology.json` | 199 concepts, **447** relations, Cytoscape export |
| **Pillar-specific libs** | pandas, pyarrow, polars, yfinance, dedupe, spaCy, scikit-learn, sentence-transformers, torch | Heavy ML/data stack in `requirements-build.txt` |
| **Pinned lockfile** | `requirements.lock` (pip freeze, 83 pkgs) | One source: `requirements.txt` → `-r requirements-build.txt` |
| **Node toolchain** | Node **v22.22.1** | JS tests only (`node tests/test_*.js`); no package.json |

**Config files:** `pyproject.toml` (project/deps/ruff/pyright/pytest), `pyrightconfig.json` (overrides pyproject pyright section — see §5), `jsconfig.json`, `jsconfig` (TypeScript-style checkJs hints), `requirements*.txt`, `etc/pillars.toml`, `etc/sources.toml`.

> **Note:** No `package.json`, `Makefile`, `wrangler.toml`, or `Dockerfile` exist. Cloudflare Pages deployment is driven purely from GitHub Actions.

---

## 2. Build & Deployment Architecture

```
GraphQL/…  (external)
      │
registry.json (260 items)  ← scripts/knowledge_ingester.py (arXiv/HN/PubMed)
      │                      scripts/fetch_news.py (23 RSS + HN + GDELT)
      │                      scripts/enrich.py
      ▼
   build.py  ──▶  dist/   (2,929 HTML pages)
      │            │
      ├─ core/build_taxonomies.py   (admin, search, tags, pilllar, feed)
      ├─ core/build_cache.py        (incremental cache + parallel_map)
      ├─ core/build_content.py      (article/learn/knowledge pages)
      ├─ core/build_images.py       (SVG thumbnails/og images)
      ├─ core/build_quality.py      (SQI backfill at build time)
      └─ core/ontology.py           (concept extraction, cytograph)
```

**Deployment:** GitHub Actions → **Cloudflare Pages** (`dist/`, project `acaciafund`) → `https://www.acaciafund.org/`
- `cloudflare/wrangler-action@v4` with `CLOUDFLARE_API_TOKEN` / `CLOUDFLARE_ACCOUNT_ID` secrets.
- `ADMIN_USERNAME` / `ADMIN_PASSWORD` injected as env into the build step.

| Workflow | Trigger | Result |
|---|---|---|
| `deploy.yml` | push/main, manual, **daily 06:00 UTC** (news ingestion) | quality (ruff+pyright) → deploy (ingest→enrich→news→smoke→build→smoke→full pytest→4 CI gates→deploy) |
| `source-refresh.yml` | **weekly Mon 04:00 UTC** | ontology regen, philosophy enrichment, glossaries, freshness, weekly notes, rebuild, commit+push |
| `ontology-validation.yml` | push/main, manual | **⚠ BROKEN — malformed YAML (see §5), never executes** |

Quality gates inside `deploy.yml`: pytest full suite, `audit_content_structure.py`, `enforce_quality_gate.py` (SQI), `check_links_and_sqi.py`, `check_external_links.py` (liveness), `check_entry_freshness.py topics --fail-on-cold 0`.

**Runtime:** 97–155 s full build (measured 134 s, 2,929 pages, `dist/build_errors.log` = 0 bytes).

---

## 3. Verification Commands (Tests, Linters, Build)

### (a) Unit / Integration tests
```bash
# Full suite — the canonical runner (isolated groups to avoid 3.14 pipe-buffering hangs)
bash scripts/run_tests.sh                 # ~44 Python groups + 15 JS suites
bash scripts/run_tests.sh tests/test_ontology.py -v

# Direct pytest (always redirect stdout/stderr to a file)
python3 -m pytest tests/ -v > /tmp/test_results.log 2>&1
timeout 300 python3 -u -m pytest tests/ | tee /tmp/test_results.log

# Pre-build registry/schema smoke  /  post-build output smoke
python3 -m pytest tests/test_smoke.py -v
python3 scripts/deploy_checks.py

# JS suites (node only, no npm)
for t in tests/test_*.js; do node "$t"; done
```
- 62 Python test modules + 15 JS test files (14 listed in `run_tests.sh` JS group + `test_nav.js` present on disk).
- Count in `AGENTS.md` ("1218 Python tests / 58 modules") is **stale** vs 62 files on disk.

### (b) Linters / type-checkers
```bash
ruff check .                              # E,F,W,I; line-length 100; excludes tests+scripts/archive (ruff 0.15.21)
pyright                                   # standard mode per pyrightconfig.json (~5 min, 68 baseline errors)
# CI gate: fails only if error count > 68 (grep -c "error:") or fatal-with-0-errors
```
- **mypy**: not configured. **ESLint** present at `/usr/bin/eslint` but **no config, no `eslint` invocation anywhere** (jsconfig `checkJs` hints only).

### (c) Local preview build
```bash
# Full rebuild (clears cache)
rm -rf dist .build_cache.json && python3 build.py
# Incremental (cache-respecting)
python3 build.py
# Serve output (static — no built-in server script found in scripts/)
python3 -m http.server 8000 --directory dist
```
- Incremental cache keyed by `URL_STRUCTURE_VERSION` in `config.py` (currently `"3.0"`).

---

## 4. Directory Topology & Key Entry Points

```
acaciafund/
├── build.py                  ← SSG entry point (4,014 lines)
├── config.py                 ← PILLAR_URL_MAP (single source of truth), subcategories (392 lines)
├── schemas.py                ← Pydantic RegistryData models (50 lines)
├── registry.json             ← content store: 260 items (research 136 / learn 83 / knowledge 41)
├── registry.db               ← optional SQLite cache (generated on demand; ignored)
├── core/                     ← 50 modules (build orchestration, ontology, retention, LLM client…)
│   ├── urls.py               ← pure URL helpers (no heavy deps — safe for tests)
│   ├── ontology.py           ← OntologyManager (199 concepts, 447 relations)
│   ├── build_taxonomies.py   ← admin/search/tag/pillar/feed generators
│   └── build_cache.py        ← incremental build cache
├── scripts/                  ← 64 active scripts (CI gates, ingestion, freshness, exports) +
│   ├── run_tests.sh          ← consolidated test runner
│   ├── fetch_news.py         ← daily news pipeline (keyless)
│   ├── knowledge_ingester.py ← multi-pillar ingestion (arXiv/HN/PubMed)
│   └── archive/              ← 70+ archived/legacy scripts (incl. deploy_cloudflare.py, mem0*
├── templates/                ← 43 Jinja2 pages + admin/ + macros/ + partials/
├── static/                   ← css/fonts/images (fetch_images.py imports CURATED_KNOWN)/js (25 files)
├── content/                  ← per-pillar source files (aml, data, data-engineering, docs, market)
├── data/                     ← ontology.json, news.json, source_health.json, freshness, cytograph, …
├── tests/                    ← 62 py + 15 js test files (+ fixtures/ + conftest.py)
├── docs/                     ← 10 numbered architecture/ops dirs + specs; index.md
├── etc/                      ← pillars.toml, sources.toml
├── schemas/                  ← validation schemas
├── .github/workflows/        ← 3 CI workflows
└── AGENTS.md                 ← 56 KB agent build guide (invariants, commands, docs)
```

**Data pipelines (entry points):**
- Ingestion: `scripts/knowledge_ingester.py`, `scripts/fetch_news.py`, `scripts/enrich.py`, `scripts/source_synthesis.py`, `scripts/source_verification.py`, `scripts/backfill_openalex.py`, `scripts/backfill_dois.py`
- Maintenance/CI gates: `audit_content_structure.py`, `enforce_quality_gate.py`, `check_links_and_sqi.py`, `check_external_links.py`, `check_entry_freshness.py`, `check_source_freshness.py`, `check_rss_feeds.py`, `remediate_content_structure.py`, `validate_cross_pillar.py`
- Generator scripts: `generate_glossaries.py`, `generate_learn_modules.py`, `generate_alpha_index.py`, `generate_weekly_notes.py`
- Ontology tooling: `bitmask_exporter.py`, `owl_reasoner.py`, `shacl_generator.py`, `z3_validator.py`, `enrich_philosophy.py`

**Agent instruction files:** `AGENTS.md` present (authoritative). **No** `CLAUDE.md`, `.cursorrules`, `.opencode/`, or `GEMINI.md`.
**Custom operational scripts:** extensive (above); no Jira/Slack/CRM integrations found. `.dlq/` (dead-letter queue) present.

---

## 5. Identified Gaps (Missing Guardrails, Type Checks, Test Coverage)

### Critical
1. **`ontology-validation.yml` is malformed YAML and never runs.**
   `python3 -c "` literal blocks at lines 41–58 drop the Python body to **column 0**, terminating the block scalar → `yaml.scanner.ScannerError`. GitHub refuses the workflow, so the "Ontology Validation & CI/CD Gates" (DAG acyclicity, deontic bitmask verification) provide **zero protection**. Also contains a stray `needs: quality` key inside a job.
2. **`deploy_cloudflare.py` is absent (archived).** AGENTS.md ("Deploy to Cloudflare: `python3 scripts/deploy_cloudflare.py`") references a script that only exists under `scripts/archive/`. Manual deploys / the documented path silently fail.

### High
3. **Pyright config duplication/divergence.** `pyproject.toml [tool.pyright]` (include=4 roots, `basic` mode) vs `pyrightconfig.json` (include `.`, `standard` mode, `reportMissingImports: none`). `pyrightconfig.json` wins, so the CI gate (baseline 68 errors) runs in *standard* mode against the whole repo, not the declared `basic`/scoped intent. Either reconcile or document.
4. **No hardening on the 68-error baseline.** CI blocks only *regressions above 68*; new type errors are allowable up to the ceiling. The baseline is unratified (no per-file allowlist, no `# pyright: ignore` sweep).
5. **Zero client-side type enforcement in CI.** `jsconfig.json` `checkJs` hints exist but no `tsc` run, no ESLint config, no lint invocation anywhere — all 15 JS suites are behavior tests only.

### Medium
6. **Coverage is gated nowhere.** `run_tests.sh` emits coverage as informational only; targets (core 80%, scripts 22%) are unenforced — CI runs `pytest -q` with no `--cov` / fail-under.
7. **Inconsistent test tooling.** CI uses `python -m pytest tests/ -q` directly; local canonical runner is `bash scripts/run_tests.sh` (stdlib `timeout`, per-group isolation). The two paths differ (isolation → timing/skip behavior), and `test_nav.js` is not in the runner's JS list.
8. **Stale telemetry in AGENTS.md — resolved 2026-10-31.** Docs now report **260 items / 2,929 pages / 447 relations / 1,321 Python tests + 15 JS suites**.
9. **Schema debt in registry — resolved 2026-10-31.** 0/260 items now lack `sqi`; `scripts/backfill_registry_sqi.py` persists the build-time fallback explicitly, and the 0.65 quality gate passes.

### Low
10. **Repository hygiene — resolved 2026-10-31.** Local virtualenvs, caches, dead-letter logs, and registry snapshot backups were removed; `registry.db`, `.coverage`, and registry backup patterns are now ignored.
11. **Single large entry file.** `build.py` (4,014 lines) is the sole SSG; split responsibilities documented in `core/*` but `build.py` remains the choke point for builds/test-imports.
12. **Performance headroom:** largest output `dist/research/workspace/index.html` = **2.2 MB** (prior-identified workspace page) — exceeds typical per-page budgets; graph data `dist/graph-data.json` = 1.1 MB.

### Not a gap
- Security: admin creds **fail-closed** (Phase 0 commit `49981d83`); no hard-coded fallback; login page renders no credentials (Cloudflare Access in front).
- Branch protection / deploy consistency: `deploy.yml` `quality` job gates `deploy` correctly (`needs: quality` validated).