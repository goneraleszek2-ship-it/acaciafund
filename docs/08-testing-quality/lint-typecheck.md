# Linting & Type Checking

## Ruff (Linter)

Configuration in `pyproject.toml`:

```toml
[tool.ruff]
target-version = "py310"
line-length = 100
exclude = ["scripts/archive", "tests", ".github"]

[tool.ruff.lint]
select = ["E", "F", "W", "I"]
ignore = ["E501", "W291"]
```

### Run Linter

```bash
ruff check .
```

Common checks:
- `E`: pycodestyle errors
- `F`: pyflakes errors
- `I`: isort import ordering
- `W`: pycodestyle warnings

## Pyright (Type Checker)

Configuration in `pyrightconfig.json`:

```json
{
  "include": ["."],
  "exclude": ["**/scripts/archive", "venv", ".venv-test", ".git", "dist", "static", "data", "docs"],
  "extraPaths": ["services"],
  "reportMissingImports": "none",
  "typeCheckingMode": "standard"
}
```

### Run Type Checker

```bash
pyright
```

Current status: **0 errors** with pyright 1.1.414 (verified 2026-11-05). CI enforces
`BASELINE=0`, so any new type error fails the quality job.

## Pre-commit

Recommended pre-commit hooks:

```bash
# Run linter
ruff check .

# Run type checker
pyright

# Run tests
python3 -m pytest tests/ -v --tb=short
```

## CI Integration

Both `ruff check .` and `pyright` run in CI; the deploy workflow gates on zero
new pyright errors:

```yaml
lint:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-python@v5
    - run: pip install ruff pyright
    - run: ruff check .
    - run: pyright
```

> **See also:** [CI Integration](ci-integration.md), [Test Overview](test-overview.md)
