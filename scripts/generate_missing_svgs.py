#!/usr/bin/env python3
"""
Generate SVG images for all Mermaid diagrams using the mermaid package.
"""

import subprocess
import sys
import textwrap
from pathlib import Path

PROJECT_ROOT = Path("/root/acaciafund")
DOCS_DIR = PROJECT_ROOT / "docs"
OUTPUT_DIR = PROJECT_ROOT / "static" / "images" / "generated" / "knowledge"
DIAGRAMS = [
    "admin_panel",
    "build_sequence",
    "pillar_taxonomy",
]


def generate_svg(mmd_path, svg_path, diagram_name):
    """Generate SVG using node mermaid package."""
    # Create a Node.js script
    node_script = textwrap.dedent(f"""
    const createDOMPurify = require('/root/acaciafund/node_modules/dompurify');
    const {{ JSDOM }} = require('/root/node_modules/jsdom');
    const dom = new JSDOM('<!DOCTYPE html><html><body></body></html>', {{
      url: 'http://localhost',
      pretendToBeVisual: true,
      resources: 'usable'
    }});
    global.window = dom.window;
    global.document = dom.window.document;
    global.CSSStyleSheet = dom.window.CSSStyleSheet;
    global.DOMPurify = createDOMPurify(dom.window);
    global.DOMPurify.sanitize = global.DOMPurify.sanitize.bind(global.DOMPurify);
    global.DOMPurify.addHook = global.DOMPurify.addHook.bind(global.DOMPurify);

    // Mock SVGElement.getBBox
    dom.window.SVGElement.prototype.getBBox = function() {{
      return {{ x: 0, y: 0, width: 100, height: 20, top: 0, bottom: 20, left: 0, right: 100 }};
    }};

    const mermaid = require('/root/acaciafund/node_modules/mermaid/dist/mermaid.core.mjs').default;
    const fs = require('fs');

    const mmdContent = fs.readFileSync('{mmd_path}', 'utf8');
    const outputPath = '{svg_path}';

    // Initialize mermaid with loose security level
    mermaid.initialize({{startOnLoad: false, securityLevel: 'loose'}});

    // Remove title line
    const lines = mmdContent.split('\\n');
    const filtered = lines.filter(l => !l.startsWith('title:')).join('\\n');

    try {{
      mermaid.parse(filtered).then(() => {{
        return mermaid.render('{diagram_name}_svg', filtered);
      }}).then(result => {{
        const svg = result.svg;
        fs.writeFileSync(outputPath, svg);
        console.log('SVG generated successfully:', outputPath);
        process.exit(0);
      }}).catch(err => {{
        console.error('Error:', err.message);
        process.exit(1);
      }});
    }} catch (e) {{
      console.error('Error:', e.message);
      process.exit(1);
    }}
    """).strip()

    # Write script to temp file
    script_path = Path(f"/tmp/generate_{diagram_name}.js")
    script_path.write_text(node_script)

    try:
        result = subprocess.run(
            ["node", str(script_path)], capture_output=True, text=True, timeout=60
        )

        if result.returncode == 0 and Path(svg_path).exists():
            print(f"  ✓ Generated: {Path(svg_path).name}")
            return True
        else:
            print(f"  ✗ Failed: {result.stderr[:200] if result.stderr else 'No error'}")
            return False
    finally:
        if script_path.exists():
            script_path.unlink()


def main():
    """Main function to generate all SVGs."""
    print("=" * 60)
    print("Mermaid Diagram to SVG Converter (Node.js)")
    print("=" * 60)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Check for mermaid
    mermaid_path = PROJECT_ROOT / "node_modules" / "mermaid" / "dist" / "mermaid.core.mjs"
    if not mermaid_path.exists():
        print(f"✗ mermaid.core.mjs not found at {mermaid_path}")
        return 1

    print("✓ mermaid is available")

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

        if generate_svg(str(mmd_path), str(svg_path), diagram):
            success_count += 1
        else:
            fail_count += 1

    print("\n" + "=" * 60)
    print(f"Summary: {success_count} succeeded, {fail_count} failed")
    print("=" * 60)

    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
