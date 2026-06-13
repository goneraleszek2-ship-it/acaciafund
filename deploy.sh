#!/bin/bash
set -e

ACCOUNT_ID="3c5c07a0b2e14740e1324c0bc0732a00"
API_TOKEN="cfat_makavpDfecbARzw94SPYhocwa1i0qtBWo45KhGUNd3876eef"

echo "🚀 Deploying to Cloudflare Pages..."

cd dist

# Upload in batches with rate limiting
find . -type f | grep -v '^\./\.$' | grep -v '^\./\.\.$' | sort | while read file; do
  echo "Uploading: $file"
  curl -s -X POST "https://api.cloudflare.com/client/v4/accounts/$ACCOUNT_ID/pages/assets/upload/acaciafund/$file" \
    -H "Authorization: Bearer $API_TOKEN" \
    -H "Content-Type: application/octet-stream" \
    --data-binary @"$file" > /dev/null 2>&1 || true
  sleep 0.3  # 300ms between requests to avoid rate limits
done

cd ..
echo "✅ Deployment complete!"
