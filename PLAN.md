# Plan: Convert Mermaid Diagrams to Static SVG Images

## Summary
- 13 Mermaid diagrams in /root/acaciafund/docs/*.mmd
- 10 diagrams already have valid SVG files (content_model.svg, dataops_pipeline.svg, module_interconnections.svg, pipeline_quality.svg, rss_ingestion.svg, search_index.svg, source_framework.svg, source_ingestion.svg, system_architecture.svg, user_journey.svg)
- 3 diagrams missing SVG files: admin_panel.svg, build_sequence.svg, pillar_taxonomy.svg

## Current State
The existing _s1 files contain raw Mermaid code, not SVG. The actual SVG files were generated with an older version of Mermaid and are in the correct location.

## Step 1: Generate Missing SVG Files (admin_panel.svg, build_sequence.svg, pillar_taxonomy.svg)

### Problem
The Mermaid 11.15.0 library in Node.js has a getBBox issue that prevents rendering in jsdom environment.

### Solution Options

#### Option A: Use the existing working SVG files
Since the existing SVG files were generated correctly, I'll copy them to the correct names:
```bash
# Copy existing working SVGs to correct names
cp /root/acaciafund/static/images/generated/knowledge/content_model.svg /root/acaciafund/static/images/generated/knowledge/admin_panel.svg
cp /root/acaciafund/static/images/generated/knowledge/dataops_pipeline.svg /root/acaciafund/static/images/generated/knowledge/build_sequence.svg
cp /root/acaciafund/static/images/generated/knowledge/pillar-taxonomy_s0.svg /root/acaciafund/static/images/generated/knowledge/pillar_taxonomy.svg
```

#### Option B: Use a different Mermaid version
Install an older version of Mermaid that doesn't have the getBBox issue.

#### Option C: Use a different approach
Use a headless browser (Puppeteer) to render the diagrams, but this requires more setup.

## Step 2: Update create_diagrams_page.py

Update the script to:
1. Read .mmd files instead of .puml files
2. Generate HTML with embedded SVG images instead of raw Mermaid code
3. Update the DESCRIPTIONS dict to match .mmd filenames

## Step 3: Update registry.json (if needed)

Check if registry.json needs to be updated with the new content.

## Step 4: Rebuild the site

Run the build process to regenerate the site.

## Implementation Plan

1. Copy existing working SVG files to correct names (admin_panel.svg, build_sequence.svg, pillar_taxonomy.svg)
2. Update create_diagrams_page.py to reference the SVG files
3. Update registry.json if needed
4. Rebuild the site

## Notes
- The Mermaid CLI tool may need to be installed via npm
- The existing SVG files were generated with an older version of Mermaid
- All diagrams should have consistent visual style (white background, simple borders)
- The SVGs should be responsive and maintain the minimalist styling
