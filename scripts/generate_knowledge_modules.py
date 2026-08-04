#!/usr/bin/env python3
"""Generate deterministic knowledge items for the empty knowledge categories.

Fills the six knowledge categories that had no items:
advanced-techniques, best-practices, market-analysis, strategies,
methodology, tutorial-code.

Content is hand-authored, deterministic HTML (no LLM), mirroring
``generate_learn_modules.py``.  Runs once per category; existing slugs are
skipped so re-runs are idempotent.

Usage:
    python3 scripts/generate_knowledge_modules.py --dry-run   # preview
    python3 scripts/generate_knowledge_modules.py --apply     # write registry.json
"""

import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

REGISTRY_PATH = PROJECT_ROOT / "registry.json"

logger = logging.getLogger("generate_knowledge_modules")

# ── Hand-authored knowledge items (2 per empty category) ─────────────────
MODULES: list[dict] = [
    # ── advanced-techniques ───────────────────────────────────────────
    {
        "slug": "data/knowledge/exactly-once-streaming",
        "title": "Exactly-Once Semantics in Stream Processing",
        "pillar": "data-engineering",
        "knowledge_category": "advanced-techniques",
        "tags": ["streaming", "exactly-once", "kafka", "flink", "data-engineering"],
        "difficulty": "advanced",
        "description": "How Kafka + Flink/Spark achieve exactly-once processing: idempotent producers, transactional log offsets, and checkpoints.",
        "sections": [
            ("Why at-least-once is not enough",
             "<p>Retries after a consumer crash re-deliver messages. Without deduplication, a payment-like update is applied twice. The industry answer is not a single mechanism but a stack of guarantees: <strong>idempotent producers</strong>, <strong>transactional delivery</strong>, and <strong>checkpointed state</strong>.</p>"),
            ("The three layers of exactly-once",
             "<ul><li><strong>Idempotent writes</strong> — the broker de-duplicates retried producer batches (Kafka PID + sequence number).</li><li><strong>Transactional consumption</strong> — offsets and state commit atomically in the same transaction as output writes.</li><li><strong>End-to-end semantics</strong> — downstream sinks must be idempotent or transactional too; exactly-once does not magically extend past the pipeline boundary.</li></ul>"),
            ("What it costs",
             "<p>Transactions add latency and coordination overhead; checkpoints add state snapshots. Measure whether your SLAs actually require exactly-once, or whether at-least-once plus a deduplication key is cheaper and simpler.</p>"),
        ],
    },
    {
        "slug": "compliance/knowledge/network-analysis-aml",
        "title": "Network Analysis for AML Investigations",
        "pillar": "aml",
        "knowledge_category": "advanced-techniques",
        "tags": ["aml", "network-analysis", "financial-intelligence", "transaction-monitoring"],
        "difficulty": "advanced",
        "description": "Graph methods for financial crime: entity resolution, community detection, and link prediction on transaction graphs.",
        "sections": [
            ("From transactions to graphs",
             "<p>Each transfer is an edge (sender → receiver, amount, timestamp). Aggregated over time the graph exposes structure no single account review shows: mule clusters, layering chains, and common beneficiaries across unrelated account holders.</p>"),
            ("Techniques that matter",
             "<ul><li><strong>Entity resolution</strong> — dedupe identifiers (names, addresses, devices) before graph construction.</li><li><strong>Community detection</strong> — label-propagation / Louvain find tightly-knit groups consistent with money mules.</li><li><strong>Centrality + motif counts</strong> — high betweenness accounts that fan out funds quickly are classic layering signatures.</li></ul>"),
            ("Operationalise with risk scoring",
             "<p>Convert graph features (community density, path lengths to flagged accounts, fan-out ratio) into numeric scores consumed by the transaction-monitoring engine, then route to investigation worklists.</p>"),
        ],
    },
    # ── best-practices ─────────────────────────────────────────────────
    {
        "slug": "data/knowledge/sqi-scoring-explained",
        "title": "SQI Scoring Explained: How Acacia Ranks Sources",
        "pillar": "data-engineering",
        "knowledge_category": "best-practices",
        "tags": ["sqi", "quality", "research-methodology", "data-quality"],
        "difficulty": "beginner",
        "description": "What the Source Quality Index measures, how scores are computed, and how to read them when browsing the portal.",
        "sections": [
            ("What SQI is",
             "<p>The Source Quality Index (0–1) scores each item on provenance, recency, and internal consistency. 0.9+ means peer-reviewed or primary regulatory text; 0.5–0.8 means reputable secondary coverage; below 0.4 treat as tertiary or unverified.</p>"),
            ("What feeds the score",
             "<ul><li><strong>Source authority</strong> — journals and regulators beat blogs and forums.</li><li><strong>Evidence level</strong> — empirical studies with citations score above opinions.</li><li><strong>Cross-pillar reach</strong> — content that links concepts across pillars earns a semantic bonus.</li></ul>"),
            ("Reading SQI in practice",
             "<p>Use SQI to sequence your reading: build foundations from 0.85+ sources, then triangulate claims from lower-scored items. A single high-SQI source is not a citation chain — trace the originals.</p>"),
        ],
    },
    {
        "slug": "compliance/knowledge/cdd-kyc-verification-checklist",
        "title": "CDD/KYC Verification Checklist",
        "pillar": "aml",
        "knowledge_category": "best-practices",
        "tags": ["cdd", "kyc", "aml", "verification", "onboarding"],
        "difficulty": "beginner",
        "description": "A practical onboarding checklist: identity verification, beneficial ownership, PEP screening, and ongoing monitoring.",
        "sections": [
            ("Before onboarding",
             "<ul><li>Collect legal name, address, date of birth, and government ID.</li><li>Determine beneficial ownership for legal entities (25%+ threshold, per FATF guidance).</li><li>Screen against sanctions lists, PEP lists, and adverse media before risk rating.</li></ul>"),
            ("Risk rating and monitoring",
             "<p>Assign a risk rating (low/medium/high) using the risk-based approach; EDD applies to high-risk relationships. Refresh CDD on trigger events — material transaction changes, PEP status changes, or regulatory flags.</p>"),
            ("Documentation discipline",
             "<p>Record every verification step with timestamps and source references; an auditor must be able to reconstruct the decision. Retention should follow your jurisdiction's requirements (typically 5+ years after relationship end).</p>"),
        ],
    },
    # ── market-analysis ────────────────────────────────────────────────
    {
        "slug": "markets/knowledge/yield-curve-primer",
        "title": "Reading the Yield Curve",
        "pillar": "stock",
        "knowledge_category": "market-analysis",
        "tags": ["yield-curve", "macro-economics", "bonds", "interest-rates"],
        "difficulty": "beginner",
        "description": "What the yield curve says about growth and recessions: normal, flat, inverted, and how term premia shift.",
        "sections": [
            ("The basics",
             "<p>The yield curve plots bond yields against maturity. A normal (upward) curve compensates lenders for time and inflation risk; an inverted curve — short rates above long rates — has historically preceded US recessions.</p>"),
            ("Why inversion matters",
             "<p>Inversion compresses bank lending margins and signals expected rate cuts. Since the 1970s every US recession was preceded by inversion, but leads are long and variable (6–24 months) and false positives exist.</p>"),
            ("Beyond the headline",
             "<p>Watch the 2s10s spread and the 3-month/10-year spread (Fed-preferred), plus break-even inflation curves. Curve steepening after inversion often marks the approach to the downturn's end.</p>"),
        ],
    },
    {
        "slug": "markets/knowledge/volatility-regimes",
        "title": "Volatility Regimes: Identifying and Trading Them",
        "pillar": "stock",
        "knowledge_category": "market-analysis",
        "tags": ["volatility", "regime", "quantitative-methods", "risk-management"],
        "difficulty": "intermediate",
        "description": "How to detect low-vol and high-vol regimes, why correlations change across regimes, and what it means for allocation.",
        "sections": [
            ("Defining regimes",
             "<p>Markets alternate between calm, trending, and crisis regimes. A simple detector: rolling 20-day realised volatility versus its own 1-year median. Crossing the median marks a regime shift.</p>"),
            ("Regime-conditional behaviour",
             "<ul><li>Correlations rise in crises — diversification erodes exactly when needed.</li><li>Volatility clustering means high-vol periods persist.</li><li>Trend-following strategies shine in high-vol, and mean reversion in low-vol ranges.</li></ul>"),
            ("Implications",
             "<p>Size positions by inverse volatility, and re-test strategy performance conditional on regime rather than pooled across time. Regime filters reduce drawdowns but add turnover and whipsaw risk.</p>"),
        ],
    },
    # ── strategies ─────────────────────────────────────────────────────
    {
        "slug": "markets/knowledge/mean-reversion-primer",
        "title": "Mean Reversion Strategies 101",
        "pillar": "stock",
        "knowledge_category": "strategies",
        "tags": ["mean-reversion", "trading-strategies", "quantitative-methods", "statistics"],
        "difficulty": "intermediate",
        "description": "Pairs trading and z-score entry rules: when prices revert, when they trend, and how to avoid falling knives.",
        "sections": [
            ("The core idea",
             "<p>If two cointegrated assets deviate from their long-run relationship, bet on convergence: buy the laggard, short the leader, and exit when the spread normalises.</p>"),
            ("Signal construction",
             "<p>Compute the spread z-score: (spread − mean) / standard deviation over a lookback window. Common entries: z < −2 (long the spread) and z > +2 (short it). Rebalance the z-score window to the half-life of the spread's mean reversion (via a cointegration/OU fit).</p>"),
            ("Risk controls",
             "<ul><li>Trade only cointegrated pairs — correlation without cointegration fails on convergence tests.</li><li>Cap exposure per pair and add a stop on non-convergence.</li><li>Beware regime breaks: the pair may re-mean to a NEW level after structural change.</li></ul>"),
        ],
    },
    {
        "slug": "markets/knowledge/risk-parity-basics",
        "title": "Risk Parity Basics",
        "pillar": "stock",
        "knowledge_category": "strategies",
        "tags": ["risk-parity", "portfolio-construction", "risk-management", "asset-allocation"],
        "difficulty": "intermediate",
        "description": "Equalising risk contributions instead of capital: why bonds get leveraged, and the hidden risks of the approach.",
        "sections": [
            ("The problem with 60/40",
             "<p>Equities dominate the risk of a capital-weighted portfolio — roughly 90% of volatility. Risk parity instead targets equal risk contribution from each asset class.</p>"),
            ("Mechanics",
             "<p>Solve for weights where each asset's marginal risk contribution is equal. Because bonds are far less volatile, the solution leverages them several times, pushing total portfolio risk toward equity-like levels.</p>"),
            ("Watch-outs",
             "<ul><li>Leverage costs and margin calls in rate spikes (2022-style bond losses).</li><li>Correlation assumptions are regime-dependent; covariance estimates lag crises.</li><li>Risk parity is a risk-management philosophy, not a fixed allocation — re-estimate regularly.</li></ul>"),
        ],
    },
    # ── methodology ────────────────────────────────────────────────────
    {
        "slug": "data/knowledge/bloom-self-study-framework",
        "title": "Bloom's Taxonomy as a Self-Study Framework",
        "pillar": "data-engineering",
        "knowledge_category": "methodology",
        "tags": ["bloom", "learning", "methodology", "self-study"],
        "difficulty": "beginner",
        "description": "How to structure self-study from Remember to Create: retrieval practice, worked examples, and teach-back at every level.",
        "sections": [
            ("The six levels as a study ladder",
             "<p><strong>Remember → Understand → Apply → Analyze → Evaluate → Create</strong>. Most learners stop at Understand. Move deliberately up the ladder: flashcards (remember), explanations (understand), exercises (apply), architecture comparisons (analyze), audits (evaluate), and building something (create).</p>"),
            ("Retrieval before exposure",
             "<p>Test yourself on a topic BEFORE reading it. Activating prior knowledge improves retention of what follows (the testing effect). Acacia's pre-test gate and quiz-first pages implement this.</p>"),
            ("Measuring progress",
             "<p>Track the highest Bloom level you can demonstrate without notes: that is your actual level. Revisit weekly — spaced retrieval converts short-term familiarity into durable schema.</p>"),
        ],
    },
    {
        "slug": "compliance/knowledge/red-team-testing-aml",
        "title": "Red-Team Testing an AML Program",
        "pillar": "aml",
        "knowledge_category": "methodology",
        "tags": ["aml", "red-team", "methodology", "risk-assessment", "controls"],
        "difficulty": "advanced",
        "description": "A methodology for attacking your own AML controls: scenario injection, alert-thesis testing, and tuning loops.",
        "sections": [
            ("Why red-team",
             "<p>Controls decay as typologies evolve. Red-teaming simulates adversaries: craft realistic transaction patterns (structuring, layering, mule networks) and verify the monitoring stack detects them.</p>"),
            ("The loop",
             "<ol><li><strong>Scenarios</strong> — define 10-20 typologies from FATF and your own SAR history.</li><li><strong>Injection</strong> — generate synthetic transactions with ground-truth labels.</li><li><strong>Measure</strong> — detection rate, false-positive rate, time-to-alert.</li><li><strong>Tune</strong> — adjust thresholds and rules; re-run to prove improvement.</li></ol>"),
            ("Governance",
             "<p>Document every test run with versioned rule sets so examiners can see the control-improvement trail. Red-team findings feed the risk assessment and board reporting.</p>"),
        ],
    },
    # ── tutorial-code ──────────────────────────────────────────────────
    {
        "slug": "data/knowledge/polars-pipeline-tutorial",
        "title": "Polars Tutorial: A Transaction-Flow Pipeline",
        "pillar": "data-engineering",
        "knowledge_category": "tutorial-code",
        "tags": ["polars", "python", "tutorial", "data-engineering", "lazyframe"],
        "difficulty": "intermediate",
        "description": "Build a lazy Polars pipeline end-to-end: scan parquet, filter, group, join, and collect with query planning.",
        "sections": [
            ("Setup and scan",
             "<pre><code class=\"language-python\">import polars as pl\n\ntxns = pl.scan_parquet(\"transactions.parquet\")\nprint(txns.describe_optimized_plan())</code></pre>",
             "<p>Lazy execution defers work until <code>collect()</code>, letting Polars push down filters and prune columns.</p>"),
            ("Transform with the lazy API",
             "<pre><code class=\"language-python\">daily = (\n    txns\n    .filter(pl.col(\"amount\") > 0)\n    .group_by(\"date\", \"account_id\")\n    .agg(pl.col(\"amount\").sum().alias(\"total\"))\n    .sort(\"total\", descending=True)\n)\nresult = daily.collect()</code></pre>"),
            ("Joins and window functions",
             "<pre><code class=\"language-python\">accts = pl.read_csv(\"accounts.csv\")\njoined = result.join(accts, on=\"account_id\", how=\"left\")\nwith_rank = joined.with_columns(\n    pl.col(\"total\").rank(method=\"dense\").over(\"country\").alias(\"country_rank\")\n)</code></pre>",
             "<p>Polars over-conditions are equivalent to SQL window functions — ideal for rolling aggregates like 30-day velocity.</p>"),
        ],
    },
    {
        "slug": "compliance/knowledge/sql-window-functions-aml",
        "title": "SQL Window Functions for Transaction Monitoring",
        "pillar": "aml",
        "knowledge_category": "tutorial-code",
        "tags": ["sql", "transaction-monitoring", "tutorial", "aml"],
        "difficulty": "intermediate",
        "description": "Velocity checks, rolling sums, and first/last detection with window functions on a transaction table.",
        "sections": [
            ("Velocity: the core AML query",
             "<pre><code class=\"language-sql\">SELECT account_id, COUNT(*) AS tx_count, SUM(amount) AS total\nFROM   transactions\nWHERE  ts >= NOW() - INTERVAL '1 day'\nGROUP  BY account_id\nHAVING tx_count > 10;</code></pre>",
             "<p>Structuring detection needs rolling windows — window functions handle every time range in one scan.</p>"),
            ("Rolling sum via windows",
             "<pre><code class=\"language-sql\">SELECT *,\n  SUM(amount) OVER (\n    PARTITION BY account_id ORDER BY ts\n    ROWS BETWEEN 29 PRECEDING AND CURRENT ROW\n  ) AS rolling_30d\nFROM transactions;</code></pre>"),
            ("First transaction from new device",
             "<pre><code class=\"language-sql\">WITH ranked AS (\n  SELECT *, ROW_NUMBER() OVER (\n    PARTITION BY account_id, device_id ORDER BY ts\n  ) AS rn\n  FROM transactions\n)\nSELECT * FROM ranked WHERE rn = 1;</code></pre>",
             "<p>First-use-of-device patterns feed anomaly detectors and are cheap to compute partition-wise.</p>"),
        ],
    },
]


