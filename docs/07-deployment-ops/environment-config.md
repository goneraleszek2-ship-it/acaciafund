# Environment Configuration

Environment variables and configuration for local development and production.

## `.env` File

The `.env` file at the project root contains sensitive configuration:

```bash
ADMIN_USERNAME=admin
ADMIN_PASSWORD=secure-password-here
```

**Never commit `.env` to version control.** It's in `.gitignore`.

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ADMIN_USERNAME` | Yes | `admin` | Admin dashboard login |
| `ADMIN_PASSWORD` | Yes | `admin` | Admin dashboard password |
| `PLAUSIBLE_DOMAIN` | No | `plausible.io` | Plausible analytics server |

## Load Order

Credentials are loaded by `build.py:load_admin_credentials()`:

```
1. Environment variables (ADMIN_USERNAME, ADMIN_PASSWORD)
2. .env file
3. Default fallback (admin/admin) with warning
```

## Config Constants

All non-sensitive configuration lives in `config.py`:

| Category | Constant | Type | Description |
|----------|----------|------|-------------|
| Site | `SITE_URL` | str | `https://www.acaciafund.org` |
| Site | `SITE_NAME` | str | `AcaciaFund` |
| Site | `SITE_DESCRIPTION` | str | Site description for meta tags |
| Paths | `PROJECT_ROOT` | Path | Project root directory |
| Paths | `REGISTRY_PATH` | Path | `registry.json` location |
| Paths | `TEMPLATE_DIR` | Path | `templates/` directory |
| Paths | `PIPELINE_STATIC_DIR` | Path | `static/` directory |
| Paths | `OUTPUT_DIR` | Path | `dist/` build output |
| Paths | `STATIC_DST_DIR` | Path | `dist/static/` |
| Pillars | `PILLAR_URL_MAP` | dict | Internal key → URL segment |
| Pillars | `PILLAR_URL_REVERSE` | dict | URL segment → internal key |
| Pillars | `PILLAR_NAMES` | dict | Internal key → display name |
| Pillars | `PILLAR_EMOJIS` | dict | Internal key → emoji |
| Quality | `SQI_THRESHOLD_MIN` | float | 0.65 |
| Quality | `SQI_BADGE_HIGH` | float | 0.60 |
| Quality | `SQI_BADGE_MED` | float | 0.35 |
| Quality | `SQI_DEFAULT` | float | 0.50 |
| Interest | `INTEREST_SQI_WEIGHT` | float | 0.60 |
| Interest | `INTEREST_RECENCY_WEIGHT` | float | 0.40 |
| Interest | `INTEREST_RECENCY_DAYS` | int | 180 |
| Version | `URL_STRUCTURE_VERSION` | str | `3.0` (bump for full rebuild) |

## Pillar Definitions

Pillar subcategories and knowledge mappings are also in `config.py`:
- `PILLAR_SUBCATEGORIES` — 3 pillars × 14 subcategories each
- `KNOWLEDGE_TO_PILLAR_CATEGORY` — 11 knowledge categories mapped to pillar subcategories

## Production vs Development

| Aspect | Development | Production |
|--------|-------------|------------|
| Admin credentials | `.env` or defaults | `.env` (secure) |
| Build cache | Enabled (faster) | Disabled (clean build) |
| Deploy target | Local `dist/` | Cloudflare Pages |
| Search index | Generated locally | Generated in CI |

> **See also:** [Config Reference](../reference/config-reference.md), [Cloudflare Deploy](cloudflare-deploy.md)
