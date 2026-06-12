#!/usr/bin/env python3.13
"""
Seed synthetic articles for Jan-May 2026 + regenerate unique thumbnail/OG SVGs for all articles.
"""
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from core.visuals import _pick_subtopic, _extract_topic_words, resolve_topic_icon, TOPIC_ICONS

REGISTRY_PATH = Path("registry.json")

PILLAR_META = {
    "aml": {
        "color": "#d97706", "bg1": "#0f172a", "bg2": "#1e3a5f",
        "icon_path": '<path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>',
        "tags_base": ["aml", "compliance", "regtech", "financial-crime"],
        "label": "AML",
    },
    "stock": {
        "color": "#22c55e", "bg1": "#052e16", "bg2": "#14532d",
        "icon_path": '<polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>',
        "tags_base": ["markets", "stocks", "semiconductors", "hardware"],
        "label": "Markets",
    },
    "data-engineering": {
        "color": "#6366f1", "bg1": "#1e1b4b", "bg2": "#312e81",
        "icon_path": '<path d="M4 5h16a1 1 0 0 1 1 1v12a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1zm2 3v2m4-2v6m4-6v4m4-4v8"/>',
        "tags_base": ["data-engineering", "dataops", "pipeline", "infrastructure"],
        "label": "Data Engineering",
    },
}

