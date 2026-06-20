# IT Technologies Relevant to AML/Fraud Detection

## Stream Processing Platforms
- **Apache Kafka** – distributed event streaming platform for high-throughput, fault-tolerant pipelines.
- **Apache Flink** – low-latency stream processor with event-time semantics and exactly-once guarantees.
- **Apache Storm** – real-time computation system (less common now).
- **Google Cloud Dataflow** – managed Apache Beam service for streaming and batch.
- **AWS Kinesis Data Analytics** – real-time processing of streaming data on AWS.

## Data Storage & Lakes
- **Data Lakehouse** (Delta Lake, Apache Iceberg) – combine lake flexibility with warehouse performance.
- **Cloud Object Stores** (Amazon S3, Azure Blob, Google Cloud Storage) – raw ingest and archival.
- **Feature Stores** (Feast, Tecton) – serve curated features for ML models in real time.

## Machine Learning & AI
- **Supervised Models** (Gradient Boosting, Neural Networks) for transaction classification.
- **Unsupervised Anomaly Detection** (Isolation Forest, Autoencoders) for emergent typologies.
- **Graph ML** (Neo4j GDS, PyTorch Geometric) to uncover money‑laundering networks.
- **Explainability Tools** (SHAP, LIME) for model audit and regulator compliance.

## Orchestration & Automation
- **Apache Airflow** – schedule and monitor complex AML workflows.
- **Kubernetes** – container orchestration for scalable micro‑services.
- **Terraform** – infrastructure‑as‑code for reproducible environments.
- **CI/CD Pipelines** (GitHub Actions, GitLab CI) – automated testing and deployment.

## Security & Privacy
- **Zero‑Trust Network Architecture** – verify every request.
- **Homomorphic Encryption** – compute on encrypted data (emerging).
- **Differential Privacy** – protect individual privacy in aggregated reports.
- **Secure Multi‑Party Computation (SMC)** – joint analysis without sharing raw data.

## Standards & APIs
- **ISO 20022** – universal financial‑industry messaging scheme.
- **REST/GraphQL APIs** – expose AML services to downstream systems.
- **Webhooks** – real‑time alerts to case‑management tools.
- **OpenTelemetry** – observability for distributed AML pipelines.

## Open‑Source Projects
- **Apache Metron** – cybersecurity platform (includes telemetry ingestion, enrichment, indexing).
- **OpenCTI** – open‑source cyber threat intelligence platform (useful for threat‑feeds in AML).
- **Maltego** – link‑analysis and visualisation (commercial with free tier).
- **Elastic Stack (ELK)** – search, logging, and analytics for alert investigation.

---
*This summary is intended as a starting point for building an AML‑focused IT stack. Specific tool choices should be driven by regulatory requirements, data volume, latency needs, and existing enterprise architecture.*