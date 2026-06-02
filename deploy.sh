#!/bin/bash
#
# deploy.sh - Manual deployment script for AcaciaFund
# Replaces GitHub Actions workflow for users on free tier limits
#
# Usage: ./deploy.sh [--skip-ingest] [--project-name PROJECT]
#
# Options:
#   --skip-ingest   Skip content ingestion step (use existing content)
#   --project-name  Cloudflare Pages project name (default: acaciafund)
#
# set -euo pipefail

# Default values
SKIP_INGEST=false
PROJECT_NAME="acaciafund"

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --skip-ingest)
      SKIP_INGEST=true
      shift
      ;;
    --project-name)
      PROJECT_NAME="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Check if we're in the right directory
if [[ ! -f "ingest.py" ]]; then
  echo "Error: This script must be run from the acaciafund root directory"
  exit 1
fi

# Load environment variables if .env exists
if [[ -f ".env" ]]; then
  echo "Loading environment variables from .env"
  export $(cat .env | xargs)
fi

# Check required environment variables
if [[ -z "${CLOUDFLARE_ACCOUNT_ID:-}" ]]; then
  echo "Error: CLOUDFLARE_ACCOUNT_ID environment variable is required"
  exit 1
fi

if [[ -z "${CLOUDFLARE_API_TOKEN:-}" ]]; then
  echo "Error: CLOUDFLARE_API_TOKEN environment variable is required"
  exit 1
fi

echo "Starting AcaciaFund deployment..."
echo "Account ID: $CLOUDFLARE_ACCOUNT_ID"
echo "Project: $PROJECT_NAME"

# Step 1: Run content ingestion (existing script)
if [[ "$SKIP_INGEST" == false ]]; then
  echo ""
  echo "Step 1: Running content ingestion..."
  python3.13 ingest.py
  echo "Content ingestion completed."
else
  echo ""
  echo "Step 1: Skipping content ingestion (--skip-ingest flag used)"
fi

# Step 2: Convert content to registry (our orchestrator)
echo ""
echo "Step 2: Converting content to registry..."
python3.13 orchestrator.py
echo "Content conversion completed."

# Step 3: Generate static site (our generator)
echo ""
echo "Step 3: Generating static site..."
python3.13 generator.py
echo "Static site generation completed."

# Step 4: Deploy to Cloudflare Pages
echo ""
echo "Step 4: Deploying to Cloudflare Pages..."
wrangler pages deploy dist \
  --project-name="$PROJECT_NAME" \
  --commit-hash=$(git rev-parse --short HEAD) \
  --commit-message="Deploy via deploy.sh: $(date +%Y-%m-%d)" \
  --branch=main

echo ""
echo "Deployment completed successfully!"
echo "Your site should be available at: https://$PROJECT_NAME.pages.dev"