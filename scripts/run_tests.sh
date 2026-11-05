#!/usr/bin/env bash
# Consolidated test runner for AcaciaFund.
#
# Default: one full pytest run (fast) + every JS suite + optional coverage.
# Pass --isolated to run each Python test module in its own pytest process
# (useful for debugging hangs/import-order issues).
#
# Environment:
#   ACACIA_TEST_TIMEOUT  seconds for the full pytest run (default 900)
#   WITH_COVERAGE=1      run the slow informational coverage report (off by default)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR/.."
cd "$PROJECT_ROOT"

PYTHON="python3"
TIMEOUT="${ACACIA_TEST_TIMEOUT:-900}"
ISOLATED=0
[ "${1:-}" = "--isolated" ] && ISOLATED=1

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

PASS=0
FAIL=0
FAILED_TESTS=()
RESULTS_FILE="$(mktemp -t acacia_test_results.XXXXXX)"
trap 'rm -f "$RESULTS_FILE"' EXIT

echo "=========================================
 AcaciaFund Test Runner
 $(date -u '+%Y-%m-%d %H:%M UTC')
 Mode: $([ "$ISOLATED" -eq 1 ] && echo isolated || echo full)
========================================="

run_python() {
    local label="$1" cmd_timeout="$2"
    shift 2
    echo -n "  ${label}... "
    if timeout "$cmd_timeout" "$PYTHON" -u -m pytest "$@" -q >> "$RESULTS_FILE" 2>&1; then
        echo -e "${GREEN}PASS${NC}"
        PASS=$((PASS + 1))
    else
        echo -e "${RED}FAIL${NC}"
        FAIL=$((FAIL + 1))
        FAILED_TESTS+=("$label")
    fi
}

if [ "$ISOLATED" -eq 1 ]; then
    echo ""
    echo "--- Python Tests (isolated modules) ---"
    for test_file in tests/test_*.py; do
        run_python "$test_file" 180 "$test_file"
    done
else
    echo ""
    echo "--- Python Tests (full suite, ${TIMEOUT}s timeout) ---"
    run_python "pytest tests/" "$TIMEOUT" tests/
fi

echo ""
echo "--- JS Tests ---"
if command -v node &>/dev/null; then
    for js_test in tests/test_*.js; do
        echo -n "  ${js_test}... "
        if timeout 30 node "$js_test" >> "$RESULTS_FILE" 2>&1; then
            echo -e "${GREEN}PASS${NC}"
            PASS=$((PASS + 1))
        else
            echo -e "${RED}FAIL${NC}"
            FAIL=$((FAIL + 1))
            FAILED_TESTS+=("$js_test")
        fi
    done
else
    echo "  JS tests skipped (node not found)"
fi

echo ""
echo "========================================="
echo -e " Results: ${GREEN}${PASS} passed${NC}, ${RED}${FAIL} failed${NC}"
echo "========================================="

if [ "${#FAILED_TESTS[@]}" -gt 0 ]; then
    echo ""
    echo "Failed groups:"
    for f in "${FAILED_TESTS[@]}"; do
        echo "  - $f"
    done
    echo ""
    echo "Last 80 lines of output:"
    tail -80 "$RESULTS_FILE"
    exit 1
fi

echo ""
echo "All tests passed."

# Coverage report (informational, non-blocking)
if [ "${WITH_COVERAGE:-0}" = "1" ] && $PYTHON -c "import pytest_cov" &>/dev/null; then
    echo ""
    echo "--- Coverage (core + scripts, informational) ---"
    timeout 600 $PYTHON -m pytest tests/ -q --cov=core --cov=scripts \
        --cov-report=term:skip-covered --no-header -p no:cacheprovider \
        >> "$RESULTS_FILE" 2>&1 || echo "  coverage report skipped (timeout or error)"
    grep -E "^(TOTAL|core/|scripts/)" "$RESULTS_FILE" | tail -15
fi
