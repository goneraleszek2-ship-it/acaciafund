#!/usr/bin/env python3
"""
Learn Module Generator

Generates interactive learn modules from ontology concepts and inspiration sources.
Creates hands-on learning content with:
- Multi-section body with code examples
- Bloom taxonomy questions
- Flashcards
- Prerequisites from ontology relations
- Cross-pillar connections

Output: Updates registry.json with new learn entries.
"""

import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

logger = logging.getLogger(__name__)

from core.ontology import OntologyManager  # noqa: E402

PROJECT_ROOT = Path(__file__).parent.parent
ONTOLOGY_PATH = PROJECT_ROOT / "data" / "ontology.json"
REGISTRY_PATH = PROJECT_ROOT / "registry.json"

# ── Module Definitions ──────────────────────────────────────────────────
# Each module is a structured template for generating learn content

MODULES = [
    # ─── DATA ENGINEERING (4 modules) ──────────────────────────────────
    {
        "slug": "data/learn/pyspark-fundamentals",
        "title": "PySpark Fundamentals: Distributed Data Processing at Scale",
        "pillar": "data-engineering",
        "tags": ["pyspark", "spark", "data-engineering", "distributed-computing", "big-data"],
        "difficulty": "intermediate",
        "prerequisites": ["data-engineering-basics", "data-pipeline-architectures"],
        "description": "Master PySpark DataFrame API, Spark SQL, and distributed processing patterns for building production data pipelines.",
        "sections": [
            {
                "heading": "What is PySpark?",
                "content": """<p>PySpark is the Python API for Apache Spark — a unified analytics engine for large-scale data processing. Spark provides an interface for programming entire clusters with implicit data parallelism and fault tolerance.</p>
<p>Key advantages over single-machine processing:</p>
<ul>
<li><strong>In-memory computation</strong> — up to 100x faster than Hadoop MapReduce for certain workloads</li>
<li><strong>Lazy evaluation</strong> — builds an optimized execution plan before running</li>
<li><strong>Unified API</strong> — same codebase for batch, streaming, SQL, and ML workloads</li>
<li><strong>Horizontal scaling</strong> — add nodes to handle larger datasets</li>
</ul>"""
            },
            {
                "heading": "SparkSession and DataFrames",
                "content": """<p>The SparkSession is your entry point to Spark functionality. It creates a bridge between your Python code and the distributed Spark engine.</p>
<pre><code class="language-python">from pyspark.sql import SparkSession
from pyspark.sql.functions import col, avg, count, when

# Initialize SparkSession
spark = SparkSession.builder \\
    .appName("AcaciaFund Analytics") \\
    .config("spark.sql.shuffle.partitions", "200") \\
    .getOrCreate()

# Read data from various sources
df = spark.read.parquet("s3://bucket/transactions/")
df_json = spark.read.json("s3://bucket/market-data/")
df_csv = spark.read.option("header", True).csv("s3://bucket/reports/")

# Basic transformations
result = df \\
    .filter(col("amount") > 10000) \\
    .groupBy("category") \\
    .agg(
        count("*").alias("transaction_count"),
        avg("amount").alias("avg_amount")
    ) \\
    .orderBy(col("avg_amount").desc())

result.show()</code></pre>"""
            },
            {
                "heading": "Transformations and Actions",
                "content": """<p>Spark operations fall into two categories:</p>
<ul>
<li><strong>Transformations</strong> (lazy) — <code>filter()</code>, <code>select()</code>, <code>groupBy()</code>, <code>join()</code>, <code>withColumn()</code></li>
<li><strong>Actions</strong> (eager) — <code>show()</code>, <code>collect()</code>, <code>count()</code>, <code>write()</code></li>
</ul>
<p>The Catalyst optimizer automatically optimizes your query plan, combining operations and eliminating unnecessary shuffles.</p>
<pre><code class="language-python"># Window functions for time-series analysis
from pyspark.sql.window import Window
from pyspark.sql.functions import lag, lead, dense_rank

window_spec = Window.partitionBy("asset_class").orderBy("date")

df_with_returns = df \\
    .withColumn("prev_close", lag("close", 1).over(window_spec)) \\
    .withColumn("daily_return", 
        (col("close") - col("prev_close")) / col("prev_close")) \\
    .withColumn("volatility_30d", 
        avg("daily_return").over(
            Window.partitionBy("asset_class")
                  .orderBy("date")
                  .rowsBetween(-30, -1)
        )
    )</code></pre>"""
            },
            {
                "heading": "Performance Optimization",
                "content": """<p>Key techniques for production PySpark workloads:</p>
<ul>
<li><strong>Partitioning</strong> — Control data distribution with <code>repartition()</code> and <code>coalesce()</code></li>
<li><strong>Caching</strong> — Use <code>cache()</code> or <code>persist()</code> for DataFrames reused across actions</li>
<li><strong>Broadcast joins</strong> — Automatically broadcasts small tables to avoid shuffles</li>
<li><strong>Bucketing</strong> — Pre-partition data by join keys for efficient joins</li>
</ul>
<pre><code class="language-python"># Cache frequently accessed data
transactions = spark.read.parquet("s3://transactions/").cache()

# Broadcast join for small dimension table
from pyspark.sql.functions import broadcast
enriched = transactions.join(broadcast(risk_scores), "customer_id")

# Optimize partition count for output
result.repartition(200, "date") \\
    .write \\
    .partitionBy("date") \\
    .parquet("s3://output/enriched-transactions/")</code></pre>"""
            },
        ],
        "bloom_questions": [
            {"level": "remember", "question": "What are the two main types of operations in PySpark?"},
            {"level": "understand", "question": "Why does Spark use lazy evaluation, and how does it benefit performance?"},
            {"level": "apply", "question": "Write a PySpark query to find the top 5 categories by total transaction volume in the last 30 days."},
            {"level": "analyze", "question": "Compare and contrast repartition() vs coalesce() — when would you use each?"},
            {"level": "evaluate", "question": "A PySpark job is running 10x slower than expected. What profiling steps would you take?"},
            {"level": "create", "question": "Design a PySpark pipeline that ingests raw transactions, applies AML risk scoring, and outputs enriched data partitioned by date."},
        ],
        "flashcards": [
            {"front": "What is a SparkSession?", "back": "The single entry point to all Spark functionality, created via SparkSession.builder"},
            {"front": "What is lazy evaluation in Spark?", "back": "Transformations are recorded but not executed until an action is called, allowing the Catalyst optimizer to plan the most efficient execution path"},
            {"front": "What is a broadcast join?", "back": "A join strategy where the smaller table is broadcast to all executors, avoiding expensive shuffle operations"},
        ],
    },
    {
        "slug": "data/learn/partitioning-strategies",
        "title": "Partitioning Strategies: Optimizing Data Layout for Performance",
        "pillar": "data-engineering",
        "tags": ["partitioning", "data-layout", "performance", "data-engineering", "storage"],
        "difficulty": "intermediate",
        "prerequisites": ["pyspark-fundamentals"],
        "description": "Learn how partitioning strategies affect query performance, storage efficiency, and cost in modern data platforms.",
        "sections": [
            {
                "heading": "Why Partitioning Matters",
                "content": """<p>Partitioning determines how data is physically organized on disk or across cluster nodes. Good partitioning enables partition pruning — skipping irrelevant data during queries — which can reduce I/O by 10-100x.</p>
<p>Key trade-offs:</p>
<ul>
<li><strong>Too few partitions</strong> — large files, poor parallelism, OOM errors</li>
<li><strong>Too many partitions</strong> — high metadata overhead, small file problem</li>
<li><strong>Wrong partition key</strong> — data skew, uneven resource utilization</li>
</ul>"""
            },
            {
                "heading": "Time-Based Partitioning",
                "content": """<p>The most common pattern for analytical workloads. Partition by date (and optionally hour) for efficient time-range queries.</p>
<pre><code class="language-python"># Good: partition by date for daily queries
df.write.partitionBy("year", "month", "day") \\
    .parquet("s3://lake/transactions/")

# Query only reads relevant partitions
SELECT * FROM transactions 
WHERE year = 2026 AND month = 7 AND day = 11

# iceberg: hidden partitioning with transform
ALTER TABLE transactions ADD PARTITION FIELD 
    days(ts)  -- automatic daily partitioning</code></pre>
<p><strong>Rule of thumb:</strong> Target 128MB-1GB per partition file. For daily partitions processing 1TB/day, this means ~1000 partitions per day.</p>"""
            },
            {
                "heading": "Hash Partitioning for Joins",
                "content": """<p>When joining large datasets on a common key, hash-partitioning both datasets by that key ensures co-located data and minimizes network shuffles.</p>
<pre><code class="language-python"># Pre-bucket by customer_id for efficient joins
df.write \\
    .bucketBy(256, "customer_id") \\
    .sortBy("customer_id") \\
    .saveAsTable("transactions_bucketed")

# Delta Lake: Z-ORDER for multi-dimensional pruning
OPTIMIZE transactions
ZORDER BY (customer_id, transaction_date)</code></pre>"""
            },
            {
                "heading": "Monitoring Partition Health",
                "content": """<p>Regularly check for partition skew and small files:</p>
<pre><code class="language-python"># Check partition sizes
df.groupBy("date").count().show()

# Iceberg: check for small files
SELECT path, file_size_in_bytes 
FROM table.files(table_name) 
ORDER BY file_size_in_bytes ASC
LIMIT 20

# Fix: compact small files
ALTER TABLE transactions EXECUTE optimize 
WHERE date = '2026-07-11'</code></pre>"""
            },
        ],
        "bloom_questions": [
            {"level": "remember", "question": "What is partition pruning?"},
            {"level": "understand", "question": "Why might partitioning by a high-cardinality column cause problems?"},
            {"level": "apply", "question": "Design a partitioning scheme for a financial transactions table queried primarily by date range and customer ID."},
            {"level": "analyze", "question": "Analyze the trade-offs between date-based partitioning and hash partitioning for a real-time analytics workload."},
        ],
        "flashcards": [
            {"front": "What is partition pruning?", "back": "The ability of a query engine to skip reading partitions that don't match the query's filter conditions, reducing I/O"},
            {"front": "What is the small file problem?", "back": "When too many small partition files create excessive metadata overhead and slow down query planning"},
            {"front": "What is Z-ORDER?", "back": "A data layout optimization in Delta Lake/Iceberg that co-locates data across multiple columns for efficient multi-dimensional queries"},
        ],
    },
    {
        "slug": "data/learn/spike-data-pipelines",
        "title": "Building Resilient Data Pipelines with Spark and dbt",
        "pillar": "data-engineering",
        "tags": ["spark", "dbt", "data-pipelines", "dataops", "testing", "data-engineering"],
        "difficulty": "intermediate",
        "prerequisites": ["pyspark-fundamentals", "building-pipelines-dbt-dagster"],
        "description": "Combine Spark's processing power with dbt's transformation layer to build production-grade, tested, documented data pipelines.",
        "sections": [
            {
                "heading": "Architecture: Spark + dbt",
                "content": """<p>The modern data stack combines Spark for heavy ETL processing with dbt for SQL-based transformations, testing, and documentation:</p>
<ul>
<li><strong>Spark</strong> — ingestion, heavy computation, ML feature engineering</li>
<li><strong>dbt</strong> — business logic transformations, data quality tests, documentation</li>
<li><strong>Orchestration</strong> — Dagster/Airflow coordinates Spark jobs → dbt runs</li>
</ul>
<pre><code class="language-python"># Spark: heavy lifting (ingestion, joins, aggregation)
# dbt/models/staging/stg_transactions.sql
WITH source AS (
    SELECT * FROM {{ source('raw', 'transactions') }}
),
cleaned AS (
    SELECT
        transaction_id,
        customer_id,
        CAST(amount AS DECIMAL(18,2)) AS amount,
        UPPER(currency) AS currency,
        DATE(transaction_ts) AS transaction_date,
        CASE 
            WHEN amount > 10000 THEN 'high_value'
            WHEN amount > 1000 THEN 'medium'
            ELSE 'standard'
        END AS value_tier
    FROM source
    WHERE transaction_id IS NOT NULL
)
SELECT * FROM cleaned</code></pre>"""
            },
            {
                "heading": "Data Quality Tests",
                "content": """<p>dbt tests validate your data at every transformation step:</p>
<pre><code class="language-yaml"># dbt/models/staging/schema.yml
version: 2
models:
  - name: stg_transactions
    columns:
      - name: transaction_id
        tests:
          - unique
          - not_null
      - name: amount
        tests:
          - not_null
          - dbt_utils.accepted_range:
              min_value: 0
              max_value: 10000000
      - name: currency
        tests:
          - accepted_values:
              values: ['USD', 'EUR', 'GBP', 'JPY']</code></pre>"""
            },
            {
                "heading": "Lineage and Documentation",
                "content": """<p>dbt auto-generates lineage graphs and documentation. Combined with Spark's execution plans, you get end-to-end visibility:</p>
<ul>
<li><strong>Column-level lineage</strong> — trace any metric back to its raw source</li>
<li><strong>Impact analysis</strong> — understand downstream effects of schema changes</li>
<li><strong>Run history</strong> — track freshness, execution time, and test results</li>
</ul>"""
            },
        ],
        "bloom_questions": [
            {"level": "remember", "question": "What are the key responsibilities of Spark vs dbt in a modern data pipeline?"},
            {"level": "understand", "question": "Why separate data processing (Spark) from business logic transformations (dbt)?"},
            {"level": "apply", "question": "Write a dbt model that calculates daily transaction totals and flags anomalous days."},
            {"level": "evaluate", "question": "Evaluate whether this architecture is appropriate for a real-time fraud detection system."},
        ],
        "flashcards": [
            {"front": "What does dbt stand for?", "back": "Data Build Tool — a SQL-based transformation framework for analytics engineering"},
            {"front": "What is dbt lineage?", "back": "The automatic graph of dependencies between models, showing how data flows from raw sources through transformations to final outputs"},
        ],
    },

    # ─── COMPLIANCE (3 modules) ────────────────────────────────────────
    {
        "slug": "aml/learn/kyc-cdd-workflows",
        "title": "KYC/CDD Workflows: From Onboarding to Ongoing Monitoring",
        "pillar": "aml",
        "tags": ["kyc", "cdd", "customer-due-diligence", "compliance", "aml", "onboarding"],
        "difficulty": "intermediate",
        "prerequisites": ["aml-basics", "aml-compliance-glossary"],
        "description": "Deep-dive into Know Your Customer and Customer Due Diligence processes — the frontline defense against financial crime.",
        "sections": [
            {
                "heading": "The KYC/CDD Framework",
                "content": """<p>KYC/CDD is mandated by FATF Recommendation 10 and forms the foundation of AML compliance. It requires financial institutions to:</p>
<ol>
<li><strong>Identify</strong> — verify the identity of customers and beneficial owners</li>
<li><strong>Understand</strong> — the nature and purpose of the business relationship</li>
<li><strong>Monitor</strong> — ongoing transactions and update customer information</li>
</ol>
<p>The three tiers of due diligence:</p>
<ul>
<li><strong>Simplified Due Diligence (SDD)</strong> — low-risk customers, basic verification</li>
<li><strong>Customer Due Diligence (CDD)</strong> — standard risk, full identity verification + source of funds</li>
<li><strong>Enhanced Due Diligence (EDD)</strong> — high-risk customers (PEPs, high-risk jurisdictions), deeper investigation</li>
</ul>"""
            },
            {
                "heading": "Onboarding Workflow",
                "content": """<pre><code>Customer Applies → Identity Verification → Risk Assessment → 
  ├─ Low Risk → SDD → Approve → Ongoing Monitoring
  ├─ Medium Risk → CDD → Approve → Enhanced Monitoring
  └─ High Risk → EDD → Compliance Review → Approve/Reject → Intensive Monitoring</code></pre>
<p>Key data points collected during onboarding:</p>
<ul>
<li>Full legal name, date of birth, nationality</li>
<li>Residential address (proof of address)</li>
<li>Identification documents (passport, national ID)</li>
<li>Source of funds / source of wealth</li>
<li>Purpose of account / business relationship</li>
<li>Beneficial ownership (for legal entities: 25%+ ownership threshold)</li>
</ul>"""
            },
            {
                "heading": "Ongoing Monitoring and Periodic Review",
                "content": """<p>CDD is not a one-time event. Institutions must:</p>
<ul>
<li><strong>Transaction monitoring</strong> — flag unusual patterns (velocity, amounts, counterparties)</li>
<li><strong>Periodic review</strong> — refresh customer information based on risk rating</li>
<li><strong>Watchlist screening</strong> — check against sanctions lists, PEP databases, adverse media</li>
<li><strong>Trigger events</strong> — re-verify when material changes occur</li>
</ul>
<p><strong>Risk-based approach:</strong> FATF recommends calibrating review frequency to customer risk level — high-risk customers reviewed at least annually, low-risk every 3-5 years.</p>"""
            },
        ],
        "bloom_questions": [
            {"level": "remember", "question": "What are the three tiers of due diligence?"},
            {"level": "understand", "question": "Why is beneficial ownership verification particularly challenging for complex corporate structures?"},
            {"level": "apply", "question": "Design a risk-scoring matrix for customer onboarding that considers jurisdiction, business type, and transaction patterns."},
            {"level": "analyze", "question": "Analyze how a fintech startup's KYC process differs from a traditional bank's — what are the regulatory risks?"},
            {"level": "evaluate", "question": "Critically assess whether AI-powered identity verification can replace manual KYC review."},
        ],
        "flashcards": [
            {"front": "What is KYC?", "back": "Know Your Customer — the process of verifying the identity, suitability, and risks of customers"},
            {"front": "What is EDD?", "back": "Enhanced Due Diligence — deeper investigation applied to high-risk customers, including source of wealth verification"},
            {"front": "What is the 25% beneficial ownership threshold?", "back": "FATF recommends identifying natural persons who own 25% or more of a legal entity as beneficial owners"},
        ],
    },
    {
        "slug": "aml/learn/sar-filing-scenarios",
        "title": "SAR Filing Scenarios: Identifying and Reporting Suspicious Activity",
        "pillar": "aml",
        "tags": ["sar", "suspicious-activity-reports", "fincen", "compliance", "aml", "reporting"],
        "difficulty": "advanced",
        "prerequisites": ["aml-basics", "kyc-cdd-workflows", "aml-compliance-glossary"],
        "description": "Master the art of Suspicious Activity Report writing through real-world scenarios — structuring, layering, trade-based ML, and crypto red flags.",
        "sections": [
            {
                "heading": "When to File a SAR",
                "content": """<p>Under the Bank Secrecy Act (BSA), financial institutions must file a SAR when they know, suspect, or have reason to suspect that a transaction:</p>
<ul>
<li>Involves funds derived from illegal activity</li>
<li>Is designed to evade BSA reporting requirements (structuring)</li>
<li>Lacks a lawful purpose or is unusual for the customer</li>
<li>Involves use of the institution to facilitate criminal activity</li>
</ul>
<p><strong>Filing thresholds:</strong></p>
<ul>
<li>Transactions ≥ $5,000 involving suspected criminal activity</li>
<li>Any amount for certain offenses (money laundering, terrorism)</li>
<li>$25,000+ if suspect is unknown</li>
</ul>"""
            },
            {
                "heading": "Scenario 1: Structuring",
                "content": """<p><strong>Pattern:</strong> Multiple cash deposits just below the $10,000 CTR threshold.</p>
<p><strong>Red flags:</strong></p>
<ul>
<li>Multiple deposits of $9,000-$9,999 within a short period</li>
<li>Deposits at different branches or ATMs</li>
<li>Customer appears to receive cash from multiple sources</li>
<li>Customer is evasive about the source of funds</li>
</ul>
<p><strong>SAR narrative example:</strong> "Account holder made 7 cash deposits between [dates] totaling $67,400, with individual deposits ranging from $8,500 to $9,800. Deposits were made at 3 different branch locations. When asked about the source, customer stated 'tips from work' but employment records show monthly salary of $3,200."</p>"""
            },
            {
                "heading": "Scenario 2: Layering through Shell Companies",
                "content": """<p><strong>Pattern:</strong> Rapid movement of funds through multiple corporate accounts with no apparent business purpose.</p>
<p><strong>Red flags:</strong></p>
<ul>
<li>Wire transfers between related entities with no clear commercial reason</li>
<li>Companies registered in secrecy jurisdictions</li>
<li>Nominee directors or shareholders</li>
<li>Funds flowing in circles (A → B → C → A)</li>
</ul>"""
            },
        ],
        "bloom_questions": [
            {"level": "remember", "question": "What are the SAR filing thresholds under the BSA?"},
            {"level": "understand", "question": "Why is structuring itself a criminal offense even if the underlying funds are legitimate?"},
            {"level": "apply", "question": "Write a SAR narrative for a scenario where a customer receives multiple international wire transfers from high-risk jurisdictions."},
            {"level": "analyze", "question": "Compare SAR filing requirements across the US (FinCEN), UK (NCA), and Canada (FINTRAC)."},
            {"level": "evaluate", "question": "Evaluate the effectiveness of current SAR filing processes in disrupting criminal financial networks."},
        ],
        "flashcards": [
            {"front": "What is structuring?", "back": "The deliberate breaking up of transactions to avoid currency transaction reporting thresholds (e.g., keeping deposits below $10,000)"},
            {"front": "What is a SAR?", "back": "Suspicious Activity Report — a document filed with FinCEN (US) or equivalent authority when suspicious transactions are detected"},
            {"front": "What is layering?", "back": "The second stage of money laundering — moving funds through multiple accounts/entities to obscure their origin"},
        ],
    },
    {
        "slug": "aml/learn/sanctions-screening",
        "title": "Sanctions Screening: Tools, Techniques, and Compliance Challenges",
        "pillar": "aml",
        "tags": ["sanctions", "ofac", "screening", "compliance", "aml", "pep"],
        "difficulty": "intermediate",
        "prerequisites": ["aml-basics", "aml-compliance-glossary"],
        "description": "Navigate the complex landscape of sanctions compliance — OFAC SDN lists, screening technologies, and managing false positives.",
        "sections": [
            {
                "heading": "Sanctions Landscape",
                "content": """<p>Sanctions are enforced by multiple authorities with overlapping but distinct lists:</p>
<ul>
<li><strong>OFAC SDN List</strong> — Specially Designated Nationals (US, ~12,000 entries)</li>
<li><strong>EU Consolidated List</strong> — EU restrictive measures</li>
<li><strong>UK HMT Sanctions List</strong> — UK autonomous sanctions</li>
<li><strong>UN Security Council</strong> — UN sanctions regimes</li>
<li><strong>FATF Grey/Black Lists</strong> — Non-cooperative jurisdictions</li>
</ul>
<p>Strict liability applies: organizations can be penalized even for inadvertent violations.</p>"""
            },
            {
                "heading": "Screening Technologies",
                "content": """<p>Modern sanctions screening systems use multiple matching techniques:</p>
<ul>
<li><strong>Exact matching</strong> — direct name comparison (fast but misses variants)</li>
<li><strong>Fuzzy matching</strong> — Levenshtein distance, Soundex, metaphone</li>
<li><strong>Transliteration matching</strong> — handles Arabic/Cyrillic/Chinese name variations</li>
<li><strong>Alias matching</strong> — checks known aliases, nicknames, abbreviation variants</li>
</ul>
<p><strong>Key challenge:</strong> Balancing sensitivity (catching true matches) with specificity (minimizing false positives). Industry average false positive rate is 95-99%.</p>"""
            },
            {
                "heading": "Managing False Positives",
                "content": """<p>A tiered approach to reducing alert fatigue:</p>
<ol>
<li><strong>Pre-screening</strong> — apply identity context (DOB, nationality, ID numbers) to filter obvious non-matches</li>
<li><strong>Scoring engine</strong> — assign confidence scores to matches, auto-clear below threshold</li>
<li><strong>Analyst review queue</strong> — prioritize by risk score and customer exposure</li>
<li><strong>Feedback loop</strong> — train matching algorithms on analyst decisions</li>
</ol>"""
            },
        ],
        "bloom_questions": [
            {"level": "remember", "question": "What are the main sanctions lists that financial institutions must screen against?"},
            {"level": "understand", "question": "Why is transliteration matching essential for sanctions compliance?"},
            {"level": "apply", "question": "Design a screening workflow that minimizes false positives while maintaining compliance coverage."},
            {"level": "evaluate", "question": "Evaluate whether AI-based fuzzy matching can safely reduce manual review volumes."},
        ],
        "flashcards": [
            {"front": "What is the OFAC SDN List?", "back": "Specially Designated Nationals and Blocked Persons List — maintained by OFAC, it identifies individuals and entities subject to US sanctions"},
            {"front": "What is strict liability in sanctions?", "back": "Legal doctrine where violations are penalized regardless of intent — even accidental sanctions breaches carry penalties"},
        ],
    },

    # ─── MARKETS (3 modules) ───────────────────────────────────────────
    {
        "slug": "markets/learn/quantitative-methods-intro",
        "title": "Quantitative Methods in Finance: From Descriptive Statistics to Factor Models",
        "pillar": "stock",
        "tags": ["quantitative", "statistics", "factor-models", "finance", "markets"],
        "difficulty": "intermediate",
        "prerequisites": ["market-fundamentals", "science-method"],
        "description": "Foundation of quantitative finance — statistical methods, risk measures, and multi-factor models used in institutional portfolio management.",
        "sections": [
            {
                "heading": "Why Quantitative Methods?",
                "content": """<p>Quantitative methods bring mathematical rigor to investment analysis, replacing intuition with systematic, testable frameworks. They underpin:</p>
<ul>
<li><strong>Risk management</strong> — Value at Risk, expected shortfall, stress testing</li>
<li><strong>Portfolio construction</strong> — mean-variance optimization, risk parity</li>
<li><strong>Alpha generation</strong> — factor-based strategies, statistical arbitrage</li>
<li><strong>Execution</strong> — algorithmic trading, optimal order placement</li>
</ul>"""
            },
            {
                "heading": "Key Statistical Concepts",
                "content": """<p>Essential statistics for financial analysis:</p>
<ul>
<li><strong>Distribution</strong> — returns are approximately normal but fat-tailed (excess kurtosis ~3-10)</li>
<li><strong>Correlation</strong> — assets become correlated during crises (correlation breakdown)</li>
<li><strong>Volatility clustering</strong> — high-vol periods follow high-vol (GARCH effects)</li>
<li><strong>Stationarity</strong> — many financial time series are non-stationary (unit roots)</li>
</ul>
<pre><code class="language-python">import numpy as np
import pandas as pd

# Annualized volatility from daily returns
daily_returns = prices.pct_change().dropna()
ann_volatility = daily_returns.std() * np.sqrt(252)

# Sharpe ratio
sharpe = (annualized_return - risk_free_rate) / ann_volatility

# Maximum drawdown
cumulative = (1 + daily_returns).cumprod()
running_max = cumulative.cummax()
drawdown = (cumulative - running_max) / running_max
max_drawdown = drawdown.min()</code></pre>"""
            },
            {
                "heading": "Factor Models",
                "content": """<p>Factor models explain asset returns through exposure to systematic risk factors:</p>
<pre><code class="language-python"># Fama-French 3-Factor Model
# Ri - Rf = alpha + b1*(Rm-Rf) + b2*SMB + b3*HML + epsilon

# Returns decomposition:
# Market risk (beta) — compensation for systematic risk
# Size (SMB) — small minus big cap returns
# Value (HML) — high book-to-market minus low
# Alpha — idiosyncratic return (skill or luck)

# Implementation with statsmodels
import statsmodels.api as sm

X = sm.add_constant(portfolio_returns - risk_free_rate)
model = sm.OLS(excess_returns, X).fit()
print(model.summary())</code></pre>"""
            },
        ],
        "bloom_questions": [
            {"level": "remember", "question": "What are the three factors in the Fama-French model?"},
            {"level": "understand", "question": "Why do financial returns exhibit fat tails, and what are the implications for risk management?"},
            {"level": "apply", "question": "Calculate the Sharpe ratio, Sortino ratio, and maximum drawdown for a given return series."},
            {"level": "analyze", "question": "Compare factor-based investing vs. traditional active management — what are the trade-offs?"},
            {"level": "evaluate", "question": "Critically assess whether factor models are reliable guides during market regime changes."},
        ],
        "flashcards": [
            {"front": "What is the Sharpe ratio?", "back": "The excess return per unit of total risk (volatility): (R - Rf) / σ. Higher is better, typically > 1 is considered good"},
            {"front": "What is fat tails?", "back": "The tendency of financial returns to have more extreme events than a normal distribution would predict"},
            {"front": "What is a factor model?", "back": "A model that explains asset returns as exposure to systematic risk factors (market, size, value, momentum, etc.) plus idiosyncratic alpha"},
        ],
    },
    {
        "slug": "markets/learn/volatility-analysis",
        "title": "Volatility Analysis: Measuring, Modeling, and Trading Uncertainty",
        "pillar": "stock",
        "tags": ["volatility", "options", "vix", "garch", "markets", "risk"],
        "difficulty": "advanced",
        "prerequisites": ["quantitative-methods-intro", "market-fundamentals"],
        "description": "Understand volatility as an asset class — from historical vol to implied vol surfaces, VIX dynamics, and volatility trading strategies.",
        "sections": [
            {
                "heading": "Types of Volatility",
                "content": """<ul>
<li><strong>Historical volatility</strong> — realized standard deviation of past returns</li>
<li><strong>Implied volatility</strong> — market's expectation of future vol, embedded in option prices</li>
<li><strong>Forward volatility</strong> — expected vol between two future dates (extracted from options)</li>
<li><strong>Local volatility</strong> — vol that varies by price level and time (Dupire model)</li>
</ul>
<p>The <strong>VIX Index</strong> (CBOE Volatility Index) measures 30-day implied volatility of S&P 500 options — often called the "fear gauge."</p>"""
            },
            {
                "heading": "Volatility Modeling",
                "content": """<pre><code class="language-python"># GARCH(1,1) — the workhorse volatility model
from arch import arch_model

returns = prices.pct_change().dropna() * 100
model = arch_model(returns, vol='Garch', p=1, q=1)
result = model.fit(disp='off')

# Conditional volatility forecast
forecasts = result.forecast(horizon=5)
predicted_vol = forecasts.variance.iloc[-1].values

# EWMA — faster-reacting alternative
ewma_vol = returns.ewm(span=21).std() * np.sqrt(252)</code></pre>"""
            },
            {
                "heading": "Volatility Risk Premium",
                "content": """<p>Historically, implied volatility exceeds realized volatility by 2-4 percentage points on average. This <strong>volatility risk premium</strong> is compensation for bearing vol risk.</p>
<p>Strategies that harvest this premium:</p>
<ul>
<li><strong>Sell covered calls</strong> — earn premium from time decay</li>
<li><strong>Short strangles</strong> — collect premium from both sides (high risk)</li>
<li><strong>Put-write strategies</strong> — systematically sell puts on indices</li>
</ul>
<p><strong>Caution:</strong> Vol selling strategies have negative skew — small steady gains punctuated by large losses during vol spikes.</p>"""
            },
        ],
        "bloom_questions": [
            {"level": "remember", "question": "What does the VIX measure?"},
            {"level": "understand", "question": "Why does implied volatility typically exceed realized volatility?"},
            {"level": "apply", "question": "Calculate the 20-day rolling volatility and identify vol regime changes in a given price series."},
            {"level": "analyze", "question": "Compare GARCH and EWMA models for volatility forecasting — when would you prefer one over the other?"},
            {"level": "evaluate", "question": "Assess the risk-reward profile of systematically selling volatility. Is the premium sufficient compensation for tail risk?"},
        ],
        "flashcards": [
            {"front": "What is implied volatility?", "back": "The volatility value that, when plugged into an option pricing model (e.g., Black-Scholes), yields the market price of the option"},
            {"front": "What is the volatility risk premium?", "back": "The historical tendency for implied volatility to exceed realized volatility — compensation for bearing uncertainty"},
        ],
    },
    {
        "slug": "markets/learn/market-microstructure",
        "title": "Market Microstructure: How Trades Execute and Prices Form",
        "pillar": "stock",
        "tags": ["microstructure", "order-book", "liquidity", "market-making", "markets"],
        "difficulty": "advanced",
        "prerequisites": ["market-fundamentals", "quantitative-methods-intro"],
        "description": "Understand the mechanics of order execution, bid-ask spreads, market making, and how electronic markets actually work.",
        "sections": [
            {
                "heading": "Order Types and the Limit Order Book",
                "content": """<p>Every trade requires a buyer and seller. The limit order book (LOB) matches them:</p>
<ul>
<li><strong>Market orders</strong> — execute immediately at best available price (taker)</li>
<li><strong>Limit orders</strong> — execute only at specified price or better (maker)</li>
<li><strong>Stop orders</strong> — become market orders when price reaches threshold</li>
<li><strong>Iceberg orders</strong> — large orders split into smaller visible portions</li>
</ul>
<p>The <strong>bid-ask spread</strong> reflects the cost of immediacy — the difference between the best buy (bid) and best sell (ask) prices.</p>"""
            },
            {
                "heading": "Market Making",
                "content": """<p>Market makers provide liquidity by continuously posting bid and ask quotes. Their profit comes from:</p>
<ul>
<li><strong>Bid-ask spread capture</strong> — buying at bid, selling at ask</li>
<li><strong>Inventory management</strong> — rebalancing to avoid directional risk</li>
<li><strong>Adverse selection cost</strong> — losing to informed traders who know the true value</li>
</ul>
<pre><code># Simplified market making P&L
spread_income = trades * half_spread
inventory_cost = position * price_change
adverse_selection = informed_trades * loss
net_pnl = spread_income - inventory_cost - adverse_selection</code></pre>"""
            },
            {
                "heading": "Market Impact and Execution Quality",
                "content": """<p>Large orders move prices. Understanding market impact is critical for institutional execution:</p>
<ul>
<li><strong>Temporary impact</strong> — price impact that decays after execution</li>
<li><strong>Permanent impact</strong> — lasting price change from information revelation</li>
<li><strong>Implementation shortfall</strong> — difference between decision price and average execution price</li>
</ul>
<p><strong>Algorithms:</strong> TWAP (time-weighted), VWAP (volume-weighted), Implementation Shortfall, Iceberg, Sniper/Iceberg hybrid.</p>"""
            },
        ],
        "bloom_questions": [
            {"level": "remember", "question": "What is the bid-ask spread?"},
            {"level": "understand", "question": "Why do market makers face adverse selection, and how do they manage it?"},
            {"level": "apply", "question": "Design a TWAP execution strategy for a $50M equity order over a 4-hour window."},
            {"level": "analyze", "question": "Analyze how dark pools affect price discovery and market quality compared to lit exchanges."},
        ],
        "flashcards": [
            {"front": "What is a limit order book?", "back": "An electronic record of all outstanding limit orders for a security, organized by price level, where market makers provide liquidity"},
            {"front": "What is adverse selection in market making?", "back": "The risk that market makers systematically lose to informed traders who trade on superior information about true value"},
        ],
    },
]

