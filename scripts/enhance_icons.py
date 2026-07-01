#!/usr/bin/env python3
"""Script to enhance the icon library."""

import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
VISUALS_PATH = PROJECT_ROOT / "core" / "visuals.py"

# New abstract icons
NEW_ICONS = {
    "parquet": {
        "type": "abstract",
        "paths": '<rect x="4" y="4" width="16" height="16" rx="2"/><path d="M8 8l8 8M16 8l-8 8"/>',
    },
    "avro": {
        "type": "abstract",
        "paths": '<polygon points="12,2 22,12 12,22 2,12"/><path d="M12 6v12M6 12h12"/>',
    },
    "orc": {
        "type": "abstract",
        "paths": '<rect x="2" y="2" width="20" height="20" rx="4"/><circle cx="12" cy="12" r="4"/><path d="M12 2v4M12 18v4M2 12h4M18 12h4"/>',
    },
    "iceberg": {
        "type": "abstract",
        "paths": '<path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5"/><path d="M12 22V12"/>',
    },
    "hudi": {
        "type": "abstract",
        "paths": '<path d="M4 4h16v16H4z"/><circle cx="12" cy="12" r="3"/><path d="M12 9v6M9 12h6"/>',
    },
    "scikit": {
        "type": "abstract",
        "paths": '<circle cx="12" cy="12" r="10"/><path d="M2 12h20M12 2v20M4.93 4.93l14.14 14.14M19.07 4.93L4.93 19.07"/>',
    },
    "mlflow": {
        "type": "abstract",
        "paths": '<polygon points="12,2 20,8 20,16 12,22 4,16 4,8"/><path d="M12 14l4-4 4 4"/>',
    },
    "aws": {
        "type": "abstract",
        "paths": '<path d="M2 8h8v8H2zM14 8h8v8h-8zM2 16h8v4H2zM14 16h8v4h-8z"/>',
    },
    "gcp": {
        "type": "abstract",
        "paths": '<path d="M4 4h16v4H4zM4 12h16v4H4zM4 20h16v4H4z"/><circle cx="12" cy="12" r="2"/>',
    },
    "azure": {
        "type": "abstract",
        "paths": '<rect x="2" y="4" width="20" height="16" rx="4"/><path d="M6 8h14M6 12h10M6 16h14"/>',
    },
    "encryption": {
        "type": "abstract",
        "paths": '<rect x="4" y="4" width="16" height="16" rx="2"/><path d="M12 8v8M8 12h8"/>',
    },
    "zero-trust": {
        "type": "abstract",
        "paths": '<circle cx="12" cy="12" r="8"/><path d="M12 2v4M12 18v4M2 12h4M18 12h4"/>',
    },
    "iam": {
        "type": "abstract",
        "paths": '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><circle cx="12" cy="12" r="3"/>',
    },
    "dashboard": {
        "type": "abstract",
        "paths": '<rect x="2" y="3" width="20" height="14" rx="2"/><path d="M6 7h14M6 11h10M6 15h6"/>',
    },
    "visualization": {
        "type": "abstract",
        "paths": '<path d="M3 3v18h18"/><path d="M18 9l-5 10-5-10"/><path d="M3 15l9-6 9 6"/>',
    },
    "chart": {"type": "abstract", "paths": '<path d="M6 18h12M6 14h8M6 10h4M6 6h2"/>'},
    "etl": {
        "type": "abstract",
        "paths": '<path d="M3 12h18M3 8h14M3 16h10"/><path d="M12 3v9M7 8l5 5 5-5"/>',
    },
    "dag": {
        "type": "abstract",
        "paths": '<path d="M3 12h18M3 8h14M3 16h10"/><circle cx="12" cy="12" r="2"/><path d="M12 3v9M7 8l5 5 5-5"/>',
    },
    "observability": {
        "type": "abstract",
        "paths": '<path d="M2 12s4-6 10-6 10 6 10 6-4 6-10 6-10-6-10-6z"/><circle cx="12" cy="12" r="3"/>',
    },
    "monitoring": {"type": "abstract", "paths": '<path d="M22 12h-4l-3 9L9 3l-3 9H2"/>'},
    "alerts": {
        "type": "abstract",
        "paths": '<path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/>',
    },
    "metrics": {
        "type": "abstract",
        "paths": '<path d="M3 3v18h18"/><path d="M18 17V9M13 17V5M8 17v-3"/>',
    },
    "testing": {
        "type": "abstract",
        "paths": '<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><path d="M22 4L12 14.01l-3-3"/>',
    },
    "validation": {
        "type": "abstract",
        "paths": '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><circle cx="12" cy="12" r="3"/>',
    },
    "schema": {
        "type": "abstract",
        "paths": '<rect x="3" y="3" width="18" height="18" rx="2"/><path d="M9 9h6v6H9z"/><path d="M9 12h6"/>',
    },
    "lineage": {
        "type": "abstract",
        "paths": '<path d="M2 22l10-10 10 10M2 10l10-10 10 10M2 18l8-8 8 8"/>',
    },
    "automation": {
        "type": "abstract",
        "paths": '<rect x="3" y="6" width="18" height="12" rx="2"/><path d="M8 10h.01M12 10h.01M16 10h.01M8 14h.01M12 14h.01M16 14h.01"/>',
    },
    "deployment": {
        "type": "abstract",
        "paths": '<path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z"/><line x1="4" x2="4" y1="22" y2="15"/><line x1="12" x2="12" y1="22" y2="15"/><line x1="20" x2="20" y1="22" y2="15"/>',
    },
    "postgresql": {
        "type": "abstract",
        "paths": '<ellipse cx="12" cy="12" rx="10" ry="4"/><ellipse cx="12" cy="12" rx="10" ry="4" transform="rotate(60 12 12)"/><ellipse cx="12" cy="12" rx="10" ry="4" transform="rotate(120 12 12)"/>',
    },
    "mongodb": {
        "type": "abstract",
        "paths": '<circle cx="12" cy="12" r="10"/><path d="M12 6a6 6 0 0 1 6 6"/><path d="M12 6a6 6 0 0 0-6 6"/><path d="M12 18a6 6 0 0 0-6-6"/><path d="M12 18a6 6 0 0 1 6-6"/>',
    },
    "redis": {
        "type": "abstract",
        "paths": '<circle cx="12" cy="12" r="10"/><path d="M12 2v4M12 18v4M2 12h4M18 12h4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M4.93 17.07l2.83-2.83M16.24 5.76l2.83-2.83"/>',
    },
    "elasticsearch": {
        "type": "abstract",
        "paths": '<circle cx="12" cy="12" r="10"/><path d="M12 6v12M6 12h12M10 8l4 4-4 4"/>',
    },
    "risk": {
        "type": "abstract",
        "paths": '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><circle cx="12" cy="12" r="3"/><path d="M2 17l10 5 10-5"/>',
    },
    "sanctions": {
        "type": "abstract",
        "paths": '<path d="M2 22l10-10 10 10M2 12l10-10 10 10M2 22V2l10 10 10-10V22"/>',
    },
    "pep": {
        "type": "abstract",
        "paths": '<circle cx="12" cy="8" r="4"/><path d="M12 12v10M8 16h8"/>',
    },
    "kyc": {
        "type": "abstract",
        "paths": '<rect x="4" y="4" width="16" height="16" rx="2"/><path d="M9 9h6v6H9z"/><path d="M12 12l4 4"/>',
    },
    "fintech": {
        "type": "abstract",
        "paths": '<rect x="2" y="4" width="20" height="16" rx="2"/><path d="M6 8h14M6 12h10M6 16h6"/><circle cx="12" cy="12" r="2"/>',
    },
    "payments": {
        "type": "abstract",
        "paths": '<rect x="3" y="3" width="18" height="18" rx="2"/><path d="M9 12h6M12 9v6M9 9l3 3-3 3"/>',
    },
    "neobank": {
        "type": "abstract",
        "paths": '<rect x="2" y="4" width="20" height="16" rx="2"/><path d="M6 8h14M10 12h4M8 16h8"/>',
    },
    "wealth": {
        "type": "abstract",
        "paths": '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="M12 6v14M8 10h8"/>',
    },
    "robo": {
        "type": "abstract",
        "paths": '<path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M12 22V12"/><circle cx="12" cy="12" r="3"/>',
    },
}

