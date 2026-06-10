#!/usr/bin/env python3.13
"""
Knowledge base overhaul: category taxonomy, expanded content, new entries, slug migration, thumbnails.
"""
import json
from datetime import datetime, timezone
from pathlib import Path

REGISTRY_PATH = Path("registry.json")

KNOWLEDGE_CATEGORIES = {
    "knowledge/about": "platform",
    "knowledge/contact": "platform",
    "knowledge/faq": "platform",
    "knowledge/research-methodology": "guide",
    "knowledge/pillar-taxonomy": "guide",
    "knowledge/glossary": "reference",
    "knowledge/dataops-glossary": "reference",
    "knowledge/open-source-tools": "reference",
    "knowledge/system-architecture": "architecture",
    "knowledge/changelog": "platform",
}

CATEGORY_META = {
    "platform": {"label": "Platform", "icon": "gear", "order": 0, "description": "About AcaciaFund — mission, team, contact, and site operations."},
    "guide": {"label": "Guides", "icon": "compass", "order": 1, "description": "Methodology, taxonomy, and how-to guides for using the platform."},
    "reference": {"label": "Reference", "icon": "book", "order": 2, "description": "Glossaries, tool landscapes, and technical terminology across all pillars."},
    "architecture": {"label": "Architecture", "icon": "network", "order": 3, "description": "System design, pipeline architecture, and DataOps implementation details."},
}

