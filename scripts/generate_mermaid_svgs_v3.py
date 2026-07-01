#!/usr/bin/env python3
"""
Generate SVG images for all Mermaid diagrams.
Uses Mermaid 11.15.0 via npm mermaid package with jsdom.
"""

import sys
from pathlib import Path

# Add node_modules to path
sys.path.insert(0, "/tmp/node_modules/mermaid/dist")

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


def generate_svg(mmd_content, output_path, diagram_name):
    """Generate SVG using mermaid.core.mjs."""
    import importlib.util

    from jsdom import JSDOM

    # Create DOM
    dom = JSDOM(
        "<!DOCTYPE html><html><body></body></html>",
        {"url": "http://localhost", "pretendToBeVisual": True, "resources": "usable"},
    )

    window = dom.window

    # Setup DOMPurify
    try:
        from dompurify import DOMPurify

        purify = DOMPurify(window)
        window.DOMPurify = purify
    except Exception as e:
        print(f"  ⚠ DOMPurify not available: {e}")
        return False

    # Load mermaid
    mermaid_path = "/tmp/node_modules/mermaid/dist/mermaid.core.mjs"
    spec = importlib.util.spec_from_file_location("mermaid", mermaid_path)
    mermaid = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mermaid)

    # Initialize
    config = {
        "startOnLoad": False,
        "theme": "default",
        "themeVariables": {
            "background": "#ffffff",
            "primaryColor": "#fff",
            "primaryBorder": "#d97706",
            "primaryTextColor": "#000",
            "secondaryColor": "#fff",
            "secondaryBorder": "#64748b",
            "secondaryTextColor": "#000",
            "tertiaryColor": "#fff",
            "tertiaryBorder": "#22c55e",
            "tertiaryTextColor": "#000",
            "lineColor": "#444",
            "fontSize": "14px",
            "fontFamily": "Arial, sans-serif",
        },
        "flowchart": {"useMaxWidth": True, "htmlLabels": True},
        "sequence": {"useMaxWidth": True, "htmlLabels": True},
        "class": {"useMaxWidth": True, "htmlLabels": True},
        "state": {"useMaxWidth": True, "htmlLabels": True},
        "pie": {"useMaxWidth": True, "htmlLabels": True},
        "xy": {"useMaxWidth": True, "htmlLabels": True},
        "timeline": {"useMaxWidth": True, "htmlLabels": True},
        "gantt": {"useMaxWidth": True, "htmlLabels": True},
        "git": {"useMaxWidth": True, "htmlLabels": True},
        "er": {"useMaxWidth": True, "htmlLabels": True},
        "mindmap": {"useMaxWidth": True, "htmlLabels": True},
        "flowchart-v2": {"useMaxWidth": True, "htmlLabels": True},
    }

    mermaid.initialize(config)

    # Remove title and render
    filtered_content = remove_title_line(mmd_content)

    try:
        # Detect diagram type
        try:
            diag_type = mermaid.detectType(filtered_content)
            print(f"  Detected type: {diag_type}")
        except Exception as e:
            print(f"  Warning: Could not detect type: {str(e)[:100]}")
            diag_type = None

        # Parse first
        try:
            mermaid.parse(filtered_content)
            print("  Parse successful")
        except Exception as e:
            print(f"  Parse error: {str(e)[:200]}")
            return False

        # Render
        svg = mermaid.render(f"{diagram_name}_svg", filtered_content)

        # Write to file
        output_path.write_text(svg)

        print(f"  ✓ Generated: {output_path.name} ({len(svg)} bytes)")
        return True

    except Exception as e:
        print(f"  ✗ Error: {str(e)[:300]}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Main function to generate all SVGs."""
    print("=" * 60)
    print("Mermaid Diagram to SVG Converter")
    print("=" * 60)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Check for mermaid
    mermaid_path = Path("/tmp/node_modules/mermaid/dist/mermaid.core.mjs")
    if not mermaid_path.exists():
        print("✗ mermaid.core.mjs not found at /tmp/node_modules/mermaid/dist/")
        print("  Run: npm install mermaid in /tmp")
        return 1

    print("✓ mermaid.core.mjs is available")

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

        if generate_svg(mmd_content, svg_path, diagram):
            success_count += 1
        else:
            fail_count += 1

    print("\n" + "=" * 60)
    print(f"Summary: {success_count} succeeded, {fail_count} failed")
    print("=" * 60)

    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
