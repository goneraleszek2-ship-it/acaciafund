"""Generate the System Diagrams knowledge page with Mermaid + ASCII representations."""
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
    subgraphs = []
    current_subgraph = None

    for line in lines:
        line = line.strip()
        if not line or line.startswith('title:') or line.startswith('flowchart') or line.startswith('---'):
            continue
        if line.startswith('subgraph '):
            name = line.split('"')[1] if '"' in line else line.split('subgraph ')[1].strip()
            current_subgraph = name
            continue
        if line.startswith('end'):
            current_subgraph = None
            continue
        if line.startswith('style'):
            continue

        # Match node definitions like U[Browser / Visitor]
        node_match = re.match(r'(\w+)\[(.+?)\]', line)
        if node_match:
            nodes[node_match.group(1)] = node_match.group(2)

        # Match edges like U --> CF
        edge_match = re.match(r'(\w+)\s*-+>\s*(\w+)', line)
        if edge_match:
            edges.append((edge_match.group(1), edge_match.group(2)))

    # Build ASCII
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


# Read the .mmd files
docs_dir = os.path.join(os.path.dirname(__file__), '..', 'docs')
mmd_files = sorted([f for f in os.listdir(docs_dir) if f.endswith('.mmd')])

page_sections = []
page_sections.append("""<h2>System Diagrams</h2>
<p>This page provides comprehensive architectural, pipeline, and flow diagrams for the AcaciaFund DataOps platform. Each diagram is available as a Mermaid definition (rendered below with JavaScript) and as a static ASCII representation (always visible). The source <code>.mmd</code> files are available in the <a href="https://github.com/goneraleszek2-ship-it/acaciafund/tree/main/docs">GitHub docs/ directory</a>.</p>

<p>New for June 2026: diagrams for the <strong>Source Framework</strong> (registry, 5 fetcher types, health tracking), <strong>Admin Panel</strong> (Flask routes, API, templates), and <strong>RSS Ingestion Pipeline</strong> (8 feed sources → classification → build).</p>

<p>Mermaid diagrams render client-side when JavaScript is enabled. The page is fully readable without JS via the ASCII fallback representations.</p>""")

for idx, mmd_file in enumerate(mmd_files, 1):
    filepath = os.path.join(docs_dir, mmd_file)
    with open(filepath) as f:
        content = f.read()

    title_match = re.search(r'title:\s*(.+?)$', content, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else mmd_file.replace('.mmd', '').replace('_', ' ').title()

    # Remove the title line and frontmatter for the Mermaid block
    mermaid_content = content
    mermaid_content = re.sub(r'^title:.*$', '', mermaid_content, flags=re.MULTILINE)
    mermaid_content = re.sub(r'^---.*$', '', mermaid_content, flags=re.MULTILINE)
    mermaid_content = mermaid_content.strip()

    # Generate ASCII representation
    ascii_art = mmd_to_ascii(content)

    slug_name = mmd_file.replace('.mmd', '')
    section_id = f'diagram-{slug_name}'

    section = f"""
<h2 id="{section_id}" style="margin-top:2rem">{idx}. {title}</h2>
<p><a href="https://github.com/goneraleszek2-ship-it/acaciafund/blob/main/docs/{mmd_file}" target="_blank" rel="noopener">View source <code>{mmd_file}</code> on GitHub ↗</a></p>

<div class="mermaid" style="background:var(--color-bg);padding:16px;border-radius:8px;overflow-x:auto">
{mermaid_content}
</div>

<pre style="background:var(--color-bg);padding:16px;border-radius:8px;overflow-x:auto;font-size:0.85em;line-height:1.4">
{ascii_art}
</pre>"""
    page_sections.append(section)

# Build the reference table rows from DESCRIPTIONS dict
# table_rows now contains just the data, not full <tr> tags
table_rows_data = []
for mmd_file in mmd_files:
    slug = mmd_file.replace('.mmd', '')
    info = DESCRIPTIONS.get(slug, (slug.replace('_', ' ').title(), "", ""))
    table_rows_data.append((mmd_file, info[1], info[2]))

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

# Add Mermaid init script
mermaid_script = """
<script src="/static/js/mermaid.min.js" defer></script>
<script defer>
document.addEventListener('DOMContentLoaded', function(){
  if (typeof mermaid !== 'undefined') {
    mermaid.initialize({
      startOnLoad: true,
      theme: 'dark',
      themeVariables: {
        background: '#0f172a',
        primaryColor: '#1e3a5f',
        secondaryColor: '#2d5a8e',
        primaryBorderColor: '#d97706',
        secondaryBorderColor: '#64748b',
        lineColor: '#64748b',
        textColor: '#e2e8f0',
        mainBkg: '#1e293b',
        nodeBorder: '#475569',
        clusterBkg: '#0f172a',
        clusterBorder: '#334155'
      }
    });
  }
});
</script>
<noscript>
  <p style="color:var(--color-text-muted);font-size:0.9em">Mermaid interactive diagrams require JavaScript. The ASCII representations above provide the same information.</p>
</noscript>"""

page_html = '\n'.join(page_sections) + '\n' + mermaid_script

# Output to stdout for use in enrichment
print(page_html)
