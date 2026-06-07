#!/bin/bash
#
# deploy.sh - Deployment script for AcaciaFund (Python-native pipeline)
#
# Usage: ./deploy.sh [--skip-ingest] [--project-name PROJECT]
#
# Options:
#   --skip-ingest   Skip content ingestion step
#   --project-name  Cloudflare Pages project name (default: acaciafund)

set -euo pipefail

SKIP_INGEST=false
PROJECT_NAME="acaciafund"

while [[ $# -gt 0 ]]; do
  case $1 in
    --skip-ingest) SKIP_INGEST=true; shift ;;
    --project-name) PROJECT_NAME="$2"; shift 2 ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

if [[ ! -f "orchestrator.py" ]]; then
  echo "Error: This script must be run from the acaciafund root directory"
  exit 1
fi

if [[ -f ".env" ]]; then
  echo "Loading environment variables from .env"
  export $(cat .env | xargs)
fi

echo "Starting AcaciaFund deployment..."
echo "Project: $PROJECT_NAME"

# Step 1: Run ingest pipeline (fetch HN/arXiv, classify, build registry)
if [[ "$SKIP_INGEST" == false ]]; then
  echo ""
  echo "Step 1: Running ingest pipeline..."
  python3 orchestrator.py --ingest
  echo "Ingest completed."
else
  echo ""
  echo "Step 1: Skipping ingest, building registry from existing content..."
  python3 orchestrator.py --from-content
fi

# Step 2: Generate static site
echo ""
echo "Step 2: Generating static site..."
python3 generator.py
echo "Static site generation completed."

# Step 3: Deploy to Cloudflare Pages
if [[ -n "${CLOUDFLARE_ACCOUNT_ID:-}" ]] && [[ -n "${CLOUDFLARE_API_TOKEN:-}" ]]; then
  echo ""
  echo "Step 3: Deploying to Cloudflare Pages..."
  wrangler pages deploy dist \
    --project-name="$PROJECT_NAME" \
    --config=wrangler.toml \
    --commit-hash=$(git rev-parse --short HEAD 2>/dev/null || echo "latest") \
    --commit-message="Deploy: $(date +%Y-%m-%d)" \
    --branch=main
  echo ""
  echo "Deployment completed!"
  echo "Site: https://$PROJECT_NAME.pages.dev"
else
  echo ""
  echo "Step 3: Skipping deploy (set CLOUDFLARE_ACCOUNT_ID and CLOUDFLARE_API_TOKEN)"
  echo "Preview your site: python3 -m http.server 8000 --dir dist"
fi

