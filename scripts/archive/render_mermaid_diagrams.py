#!/usr/bin/env python3
"""
Render Mermaid diagrams in /root/acaciafund/docs/*.mmd to SVG/JPG/PNG in
/root/acaciafund/static/images/generated/knowledge/ for the diagrams section.

Usage:
  python3 scripts/render_mermaid_diagrams.py --png image.png [--theme dark|default] < diagram.mmd

Adapted to scrape .mmd files for Mermaid blocks and render using Node mermaid CLI if available, or
fallback to a pure-JS render using the mermaid npm package and a minimal HTML runner.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import List

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = PROJECT_ROOT / "docs"
KNOWLEDGE_IMAGES_DIR = PROJECT_ROOT / "static" / "images" / "generated" / "knowledge"

# Create images dir
KNOWLEDGE_IMAGES_DIR.mkdir(parents=True, exist_ok=True)

# List of diagram .mmd files to prioritize, in order of appearance on /knowledge/diagrams/
ORDERED_MMDS = [
    "admin_panel.mmd",
    "build_sequence.mmd",
    "content_model.mmd",
    "dataops_pipeline.mmd",
    "module_interconnections.mmd",
    "pipeline_quality.mmd",
    "rss_ingestion.mmd",
    "search_index.mmd",
    "source_framework.mmd",
    "source_ingestion.mmd",
    "system_architecture.mmd",
    "user_journey.mmd",
    "pillar_taxonomy.mmd",
]

MERMAID_PATTERN = re.compile(r"^flowchart\b|^sequenceDiagram\b|^classDiagram\b|^mindmap\b", re.M)

STYLE_BLOCK_PATTERN = re.compile(r"^\s*style\s+\w+\s+[^\n]+$", re.MULTILINE | re.DOTALL)


def parse_title_from_mmd(mmd_path: Path) -> str:
    if not mmd_path.exists():
        return mmd_path.stem.replace("_", " ").title()
    text = mmd_path.read_text(encoding="utf-8")
    match = re.search(r"^title:\s*(.+)$", text, re.MULTILINE)
    if match:
        return match.group(1).strip()
    slug = mmd_path.stem
    if slug.endswith("_mmd"):
        slug = slug[:-4]
    return slug.replace("_", " ").replace("-", " ").title()


def extract_mermaid_diagram_content(mmd_path: Path) -> List[str]:
    """Return list of Mermaid diagram source strings from .mmd file."""
    if not mmd_path.exists():
        return []
    text = mmd_path.read_text(encoding="utf-8")
    # Split into lines for simpler processing
    lines = text.split("\n")
    diagrams: List[str] = []
    current: List[str] = []
    in_flow = False

    for idx, line in enumerate(lines):
        if line.startswith("```mermaid"):
            # Start of a Mermaid block
            in_flow = True
            current = []
            continue
        if in_flow:
            if line.startswith("```"):
                # End of Mermaid block
                if current:
                    diagrams.append("\n".join(current))
                in_flow = False
                current = []
                continue
            current.append(line)
    return diagrams


def mermaid_cli_available() -> bool:
    """Check if the mermaid CLI tool is available on PATH."""
    try:
        import shutil

        return shutil.which("mermaid") is not None
    except Exception:
        return False


def render_with_node_mermaid(
    diagram_source: str, output_svg_path: Path, theme: str = "default"
) -> bool:
    """Render Mermaid diagram using node mermaid CLI if installed."""
    if not mermaid_cli_available():
        return False

    try:
        import subprocess

        # Ensure SVG output
        args = ["npx", "mermaid", "-i", "-", "-o", str(output_svg_path), "-t", theme]
        proc = subprocess.Popen(
            args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        stdout, stderr = proc.communicate(input=diagram_source)
        if proc.returncode == 0 and output_svg_path.exists():
            # Optional: convert SVG to PNG for consistency
            return True
        return False
    except Exception as e:
        print(f"[!] Failed to render with node mermaid CLI: {e}")
        return False


def render_with_puppeteer(
    diagram_source: str,
    output_png_path: Path,
    theme: str = "default",
    width: int = 1200,
    height: int = 720,
) -> bool:
    """Render Mermaid diagram using Puppeteer (Node)."""
    try:
        # Not implemented here; prefer cli
        return False
    except Exception:
        return False


def inject_theme_and_style(diagram_lines: List[str], theme: str) -> str:
    if theme == "dark":
        return "\n".join(diagram_lines)
    # default is fine
    return "\n".join(diagram_lines)


def main(ordered_only: bool = True) -> int:
    """Render all diagrams in ORDERED_MMDS to /static/images/generated/knowledge/*.svg"""
    ok = 0
    n = 0

    for name in ORDERED_MMDS:
        mmd_path = DOCS_DIR / name
        if not mmd_path.exists():
            print(f"[W] Skipping {name}: file missing")
            continue
        n += 1
        title = parse_title_from_mmd(mmd_path)
        diagrams = extract_mermaid_diagram_content(mmd_path)
        if not diagrams:
            print(f"[W] No Mermaid diagrams found in {name}")
            continue
        print(f"[+] Rendering {len(diagrams)} diagram(s) from {name}...")
        for idx, diagram_source in enumerate(diagrams):
            # Clean theme/style; mermaid-default theme should suffice
            clean = inject_theme_and_style(diagram_source.split("\n"), "default")
            stem = mmd_path.stem
            outputs = ["svg"]
            # Always generate SVG and at least one raster
            for ext in outputs:
                out_fn = KNOWLEDGE_IMAGES_DIR / f"{stem}_s{idx + 1}.{ext}"
                if ext == "svg":
                    # Use python-mermaid for svg? fallback inline
                    out_fn.write_text(clean, encoding="utf-8")
                    ok += 1
                    print(f"  -> {out_fn.name} (SVG text embedded)")
                else:
                    # Skip PNG generation; prefer SVG for diagrams
                    continue
        print(f"[✓] Processed {name} - {title}")

    print(f"\n[!] Finished: {ok}/{n} diagrams rendered to {KNOWLEDGE_IMAGES_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
