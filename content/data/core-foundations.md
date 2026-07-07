---
title: "Declarative DataOps and Schema Governance Architectures"
slug: "data-core-foundations"
category: foundation
pillar: data
tags: [dataops, schema-governance, data-lakehouse, data-quality, query-optimization, distributed-systems]
author: AcaciaFund
date: 2026-07-07
sqi: 1.0
---

# Declarative DataOps and Schema Governance Architectures

## Section 1: The Declarative Ingestion Paradigm

Data engineering has undergone a paradigm shift from imperative scripting to declarative compilation. In the imperative paradigm (Python scripts, shell pipelines, manually scheduled cron jobs), each data transformation is a procedural specification: "run this function, then that function, then persist the result." The order matters, the execution environment matters, and the developer is responsible for tracking which transformations depend on which inputs. This approach produces what Barr Moses termed "the data pipeline debt spiral": as the number of pipelines grows linearly, the debugging cost grows superlinearly because each pipeline's dependencies are implicit.

### Declarative Models as Compilation Targets

In the declarative paradigm (dbt, SQLMesh, Dagster with software-defined assets), each transformation is a SELECT statement or a Python function annotated with its input and output dependencies. The orchestration engine compiles the full dependency graph before executing any node:

```
# Declarative model — data/product_metrics.sql
SELECT
    product_id,
    COUNT(DISTINCT user_id) AS active_users,
    SUM(revenue) AS total_revenue,
    AVG(session_duration) AS avg_session_duration
FROM raw.events
WHERE event_date >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY product_id
```

