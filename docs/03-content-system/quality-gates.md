# Quality Gates (SQI)

The Signal Quality Index (SQI) is AcaciaFund's deterministic content-quality
metric. It scores every item from 0.0 to 1.0 as a weighted sum of rule-based
signals; it is not a Bayesian posterior.

## SQI Components

| Component | Weight | Description |
|-----------|--------|-------------|
| `source_credibility` | 0.25 | Source count and source-type authority |
| `technical_accuracy` | 0.25 | Depth, code, and reference markers; long-form bonus |
| `practical_value` | 0.20 | Practical/tool markers and learn-module bonus |
| `freshness` | 0.15 | Publication age with a foundational-content floor |
| `trend_relevance` | 0.10 | Ingested trend-strength signal |
| `educational_quality` | 0.05 | Bloom questions, flashcards, learn content |

### Computation

SQI is computed in `core/build_quality.py:_compute_sqi_for_item()`; the
canonical formula and invariants live in `docs/SQI_meaning_spec.md`. The
archived `scripts/archive/backfill_sqi.py` defines the formula that produced
most stored `sqi` values, and `scripts/backfill_registry_sqi.py` persists it for
new or missing items.

## Thresholds

| Threshold | Meaning | Badge Color |
|-----------|---------|-------------|
| ≥ 0.65 | Quality gate pass | — |
| ≥ 0.60 | Good quality | Green |
| ≥ 0.35 | Acceptable | Amber |
| < 0.35 | Below threshold | Red |

**Default SQI** (when signals are missing): `0.5`

## Quality Gate

The build enforces a quality gate at `SQI_THRESHOLD_MIN = 0.65`:

- Items below 0.65 are flagged in `build-meta.json` under `low_sqi_items`
- The build records `quality.gate_passed`; `scripts/enforce_quality_gate.py` turns it into a hard CI gate
- Admin quality page displays the distribution and failing items

## CI Quality Gates (deploy pipeline)

Every deploy runs four gates after the build; any failure blocks the deploy:

| Gate | Command | Fails when |
|------|---------|------------|
| Content structure audit | `scripts/audit_content_structure.py --report dist/content-structure-report.json` | Errors (min-h2=3 for research, empty sections, markdown residue, control chars) — warnings are non-blocking |
| SQI gate | `scripts/enforce_quality_gate.py --build-meta dist/build-meta.json` | `low_sqi_count` exceeds `--fail-on-low-sqi` (default 0) |
| Internal links | `scripts/check_links_and_sqi.py --dist-dir dist` | Any broken internal link (exit 1); also reports low-SQI pages |
| External reference liveness | `scripts/check_external_links.py --dist-dir dist` | Definitive 4xx URLs (5xx = warning; quarantined hosts in `data/known_blocking_hosts.json` are skipped) |
| Topic currency triage | `scripts/check_entry_freshness.py topics --fail-on-cold 0` | Cold topics (≥1 outdated or ≥2 stale time-sensitive items) |
| Full test suite | `python -m pytest tests/ -q` | Any test failure (Python tests) |

## Pluralistic Validation (advisory)

`core/validation.py` and `scripts/backfill_validation.py` maintain a five-track
rubric (`empirical_fidelity`, `coherence`, `philosophical_consistency`,
`schema_validity`, `test_suite_validity`) and persist `validation_composite` /
`validation_decision` on every registry item. It is intentionally **advisory**:
the build and CI do not gate on the decision because a large share of the
catalog still lacks the evidence signals the rubric requires.

Snapshot after the 2026-10-31 backfill (260 items): **168 accept / 23 review /
69 reject**, average composite 0.650. Rejected items are concentrated in
unverified research digests and glossary/explainer pages; enforcing the rubric
would require either content remediation or threshold calibration first.

## Entry Freshness & Currency Tiers

`scripts/check_entry_freshness.py` classifies every registry item into a currency tier:

- **time_sensitive** — explicit `currency_tier` field, or research items in `earnings-analysis` / `industry-analysis` / `market-analysis`. Decays fresh → stale (30 days) → outdated (90 days).
- **timeless** (evergreen) — everything else. Never decays past `fresh`; missing dates are `never`.

Pages render a freshness badge (Evergreen / Fresh / Stale / Outdated / Unverified) in the article metadata. Topic currency reports (`dist/topic-currency.json`) mark topics cold/cooling/current, with `--fail-on-cold N` gating CI.

## Provenance Badges

Every article shows a provenance badge in its metadata, classifying how the content was produced:

- **Verified** — carries `last_reviewed` / `last_verified` (human review anchor present)
- **Synthesized** — built automatically from source feeds (non-empty `source_breakdown`; arXiv, HN, PubMed, GDELT, SSRN, NBER, SEC EDGAR, Semantic Scholar)
- **Curated** — hand-authored editorial content (learn/knowledge templates, platform pages)

Derivation lives in `core/content.py:provenance_of()` and is injected at build time; the badge is `templates/partials/provenance_badge.j2`.

## Editor's Notes

`data/editor_notes.json` holds human-written annotations keyed by slug (or topic segment). The build merges them via `core/editor_notes.py:attach_editor_notes()` and renders `templates/partials/editor_note.j2` as a callout on research pages — the human voice on synthesized articles. The file is hashed into the build cache so note edits invalidate the affected pages.

## Citation Export

Research pages with a DOI or source URL render `templates/partials/citation_export.j2`: a DOI deep link (`https://doi.org/…`) plus BibTeX and RIS copy buttons. DOIs are captured at ingestion (`core/fetch.py` extracts them from arXiv / PubMed / Semantic Scholar; arXiv items without one get the deterministic `10.48550/arXiv.<id>`) and backfilled for existing items via `scripts/backfill_dois.py`.

## Backfill Script

`scripts/backfill_registry_sqi.py` recomputes and persists SQI for items that are missing it (the original `scripts/archive/backfill_sqi.py` defines the canonical formula):

```bash
python3 scripts/backfill_registry_sqi.py
```

- Scans all registry items
- Computes SQI from `signals` data where available
- Writes `sqi` field back to each item
- Preserves existing SQI values if signals are unchanged

## Interest Score

A combined score for content ranking:

```python
interest_score = SQI_WEIGHT(0.6) × sqi + RECENCY_WEIGHT(0.4) × recency
```

Where recency decays over `INTEREST_RECENCY_DAYS = 180`:
```python
recency = max(0, 1 - days_since_published / 180)
```

## Config Constants

| Constant | Default | Description |
|----------|---------|-------------|
| `SQI_THRESHOLD_MIN` | 0.65 | Minimum SQI for quality gate |
| `SQI_BADGE_HIGH` | 0.60 | Above this → green badge |
| `SQI_BADGE_MED` | 0.35 | Above this → amber badge |
| `SQI_DEFAULT` | 0.50 | Fallback when signal missing |
| `INTEREST_SQI_WEIGHT` | 0.60 | SQI weight in interest score |
| `INTEREST_RECENCY_WEIGHT` | 0.40 | Recency weight in interest score |
| `INTEREST_RECENCY_DAYS` | 180 | Recency half-life |

> **See also:** [Admin Quality Page](../06-admin-observability/quality-admin.md), [Backfill Script](../reference/cli-commands.md)
