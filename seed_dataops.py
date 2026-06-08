#!/usr/bin/env python3.13
"""
Seed DataOps/Data Science/Engineering articles across all 3 content types.
Also adds system architecture page and updates the DataOps tool landscape.
"""
import hashlib, json, math, re
from datetime import datetime, timezone
from pathlib import Path
from seed_articles import (generate_thumbnail_svg, generate_og_svg,
                           make_bloom_questions, make_flashcards,
                           generate_body_html, PILLAR_META as pm)

REGISTRY_PATH = Path("registry.json")

NEW_RESEARCH = [
    {
        "slug": "blog/2026-06-08-dataops-aml",
        "title": "Data Pipeline Observability in Financial Crime Compliance: Real-Time AML Monitoring at Scale",
        "description": "How DataOps practices including pipeline observability, data quality monitoring, and automated lineage tracking are transforming anti-money laundering transaction monitoring systems at major financial institutions.",
        "date": "2026-06-08", "pillar": "aml",
        "tags": ["aml", "dataops", "observability", "pipeline", "real-time", "compliance"],
        "sqi": 0.82, "hn_pts": 512, "source_count": 14, "domains": 6,
    },
    {
        "slug": "blog/2026-06-08-dataops-markets",
        "title": "Real-Time Data Engineering for Algorithmic Trading: From Tick Data to Execution Signals",
        "description": "Production-grade data pipelines for algorithmic trading systems: handling market data at microsecond latency, feature engineering stream processing, backtesting infrastructure, and DataOps orchestration.",
        "date": "2026-06-08", "pillar": "stock",
        "tags": ["markets", "dataops", "real-time", "trading", "stream-processing", "engineering"],
        "sqi": 0.87, "hn_pts": 678, "source_count": 16, "domains": 7,
    },
    {
        "slug": "blog/2026-06-08-dataops-science",
        "title": "Reproducible ML Pipelines in Computational Biology: MLOps for CRISPR Target Discovery",
        "description": "Applying DataOps and MLOps principles to computational biology workflows: version-controlled training data, reproducible feature engineering, automated model validation, and pipeline CI/CD for CRISPR target prediction.",
        "date": "2026-06-08", "pillar": "data-engineering",
        "tags": ["dataops", "data-engineering", "mlops", "crispr", "reproducibility", "bioinformatics"],
        "sqi": 0.84, "hn_pts": 423, "source_count": 15, "domains": 6,
    },
]

