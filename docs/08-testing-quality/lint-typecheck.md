# Linting & Type Checking

## Ruff (Linter)

Configuration in `pyproject.toml`:

```toml
[tool.ruff]
line-length = 120
target-version = "py314"
select = ["E", "F", "I", "N", "W", "UP"]
ignore = ["E501"]  # Line length (handled by formatter)
```

### Run Linter

```bash
ruff check .
```

Common checks:
- `E`: pycodestyle errors
- `F`: pyflakes errors
- `I`: isort import ordering
- `N`: naming conventions
- `W`: pycodestyle warnings
- `UP`: pyupgrade (modern Python syntax)

## Pyright (Type Checker)

Configuration in `pyrightconfig.json`:

```json
{
    "typeCheckingMode": "standard",
    "include": [
        "build.py",
        "config.py",
        "core/",
        "scripts/",
        "schemas.py",
        "seed_learn.py"
    ],
    "ignore": [
        "scripts/archive/",
        "venv/"
    ]
}
```

### Run Type Checker

```bash
pyright
```

### Known Type Issues

Some modules are excluded or have inline `pyright: ignore` comments:

| Issue | Location | Reason |
|-------|----------|--------|
| Missing `services.mem0` | `build.py:105` | `reportMissingImports` — planned module |
| Dynamic attributes | Various | `getattr` patterns for flexible item access |
| Jinja2 template types | Template files | Not Python, no type info |

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

Both `ruff check .` and `pyright` can be run in CI:

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
