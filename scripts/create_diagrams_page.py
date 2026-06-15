#!/usr/bin/env python3
"""Generate the System Diagrams knowledge page with PlantUML."""
import json
import re
import os

DESCRIPTIONS = {
    "system_architecture": ("System Architecture", "End-to-end system: user → CDN → build pipeline → 236 pages output", "Flowchart"),
    "dataops_pipeline": ("DataOps Pipeline — 8 Stages", "8-stage pipeline: ingest → validate → transform → catalog → visualize → render → serve → observe", "Flowchart"),
    "module_interconnections": ("Module Interconnections", "UML class diagram: config → validates → reads → invokes → renders", "Class Diagram"),
    "content_model": ("Content Data Model", "Content data model: RegistryData → ContentItem → BloomQuestion + Flashcard", "Class Diagram"),
    "build_sequence": ("Build Process — Sequence Diagram", "Build sequence: git push → CF Pages → generator → dist → deploy", "Sequence Diagram"),
    "user_journey": ("User Journey — Site Navigation", "User navigation: Home → Research/Learn/Knowledge → Article/Lesson/Page", "Flowchart"),
    "source_ingestion": ("Source Ingestion & Content Flow", "Source ingestion: APIs → seed_articles.py → NLP enrichment → registry.json", "Flowchart"),
    "pillar_taxonomy": ("Pillar Taxonomy — Content Classification", "Mindmap of 3 pillars × 6-7 topics + cross-cutting: AML/Markets/Science/DataOps", "Mindmap"),
    "pipeline_quality": ("Pipeline Quality Gates & Observability", "Quality gates: Pydantic validation → SQI → domain % → flags + observability", "Flowchart"),
    "search_index": ("Search Index Architecture", "Search: build-time JSON generation → client-side fetch/filter", "Flowchart"),
    "source_framework": ("Source Framework — Registry, Fetchers & Health", "Source registry architecture: etc/sources.toml → BaseFetcher ABC → 5 fetcher types → health + DLQ → admin dashboard", "Flowchart"),
    "admin_panel": ("Admin Panel — Routes, API & Templates", "Flask admin panel: 11 page routes + 7 API endpoints + 12 Jinja2 templates + 4 data sources", "Flowchart"),
    "rss_ingestion": ("RSS Ingestion Pipeline", "RSS ingestion flow: 8 feed sources → RSSFetcher → health/DLQ → ingest.py → pillar classification → build → pages", "Flowchart"),
}

def mmd_to_ascii(mmd_content):
    """Convert simple Mermaid flowchart TD to ASCII representation."""
    lines = mmd_content.strip().split('\n')
    nodes = {}
    edges = []

    for line in lines:
        line = line.strip()
        if not line or line.startswith('title:') or line.startswith('flowchart') or line.startswith('---'):
            continue
        if line.startswith('subgraph '):
            continue
        if line.startswith('end'):
            continue
        if line.startswith('style'):
            continue

        node_match = re.match(r'(\w+)\[(.+?)\]', line)
        if node_match:
            nodes[node_match.group(1)] = node_match.group(2)

        edge_match = re.match(r'(\w+)\s*-+>\s*(\w+)', line)
        if edge_match:
            edges.append((edge_match.group(1), edge_match.group(2)))

    ascii = []
    ascii.append('┌──────────────────────────────────────┐')
    ascii.append('│          SYSTEM DIAGRAM              │')
    ascii.append('├──────────────────────────────────────┤')
    for nid, label in nodes.items():
        label_clean = label.replace('<br/>', ' / ')[:40]
        ascii.append(f'│ [{nid}] {label_clean}')
    ascii.append('├──────────────────────────────────────┤')
    ascii.append('│ FLOW:                                │')
    for src, dst in edges:
        src_name = nodes.get(src, src)[:20]
        dst_name = nodes.get(dst, dst)[:20]
        ascii.append(f'│ {src_name} → {dst_name}')
    ascii.append('└──────────────────────────────────────┘')
    return '\n'.join(ascii)


# Read the .puml files
docs_dir = os.path.join(os.path.dirname(__file__), '..', 'docs')
puml_files = sorted([f for f in os.listdir(docs_dir) if f.endswith('.puml')])

