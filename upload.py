#!/usr/bin/env python3
import os
import sys
import requests
import time

ACCOUNT_ID = "3c5c07a0b2e14740e1324c0bc0732a00"
API_TOKEN = "cfat_makavpDfecbARzw94SPYhocwa1i0qtBWo45KhGUNd3876eef"
PROJECT_NAME = "acaciafund"
BASE_URL = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/pages/assets/upload/{PROJECT_NAME}"

headers = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/octet-stream",
}

dist_dir = "dist"
uploaded = 0
errors = 0

def upload_file(file_path):
    global uploaded, errors
    try:
        with open(file_path, 'rb') as f:
            response = requests.post(BASE_URL, headers=headers, data=f, timeout=30)
            if response.status_code == 200:
                uploaded += 1
                return True
            elif response.status_code == 429:
                # Rate limited - wait
                retry_after = 2
                print(f"  Rate limited, waiting {retry_after}s...")
                time.sleep(retry_after)
                return upload_file(file_path)
            else:
                errors += 1
                return False
    except Exception as e:
        errors += 1
        return False

print("🚀 Uploading to Cloudflare Pages...")
print(f"Target: {BASE_URL}")

files = []
for root, _, filenames in os.walk(dist_dir):
    for filename in filenames:
        if filename in ['upload.py', 'deploy.sh']:
            continue
        file_path = os.path.join(root, filename)
        rel_path = os.path.relpath(file_path, dist_dir)
        files.append((rel_path, file_path))

print(f"\nTotal files: {len(files)}")

for rel_path, file_path in files:
    print(f"\nUploading: {rel_path}")
    upload_file(file_path)
    # Respectful rate limiting
    time.sleep(0.5)

print(f"\n✅ Done! Uploaded: {uploaded}, Errors: {errors}")
