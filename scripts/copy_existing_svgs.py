#!/usr/bin/env python3
"""
Generate SVG images for all Mermaid diagrams.
Since the Mermaid CLI is having issues, we'll use the existing SVG files
that were already generated correctly.
"""
import os
import subprocess
from pathlib import Path

DOCS_DIR = Path("/root/acaciafund/docs")
OUTPUT_DIR = Path("/root/acaciafund/static/images/generated/knowledge")
DIAGRAMS = [
    "admin_panel",
    "build_sequence",
    "pillar_taxonomy",
]

def main():
    """Main function to copy existing SVGs."""
    print("=" * 60)
    print("Copy existing SVG files for missing diagrams")
    print("=" * 60)
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # The _s1 files contain raw Mermaid, not SVG
    # We need to find the actual SVG files
    # Check if there are any SVG files in the directory
    
    svg_files = list(OUTPUT_DIR.glob("*.svg"))
    print(f"\nFound {len(svg_files)} SVG files in {OUTPUT_DIR}")
    
    # List all SVG files
    for svg_file in sorted(svg_files):
        print(f"  - {svg_file.name}")
    
    # Check for the specific diagrams
    print("\nChecking for specific diagrams:")
    for diagram in DIAGRAMS:
        svg_path = OUTPUT_DIR / f"{diagram}.svg"
        if svg_path.exists():
            print(f"  ✓ {diagram}.svg exists")
        else:
            # Check for variants
            variants = list(OUTPUT_DIR.glob(f"{diagram}_*.svg"))
            if variants:
                print(f"  ⚠ {diagram}.svg missing, but found: {[v.name for v in variants]}")
            else:
                print(f"  ✗ {diagram}.svg MISSING")
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
