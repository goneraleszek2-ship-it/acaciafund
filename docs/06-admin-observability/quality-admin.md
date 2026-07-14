# Quality Admin

The quality and coverage admin pages provide SQI monitoring and content distribution analysis.

## Quality Page (`admin/quality.html`)

Displays:

### SQI Distribution

- Histogram of SQI scores across items
- Buckets: 0.0–0.35, 0.35–0.5, 0.5–0.65, 0.65–0.8, 0.8–1.0
- Count and percentage per bucket
- Average SQI displayed at top

### Threshold Failures

- Items with SQI below `SQI_THRESHOLD_MIN` (0.65)
- Shown as a table with: slug, title, current SQI, gap to threshold
- Highlighted in red

### Per-Pillar Breakdown

- Average SQI per pillar (Compliance, Markets, Data Engineering)
- Item count per pillar
- Threshold failure count per pillar

### Quality Trends

- SQI changes between builds (if build history is available)
- Items that improved or regressed

## Coverage Page (`admin/coverage.html`)

Displays:

### Content Distribution

- Items by pillar (Compliance / Markets / Data)
- Items by content_type (Research / Learn / Knowledge)
- Items by difficulty (Beginner / Intermediate / Advanced)

### Category Coverage

- For each pillar: subcategories with item counts
- Empty categories highlighted (warnings)
- Percentage coverage per pillar

### Historical Comparison

- Total page count trend
- SQI average trend

## Data Source

Quality data comes from the registry items' SQI fields and `dist/build-meta.json`:

```json
{
  "sqi_avg": 0.823,
  "sqi_below_threshold": [
    {"slug": "aml/knowledge/glossary", "sqi": 0.45, "gap": 0.2}
  ]
}
```

> **See also:** [Admin Dashboard](admin-dashboard.md), [Quality Gates (SQI)](../03-content-system/quality-gates.md)