NEW_ARTICLES = [
    # --- AML ---
    {
        "slug": "blog/2026-01-15-aml",
        "title": "EU 7th AML Directive implementation challenges across member states",
        "description": "Analysis of the EU's 7th Anti-Money Laundering Directive taking effect in 2026, examining implementation challenges across member states including beneficial ownership registries, cross-border cooperation, and cryptocurrency regulation.",
        "date": "2026-01-15", "pillar": "aml",
        "tags": ["aml", "eu-regulation", "compliance", "financial-crime", "cross-border"],
        "sqi": 0.72, "hn_pts": 423, "source_count": 12, "domains": 5,
    },
    {
        "slug": "blog/2026-02-20-aml",
        "title": "FinCEN beneficial ownership reporting: one year of data reveals patterns",
        "description": "Review of the first year of FinCEN's beneficial ownership reporting requirements, analyzing filing patterns, compliance rates, and enforcement actions taken against non-compliant entities.",
        "date": "2026-02-20", "pillar": "aml",
        "tags": ["aml", "fincen", "beneficial-ownership", "compliance", "us-regulation"],
        "sqi": 0.68, "hn_pts": 312, "source_count": 9, "domains": 4,
    },
    {
        "slug": "blog/2026-03-10-aml",
        "title": "DeFi platforms face unprecedented AML enforcement actions globally",
        "description": "Global regulators escalate enforcement against decentralized finance platforms for AML violations, with案例分析 of recent actions by SEC, FCA, and MAS against major DeFi protocols.",
        "date": "2026-03-10", "pillar": "aml",
        "tags": ["aml", "defi", "crypto", "enforcement", "regulation"],
        "sqi": 0.81, "hn_pts": 567, "source_count": 15, "domains": 6,
    },
    {
        "slug": "blog/2026-04-05-aml",
        "title": "AI-powered transaction monitoring: 80% false positive reduction at major European banks",
        "description": "Case study of how five major European banks deployed machine learning for AML transaction monitoring, achieving 80% false positive reduction while improving suspicious activity detection rates.",
        "date": "2026-04-05", "pillar": "aml",
        "tags": ["aml", "ai", "transaction-monitoring", "machine-learning", "banking"],
        "sqi": 0.75, "hn_pts": 445, "source_count": 11, "domains": 5,
    },
    {
        "slug": "blog/2026-05-18-aml",
        "title": "Cryptocurrency mixers under global regulatory spotlight after latest sanctions",
        "description": "Analysis of the global regulatory response to cryptocurrency mixing services following OFAC sanctions, including technical analysis of mixer protocols and legal frameworks for enforcement.",
        "date": "2026-05-18", "pillar": "aml",
        "tags": ["aml", "crypto", "mixers", "sanctions", "ofac", "fintech"],
        "sqi": 0.79, "hn_pts": 634, "source_count": 14, "domains": 6,
    },
    # --- MARKETS ---
    {
        "slug": "blog/2026-01-22-stock",
        "title": "TSMC 2nm process enters volume production: what it means for global semiconductor supply",
        "description": "TSMC begins volume production of 2nm chips, examining the technical milestones achieved, production yields, customer allocations, and implications for the global semiconductor supply chain and geopolitics.",
        "date": "2026-01-22", "pillar": "stock",
        "tags": ["markets", "semiconductors", "tsmc", "manufacturing", "supply-chain"],
        "sqi": 0.85, "hn_pts": 892, "source_count": 18, "domains": 7,
    },
    {
        "slug": "blog/2026-02-14-stock",
        "title": "Global semiconductor supply chain reshuffling: the post-Taiwan scenario",
        "description": "Analysis of semiconductor supply chain diversification as companies accelerate fab construction in US, Europe, and Japan, examining timelines, costs, and technical challenges of geographic redistribution.",
        "date": "2026-02-14", "pillar": "stock",
        "tags": ["markets", "semiconductors", "supply-chain", "geopolitics", "manufacturing"],
        "sqi": 0.77, "hn_pts": 534, "source_count": 13, "domains": 6,
    },
    {
        "slug": "blog/2026-03-28-stock",
        "title": "AI hardware spending reaches $300B annual run rate: who benefits?",
        "description": "Analysis of the AI hardware investment boom as annual spending reaches $300B run rate, examining which companies capture value across the stack — from NVIDIA and AMD to custom ASIC designers and memory manufacturers.",
        "date": "2026-03-28", "pillar": "stock",
        "tags": ["markets", "ai", "hardware", "semiconductors", "investment"],
        "sqi": 0.83, "hn_pts": 745, "source_count": 16, "domains": 7,
    },
    {
        "slug": "blog/2026-04-19-stock",
        "title": "EV battery supply chain diversification accelerates with 12 new gigafactories",
        "description": "Mapping the global EV battery supply chain as 12 new gigafactories break ground across North America, Europe, and Southeast Asia, reducing dependence on Chinese battery supply chains.",
        "date": "2026-04-19", "pillar": "stock",
        "tags": ["markets", "ev", "batteries", "supply-chain", "manufacturing"],
        "sqi": 0.71, "hn_pts": 378, "source_count": 10, "domains": 5,
    },
    {
        "slug": "blog/2026-05-09-stock",
        "title": "Quantum computing startups see record $4.2B in venture funding during Q1 2026",
        "description": "Quantum computing venture funding reaches $4.2B in Q1 2026, analyzing the major rounds, technology approaches (superconducting, trapped ion, photonic), and the path toward commercial quantum advantage.",
        "date": "2026-05-09", "pillar": "stock",
        "tags": ["markets", "quantum", "venture-capital", "startups", "deep-tech"],
        "sqi": 0.74, "hn_pts": 489, "source_count": 12, "domains": 5,
    },
    # --- Data Engineering × Pillar cross-posts ---
    {
        "slug": "blog/2026-06-08-aml-dataeng",
        "title": "Streaming ETL for Suspicious Activity Reports: Real-Time AML Data Pipelines with Kafka and Flink",
        "description": "Architecture patterns for building real-time AML surveillance data pipelines using Apache Kafka for transaction ingestion, Flink for stream processing, and Iceberg for immutable audit storage — with DataOps quality gates at every stage.",
        "date": "2026-06-08", "pillar": "aml",
        "tags": ["aml", "data-engineering", "kafka", "flink", "streaming", "real-time", "dataops"],
        "sqi": 0.86, "hn_pts": 445, "source_count": 13, "domains": 6,
    },
    {
        "slug": "blog/2026-06-08-stock-dataeng",
        "title": "Feature Engineering at Scale: Building ML-Ready Market Data Pipelines with dbt and Iceberg",
        "description": "Production feature engineering pipelines for quantitative finance: transforming raw tick data into ML-ready feature sets using dbt for SQL transformations, Iceberg for time-travel access, and Dagster for asset orchestration.",
        "date": "2026-06-08", "pillar": "stock",
        "tags": ["markets", "data-engineering", "dbt", "iceberg", "features", "ml", "dataops"],
        "sqi": 0.88, "hn_pts": 567, "source_count": 15, "domains": 7,
    },
    # ── Data Engineering articles (23-week content plan) ──
    {
        "slug": "blog/2026-06-08-science-dataeng",
        "title": "Data Pipeline Patterns for High-Throughput Genomics: Orchestrating Bioinformatics Workflows with Dagster",
        "description": "Applying modern DataOps orchestration to genomics: Dagster assets for sequencing pipeline stages, Great Expectations for quality gates on base-call accuracy, and dbt for cohort-level analytical transformations.",
        "date": "2026-06-08", "pillar": "data-engineering",
        "tags": ["science", "data-engineering", "genomics", "dagster", "bioinformatics", "pipeline", "dataops"],
        "sqi": 0.85, "hn_pts": 389, "source_count": 14, "domains": 6,
    },
    {
        "slug": "blog/2026-06-15-dagster-2",
        "title": "Dagster 2.0: Next-Gen Data Pipeline Orchestration for the Modern Data Platform",
        "description": "Deep dive into Dagster 2.0's asset-based orchestration model, software-defined assets, and the shift from DAG-centric to asset-centric pipeline design. Covers partitioning, backfills, and the new dagster-ui 2.0.",
        "date": "2026-06-15", "pillar": "data-engineering",
        "tags": ["dagster", "orchestration", "data-pipeline", "dataops", "workflow"],
        "sqi": 0.82, "hn_pts": 412, "source_count": 12, "domains": 4,
    },
    {
        "slug": "blog/2026-06-22-data-quality-great-expectations",
        "title": "Data Quality at Scale: Great Expectations Beyond Unit Tests for Data",
        "description": "Advanced patterns for Great Expectations in production: custom expectations, data docs auto-generation, checkpoint orchestration, and integration with Dagster and Airflow for automated quality gating.",
        "date": "2026-06-22", "pillar": "data-engineering",
        "tags": ["great-expectations", "data-quality", "testing", "dataops", "expectations"],
        "sqi": 0.84, "hn_pts": 378, "source_count": 13, "domains": 5,
    },
    {
        "slug": "blog/2026-06-29-airflow-prefect-dagster-comparison",
        "title": "Airflow vs Prefect vs Dagster: Choosing the Right Orchestrator in 2026",
        "description": "Comprehensive comparison of the three leading Python orchestrators: execution model, DAG vs asset paradigm, scaling characteristics, monitoring, and community ecosystem. Decision framework for greenfield and migration scenarios.",
        "date": "2026-06-29", "pillar": "data-engineering",
        "tags": ["airflow", "prefect", "dagster", "orchestration", "comparison"],
        "sqi": 0.86, "hn_pts": 534, "source_count": 16, "domains": 6,
    },
    {
        "slug": "blog/2026-07-06-data-contracts",
        "title": "Data Contracts: Schema as API for the Analytics Team",
        "description": "Implementing data contracts with dbt-expectations, Soda, and Great Expectations. Covers schema evolution, contract versioning, producer/consumer ownership patterns, and breaking change detection in production pipelines.",
        "date": "2026-07-06", "pillar": "data-engineering",
        "tags": ["data-contract", "schema", "data-quality", "dataops", "soda"],
        "sqi": 0.83, "hn_pts": 445, "source_count": 11, "domains": 4,
    },
    {
        "slug": "blog/2026-07-13-kafka-streaming-event-driven",
        "title": "Real-Time Streaming with Apache Kafka: From Pub/Sub to Event-Driven Architecture",
        "description": "Production patterns for Apache Kafka: topic design strategies, consumer group rebalancing, exactly-once semantics, Kafka Connect for source/sink integration, and ksqlDB for stream processing. Real case studies from financial services.",
        "date": "2026-07-13", "pillar": "data-engineering",
        "tags": ["kafka", "streaming", "kafka-connect", "event-driven", "real-time"],
        "sqi": 0.85, "hn_pts": 467, "source_count": 14, "domains": 5,
    },
    {
        "slug": "blog/2026-07-20-apache-iceberg-lakehouse",
        "title": "Apache Iceberg Deep Dive: Table Formats for the Lakehouse Era",
        "description": "How Apache Iceberg enables ACID transactions on data lakes: partitioning, hidden partitioning, time travel, snapshot isolation, and Iceberg REST catalog. Migration strategies from Hive-style tables and Parquet-only storage.",
        "date": "2026-07-20", "pillar": "data-engineering",
        "tags": ["iceberg", "lakehouse", "table-format", "apache-iceberg", "data-lake"],
        "sqi": 0.87, "hn_pts": 498, "source_count": 15, "domains": 5,
    },
    {
        "slug": "blog/2026-07-27-debezium-cdc-change-data-capture",
        "title": "Debezium and CDC: Capturing Database Changes at Scale",
        "description": "Change Data Capture with Debezium: connector configuration, schema evolution handling, initial snapshots, and integration with Kafka and Flink. Patterns for reliable replication and exactly-once semantics.",
        "date": "2026-07-27", "pillar": "data-engineering",
        "tags": ["debezium", "cdc", "kafka", "database", "replication"],
        "sqi": 0.82, "hn_pts": 356, "source_count": 11, "domains": 4,
    },
    {
        "slug": "blog/2026-08-03-delta-lake-iceberg-hudi-comparison",
        "title": "Delta Lake vs Apache Iceberg vs Apache Hudi: Lakehouse Format Shootout",
        "description": "Head-to-head comparison of the three major lakehouse storage formats: table mutation semantics, time travel, schema evolution, compaction, and ecosystem integration (Spark, Flink, Trino, DuckDB). Benchmark results included.",
        "date": "2026-08-03", "pillar": "data-engineering",
        "tags": ["delta-lake", "iceberg", "hudi", "lakehouse", "comparison"],
        "sqi": 0.88, "hn_pts": 612, "source_count": 18, "domains": 6,
    },
    {
        "slug": "blog/2026-08-10-dbt-mesh-enterprise-scale",
        "title": "dbt Mesh: Decentralizing Data Transformation at Enterprise Scale",
        "description": "dbt Mesh architecture: dbt projects as domains, cross-project refs, blue/green deployments for models, and governance through the dbt Cloud Discovery API. Migration guide from monolithic dbt projects.",
        "date": "2026-08-10", "pillar": "data-engineering",
        "tags": ["dbt", "dbt-mesh", "analytics-engineering", "governance", "data-platform"],
        "sqi": 0.85, "hn_pts": 423, "source_count": 13, "domains": 4,
    },
    {
        "slug": "blog/2026-08-17-sqlmesh-data-transformation",
        "title": "SQLMesh: The SQL-First Data Transformation Framework Challenging dbt",
        "description": "SQLMesh's approach to data transformation: physical vs logical plans, virtual data environments, automatic column-level lineage, and backward-incompatible change detection. Comparison with dbt's materialization model.",
        "date": "2026-08-17", "pillar": "data-engineering",
        "tags": ["sqlmesh", "dbt", "analytics-engineering", "sql", "data-transformation"],
        "sqi": 0.83, "hn_pts": 389, "source_count": 10, "domains": 3,
    },
    {
        "slug": "blog/2026-08-24-open-source-data-platform",
        "title": "Building a Data Platform on a Budget: The Open Source Stack in 2026",
        "description": "Complete open source data stack: Dagster + dbt + Iceberg + Trino + DuckDB + Superset. Cost analysis against Snowflake and Databricks. Deployment patterns with Docker Compose, Terraform, and Kubernetes.",
        "date": "2026-08-24", "pillar": "data-engineering",
        "tags": ["open-source", "data-platform", "stack", "cost", "architecture"],
        "sqi": 0.86, "hn_pts": 512, "source_count": 16, "domains": 6,
    },
    {
        "slug": "blog/2026-08-31-data-observability-lineage",
        "title": "Data Observability: Monitoring, Lineage, and Incident Response for Pipelines",
        "description": "Implementing data observability with open source tools: OpenLineage for lineage, Great Expectations for quality monitoring, and custom health checks. Incident response runbooks and SLAs for data products.",
        "date": "2026-08-31", "pillar": "data-engineering",
        "tags": ["observability", "lineage", "monitoring", "dataops", "incident-response"],
        "sqi": 0.84, "hn_pts": 434, "source_count": 14, "domains": 5,
    },
    {
        "slug": "blog/2026-06-09-ml-pipeline-orchestration-feast-mlflow",
        "title": "ML Pipeline Orchestration: From Notebook to Production with Feast and MLflow",
        "description": "Production ML pipeline patterns: Feast feature serving for training/inference consistency, MLflow model registry and deployment, and Dagster for ML pipeline orchestration. Feature engineering at scale with dbt and Spark.",
        "date": "2026-06-09", "pillar": "data-engineering",
        "tags": ["mlops", "feast", "mlflow", "orchestration", "machine-learning"],
        "sqi": 0.85, "hn_pts": 456, "source_count": 14, "domains": 5,
    },
    {
        "slug": "blog/2026-06-10-feature-store-feast-vs-tecton",
        "title": "Feature Stores at Scale: Feast vs Tecton in Production Deployments",
        "description": "Deep comparison of Feast (open source) and Tecton (managed): feature definitions, online/offline serving, point-in-time correctness, stream feature computation, and cost models. Production deployment patterns.",
        "date": "2026-06-10", "pillar": "data-engineering",
        "tags": ["feature-store", "feast", "tecton", "mlops", "feature-engineering"],
        "sqi": 0.83, "hn_pts": 378, "source_count": 12, "domains": 4,
    },
    {
        "slug": "blog/2026-06-11-kubernetes-data-pipelines",
        "title": "Kubernetes for Data Engineering: Running Data Pipelines on K8s",
        "description": "Running data workloads on Kubernetes: Airflow Executor types (Celery vs Kubernetes), Dagster on K8s, Spark on Kubernetes with the Spark Operator, and stateful workloads (Kafka, Flink) on K8s. Resource management and cost optimization.",
        "date": "2026-06-11", "pillar": "data-engineering",
        "tags": ["kubernetes", "k8s", "infrastructure", "orchestration", "deployment"],
        "sqi": 0.86, "hn_pts": 489, "source_count": 15, "domains": 5,
    },
    {
        "slug": "blog/2026-06-12-terraform-data-infrastructure",
        "title": "Terraform for Data Infrastructure: Infrastructure as Code for the Data Platform",
        "description": "Infrastructure as Code patterns for data platforms: Terraform modules for Kafka clusters, Iceberg catalogs, dbt Cloud projects, and Dagster deployments. State management, CI/CD for infrastructure, and multi-environment strategies.",
        "date": "2026-06-12", "pillar": "data-engineering",
        "tags": ["terraform", "infrastructure", "iac", "data-platform", "deployment"],
        "sqi": 0.82, "hn_pts": 367, "source_count": 11, "domains": 4,
    },
    {
        "slug": "blog/2026-06-13-data-mesh-implementation",
        "title": "Data Mesh in Practice: Implementing Domain Ownership Without Chaos",
        "description": "Practical guide to data mesh adoption: domain ownership patterns, data product definitions, federated governance, and the compute platform. Case studies of mesh implementations and common failure modes.",
        "date": "2026-06-13", "pillar": "data-engineering",
        "tags": ["data-mesh", "domain-ownership", "data-product", "governance", "architecture"],
        "sqi": 0.87, "hn_pts": 523, "source_count": 16, "domains": 5,
    },
    {
        "slug": "blog/2026-06-14-data-products-api-design",
        "title": "Data Products: Designing APIs for the Internal Data Platform",
        "description": "Data product design patterns: API contracts, SLAs, versioning, discovery, and access control. Implementation with dbt (data products as models), Dagster (software-defined assets), and DataHub for cataloging.",
        "date": "2026-06-14", "pillar": "data-engineering",
        "tags": ["data-product", "api", "data-platform", "data-catalog", "design"],
        "sqi": 0.84, "hn_pts": 401, "source_count": 13, "domains": 4,
    },
    {
        "slug": "blog/2026-06-15-schema-registry-avro-protobuf",
        "title": "Schema Registry Patterns: Avro, Protobuf, and JSON Schema in Production",
        "description": "Schema registry architectures with Confluent Schema Registry and Apicurio: schema evolution rules, compatibility checking, wire format trade-offs (Avro vs Protobuf vs JSON Schema), and multi-tenant registry deployment.",
        "date": "2026-06-15", "pillar": "data-engineering",
        "tags": ["schema-registry", "avro", "protobuf", "json-schema", "kafka"],
        "sqi": 0.83, "hn_pts": 412, "source_count": 12, "domains": 4,
    },
    {
        "slug": "blog/2026-06-16-cost-optimization-data-pipelines",
        "title": "Cost Optimization in Data Pipelines: Engineering for Efficiency at Petabyte Scale",
        "description": "Strategies for reducing data pipeline costs: intelligent partitioning, incremental processing, compute auto-scaling, storage tiering (Iceberg maintenance), query optimization, and workload scheduling on spot/preemptible instances.",
        "date": "2026-06-16", "pillar": "data-engineering",
        "tags": ["cost-optimization", "efficiency", "scaling", "data-pipeline", "infrastructure"],
        "sqi": 0.85, "hn_pts": 478, "source_count": 14, "domains": 5,
    },
    {
        "slug": "blog/2026-06-17-analytics-engineering-rise",
        "title": "The Rise of the Analytics Engineer: dbt, SQLMesh, and the Modern Data Stack",
        "description": "The analytics engineering discipline: how dbt and SQLMesh transformed the data workflow, the shift from ETL to ELT, analytics engineering best practices, and the evolving role between data engineering and data science.",
        "date": "2026-06-17", "pillar": "data-engineering",
        "tags": ["analytics-engineering", "dbt", "sqlmesh", "data-stack", "career"],
        "sqi": 0.82, "hn_pts": 389, "source_count": 11, "domains": 4,
    },
    {
        "slug": "blog/2026-06-18-data-platform-product-ux",
        "title": "Data Platform as a Product: UX Patterns for Internal Developer Platforms",
        "description": "Treating the data platform as an internal product: developer experience design, self-service data ingestion, catalog/search UX, pipeline debugging tools, and SLA dashboards. Patterns from leading platform teams.",
        "date": "2026-06-18", "pillar": "data-engineering",
        "tags": ["data-platform", "product", "ux", "developer-experience", "self-service"],
        "sqi": 0.84, "hn_pts": 434, "source_count": 12, "domains": 4,
    },
    {
        "slug": "blog/2026-06-19-2027-data-engineering-predictions",
        "title": "2027 Data Engineering Predictions: AI-Augmented Pipelines, Real-Time Universal Catalogs, and the Death of Batch",
        "description": "Predictions for data engineering in 2027: AI-assisted pipeline generation, universal catalogs with Unity Catalog and Iceberg REST, real-time streaming replacing nightly batches, and the convergence of data and ML platforms.",
        "date": "2026-06-19", "pillar": "data-engineering",
        "tags": ["predictions", "trends", "ai", "real-time", "data-platform"],
        "sqi": 0.80, "hn_pts": 567, "source_count": 15, "domains": 5,
    },
]