# New brand keyword groups
NEW_BRANDS = {
    "dagster": {"dagster", "dagster ci", "dagster pipeline"},
    "prefect": {"prefect", "prefect cloud", "prefect orchestration"},
    "kestra": {"kestra", "kestra workflow"},
    "apachebeam": {"beam", "apache beam", "dataflow"},
    "databricks": {"databricks", "databricks lakehouse", "databricks workspace"},
    "confluent": {"confluent", "kafka connect", "kafka streams"},
    "apachehdfs": {"hdfs", "hadoop distributed filesystem"},
    "apachecassandra": {"cassandra", "apache cassandra", "nosql"},
    "apache pinot": {"pinot", "apache pinot", "realtime analytics"},
    "clickhouse": {"clickhouse", "clickhouse db"},
    "druid": {"druid", "apache druid", "realtime analytics"},
    "milvus": {"milvus", "vector database"},
    "qdrant": {"qdrant", "vector search"},
    "pgvector": {"pgvector", "postgres vector"},
    "weaviate": {"weaviate", "vector database"},
    "pinecone": {"pinecone", "vector database"},
    "chromadb": {"chroma", "chroma db", "vector database"},
    "langchain": {"langchain", "langchain llm"},
    "huggingface": {"huggingface", "hugging face", "transformers"},
    "vectordb": {"vector database", "vector search", "embedding"},
    "featurestore": {"feature store", "feature", "realtime features"},
    "dbtcloud": {"dbt cloud", "dbt transform"},
    "scikit": {"scikit", "scikit learn", "sklearn"},
    "wandb": {"wandb", "weights and biases"},
    "comet": {"comet ml", "comet"},
    "neptune": {"neptune ai", "neptune"},
    "hashicorp": {"hashicorp", "vault", "terraform cloud"},
    "okta": {"okta", "identity management"},
    "auth0": {"auth0", "auth0 identity"},
    "keycloak": {"keycloak", "keycloak identity"},
    "bitbucket": {"bitbucket", "bitbucket cloud"},
    "circleci": {"circleci", "circle ci"},
    "argocd": {"argocd", "argocd continuous delivery"},
    "flux": {"flux cd", "flux continuous delivery"},
    "istio": {"istio", "istio service mesh"},
    "linkerd": {"linkerd", "linkerd service mesh"},
    "consul": {"consul", "hashicorp consul"},
    "nomad": {"nomad", "hashicorp nomad"},
    "vault": {"vault", "hashicorp vault"},
    "supabase": {"supabase", "supabase postgres"},
    "neon": {"neon", "neon postgres"},
    "planetscale": {"planetscale", "planetscale mysql"},
    "cockroachdb": {"cockroachdb", "cockroach"},
    "timescale": {"timescale", "timescale db"},
    "influxdb": {"influxdb", "influxdb time series"},
    "prometheus": {"prometheus", "prometheus monitoring"},
    "grafana": {"grafana", "grafana dashboard"},
    "datadog": {"datadog", "datadog monitoring"},
    "newrelic": {"newrelic", "newrelic observability"},
    "sentry": {"sentry", "sentry error tracking"},
    "tableau": {"tableau", "tableau desktop"},
    "powerbi": {"power bi", "microsoft power bi"},
    "looker": {"looker", "looker data"},
    "qlik": {"qlik", "qlik view"},
    "biopython": {"biopython", "biopython bioinformatics"},
    "rdkit": {"rdkit", "rdkit cheminformatics"},
    "vscode": {"vscode", "visual studio code"},
    "intellij": {"intellij", "jetbrains intellij"},
}


def read_visuals():
    with open(VISUALS_PATH, "r") as f:
        content = f.read()
    return content


def write_visuals(content):
    VISUALS_PATH.write_text(content, encoding="utf-8")
    print(f"Updated {VISUALS_PATH}")


def main():
    print("Enhancing icon library...")
    content = read_visuals()

    # Add new abstract icons after infrastructure
    icons_str = "\n".join([f'    "{k}": {v},' for k, v in NEW_ICONS.items()])
    pattern = r'(    "infrastructure":\{.*?\},\n)'
    content = re.sub(pattern, r"\1" + icons_str, content, flags=re.DOTALL)

    # Add new brand keywords after fedora
    brands_str = "\n".join([f'    "{k}": {v},' for k, v in NEW_BRANDS.items()])
    pattern = r'(    "fedora":.*?,\n)'
    content = re.sub(pattern, r"\1" + brands_str, content, flags=re.DOTALL)

    write_visuals(content)

    print(f"Added {len(NEW_ICONS)} new abstract icons")
    print(f"Added {len(NEW_BRANDS)} new brand keyword groups")
    print("Enhancement complete!")


if __name__ == "__main__":
    main()
