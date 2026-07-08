#!/usr/bin/env python3
"""Update registry.json with clean diagrams content from .mmd files."""

import json
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Read create_diagrams_page.py output
script_path = PROJECT_ROOT / "scripts" / "create_diagrams_page.py"
result = os.popen(f"python3 {script_path}").read()

# The script now outputs clean HTML without mermaid init script
# All content is the body_html
body_html = result.strip()

print(f"Generated body_html length: {len(body_html)} bytes")

# Load registry.json
registry_path = PROJECT_ROOT / "registry.json"
with open(registry_path) as f:
    registry = json.load(f)

# Find and update the diagrams page entry
diagrams_entry = None
for i, item in enumerate(registry["content"]):
    if item.get("slug") == "knowledge/diagrams":
        diagrams_entry = item
        print(f"Found diagrams entry at index {i}")
        print(f"Old body_html length: {len(item.get('body_html', ''))} bytes")
        break

if not diagrams_entry:
    print("ERROR: Could not find knowledge/diagrams entry in registry.json")
    sys.exit(1)

# Update body_html
diagrams_entry["body_html"] = body_html

# Save updated registry
from core.registry_io import save_registry as _atomic_save
_atomic_save(registry, registry_path)

print("✅ Updated registry.json with clean diagrams content")
print(f"New body_html length: {len(body_html)} bytes")

# Verify SVG references are present
svg_count = body_html.count('<img src="/static/images/generated/knowledge/')
print(f"Found {svg_count} SVG image references")

if svg_count == 0:
    print("⚠️  WARNING: No SVG image references found!")
    sys.exit(1)

print(f"✅ Verified: {svg_count} SVG image references present")