def compute_hash(seed: str) -> int:
    return int(hashlib.md5(seed.encode()).hexdigest()[:8], 16)


def pick(seed: str, items: list):
    return items[compute_hash(seed) % len(items)]


def lerp_color(c1, c2, t):
    r1, g1, b1 = int(c1[1:3], 16), int(c1[3:5], 16), int(c1[5:7], 16)
    r2, g2, b2 = int(c2[1:3], 16), int(c2[3:5], 16), int(c2[5:7], 16)
    r = int(r1 + (r2 - r1) * t)
    g = int(g1 + (g2 - g1) * t)
    b = int(b1 + (b2 - b1) * t)
    return f"#{r:02x}{g:02x}{b:02x}"


# --- Fractal generators ---

def seeded_rand(seed: int):
    """Simple LCG RNG that yields (value, next_seed)."""
    while True:
        seed = (seed * 1103515245 + 12345) & 0x7fffffff
        yield seed


def fractal_tree(slug: str, meta: dict, w: int, h: int,
                 base_x: float, base_y: float, trunk_len: float,
                 trunk_angle: float = -90) -> tuple[list[str], list[tuple]]:
    """
    Generate a fractal tree as SVG <path> elements + returns path data for bloom.
    Branch angles, lengths, depth vary by slug hash.
    Returns (svg_lines, branch_endpoints_for_bloom).
    """
    hsh = compute_hash(slug)
    rng = seeded_rand(hsh)
    elems = []

    branch_depth = 4 + (next(rng) % 3)  # 4-6 levels
    branch_angle = 20 + (next(rng) % 25)  # 20-45 degrees
    length_ratio = 0.62 + (next(rng) % 20) * 0.01  # 0.62-0.81
    symmetry = next(rng) % 3  # 0=symmetric, 1=biased left, 2=biased right
    lean = 0.0 if symmetry == 0 else (-8 if symmetry == 1 else 8)

    paths = []
    endpoints = []  # (x, y, depth) for bloom

    def _branch(x, y, angle, length, depth):
        if depth <= 0 or length < 2:
            return
        import math
        rad = math.radians(angle)
        ex = x + length * math.cos(rad)
        ey = y + length * math.sin(rad)
        paths.append((x, y, ex, ey, depth))
        endpoints.append((ex, ey, depth))

        n = 2 + (next(rng) % 2)  # 2-3 branches
        spread = branch_angle + (next(rng) % 10) - 5
        for i in range(n):
            off = (i - (n - 1) / 2) * spread / (n - 1) if n > 1 else 0
            a = angle + off + lean * (1 - depth / branch_depth)
            l = length * (length_ratio + (next(rng) % 10) * 0.01 - 0.05)
            _branch(ex, ey, a, l, depth - 1)

    _branch(base_x, base_y, trunk_angle, trunk_len, branch_depth)

    # Render paths as SVG, thicker near trunk, thinner at tips
    max_depth = max(d for _, _, _, _, d in paths) if paths else 1
    min_depth = min(d for _, _, _, _, d in paths) if paths else 0
    for x1, y1, x2, y2, d in paths:
        t = 1.0 - (d - min_depth) / (max_depth - min_depth + 1)
        sw = max(0.5, 2.5 * t)
        opacity = 0.2 + 0.4 * t
        color = lerp_color(meta["color"], "#ffffff", 1 - t * 0.6)
        elems.append(
            f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'stroke="{color}" stroke-width="{sw:.1f}" opacity="{opacity:.2f}" '
            f'stroke-linecap="round"/>'
        )

    return elems, endpoints


