#!/usr/bin/env python3
"""Enrich data engineering items with structured metadata (technologies, use cases, prerequisites).

Reads registry.json, analyzes each data-engineering item's title, description,
tags, and body_html to extract:
  - technologies: list of tools/platforms mentioned (Kafka, Spark, dbt, etc.)
  - use_cases: list of application categories (streaming, batch, governance, etc.)

Usage:
    python3 scripts/enrich_de_metadata.py --dry-run    # preview changes (default)
    python3 scripts/enrich_de_metadata.py --apply       # write to registry.json
    python3 scripts/enrich_de_metadata.py --verbose     # per-item detail
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

logger = logging.getLogger(__name__)

# ── Technology/Product Detection Patterns ─────────────────────────────────

TECH_PATTERNS: dict[str, list[str]] = {
    "dbt": [r"\bdbt\b", r"\bdata\.build\.tool"],
    "Apache Spark": [r"\bspark\b", r"\bapache\.spark", r"\bpyspark"],
    "Apache Flink": [r"\bflink\b", r"\bapache\.flink"],
    "Apache Kafka": [r"\bkafka\b", r"\bapache\.kafka", r"\bconfluent"],
    "Apache Airflow": [r"\bairflow\b", r"\bapache\.airflow"],
    "Dagster": [r"\bdagster\b"],
    "Prefect": [r"\bprefect\b"],
    "DuckDB": [r"\bduckdb\b", r"\bduck\.db\b"],
    "Apache Iceberg": [r"\biceberg\b", r"\bapache\.iceberg"],
    "Delta Lake": [r"\bdelta\.lake\b", r"\bdelta\s+lake\b"],
    "Apache Parquet": [r"\bparquet\b"],
    "Apache Arrow": [r"\bapache\.arrow", r"\bpyarrow\b"],
    "Great Expectations": [r"\bgreat\.expectations", r"\bgreat\s+expectations"],
    "SQLMesh": [r"\bsqlmesh\b", r"\bsql\.mesh\b"],
    "Debezium": [r"\bdebezium\b"],
    "Kubernetes": [r"\bkubernetes\b", r"\bk8s\b"],
    "Terraform": [r"\bterraform\b"],
    "Feast": [r"\bfeast\b"],
    "MLflow": [r"\bmlflow\b", r"\bml\.flow\b"],
    "dbt Mesh": [r"\bdbt\s+mesh\b", r"\bdbt\.mesh\b"],
    "dbt Cloud": [r"\bdbt\s+cloud\b"],
    "Apache Hudi": [r"\bhudi\b", r"\bapache\.hudi"],
    "Trino": [r"\btrino\b"],
    "PostgreSQL": [r"\bpostgres", r"\bpgsql\b"],
    "Snowflake": [r"\bsnowflake\b"],
    "BigQuery": [r"\bbigquery\b", r"\bbig\.query\b"],
    "Redshift": [r"\bredshift\b"],
    "Databricks": [r"\bdatabricks\b"],
    "dlt": [r"\bdlt\b"],
    "Airbyte": [r"\bairbyte\b"],
    "Fivetran": [r"\bfivetran\b"],
    "Stitch": [r"\bstitch\b"],
    "Metabase": [r"\bmetabase\b"],
    "Superset": [r"\bapache\.superset", r"\bsuperset\b"],
    "Grafana": [r"\bgrafana\b"],
    "Prometheus": [r"\bprometheus\b"],
    "Apache Druid": [r"\bdruid\b"],
    "ClickHouse": [r"\bclickhouse\b", r"\bclick\.house\b"],
    "MongoDB": [r"\bmongodb\b", r"\bmongo\s+db\b"],
    "Elasticsearch": [r"\belasticsearch\b"],
    "dask": [r"\bdask\b"],
    "Ray": [r"\bray\b"],
    "Apache Beam": [r"\bbeam\b", r"\bapache\.beam"],
    "Apache NiFi": [r"\bnifi\b", r"\bapache\.nifi"],
    "AWS Glue": [r"\baws\s+glue\b", r"\bglue\b"],
    "EMR": [r"\bemr\b"],
    "GCP Dataflow": [r"\bdataflow\b"],
    "Azure Data Factory": [r"\bazure\s+data\s+factory\b", r"\badf\b"],
    "Snowplow": [r"\bsnowplow\b"],
    "Segment": [r"\bsegment\b"],
    "dvc": [r"\bdvc\b", r"\bdata\.version\s+control"],
    "Kestra": [r"\bkestra\b"],
    "Spark SQL": [r"\bspark\s+sql\b"],
    "Apache Hive": [r"\bhive\b"],
    "Presto": [r"\bpresto\b"],
    "Materialize": [r"\bmaterialize\b"],
    "RisingWave": [r"\brisingwave\b", r"\brising\.wave\b"],
    "Redpanda": [r"\bredpanda\b"],
    "Pulsar": [r"\bpulsar\b", r"\bapache\.pulsar"],
    "NATS": [r"\bnats\b"],
    "Alluxio": [r"\balluxio\b"],
    "MinIO": [r"\bminio\b"],
    "Apache Hadoop": [r"\bhadoop\b"],
    "Apache Cassandra": [r"\bcassandra\b"],
    "Redis": [r"\bredis\b"],
    "Neo4j": [r"\bneo4j\b"],
    "Apache ZooKeeper": [r"\bzookeeper\b"],
    "Jaeger": [r"\bjaeger\b"],
    "OpenTelemetry": [r"\bopen.telemetry\b", r"\bopentelemetry\b"],
    "Starburst": [r"\bstarburst\b"],
}

# ── Use Case Detection Patterns ──────────────────────────────────────────

USE_CASE_PATTERNS: dict[str, list[str]] = {
    "streaming": [
        r"\bstream\b", r"\breal.time\b", r"\bevent.driven", r"\bcdc\b",
        r"\bchange.data.capture", r"\bkafka\b", r"\bflink\b",
    ],
    "batch-processing": [
        r"\bbatch\b", r"\bbulk\b", r"\betl\b", r"\bdata.warehouse",
        r"\bnightly", r"\bscheduled", r"\bworkflow\b",
    ],
    "data-quality": [
        r"\bdata.quality", r"\bquality\b", r"\bgreat.expectations",
        r"\bobservability", r"\bmonitoring", r"\bdata.valid",
        r"\bprofiling", r"\banomaly.detect",
    ],
    "data-governance": [
        r"\bgovernance", r"\bdata.catalog", r"\bdata.lineage",
        r"\bdata.contract", r"\bschema.registry", r"\bmetadata",
        r"\bdata.mesh", r"\bdata.product",
    ],
    "data-lakehouse": [
        r"\blakehouse\b", r"\bdata.lake", r"\biceberg\b", r"\bdelta.lake",
        r"\bparquet\b", r"\bcolumnar\b", r"\bopen.table",
    ],
    "orchestration": [
        r"\borchestrat", r"\bairflow\b", r"\bdagster\b", r"\bprefect\b",
        r"\bdag\b", r"\bpipeline.orchestrat",
    ],
    "elt-analytics-engineering": [
        r"\belt\b", r"\breverse.etl\b", r"\banalytics.engineering",
        r"\bdbt\b", r"\bsqlmesh\b", r"\btransformation",
    ],
    "data-pipeline": [
        r"\bpipeline", r"\bdata.pipeline", r"\bdata.engineering",
        r"\bdataops\b", r"\bdata.workflow",
    ],
    "schema-management": [
        r"\bschema\b", r"\bmigration", r"\bevolution", r"\bversioning",
        r"\bddl\b", r"\bdata.model", r"\bdimensional",
    ],
    "privacy-security": [
        r"\bprivacy", r"\bsecurity", r"\baccess.control", r"\bencrypt",
        r"\bpii\b", r"\bdp\b", r"\bdifferential.privacy",
    ],
    "infrastructure": [
        r"\binfrastructure", r"\bterraform\b", r"\bkubernetes\b",
        r"\bdocker\b", r"\bci/cd\b", r"\bdeployment", r"\bcloud\b",
    ],
    "ml-engineering": [
        r"\bml\b", r"\bmachine.learning", r"\bfeature.store",
        r"\bfeast\b", r"\bmlflow\b", r"\bmodel\b", r"\btraining",
        r"\binference", r"\bai\b",
    ],
}

TECH_TO_USE_CASE: dict[str, str] = {
    "Apache Kafka": "streaming",
    "Debezium": "streaming",
    "Apache Flink": "streaming",
    "Redpanda": "streaming",
    "Pulsar": "streaming",
    "RisingWave": "streaming",
    "Materialize": "streaming",
    "dbt": "elt-analytics-engineering",
    "SQLMesh": "elt-analytics-engineering",
    "Great Expectations": "data-quality",
    "Apache Iceberg": "data-lakehouse",
    "Delta Lake": "data-lakehouse",
    "Apache Parquet": "data-lakehouse",
    "Apache Arrow": "data-lakehouse",
    "Apache Airflow": "orchestration",
    "Dagster": "orchestration",
    "Prefect": "orchestration",
    "Feast": "ml-engineering",
    "MLflow": "ml-engineering",
    "Kubernetes": "infrastructure",
    "Terraform": "infrastructure",
    "dbt Mesh": "data-governance",
    "dbt Cloud": "elt-analytics-engineering",
}


def _clean_text(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"[^a-zA-Z0-9\s.]", " ", text)
    text = re.sub(r"\s+", " ", text).strip().lower()
    text = text.replace(".", " ")
    return text


def detect_technologies(text: str) -> list[str]:
    lower = text.lower()
    found: list[str] = []
    for tech, patterns in TECH_PATTERNS.items():
        for p in patterns:
            if re.search(p, lower):
                found.append(tech)
                break
    return sorted(set(found), key=lambda t: TECH_PATTERNS[t][0])


def detect_use_cases(text: str, technologies: list[str]) -> list[str]:
    lower = text.lower()
    found: set[str] = set()
    for uc, patterns in USE_CASE_PATTERNS.items():
        for p in patterns:
            if re.search(p, lower):
                found.add(uc)
                break
    # Infer use cases from detected technologies
    for tech in technologies:
        uc = TECH_TO_USE_CASE.get(tech)
        if uc:
            found.add(uc)
    return sorted(found)


def main() -> int:
    parser = argparse.ArgumentParser(description="Enrich data engineering metadata")
    parser.add_argument("--dry-run", action="store_true", default=True, help="Preview only")
    parser.add_argument("--apply", action="store_true", help="Write to registry.json")
    parser.add_argument("--verbose", "-v", action="store_true", help="Per-item detail")
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(message)s")

    if args.apply:
        args.dry_run = False

    registry_path = ROOT / "registry.json"
    with open(registry_path, encoding="utf-8") as f:
        registry = json.load(f)

    content: list[dict[str, Any]] = registry.get("content", [])
    enriched = 0
    unchanged = 0

    for item in content:
        if item.get("pillar") != "data-engineering":
            continue

        slug = item.get("slug", "?")
        text = " ".join([
            item.get("title", ""),
            item.get("description", ""),
            " ".join(item.get("tags", [])),
            _clean_text(item.get("body_html", "")),
        ])

        technologies = detect_technologies(text)
        use_cases = detect_use_cases(text, technologies)

        old_tech = item.get("technologies", [])
        old_uc = item.get("use_cases", [])

        if sorted(old_tech) == technologies and sorted(old_uc) == use_cases:
            unchanged += 1
            if args.verbose:
                logger.debug(f"  UNCHANGED [{slug}]")
            continue

        item["technologies"] = technologies
        item["use_cases"] = use_cases
        enriched += 1

        if args.verbose:
            logger.debug(f"  ENRICHED  [{slug}]")
            logger.debug(f"    Technologies: {technologies}")
            logger.debug(f"    Use cases:    {use_cases}")

    logger.info("")
    logger.info(f"Data-engineering items: {enriched + unchanged}  |  Enriched: {enriched}  |  Unchanged: {unchanged}")

    if not args.dry_run and enriched > 0:
        registry["content"] = content
        with open(registry_path, "w", encoding="utf-8") as f:
            json.dump(registry, f, indent=1)
        logger.info(f"Updated {enriched} items in {registry_path}")
    elif enriched > 0:
        logger.info(f"Dry run — {enriched} items would be updated. Use --apply to write.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
