# Monitoring

Build metrics, source health, and error logging provide operational visibility.

## Build Artifacts

### `dist/build-meta.json`

Generated after each build:

```json
{
  "build_time_s": 26.9,
  "pages_total": 810,
  "registry_items": 280,
  "skipped_items": 0,
  "sqi_avg": 0.823,
  "sqi_below_threshold": [],
  "generated_at": "2026-07-13T12:00:00+00:00",
  "url_structure_version": "3.0"
}
```

### `dist/build_errors.log`

- **Empty file (0 bytes):** Clean build
- **Non-empty:** Error messages from build process

### `dist/source_health.json`

Freshness status for all 32 inspiration sources:

```json
{
  "generated_at": "2026-07-13T04:00:00+00:00",
  "sources": [
    {
      "url": "https://www.fatf-gafi.org",
      "name": "FATF",
      "pillar": "aml",
      "status": "active",
      "http_status": 200,
      "last_verified": "2026-07-13T04:00:00+00:00"
    }
  ]
}
```

## Data Persistence Files

| File | Description | Update Frequency |
|------|-------------|-----------------|
| `registry.json` | Content registry (~280 items) | On content change |
| `.build_cache.json` | Incremental build cache | Every build |
| `data/ontology.json` | Persisted ontology (48 concepts) | Weekly + manual |
| `data/source_health.json` | Source freshness data | Weekly |

## Health Indicators

| Indicator | Source | Warning | Critical |
|-----------|--------|---------|----------|
| Build errors | `build_errors.log` | Non-empty | Large file |
| SQI average | `build-meta.json` | < 0.75 | < 0.65 |
| SQI failures | `build-meta.json.sqi_below_threshold` | 1-3 items | 5+ items |
| Source freshness | `source_health.json` | 1+ degraded | 1+ error |
| Page count | `build-meta.json.pages_total` | Drop > 10% | Drop > 25% |

## SQI Audit

Run SQI audit to check content quality:

```bash
python3 scripts/check_links_and_sqi.py --dist-dir dist
```

Output includes:
- SQI distribution histogram
- Items below threshold
- Per-pillar SQI averages

## Link Checking

The same script checks for broken links in the built site:

```bash
python3 scripts/check_links_and_sqi.py --dist-dir dist
```

Checks:
- Internal links (within `dist/`)
- External resource links
- Image source URLs
- Redirect targets

> **See also:** [Quality Gates](../03-content-system/quality-gates.md), [Source Freshness](../04-ontology-knowledge-graph/source-freshness.md)