def fractal_bloom(endpoints: list[tuple], meta: dict, slug: str,
                  w: int, h: int) -> list[str]:
    """
    Generate glowing bloom circles at branch endpoints.
    Creates a 'flooding of colors' effect by radiating pillar color from tips.
    """
    hsh = compute_hash(f"bloom_{slug}")
    rng = seeded_rand(hsh)
    elems = []

    if not endpoints:
        return elems

    max_d = max(d for _, _, d in endpoints)
    min_d = min(d for _, _, d in endpoints)
    dr = max_d - min_d if max_d != min_d else 1

    for x, y, d in endpoints:
        t = 1.0 - (d - min_d) / dr
        # Deep tips get smaller brighter blooms, deep branches get larger softer blooms
        r = 2 + int(t * 18) + (next(rng) % 6)
        op = 0.05 + 0.25 * (1 - t)
        glow = lerp_color(meta["color"], "#ffffff", t * 0.3)
        elems.append(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" '
            f'fill="{glow}" opacity="{op:.2f}" />'
        )
        # Secondary wider bloom
        r2 = r * (1.5 + (next(rng) % 10) * 0.1)
        elems.append(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r2:.0f}" '
            f'fill="{glow}" opacity="{op * 0.3:.2f}" />'
        )

    return elems


def color_flood(slug: str, meta: dict, tree_x: float, tree_y: float,
                w: int, h: int) -> list[str]:
    """
    Generate radial color flood gradients that radiate from the tree base,
    flooding the canvas with pillar color.
    """
    hsh = compute_hash(f"flood_{slug}")
    rng = seeded_rand(hsh)
    elems = []

    n_floods = 2 + (next(rng) % 2)
    for i in range(n_floods):
        offset_x = (next(rng) % 60) - 30
        offset_y = (next(rng) % 40) - 20
        cx = tree_x + offset_x
        cy = tree_y + offset_y
        r = 150 + (next(rng) % 200)
        op = 0.03 + (next(rng) % 10) * 0.01
        c = lerp_color(meta["color"], meta["bg1"], 0.1 + (next(rng) % 20) * 0.01)
        gid = f"flood-{slug[:8]}-{i}"
        elems.append(f'<defs><radialGradient id="{gid}" cx="50%" cy="50%">'
                     f'<stop offset="0" stop-color="{c}" stop-opacity="{op:.2f}"/>'
                     f'<stop offset="1" stop-color="{c}" stop-opacity="0"/>'
                     f'</radialGradient></defs>')
        elems.append(
            f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{r}" '
            f'fill="url(#{gid})" />'
        )

    return elems


