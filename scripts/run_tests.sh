#!/usr/bin/env bash
# Consolidated test runner for AcaciaFund.
# Runs test files in isolation to avoid timeout issues from large combined suites.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR/.."
cd "$PROJECT_ROOT"

PYTHON="python3"
TIMEOUT=120

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

PASS=0
FAIL=0
FAILED_TESTS=""
RESULTS_FILE="/tmp/acacia_test_results.$$"
> "$RESULTS_FILE"

# Test groups ordered by speed (fastest first)
TEST_GROUPS=(
    # Core P4/P5 modules (fast)
    "tests/test_evidence_grade.py"
    "tests/test_export_research.py"
    "tests/test_adaptive.py"
    "tests/test_contradiction.py"
    "tests/test_source_trail.py"

    # Schema builder & retention (light dependencies)
    "tests/test_schema_builder.py"
    "tests/test_retention_engine.py"

    # Utility modules
    "tests/test_compositor.py"
    "tests/test_extractors.py"
    "tests/test_generate_pages.py"
    "tests/test_contracts.py"

    # Ontology & data
    "tests/test_ontology.py"
    "tests/test_data.py"
    "tests/test_content.py"
    "tests/test_metadata.py"

    # Build & taxonomy tests
    "tests/test_urls.py"
    "tests/test_build_cache.py"
    "tests/test_check_source_freshness.py"
    "tests/test_source_synthesis.py"

    # Legacy/slow tests (run individually)
    "tests/test_build_taxonomies.py"
)

SLOW_GROUPS=(
    "tests/test_learn_generation.py"
    "tests/test_retention_engine.py"
)

echo "=========================================
 AcaciaFund Test Runner
 $(date -u '+%Y-%m-%d %H:%M UTC')
========================================="

run_group() {
    local label="$1" group="$2" timeout_val="${3:-$TIMEOUT}"

    if [ ! -f "$group" ]; then
        echo -e "  ${label} ${YELLOW}[SKIP]${NC}"
        return 0
    fi

    echo -ne "  ${label} ${group}... "
    if timeout "$timeout_val" $PYTHON -u -m pytest "$group" -v >> "$RESULTS_FILE" 2>&1; then
        echo -e "${GREEN}PASS${NC}"
        PASS=$((PASS + 1))
    else
        echo -e "${RED}FAIL${NC}"
        FAIL=$((FAIL + 1))
        FAILED_TESTS="$FAILED_TESTS $group"
    fi
}

echo ""
echo "--- Core Tests (fast, 120s timeout) ---"
for group in "${TEST_GROUPS[@]}"; do
    run_group "" "$group" 120
done

echo ""
echo "--- Slow / Legacy Tests (300s timeout each) ---"
for group in "${SLOW_GROUPS[@]}"; do
    run_group "" "$group" 300
done

echo ""
echo "========================================="
echo -e " Results: ${GREEN}${PASS} passed${NC}, ${RED}${FAIL} failed${NC}"
echo "========================================="

if [ -n "$FAILED_TESTS" ]; then
    echo ""
    echo "Failed groups:"
    for f in $FAILED_TESTS; do
        echo "  - $f"
    done
    echo ""
    echo "Last 50 lines of output for each failed group:"
    for f in $FAILED_TESTS; do
        echo "=== $f ==="
        grep -A 50 "FAILED\|ERROR" "$RESULTS_FILE" | tail -50
    done
    exit 1
fi

# JS tests
echo ""
echo "--- Progressive Disclosure JS ---"
if command -v node &>/dev/null && [ -f "tests/test_progressive_disclosure.js" ]; then
    if timeout 30 node tests/test_progressive_disclosure.js; then
        echo -e "${GREEN}JS tests passed${NC}"
    else
        echo -e "${RED}JS tests failed${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}JS tests skipped (node not found or no test file)${NC}"
fi

echo ""
echo "All tests passed."