# ── Generation Logic ──────────────────────────────────────────────────

def generate_module_body(module):
    """Generate Markdown body HTML for a learn module."""
    sections_html = []
    for section in module["sections"]:
        sections_html.append(f'<h2>{section["heading"]}</h2>')
        sections_html.append(section["content"])
    return "\n\n".join(sections_html)


# ── Auto-generate modules from ontology concepts ─────────────────────

AUTO_MODULE_PROMPT = """You are generating a learn module for an educational portal.
Concept: {concept_label} ({concept_id})
Pillar: {pillar}
Description: {description}
Category: {category}
Relations: {relations}

Generate ONLY valid JSON for a learn module with these fields:
{{
  "title": "string - clear, descriptive title",
  "description": "2-3 sentence overview",
  "difficulty": "beginner|intermediate|advanced",
  "tags": ["tag1", "tag2", "tag3"],
  "sections": [
    {{
      "heading": "Section Title",
      "content": "<p>HTML paragraph explaining the concept...</p>"
    }}
  ],
  "flashcards": [
    {{"front": "Question?", "back": "Answer"}}
  ],
  "bloom_questions": [
    {{
      "question": "Multiple choice question?",
      "choices": ["A", "B", "C", "D"],
      "correct_index": 0,
      "explanation": "Why this is correct"
    }}
  ]
}}
Generate 3-4 sections, 4-6 flashcards, 3-4 Bloom questions.
No markdown, no code fences, just JSON."""