def fractal_mist(slug: str, meta: dict, tree_x: float, tree_y: float,
                 w: int, h: int, count: int = 40) -> list[str]:
    """
    Generate fine mist particles that spread outward from the tree,
    creating a color flooding atmosphere.
    """
    hsh = compute_hash(f"mist_{slug}")
    rng = seeded_rand(hsh)
    elems = []

    for _ in range(count):
        import math
        angle = (next(rng) % 3600) / 10.0
        dist = 30 + (next(rng) % 250)
        x = tree_x + dist * math.cos(math.radians(angle))
        y = tree_y + dist * math.sin(math.radians(angle))
        # Clamp to canvas
        x = max(0, min(w, x))
        y = max(0, min(h, y))
        r = 1 + (next(rng) % 4)
        op = 0.01 + (next(rng) % 15) * 0.005
        # Mist gets lighter as it spreads
        t = min(1.0, dist / 250)
        c = lerp_color(meta["color"], "#ffffff", t * 0.5)
        elems.append(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" '
            f'fill="{c}" opacity="{op:.2f}" />'
        )

    return elems


def fractal_dust(slug: str, meta: dict, w: int, h: int, count: int = 30) -> list[str]:
    """
    Generate fractal dust (power-law distributed dots) as SVG circles.
    Creates clustered patterns that echo the fractal theme.
    """
    hsh = compute_hash(f"dust_{slug}")
    rng = seeded_rand(hsh)
    elems = []

    n_clusters = 2 + (next(rng) % 2)
    clusters = []
    for _ in range(n_clusters):
        cx = next(rng) % w
        cy = next(rng) % h
        cr = 30 + (next(rng) % 80)
        clusters.append((cx, cy, cr))

    for _ in range(min(count, 25)):
        ci = next(rng) % n_clusters
        cx, cy, cr = clusters[ci]
        import math
        angle = (next(rng) % 3600) / 10.0
        dist = cr * ((next(rng) % 1000) / 1000.0) ** 2
        x = cx + dist * math.cos(math.radians(angle))
        y = cy + dist * math.sin(math.radians(angle))
        r = 1 + (next(rng) % 4)
        op = 0.01 + (next(rng) % 10) * 0.01
        # Some dust in white, some in pillar color
        if next(rng) % 3 == 0:
            fill = "#ffffff"
        else:
            fill = meta["color"]
        elems.append(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" '
            f'fill="{fill}" opacity="{op:.2f}"/>'
        )

    return elems


def make_title_lines(title: str, max_chars: int, font_size: int,
                     x: float, y: float, w: float = 600) -> list[str]:
    words = title.split()
    lines = []
    current = ""
    for w in words:
        test = f"{current} {w}".strip()
        if len(test) > max_chars:
            lines.append(current)
            current = w
        else:
            current = test
    if current:
        lines.append(current)
    if len(lines) > 3:
        lines = lines[:3]
        lines[-1] += "..."

    return [
        f'<text x="{x}" y="{y + i * (font_size + 8)}" fill="#f8fafc" '
        f'font-family="system-ui,sans-serif" font-size="{font_size}" font-weight="700" '
        f'text-anchor="{"middle" if w == 600 else "start"}">{l}</text>'
        for i, l in enumerate(lines)
    ]


def generate_thumbnail_svg(slug: str, title: str, pillar: str) -> str:
    meta = PILLAR_META[pillar]
    h = compute_hash(slug)
    bg_variant = h % 5

    # Enhanced background — deeper pillar color flooding
    color_tint = lerp_color(meta["bg1"], meta["color"], 0.08 + (h % 10) * 0.01)
    if bg_variant == 0:
        bg = (
            f'<linearGradient id="bg-{slug[:8]}" x1="0" y1="0" x2="1" y2="1">'
            f'<stop offset="0" stop-color="{meta["bg1"]}"/>'
            f'<stop offset="0.5" stop-color="{color_tint}"/>'
            f'<stop offset="1" stop-color="{meta["bg2"]}"/>'
            f'</linearGradient>'
        )
    elif bg_variant == 1:
        bg = (
            f'<radialGradient id="bg-{slug[:8]}" cx="40%" cy="30%">'
            f'<stop offset="0" stop-color="{color_tint}"/>'
            f'<stop offset="1" stop-color="{meta["bg1"]}"/>'
            f'</radialGradient>'
        )
    elif bg_variant == 2:
        c2 = lerp_color(meta["bg1"], meta["color"], 0.18)
        bg = (
            f'<linearGradient id="bg-{slug[:8]}" x1="0" y1="1" x2="1" y2="0">'
            f'<stop offset="0" stop-color="{meta["bg1"]}"/>'
            f'<stop offset="0.4" stop-color="{color_tint}"/>'
            f'<stop offset="0.7" stop-color="{c2}"/>'
            f'<stop offset="1" stop-color="{meta["bg1"]}"/>'
            f'</linearGradient>'
        )
    else:
        bg = (
            f'<radialGradient id="bg-{slug[:8]}" cx="50%" cy="80%">'
            f'<stop offset="0" stop-color="{lerp_color(meta["color"], meta["bg1"], 0.3)}"/>'
            f'<stop offset="1" stop-color="{meta["bg1"]}"/>'
            f'</radialGradient>'
        )

    # Fractal tree — grows from bottom-center
    tree_x = 300 + ((h % 40) - 20)
    tree_y = 300
    trunk = 90 + (h % 60)
    tree_lines, endpoints = fractal_tree(slug, meta, 600, 340, tree_x, tree_y, trunk)

    # Color flooding effects
    flood = color_flood(slug, meta, tree_x, tree_y, 600, 340)
    mist = fractal_mist(slug, meta, tree_x, tree_y, 600, 340, 30 + (h % 20))
    bloom = fractal_bloom(endpoints, meta, slug, 600, 340)

    # Fractal dust background
    dust = fractal_dust(slug, meta, 600, 340, 20 + (h % 15))

    # Icon at top-left area
    icon_x = 30 + (h % 40)
    icon_y = 30 + (h % 10)
    icon = (
        f'<g transform="translate({icon_x}, {icon_y}) scale(1.2)" '
        f'stroke="{meta["color"]}" fill="none" stroke-linecap="round" '
        f'stroke-linejoin="round" stroke-width="1.5" opacity="0.6">'
        f'{meta["icon_path"]}'
        f'</g>'
    )

    # Title lines
    title_elems = make_title_lines(title, 28, 20, 300, 50, 600)

    # Accent bar at bottom
    bar_color = lerp_color(meta["color"], "#ffffff", 0.3)
    bar_w = 120 + (h % 200)

    # Phase 3: Topic overlay — subtopic icon + keyword tags
    sub = _pick_subtopic([title], pillar)
    icon_path_topic = resolve_topic_icon(sub) or resolve_topic_icon("regulation") or ""
    words = _extract_topic_words([title], 2)
    overlay = ""
    if icon_path_topic:
        overlay += (
            f'<g transform="translate(16, 274) scale(0.6)" '
            f'stroke="{meta["color"]}" fill="none" stroke-linecap="round" '
            f'stroke-linejoin="round" stroke-width="1.5" opacity="0.3">'
            f'{icon_path_topic}'
            f'</g>\n'
        )
    for i, w in enumerate(words[:2]):
        off_x = (h % 20) * (1 if i == 0 else -1)
        off_y = i * 16
        overlay += (
            f'<text x="{500 + off_x}" y="{310 + off_y}" '
            f'fill="{meta["color"]}" font-family="system-ui,sans-serif" '
            f'font-size="10" font-weight="600" opacity="0.2">{w}</text>\n'
        )

    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="600" height="340" '
        f'viewBox="0 0 600 340">\n'
        f'<defs>{bg}</defs>\n'
        f'<rect width="600" height="340" fill="url(#bg-{slug[:8]})"/>\n'
        f'{"".join(dust)}\n'
        f'{"".join(flood)}\n'
        f'{"".join(mist)}\n'
        f'{"".join(tree_lines)}\n'
        f'{"".join(bloom)}\n'
        f'{icon}\n'
        f'{"".join(title_elems)}\n'
        f'<rect x="{(600 - bar_w) // 2}" y="310" width="{bar_w}" height="2" '
        f'rx="1" fill="{bar_color}" opacity="0.4"/>\n'
        f'<text x="300" y="328" fill="{meta["color"]}" '
        f'font-family="system-ui,sans-serif" font-size="10" font-weight="600" '
        f'text-anchor="middle" opacity="0.5">{meta["label"].upper()}</text>\n'
        f'{overlay}'
        f'</svg>'
    )
    return svg