EXPANDED_BODIES = {
    "knowledge/about": """<h2>About AcaciaFund</h2>
<p>AcaciaFund is an automated research synthesis platform that applies <strong>DataOps principles</strong> to the content lifecycle: ingesting from HackerNews and arXiv, classifying via Bloom taxonomy, scoring with the Signal Quality Index (SQI), and serving as a static data product.</p>

<h3>Mission</h3>
<p>To make high-quality, multi-perspective research synthesis accessible — bridging anti-money laundering (AML), financial markets, and data engineering infrastructure through automated classification and transparent quality metrics.</p>

<h3>How It Works</h3>
<ul>
<li><strong>Ingestion:</strong> Daily stories from HackerNews, academic preprints from arXiv, and biomedical research from PubMed are collected and analyzed.</li>
<li><strong>Classification:</strong> Each article is classified using Bloom taxonomy (remember → create) to determine its cognitive depth and learning value.</li>
<li><strong>Scoring:</strong> The Signal Quality Index (SQI) combines source authority, freshness, consensus, and relevance into a composable [0,1] metric.</li>
<li><strong>Serving:</strong> A deterministic Python-native generator (Jinja2 + Pydantic) transforms structured data into static HTML, deployed via Cloudflare Pages.</li>
</ul>

<h3>Content Taxonomy</h3>
<ul>
<li><strong>Research:</strong> Bloom-classified articles with SQI, signals, flashcards, and source breakdowns. Organized by pillar (AML, Markets, Data Engineering).</li>
<li><strong>Learn:</strong> Structured lessons with flashcards, code examples, and practical exercises for self-directed study.</li>
<li><strong>Knowledge:</strong> Reference documentation — glossaries, architecture, tools landscape, methodology guides, and platform information.</li>
</ul>

<h3>Tech Stack</h3>
<ul>
<li><strong>Generator:</strong> Python 3.13, Pydantic, Jinja2, Markdown2</li>
<li><strong>Styling:</strong> Tailwind CSS 3.4.19 (self-hosted, 28KB), custom CSS with CSS variables for dark mode</li>
<li><strong>Fonts:</strong> Inter (Regular/SemiBold/Bold — self-hosted WOFF2, zero external requests)</li>
<li><strong>Hosting:</strong> Cloudflare Pages (static) + Railway (FastAPI service for progress tracking)</li>
<li><strong>CI/CD:</strong> GitHub → Cloudflare Pages auto-deploy from <code>main</code></li>
</ul>

<p><em>Last updated: 2026-06-08</em></p>""",

    "knowledge/contact": """<h2>Contact Us</h2>
<p>Get in touch with the AcaciaFund team. We welcome questions, feedback, research collaborations, and bug reports.</p>

<h3>GitHub</h3>
<p>The primary channel for issues, feature requests, and contributions is the <a href="https://github.com/goneraleszek2-ship-it/acaciafund">AcaciaFund GitHub repository</a>. Please open an issue for bug reports or feature suggestions.</p>

<h3>Research Collaboration</h3>
<p>Interested in collaborating on research synthesis, Bloom taxonomy classification, or DataOps pipeline design? Reach out via GitHub discussions or open an issue with the "collaboration" label.</p>

<h3>Reporting Issues</h3>
<p>If you find a bug, broken link, or inaccuracy in any article, please <a href="https://github.com/goneraleszek2-ship-it/acaciafund/issues">file an issue</a> with the relevant article slug and description of the problem.</p>

<h3>Content Suggestions</h3>
<p>To suggest a topic for research synthesis or a new knowledge base entry, open a GitHub issue with the "content-suggestion" label and include relevant source links.</p>

<p><em>Last updated: 2026-06-08</em></p>""",

    "knowledge/faq": """<h2>Frequently Asked Questions</h2>

<h3>What is the Signal Quality Index (SQI)?</h3>
<p>SQI is a composite metric that evaluates the quality of synthesized content across four dimensions: <strong>source authority</strong> (is the source reputable?), <strong>freshness</strong> (how recent is the data?), <strong>consensus</strong> (do multiple sources agree?), and <strong>relevance</strong> (how directly does it relate to the pillar?). SQI is normalized to [0, 1] and displayed on every research article.</p>

<h3>How does Bloom taxonomy classification work?</h3>
<p>Each article is classified across six cognitive levels: <strong>remember</strong>, <strong>understand</strong>, <strong>apply</strong>, <strong>analyze</strong>, <strong>evaluate</strong>, and <strong>create</strong>. Questions and flashcards are generated at each level to support different learning objectives. A single article may span multiple levels depending on its content depth.</p>

<h3>What are the three pillars?</h3>
<p><strong>AML</strong> (Anti-Money Laundering) covers financial crime, compliance, regulation, and risk management. <strong>Markets</strong> covers semiconductors, supply chains, AI industry, and manufacturing. <strong>Data Engineering</strong> covers data pipelines, orchestration, quality engineering, streaming, storage, and analytics infrastructure.</p>

<h3>How are sources selected?</h3>
<p>Sources are drawn from two primary feeds: <strong>HackerNews</strong> (technology and current events) and <strong>arXiv</strong> (academic preprints across computer science, statistics, and finance). Articles are filtered by relevance to the three pillars and scored using the SQI framework.</p>

<h3>How often is content updated?</h3>
<p>Research articles are published as significant stories emerge. The pipeline processes HackerNews and arXiv feeds daily, but publication frequency depends on the volume of high-SQI signals. Historical articles are preserved with their original quality metrics.</p>

<h3>Can I reuse or cite AcaciaFund content?</h3>
<p>All content is licensed under MIT. You are free to reuse, adapt, and cite. We recommend citing by article slug and date, as content is version-controlled via Git. Each article has a canonical URL and JSON-LD structured data for citation purposes.</p>

<h3>How are thumbnails generated?</h3>
<p>Each research article gets a unique fractal tree SVG, generated using a seed-based L-system. The tree shape is deterministic (same title = same tree) and colored by pillar (amber for AML, green for Markets, indigo for Data Engineering). Additional color flooding, bloom, and mist effects create a distinctive visual identity per article.</p>

<h3>Does AcaciaFund use client-side JavaScript?</h3>
<p>JavaScript is used only for UI enhancements: dark mode toggling, mobile navigation, reading progress bar, table of contents highlighting, and focus mode. No JavaScript is required for reading content — the site is fully functional with JavaScript disabled.</p>

<p><em>Last updated: 2026-06-08</em></p>""",

    "knowledge/glossary": """<h2>Glossary — Research &amp; Financial Crime Terminology</h2>
<p>Key terms used across AcaciaFund's research, organized by pillar. This glossary is continuously expanded as new concepts are encountered.</p>

<h3>AML &amp; Compliance</h3>
<dl style="line-height:1.8">
<dt><strong>AML</strong></dt><dd>Anti-Money Laundering — regulatory framework to detect and prevent the conversion of illicit funds into legitimate assets.</dd>
<dt><strong>Beneficial Ownership</strong></dt><dd>The natural person who ultimately owns, controls, or benefits from a legal entity or arrangement. Central to modern AML frameworks.</dd>
<dt><strong>FinCEN</strong></dt><dd>Financial Crimes Enforcement Network — U.S. Treasury bureau responsible for collecting and analyzing financial intelligence.</dd>
<dt><strong>SAR</strong></dt><dd>Suspicious Activity Report — mandatory filing by financial institutions when suspicious transactions are detected.</dd>
<dt><strong>CDD / EDD</strong></dt><dd>Customer Due Diligence / Enhanced Due Diligence — risk-based customer vetting processes required by AML regulations.</dd>
<dt><strong>Transaction Monitoring</strong></dt><dd>Automated or manual screening of financial transactions for patterns indicative of money laundering or terrorist financing.</dd>
<dt><strong>OFAC</strong></dt><dd>Office of Foreign Assets Control — U.S. agency that administers and enforces economic sanctions.</dd>
<dt><strong>KYC</strong></dt><dd>Know Your Customer — the process of verifying client identity, assessing risk, and understanding financial behavior.</dd>
<dt><strong>Crypto Mixer</strong></dt><dd>A service that pools cryptocurrency from multiple users to obscure the trail of transactions, often targeted by regulators.</dd>
</dl>

<h3>Markets &amp; Industry</h3>
<dl style="line-height:1.8">
<dt><strong>Semiconductor Node</strong></dt><dd>Manufacturing process size for transistors (e.g., 2nm, 3nm). Smaller nodes enable more powerful, energy-efficient chips.</dd>
<dt><strong>Supply Chain Diversification</strong></dt><dd>Strategy of spreading production across multiple regions to reduce geopolitical and operational risk.</dd>
<dt><strong>Gigafactory</strong></dt><dd>Large-scale manufacturing facility, typically for batteries or electric vehicle components, producing at GWh-scale annual capacity.</dd>
<dt><strong>Venture Capital (VC)</strong></dt><dd>Private equity investment in early-stage, high-growth companies. Key funding source for deep-tech and quantum computing startups.</dd>
<dt><strong>ETL / ELT</strong></dt><dd>Extract-Transform-Load vs Extract-Load-Transform — data pipeline patterns for moving data from sources to analytics platforms.</dd>
<dt><strong>Feature Store</strong></dt><dd>Centralized repository for ML features enabling consistent computation, sharing, and serving across training and inference.</dd>
</dl>

<h3>Science &amp; Discovery</h3>
<dl style="line-height:1.8">
<dt><strong>CRISPR-Cas9</strong></dt><dd>Gene-editing technology enabling precise modification of DNA sequences. Applications include therapy for genetic disorders and agricultural improvement.</dd>
<dt><strong>AlphaFold</strong></dt><dd>DeepMind's AI system for predicting protein 3D structures from amino acid sequences, achieving near-experimental accuracy.</dd>
<dt><strong>JWST</strong></dt><dd>James Webb Space Telescope — infrared space observatory providing unprecedented views of exoplanet atmospheres, galaxy formation, and stellar evolution.</dd>
<dt><strong>BCI</strong></dt><dd>Brain-Computer Interface — direct communication pathway between brain electrical activity and external devices, enabling control of computers or prosthetics.</dd>
<dt><strong>Exoplanet Atmosphere</strong></dt><dd>The layer of gases surrounding planets outside our solar system, analyzed via transmission spectroscopy during transits.</dd>
<dt><strong>Superconductivity</strong></dt><dd>Zero electrical resistance in a material below a critical temperature. Room-temperature superconductivity remains an active research frontier.</dd>
</dl>
<p><em>Note: The Science glossary section is preserved for archival reference. Active coverage now focuses on Data Engineering.</em></p>

<h3>DataOps &amp; Engineering</h3>
<dl style="line-height:1.8">
<dt><strong>DataOps</strong></dt><dd>Automated methodology applying Agile, DevOps, and SPC principles to data pipeline lifecycle management.</dd>
<dt><strong>Pipeline Observability</strong></dt><dd>Real-time monitoring of data pipeline metrics — row counts, schema drift, latency, error rates — to detect and diagnose failures.</dd>
<dt><strong>Lakehouse</strong></dt><dd>Data architecture combining data lake flexibility with warehouse ACID guarantees via table formats like Apache Iceberg.</dd>
<dt><strong>dbt</strong></dt><dd>Data build tool — SQL-first transformation framework where models are SELECT statements with automated testing and documentation.</dd>
<dt><strong>Data Contract</strong></dt><dd>Formal agreement between data producers and consumers specifying schema, semantics, quality SLOs, and ownership.</dd>
<dt><strong>Medallion Architecture</strong></dt><dd>Bronze (raw) → Silver (cleaned) → Gold (aggregated) layering pattern for lakehouse data organization.</dd>
</dl>

<p><em>Last updated: 2026-06-08</em></p>""",

    "knowledge/research-methodology": """<h2>Research Methodology</h2>
<p>How AcaciaFund transforms raw signals into structured, quality-scored research articles.</p>

<h3>Pipeline Stages</h3>

<h4>1. Source Ingestion</h4>
<p>Content is drawn from three primary feeds:</p>
<ul>
<li><strong>HackerNews API</strong> (news.ycombinator.com) — technology, business, and science stories ranked by community engagement (points, comments). Top ~30 stories per day are analyzed.</li>
<li><strong>arXiv API</strong> (arxiv.org) — academic preprints across computer science, physics, mathematics, quantitative biology, and finance. Filtered by relevance to pillar topics.</li>
<li><strong>PubMed</strong> — biomedical literature (archived — science pillar discontinued).</li>
</ul>

<h4>2. Entity Extraction &amp; Summarization</h4>
<p>Each source is processed through NLP pipelines for:</p>
<ul>
<li><strong>Named Entity Recognition (NER)</strong> — extracting organizations, people, technologies, regulations, and financial instruments.</li>
<li><strong>Automatic Summarization</strong> — extractive summarization identifying key claims, numerical data, and conclusions.</li>
<li><strong>Topic Modeling</strong> — LDA-based classification into pillar-relevant topics and subtopics.</li>
</ul>

<h4>3. Bloom Taxonomy Classification</h4>
<p>Every article is assessed across six cognitive levels:</p>
<table style="width:100%;border-collapse:collapse;font-size:0.9em">
<tr style="background:var(--color-bg)"><th style="padding:8px;border:1px solid var(--color-border);text-align:left">Level</th><th style="padding:8px;border:1px solid var(--color-border);text-align:left">Description</th><th style="padding:8px;border:1px solid var(--color-border);text-align:left">Example Question</th></tr>
<tr><td style="padding:8px;border:1px solid var(--color-border)">Remember</td><td style="padding:8px;border:1px solid var(--color-border)">Recall facts and basic concepts</td><td style="padding:8px;border:1px solid var(--color-border)">Which pillar does this article belong to?</td></tr>
<tr><td style="padding:8px;border:1px solid var(--color-border)">Understand</td><td style="padding:8px;border:1px solid var(--color-border)">Explain ideas and concepts</td><td style="padding:8px;border:1px solid var(--color-border)">What is the primary domain of this article?</td></tr>
<tr><td style="padding:8px;border:1px solid var(--color-border)">Apply</td><td style="padding:8px;border:1px solid var(--color-border)">Use information in new situations</td><td style="padding:8px;border:1px solid var(--color-border)">How can these findings be applied in practice?</td></tr>
<tr><td style="padding:8px;border:1px solid var(--color-border)">Analyze</td><td style="padding:8px;border:1px solid var(--color-border)">Draw connections among ideas</td><td style="padding:8px;border:1px solid var(--color-border)">What assumptions underlie this analysis?</td></tr>
<tr><td style="padding:8px;border:1px solid var(--color-border)">Evaluate</td><td style="padding:8px;border:1px solid var(--color-border)">Justify a stand or decision</td><td style="padding:8px;border:1px solid var(--color-border)">How strong is the evidence presented?</td></tr>
<tr><td style="padding:8px;border:1px solid var(--color-border)">Create</td><td style="padding:8px;border:1px solid var(--color-border)">Produce new or original work</td><td style="padding:8px;border:1px solid var(--color-border)">Design an experiment to test this hypothesis.</td></tr>
</table>

<h4>4. Signal Quality Index (SQI) Computation</h4>
<p>SQI is a composable metric computed per article as a weighted combination:</p>
<pre style="background:var(--color-bg);padding:16px;border-radius:8px;font-size:0.85em">
SQI = w₁ · Authority + w₂ · Freshness + w₃ · Consensus + w₄ · Relevance

where:
  Authority    = domain reputation score (0–1)
  Freshness    = 1 - (days_since_publication / freshness_window)
  Consensus    = cross-source agreement rate
  Relevance    = keyword overlap with pillar taxonomy

Default weights: w₁=0.35, w₂=0.25, w₃=0.25, w₄=0.15
</pre>
<p>Weights are adjustable per pillar to prioritize different quality dimensions (e.g., AML favors authority, Data Engineering favors freshness).</p>

<h4>5. Cross-Pillar Analysis</h4>
<p>Each article is analyzed for connections to other pillars via:</p>
<ul>
<li><strong>Shared entity references</strong> — organizations, regulations, or technologies that appear across pillars</li>
<li><strong>Source overlap</strong> — articles from different pillars citing the same source</li>
<li><strong>Topic bridging</strong> — latent topic modeling revealing cross-domain themes</li>
</ul>

<h4>6. Quality Gates &amp; Serving</h4>
<p>Before publication, each article passes through quality gates:</p>
<ul>
<li><strong>Schema validation</strong> — Pydantic ensures all required fields are present and correctly typed</li>
<li><strong>Source diversity check</strong> — minimum source count and domain diversity thresholds</li>
<li><strong>SQI threshold</strong> — minimum SQI of 0.35 for publication</li>
<li><strong>Deterministic build</strong> — same registry.json always produces identical output</li>
</ul>
<p>The final artifact is static HTML deployed to Cloudflare Pages via <code>python3.13 build.py</code>.</p>

<p><em>Last updated: 2026-06-08</em></p>""",

    "knowledge/pillar-taxonomy": """<h2>Pillar Taxonomy Guide</h2>
<p>How AcaciaFund organizes research into three thematic pillars, with criteria for classification and examples.</p>

<h3>AML — Anti-Money Laundering</h3>
<table style="width:100%;border-collapse:collapse;font-size:0.9em">
<tr style="background:var(--color-bg)"><th style="padding:8px;border:1px solid var(--color-border);text-align:left">Aspect</th><th style="padding:8px;border:1px solid var(--color-border);text-align:left">Detail</th></tr>
<tr><td style="padding:8px;border:1px solid var(--color-border)">Color</td><td style="padding:8px;border:1px solid var(--color-border)">Amber (#d97706)</td></tr>
<tr><td style="padding:8px;border:1px solid var(--color-border)">Icon</td><td style="padding:8px;border:1px solid var(--color-border)">Shield</td></tr>
<tr><td style="padding:8px;border:1px solid var(--color-border)">Scope</td><td style="padding:8px;border:1px solid var(--color-border)">Financial crime detection, regulatory compliance, sanctions enforcement, crypto regulation, cross-border financial intelligence</td></tr>
<tr><td style="padding:8px;border:1px solid var(--color-border)">Key Sources</td><td style="padding:8px;border:1px solid var(--color-border)">FinCEN, FATF, OFAC, EU Commission, national regulators, compliance technology vendors</td></tr>
<tr><td style="padding:8px;border:1px solid var(--color-border)">Example Tags</td><td style="padding:8px;border:1px solid var(--color-border)">aml, compliance, regtech, financial-crime, sanctions, kyc, transaction-monitoring</td></tr>
</table>

<h3>Markets — Markets &amp; Industry</h3>
<table style="width:100%;border-collapse:collapse;font-size:0.9em">
<tr style="background:var(--color-bg)"><th style="padding:8px;border:1px solid var(--color-border);text-align:left">Aspect</th><th style="padding:8px;border:1px solid var(--color-border);text-align:left">Detail</th></tr>
<tr><td style="padding:8px;border:1px solid var(--color-border)">Color</td><td style="padding:8px;border:1px solid var(--color-border)">Green (#22c55e)</td></tr>
<tr><td style="padding:8px;border:1px solid var(--color-border)">Icon</td><td style="padding:8px;border:1px solid var(--color-border)">Chart</td></tr>
<tr><td style="padding:8px;border:1px solid var(--color-border)">Scope</td><td style="padding:8px;border:1px solid var(--color-border)">Semiconductor manufacturing, supply chain dynamics, AI hardware investment, EV battery production, quantum computing VC, industrial policy</td></tr>
<tr><td style="padding:8px;border:1px solid var(--color-border)">Key Sources</td><td style="padding:8px;border:1px solid var(--color-border)">Industry reports, earnings calls, trade publications, patent filings, venture capital data, government industrial policy documents</td></tr>
<tr><td style="padding:8px;border:1px solid var(--color-border)">Example Tags</td><td style="padding:8px;border:1px solid var(--color-border)">markets, semiconductors, supply-chain, manufacturing, ev, batteries, venture-capital, deep-tech</td></tr>
</table>

<h3>Data Engineering — Data Engineering &amp; Infrastructure</h3>
<table style="width:100%;border-collapse:collapse;font-size:0.9em">
<tr style="background:var(--color-bg)"><th style="padding:8px;border:1px solid var(--color-border);text-align:left">Aspect</th><th style="padding:8px;border:1px solid var(--color-border);text-align:left">Detail</th></tr>
<tr><td style="padding:8px;border:1px solid var(--color-border)">Color</td><td style="padding:8px;border:1px solid var(--color-border)">Indigo (#6366f1)</td></tr>
<tr><td style="padding:8px;border:1px solid var(--color-border)">Icon</td><td style="padding:8px;border:1px solid var(--color-border)">Gears</td></tr>
<tr><td style="padding:8px;border:1px solid var(--color-border)">Scope</td><td style="padding:8px;border:1px solid var(--color-border)">Data pipeline orchestration (Dagster, Airflow, Prefect), data quality engineering (Great Expectations, Soda), streaming platforms (Kafka, Flink), lakehouse architectures (Iceberg, Delta Lake), analytics engineering (dbt, SQLMesh)</td></tr>
<tr><td style="padding:8px;border:1px solid var(--color-border)">Key Sources</td><td style="padding:8px;border:1px solid var(--color-border)">Dagster blog, dbt developer blog, Apache project docs, Data Engineering Weekly, Confluent blog, vendor engineering blogs</td></tr>
<tr><td style="padding:8px;border:1px solid var(--color-border)">Example Tags</td><td style="padding:8px;border:1px solid var(--color-border)">data-engineering, dataops, pipeline, orchestration, dbt, dagster, kafka, data-quality, lakehouse, streaming</td></tr>
</table>

<h3>Cross-Pillar Topics</h3>
<p>Some topics span multiple pillars. Notable cross-pillar themes include:</p>
<ul>
<li><strong>Crypto &amp; Blockchain</strong> — AML (regulatory enforcement), Markets (investment, mining economics), Data Engineering (blockchain data pipelines, on-chain analytics infrastructure)</li>
<li><strong>AI Regulation</strong> — AML (compliance automation), Markets (AI industry investment), Data Engineering (ML pipeline infrastructure, feature stores, model serving)</li>
<li><strong>Supply Chain Intelligence</strong> — AML (trade-based money laundering), Markets (semiconductor/EV supply chains), Data Engineering (supply chain data integration, real-time tracking pipelines)</li>
</ul>

<p><em>Last updated: 2026-06-08</em></p>""",

    "knowledge/changelog": """<h2>Changelog</h2>
<p>Platform version history and notable changes to AcaciaFund.</p>

<h3>2026-06-08 — Knowledge Base Overhaul</h3>
<ul>
<li>Added dedicated <code>knowledge.j2</code> template with TOC, breadcrumbs, cross-references, and progress bar</li>
<li>Reorganized knowledge entries into categories: Platform, Guides, Reference, Architecture</li>
<li>Expanded glossary to 30+ terms across all categories (AML, Markets, Data Engineering, DataOps)</li>
<li>Added Research Methodology guide with full SQI formula and pipeline description</li>
<li>Added Pillar Taxonomy guide with per-pillar scope, sources, and tag examples</li>
<li>Migrated all knowledge slugs under <code>/knowledge/</code> namespace</li>
<li>Added cross-referencing between knowledge and research/learn content via tag matching</li>
<li>Generated category-specific thumbnail SVGs for knowledge sub-categories</li>
</ul>

<h3>2026-06-08 — DataOps System Architecture</h3>
<ul>
<li>Added system architecture knowledge page</li>
<li>Added DataOps glossary and open source tool landscape</li>
<li>Updated README with full system architecture diagram</li>
<li>Added <code>seed_dataops.py</code> for DataOps/engineering content seeding</li>
</ul>

<h3>2026-06-08 — 3-Category Taxonomy Launch</h3>
<ul>
<li>Introduced <code>content_type</code> field (research | learn | knowledge)</li>
<li>Reclassified all registry entries</li>
<li>Created category index pages for research/, learn/, knowledge/</li>
<li>Created dedicated <code>learn.j2</code> template</li>
<li>Added learning hub entries (AML basics, market analysis, science method, quiz)</li>
<li>Added static knowledge pages (about, research overview, scholarship, contact, glossary, FAQ)</li>
</ul>

<h3>2026-06-07 — Fractal Thumbnails &amp; Interest Ranking</h3>
<ul>
<li>Implemented seed-based fractal tree SVGs for per-article unique thumbnails</li>
<li>Added OG image generation for social sharing</li>
<li>Homepage now ranks articles by interest score (SQI × 0.6 + recency × 0.4)</li>
<li>Added 15 new articles (Jan–May 2026, 5 per pillar)</li>
</ul>

<h3>2026-06-01 — Initial Platform Launch</h3>
<ul>
<li>Python-native static generator with Jinja2 + Pydantic</li>
<li>Dark mode with FOUC prevention and localStorage persistence</li>
<li>Accessible dropdown navigation and mobile menu</li>
<li>Reading progress bar, TOC sidebar, focus mode</li>
<li>Self-hosted Tailwind and Inter font</li>
<li>Cloudflare Pages deployment via GitHub</li>
<li>12 initial research articles (daily digest format)</li>
</ul>

<p><em>Last updated: 2026-06-08</em></p>""",

    "knowledge/system-architecture": """<h2>AcaciaFund as a DataOps Pipeline</h2>
<p>AcaciaFund is not just a static site — it is a <strong>data product</strong> produced by an automated DataOps pipeline. Every component from source ingestion to final HTML rendering follows DataOps principles: version control, quality gates, observability, and reproducible builds.</p>

<figure style="margin:1.5rem 0"><img src="/static/images/pipeline-diagram.svg" alt="AcaciaFund DataOps Content Pipeline Diagram" style="width:100%;max-width:900px;border-radius:12px;box-shadow:0 4px 12px rgba(0,0,0,0.3)"></figure>

<h2>Pipeline Architecture</h2>
<pre style="background:var(--color-bg);padding:16px;border-radius:8px;overflow-x:auto;font-size:0.85em;line-height:1.6">
┌──────────────────────────────────────────────────────────┐
│                      INGESTION LAYER                      │
│  HackerNews API ──┐                                       │
│  arXiv API        ├──→ trending stories + analysis        │
│  PubMed           ┘    (manual + scheduled)               │
└─────────────────────────────┬────────────────────────────┘
                              │
┌─────────────────────────────▼────────────────────────────┐
│                   TRANSFORMATION LAYER                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │ NLP Pipeline │  │   Bloom     │  │    SQI       │    │
│  │ (entity ext, │→│  Taxonomy   │→│  Computation │    │
│  │ summarization│) │  Classifier │  │  (0.0 – 1.0) │    │
│  └──────────────┘  └──────────────┘  └──────────────┘    │
└─────────────────────────────┬────────────────────────────┘
                              │
┌─────────────────────────────▼────────────────────────────┐
│                   STORAGE / CATALOG LAYER                  │
│  ┌────────────────────────────────────────────────────┐  │
│  │             registry.json (Data Catalog)            │  │
│  │  • Content metadata    • Quality metrics            │  │
│  │  • Source lineage      • Pipeline state             │  │
│  │  • Signal scores       • Taxonomy classification    │  │
│  └────────────────────────────────────────────────────┘  │
└─────────────────────────────┬────────────────────────────┘
                              │
┌─────────────────────────────▼────────────────────────────┐
│                    SERVING LAYER                           │
│  ┌──────────────┐    ┌──────────────┐                     │
│  │  generator   │───→│   Static     │───→ Cloudflare      │
│  │  .py (Jinja2)│    │  HTML Files  │    Pages (CDN)      │
│  └──────────────┘    └──────────────┘                     │
│  Serves: research/ · learn/ · knowledge/ · pillars/       │
└──────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────▼────────────────────────────┐
│                OBSERVABILITY & QUALITY                    │
│  • SQI per article (0–1)    • Source diversity score      │
│  • Quality flags            • Cross-pillar connections    │
│  • Source breakdown (HN/arXiv/PubMed)                     │
│  • Build output: 59 pages, validated                      │
└──────────────────────────────────────────────────────────┘
</pre>

<h2>DataOps Principles Applied</h2>

<h3>1. Version Control Everything</h3>
<p><strong>registry.json</strong> — the content catalog — is under Git version control alongside pipeline code (<code>build.py</code>, <code>schemas.py</code>). Every content change is a Git commit with a full audit trail. Rolling back is a <code>git revert</code> away.</p>

<h3>2. Data Quality as Code</h3>
<p>Each content entry carries structured <strong>quality metrics</strong> (source score, diversity, recency) and <strong>quality flags</strong>. The <strong>Signal Quality Index (SQI)</strong> is a composable metric computed from source authority, freshness, consensus, and relevance — evaluated programmatically, not manually.</p>

<h3>3. CI/CD for Data</h3>
<p>On push to <code>main</code>, <strong>Cloudflare Pages</strong> runs <code>python3.13 build.py</code> — an automated build that transforms raw registry data into static HTML. Failed builds (e.g., schema validation errors) prevent deployment, acting as a quality gate.</p>

<h3>4. Declarative Pipeline</h3>
<p>The pipeline is <strong>deterministic</strong>: same <code>registry.json</code> → identical output. No side effects, no external state at build time. This makes builds reproducible and debuggable.</p>

<h3>5. Observability</h3>
<p>Every article exposes structured signal data: source breakdown (HN vs arXiv vs PubMed counts), domain diversity, top entities, and SQI score. These serve as <strong>pipeline metrics</strong> for monitoring content quality over time.</p>

<h3>6. Separation of Concerns</h3>
<table style="width:100%;border-collapse:collapse;font-size:0.9em">
<tr style="background:var(--color-bg)"><th style="padding:8px;border:1px solid var(--color-border);text-align:left">Layer</th><th style="padding:8px;border:1px solid var(--color-border);text-align:left">Tool</th><th style="padding:8px;border:1px solid var(--color-border);text-align:left">DataOps Equivalent</th></tr>
<tr><td style="padding:8px;border:1px solid var(--color-border)">Ingestion</td><td style="padding:8px;border:1px solid var(--color-border)">HackerNews API / arXiv API</td><td style="padding:8px;border:1px solid var(--color-border)">Source connectors</td></tr>
<tr><td style="padding:8px;border:1px solid var(--color-border)">Transformation</td><td style="padding:8px;border:1px solid var(--color-border)">seed_articles.py + manual</td><td style="padding:8px;border:1px solid var(--color-border)">dbt models / transformation DAG</td></tr>
<tr><td style="padding:8px;border:1px solid var(--color-border)">Storage</td><td style="padding:8px;border:1px solid var(--color-border)">registry.json (Git)</td><td style="padding:8px;border:1px solid var(--color-border)">Data catalog (OpenMetadata-style)</td></tr>
<tr><td style="padding:8px;border:1px solid var(--color-border)">Quality</td><td style="padding:8px;border:1px solid var(--color-border)">SQI + quality_metrics</td><td style="padding:8px;border:1px solid var(--color-border)">Great Expectations suites</td></tr>
<tr><td style="padding:8px;border:1px solid var(--color-border)">Serving</td><td style="padding:8px;border:1px solid var(--color-border)">build.py → static HTML</td><td style="padding:8px;border:1px solid var(--color-border)">Data mart / analytics layer</td></tr>
<tr><td style="padding:8px;border:1px solid var(--color-border)">CI/CD</td><td style="padding:8px;border:1px solid var(--color-border)">Git → Cloudflare Pages</td><td style="padding:8px;border:1px solid var(--color-border)">dbt Cloud / Airflow CI</td></tr>
</table>

<h2>Pipeline Metrics</h2>
<ul>
<li><strong>Content volume:</strong> 51 entries across research (33), learn (8), knowledge (10)</li>
<li><strong>Pillar coverage:</strong> AML (11), Markets (11), Data Engineering (5)</li>
<li><strong>Build time:</strong> ~2 seconds (Python-native, no external deps at build)</li>
<li><strong>Output size:</strong> ~2MB uncompressed (HTML + SVG thumbnails + OG images)</li>
<li><strong>SQI range:</strong> 0.35 – 0.88 across all research articles</li>
<li><strong>Source diversity:</strong> HN, arXiv, PubMed — avg 5-7 domains per article</li>
</ul>

<h2>Future: Service Layer</h2>
<p>A separate <strong>FastAPI service</strong> (deployed on Railway) adds real-time capabilities:</p>
<ul>
<li>Progress tracking across articles (POST/GET progress)</li>
<li>Trending signals per pillar</li>
<li>Reader engagement metrics</li>
</ul>
<p>This follows the <strong>lambda architecture</strong> pattern: batch (static site) + speed (API) layers.</p>

<p><em>Last updated: 2026-06-08</em></p>""",
}