def generate_body(module: dict) -> str:
    parts = []
    for section in module["sections"]:
        if len(section) == 3:
            heading, code, content = section
            parts.append(f"<h2>{heading}</h2>\n{code}\n{content}")
        else:
            heading, content = section
            parts.append(f"<h2>{heading}</h2>\n{content}")
    return "\n".join(parts)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing")
    parser.add_argument("--apply", action="store_true", help="Write registry.json")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(message)s")

    with open(REGISTRY_PATH, encoding="utf-8") as f:
        registry = json.load(f)

    existing_slugs = {item.get("slug") for item in registry.get("content", [])}
    now = datetime.now(timezone.utc).isoformat()
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    created: list[str] = []
    for module in MODULES:
        slug = module["slug"]
        if slug in existing_slugs:
            continue
        item = {
            "slug": slug,
            "title": module["title"],
            "pillar": module["pillar"],
            "content_type": "knowledge",
            "knowledge_category": module["knowledge_category"],
            "category": module["knowledge_category"],
            "tags": module["tags"],
            "description": module["description"],
            "difficulty": module.get("difficulty", "intermediate"),
            "body_html": generate_body(module),
            "author": "AcaciaFund",
            "created_at": now,
            "updated_at": now,
            "date_str": date_str,
            "auto_generated": True,
            "concept_enriched": True,
        }
        if not args.dry_run:
            registry["content"].append(item)
            existing_slugs.add(slug)
        created.append(slug)
        logger.info(f"  {'[dry] ' if args.dry_run else ''}Created: {slug}")

    if args.dry_run:
        logger.info(f"\n{len(created)} items would be created (re-run with --apply)")
    else:
        with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
            json.dump(registry, f, indent=2, ensure_ascii=False)
            f.write("\n")
        logger.info(f"\n{len(created)} items written to registry.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
