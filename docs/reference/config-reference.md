# Config Reference

All non-sensitive configuration constants from `config.py`.

## Site Identity

| Constant | Value | Description |
|----------|-------|-------------|
| `SITE_URL` | `"https://www.acaciafund.org"` | Production site URL |
| `SITE_NAME` | `"AcaciaFund"` | Site display name |
| `SITE_DESCRIPTION` | *Long string* | Meta description |
| `PLAUSIBLE_DOMAIN` | `"plausible.io"` | Plausible analytics server |

## Paths

| Constant | Value | Description |
|----------|-------|-------------|
| `PROJECT_ROOT` | Path to project root | Auto-detected from file location |
| `REGISTRY_PATH` | `{PROJECT_ROOT}/registry.json` | Content registry file |
| `TEMPLATE_DIR` | `{PROJECT_ROOT}/templates` | Jinja2 template directory |
| `PIPELINE_STATIC_DIR` | `{PROJECT_ROOT}/static` | Source static assets |
| `OUTPUT_DIR` | `{PROJECT_ROOT}/dist` | Build output directory |
| `STATIC_DST_DIR` | `{OUTPUT_DIR}/static` | Output static assets |

## Quality Thresholds

| Constant | Default | Description |
|----------|---------|-------------|
| `SQI_THRESHOLD_MIN` | `0.65` | Minimum SQI for quality gate |
| `SQI_BADGE_HIGH` | `0.60` | SQI above this → green badge |
| `SQI_BADGE_MED` | `0.35` | SQI above this → amber badge |
| `SQI_DEFAULT` | `0.50` | Fallback when signal missing |

## Interest Score Weights

| Constant | Default | Description |
|----------|---------|-------------|
| `INTEREST_SQI_WEIGHT` | `0.60` | SQI weight in interest score |
| `INTEREST_RECENCY_WEIGHT` | `0.40` | Recency weight |
| `INTEREST_RECENCY_DAYS` | `180` | Recency half-life in days |

## Pillar Mapping

| Constant | Type | Description |
|----------|------|-------------|
| `PILLAR_URL_MAP` | `dict[str, str]` | `{"aml": "compliance", "stock": "markets", "data-engineering": "data"}` |
| `PILLAR_URL_REVERSE` | `dict[str, str]` | Reverse mapping: `{"compliance": "aml", ...}` |
| `PILLAR_NAMES` | `dict[str, str]` | Display names |
| `PILLAR_EMOJIS` | `dict[str, str]` | Pillar emoji icons |

## Version

| Constant | Default | Description |
|----------|---------|-------------|
| `URL_STRUCTURE_VERSION` | `"3.0"` | Bump to force full cache rebuild |

## Pillar Subcategories

`PILLAR_SUBCATEGORIES: dict[str, dict[str, dict[str, str]]]`

3 pillars × 14 subcategories each. Each subcategory has `label`, `icon`, `description`.

**See:** [Pillar System](../01-architecture/pillars.md) for the full table.

## Knowledge-to-Pillar Mapping

`KNOWLEDGE_TO_PILLAR_CATEGORY: dict[str, dict[str, str]]`

11 knowledge categories mapped to pillar-specific subcategories.

**See:** [Knowledge Taxonomy](../03-content-system/knowledge-taxonomy.md) for the full mapping.