def generate_knowledge_thumbnail(category: str) -> str:
    """Generate a geometric abstract SVG for a knowledge sub-category."""
    meta = CATEGORY_META[category]
    colors = {
        "platform": {"primary": "#6366f1", "secondary": "#818cf8", "bg": "#0f172a"},
        "guide": {"primary": "#22c55e", "secondary": "#4ade80", "bg": "#052e16"},
        "reference": {"primary": "#d97706", "secondary": "#f59e0b", "bg": "#0f172a"},
        "architecture": {"primary": "#a855f7", "secondary": "#c084fc", "bg": "#1e1b4b"},
    }
    c = colors[category]
    cat = category.upper()
    if category == "platform":
        # Grid pattern
        elements = [
            f'<rect x="40" y="40" width="50" height="50" rx="6" fill="none" stroke="{c["primary"]}" stroke-width="1.5" opacity="0.3"/>',
            f'<rect x="100" y="40" width="50" height="50" rx="6" fill="none" stroke="{c["primary"]}" stroke-width="1.5" opacity="0.5"/>',
            f'<rect x="40" y="100" width="50" height="50" rx="6" fill="none" stroke="{c["primary"]}" stroke-width="1.5" opacity="0.4"/>',
            f'<circle cx="125" cy="65" r="12" fill="{c["primary"]}" opacity="0.2"/>',
            f'<circle cx="65" cy="65" r="8" fill="{c["secondary"]}" opacity="0.15"/>',
            f'<line x1="200" y1="50" x2="520" y2="50" stroke="{c["primary"]}" stroke-width="1" opacity="0.2"/>',
            f'<line x1="200" y1="110" x2="480" y2="110" stroke="{c["primary"]}" stroke-width="1" opacity="0.15"/>',
        ]
    elif category == "guide":
        # Compass/book
        elements = [
            f'<circle cx="100" cy="80" r="40" fill="none" stroke="{c["primary"]}" stroke-width="1.5" opacity="0.3"/>',
            f'<circle cx="100" cy="80" r="20" fill="none" stroke="{c["primary"]}" stroke-width="1" opacity="0.5"/>',
            f'<line x1="100" y1="30" x2="100" y2="130" stroke="{c["primary"]}" stroke-width="1" opacity="0.3"/>',
            f'<line x1="50" y1="80" x2="150" y2="80" stroke="{c["primary"]}" stroke-width="1" opacity="0.3"/>',
            f'<circle cx="100" cy="80" r="4" fill="{c["primary"]}" opacity="0.6"/>',
            f'<circle cx="80" cy="60" r="60" fill="none" stroke="{c["secondary"]}" stroke-width="0.5" opacity="0.15"/>',
        ]
    elif category == "reference":
        # Book/lines pattern
        elements = [
            f'<rect x="40" y="40" width="80" height="110" rx="4" fill="none" stroke="{c["primary"]}" stroke-width="1.5" opacity="0.3"/>',
            f'<line x1="55" y1="65" x2="105" y2="65" stroke="{c["primary"]}" stroke-width="2" opacity="0.4"/>',
            f'<line x1="55" y1="80" x2="105" y2="80" stroke="{c["secondary"]}" stroke-width="1.5" opacity="0.3"/>',
            f'<line x1="55" y1="95" x2="95" y2="95" stroke="{c["primary"]}" stroke-width="1.5" opacity="0.25"/>',
            f'<line x1="55" y1="110" x2="100" y2="110" stroke="{c["secondary"]}" stroke-width="1" opacity="0.2"/>',
            f'<circle cx="160" cy="60" r="30" fill="{c["primary"]}" opacity="0.08"/>',
            f'<circle cx="160" cy="60" r="15" fill="{c["secondary"]}" opacity="0.12"/>',
        ]
    else:
        # Architecture — network nodes
        elements = [
            f'<circle cx="60" cy="60" r="15" fill="none" stroke="{c["primary"]}" stroke-width="1.5" opacity="0.5"/>',
            f'<circle cx="140" cy="40" r="10" fill="none" stroke="{c["primary"]}" stroke-width="1.5" opacity="0.4"/>',
            f'<circle cx="120" cy="100" r="12" fill="none" stroke="{c["secondary"]}" stroke-width="1.5" opacity="0.35"/>',
            f'<line x1="60" y1="60" x2="140" y2="40" stroke="{c["primary"]}" stroke-width="1" opacity="0.3"/>',
            f'<line x1="60" y1="60" x2="120" y2="100" stroke="{c["primary"]}" stroke-width="1" opacity="0.25"/>',
            f'<line x1="140" y1="40" x2="120" y2="100" stroke="{c["primary"]}" stroke-width="1" opacity="0.2"/>',
            f'<circle cx="60" cy="60" r="4" fill="{c["primary"]}" opacity="0.6"/>',
            f'<circle cx="140" cy="40" r="3" fill="{c["primary"]}" opacity="0.5"/>',
            f'<circle cx="120" cy="100" r="3" fill="{c["secondary"]}" opacity="0.5"/>',
        ]

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="600" height="200" viewBox="0 0 600 200">
<defs>
<linearGradient id="kb-{category}" x1="0" y1="0" x2="1" y2="1">
<stop offset="0" stop-color="{c["bg"]}"/>
<stop offset="0.5" stop-color="{c["bg"]}"/>
<stop offset="1" stop-color="#0a0a1a"/>
</linearGradient>
</defs>
<rect width="600" height="200" fill="url(#kb-{category})"/>
<circle cx="300" cy="100" r="180" fill="{c["primary"]}" opacity="0.03"/>
<circle cx="300" cy="100" r="120" fill="{c["secondary"]}" opacity="0.03"/>
{"".join(elements)}
<text x="300" y="170" text-anchor="middle" fill="{c["primary"]}" font-family="system-ui,sans-serif" font-size="11" font-weight="600" opacity="0.6">{cat}</text>
</svg>"""


def main():
    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        registry = json.load(f)

    existing = {c["slug"]: c for c in registry["content"]}

    old_slugs = {"about": "knowledge/about",
                 "contact": "knowledge/contact",
                 "research": "knowledge/research-methodology"}

    # --- Remove old flat-slug entries, mark for add/rename ---
    slugs_to_remove = set()
    slugs_to_add = {}

    for old_slug, new_slug in old_slugs.items():
        if old_slug in existing:
            entry = existing[old_slug]
            slugs_to_remove.add(old_slug)
            entry["slug"] = new_slug
            slugs_to_add[new_slug] = entry
            print(f"  Migrating: {old_slug} → {new_slug}")

    # --- Remove old flat-slug entries from content list ---
    registry["content"] = [c for c in registry["content"] if c["slug"] not in slugs_to_remove]

    # --- Add migrated entries back ---
    added_slugs = set()
    for slug, entry in slugs_to_add.items():
        if slug not in existing:
            registry["content"].append(entry)
            added_slugs.add(slug)
            print(f"  Added migrated: {slug}")

    # --- Update or add new knowledge entries ---
    new_knowledge_slugs = [
        "knowledge/about", "knowledge/contact", "knowledge/faq",
        "knowledge/research-methodology", "knowledge/pillar-taxonomy",
        "knowledge/glossary",
        "knowledge/changelog",
        "knowledge/dataops-glossary",
        "knowledge/open-source-tools",
        "knowledge/system-architecture",
    ]

    # Remove migrated + updated entries to re-add cleanly
    registry["content"] = [c for c in registry["content"]
                           if c.get("content_type") != "knowledge"
                           or c["slug"] not in new_knowledge_slugs]

    now = datetime.now(timezone.utc)
    for slug in new_knowledge_slugs:
        if slug in existing and slug not in added_slugs:
            entry = existing[slug]
        else:
            entry = None

        category = KNOWLEDGE_CATEGORIES.get(slug, "reference")

        if entry is None:
            # New entry — build from scratch
            title_map = {
                "knowledge/about": "About AcaciaFund",
                "knowledge/contact": "Contact Us",
                "knowledge/faq": "Frequently Asked Questions",
                "knowledge/research-methodology": "Research Methodology",
                "knowledge/pillar-taxonomy": "Pillar Taxonomy Guide",
                "knowledge/glossary": "Glossary",
                "knowledge/changelog": "Changelog",
                "knowledge/dataops-glossary": "DataOps Glossary",
                "knowledge/open-source-tools": "Open Source Data Engineering Tool Landscape",
                "knowledge/system-architecture": "AcaciaFund System Architecture",
            }
            desc_map = {
                "knowledge/about": "Mission, vision, and architecture of the AcaciaFund research synthesis platform.",
                "knowledge/contact": "How to reach the AcaciaFund team, report issues, or suggest content.",
                "knowledge/faq": "Answers to common questions about AcaciaFund's methodology, content, and platform.",
                "knowledge/research-methodology": "How AcaciaFund transforms raw signals into quality-scored research — SQI, Bloom taxonomy, pipeline stages.",
                "knowledge/pillar-taxonomy": "Detailed guide to the AML, Markets, and Data Engineering pillars with scope criteria and examples.",
                "knowledge/glossary": "Terms defined across AML, Markets, Data Engineering, and DataOps — continuously expanded.",
                "knowledge/changelog": "Platform version history and notable changes.",
                "knowledge/dataops-glossary": "Key DataOps and data engineering terminology.",
                "knowledge/open-source-tools": "Curated reference of open source tools for modern data platforms.",
                "knowledge/system-architecture": "AcaciaFund as a DataOps pipeline — architecture, principles, and metrics.",
            }
            tag_map = {
                "knowledge/about": ["about", "info", "platform"],
                "knowledge/contact": ["contact", "support"],
                "knowledge/faq": ["faq", "help", "questions"],
                "knowledge/research-methodology": ["methodology", "research", "pipeline", "sqi", "bloom"],
                "knowledge/pillar-taxonomy": ["pillars", "taxonomy", "aml", "markets", "data-engineering"],
                "knowledge/glossary": ["glossary", "reference", "terms"],
                "knowledge/changelog": ["changelog", "version", "history"],
                "knowledge/dataops-glossary": ["dataops", "glossary", "reference"],
                "knowledge/open-source-tools": ["dataops", "tools", "open-source", "reference"],
                "knowledge/system-architecture": ["dataops", "architecture", "system", "pipeline"],
            }
            entry = {
                "slug": slug,
                "language": "en",
                "title": title_map[slug],
                "description": desc_map[slug],
                "body_html": EXPANDED_BODIES.get(slug, "<p>Content coming soon.</p>"),
                "category": "page",
                "content_type": "knowledge",
                "tags": tag_map[slug],
                "created_at": now.isoformat(),
                "updated_at": None,
                "pillar": "",
                "date_str": "2026-06-08",
                "thumbnail_svg": generate_knowledge_thumbnail(category),
                "og_svg": "",
                "featured_image": "",
                "trending_html": "",
                "analysis_html": "",
                "cross_pillar_html": "",
                "bloom_questions": [],
                "flashcards": [],
                "signals": {},
                "source_breakdown": {},
                "quality_metrics": {},
                "lineage": {},
                "quality_flags": [],
            }
        else:
            # Update existing entry
            entry["slug"] = slug
            entry["body_html"] = EXPANDED_BODIES.get(slug, entry.get("body_html", ""))
            entry["description"] = {
                "knowledge/about": "Mission, vision, and architecture of the AcaciaFund research synthesis platform.",
                "knowledge/contact": "How to reach the AcaciaFund team, report issues, or suggest content.",
                "knowledge/faq": "Answers to common questions about AcaciaFund's methodology, content, and platform.",
                "knowledge/research-methodology": "How AcaciaFund transforms raw signals into quality-scored research — SQI, Bloom taxonomy, pipeline stages.",
                "knowledge/pillar-taxonomy": "Detailed guide to the AML, Markets, and Data Engineering pillars with scope criteria and examples.",
                "knowledge/glossary": "Terms defined across AML, Markets, Data Engineering, and DataOps — continuously expanded.",
                "knowledge/changelog": "Platform version history and notable changes.",
                "knowledge/dataops-glossary": "Key DataOps and data engineering terminology.",
                "knowledge/open-source-tools": "Curated reference of open source tools for modern data platforms.",
                "knowledge/system-architecture": "AcaciaFund as a DataOps pipeline — architecture, principles, and metrics.",
            }.get(slug, entry.get("description", ""))
            entry["tags"] = {
                "knowledge/about": ["about", "info", "platform"],
                "knowledge/contact": ["contact", "support"],
                "knowledge/faq": ["faq", "help", "questions"],
                "knowledge/research-methodology": ["methodology", "research", "pipeline", "sqi", "bloom"],
                "knowledge/pillar-taxonomy": ["pillars", "taxonomy", "aml", "markets", "data-engineering"],
                "knowledge/glossary": ["glossary", "reference", "terms"],
                "knowledge/changelog": ["changelog", "version", "history"],
                "knowledge/dataops-glossary": ["dataops", "glossary", "reference"],
                "knowledge/open-source-tools": ["dataops", "tools", "open-source", "reference"],
                "knowledge/system-architecture": ["dataops", "architecture", "system", "pipeline"],
            }.get(slug, entry.get("tags", []))
            entry["date_str"] = "2026-06-08"
            entry["corrected_at"] = now.isoformat()
            entry["thumbnail_svg"] = generate_knowledge_thumbnail(category)

        # Ensure content_type
        entry["content_type"] = "knowledge"
        # Add knowledge_category as a tag prefix for template filtering
        entry["knowledge_category"] = category

        registry["content"].append(entry)
        print(f"  Knowledge: {slug} ({category})")

    # --- Sort: research → learn → knowledge ---
    research = [c for c in registry["content"] if c.get("content_type") == "research"]
    learn = [c for c in registry["content"] if c.get("content_type") == "learn"]
    knowledge = [c for c in registry["content"] if c.get("content_type") == "knowledge"]
    research.sort(key=lambda c: c.get("date_str", ""), reverse=True)
    registry["content"] = research + learn + knowledge

    registry["last_run"] = now.isoformat()

    with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2, ensure_ascii=False)

    r, l, k = len(research), len(learn), len(knowledge)
    print(f"\nDone. {r} research + {l} learn + {k} knowledge = {r+l+k} total.")


if __name__ == "__main__":
    main()
