# Cloudflare Pages Deployment

AcaciaFund deploys to **Cloudflare Pages** at `https://www.acaciafund.org/`. Deployment is triggered via GitHub Actions.

## Deploy Script

`scripts/deploy_cloudflare.py` triggers a deployment:

```bash
python3 scripts/deploy_cloudflare.py
```

The script sends a `repository_dispatch` event to GitHub Actions:

```python
# Pseudocode
def trigger_deploy():
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"}
    data = {"event_type": "deploy"}
    post("https://api.github.com/repos/.../dispatches", headers=headers, json=data)
```

## Manual Deploy

```bash
# Full rebuild and deploy
rm -rf dist .build_cache.json && python3 build.py && python3 scripts/deploy_cloudflare.py
```

## Continuous Deployment

**Automatic deploys happen:**
- Every Monday at 04:00 UTC (weekly refresh workflow)
- On any push to main branch (standard GitHub Pages workflow)

## GitHub Actions Workflow

The deploy workflow (`.github/workflows/deploy.yml`):

```yaml
jobs:
  build-and-deploy:
    steps:
      - checkout
      - setup-python
      - install-deps
      - build: python3 build.py
      - deploy: wrangler pages publish dist/
```

## Cloudflare Configuration

- **Project:** AcaciaFund
- **Domain:** `https://www.acaciafund.org/`
- **Build output:** `dist/`
- **Redirect rules:** `dist/_redirects`
- **Preview deployments:** On PR branches

## Prerequisites

| Requirement | Source |
|-------------|--------|
| `GITHUB_TOKEN` | GitHub secret (automatically available in Actions) |
| `CLOUDFLARE_API_TOKEN` | Cloudflare API token (stored as GitHub secret) |
| `wrangler` CLI | Installed in CI environment |

> **See also:** [Weekly Refresh](weekly-refresh.md), [Redirect Rules](redirects.md)
