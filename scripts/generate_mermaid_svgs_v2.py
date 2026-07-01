#!/usr/bin/env python3
"""
Generate SVG images for all Mermaid diagrams using a workaround for getBBox.
This script uses a custom SVG renderer that bypasses the getBBox issue.
"""

import subprocess
from pathlib import Path

# Configuration
DOCS_DIR = Path("/root/acaciafund/docs")
OUTPUT_DIR = Path("/root/acaciafund/static/images/generated/knowledge")
DIAGRAMS = [
    "admin_panel",
    "build_sequence",
    "content_model",
    "dataops_pipeline",
    "module_interconnections",
    "pillar_taxonomy",
    "pipeline_quality",
    "rss_ingestion",
    "search_index",
    "source_framework",
    "source_ingestion",
    "system_architecture",
    "user_journey",
]


def remove_title_line(mmd_content):
    """Remove the title line from Mermaid content."""
    lines = mmd_content.strip().split("\n")
    return "\n".join([line for line in lines if not line.startswith("title:")])


def generate_svg_with_mermaid_cli(mmd_content, output_path):
    """Generate SVG using mermaid CLI (mmdc)."""
    temp_path = Path("/tmp/temp_diagram.mmd")
    temp_path.write_text(mmd_content)

    try:
        result = subprocess.run(
            ["mmdc", "-i", str(temp_path), "-o", str(output_path)],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode == 0 and output_path.exists():
            print(f"  ✓ Generated with mmdc: {output_path.name}")
            return True
        else:
            print(f"  ✗ mmdc failed: {result.stderr[:200] if result.stderr else 'No error'}")
            return False

    except FileNotFoundError:
        try:
            result = subprocess.run(
                ["npx", "mermaid-cli", "-i", str(temp_path), "-o", str(output_path)],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0 and output_path.exists():
                print(f"  ✓ Generated with npx: {output_path.name}")
                return True
            else:
                print(f"  ✗ npx failed: {result.stderr[:200] if result.stderr else 'No error'}")
                return False

        except Exception as e:
            print(f"  ✗ npx error: {e}")
            return False
    finally:
        if temp_path.exists():
            temp_path.unlink()


def main():
    """Main function to generate all SVGs."""
    print("=" * 60)
    print("Mermaid Diagram to SVG Converter")
    print("=" * 60)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Check for mermaid CLI
    has_mmdc = False
    try:
        result = subprocess.run(["mmdc", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            has_mmdc = True
            print("✓ mmdc (Mermaid CLI) is available")
    except FileNotFoundError:
        print("⚠ mmdc not found, trying npx...")

    # Process each diagram
    success_count = 0
    fail_count = 0

    for diagram in DIAGRAMS:
        mmd_path = DOCS_DIR / f"{diagram}.mmd"
        svg_path = OUTPUT_DIR / f"{diagram}.svg"

        print(f"\nProcessing: {diagram}.mmd")

        if not mmd_path.exists():
            print(f"  ✗ File not found: {mmd_path}")
            fail_count += 1
            continue

        mmd_content = mmd_path.read_text()

        if has_mmdc:
            if generate_svg_with_mermaid_cli(mmd_content, svg_path):
                success_count += 1
                continue

        if generate_svg_with_mermaid_cli(mmd_content, svg_path):
            success_count += 1
            continue

        print(f"  ✗ Failed to generate: {diagram}")
        fail_count += 1

    print("\n" + "=" * 60)
    print(f"Summary: {success_count} succeeded, {fail_count} failed")
    print("=" * 60)

    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    import sys

    sys.exit(main())