def auto_generate_from_ontology(
    ontology, registry, llm_client=None, max_new: int = 20
) -> list[str]:
    """Auto-generate learn modules for ontology concepts missing learn content.

    Returns list of newly created slugs.
    """
    existing_slugs = {item.get("slug") for item in registry.get("content", [])}
    existing_learn_slugs = {
        item.get("slug")
        for item in registry.get("content", [])
        if item.get("content_type") == "learn"
    }

    # Find concepts without a learn module
    concepts_needing_modules = []
    for concept in ontology.concepts:
        # Check if any learn slug contains this concept id
        has_module = any(
            concept.id in slug for slug in existing_learn_slugs
        )
        if not has_module:
            concepts_needing_modules.append(concept)

    if not concepts_needing_modules:
        logger.info("  All ontology concepts already have learn modules.")
        return []

    logger.info(f"  Found {len(concepts_needing_modules)} concepts without learn modules")
    new_slugs = []
    now = datetime.now(timezone.utc).isoformat()

    for concept in concepts_needing_modules[:max_new]:
        # Determine pillar from concept
        pillar = concept.pillar if hasattr(concept, "pillar") and concept.pillar else "data"
        pillar_map = {"aml": "aml", "stock": "stock", "data-engineering": "data-engineering"}
        pillar_key = pillar_map.get(pillar, "data-engineering")

        # Build concept relations string
        relations = []
        if hasattr(concept, "category"):
            relations.append(f"category: {concept.category}")

        slug_base = concept.id.replace(" ", "-").replace("/", "-")
        slug = f"{pillar_key}/learn/{slug_base}"

        if slug in existing_slugs:
            continue

        if llm_client:
            # Use LLM to generate rich content
            prompt = AUTO_MODULE_PROMPT.format(
                concept_label=concept.label,
                concept_id=concept.id,
                pillar=pillar_key,
                description=getattr(concept, "description", concept.label),
                category=getattr(concept, "category", "foundations"),
                relations=", ".join(relations) if relations else "none",
            )
            try:
                resp = llm_client.chat.completions.create(
                    model="meta/llama-3.1-70b-instruct",
                    messages=[
                        {"role": "system", "content": "You output only valid JSON."},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.5,
                    max_tokens=2000,
                )
                raw = resp.choices[0].message.content.strip()
                if raw.startswith("```"):
                    lines = raw.split("\n")
                    lines = [line for line in lines if not line.strip().startswith("```")]
                    raw = "\n".join(lines)
                module_data = json.loads(raw)
            except Exception:
                continue
        else:
            # Deterministic fallback: minimal stub
            module_data = {
                "title": f"Understanding {concept.label}",
                "description": f"Learn about {concept.label} in the context of {pillar_key}.",
                "difficulty": "intermediate",
                "tags": [concept.id, pillar_key],
                "sections": [
                    {
                        "heading": f"What is {concept.label}?",
                        "content": f"<p>{concept.label} is a key concept in {pillar_key}. This module provides an introduction and practical understanding.</p>",
                    },
                    {
                        "heading": "Key Principles",
                        "content": f"<p>The core principles of {concept.label} include understanding its foundational assumptions and practical applications.</p>",
                    },
                ],
                "flashcards": [
                    {"front": f"What is {concept.label}?", "back": f"{concept.label} is a concept in {pillar_key}."}
                ],
                "bloom_questions": [
                    {
                        "question": f"What is {concept.label} primarily used for?",
                        "choices": ["Analysis", "Synthesis", "Evaluation", "Memory"],
                        "correct_index": 0,
                        "explanation": f"{concept.label} is primarily used for analysis in {pillar_key}.",
                    }
                ],
            }

        body_html = generate_module_body(module_data)

        item = {
            "slug": slug,
            "title": module_data.get("title", f"Understanding {concept.label}"),
            "pillar": pillar_key,
            "content_type": "learn",
            "tags": module_data.get("tags", [concept.id]),
            "description": module_data.get("description", f"Learn about {concept.label}"),
            "difficulty": module_data.get("difficulty", "intermediate"),
            "body_html": body_html,
            "bloom_questions": module_data.get("bloom_questions", []),
            "flashcards": module_data.get("flashcards", []),
            "prerequisites": [],
            "author": "AcaciaFund",
            "created_at": now,
            "updated_at": now,
            "date_str": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "auto_generated": True,
            "concept_enriched": True,
            "concept_id": concept.id,
        }

        registry["content"].append(item)
        existing_slugs.add(slug)
        new_slugs.append(slug)
        logger.info(f"  Auto-generated: {slug}")

    return new_slugs


def main():
    parser = argparse.ArgumentParser(description="Learn Module Generator")
    parser.add_argument(
        "--infer",
        action="store_true",
        help="Enable LLM-based auto-generation from ontology (requires API key)",
    )
    parser.add_argument(
        "--max-new",
        type=int,
        default=20,
        help="Max auto-generated modules to create (default: 20)",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed output",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(message)s")

    logger.info("=" * 60)
    logger.info("Learn Module Generator")
    logger.info("=" * 60)

    # Load ontology for prerequisite resolution
    ontology = None
    if ONTOLOGY_PATH.exists():
        ontology = OntologyManager.load(ONTOLOGY_PATH)

    # Load registry
    with open(REGISTRY_PATH, encoding="utf-8") as f:
        registry = json.load(f)

    existing_slugs = {item.get("slug") for item in registry.get("content", [])}
    new_modules = []
    created = 0

    now = datetime.now(timezone.utc).isoformat()

    # ── Phase 1: Hand-authored modules ────────────────────────────────
    for module in MODULES:
        slug = module["slug"]

        # Skip if already exists
        if slug in existing_slugs:
            continue

        # Generate body
        body_html = generate_module_body(module)

        # Resolve prerequisites
        prerequisites = module.get("prerequisites", [])
        prereq_slugs = []
        for prereq_name in prerequisites:
            for item in registry["content"]:
                if prereq_name in item.get("slug", ""):
                    prereq_slugs.append(item["slug"])
                    break

        # Build content item
        item = {
            "slug": slug,
            "title": module["title"],
            "pillar": module["pillar"],
            "content_type": "learn",
            "tags": module["tags"],
            "description": module["description"],
            "difficulty": module.get("difficulty", "intermediate"),
            "body_html": body_html,
            "bloom_questions": module.get("bloom_questions", []),
            "flashcards": module.get("flashcards", []),
            "prerequisites": prereq_slugs,
            "author": "AcaciaFund",
            "created_at": now,
            "updated_at": now,
            "date_str": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "auto_generated": True,
            "concept_enriched": True,
        }

        registry["content"].append(item)
        existing_slugs.add(slug)
        new_modules.append(slug)
        created += 1
        logger.info(f"  Created: {slug}")

    # ── Phase 2: Auto-generate from ontology (LLM only) ──────────────
    if ontology and args.infer:
        logger.info("\nAuto-generating modules from ontology concepts via LLM...")
        llm_client = None
        try:
            import os

            from openai import OpenAI
            api_key = os.environ.get("NVIDIA_API_KEY") or os.environ.get("OPENAI_API_KEY")
            if api_key:
                llm_client = OpenAI(
                    base_url="https://integrate.api.nvidia.com/v1",
                    api_key=api_key,
                )
        except ImportError:
            pass
        if llm_client:
            auto_slugs = auto_generate_from_ontology(
                ontology, registry, llm_client=llm_client, max_new=args.max_new
            )
            created += len(auto_slugs)
        else:
            logger.warning("  No LLM client available (missing API key or openai package)")
    elif ontology:
        logger.info("\n  Skipping auto-generation (use --infer for LLM-generated modules)")

    # Save registry
    with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2, default=str)

    logger.info(f"\n  Total new modules: {created}")
    logger.info(f"  Registry now has {len(registry['content'])} items")


if __name__ == "__main__":
    main()
