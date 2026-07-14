# Redirect Rules

Redirects handle legacy URL paths and ensure backward compatibility after URL restructuring.

## Cloudflare `_redirects`

The build generates `dist/_redirects` for Cloudflare Pages:

```
/aml/*          /compliance/:splat   301
/aml/signals/*  /compliance/signals/:splat  301
/stock/*        /markets/:splat      301
/stock/signals/*  /markets/signals/:splat  301
/science/*      /research/:splat     301
/contact/*      /knowledge/contact/:splat  301
```

## Meta-Refresh Redirects

For environments without Cloudflare Pages (e.g., local preview), meta-refresh redirect pages are generated:

### Example: `dist/aml/index.html`

```html
<html><head>
  <meta http-equiv="refresh" content="0; url=/compliance/">
  <link rel="canonical" href="/compliance/">
  <script>location.href = '/compliance/';</script>
</head></html>
```

### Generated Redirect Pages

| Path | Redirects To |
|------|-------------|
| `dist/aml/index.html` | `/compliance/` |
| `dist/stock/index.html` | `/markets/` |
| `dist/science/index.html` | `/research/` |

## Legacy URL Changes

| Old Path | New Path | Reason |
|----------|----------|--------|
| `/aml/...` | `/compliance/...` | Pillar rename |
| `/stock/...` | `/markets/...` | Pillar rename |
| `/science/...` | `/research/...` | Section rename |
| `/contact/` | `/knowledge/contact/` | Content restructure |

## Redirect Source

Redirect rules are also defined in `redirects.json` for reference:

```json
[
  {"from": "/aml/*", "to": "/compliance/:splat", "status": 301},
  {"from": "/stock/*", "to": "/markets/:splat", "status": 301}
]
```

## Testing Redirects

```bash
python3 -m pytest tests/test_redirects.py -v
```

Tests verify:
- All legacy paths resolve to new locations
- 301 status codes
- No redirect chains

> **See also:** [Deployment](cloudflare-deploy.md), [URL Structure](../01-architecture/pillars.md)
