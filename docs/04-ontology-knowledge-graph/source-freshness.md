# Source Freshness

32 inspiration sources (configured in `etc/pillars.toml`) are periodically checked for availability. Freshness data powers the admin sources page and the "Further Reading" section on knowledge items.

## Source Configuration

Defined in `etc/pillars.toml` under `[inspiration_sources]`:

```toml
[inspiration_sources]
sources = [
    { url = "https://www.fatf-gafi.org", name = "FATF", pillar = "aml", frequency = "weekly", relevance = 1.0 },
    { url = "https://www.acamstoday.org", name = "ACAMS", pillar = "aml", frequency = "weekly", relevance = 0.9 },
    # ... 30 more sources
]
```

### Source Distribution

| Pillar | Sources |
|--------|---------|
| Compliance | FATF, ACAMS, FinCEN, OFAC, ECB, FCA, Egmont Group, FINTRAC, Payments.org, Chainalysis |
| Data Engineering | Databricks, Kafka, Flink, Iceberg, dbt, Dagster, Confluent, AWS, GCP, Meltano, Snowflake |
| Markets | SEC, BIS, IMF, MSCI, Bloomberg, S&P Global, Man Group, AQR, Reuters, FT, Quantocracy |

## Freshness Check

`scripts/check_source_freshness.py` performs HTTP HEAD requests:

```bash
# Check all sources (writes to dist/ + data/)
python3 scripts/check_source_freshness.py

# Check and update ontology with freshness data
python3 scripts/check_source_freshness.py --update-ontology
```

### Status Categories

| HTTP Status | Status | Meaning |
|-------------|--------|---------|
| 2xx-3xx | `active` | Source is accessible |
| 4xx | `degraded` | Source returning client errors |
| 5xx / timeout | `error` | Source is down or unreachable |

## Output Files

| File | Description |
|------|-------------|
| `data/source_health.json` | Persistent freshness cache (committed to repo) |
| `dist/source_health.json` | Freshness data for admin page consumption |

Both contain:

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

## Admin Integration

The admin sources page (`admin/sources.html`) displays:
- Overall freshness badge (all active / some degraded / some error)
- Per-source status with last-verified timestamp
- Pillar-based grouping
- HTTP status codes

## Weekly Workflow

Freshness is checked automatically every Monday at 04:00 UTC via `.github/workflows/source-refresh.yml`:

```
Monday 04:00 UTC
  → Check 32 sources (HEAD requests)
  → Write data/source_health.json
  → Build site
  → Deploy to Cloudflare
```

> **See also:** [Admin Intelligence Pages](../06-admin-observability/intelligence-admin.md), [Weekly Refresh](../07-deployment-ops/weekly-refresh.md)