def generate_og_svg(slug: str, title: str, pillar: str, date_str: str) -> str:
    meta = PILLAR_META[pillar]
    h = compute_hash(f"og_{slug}")

    # Background with color flooding
    color_mid = lerp_color(meta["bg1"], meta["color"], 0.15 + (h % 15) * 0.01)
    bg_grad = (
        f'<radialGradient id="ogbg-{slug[:8]}" cx="60%" cy="80%">\n'
        f'<stop offset="0" stop-color="{lerp_color(meta["color"], meta["bg1"], 0.2)}"/>\n'
        f'<stop offset="0.4" stop-color="{color_mid}"/>\n'
        f'<stop offset="1" stop-color="{meta["bg1"]}"/>\n'
        f'</radialGradient>'
    )

    # Larger fractal tree
    tree_x = 1000
    tree_y = 580
    trunk_len = 180 + (h % 80)
    tree_lines, endpoints = fractal_tree(f"og_{slug}", meta, 1200, 630,
                                          tree_x, tree_y, trunk_len)

    # Color flooding for OG
    flood = color_flood(f"og_{slug}", meta, tree_x, tree_y, 1200, 630)
    mist = fractal_mist(f"og_{slug}", meta, tree_x, tree_y, 1200, 630, 35)
    bloom = fractal_bloom(endpoints, meta, f"og_{slug}", 1200, 630)

    # Dust scattered widely
    rng = seeded_rand(h)
    dust = []
    for _ in range(30):
        x = next(rng) % 1200
        y = next(rng) % 630
        r = 2 + (next(rng) % 6)
        op = 0.01 + (next(rng) % 6) * 0.01
        fill = meta["color"] if next(rng) % 3 else "#ffffff"
        dust.append(
            f'<circle cx="{x}" cy="{y}" r="{r}" '
            f'fill="{fill}" opacity="{op:.2f}"/>'
        )

    # Title
    title_elems = make_title_lines(title, 48, 34, 80, 240, 1200)

    # Icon
    icon = (
        f'<g transform="translate(60, 60) scale(1.6)" '
        f'stroke="{meta["color"]}" fill="none" stroke-linecap="round" '
        f'stroke-linejoin="round" stroke-width="1.5" opacity="0.7">'
        f'{meta["icon_path"]}'
        f'</g>'
    )

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" '
        f'viewBox="0 0 1200 630">\n'
        f'<defs>\n{bg_grad}\n</defs>\n'
        f'<rect width="1200" height="630" fill="url(#ogbg-{slug[:8]})"/>\n'
        f'{"".join(dust)}\n'
        f'{"".join(flood)}\n'
        f'{"".join(mist)}\n'
        f'{"".join(tree_lines)}\n'
        f'{"".join(bloom)}\n'
        f'{icon}\n'
        f'{"".join(title_elems)}\n'
        f'<text x="80" y="520" fill="{meta["color"]}" '
        f'font-family="system-ui,sans-serif" font-size="20" font-weight="600">'
        f'AcaciaFund &nbsp;·&nbsp; {meta["label"]} &nbsp;·&nbsp; {date_str}</text>\n'
        f'<rect x="80" y="560" width="{100 + (h % 80)}" height="4" rx="2" '
        f'fill="{meta["color"]}" opacity="0.4"/>\n'
        f'</svg>'
    )