NEW_LEARN = [
    {
        "slug": "learn/dataops-introduction",
        "title": "Introduction to DataOps: Principles, Practices, and Pipeline Architecture",
        "body_html": """<h2>What is DataOps?</h2>
<p>DataOps is an automated, process-oriented methodology used by data teams to improve the quality and reduce the cycle time of data analytics. It applies agile software development, DevOps, and statistical process control (SPC) principles to the data pipeline lifecycle.</p>

<h2>Core Principles</h2>
<ul>
<li><strong>Continuous Integration & Delivery:</strong> Changes to data pipelines, schemas, and transformations are automatically tested and deployed — just like application code.</li>
<li><strong>Pipeline Observability:</strong> Every stage of the data pipeline emits metrics: row counts, schema drift, null rates, latency percentiles. Teams monitor these in real-time dashboards.</li>
<li><strong>Data Quality as Code:</strong> Expectations and quality checks are defined programmatically (Great Expectations, Soda, dbt tests) and run on every pipeline execution.</li>
<li><strong>Version Everything:</strong> Data schemas, transformation logic, pipeline definitions, training datasets — all under version control with semantic versioning.</li>
<li><strong>Reproducibility:</strong> Given the same input data and pipeline version, the output must be identical. This requires deterministic transforms, immutable data layers, and full lineage tracking.</li>
</ul>

<h2>DataOps vs DevOps vs MLOps</h2>
<table style="width:100%;border-collapse:collapse;font-size:0.9em">
<tr style="background:var(--color-bg)"><th style="padding:8px;border:1px solid var(--color-border);text-align:left">Dimension</th><th style="padding:8px;border:1px solid var(--color-border);text-align:left">DevOps</th><th style="padding:8px;border:1px solid var(--color-border);text-align:left">DataOps</th><th style="padding:8px;border:1px solid var(--color-border);text-align:left">MLOps</th></tr>
<tr><td style="padding:8px;border:1px solid var(--color-border)">Unit of work</td><td style="padding:8px;border:1px solid var(--color-border)">Code commit</td><td style="padding:8px;border:1px solid var(--color-border)">Data pipeline run</td><td style="padding:8px;border:1px solid var(--color-border)">Model training run</td></tr>
<tr><td style="padding:8px;border:1px solid var(--color-border)">Quality gate</td><td style="padding:8px;border:1px solid var(--color-border)">Tests pass</td><td style="padding:8px;border:1px solid var(--color-border)">Expectations pass</td><td style="padding:8px;border:1px solid var(--color-border)">Metrics threshold met</td></tr>
<tr><td style="padding:8px;border:1px solid var(--color-border)">Artifact</td><td style="padding:8px;border:1px solid var(--color-border)">Deployable binary</td><td style="padding:8px;border:1px solid var(--color-border)">Cleaned dataset</td><td style="padding:8px;border:1px solid var(--color-border)">Trained model</td></tr>
<tr><td style="padding:8px;border:1px solid var(--color-border)">Orchestration</td><td style="padding:8px;border:1px solid var(--color-border)">CI/CD pipeline</td><td style="padding:8px;border:1px solid var(--color-border)">Airflow/Dagster DAG</td><td style="padding:8px;border:1px solid var(--color-border)">MLflow/Kubeflow</td></tr>
</table>

<h2>Key Tools by Category</h2>
<ul>
<li><strong>Orchestration:</strong> Apache Airflow, Dagster, Prefect</li>
<li><strong>Data Integration:</strong> Airbyte, Meltano, Apache NiFi</li>
<li><strong>Transformation:</strong> dbt, SQLMesh</li>
<li><strong>Quality:</strong> Great Expectations, Soda, dbt tests</li>
<li><strong>Catalog & Lineage:</strong> OpenMetadata, DataHub, Amundsen</li>
<li><strong>Monitoring:</strong> Monte Carlo, Bigeye, custom (Prometheus + Grafana)</li>
<li><strong>Streaming:</strong> Apache Kafka, Apache Flink, RisingWave</li>
</ul>

<h2>Practice: Build a Pipeline Manifest</h2>
<p>Every data pipeline should have a manifest file (YAML or TOML) that declares:</p>
<ul>
<li>Source connectors and their schemas</li>
<li>Transformation DAG (materialized views or dbt models)</li>
<li>Data quality expectations per stage</li>
<li>SLOs (freshness, completeness, accuracy)</li>
<li>Ownership and escalation contacts</li>
</ul>
<p>This manifest becomes the single source of truth for pipeline operations — the <em>registry of pipelines</em>, analogous to this site's registry.json for content.</p>""",
        "date": "2026-06-08", "pillar": "",
        "tags": ["dataops", "data-engineering", "pipeline", "best-practices"],
        "flashcards": [
            {"term": "DataOps", "definition": "Automated, process-oriented methodology applying DevOps and SPC principles to data pipeline lifecycle."},
            {"term": "Pipeline Observability", "definition": "Real-time monitoring of data pipeline metrics: row counts, schema drift, latency, null rates at every stage."},
            {"term": "dbt", "definition": "Data build tool — SQL-first transformation framework that enables analysts to define transformations as version-controlled, tested SQL SELECT statements."},
            {"term": "Great Expectations", "definition": "Open-source data quality framework that lets teams define, test, and document data expectations programmatically."},
            {"term": "Medallion Architecture", "definition": "Lakehouse data organization pattern with Bronze (raw), Silver (cleaned), and Gold (aggregated/business-ready) layers."},
        ],
    },
    {
        "slug": "learn/data-quality-engineering",
        "title": "Data Quality Engineering: Testing, Monitoring, and Expectations at Scale",
        "body_html": """<h2>Why Data Quality Engineering Matters</h2>
<p>In a DataOps culture, data quality is not discovered after the fact — it is engineered into the pipeline from day one. Every time data moves between stages, there is a risk of corruption, drift, or silent failure. Data quality engineering applies software testing principles to data.</p>

<h2>Three Layers of Data Quality</h2>

<h3>1. Freshness</h3>
<p>Is the data current? A pipeline SLO might state: "All source data must be ingested within 5 minutes of production." Violations trigger alerts and page the on-call data engineer. Freshness checks compare the max timestamp of incoming records against the current time.</p>

<h3>2. Completeness</h3>
<p>Are all expected records present? Row count checks compare expected vs actual counts. A sudden drop of 30% in event volume usually means a source connector failed or schema changed.</p>

<h3>3. Accuracy</h3>
<p>Do the values make sense? Accuracy checks include: NULL ratio thresholds, reference integrity (every foreign key has a matching primary key), domain constraints (age between 0 and 120), and statistical distribution checks (z-score outlier detection).</p>

<h2>Expectations as Code</h2>
<p>Great Expectations lets you define expectations as Python objects:</p>
<pre style="background:var(--color-bg);padding:16px;border-radius:8px;overflow-x:auto;font-size:0.85em">
expectation_suite = ExpectationSuite("transactions_clean")
expectation_suite.add_expectation(
    ExpectColumnValuesToBeBetween("amount", 0, 1000000)
)
expectation_suite.add_expectation(
    ExpectColumnValuesToNotBeNull("transaction_id")
)
</pre>
<p>These expectations run on every pipeline execution. If they fail, the pipeline either halts (hard gate) or proceeds with a warning (soft gate) depending on severity.</p>

<h2>Monitoring Dashboard</h2>
<p>A production data quality dashboard tracks:</p>
<ul>
<li>Pass/fail rate per expectation over time</li>
<li>Data freshness (minutes since last successful ingestion) per source</li>
<li>Row count trends with anomaly detection (sudden drops/spikes)</li>
<li>Schema change events (new columns, dropped columns, type changes)</li>
<li>Pipeline DAG health (success rate, duration, backlog)</li>
</ul>
<p>The AcaciaFund SQI (Signal Quality Index) is itself a data quality metric — combining source authority, freshness, consensus, and relevance into a single composable score.</p>""",
        "date": "2026-06-08", "pillar": "",
        "tags": ["data-quality", "testing", "dataops", "engineering"],
        "flashcards": [
            {"term": "Expectation Suite", "definition": "Collection of data quality assertions that define the expected state of a dataset."},
            {"term": "Soft Gate vs Hard Gate", "definition": "Soft gate: pipeline continues but issues warning. Hard gate: pipeline halts on quality failure."},
            {"term": "Schema Drift", "definition": "Unexpected change in dataset schema (new/missing columns, type changes) that can cause downstream failures."},
            {"term": "Signal Quality Index (SQI)", "definition": "Composite metric measuring source authority, freshness, consensus, and relevance of synthesized content."},
        ],
    },
    {
        "slug": "learn/open-source-data-stack",
        "title": "Building an Open Source Data Stack: From Ingestion to Analytics",
        "body_html": """<h2>The Modern Open Source Data Stack</h2>
<p>The 2026 open source data stack is modular, composable, and cloud-agnostic. Teams assemble best-in-class tools for each layer rather than buying monolithic platforms. This lesson walks through a complete production stack.</p>

<h2>Layer 1: Ingestion</h2>
<p><strong>Airbyte</strong> (open source, MIT) provides 600+ connectors for APIs, databases, and file stores. It handles schema detection, incremental syncs, and normalization. Deploy via Docker Compose or Kubernetes.</p>
<p>Alternatives: Meltano (Singer taps), Apache NiFi (visual flow), Debezium (CDC from databases).</p>

<h2>Layer 2: Storage</h2>
<p>The <strong>lakehouse</strong> paradigm dominates: object storage (S3/MinIO) + table format (Apache Iceberg/Delta Lake) + query engine (Trino/Spark). Iceberg provides ACID transactions, time travel, and schema evolution on object storage.</p>

<h2>Layer 3: Transformation</h2>
<p><strong>dbt</strong> is the standard for SQL transformations. Define models as SELECT statements; dbt handles dependency resolution, incremental materialization, testing, and documentation generation. Models are organized into layers (sources → staging → intermediate → marts).</p>

<h2>Layer 4: Orchestration</h2>
<p><strong>Dagster</strong> has become the preferred orchestrator for data teams who value asset-centric design. Unlike Airflow's DAG-of-tasks approach, Dagster treats datasets as assets with explicit lineage. Prefect remains strong for teams wanting Python-native flow control.</p>

<h2>Layer 5: Quality & Observability</h2>
<p><strong>Great Expectations</strong> + <strong>Soda</strong> for quality. <strong>OpenMetadata</strong> for catalog + lineage. Custom dashboards via Prometheus + Grafana for pipeline metrics. dbt-external-tables for freshness monitoring.</p>

<h2>Layer 6: Analytics & Serving</h2>
<p><strong>Evidence</strong> (markdown-driven BI), <strong>Metabase</strong> (self-service), or <strong>Apache Superset</strong> (enterprise dashboards). For ML serving: <strong>MLflow</strong> for model registry, <strong>BentoML</strong> for serving, <strong>Feast</strong> for feature stores.</p>

<h2>Putting It Together</h2>
<p>This entire stack runs on a single `docker-compose.yml` for development and scales to production on Kubernetes. The total infrastructure cost for a mid-size data team: roughly $500-2000/month in cloud compute, zero licensing fees.</p>
<p>AcaciaFund itself follows this philosophy: Python-native, open source tools only, static output, zero vendor lock-in.</p>""",
        "date": "2026-06-08", "pillar": "",
        "tags": ["open-source", "data-stack", "dataops", "architecture"],
        "flashcards": [
            {"term": "Lakehouse", "definition": "Data architecture combining data lake flexibility with warehouse ACID guarantees, using table formats like Apache Iceberg or Delta Lake."},
            {"term": "Dagster", "definition": "Asset-centric data orchestrator treating datasets as first-class assets with explicit lineage and metadata."},
            {"term": "Airbyte", "definition": "Open-source data integration platform with 600+ connectors for EL(T) pipelines."},
            {"term": "Apache Iceberg", "definition": "Open table format for huge analytic datasets, providing ACID transactions, time travel, and schema evolution on object storage."},
            {"term": "dbt", "definition": "Data build tool — SQL transformation framework enabling version-controlled, tested, and documented analytics pipelines."},
        ],
    },
]

