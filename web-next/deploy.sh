#!/bin/bash

# Build and deploy AcaciaFund site to Cloudflare Pages

# Exit on any error
set -e

echo "🔨 Building site..."
npm run build

echo "📦 Exporting site..."
npm run export

echo "🚀 Deploying to Cloudflare Pages..."
CLOUDFLARE_API_TOKEN=cfat_makavpDfecbARzw94SPYhocwa1i0qtBWo45KhGUNd3876eef \
CLOUDFLARE_ACCOUNT_ID=3c5c07a0b2e14740e1324c0bc0732a00 \
npx wrangler pages deploy out/ --project-name=acaciafund-web-next --commit-dirty=true

echo "✅ Deployment complete!"