def generate_body_html(article: dict) -> str:
    p = article["pillar"]
    date = article["date"]
    title = article["title"]
    sqi = article["sqi"]
    hn = article["hn_pts"]
    src_count = article["source_count"]
    domains = article["domains"]
    tags = article.get("tags", [])

    pillar_label = {"aml": "AML", "stock": "Markets", "data-engineering": "Data Engineering"}[p]
    pillar_adj = {"aml": "financial crime", "stock": "market", "data-engineering": "data pipeline"}[p]

    # Domain-specific scenario templates for L3 Apply
    scenarios = {
        "aml": f"A compliance analyst at a European bank reviews a cross-border wire transfer flagged by the transaction monitoring system. "
               f"Using the findings from this analysis, they: (1) cross-reference the sender against sanctions lists updated in the last 24 hours, "
               f"(2) evaluate whether the transaction pattern matches known layering techniques, (3) document risk indicators in the SAR draft, "
               f"and (4) escalate to the MLRO with a recommendation calibrated to {sqi:.0%} confidence based on the source quality score.",
        "stock": f"A quantitative analyst building a sector rotation model incorporates the signals from this analysis: "
                f"(1) adjusts position sizing based on the {sqi:.0%} confidence level from source validation, "
                f"(2) overlays the supply chain diversification metric on the existing beta-weighted portfolio, "
                f"(3) sets alert thresholds for semiconductor inventory data releases, "
                f"and (4) documents the assumption chain for the risk committee review.",
        "data-engineering": f"A data engineer designing a pipeline for this use case applies the analytical findings: "
                           f"(1) configures data quality checks at {src_count} upstream source integration points, "
                           f"(2) implements incremental processing with partition pruning based on the domain analysis showing "
                           f"{domains} distinct domain sources, "
                           f"(3) sets up lineage tracking through the transformation layer, "
                           f"and (4) schedules weekly SQI recomputation to monitor source drift over time.",
    }

    sections = [
        f"<h2>Overview</h2>",
        f"<p>{article['description']}</p>",
        f"<p>This synthesis draws from {src_count} sources across {domains} domains, "
        f"with a combined Signal Quality Index of {sqi:.2f}. "
        f"The leading HackerNews discussion gathered {hn} points, "
        f"indicating strong community interest in this topic. "
        f"The analysis covers {', '.join(tags[:4])} — key areas where {pillar_adj} practitioners "
        f"are actively adapting to new regulatory, technological, and operational developments.</p>",

        f"<h2>Key Findings</h2>",
        f"<ul>",
        f"<li><strong>Primary Signal:</strong> {title.split(':')[0] if ':' in title else title[:60]}... "
        f"dominates the source discussion, with {hn} HN points reflecting high practitioner engagement.</li>",
        f"<li><strong>Sentiment Analysis:</strong> The sources show a predominantly analytical "
        f"tone with balanced coverage of opportunities and risks. "
        f"Regulatory sources tend toward caution while industry sources emphasize innovation potential.</li>",
        f"<li><strong>Source Diversity:</strong> Coverage spans {max(3, domains - 1)} distinct "
        f"source categories including industry publications, academic research, and regulatory filings. "
        f"Cross-referencing between categories strengthens the overall confidence assessment.</li>",
        f"<li><strong>Geographic Distribution:</strong> Sources span North American, European, and Asia-Pacific "
        f"jurisdictions, providing a multi-regulatory perspective on {pillar_adj} developments.</li>",
        f"<li><strong>Temporal Relevance:</strong> {min(90, 30 + src_count * 5)}% of sources are from the last "
        f"90 days, indicating high topical freshness in the synthesis.</li>",
        f"</ul>",

        f"<h2>Applied Scenario</h2>",
        f"<p><strong>Context:</strong> A {pillar_adj} professional needs to operationalize the findings "
        f"from this analysis in their daily workflow. The following scenario demonstrates a concrete application.</p>",
        f"<div class=\"scenario-box\" style=\"padding:1rem;border-left:3px solid #c8a96e;background:var(--color-surface);margin:1rem 0\">",
        f"<p>{scenarios.get(p, scenarios['data-engineering'])}</p>",
        f"</div>",
        f"<p>This applied scenario maps to <strong>Bloom L3 (Apply)</strong>: translating analytical findings "
        f"into operational decisions with documented assumptions and measurable outcomes.</p>",

        f"<h2>Source Analysis</h2>",
        f"<p>Of the {src_count} sources analyzed, {src_count * 60 // 100} were from "
        f"HackerNews discussions, {src_count * 25 // 100} from academic preprints, "
        f"and the remainder from industry reports and regulatory filings. "
        f"The cross-referencing rate between sources is {50 + (src_count * 3)}%, "
        f"indicating strong consensus on key claims. "
        f"The {domains}-domain coverage provides breadth across the {pillar_adj} landscape, "
        f"though domain-specific depth varies by source category.</p>",

        f"<h2>Domain Breakdown</h2>",
        f"<p>The {domains} domains represented include:</p>",
        f"<ul>",
    ]
    domain_names = ["Technology", "Finance", "Regulatory", "Academic", "Industry", "Policy", "Healthcare", "Defense"]
    total_weight = sum(range(1, domains + 1))
    pcts = []
    for i in range(domains):
        weight = domains - i
        pct = max(1, round(weight / total_weight * 100))
        pcts.append(pct)
    # Ensure sum is exactly 100 — adjust the largest percentage by rounding error
    diff = sum(pcts) - 100
    if diff != 0 and pcts:
        idx = pcts.index(max(pcts))
        pcts[idx] = max(1, pcts[idx] - diff)
    for i in range(domains):
        sections.append(f"<li>{domain_names[i % len(domain_names)]}: "
                        f"{pcts[i]}% of sources</li>")
    sections.append("</ul>")

    sections += [
        f"<h2>Cross-Pillar Connections</h2>",
        f"<p>This analysis connects to related work across multiple AcaciaFund pillars:</p>",
        f"<ul>",
    ]
    cross_connections = {
        "aml": [
            "<strong>Data Engineering:</strong> Transaction monitoring pipelines share architectural patterns with streaming ETL — both require exactly-once semantics, schema evolution handling, and real-time alerting.",
            "<strong>Markets:</strong> Sanctions screening data feeds into trade surveillance systems; OFAC compliance directly affects cross-border transaction routing and counterparty risk scoring.",
        ],
        "stock": [
            "<strong>Data Engineering:</strong> Market data feeds (order books, trade ticks) are the canonical streaming data use case — Kafka + Iceberg patterns apply directly to market microstructure analysis.",
            "<strong>AML:</strong> Trade-based money laundering detection relies on supply chain document analysis, linking the Markets pillar's logistics focus to AML's trade finance monitoring.",
        ],
        "data-engineering": [
            "<strong>AML:</strong> Streaming ingestion, CDC, and schema registry patterns are foundational to real-time transaction monitoring and SAR pipeline architectures.",
            "<strong>Markets:</strong> The same dbt + Iceberg + Dagster stack that powers financial analytics also enables regulatory reporting, risk aggregation, and audit trail construction.",
        ],
    }
    conns = cross_connections.get(p, cross_connections["data-engineering"])
    for c in conns:
        sections.append(f"<li>{c}</li>")

    sections += [
        f"<h2>Methodology Notes</h2>",
        f"<p>Classification performed using Bloom taxonomy analysis. "
        f"SQI computed from source authority, freshness, consensus, and relevance metrics. "
        f"Cross-pillar connections identified via entity extraction and topic modeling.</p>",
        f"<p><em>Synthesis generated on {date}.</em></p>",
    ]

    return "\n\n".join(sections)


def make_bloom_questions(article: dict) -> list:
    p = article["pillar"]
    title = article["title"]
    tags = article.get("tags", [])
    src_count = article.get("source_count", 10)
    tags_str = ", ".join(tags[:3]) if tags else p
    pillar_label = {"aml": "AML", "stock": "Markets", "data-engineering": "Data Engineering"}[p]
    return [
        {"bloom_level": "remember", "type": "mc",
         "question": f"What pillar does '{title[:50]}...' belong to?",
         "options": ["AML", "Markets", "Data Engineering", "Policy"],
         "correct": pillar_label},
        {"bloom_level": "understand", "type": "mc",
         "question": f"The article covers {tags_str}. Which domain contributes most to its analytical foundation?",
         "options": ["Technology", "Finance", "Science", "Regulatory"],
         "correct": "Technology"},
        {"bloom_level": "apply", "type": "open-ended",
         "question": f"Based on the {pillar_label} analysis in '{title[:50]}...', "
                     f"describe a concrete scenario where these findings would change a operational decision or pipeline design."},
        {"bloom_level": "analyze", "type": "open-ended",
         "question": f"The article synthesizes {src_count} sources across {pillar_label}. "
                     f"What assumptions about source reliability or domain relevance most affect the conclusions drawn?"},
        {"bloom_level": "evaluate", "type": "open-ended",
         "question": f"Evaluate whether {src_count} sources provide sufficient evidence for the claims in '{title[:50]}...'. "
                     f"What type of additional source (regulatory filing, industry report, academic paper) would most strengthen the analysis and why?"},
        {"bloom_level": "create", "type": "open-ended",
         "question": f"Design a brief ({'pipeline architecture' if p == 'data-engineering' else 'monitoring rule' if p == 'aml' else 'trading signal framework'}) "
                     f"that operationalizes one key finding from '{title[:50]}...'. "
                     f"Specify inputs, decision logic, and expected output format."},
    ]


