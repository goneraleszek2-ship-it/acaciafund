# Quality Gates (SQI)

The Semantic Quality Index (SQI) is AcaciaFund's content quality metric. It scores every item from 0.0 to 1.0 based on content quality, readability, topical relevance, recency, and ontology concept coverage.

## SQI Components

| Component | Weight | Description |
|-----------|--------|-------------|
| `content_score` | 0.25 | Structure, length, heading hierarchy |
| `readability_score` | 0.25 | Flesch reading ease, sentence complexity |
| `topical_score` | 0.20 | Tag coherence, category match |
| `recency_score` | 0.15 | Publication freshness (decays over days) |
| `concept_overlap` | 0.15 | Ontology concept coverage in body text |

### Computation

SQI is computed in `build.py:_compute_sqi_for_item()`:

```python
def _compute_sqi_for_item(item):
    # 1. Readability: Flesch reading ease from body text
    # 2. Topical: Tag overlap with body content keywords
    # 3. Recency: Exponential decay based on days since publication
    # 4. Concept: Extract ontology concepts from body, score by count
    # 5. Aggregate: Weighted average → linear scale 0.0-1.0
```

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
| External reference liveness | `scripts/check_external_links.py --dist-dir dist` | Definitive 4xx URLs (5xx = warning; quarantined hosts in `data/known_blocking_hosts.json` are skipped) |
| Topic currency triage | `scripts/check_entry_freshness.py topics --fail-on-cold 0` | Cold topics (≥1 outdated or ≥2 stale time-sensitive items) |
| Full test suite | `python -m pytest tests/ -q` | Any test failure (1132 Python tests) |

## Entry Freshness & Currency Tiers

`scripts/check_entry_freshness.py` classifies every registry item into a currency tier:

- **time_sensitive** — explicit `currency_tier` field, or research items in `earnings-analysis` / `industry-analysis` / `market-analysis`. Decays fresh → stale (30 days) → outdated (90 days).
- **timeless** (evergreen) — everything else. Never decays past `fresh`; missing dates are `never`.

Pages render a freshness badge (Evergreen / Fresh / Stale / Outdated / Unverified) in the article metadata. Topic currency reports (`dist/topic-currency.json`) mark topics cold/cooling/current, with `--fail-on-cold N` gating CI.

## Backfill Script

`scripts/backfill_sqi.py` recomputes SQI for items that are missing it:

```bash
python3 scripts/backfill_sqi.py
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
