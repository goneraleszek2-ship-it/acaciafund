#!/usr/bin/env python3
"""Deploy AcaciaFund to Cloudflare Pages"""

import os
import sys
import time
import urllib.request
import urllib.error

ACCOUNT_ID = "3c5c07a0b2e14740e1324c0bc0732a00"
API_TOKEN = "YOUR_CLOUDFLARE_API_TOKEN_HERE"
BASE_URL = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/pages/assets/upload/acaciafund"

def upload_file(file_path, relative_path):
    """Upload a single file to Cloudflare Pages"""
    try:
        with open(file_path, 'rb') as f:
            data = f.read()
        
        req = urllib.request.Request(
            f"{BASE_URL}/{relative_path}",
            data=data,
            headers={
                'Authorization': f'Bearer {API_TOKEN}',
                'Content-Type': 'application/octet-stream'
            },
            method='POST'
        )
        
        with urllib.request.urlopen(req, timeout=30) as response:
            return response.status == 200
            
    except Exception as e:
        print(f"  Error uploading {relative_path}: {str(e)[:50]}")
        return False

def main():
    dist_dir = "/root/acaciafund/dist"
    
    if not os.path.exists(dist_dir):
        print(f"Error: {dist_dir} not found")
        sys.exit(1)
    
    files = []
    for root, dirs, filenames in os.walk(dist_dir):
        for filename in filenames:
            file_path = os.path.join(root, filename)
            relative_path = os.path.relpath(file_path, dist_dir)
            files.append((file_path, relative_path))
    
    files.sort(key=lambda x: x[1])
    
    print(f"🚀 Found {len(files)} files to upload...")
    print(f"🚀 Starting deployment to Cloudflare Pages...")
    print()
    
    success_count = 0
    error_count = 0
    
    for file_path, relative_path in files:
        success = upload_file(file_path, relative_path)
        if success:
            success_count += 1
        else:
            error_count += 1
        
        # Rate limiting
        time.sleep(0.25)  # 250ms between requests
    
    print()
    print(f"✅ Deployment complete!")
    print(f"   Success: {success_count}")
    print(f"   Errors: {error_count}")
    
    if error_count > 0:
        print(f"\n⚠️  Some files failed to upload. Please check the Cloudflare dashboard.")

if __name__ == "__main__":
    main()
