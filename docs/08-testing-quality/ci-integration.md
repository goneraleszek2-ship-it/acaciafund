# CI Integration

Tests, linting, and type checking are integrated into GitHub Actions workflows.

## Standard CI Workflow

`.github/workflows/test.yml` (inferred):

```yaml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.14"
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Lint
        run: ruff check .
      - name: Type check
        run: pyright
      - name: Test
        run: python3 -m pytest tests/ -v --timeout=60
```

## Weekly Refresh Workflow

`.github/workflows/source-refresh.yml`:

- **Schedule:** Every Monday at 04:00 UTC
- **Steps:**
  1. Regenerate ontology
  2. Source synthesis + verification
  3. Source freshness check
  4. Regenerate glossaries
  5. Generate learn modules
  6. Full build
  7. Links check + SQI audit
  8. Upload artifacts (30-day retention)
  9. Commit data files (`data/ontology.json`, `registry.json`, `data/source_health.json`)
  10. Deploy to Cloudflare

## Test Timeouts

Some tests may hang due to heavy imports (pandas, PIL). The CI workflow uses:

```bash
timeout 300 python3 -m pytest tests/ -v --timeout=60
```

## Artifacts

Generated artifacts retained for 30 days:
- `dist/` (full build output)
- `registry.json` (with any updates)
- `data/ontology.json`
- `data/source_health.json`

## Failure Handling

| Failure | Impact | Action |
|---------|--------|--------|
| Lint error | CI fails | Fix issues, re-push |
| Type error | CI fails | Fix types or add ignore |
| Test failure | CI fails | Fix test or code |
| Build error | CI fails | Check build_errors.log |
| Deploy failure | Site stale | Retry deploy |

> **See also:** [Testing Overview](test-overview.md), [Weekly Refresh](../07-deployment-ops/weekly-refresh.md)
