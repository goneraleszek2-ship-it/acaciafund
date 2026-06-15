#!/usr/bin/env python3
"""Update registry.json with clean diagrams content from .mmd files."""

import json
import os
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Read create_diagrams_page.py output
script_path = PROJECT_ROOT / "scripts" / "create_diagrams_page.py"
result = os.popen(f"python3 {script_path}").read()

# Extract the HTML content (everything before the mermaid init script)
# The script outputs HTML with <script> tags at the end for mermaid init
# We need just the HTML content for body_html

# Find the position of the first <script> tag (mermaid init)
mermaid_script_start = result.find('<script src="/static/js/mermaid.min.js"')
if mermaid_script_start > 0:
    body_html = result[:mermaid_script_start].strip()
else:
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
with open(registry_path, "w") as f:
    json.dump(registry, f, indent=2, ensure_ascii=False)

print(f"✅ Updated registry.json with clean diagrams content")
print(f"New body_html length: {len(body_html)} bytes")

# Verify no emojis or multi-line nodes in Mermaid sections (not ASCII fallback)
# Extract just the Mermaid content (between <div class="mermaid" and </div>)
mermaid_sections = re.findall(r'<div class="mermaid".*?>(.*?)</div>', body_html, re.DOTALL)
for section in mermaid_sections:
    if "🖥️" in section or "📄" in section:
        print("⚠️  WARNING: Emojis still present in Mermaid section!")
        sys.exit(1)
    # Check for actual multi-line node definitions - [label with \n inside]
    # This would be like [label\n  continuation] which is invalid
    if re.search(r'\[[^\]]*\n[^\]]*\]', section):
        print("⚠️  WARNING: Multi-line nodes still present in Mermaid section!")
        sys.exit(1)

print("✅ Verified: No emojis, no multi-line nodes in Mermaid sections")
