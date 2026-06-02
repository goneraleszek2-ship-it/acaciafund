#!/usr/bin/env python3
"""
Orchestrator for AcaciaFund: converts Markdown content to structured registry.json.
"""
import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import markdown
from pydantic import ValidationError

from schemas import AcaciaContent, PipelineStage, MCPIntegration, PlannedFeature, RegistryData

# Configuration
CONTENT_ROOT = Path("content")
REGISTRY_PATH = Path("registry.json")

# Static data for the site (can be extended or loaded from files)
PIPELINE_STAGES = [
    PipelineStage(id="bronze", title="Bronze Layer", description="Raw data ingestion from external sources."),
    PipelineStage(id="silver", title="Silver Layer", description="Cleaned and validated data ready for analysis."),
    PipelineStage(id="gold", title="Gold Layer", description="Actionable insights and final products."),
]

MCP_INTEGRATIONS = [
    MCPIntegration(name="GitHub", status="active", description="Version control and collaboration."),
    MCPIntegration(name="Hugging Face", status="active", description="Access to AI models and datasets."),
    MCPIntegration(name="Weaviate", status="planned", description="Vector storage for semantic search."),
]

PLANNED_FEATURES = [
    PlannedFeature(name="AI Research Assistant", description="An AI agent to help navigate and synthesize research."),
    PlannedFeature(name="Real-time Alerts", description="Get notified when new signals are detected."),
]

def parse_markdown_file(file_path: Path) -> dict:
    """Parse a Markdown file with frontmatter and return metadata and body."""
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return {}

    # Split frontmatter and body
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) < 3:
            return {}
        frontmatter_text = parts[1]
        body = parts[2].strip()
    else:
        # No frontmatter
        frontmatter_text = ""
        body = content

    # Parse frontmatter (simple key: value)
    metadata = {}
    for line in frontmatter_text.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            metadata[key.strip()] = value.strip()

    # Convert body to HTML
    try:
        html = markdown.markdown(body, extensions=['fenced_code', 'tables'])
    except Exception as e:
        print(f"Error converting Markdown to HTML in {file_path}: {e}")
        html = ""

    return {
        "raw_content": content,
        "metadata": metadata,
        "body": body,
        "body_html": html,
    }

def walk_content_directory(root: Path) -> List[dict]:
    """Walk the content directory and parse all Markdown files."""
    records = []
    for md_file in root.rglob("*.md"):
        # Skip files that are in directories starting with _ or .
        if any(part.startswith("_") or part.startswith(".") for part in md_file.parts):
            continue
        parsed = parse_markdown_file(md_file)
        if not parsed:
            continue
        records.append((md_file, parsed))
    return records

def create_acacia_content(md_file: Path, parsed: dict) -> Optional[AcaciaContent]:
    """Create an AcaciaContent instance from parsed Markdown file."""
    metadata = parsed["metadata"]
    # Determine slug and language from the file path
    # We assume the structure: content/<language>/<section>/<slug>.md
    # or content/<section>/<slug>.md for the root language (default to 'en')
    relative_path = md_file.relative_to(CONTENT_ROOT)
    parts = list(relative_path.parts)
    # Remove the file name (without extension)
    slug_parts = parts[:-1]  # directory path
    file_name = parts[-1]   # e.g., "index.md" or "2026-06-01-aml.md"
    slug_name = file_name[:-3] if file_name.endswith(".md") else file_name

    # Determine language: if the first part is a two-letter code, use it, else default to 'en'
    language = "en"
    if len(parts) >= 2 and len(parts[0]) == 2 and parts[0].isalpha() and parts[0].islower():
        language = parts[0]
        # The slug path starts from the second part
        slug_path_parts = parts[1:-1] + [slug_name]
    else:
        slug_path_parts = parts[:-1] + [slug_name]

    # Build the slug: join the path parts with slashes, and append the slug name if not index
    # For index.md, we want the directory path as the slug (e.g., "about/" -> we'll use "about" as slug)
    # But note: we want to avoid double slashes and trailing slashes in the slug? We'll keep it clean.
    if slug_name == "index":
        # For index files, the slug is the directory path (without trailing slash)
        slug = "/".join(slug_path_parts[:-1]) if len(slug_path_parts) > 1 else ""
        # If the slug is empty, it's the homepage
        if slug == "":
            slug = "index"
    else:
        # For non-index files, the slug is the full path including the file name (without extension)
        slug = "/".join(slug_path_parts)

    # Ensure slug is not empty
    if not slug:
        slug = "index"

    # Determine category from the first directory after language (if present) or from frontmatter
    category = metadata.get("category", "")
    if not category and len(slug_path_parts) >= 1:
        # Try to get the first directory after language as category
        # For example: content/en/blog/2026-06-01-aml/index.md -> category = "blog"
        # But note: we have a separate category for blog, course, etc.
        # We'll use the first directory in the slug_path_parts (if any) as category, but we have to skip the language part if present.
        # Actually, we already removed the language part in slug_path_parts when language is detected.
        # So slug_path_parts is already relative to the language directory.
        if slug_path_parts:
            category = slug_path_parts[0]
    # If still not set, default to "post"
    if not category:
        category = "post"

    # Extract tags from metadata (if present) or from frontmatter tags
    tags = metadata.get("tags", [])
    if isinstance(tags, str):
        tags = [tag.strip() for tag in tags.split(",")]
    elif not isinstance(tags, list):
        tags = []

    # Prepare the data for AcaciaContent
    content_data = {
        "slug": slug,
        "language": language,
        "title": metadata.get("title", ""),
        "body_html": parsed["body_html"],
        "category": category,
        "tags": tags,
        "created_at": datetime.utcnow(),  # We'll use the file's modified time or the date from frontmatter if available
        "updated_at": None,
    }

    # Try to parse the date from metadata
    date_str = metadata.get("date")
    if date_str:
        try:
            # Expected format: YYYY-MM-DD
            content_data["created_at"] = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            pass  # Keep the default

    try:
        return AcaciaContent(**content_data)
    except ValidationError as e:
        print(f"Validation error for {md_file}: {e}")
        return None

def main():
    """Main function to run the orchestrator."""
    print("Starting AcaciaFund orchestrator...")
    records = walk_content_directory(CONTENT_ROOT)
    print(f"Found {len(records)} Markdown files.")

    content_list = []
    for md_file, parsed in records:
        content = create_acacia_content(md_file, parsed)
        if content:
            content_list.append(content)
        else:
            print(f"Skipping {md_file} due to validation errors.")

    print(f"Successfully processed {len(content_list)} content items.")

    # Build the registry
    registry = RegistryData(
        last_run=datetime.utcnow(),
        content=content_list,
        pipeline_stages=PIPELINE_STAGES,
        mcp_integrations=MCP_INTEGRATIONS,
        planned_features=PLANNED_FEATURES,
    )

    # Write to registry.json
    try:
        with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
            json.dump(registry.dict(), f, indent=2, default=str)
        print(f"Registry written to {REGISTRY_PATH}")
    except Exception as e:
        print(f"Error writing registry: {e}")
        return 1

    return 0

if __name__ == "__main__":
    exit(main())