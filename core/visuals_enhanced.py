"""Enhanced icon library and matching system for AcaciaFund."""

# Additional abstract icons for Data Engineering
DATA_ENGINEERING_ICONS = {
    # Data Formats
    "parquet": {"type": "abstract", "paths": '<rect x="4" y="4" width="16" height="16" rx="2"/><path d="M8 8l8 8M16 8l-8 8"/>'},
    "avro": {"type": "abstract", "paths": '<polygon points="12,2 22,12 12,22 2,12"/><path d="M12 6v12M6 12h12"/>'},
    "orc": {"type": "abstract", "paths": '<rect x="2" y="2" width="20" height="20" rx="4"/><circle cx="12" cy="12" r="4"/><path d="M12 2v4M12 18v4M2 12h4M18 12h4"/>'},
    "iceberg": {"type": "abstract", "paths": '<path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5"/><path d="M12 22V12"/>'},
    "hudi": {"type": "abstract", "paths": '<path d="M4 4h16v16H4z"/><circle cx="12" cy="12" r="3"/><path d="M12 9v6M9 12h6"/>'},
    
    # ML/AI Frameworks
    "pytorch": {"type": "abstract", "paths": '<path d="M4 12c0-4.4 3.6-8 8-8s8 3.6 8 8-3.6 8-8 8-8-3.6-8-8z"/><circle cx="12" cy="12" r="2"/><path d="M10 8l4 4-4 4"/>'},
    "tensorflow": {"type": "abstract", "paths": '<path d="M4 16c0-4.4 3.6-8 8-8s8 3.6 8 8-3.6 8-8 8-8-3.6-8-8z"/><path d="M12 10l4 4-4 4"/>'},
    "scikit": {"type": "abstract", "paths": '<circle cx="12" cy="12" r="10"/><path d="M2 12h20M12 2v20M4.93 4.93l14.14 14.14M19.07 4.93L4.93 19.07"/>'},
    "mlflow": {"type": "abstract", "paths": '<polygon points="12,2 20,8 20,16 12,22 4,16 4,8"/><path d="M12 14l4-4 4 4"/>'},
    
    # Cloud Providers
    "aws": {"type": "abstract", "paths": '<path d="M2 8h8v8H2zM14 8h8v8h-8zM2 16h8v4H2zM14 16h8v4h-8z"/>'},
    "gcp": {"type": "abstract", "paths": '<path d="M4 4h16v4H4zM4 12h16v4H4zM4 20h16v4H4z"/><circle cx="12" cy="12" r="2"/>'},
    "azure": {"type": "abstract", "paths": '<rect x="2" y="4" width="20" height="16" rx="4"/><path d="M6 8h14M6 12h10M6 16h14"/>'},
    "oracle": {"type": "abstract", "paths": '<circle cx="12" cy="12" r="10"/><path d="M12 2v4M12 18v4M2 12h4M18 12h4"/>'},
    
    # Security
    "encryption": {"type": "abstract", "paths": '<rect x="4" y="4" width="16" height="16" rx="2"/><path d="M12 8v8M8 12h8"/>'},
    "zero-trust": {"type": "abstract", "paths": '<circle cx="12" cy="12" r="8"/><path d="M12 2v4M12 18v4M2 12h4M18 12h4"/>'},
    "iam": {"type": "abstract", "paths": '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><circle cx="12" cy="12" r="3"/>'},
    "compliance": {"type": "abstract", "paths": '<rect x="3" y="3" width="18" height="18" rx="2"/><path d="M9 12l2 2 4-4"/><path d="M12 9v6M12 15h4"/>'},
    
    # Analytics
    "dashboard": {"type": "abstract", "paths": '<rect x="2" y="3" width="20" height="14" rx="2"/><path d="M6 7h14M6 11h10M6 15h6"/>'},
    "visualization": {"type": "abstract", "paths": '<path d="M3 3v18h18"/><path d="M18 9l-5 10-5-10"/><path d="M3 15l9-6 9 6"/>'},
    "chart": {"type": "abstract", "paths": '<path d="M6 18h12M6 14h8M6 10h4M6 6h2"/>'},
    
    # Data Operations
    "etl": {"type": "abstract", "paths": '<path d="M3 12h18M3 8h14M3 16h10"/><path d="M12 3v9M7 8l5 5 5-5"/>'},
    "orchestration": {"type": "abstract", "paths": '<path d="M3 12h18M3 8h14M3 16h10"/><circle cx="12" cy="12" r="2"/><path d="M12 3v9M7 8l5 5 5-5"/>'},
    "workflow": {"type": "abstract", "paths": '<path d="M3 12h18M3 8h14M3 16h10"/><path d="M12 3v9M7 8l5 5 5-5"/>'},
    "dag": {"type": "abstract", "paths": '<path d="M3 12h18M3 8h14M3 16h10"/><circle cx="12" cy="12" r="2"/><path d="M12 3v9M7 8l5 5 5-5"/>'},
    
    # Monitoring
    "observability": {"type": "abstract", "paths": '<path d="M2 12s4-6 10-6 10 6 10 6-4 6-10 6-10-6-10-6z"/><circle cx="12" cy="12" r="3"/>'},
    "monitoring": {"type": "abstract", "paths": '<path d="M22 12h-4l-3 9L9 3l-3 9H2"/>'},
    "alerts": {"type": "abstract", "paths": '<path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/>'},
    "metrics": {"type": "abstract", "paths": '<path d="M3 3v18h18"/><path d="M18 17V9M13 17V5M8 17v-3"/>'},
    
    # Data Quality
    "testing": {"type": "abstract", "paths": '<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><path d="M22 4L12 14.01l-3-3"/></>'},
    "validation": {"type": "abstract", "paths": '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><circle cx="12" cy="12" r="3"/>'},
    "schema": {"type": "abstract", "paths": '<rect x="3" y="3" width="18" height="18" rx="2"/><path d="M9 9h6v6H9z"/><path d="M9 12h6"/></>'},
    "lineage": {"type": "abstract", "paths": '<path d="M2 22l10-10 10 10M2 10l10-10 10 10M2 18l8-8 8 8"/></>'},
    
    # Automation
    "ci-cd": {"type": "abstract", "paths": '<path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z'/>'},
    "automation": {"type": "abstract", "paths": '<rect x="3" y="6" width="18" height="12" rx="2"/><path d="M8 10h.01M12 10h.01M16 10h.01M8 14h.01M12 14h.01M16 14h.01"/>'},
    "deployment": {"type": "abstract", "paths": '<path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z"/><line x1="4" x2="4" y1="22" y2="15"/><line x1="12" x2="12" y1="22" y2="15"/><line x1="20" x2="20" y1="22" y2="15"/>'},
    
    # Database
    "postgresql": {"type": "abstract", "paths": '<ellipse cx="12" cy="12" rx="10" ry="4"/><ellipse cx="12" cy="12" rx="10" ry="4" transform="rotate(60 12 12)"/><ellipse cx="12" cy="12" rx="10" ry="4" transform="rotate(120 12 12)"/>'},
    "mongodb": {"type": "abstract", "paths": '<circle cx="12" cy="12" r="10"/><path d="M12 6a6 6 0 0 1 6 6"/><path d="M12 6a6 6 0 0 0-6 6"/><path d="M12 18a6 6 0 0 0-6-6"/><path d="M12 18a6 6 0 0 1 6-6"/>'},
    "redis": {"type": "abstract", "paths": '<circle cx="12" cy="12" r="10"/><path d="M12 2v4M12 18v4M2 12h4M18 12h4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M4.93 17.07l2.83-2.83M16.24 5.76l2.83-2.83"/>'},
    "elasticsearch": {"type": "abstract", "paths": '<circle cx="12" cy="12" r="10"/><path d="M12 6v12M6 12h12M10 8l4 4-4 4"/></>'},
}

# Additional brand icons (Simple Icons)
ADDITIONAL_BRANDS = {
    # Data Engineering
    "dagster": {"dagster", "dagster ci", "dagster pipeline"},
    "prefect": {"prefect", "prefect cloud", "prefect orchestration"},
    "kestra": {"kestra", "kestra workflow"},
    "apachebeam": {"beam", "apache beam", "dataflow"},
    "snowflake": {"snowflake", "snowpipe", "snowsql", "snowflake data cloud"},
    "databricks": {"databricks", "databricks lakehouse", "databricks workspace"},
    "confluent": {"confluent", "kafka connect", "kafka streams"},
    "apachehdfs": {"hdfs", "hadoop distributed filesystem"},
    "apachecassandra": {"cassandra", "apache cassandra", "nosql"},
    "apachepinot": {"pinot", "apache pinot", "realtime analytics"},
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
    "featurestore": {"feature store", "feast", "tecton"},
    "dbtcloud": {"dbt cloud", "dbt transform"},
    
    # ML/AI
    "scikit": {"scikit", "scikit learn", "sklearn"},
    "pycub": {"pycub", "cub"},
    "openai": {"openai", "chatgpt", "gpt", "o1", "o3", "llm"},
    "anthropic": {"anthropic", "claude", "claude ai"},
    "cohere": {"cohere", "cohere ai", "cohere llm"},
    "mistral": {"mistral", "mistral ai"},
    "groq": {"groq", "groq cloud"},
    "replicate": {"replicate", "replicate ai"},
    "wandb": {"wandb", "weights and biases"},
    "comet": {"comet ml", "comet"},
    "neptune": {"neptune ai", "neptune"},
    "mlflow": {"mlflow", "mlflow tracking", "mlflow model registry"},
    "dvc": {"dvc", "data version control"},
    "gitlfs": {"git lfs", "git large file storage"},
    
    # Security
    "hashicorp": {"hashicorp", "vault", "terraform cloud"},
    "sentinelone": {"sentinelone", "endpoint security"},
    "crowdstrike": {"crowdstrike", "falcon"},
    "okta": {"okta", "identity management"},
    "auth0": {"auth0", "auth0 identity"},
    "keycloak": {"keycloak", "keycloak identity"},
    "fortinet": {"fortinet", "fortigate"},
    "paloalto": {"palo alto", "palo alto networks"},
    "checkpoint": {"checkpoint", "checkpoint software"},
    
    # Cloud DevOps
    "bitbucket": {"bitbucket", "bitbucket cloud"},
    "circleci": {"circleci", "circle ci"},
    "gitlabci": {"gitlab ci/cd", "gitlab pipeline"},
    "jenkins": {"jenkins", "jenkins ci"},
    "spinnaker": {"spinnaker", "spinnaker deploy"},
    "argocd": {"argocd", "argocd continuous delivery"},
    "flux": {"flux cd", "flux continuous delivery"},
    "helm": {"helm", "helm chart"},
    "istio": {"istio", "istio service mesh"},
    "linkerd": {"linkerd", "linkerd service mesh"},
    "consul": {"consul", "hashicorp consul"},
    "nomad": {"nomad", "hashicorp nomad"},
    "vault": {"vault", "hashicorp vault"},
    
    # Databases
    "supabase": {"supabase", "supabase postgres"},
    "neon": {"neon", "neon postgres"},
    "planetscale": {"planetscale", "planetscale mysql"},
    "firebird": {"firebird", "firebird database"},
    "sqlite": {"sqlite", "sqlite database"},
    "cockroachdb": {"cockroachdb", "cockroach"},
    "timescale": {"timescale", "timescale db"},
    "influxdb": {"influxdb", "influxdb time series"},
    "prometheus": {"prometheus", "prometheus monitoring"},
    "grafana": {"grafana", "grafana dashboard"},
    "datadog": {"datadog", "datadog monitoring"},
    "newrelic": {"newrelic", "newrelic observability"},
    "sentry": {"sentry", "sentry error tracking"},
    
    # Analytics BI
    "tableau": {"tableau", "tableau desktop"},
    "powerbi": {"power bi", "microsoft power bi"},
    "looker": {"looker", "looker data"},
    "qlik": {"qlik", "qlik view"},
    "sisense": {"sisense", "sisense analytics"},
    "periscope": {"periscope data", "periscope analytics"},
    "mode": {"mode analytics", "mode"},
    "redash": {"redash", "redash sql"},
    
    # Science
    "cns": {"cns", "computational neuroscience"},
    "biopython": {"biopython", "biopython bioinformatics"},
    "rdkit": {"rdkit", "rdkit cheminformatics"},
    "chembl": {"chembl", "chembl database"},
    "pdb": {"pdb", "protein data bank"},
    "uniprot": {"uniprot", "uniprot protein"},
    "ensembl": {"ensembl", "ensembl genome"},
    "ucsc": {"ucsc", "ucsc genome browser"},
    "galaxy": {"galaxy", "galaxy project"},
    "jupyter": {"jupyter", "jupyter notebook", "jupyterlab"},
    "vscode": {"vscode", "visual studio code"},
    "pycharm": {"pycharm", "jetbrains pycharm"},
    "intellij": {"intellij", "jetbrains intellij"},
}

# Add additional brand icons to TOPIC_ICONS
for slug, keywords in ADDITIONAL_BRANDS.items():
    TOPIC_ICONS[slug] = {"type": "brand", "slug": slug}

# Expand SUBTOPIC_CATEGORIES with new data engineering topics
SUBTOPIC_CATEGORIES["data-engineering"].update({
    "parquet": {"parquet", "apache parquet", "columnar", "storage format"},
    "avro": {"avro", "apache avro", "schema registry"},
    "orc": {"orc", "apache orc", "columnar format"},
    "iceberg": {"iceberg", "apache iceberg", "table format"},
    "hudi": {"hudi", "apache hudi", "data lake"},
    "mlflow": {"mlflow", "mlflow tracking", "model registry"},
    "scikit": {"scikit", "scikit learn", "machine learning"},
    "pytorch": {"pytorch", "torch", "deep learning"},
    "tensorflow": {"tensorflow", "tf", "deep learning"},
    "aws": {"aws", "amazon web services", "cloud"},
    "gcp": {"gcp", "google cloud", "cloud platform"},
    "azure": {"azure", "microsoft azure", "cloud"},
    "encryption": {"encryption", "encrypt", "security", "ssl", "tls"},
    "zero-trust": {"zero trust", "zero-trust", "security model"},
    "iam": {"iam", "identity", "access management", "authentication"},
    "dashboard": {"dashboard", "dashboard view", "analytics view"},
    "visualization": {"visualization", "viz", "data viz", "chart"},
    "observability": {"observability", "obs", "monitoring", "logging"},
    "ci-cd": {"ci/cd", "ci cd", "continuous integration", "continuous deployment"},
    "deployment": {"deployment", "deploy", "release", "rollout"},
    "postgresql": {"postgresql", "postgres", "psql", "db"},
    "mongodb": {"mongodb", "mongo", "nosql"},
    "elasticsearch": {"elasticsearch", "es", "search engine"},
    "langchain": {"langchain", "llm app", "ai app"},
    "huggingface": {"huggingface", "hf", "transformers", "nlp"},
    "vector database": {"vector db", "vector search", "embedding", "vector"},
    "featurestore": {"feature store", "feature", "realtime features"},
    "wandb": {"wandb", "weights and biases", "ml experiment"},
    "comet": {"comet ml", "ml experiment tracking"},
    "neptune": {"neptune ai", "ml metadata"},
    "hashicorp": {"hashicorp", "vault", "secrets management"},
    "bitbucket": {"bitbucket", "atlassian"},
    "circleci": {"circleci", "ci pipeline"},
    "grafana": {"grafana", "dashboard", "visualization"},
    "tableau": {"tableau", "bi", "business intelligence"},
    "powerbi": {"power bi", "microsoft", "bi"},
    "looker": {"looker", "data", "analytics"},
})

# Update SUBTOPIC_CATEGORIES for AML and Stock with additional topics
SUBTOPIC_CATEGORIES["aml"].update({
    "risk": {"risk", "risk assessment", "risk model", "risk management"},
    "sanctions": {"sanctions", "sanctions list", "ofac", "trade sanctions"},
    "pep": {"pep", "politically exposed person", "politically exposed"},
    "kyc": {"kyc", "know your customer", "customer due diligence"},
    "aml-software": {"aml software", "aml platform", "aml solution"},
})

SUBTOPIC_CATEGORIES["stock"].update({
    "fintech": {"fintech", "financial technology", "fin tech"},
    "payments": {"payments", "payment processing", "payment gateway"},
    "neobank": {"neobank", "neo bank", "digital bank"},
    "wealth": {"wealth", "wealth management", "wealth tech"},
    "robo": {"robo advisor", "robo-advisor", "automated investing"},
})