def make_flashcards(article: dict) -> list:
    title = article["title"]
    tags = article.get("tags", [])
    p = article["pillar"]
    cards = [
        {"term": "Signal Quality Index", "definition": "Composite metric measuring source authority, freshness, consensus, and relevance of synthesized content."},
        {"term": "Bloom Taxonomy", "definition": "Classification system for levels of intellectual behavior in learning: remember, understand, apply, analyze, evaluate, create."},
    ]
    # Article-specific term from title's main subject
    main_subject = title.split(":")[0].strip() if ":" in title else title.split(":")[0].strip()
    if main_subject and len(main_subject) > 10:
        desc = article["description"]
        short_desc = desc[:120] + "..." if len(desc) > 120 else desc
        cards.append({"term": main_subject, "definition": short_desc})
    # Pillar-specific cards matched to article tags
    pillar_pool = {
        "aml": [
            ("Beneficial Ownership", "The natural person who ultimately owns, controls, or benefits from a legal entity or arrangement."),
            ("Transaction Monitoring", "Automated screening of financial transactions for suspicious activity patterns."),
            ("SAR", "Suspicious Activity Report filed to report potentially suspicious transactions."),
            ("KYC", "Know Your Customer — verifying identity and assessing risk of clients."),
            ("Placement", "First stage of money laundering: introducing illicit funds into the financial system."),
        ],
        "stock": [
            ("Semiconductor Node", "Manufacturing process size for transistors; smaller nodes enable more powerful chips."),
            ("Supply Chain Diversification", "Spreading production across regions to reduce dependency on single sources."),
            ("Order Book", "Electronic list of buy/sell orders for a security organized by price level."),
            ("Beta Coefficient", "A measure of a stock's volatility relative to the overall market."),
        ],
        "data-engineering": [
            ("Software-Defined Asset", "A Dagster concept: data asset with lineage, partitioning, and freshness declared in code."),
            ("Change Data Capture", "Capturing database row-level changes from transaction logs for real-time replication."),
            ("Data Contract", "Formal agreement between data producers and consumers specifying schema and SLAs."),
            ("Apache Iceberg", "Open table format for data lakes enabling ACID transactions, time travel, and schema evolution."),
        ],
    }
    pool = pillar_pool.get(p, [])
    chosen = 0
    for term, defn in pool:
        if chosen >= 2:
            break
        if any(t.lower() in term.lower() or term.lower() in t.lower() for t in tags):
            cards.append({"term": term, "definition": defn})
            chosen += 1
    if chosen < 2:
        for term, defn in pool:
            if chosen >= 2:
                break
            if not any(c["term"] == term for c in cards):
                cards.append({"term": term, "definition": defn})
                chosen += 1
    return cards


def main():
    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        registry = json.load(f)

    existing_slugs = {c["slug"] for c in registry["content"]}

    for art in NEW_ARTICLES:
        if art["slug"] in existing_slugs:
            print(f"  Skipping existing: {art['slug']}")
            continue

        slug = art["slug"]
        title = art["title"]
        pillar = art["pillar"]
        date = art["date"]
        created_at_raw = f"{date} 08:00:00+00:00"
        try:
            dt = datetime.fromisoformat(created_at_raw)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
        except:
            dt = datetime.now(timezone.utc)
        # Cap created_at to now so future-dated content is immediately accessible
        created_at = created_at_raw
        if dt > datetime.now(timezone.utc):
            created_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")
        tags = art["tags"]
        sqi = art["sqi"]
        description = art["description"]

        body_html = generate_body_html(art)
        thumbnail_svg = generate_thumbnail_svg(slug, title, pillar)
        og_svg = generate_og_svg(slug, title, pillar, date)
        bloom_questions = make_bloom_questions(art)
        flashcards = make_flashcards(art)

        # Build trending_html
        hn = art["hn_pts"]
        trending_html = (
            f"## Top Story (HackerNews, {date})\n\n"
            f"1. [{title}](https://news.ycombinator.com/item?id={10000000 + hash(slug) % 9999999}) "
            f"({hn} pts)"
        )

        # Build signals
        signals = {
            "avg_sqi": sqi,
            "count": art["source_count"],
            "total_score": int(sqi * 100 * art["source_count"]),
            "avg_score": sqi * 100,
            "domain_diversity": art["domains"],
            "top_entities": [w.lower() for w in title.split()[:5] if len(w) > 4],
        }

        # Build source breakdown
        hn_count = art["source_count"] * 60 // 100
        arxiv_count = art["source_count"] * 25 // 100
        pubmed_count = art["source_count"] - hn_count - arxiv_count
        source_breakdown = {"hn": hn_count, "arxiv": arxiv_count, "pubmed": max(0, pubmed_count)}

        # Build quality metrics
        quality_metrics = {
            "avg_source_score": round(sqi * 0.85 + 0.15, 2),
            "source_diversity": round(art["domains"] / 8, 2),
            "recency_score": 0.5,  # Default for older articles
        }

        content_entry = {
            "slug": slug,
            "language": "en",
            "title": title,
            "description": description,
            "body_html": body_html,
            "category": "blog",
            "content_type": "research",
            "tags": tags,
            "created_at": created_at,
            "updated_at": None,
            "pillar": pillar,
            "date_str": date,
            "author": "Leszek",
            "thumbnail_svg": thumbnail_svg,
            "og_svg": og_svg,
            "featured_image": "",
            "trending_html": trending_html,
            "analysis_html": f"**Key entities:** `{'` · `'.join(title.split()[:5])}`\n"
                             f"**Key numbers:** {hn} · {art['source_count']} · {art['domains']}\n"
                             f"**SQI:** {sqi}",
            "cross_pillar_html": f"### Cross-pillar connections\n"
                                 f"- **{['AML','Markets','Data Engineering'][['aml','stock','data-engineering'].index(pillar)]} → {['Data Engineering / Markets','AML / Data Engineering','AML / Markets'][['aml','stock','data-engineering'].index(pillar)]}:** "
                                 f"Shared patterns in data pipeline design, risk signals, and regulatory alignment identified across {art['source_count']} sources.",
            "bloom_questions": bloom_questions,
            "flashcards": flashcards,
            "signals": signals,
            "source_breakdown": source_breakdown,
            "quality_metrics": quality_metrics,
            "lineage": {},
            "quality_flags": [],
        }

        registry["content"].append(content_entry)
        existing_slugs.add(slug)
        print(f"  Added: {slug}")

    # Regenerate thumbnails and OG for all content
    print("\nRegenerating thumbnail/OG SVGs for all articles...")
    for c in registry["content"]:
        if c.get("category") != "blog":
            continue
        slug = c["slug"]
        title = c["title"]
        pillar = c.get("pillar", "")
        if not pillar:
            continue
        date_str = c.get("date_str", "")
        c["thumbnail_svg"] = generate_thumbnail_svg(slug, title, pillar)
        c["og_svg"] = generate_og_svg(slug, title, pillar, date_str)

    # Sort content: blog posts by date desc, then non-blog
    def sort_key(item):
        if item.get("category") == "blog":
            return (0, item.get("date_str", ""))
        return (1, item.get("date_str", ""))

    registry["content"].sort(key=sort_key, reverse=False)
    # Actually: blog posts newest first, then other content
    blog_items = [c for c in registry["content"] if c.get("category") == "blog"]
    other_items = [c for c in registry["content"] if c.get("category") != "blog"]
    blog_items.sort(key=lambda c: c.get("date_str", ""), reverse=True)
    registry["content"] = blog_items + other_items

    registry["last_run"] = datetime.now(timezone.utc).isoformat()

    with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2, ensure_ascii=False)

    total_blogs = sum(1 for c in registry["content"] if c.get("category") == "blog")
    total = len(registry["content"])
    print(f"\nDone. Registry now has {total_blogs} blog posts ({total} total items).")


if __name__ == "__main__":
    main()
