#!/usr/bin/env python3
import os
import json
import re
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent

KNOWLEDGE_VAULT = {
    "aml": [
        {
            "slug": "ubo-unwinding-algorithms",
            "title": "Recursive Ultimate Beneficial Ownership (UBO) Unwinding in Complex Corporate Networks",
            "tags": ["aml", "entity-resolution", "graph-theory"],
            "cross_vectors": ["zero-copy-arrow-iceberg"],
            "content": """# Recursive Ultimate Beneficial Ownership (UBO) Unwinding

## 1. Topological Decomposition of Layered Shell Entities
Sanctions evasion and complex corporate financial crime patterns frequently employ nested legal structures spanning multiple jurisdictions. To programmatically isolate the Ultimate Beneficial Owner (UBO), we model corporate equity control structures as a directed acyclic or cyclic weighted graph $G = (V, E)$, where vertices $v \\in V$ represent natural persons or corporate entities, and directed edges $e_{ij} = (v_i, v_j) \\in E$ represent fractional equity ownership ownership shares $w_{ij} \\in (0, 1]$.

The structural challenge arises when ownership is layered recursively through holding companies, offshore trusts, and cross-shareholding structures. Traditional compliance systems fail because they evaluate only direct relationships ($1$st-hop links). To resolve the true voting or economic control vector of a natural person over a target asset, the system must execute a full topological closure computation across all available dependency pathways.

## 2. The Multi-Hop Control Accumulation Equation
We formulate the cumulative tracking share of a natural person $v_{\\text{human}}$ over a target entity $v_{\\text{target}}$ as the sum of all path-dependent product chains across the network topology:

$$W_{v_{\\text{human}} \\to v_{\\text{target}}} = \\sum_{p \\in \\mathcal{P}} \\prod_{e_{ij} \\in p} w_{ij}$$

Where $\\mathcal{P}$ represents the complete set of all directed paths from $v_{\\text{human}}$ to $v_{\\text{target}}$. In the presence of cross-shareholding loops (where corporate entities hold shares in one another), the path set $\\mathcal{P}$ becomes infinite. We resolve this infinite matrix series using Leontief inversion logic. Let $\\mathbf{A}$ be the $|V| \\times |V|$ adjacency matrix of direct ownership percentages. The total global control matrix $\\mathbf{T}$ is solved via:

$$\\mathbf{T} = \\sum_{k=1}^{\\infty} \\mathbf{A}^k = (\\mathbf{I} - \\mathbf{A})^{-1} - \\mathbf{I}$$

Where $\\mathbf{I}$ is the identity matrix. The algorithm flags any natural person whose computed value $T_{i,j} \\ge 0.25$, identifying individuals exercising significant control regardless of the structural path length or institutional layering depth.
"""
        },
        {
            "slug": "tbml-pricing-anomalies",
            "title": "Trade-Based Money Laundering (TBML) Detection via Statistical Pricing Anomaly Isolation",
            "tags": ["aml", "statistical-modeling", "fraud-detection"],
            "cross_vectors": ["hawkes-microstructure"],
            "content": """# Trade-Based Money Laundering (TBML) Detection

## 1. Mechanics of Mis-Invoicing Vectors
Trade-Based Money Laundering (TBML) represents one of the most sophisticated methodologies for transferring value across international borders under the guise of legitimate commercial transactions. The primary operational vectors include:
* **Over-Invoicing:** The seller bills the buyer at a price significantly above market value, moving capital from the buyer's jurisdiction to the seller's.
* **Under-Invoicing:** The seller bills the buyer at a price significantly below market value, allowing the buyer to realize an outsized profit upon local resale.

To automate the detection of these fraudulent value transfers, transaction monitoring engines must cross-reference unit prices declared on customs manifests against high-frequency global spot market pricing distributions.

## 2. Mathematical Isolation via Z-Score and Interquartile Range (IQR) Profiles
Let $x_{c,t}$ be the declared unit price of a specific commodity code $c$ at transaction time $t$. We establish a dynamic reference distribution using historical global customs indices over an evaluation window $\\Delta t$. The pricing variance is monitored using a dual-metric filtering framework:

$$\\text{Z-Score}(x_{c,t}) = \\frac{x_{c,t} - \\mu_c}{\\sigma_c}$$

Where $\\mu_c$ is the running mean and $\\sigma_c$ is the standard deviation of the global pricing matrix. To handle heavy-tailed or non-Gaussian commodity distributions, we supplement the Z-score check with a non-parametric Interquartile Range (IQR) fence:

$$\\text{Lower Fence} = Q_1 - 1.5 \\times \\text{IQR}, \\quad \\text{Upper Fence} = Q_3 + 1.5 \\times \\text{IQR}$$

If $x_{c,t}$ violates the upper or lower fence constraints while simultaneously matching high-risk routing tags or shell company flags, the transaction entry is dynamically routed into an accelerated manual remediation queue.
"""
        }
    ],
    "market": [
        {
            "slug": "vpin-toxicity-modeling",
            "title": "Volume-Synchronized Probability of Toxicity (VPIN) in High-Frequency Order Streams",
            "tags": ["market", "microstructure", "quantitative-finance"],
            "cross_vectors": ["hawkes-microstructure", "zero-copy-arrow-iceberg"],
            "content": """# Volume-Synchronized Probability of Toxicity (VPIN)

## 1. Order Flow Toxicity and Information Asymmetry
In electronic matching engines, order flow toxicity represents the probability that un-informed liquidity providers (market makers) are executing trades against toxic, informed traders. Informed traders possess structural or informational asymmetric advantages, allowing them to systematically pick off stale quotes. This triggers severe inventory imbalances and structural losses for automated liquidity provision systems.

Instead of measuring information toxicity across arbitrary physical time slices (which fails to account for fluctuating market velocity), we utilize volume-synchronized time slicing. By sampling the order stream inside uniform volume buckets, we normalize the information arrival rate across highly variable trading sessions.

## 2. Mathematical Formalization of the VPIN Metric
Let $V$ be a predefined constant volume bucket size (e.g., $10,000$ shares). The trading day is divided into $B$ successive volume bars. For each volume bucket $b$, total trading activity is decomposed into buy volume $V_b^B$ and sell volume $V_b^S$ using standard trade classification heuristics (e.g., the Lee-Ready tick algorithm). The Volume-Synchronized Probability of Toxicity (VPIN) index over a sample window of $N$ volume buckets is formulated as:

$$\\text{VPIN} = \\frac{\\sum_{b=1}^N |V_b^B - V_b^S|}{N \\times V}$$

The resulting VPIN metric outputs a normalized boundary value:

$$\\text{VPIN} \\in [0, 1]$$

A VPIN value approaching $1.0$ indicates complete directional dominance of the order book by informed aggressive orders. When the VPIN crosses an empirical $99$th percentile trigger, market-making algorithms systematically pull their depth allocations to mitigate adverse selection risk, directly preceding systemic liquidity collapses.
"""
        },
        {
            "slug": "implied-volatility-surfaces",
            "title": "Implied Volatility Surface Dynamics and Arbitrage-Free Constraint Systems",
            "tags": ["market", "derivatives", "mathematical-modeling"],
            "cross_vectors": ["hawkes-microstructure"],
            "content": """# Implied Volatility Surface Dynamics

## 1. The Volatility Smile and Skew Topography
The Black-Scholes-Merton option pricing framework assumes that the underlying asset volatility is a constant parameter $\\sigma$. Empirical options market pricing explicitly refutes this assumption, forming multi-dimensional Implied Volatility Surfaces where $\\sigma_{\\text{implied}}$ varies non-linearly across both option strike prices $K$ and time-to-maturity maturities $T$:

$$\\sigma = f(K, T)$$

This structural geometry creates the *volatility smile* across equity options and the *volatility skew* across commodity and currency derivatives, reflecting the market's endogenous pricing of jump-diffusion risks and systemic tail events.

## 2. Formulation of Arbitrage-Free Structural Constraints
To prevent toxic execution strategies from draining capital pools, an options analytics engine must enforce strict mathematical constraints to guarantee that the modeled surface is entirely free of static arbitrage conditions.
* **Vertical (Butterfly) Arbitrage-Free Constraint:** The probability density function derived from option pricing must be non-negative everywhere, requiring the second partial derivative of the call price function with respect to the strike price to be greater than or equal to zero:

$$\\frac{\\partial^2 C(K, T)}{\\partial K^2} \\ge 0$$

* **Calendar Spread Arbitrage-Free Constraint:** Total implied variance must increase strictly monotonically with respect to the maturity parameter, ensuring that option values do not experience unphysical decays over time:

$$\\frac{\\partial C(K, T)}{\\partial T} \\ge 0$$

The options module continuously monitors the surface model using these partial differential bounds. Any localized surface calculation that violates these invariants is instantly isolated as an execution anomaly or a trade pricing discrepancy.
"""
        }
    ],
    "data": [
        {
            "slug": "cdc-debezium-statemachines",
            "title": "Distributed Change Data Capture (CDC) State Machines with Debezium and Kafka",
            "tags": ["data", "infrastructure", "stream-processing"],
            "cross_vectors": ["zero-copy-arrow-iceberg", "temporal-graph-aml"],
            "content": """# Distributed Change Data Capture (CDC) State Machines

## 1. Decoupled Ingestion via Transaction Log Mining
Traditional polling-based data extraction routines degrade master database performance and introduce significant ingestion latency. Advanced DataOps frameworks eliminate these performance bottlenecks by deploying log-based Change Data Capture (CDC). By mining the database's internal write-ahead logs (WAL), such as PostgreSQL's WAL or MySQL's binlog, CDC engines extract transactional state modifications asynchronously without touching active runtime execution tables.

We implement this pipeline using a fault-tolerant architecture composed of distributed Debezium source connectors running inside an Apache Kafka cluster, streaming immutable event logs into a decentralized storage lakehouse layer.

## 2. Event-Driven Schema Evolution Logic
Every database state update is wrapped by Debezium into a highly structured JSON or Apache Avro event block containing two distinct payloads: `before` and `after`. The transaction engine evaluates the structural transition vector via state machines:

$$\\Delta S = S_{\\text{after}} - S_{\\text{before}}$$

```
+------------------+       Write-Ahead Log       +------------------+
|  Source Database | --------------------------> | Debezium Engine  |
+------------------+                             +--------+---------+
                                                            |
                                                     Kafka Event Bus
                                                            |
                                                            v
+------------------+      Zero-Copy Streaming     +------------------+
| Apache Iceberg   | <-------------------------- |  Apache Flink    |
+------------------+                             +------------------+
```

When a database administrator executes a structural schema modification (e.g., appending an alternate currency code tracking column), the CDC state engine detects the schema version update via Kafka Schema Registry integrations. The downstream ingestion DAG parses the change, updates the active metadata schema configuration, and updates target tables inline without dropping connections or interrupting live compliance streams.
"""
        },
        {
            "slug": "flink-stateful-stream-joins",
            "title": "Low-Latency Stateful Stream Joins and Compaction Metrics in Apache Flink",
            "tags": ["data", "stream-processing", "distributed-systems"],
            "cross_vectors": ["zero-copy-arrow-iceberg", "temporal-graph-aml", "vpin-toxicity-modeling"],
            "content": """# Low-Latency Stateful Stream Joins in Apache Flink

## 1. Temporal Alignment under Variable Network Latency
Executing continuous real-time multi-source data joins requires reconciling distinct, asynchronous data streams under volatile network transmission speeds. In high-performance compliance filtering and high-frequency trading architectures, merging a transaction event stream against a dynamic market data feed requires strict temporal alignment.

Apache Flink solves this by managing distributed state abstractions over localized RocksDB key-value storage backends. Data rows are evaluated using Event-Time attributes rather than Processing-Time metrics, allowing the system to maintain processing consistency regardless of network out-of-order delivery patterns.

## 2. Bounded Window Co-Group Processing Constraints
To execute a stateful streaming join between Transaction Stream $A$ and Order Book Stream $B$ within a specified time tolerance window $\\pm \\Delta t$, we define an interval join condition over the respective data timelines:

$$A_{\\text{time}} - \\Delta t_1 \\le B_{\\text{time}} \\le A_{\\text{time}} + \\Delta t_2$$

The Flink engine maintains execution states within these time boundaries by generating dynamic progress markers called *Watermarks*. A Watermark $W(t)$ asserts that all subsequent event payloads will arrive with timestamps greater than $t$:

$$t_{\\text{event}} > W(t)$$

```
Stream A: --(t=12)--(t=15)--(t=18)--[Watermark W=15]--> (Drop older events)
                              |
                         State Compaction
                              |
                              v
                         RocksDB Cleared
```

Once the Watermark surpasses the active evaluation window, Flink triggers state compaction, purging obsolete records from the RocksDB backend. This maintains low-latency execution while ensuring that processing memory limits remain strictly bounded even under sustained multi-gigabyte throughput loads.
"""
        }
    ]
}