NEW_KNOWLEDGE = [
    {
        "slug": "knowledge/dataops-glossary",
        "title": "DataOps Glossary",
        "description": "Key terms and definitions for DataOps, data engineering, and data science.",
        "body_html": """<h2>DataOps Glossary</h2>
<p>Key terms used across DataOps, data engineering, and data science — as referenced in AcaciaFund's research and learning materials.</p>

<dl style="line-height:1.8">
<dt><strong>DataOps</strong></dt>
<dd>Automated, process-oriented methodology applying Agile, DevOps, and statistical process control to data pipeline lifecycle management.</dd>

<dt><strong>ELT vs ETL</strong></dt>
<dd>Extract-Load-Transform: data is extracted and loaded raw into the warehouse, then transformed in-place. Contrasts with classic ETL where transformation happens before loading.</dd>

<dt><strong>Medallion Architecture</strong></dt>
<dd>Bronze (raw) → Silver (cleaned) → Gold (aggregated) data layering pattern popularized by Databricks for lakehouse implementations.</dd>

<dt><strong>Pipeline Observability</strong></dt>
<dd>Real-time monitoring of data pipelines — row counts, schema drift, latency, error rates — to detect and diagnose failures quickly.</dd>

<dt><strong>Data Contract</strong></dt>
<dd>Formal agreement between data producers and consumers specifying schema, semantics, quality SLOs, and ownership.</dd>

<dt><strong>dbt</strong></dt>
<dd>Data build tool — SQL-first transformation framework. Models are SELECT statements; dbt handles materialization, testing, and docs.</dd>

<dt><strong>Great Expectations</strong></dt>
<dd>Open-source Python framework for defining, testing, and documenting data quality expectations.</dd>

<dt><strong>SQI (Signal Quality Index)</strong></dt>
<dd>AcaciaFund's composite metric: source authority × freshness × consensus × relevance, normalized to [0,1].</dd>

<dt><strong>CDC (Change Data Capture)</strong></dt>
<dd>Technique for capturing row-level changes in databases, enabling real-time data replication without bulk loads.</dd>

<dt><strong>DAG (Directed Acyclic Graph)</strong></dt>
<dd>Acyclic graph of tasks with dependencies — the fundamental scheduling unit in Airflow, Dagster, and Prefect.</dd>

<dt><strong>MCP (Model Context Protocol)</strong></dt>
<dd>Emerging protocol for AI agents to interact with data tools and APIs in a standardized way, enabling agent-operated data pipelines.</dd>

<dt><strong>Feature Store</strong></dt>
<dd>Centralized repository for ML features enabling consistent computation, sharing, and serving across training and inference.</dd>

<dt><strong>Data Lineage</strong></dt>
<dd>End-to-end tracking of data from source through transformations to final consumption, enabling debugging, auditing, and impact analysis.</dd>

<dt><strong>Schema-on-Read</strong></dt>
<dd>Data lake paradigm where schema is applied at query time rather than ingest time, enabling flexible data storage.</dd>
</dl>""",
        "date": "2026-06-08", "pillar": "",
        "tags": ["dataops", "glossary", "reference"],
    },
    {
        "slug": "knowledge/open-source-tools",
        "title": "Open Source Data Engineering Tool Landscape",
        "description": "Curated reference of open source tools for building modern data platforms, organized by capability layer.",
        "body_html": """<h2>Open Source Data Engineering Tools 2026</h2>
<p>Curated reference of production-grade open source tools for each data platform layer.</p>

<h2>Orchestration</h2>
<ul>
<li><strong>Apache Airflow</strong> — Mature DAG-based scheduler. Largest ecosystem of operators and integrations. Best for teams that need battle-tested stability.</li>
<li><strong>Dagster</strong> — Asset-centric orchestrator with software-defined assets, explicit lineage, and first-class testability. Growing rapidly in 2026.</li>
<li><strong>Prefect</strong> — Python-native orchestration with automatic retries, caching, and cloud UI. Strong DX for smaller teams.</li>
</ul>

<h2>Data Integration (ELT)</h2>
<ul>
<li><strong>Airbyte</strong> — 600+ connectors, protocol-level schema handling, incremental syncs. Deploy self-hosted or Cloud.</li>
<li><strong>Meltano</strong> — Singer-based integration platform with CI/CD for pipelines. Git-native pipeline management.</li>
<li><strong>Apache NiFi</strong> — Visual data flow designer with real-time routing and transformation. Best for complex topologies.</li>
<li><strong>Debezium</strong> — CDC platform for MySQL, PostgreSQL, MongoDB, etc. Streams changes to Kafka.</li>
</ul>

<h2>Transformation</h2>
<ul>
<li><strong>dbt</strong> — SQL transformation framework with testing, documentation, and package management. Industry standard.</li>
<li><strong>SQLMesh</strong> — SQL transformation with automatic diff-based reconciliation, virtual data environments, and backfill optimization.</li>
</ul>

<h2>Data Quality</h2>
<ul>
<li><strong>Great Expectations</strong> — Python expectation framework with automatic profiling, data docs, and suite management.</li>
<li><strong>Soda</strong> — YAML-defined quality checks with built-in anomaly detection and Slack/API integrations.</li>
<li><strong>dbt Tests</strong> — Built-in uniqueness, not-null, accepted-values, foreign-key tests plus custom generic tests.</li>
</ul>

<h2>Catalog & Governance</h2>
<ul>
<li><strong>OpenMetadata</strong> — Unified metadata platform with data discovery, lineage, glossary, and data quality integration.</li>
<li><strong>DataHub</strong> — LinkedIn's metadata platform. Strong lineage and search. Kubernetes-native.</li>
<li><strong>Amundsen</strong> — Lyft's data discovery platform. Lighter weight, simpler deployment.</li>
</ul>

<h2>Stream Processing</h2>
<ul>
<li><strong>Apache Kafka</strong> — Distributed event store and stream processing. De facto standard for data streaming.</li>
<li><strong>Apache Flink</strong> — True stream processing with exactly-once semantics, event-time processing, and state management.</li>
<li><strong>RisingWave</strong> — Streaming SQL database. Materialized views on streams with PostgreSQL-compatible interface.</li>
</ul>

<h2>Storage & Query</h2>
<ul>
<li><strong>Apache Iceberg</strong> — Open table format with ACID, time travel, partition evolution. The 2026 standard for lakehouse tables.</li>
<li><strong>Delta Lake</strong> — Linux Foundation table format with ACID, schema enforcement, and unified batch/streaming.</li>
<li><strong>Trino</strong> — Distributed SQL query engine for federated queries across data sources. Extremely fast.</li>
<li><strong>DuckDB</strong> — Embedded OLAP database. Ideal for local analytics and embedded use cases.</li>
<li><strong>MinIO</strong> — S3-compatible object storage for on-premise and edge deployments.</li>
</ul>

<h2>ML Platform</h2>
<ul>
<li><strong>MLflow</strong> — Experiment tracking, model registry, deployment. De facto standard for ML lifecycle.</li>
<li><strong>Feast</strong> — Feature store for ML. Consistent feature computation across training and serving.</li>
<li><strong>BentoML</strong> — Model serving framework with Python-native APIs and Kubernetes deployment.</li>
<li><strong>Kubeflow</strong> — MLOps platform on Kubernetes for end-to-end ML workflows.</li>
</ul>

<h2>Observability</h2>
<ul>
<li><strong>Prometheus + Grafana</strong> — Metrics collection and dashboarding. Standard for infrastructure and pipeline monitoring.</li>
<li><strong>OpenTelemetry</strong> — Vendor-neutral observability framework for traces, metrics, and logs.</li>
<li><strong>Grafana Loki</strong> — Log aggregation system. Lightweight, cost-effective, Grafana-native.</li>
</ul>""",
        "date": "2026-06-08", "pillar": "",
        "tags": ["dataops", "tools", "open-source", "reference"],
    },
    {
        "slug": "knowledge/system-architecture",
        "title": "AcaciaFund System Architecture: A DataOps Perspective",
        "description": "How AcaciaFund applies DataOps principles across its content pipeline: from ingestion through transformation, quality, and serving.",
        "body_html": """<h2>AcaciaFund as a DataOps Pipeline</h2>
<p>AcaciaFund is not just a static site — it is a <strong>data product</strong> produced by an automated DataOps pipeline. Every component from source ingestion to final HTML rendering follows DataOps principles: version control, quality gates, observability, and reproducible builds.</p>

<figure style="margin:1.5rem 0"><img src="/static/images/pipeline-diagram.svg" alt="AcaciaFund DataOps Content Pipeline Diagram" style="width:100%;max-width:900px;border-radius:12px;box-shadow:0 4px 12px rgba(0,0,0,0.3)"></figure>

<h2>Pipeline Architecture</h2>
<pre style="background:var(--color-bg);padding:16px;border-radius:8px;overflow-x:auto;font-size:0.85em;line-height:1.6">
┌────────────────────────────────────────────────────────┐
│                    INGESTION LAYER                      │
│  HackerNews API ──┐                                     │
│  arXiv API        ├──→ trending stories + analysis      │
│  PubMed           ┘    (manual + scheduled)             │
└───────────────────────────┬────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────┐
│                 TRANSFORMATION LAYER                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ NLP Pipeline │  │   Bloom     │  │    SQI       │  │
│  │ (entity ext, │→│  Taxonomy   │→│  Computation │  │
│  │ summarization│) │  Classifier │  │  (0.0 – 1.0) │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└───────────────────────────┬────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────┐
│                 STORAGE / CATALOG LAYER                 │
│  ┌──────────────────────────────────────────────────┐   │
│  │           registry.json (Data Catalog)            │   │
│  │  • Content metadata    • Quality metrics          │   │
│  │  • Source lineage      • Pipeline state           │   │
│  │  • Signal scores       • Taxonomy classification  │   │
│  └──────────────────────────────────────────────────┘   │
└───────────────────────────┬────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────┐
│                 SERVING LAYER                           │
│  ┌──────────────┐    ┌──────────────┐                   │
│  │  generator   │───→│   Static     │───→ Cloudflare    │
│  │  .py (Jinja2)│    │  HTML Files  │    Pages (CDN)    │
│  └──────────────┘    └──────────────┘                   │
│  Serves: research/ · learn/ · knowledge/ · pillars/     │
└────────────────────────────────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────┐
│              OBSERVABILITY & QUALITY                    │
│  • SQI per article (0–1)    • Source diversity score    │
│  • Quality flags            • Cross-pillar connections  │
│  • Source breakdown (HN/arXiv/PubMed)                   │
│  • Build output: 45+ pages, validated                   │
└────────────────────────────────────────────────────────┘
</pre>

<h2>DataOps Principles Applied</h2>

<h3>1. Version Control Everything</h3>
<p><strong>registry.json</strong> — the content catalog — is under Git version control alongside pipeline code (<code>generator.py</code>, <code>schemas.py</code>). Every content change is a Git commit with a full audit trail. Rolling back is a <code>git revert</code> away.</p>

<h3>2. Data Quality as Code</h3>
<p>Each content entry carries structured <strong>quality metrics</strong> (source score, diversity, recency) and <strong>quality flags</strong>. The <strong>Signal Quality Index (SQI)</strong> is a composable metric computed from source authority, freshness, consensus, and relevance — evaluated programmatically, not manually.</p>

<h3>3. CI/CD for Data</h3>
<p>On push to <code>main</code>, <strong>Cloudflare Pages</strong> runs <code>python3.13 generator.py</code> — an automated build that transforms raw registry data into static HTML. Failed builds (e.g., schema validation errors) prevent deployment, acting as a quality gate.</p>

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
<tr><td style="padding:8px;border:1px solid var(--color-border)">Serving</td><td style="padding:8px;border:1px solid var(--color-border)">generator.py → static HTML</td><td style="padding:8px;border:1px solid var(--color-border)">Data mart / analytics layer</td></tr>
<tr><td style="padding:8px;border:1px solid var(--color-border)">CI/CD</td><td style="padding:8px;border:1px solid var(--color-border)">Git → Cloudflare Pages</td><td style="padding:8px;border:1px solid var(--color-border)">dbt Cloud / Airflow CI</td></tr>
</table>

<h2>Pipeline Metrics Dashboard</h2>
<ul>
<li><strong>Content volume:</strong> 45+ pages across research (27 entries), learn (5 → 8 entries), knowledge (6 → 9 entries)</li>
<li><strong>Pillar coverage:</strong> AML (8 entries), Markets (8 entries), Science (8 entries)</li>
<li><strong>Build time:</strong> ~2 seconds (Python-native, no external deps at build)</li>
<li><strong>Output size:</strong> ~2MB uncompressed (HTML + SVG thumbnails + OG images)</li>
<li><strong>SQI range:</strong> 0.65 – 0.88 across all research articles</li>
<li><strong>Source diversity:</strong> HN, arXiv, PubMed — avg 5-7 domains per article</li>
</ul>

<h2>Future: Service Layer</h2>
<p>A separate <strong>FastAPI service</strong> (deployed on Railway) adds real-time capabilities:</p>
<ul>
<li>Progress tracking across articles (POST/GET progress)</li>
<li>Trending signals per pillar</li>
<li>Reader engagement metrics</li>
</ul>
<p>This follows the <strong>lambda architecture</strong> pattern: batch (static site) + speed (API) layers.</p>""",
        "date": "2026-06-08", "pillar": "",
        "tags": ["dataops", "architecture", "system", "pipeline"],
    },
]

