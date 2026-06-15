# Mem0 Integration Tests

This directory contains tests for the Mem0 integration.

## Running Tests

```bash
# Run all Mem0 tests
python3 tests/test_mem0.py

# Run with pytest (if configured)
pytest tests/test_mem0.py -v
```

## Test Coverage

- ✅ Database initialization
- ✅ Conversation storage and retrieval
- ✅ Deployment logging and history
- ✅ Insight storage and retrieval
- ✅ Session management (start/end/get)
- ✅ Commit message extraction
- ✅ Deployment logging convenience function
- ✅ Session querying
- ✅ Insight content querying

## CI Integration

Add to `.github/workflows/deploy-pages.yml`:

```yaml
- name: Run Mem0 tests
  run: python3 -m pytest tests/test_mem0.py -v
```