page_sections = []
page_sections.append("""<h2>System Diagrams</h2>
<p>This page provides comprehensive architectural, pipeline, and flow diagrams for the AcaciaFund DataOps platform. Each diagram is rendered using PlantUML with a simple, clear visual style.</p>

<p>New for June 2026: diagrams for the <strong>Source Framework</strong> (registry, 5 fetcher types, health tracking), <strong>Admin Panel</strong> (Flask routes, API, templates), and <strong>RSS Ingestion Pipeline</strong> (8 feed sources → classification → build).</p>""")

for idx, puml_file in enumerate(puml_files, 1):
    filepath = os.path.join(docs_dir, puml_file)
    with open(filepath) as f:
        content = f.read()

    # Extract title from PlantUML file
    title_match = re.search(r'^title:\s*(.+?)$', content, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else puml_file.replace('.puml', '').replace('_', ' ').title()

    # Remove PlantUML markers
    puml_content = content
    puml_content = re.sub(r'^@startuml', '', puml_content, flags=re.MULTILINE)
    puml_content = re.sub(r'^@enduml', '', puml_content, flags=re.MULTILINE)
    puml_content = re.sub(r'^title:.*$', '', puml_content, flags=re.MULTILINE)
    puml_content = puml_content.strip()

    # Generate ASCII representation from original .mmd file
    mmd_filepath = os.path.join(docs_dir, puml_file.replace('.puml', '.mmd'))
    if os.path.exists(mmd_filepath):
        with open(mmd_filepath) as f:
            mmd_content = f.read()
        ascii_art = mmd_to_ascii(mmd_content)
    else:
        ascii_art = mmd_to_ascii(content)

    slug_name = puml_file.replace('.puml', '')
    section_id = f'diagram-{slug_name}'

    section = f"""
<h2 id="{section_id}" style="margin-top:2rem">{idx}. {title}</h2>
<p><a href="https://github.com/goneraleszek2-ship-it/acaciafund/blob/main/docs/{puml_file}" target="_blank" rel="noopener">View source <code>{puml_file}</code> on GitHub ↗</a></p>

<div class="plantuml" style="background:var(--color-bg);padding:16px;border-radius:8px;overflow-x:auto">
{puml_content}
</div>"""
    page_sections.append(section)

# Build the reference table
table_rows_data = []
for puml_file in puml_files:
    slug = puml_file.replace('.puml', '')
    info = DESCRIPTIONS.get(slug, (slug.replace('_', ' ').title(), "", ""))
    table_rows_data.append((puml_file, info[1], info[2]))

table_html = f"""<h2>Diagram Reference</h2>
<table style="width:100%;border-collapse:collapse;font-size:0.9em">
<thead>
<tr style="background:var(--color-bg)"><th style="padding:8px;border:1px solid var(--color-border);text-align:left">#</th><th style="padding:8px;border:1px solid var(--color-border);text-align:left">File</th><th style="padding:8px;border:1px solid var(--color-border);text-align:left">Description</th><th style="padding:8px;border:1px solid var(--color-border);text-align:left">Type</th></tr>
</thead>
<tbody>
{chr(10).join(f'<tr><td style="padding:8px;border:1px solid var(--color-border)">{i}</td><td style="padding:8px;border:1px solid var(--color-border)"><code>{file}</code></td><td style="padding:8px;border:1px solid var(--color-border)">{desc}</td><td style="padding:8px;border:1px solid var(--color-border)">{typ}</td></tr>' for i, (file, desc, typ) in enumerate(table_rows_data, 1))}
</tbody>
</table>"""

page_sections.append(table_html)

# Add PlantUML init script
plantuml_script = """
<script src="/static/js/plantuml/plantuml.min.js" defer></script>
<script defer>
document.addEventListener('DOMContentLoaded', function(){
  if (typeof plantuml !== 'undefined') {
    console.log('PlantUML.js loaded successfully');
  } else {
    console.error('PlantUML.js failed to load');
  }
});
</script>"""

page_html = '\n'.join(page_sections) + '\n' + plantuml_script

print(page_html)