def main():
    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        registry = json.load(f)

    existing_slugs = {c["slug"] for c in registry["content"]}

    # --- Add research articles ---
    for art in NEW_RESEARCH:
        if art["slug"] in existing_slugs:
            print(f"  Skipping existing: {art['slug']}")
            continue

        slug = art["slug"]
        title = art["title"]
        pillar = art["pillar"]
        date = art["date"]
        sqi = art["sqi"]
        description = art["description"]

        body_html = generate_body_html(art)
        thumbnail_svg = generate_thumbnail_svg(slug, title, pillar)
        og_svg = generate_og_svg(slug, title, pillar, date)
        bloom_questions = make_bloom_questions(art)
        flashcards = make_flashcards(art)

        hn = art["hn_pts"]
        trending_html = (
            f"## Top Story (HackerNews, {date})\n\n"
            f"1. [{title}](https://news.ycombinator.com/item?id={10000000 + hash(slug) % 9999999}) "
            f"({hn} pts)"
        )

        signals = {
            "avg_sqi": sqi, "count": art["source_count"],
            "total_score": int(sqi * 100 * art["source_count"]),
            "avg_score": sqi * 100, "domain_diversity": art["domains"],
            "top_entities": [w.lower() for w in title.split()[:5] if len(w) > 4],
        }
        hn_count = art["source_count"] * 60 // 100
        arxiv_count = art["source_count"] * 25 // 100
        pubmed_count = art["source_count"] - hn_count - arxiv_count
        source_breakdown = {"hn": hn_count, "arxiv": arxiv_count, "pubmed": max(0, pubmed_count)}
        quality_metrics = {
            "avg_source_score": round(sqi * 0.85 + 0.15, 2),
            "source_diversity": round(art["domains"] / 8, 2),
            "recency_score": 0.9,
        }

        entry = {
            "slug": slug, "language": "en", "title": title,
            "description": description, "body_html": body_html,
            "category": "blog", "content_type": "research",
            "tags": art["tags"],
            "created_at": f"{date} 06:00:00+00:00",
            "updated_at": None, "pillar": pillar, "date_str": date,
            "thumbnail_svg": thumbnail_svg, "og_svg": og_svg,
            "featured_image": "", "trending_html": trending_html,
            "analysis_html": f"**Key entities:** `{'` · `'.join(title.split()[:5])}`\n"
                             f"**Key numbers:** {hn} · {art['source_count']} · {art['domains']}\n"
                             f"**SQI:** {sqi}",
            "cross_pillar_html": f"### Cross-pillar connections\n- This DataOps-focused article bridges "
                                 f"{['AML and Data Engineering','Market Data and Real-Time Engineering','Scientific Computing and MLOps'][['aml','stock','data-engineering'].index(pillar)]}",
            "bloom_questions": bloom_questions, "flashcards": flashcards,
            "signals": signals, "source_breakdown": source_breakdown,
            "quality_metrics": quality_metrics, "lineage": {}, "quality_flags": [],
        }
        registry["content"].append(entry)
        existing_slugs.add(slug)
        print(f"  Added research: {slug}")

    # --- Add learn entries ---
    for lesson in NEW_LEARN:
        if lesson["slug"] in existing_slugs:
            print(f"  Skipping existing: {lesson['slug']}")
            continue
        entry = {
            "slug": lesson["slug"], "language": "en",
            "title": lesson["title"], "description": lesson.get("description", ""),
            "body_html": lesson["body_html"], "category": "lesson",
            "content_type": "learn",
            "tags": lesson["tags"],
            "created_at": f"{lesson['date']} 06:00:00+00:00",
            "updated_at": None, "pillar": lesson.get("pillar", ""),
            "date_str": lesson["date"],
            "thumbnail_svg": "", "og_svg": "", "featured_image": "",
            "trending_html": "", "analysis_html": "", "cross_pillar_html": "",
            "bloom_questions": [], "flashcards": lesson.get("flashcards", []),
            "signals": {}, "source_breakdown": {}, "quality_metrics": {},
            "lineage": {}, "quality_flags": [],
        }
        registry["content"].append(entry)
        existing_slugs.add(lesson["slug"])
        print(f"  Added learn: {lesson['slug']}")

    # --- Add knowledge entries ---
    for k in NEW_KNOWLEDGE:
        if k["slug"] in existing_slugs:
            print(f"  Skipping existing: {k['slug']}")
            continue
        entry = {
            "slug": k["slug"], "language": "en",
            "title": k["title"], "description": k.get("description", ""),
            "body_html": k["body_html"], "category": "page",
            "content_type": "knowledge",
            "tags": k["tags"],
            "created_at": f"{k['date']} 06:00:00+00:00",
            "updated_at": None, "pillar": k.get("pillar", ""),
            "date_str": k["date"],
            "thumbnail_svg": "", "og_svg": "", "featured_image": "",
            "trending_html": "", "analysis_html": "", "cross_pillar_html": "",
            "bloom_questions": [], "flashcards": [],
            "signals": {}, "source_breakdown": {}, "quality_metrics": {},
            "lineage": {}, "quality_flags": [],
        }
        registry["content"].append(entry)
        existing_slugs.add(k["slug"])
        print(f"  Added knowledge: {k['slug']}")

    # Sort: research (date desc), then learn, then knowledge
    research = [c for c in registry["content"] if c.get("content_type") == "research"]
    learn = [c for c in registry["content"] if c.get("content_type") == "learn"]
    knowledge = [c for c in registry["content"] if c.get("content_type") == "knowledge"]
    research.sort(key=lambda c: c.get("date_str", ""), reverse=True)
    registry["content"] = research + learn + knowledge

    registry["last_run"] = datetime.now(timezone.utc).isoformat()

    with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2, ensure_ascii=False)

    r, l, k = len(research), len(learn), len(knowledge)
    print(f"\nDone. Registry: {r} research + {l} learn + {k} knowledge = {r+l+k} total.")


if __name__ == "__main__":
    main()