The orchestration engine performs static analysis at compile time:
1. **Dependency resolution.** Parse the FROM clause to determine upstream dependencies (`raw.events`). Construct the Directed Acyclic Graph (DAG) of all models.
2. **Lineage tracking.** For each column in the SELECT clause, trace its origin to the source table's columns. A column-level lineage graph `G_c = (C, E)` where each edge `(c_i, c_j)` indicates that column `c_j` is derived from column `c_i`. This graph supports impact analysis: "if we rename `raw.events.revenue`, which downstream reports break?"
3. **Type checking.** Ensure that the SELECT statement produces a schema consistent with the declared model schema. Mismatched types raise a compile-time error, not a runtime failure — this is the critical advantage over imperative scripting, where type mismatches surface when the pipeline runs at 3 AM on a Saturday.
4. **Incremental computation.** If the model is declared as incremental (`WHERE event_date >= CURRENT_DATE - INTERVAL '30 days'`), the engine generates two execution plans: a full-refresh plan (for initial load) and an incremental plan (for daily updates using the model's unique key). The incremental plan applies only changed records, reducing execution time by orders of magnitude for append-only event streams.

### Static Compilation Testing

Declarative orchestration enables static compilation testing — verifying the DAG without executing it. The test suite:

```python
def test_model_compiles():
    from dbt.compilation import compile_project
    manifest = compile_project("/path/to/project")
    assert len(manifest.nodes) > 0, "No models found"
    assert all(not n.has_compile_error for n in manifest.nodes)

def test_no_cycles():
    from dbt.graph import perform_graph_operations
    graph = perform_graph_operations(manifest)
    assert not graph.has_cycles, "DAG contains cycles"

def test_column_lineage():
    for model in manifest.nodes:
        for column in model.columns:
            assert column.lineage is not None, f"{model.name}.{column.name} has no lineage"
```

These tests execute in under 10 seconds for a project with 500 models. They catch 60-70% of deployment-blocking issues (missing sources, circular dependencies, type mismatches) before any data is processed — the declarative paradigm's fundamental efficiency advantage.

### Section 2: Distributed Table Storage Topologies

### Decoupled Storage Architecture

Modern data lakehouse architectures decouple storage from compute, persisting data in open formats (Apache Iceberg, Delta Lake, Apache Hudi) on object storage (S3, GCS, Azure Blob) while compute engines (Spark, Trino, DuckDB) read and write through a metadata coordination layer.

The storage topology for an Iceberg table is a three-level tree:

```
Table root (database.table_name)
├── Metadata layer
│   ├── v1.metadata.json       — Current table snapshot
│   ├── v2.metadata.json       — Updated after append
│   └── v3.metadata.json       — Updated after compaction
├── Manifest list
│   ├── snap-12345.avro        — Manifests for snapshot v2
│   └── snap-12346.avro        — Manifests for snapshot v3
└── Data files (Parquet)
    ├── partition=2026-07-01/
    │   ├── 000000-001.parquet
    │   └── 000000-002.parquet
    ├── partition=2026-07-02/
    │   └── 000001-001.parquet
    └── partition=2026-07-03/
        └── 000002-001.parquet
```

Each metadata JSON file contains:
- The schema (column names, types, nullable constraints)
- The partition spec (how data is physically organised: `PARTITION BY date`)
- The sort order (how data within each partition is ordered: `ORDER BY transaction_id`)
- The snapshot's manifest list — a set of Avro files that each track a collection of data files

This three-level indirection enables atomic operations: when a query engine commits a write, it creates a new metadata file and atomically switches the table's current snapshot pointer. Readers see either the old snapshot or the new one, never an intermediate state. The atomic switch is implemented via a file system operation or a catalog transaction (Hive Metastore, AWS Glue, Nessie).

### File Compaction Tactics

The data lakehouse write pattern — append-only streaming inserts — produces a large number of small files over time. A streaming pipeline writing 1,000 events/second with a 60-second checkpoint interval produces 86,400 files per day per table. Each file incurs a listing overhead on object storage (approximately 5-10 milliseconds per file on S3) and a planning overhead in the query engine (opening each file to read its metadata footer).

Compaction is the process of merging small files into larger ones. The compaction policy for a production Iceberg table with 100 GB/day ingestion:

1. **Target file size:** 512 MB per Parquet file after compaction. This balances query parallelism (more files = more concurrent readers) with planning overhead (fewer files = faster planning).
2. **Compaction trigger:** Automatic compaction activates when the ratio of small files (<128 MB) to total files exceeds 0.3, or when total file count exceeds 10,000.
3. **Compaction execution:** A rewrite operation reads all data files in a partition, sorts them by the table's sort order, and writes new files of the target size. The operation is ACID: the rewrite creates new metadata and manifests atomically, and old files are eventually garbage-collected when no snapshot references them.

### Metadata Coordination — The Concurrency Problem

When multiple engines write to the same Iceberg table concurrently (e.g., a Spark batch job and a Flink streaming job), they contend on the metadata file. Iceberg's optimistic concurrency control uses a compare-and-swap (CAS) on the current metadata pointer:

```
1. Engine A reads current metadata (v2)
2. Engine B reads current metadata (v2)
3. Engine A writes data, creates v3, attempts to CAS: v2 → v3
4. CAS succeeds (current is v2)
5. Engine B writes data, creates v4, attempts to CAS: v2 → v4
6. CAS fails (current is now v3)
7. Engine B retries: re-reads v3, merges its changes, creates v5, CAS: v3 → v5
8. CAS succeeds
```

If Engine B's writes conflict with Engine A's (e.g., both modified the same data file), the merge fails and Engine B must resolve the conflict. Iceberg's default conflict resolution is "last writer wins" — Engine B's write overwrites Engine A's if they touched the same file. For streaming ingestion where writers append to different data files, conflicts are rare. For concurrent compaction operations that both rewrite the same partition, conflicts are frequent and require explicit coordination (e.g., a distributed lock via ZooKeeper).

## Section 3: Stateful Stream Processing

### Stateful Stream Joins in Apache Flink

Stream processing systems perform stateful operations — aggregations, joins, pattern matching — by maintaining operator state in local embedded key-value stores (RocksDB for Flink) or remote stores (Redis, mem0). The state is checkpointed periodically to durable storage for fault tolerance.

A stream-stream join (enriching a transaction stream with a customer profile stream) requires maintaining both sides in state:

```sql
-- Flink SQL: Stream-stream interval join
SELECT
    t.transaction_id,
    t.amount,
    c.customer_risk_rating,
    c.jurisdiction
FROM transactions t
JOIN customers c
    ON t.customer_id = c.customer_id
    AND t.event_time BETWEEN c.profile_valid_from AND c.profile_valid_to
```

This join requires Flink to maintain:
- The `transactions` stream's state: keys and event times for the past N minutes (the join interval)
- The `customers` stream's state: complete profile history (because profiles can change over time)

### State Compaction Strategies

Without state management, the `customers` join state grows without bound as new profiles are added. Production deployments use three compaction tactics:

1. **Time-to-live (TTL) watermarking.** Each state entry carries a TTL. For the transaction side, TTL equals the join interval (typically 5-60 minutes). For the customer side, TTL is the maximum expected profile validity period (typically 7-30 days). State entries exceeding TTL are garbage-collected during checkpointing.

2. **Versioned state with compaction.** For the customer side, only the most recent profile per `customer_id` is needed for correct join semantics (assuming profile updates supersede previous ones). Flink's RocksDB backend supports compaction filters that discard obsolete entries during RocksDB's LSM-tree compaction cycle:

```java
// Flink compaction filter: discard customer profiles superseded by newer ones
public class CustomerProfileCompactionFilter
    implements KeyedStateCompactionFilter<String, CustomerProfile> {
    
    @Override
    public boolean filter(String key, CustomerProfile value, long timestamp) {
        return value.isSuperseded();  // true = discard
    }
}
```

3. **Event-time alignment.** The join operation must handle out-of-order events — a transaction emitted with a 5-second latency must still join with the correct customer profile. Flink uses watermarks (event-time progress markers) to determine when no more events with timestamp `t < watermark` will arrive. Events arriving after the watermark are "late data" and can be discarded or routed to a side output for offline reprocessing.

### State Backend Configuration for Production

The Flink state backend configuration for a production stream join processing 50,000 events/second:

```yaml
state.backend: rocksdb
state.backend.rocksdb.timer-service-factory: ROCKSDB
state.backend.rocksdb.ttl.compaction.filter.enabled: true
state.backend.incremental: true
state.checkpoints.dir: s3://acaciafund-checkpoints/stream-joins/
state.checkpoints.num-retained: 3
state.backend.local-recovery: true
```

This configuration:
- Uses RocksDB (disk-based) rather than Heap (memory-based) because the join state exceeds 100 GB for a 30-day customer profile retention window
- Enables RocksDB's TTL compaction filter to automatically discard expired state entries
- Configures incremental checkpointing (only changed state entries are persisted per checkpoint, reducing checkpoint time from minutes to seconds)
- Retains 3 checkpoints for recovery: enough for at-least-once semantics, not enough to overflow S3 storage
- Enables local recovery (state is restored from local disk rather than re-downloading from S3 on restart), reducing failover time from 30 minutes to 2 minutes for a 100 GB state backend

---

**Last Updated:** 2026-07-07
**Version:** 1.0.0
**Classification:** Data Engineering Foundations
**Primary Sources:** Apache Iceberg Specification v2; Flink State Backend Tuning Guide; Barr Moses — *Data Quality Fundamentals*
**Confidence Score:** 1.00
**Ontology Tag:** data/core-foundations
