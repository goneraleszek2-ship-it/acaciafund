#!/bin/bash
set -euo pipefail
cd /root/acaciafund
source venv/bin/activate
DATE=$(date +%Y-%m-%d)
LOGDIR="/root/acaciafund/logs/daily"
mkdir -p "$LOGDIR"
LOGFILE="$LOGDIR/${DATE}.log"
{
    echo "=== Daily Summary for $DATE ==="
    echo "Running validation..."
    python scripts/validation_layer.py 2>&1 | tee -a "$LOGFILE"
    echo ""
    echo "Checking for new/changed files in backup..."
    # Simple check: list files modified in last 24h
    find /root/acaciafund/backup -type f -mtime -1 -printf '%TY-%m-%d %H:%M:%S %p\n' 2>/dev/null | tee -a "$LOGFILE"
    echo ""
    echo "Quarantine directory contents:"
    ls -la /root/acaciafund/quarantine 2>/dev/null || echo "No quarantine directory."
} >> "$LOGFILE" 2>&1
echo "Summary written to $LOGFILE"
