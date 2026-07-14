#!/bin/bash
set -euo pipefail
# Usage: ./run_ingestion_with_validation.sh <ingestion_script> [args...]
# The ingestion script should output a list of processed files or produce Parquet in a known location.
# We'll assume the ingestion script writes Parquet files to a temporary location defined by env var OUTPUT_DIR.
# For simplicity, we'll run the script, then run the adapter on the OUTPUT_DIR.
cd /root/acaciafund
source venv/bin/activate

INGEST_SCRIPT="$1"
shift
ARGS=("$@")

# Define where ingestion should output Parquet (can be overridden)
OUTPUT_DIR="${OUTPUT_DIR:-/root/acaciafund/tmp_ingest}"
mkdir -p "$OUTPUT_DIR"

# Run ingestion
echo "Running ingestion script: $INGEST_SCRIPT ${ARGS[@]}"
python "$INGEST_SCRIPT" "${ARGS[@]}" || {
    echo "Ingestion script failed"
    exit 1
}

# Validate using adapter
ADAPTER="/root/acaciafund/backup/ontology_adapter_template.py"
QUARANTINE="/root/acaciafund/quarantine"
LOG_FILE="/root/acaciafund/integrity_events.log"

echo "Running adapter validation on $OUTPUT_DIR"
python "$ADAPTER" --input-dir "$OUTPUT_DIR" --output-dir /tmp/validated_json 2>&1 | tee -a "$LOG_FILE" || {
    echo "Adapter validation failed - moving offending files to quarantine"
    # For simplicity, move the whole output dir to quarantine with timestamp
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    mv "$OUTPUT_DIR" "$QUARANTINE/ingest_failed_$TIMESTAMP"
    mkdir -p "$OUTPUT_DIR"
    exit 1
}
echo "Validation succeeded"
# Optionally, move validated Parquet to dist or wherever needed