def escape_body(text: str) -> str:
    """Escape standalone < in body (not in YAML frontmatter) to prevent strip_html mangling."""
    m = re.match(r'^(---\s*\n.*?\n---\s*\n)(.*)', text, re.DOTALL)
    if m:
        return m.group(1) + m.group(2).replace('<', '&lt;')
    return text.replace('<', '&lt;')


def main():
    now = datetime.now(timezone.utc)
    today = now.strftime("%Y-%m-%d")
    today_iso = now.isoformat()

    # 1. Write Markdown documents to filesystem
    for pillar, files in KNOWLEDGE_VAULT.items():
        pillar_dir = ROOT / "content" / pillar
        pillar_dir.mkdir(parents=True, exist_ok=True)

        for file_data in files:
            file_path = pillar_dir / f"{file_data['slug']}.md"

            all_tags = file_data["tags"] + file_data["cross_vectors"]
            frontmatter = (
                "---\n"
                f'title: "{file_data["title"]}"\n'
                f'slug: "{file_data["slug"]}"\n'
                f'pillar: "{pillar}"\n'
                "quality_score: 1.0\n"
                "content_type: \"deep-domain\"\n"
                f"tags: {json.dumps(all_tags)}\n"
                f"cross_vectors: {json.dumps(file_data['cross_vectors'])}\n"
                "---\n\n"
            )

            full_content = frontmatter + file_data["content"].strip()
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(full_content)
            print(f"Ingested: {file_path.relative_to(ROOT)}")

    # 2. Register in registry.json under content key (matching existing pattern)
    reg_path = ROOT / "registry.json"
    with open(reg_path, "r", encoding="utf-8") as f:
        registry = json.load(f)

    content_list = registry.setdefault("content", [])
    existing_slugs = {item["slug"] for item in content_list}
    added = 0

    for pillar, files in KNOWLEDGE_VAULT.items():
        for file_data in files:
            slug = file_data["slug"]
            if slug in existing_slugs:
                print(f"  Skipped {slug} (already in registry)")
                continue

            # Load body from the file we just wrote
            md_path = ROOT / "content" / pillar / f"{slug}.md"
            body = ""
            if md_path.exists():
                raw = md_path.read_text(encoding="utf-8")
                match = re.match(r"^---\s*\n.*?\n---\s*\n(.*)", raw, re.DOTALL)
                body = escape_body(match.group(1).strip() if match else raw.strip())

            all_tags = file_data["tags"] + file_data["cross_vectors"]

            entry = {
                "slug": slug,
                "title": file_data["title"],
                "description": file_data["content"].splitlines()[1][:250] if len(file_data["content"].splitlines()) > 1 else file_data["title"],
                "body_html": f"<pre>{body}</pre>",
                "category": "knowledge",
                "content_type": "knowledge",
                "tags": all_tags,
                "pillar": pillar,
                "author": "AcaciaFund",
                "date_str": today,
                "sqi": 1.0,
                "language": "en",
                "created_at": today_iso,
                "updated_at": today_iso,
                "deprecated": False,
                "enriched": True,
                "enriched_at": today,
            }
            content_list.append(entry)
            existing_slugs.add(slug)
            added += 1
            print(f"  Registered {slug} ({file_data['title'][:60]}...)")

    registry["content"] = content_list
    registry["last_updated"] = today
    registry["last_run"] = today

    with open(reg_path, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2, ensure_ascii=False)

    print(f"\nDone — {added} new vault entries integrated into registry.json")
    if added > 0:
        print("Run `python build.py` to rebuild the site with the new assets.")


if __name__ == "__main__":
    main()
