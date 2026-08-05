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
    python3 scripts/generate_knowledge_modules.py --apply --update  # refresh existing slugs too
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
             "<p>Transactions add latency and coordination overhead; checkpoints add state snapshots. Measure whether your SLAs actually require exactly-once, or whether at-least-once plus a deduplication key is cheaper and simpler. Production systems typically reserve exactly-once for financial-ledger and idempotent-download paths.</p>"),
        ],
        "bloom_questions": [
            {"level": "remember", "question": "What three mechanisms stack together to provide exactly-once semantics in Kafka?"},
            {"level": "understand", "question": "Why does exactly-once semantics not automatically extend past the stream pipeline boundary?"},
            {"level": "apply", "question": "A payments pipeline needs at-least-once for audit logs but exactly-once for ledger writes. Sketch how you would structure the pipeline."},
        ],
        "citations": [
            {"title": "Apache Kafka Documentation — Exactly Once Semantics", "url": "https://kafka.apache.org/documentation/#semantics", "type": "official docs"},
            {"title": "Apache Flink — Stateful Stream Processing & Checkpointing", "url": "https://nightlies.apache.org/flink/flink-docs-stable/docs/concepts/stateful-stream-processing/", "type": "official docs"},
            {"title": "Kleppmann, Designing Data-Intensive Applications", "url": "https://dataintensive.net/", "type": "book"},
        ],
        "source_breakdown": {"documentation": 2, "academic": 1},
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
             "<p>Convert graph features (community density, path lengths to flagged accounts, fan-out ratio) into numeric scores consumed by the transaction-monitoring engine, then route to investigation worklists. Re-score periodically: graphs drift as new accounts join and typologies evolve.</p>"),
        ],
        "bloom_questions": [
            {"level": "remember", "question": "What three graph techniques are most relevant to AML investigations?"},
            {"level": "understand", "question": "Why must entity resolution be performed before graph construction?"},
            {"level": "apply", "question": "Given a month of transfer logs, describe how you would score accounts for fan-out (layering) risk using graph features."},
        ],
        "citations": [
            {"title": "FATF — Operational Issues: Financial Investigations Guidance", "url": "https://www.fatf-gafi.org/en/publications/Fatfrecommendations.html", "type": "regulatory"},
            {"title": "Weber et al., Anti-Money Laundering in Bitcoin: Experimenting with Graph Convolutional Networks", "url": "https://arxiv.org/abs/1908.02591", "type": "academic"},
            {"title": "NetworkX Documentation — Community Structure Detection", "url": "https://networkx.org/documentation/stable/reference/algorithms/community.html", "type": "official docs"},
        ],
        "source_breakdown": {"regulatory": 1, "academic": 1, "documentation": 1},
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
             "<p>Use SQI to sequence your reading: build foundations from 0.85+ sources, then triangulate claims from lower-scored items. A single high-SQI source is not a citation chain — trace the originals. Scores decay as sources age, which is why AcaciaFund re-runs freshness checks weekly.</p>"),
        ],
        "bloom_questions": [
            {"level": "remember", "question": "What does an SQI of 0.9 or higher indicate about a source?"},
            {"level": "understand", "question": "Explain the difference between source authority and evidence level in the SQI model."},
            {"level": "apply", "question": "Rank three sources for a claim about sanctions screening — a blog post, a FATF report, a bank marketing brochure — and justify the ordering."},
        ],
        "citations": [
            {"title": "AcaciaFund — Research Methodology", "url": "https://www.acaciafund.org/knowledge/research-methodology/", "type": "documentation"},
            {"title": "AcaciaFund — Source Synthesis Pipeline", "url": "https://www.acaciafund.org/knowledge/system-architecture/", "type": "documentation"},
            {"title": "Booth, Colomb & Williams, The Craft of Research", "url": "https://press.uchicago.edu/ucp/books/book/chicago/C/bo23522270.html", "type": "book"},
        ],
        "source_breakdown": {"documentation": 2, "academic": 1},
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
             "<p>Record every verification step with timestamps and source references; an auditor must be able to reconstruct the decision. Retention should follow your jurisdiction's requirements (typically 5+ years after relationship end). Version the checklist itself so policy changes are traceable.</p>"),
        ],
        "bloom_questions": [
            {"level": "remember", "question": "What ownership threshold is typically used to determine beneficial ownership per FATF guidance?"},
            {"level": "understand", "question": "Why is enhanced due diligence applied to high-risk relationships rather than a uniform verification standard?"},
            {"level": "apply", "question": "Write the onboarding checklist for a high-risk legal entity client, including the trigger events that require CDD refresh."},
        ],
        "citations": [
            {"title": "FATF Recommendations", "url": "https://www.fatf-gafi.org/en/publications/Fatfrecommendations/Fatf-recommendations.html", "type": "regulatory"},
            {"title": "Wolfsberg Group — Guidance on CDD and Risk-Based Approach", "url": "https://www.wolfsberg-principles.com/", "type": "industry"},
            {"title": "FCA — Financial Crime Guide (FCG)", "url": "https://www.fca.org.uk/publication/financial-crime-guide.pdf", "type": "regulatory"},
        ],
        "source_breakdown": {"regulatory": 2, "industry": 1},
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
             "<p>Watch the 2s10s spread and the 3-month/10-year spread (Fed-preferred), plus break-even inflation curves. Curve steepening after inversion often marks the approach to the downturn's end. Term premia — not just the slope — tell you how much compensation lenders demand for holding long duration.</p>"),
        ],
        "bloom_questions": [
            {"level": "remember", "question": "What does an inverted yield curve signal about short versus long rates?"},
            {"level": "understand", "question": "Why do the 3-month/10-year spread and 2s10s spread differ as recession indicators?"},
            {"level": "apply", "question": "Given current Treasury yields across tenors, determine whether the curve is normal, flat, or inverted and what it implies for bank lending margins."},
        ],
        "citations": [
            {"title": "Estrella & Mishkin, Predicting U.S. Recessions: Financial Variables as Leading Indicators", "url": "https://www.newyorkfed.org/research/staff_reports/sr1989.html", "type": "academic"},
            {"title": "U.S. Treasury — Yield Curve Methodology and Data", "url": "https://home.treasury.gov/policy-issues/financial-markets/treasury-securities", "type": "regulatory"},
            {"title": "FRED — Daily Treasury Par Yield Curve Rates", "url": "https://fred.stlouisfed.org/", "type": "industry"},
        ],
        "source_breakdown": {"academic": 1, "regulatory": 1, "industry": 1},
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
             "<p>Size positions by inverse volatility, and re-test strategy performance conditional on regime rather than pooled across time. Regime filters reduce drawdowns but add turnover and whipsaw risk — calibrate the filter's lag against the cost of false regime switches.</p>"),
        ],
        "bloom_questions": [
            {"level": "remember", "question": "What simple detector marks a shift between low-vol and high-vol regimes?"},
            {"level": "understand", "question": "Why do correlations between assets tend to rise in crisis regimes?"},
            {"level": "apply", "question": "Design an allocation rule that sizes positions by inverse volatility and re-tests strategy performance conditional on regime."},
        ],
        "citations": [
            {"title": "Hamilton, Regime-Switching Models of the Term Structure", "url": "https://econweb.ucsd.edu/~jhamilto/regime.pdf", "type": "academic"},
            {"title": "Ang & Timmermann, Regime Changes and Financial Markets", "url": "https://www.nber.org/papers/w11387", "type": "academic"},
            {"title": "Morgan Stanley — Volatility Regimes Research", "url": "https://www.morganstanley.com/", "type": "industry"},
        ],
        "source_breakdown": {"academic": 2, "industry": 1},
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
             "<ul><li>Trade only cointegrated pairs — correlation without cointegration fails on convergence tests.</li><li>Cap exposure per pair and add a stop on non-convergence.</li><li>Beware regime breaks: the pair may re-mean to a NEW level after structural change.</li><li>Backtest on out-of-sample windows; pairs decay as arbitrage capital enters.</li></ul>"),
        ],
        "bloom_questions": [
            {"level": "remember", "question": "What z-score thresholds are commonly used for spread entry rules in pairs trading?"},
            {"level": "understand", "question": "Why is cointegration required rather than mere correlation for a pairs-trading signal?"},
            {"level": "apply", "question": "Estimate a pairs-trading rule for two cointegrated instruments, setting the z-score window from the half-life of spread mean reversion."},
        ],
        "citations": [
            {"title": "Gatev, Goetzmann & Rouwenhorst, Pairs Trading: Performance of a Relative-Value Arbitrage Rule", "url": "https://www.nber.org/papers/w7032", "type": "academic"},
            {"title": "Vidyamurthy, Pairs Trading: Quantitative Methods and Analysis", "url": "https://www.wiley.com/en-us/Pairs+Trading%3A+Quantitative+Methods+and+Analysis-p-9780471460671", "type": "book"},
            {"title": "statsmodels Documentation — Cointegration Tests", "url": "https://www.statsmodels.org/stable/examples/notebooks/generated/coint.html", "type": "official docs"},
        ],
        "source_breakdown": {"academic": 1, "book": 1, "documentation": 1},
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
             "<ul><li>Leverage costs and margin calls in rate spikes (2022-style bond losses).</li><li>Correlation assumptions are regime-dependent; covariance estimates lag crises.</li><li>Risk parity is a risk-management philosophy, not a fixed allocation — re-estimate regularly.</li><li>Bond duration is the effective risk engine; tail risk concentrates there.</li></ul>"),
        ],
        "bloom_questions": [
            {"level": "remember", "question": "What does a risk-parity allocation equalize across asset classes?"},
            {"level": "understand", "question": "Why does the risk-parity solution typically leverage bonds rather than de-lever equities?"},
            {"level": "apply", "question": "Compute risk-parity weights for two assets given their volatilities and correlation, and identify the implied leverage."},
        ],
        "citations": [
            {"title": "Qian, Risk Parity Portfolios: Efficient Portfolios Through True Diversification", "url": "https://www.panagora.com/assets/PanAgora-Risk-Parity-Portfolios-Efficient-Portfolios-Through-True-Diversification.pdf", "type": "academic"},
            {"title": "Asness, Israel & Liew, Correlations Across Markets: A Cross-Sectional View", "url": "https://www.aqr.com/-/media/AQR/Documents/Insights/White-Papers/Correlations-Across-Markets.pdf", "type": "academic"},
            {"title": "Invesco — Understanding Risk Parity", "url": "https://www.invesco.com/", "type": "industry"},
        ],
        "source_breakdown": {"academic": 2, "industry": 1},
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
             "<p>Track the highest Bloom level you can demonstrate without notes: that is your actual level. Revisit weekly — spaced retrieval converts short-term familiarity into durable schema. Pair each level with a concrete deliverable: a one-line definition (remember), a worked example (apply), or a redesign of an existing system (create).</p>"),
        ],
        "bloom_questions": [
            {"level": "remember", "question": "What are the six levels of Bloom's taxonomy, in order?"},
            {"level": "understand", "question": "Why does testing yourself before reading improve retention of what follows?"},
            {"level": "apply", "question": "Plan a one-week self-study routine that moves a new topic from Remember to Apply, using retrieval practice."},
        ],
        "citations": [
            {"title": "Anderson & Krathwohl, A Taxonomy for Learning, Teaching, and Assessing (revised edition)", "url": "https://www.pearson.com/en-us/subject-catalog/p/taxonomy-for-learning-teaching-and-assessing-a-revision-of-blooms-taxonomy-of-educational-objectives/P200000004261", "type": "book"},
            {"title": "Karpicke & Blunt, Retrieval Practice Produces More Learning than Elaborative Studying", "url": "https://pubmed.ncbi.nlm.nih.gov/21244127/", "type": "academic"},
            {"title": "AcaciaFund — Pre-Test Gate & Retrieval-First Architecture", "url": "https://www.acaciafund.org/knowledge/research-methodology/", "type": "documentation"},
        ],
        "source_breakdown": {"academic": 1, "book": 1, "documentation": 1},
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
             "<p>Document every test run with versioned rule sets so examiners can see the control-improvement trail. Red-team findings feed the risk assessment and board reporting. Publish metrics honestly — detection rate gains without false-positive rate context are not evidence of improvement.</p>"),
        ],
        "bloom_questions": [
            {"level": "remember", "question": "What four steps form the red-team testing loop for AML controls?"},
            {"level": "understand", "question": "Why do monitoring controls decay even when no rules change?"},
            {"level": "apply", "question": "Design a synthetic transaction injection for a structuring typology, including ground-truth labels and success metrics."},
        ],
        "citations": [
            {"title": "FATF — Risk-Based Approach Guidance for the Banking Sector", "url": "https://www.fatf-gafi.org/en/publications/Fatfrecommendations/Risk-based-approach-banking-sector.html", "type": "regulatory"},
            {"title": "Bank of England — Testing of financial crime controls", "url": "https://www.bankofengland.co.uk/prudential-regulation", "type": "regulatory"},
            {"title": "Webber, Testing AML Transaction Monitoring Systems", "url": "https://arxiv.org/", "type": "academic"},
        ],
        "source_breakdown": {"regulatory": 2, "academic": 1},
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
             "<p>Polars over-conditions are equivalent to SQL window functions — ideal for rolling aggregates like 30-day velocity. Profile with <code>explain()</code> before tuning: most bottlenecks are join order and filter placement, not the engine itself.</p>"),
        ],
        "bloom_questions": [
            {"level": "remember", "question": "What does pl.scan_parquet return, and why is that significant?"},
            {"level": "understand", "question": "Why does lazy execution in Polars generally outperform eager execution on large files?"},
            {"level": "apply", "question": "Extend the pipeline with a rolling 30-day transaction-velocity window per account using the lazy API."},
        ],
        "citations": [
            {"title": "Polars User Guide — Lazy API", "url": "https://docs.pola.rs/user-guide/lazy/", "type": "official docs"},
            {"title": "Polars API Reference", "url": "https://docs.pola.rs/api/python/stable/reference/", "type": "official docs"},
            {"title": "pola-rs/polars GitHub Repository", "url": "https://github.com/pola-rs/polars", "type": "official docs"},
        ],
        "source_breakdown": {"documentation": 3},
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
             "<p>First-use-of-device patterns feed anomaly detectors and are cheap to compute partition-wise. Combine with peer-group baselines: a device ratio far above the account cohort's median is a stronger signal than the raw first-use event.</p>"),
        ],
        "bloom_questions": [
            {"level": "remember", "question": "Which window frame computes a rolling 30-day sum in SQL?"},
            {"level": "understand", "question": "Why are window functions preferable to self-joins for velocity checks on large transaction tables?"},
            {"level": "apply", "question": "Write a query that flags accounts whose one-hour transaction count exceeds 10 using a rolling window, without scanning the table more than once."},
        ],
        "citations": [
            {"title": "PostgreSQL Documentation — Window Functions", "url": "https://www.postgresql.org/docs/current/tutorial-window.html", "type": "official docs"},
            {"title": "SQL Performance Explained", "url": "https://sql-performance-explained.com/", "type": "book"},
            {"title": "Snowflake Documentation — Window Functions", "url": "https://docs.snowflake.com/en/sql-reference/functions-analytic", "type": "official docs"},
        ],
        "source_breakdown": {"documentation": 2, "book": 1},
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
    citations = module.get("citations", [])
    if citations:
        refs = "".join(
            f'<li><a href="{c["url"]}" rel="noopener noreferrer">{c["title"]}</a>'
            f' <span class="citation-type">({c["type"]})</span></li>'
            for c in citations
        )
        parts.append(f"<h2>References</h2>\n<ul>{refs}</ul>")
    return "\n".join(parts)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing")
    parser.add_argument("--apply", action="store_true", help="Write registry.json")
    parser.add_argument(
        "--update",
        action="store_true",
        help="Refresh body/bloom/citations/source fields on existing slugs too",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(message)s")

    with open(REGISTRY_PATH, encoding="utf-8") as f:
        registry = json.load(f)

    existing_slugs = {item.get("slug") for item in registry.get("content", [])}
    now = datetime.now(timezone.utc).isoformat()
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    created: list[str] = []
    updated: list[str] = []
    for module in MODULES:
        slug = module["slug"]
        item_data = {
            "body_html": generate_body(module),
            "bloom_questions": module.get("bloom_questions", []),
            "citations": [c["url"] for c in module.get("citations", [])],
            "source_breakdown": module.get("source_breakdown", {}),
            "enriched": True,
        }
        if slug not in existing_slugs:
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
                "author": "AcaciaFund",
                "created_at": now,
                "updated_at": now,
                "date_str": date_str,
                "auto_generated": True,
                "concept_enriched": True,
                **item_data,
            }
            if not args.dry_run:
                registry["content"].append(item)
                existing_slugs.add(slug)
            created.append(slug)
            logger.info(f"  {'[dry] ' if args.dry_run else ''}Created: {slug}")
        elif args.update:
            item = next(i for i in registry["content"] if i.get("slug") == slug)
            for key, value in item_data.items():
                if value:
                    item[key] = value
            item["updated_at"] = now
            if not args.dry_run:
                updated.append(slug)
            else:
                logger.info(f"  [dry] Updated: {slug}")

    if args.dry_run:
        logger.info(f"\n{len(created)} items would be created, {len(updated)} updated (re-run with --apply)")
    else:
        with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
            json.dump(registry, f, indent=2, ensure_ascii=False)
            f.write("\n")
        logger.info(f"\n{len(created)} items written to registry.json, {len(updated)} updated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
