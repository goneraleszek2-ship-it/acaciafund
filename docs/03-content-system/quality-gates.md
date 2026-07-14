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

- Items below 0.65 are flagged in `build-meta.json` under `sqi_below_threshold`
- The build does not fail — the gate is informational
- Admin quality page displays the distribution and failing items

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
