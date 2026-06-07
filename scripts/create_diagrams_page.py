"""Generate the System Diagrams knowledge page with Mermaid + ASCII representations."""
import json
import re

def mmd_to_ascii(mmd_content):
    """Convert simple Mermaid flowchart TD to ASCII representation."""
    lines = mmd_content.strip().split('\n')
    # Filter out non-flowchart lines
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
        label_clean = label.replace('<br/>', ' / ')
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
import os
docs_dir = '/root/acaciafund/docs'
mmd_files = [f for f in os.listdir(docs_dir) if f.endswith('.mmd')]

page_sections = []
page_sections.append("""<h2>System Diagrams</h2>
<p>This page provides comprehensive architectural, pipeline, and flow diagrams for the AcaciaFund DataOps platform. Each diagram is available as a Mermaid definition (rendered below with JavaScript) and as a static ASCII representation (always visible). The source <code>.mmd</code> files are available in the <a href="https://github.com/goneraleszek2-ship-it/acaciafund/tree/main/docs">GitHub docs/ directory</a>.</p>

<p>Mermaid diagrams render client-side when JavaScript is enabled. The page is fully readable without JS via the ASCII fallback representations.</p>""")

for mmd_file in sorted(mmd_files):
    with open(os.path.join(docs_dir, mmd_file)) as f:
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
<h2 id="{section_id}">{title}</h2>
<p><a href="https://github.com/goneraleszek2-ship-it/acaciafund/blob/main/docs/{mmd_file}" target="_blank" rel="noopener">View source <code>{mmd_file}</code> on GitHub ↗</a></p>

<h3>Mermaid Diagram</h3>
<div class="mermaid" style="background:var(--color-bg);padding:16px;border-radius:8px;overflow-x:auto">
{mermaid_content}
</div>

<h3>ASCII Representation</h3>
<pre style="background:var(--color-bg);padding:16px;border-radius:8px;overflow-x:auto;font-size:0.85em;line-height:1.4">
{ascii_art}
</pre>"""
    page_sections.append(section)

# Add Mermaid init script
mermaid_script = """
<h2>About These Diagrams</h2>
<table style="width:100%;border-collapse:collapse;font-size:0.9em">
<tr style="background:var(--color-bg)"><th style="padding:8px;border:1px solid var(--color-border);text-align:left">File</th><th style="padding:8px;border:1px solid var(--color-border);text-align:left">Description</th><th style="padding:8px;border:1px solid var(--color-border);text-align:left">Type</th></tr>
<tr><td style="padding:8px;border:1px solid var(--color-border)"><code>system_architecture.mmd</code></td><td style="padding:8px;border:1px solid var(--color-border)">End-to-end system from user browser through CDN to build pipeline and generated output</td><td style="padding:8px;border:1px solid var(--color-border)">Flowchart</td></tr>
<tr><td style="padding:8px;border:1px solid var(--color-border)"><code>dataops_pipeline.mmd</code></td><td style="padding:8px;border:1px solid var(--color-border)">8-stage DataOps pipeline: ingestion → validation → transformation → catalog → visualization → rendering → serving → observability</td><td style="padding:8px;border:1px solid var(--color-border)">Flowchart</td></tr>
<tr><td style="padding:8px;border:1px solid var(--color-border)"><code>module_interconnections.mmd</code></td><td style="padding:8px;border:1px solid var(--color-border)">UML class diagram showing Python module relationships: config.py, schemas.py, registry.json, generator.py, visuals.py, templates</td><td style="padding:8px;border:1px solid var(--color-border)">Class Diagram</td></tr>
<tr><td style="padding:8px;border:1px solid var(--color-border)"><code>content_model.mmd</code></td><td style="padding:8px;border:1px solid var(--color-border)">UML class diagram of the content data model: RegistryData → ContentItem → BloomQuestion + Flashcard</td><td style="padding:8px;border:1px solid var(--color-border)">Class Diagram</td></tr>
<tr><td style="padding:8px;border:1px solid var(--color-border)"><code>build_sequence.mmd</code></td><td style="padding:8px;border:1px solid var(--color-border)">Sequence diagram of the build process: git push → Cloudflare Pages → generator.py → registry → visuals → templates → dist → deploy</td><td style="padding:8px;border:1px solid var(--color-border)">Sequence Diagram</td></tr>
<tr><td style="padding:8px;border:1px solid var(--color-border)"><code>user_journey.mmd</code></td><td style="padding:8px;border:1px solid var(--color-border)">User navigation flow through the site: Home → Research/Learn/Knowledge → Articles/Lessons with flashcards and quizzes</td><td style="padding:8px;border:1px solid var(--color-border)">Flowchart</td></tr>
<tr><td style="padding:8px;border:1px solid var(--color-border)"><code>source_ingestion.mmd</code></td><td style="padding:8px;border:1px solid var(--color-border)">External source ingestion: HackerNews/arXiv/PubMed APIs → seed_articles.py → NLP enrichment → registry.json</td><td style="padding:8px;border:1px solid var(--color-border)">Flowchart</td></tr>
<tr><td style="padding:8px;border:1px solid var(--color-border)"><code>pillar_taxonomy.mmd</code></td><td style="padding:8px;border:1px solid var(--color-border)">Mindmap of content pillar taxonomy: AML, Markets, Science (3 pillars × 6-7 topics each) plus cross-cutting categories</td><td style="padding:8px;border:1px solid var(--color-border)">Mindmap</td></tr>
<tr><td style="padding:8px;border:1px solid var(--color-border)"><code>pipeline_quality.mmd</code></td><td style="padding:8px;border:1px solid var(--color-border)">Quality gates (Pydantic validation, SQI thresholds, domain sanitization) and observability metrics</td><td style="padding:8px;border:1px solid var(--color-border)">Flowchart</td></tr>
<tr><td style="padding:8px;border:1px solid var(--color-border)"><code>search_index.mmd</code></td><td style="padding:8px;border:1px solid var(--color-border)">Search index architecture: build-time JSON generation → client-side filtering with JavaScript</td><td style="padding:8px;border:1px solid var(--color-border)">Flowchart</td></tr>
</table>

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
    // Hide ASCII blocks when Mermaid renders successfully
    var asciiBlocks = document.querySelectorAll('h3:contains(\"ASCII\")');
    asciiBlocks.forEach(function(el) { el.style.display = 'none'; });
  }
});
</script>
<noscript>
  <p style="color:var(--color-text-muted);font-size:0.9em">Mermaid interactive diagrams require JavaScript. The ASCII representations above provide the same information.</p>
</noscript>"""

page_html = '\n'.join(page_sections) + '\n' + mermaid_script

# Output to stdout for use in enrichment
print(page_html)
