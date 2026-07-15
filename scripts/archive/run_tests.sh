#!/usr/bin/env bash
# Run the AcaciaFund test suite.
# Redirects to a log file to avoid Python 3.14 pipe buffering issues.
set +euo pipefail

LOG="/tmp/acaciafund_tests_$(date +%Y%m%d_%H%M%S).log"

echo "Running tests..."
python3 -u -m pytest "$@" > "$LOG" 2>&1
RC=$?

if [ $RC -eq 0 ]; then
    SUMMARY=$(grep -E "passed|failed" "$LOG" | tail -1)
    echo "$SUMMARY"
    echo "log: $LOG"
else
    tail -10 "$LOG"
    echo "FAILED (exit=$RC) — log: $LOG"
fi
exit $RC
