"""Diagnostic placement quiz helpers (Task 2.4).

Pure functions over a curated per-pillar question bank: the page at
``/diagnostic/`` asks one beginner, one intermediate and one expert question
per pillar, scores locally, and writes the resulting level into the existing
``acacia_learning_mode`` localStorage key used by the site's mode toggle.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

LEVELS = ("beginner", "intermediate", "expert")

PILLARS = (
    ("aml", "Compliance"),
    ("stock", "Markets"),
    ("data-engineering", "Data Engineering"),
)

DIAGNOSTIC_QUESTIONS: list[dict[str, Any]] = [
    # ── Compliance (aml) ─────────────────────────────────────────────
    {
        "pillar": "aml",
        "tier": "beginner",
        "question": "What does CDD stand for in KYC workflows?",
        "options": [
            "Customer Due Diligence",
            "Common Data Directory",
            "Cash Deposit Division",
            "Compliance Data Deduplication",
        ],
        "correct": 0,
        "rationale": "CDD — Customer Due Diligence — is the foundation of KYC: verifying identity and assessing risk before onboarding.",
        "module": "aml/learn/aml-basics",
    },
    {
        "pillar": "aml",
        "tier": "intermediate",
        "question": "A transaction-monitoring alert matches a customer's name to an OFAC SDN entry, but it is a different person with the same name. What is this called?",
        "options": [
            "A false positive",
            "A false negative",
            "A true match",
            "A data breach",
        ],
        "correct": 0,
        "rationale": "Name-alike matches that are actually innocent are false positives — screening tuning reduces these without missing true matches.",
        "module": "aml/learn/sanctions-screening",
    },
    {
        "pillar": "aml",
        "tier": "expert",
        "question": "A bank processes a payment that unintentionally benefits a sanctioned entity — the bank had no knowledge of the link. US sanctions law can still penalize the bank. This illustrates:",
        "options": [
            "Strict liability",
            "Due process",
            "Proportionality",
            "Voluntary self-disclosure",
        ],
        "correct": 0,
        "rationale": "Sanctions enforcement follows strict liability: violations are penalized regardless of intent, so screening controls must be rigorous.",
        "module": "aml/learn/sanctions-screening",
    },
    # ── Markets (stock) ──────────────────────────────────────────────
    {
        "pillar": "stock",
        "tier": "beginner",
        "question": "What is the bid-ask spread?",
        "options": [
            "The difference between the highest price a buyer will pay and the lowest price a seller will accept",
            "The fee a broker charges per trade",
            "The difference between a stock's open and close price",
            "The volatility of a stock over a month",
        ],
        "correct": 0,
        "rationale": "The spread is the gap between bid and ask — it is the market maker's compensation for providing liquidity.",
        "module": "markets/learn/market-fundamentals",
    },
    {
        "pillar": "stock",
        "tier": "intermediate",
        "question": "Which index measures 30-day implied volatility of S&P 500 options?",
        "options": ["VIX", "S&P 500", "Russell 2000", "Nasdaq Composite"],
        "correct": 0,
        "rationale": "The VIX (CBOE Volatility Index) is the market's 'fear gauge' — it quotes expected 30-day S&P 500 volatility.",
        "module": "markets/learn/volatility-analysis",
    },
    {
        "pillar": "stock",
        "tier": "expert",
        "question": "A market maker widens quotes on a stock with heavy informed order flow. Which risk are they pricing in?",
        "options": [
            "Adverse selection",
            "Regulatory risk",
            "Interest rate risk",
            "Counterparty default",
        ],
        "correct": 0,
        "rationale": "Market makers lose to informed traders who trade on superior information — adverse selection risk is priced into wider spreads.",
        "module": "markets/learn/market-microstructure",
    },
    # ── Data Engineering (data-engineering) ──────────────────────────
    {
        "pillar": "data-engineering",
        "tier": "beginner",
        "question": "What is a data warehouse?",
        "options": [
            "A central repository optimized for cleaned, structured data used in analytics and reporting",
            "A cache that stores copies of web pages",
            "A raw store of unprocessed source files",
            "A queue for streaming events",
        ],
        "correct": 0,
        "rationale": "Warehouses hold cleaned, structured data optimized for analytical querying — the backbone of most BI stacks.",
        "module": "data/learn/data-engineering-basics",
    },
    {
        "pillar": "data-engineering",
        "tier": "intermediate",
        "question": "A query engine skips reading partitions that do not match the query's filter conditions. This optimization is called:",
        "options": [
            "Partition pruning",
            "Shuffle join",
            "Broadcast join",
            "Columnar compression",
        ],
        "correct": 0,
        "rationale": "Partition pruning lets engines read only the partitions a query actually needs, cutting I/O dramatically.",
        "module": "data/learn/spike-data-pipelines",
    },
    {
        "pillar": "data-engineering",
        "tier": "expert",
        "question": "A table has tens of thousands of tiny files across partitions, slowing down query planning. What is the underlying problem?",
        "options": [
            "The small file problem",
            "The large file problem",
            "Schema drift",
            "Join skew",
        ],
        "correct": 0,
        "rationale": "Too many small partition files create excessive metadata overhead — compaction and co-location (e.g., Z-ORDER) mitigate it.",
        "module": "data/learn/spike-data-pipelines",
    },
]


def compute_placement(correct: int, total: int | None = None) -> str:
    """Map a raw correct count to a learning mode level."""
    total = len(DIAGNOSTIC_QUESTIONS) if total is None else total
    ratio = (correct / total) if total else 0.0
    if ratio >= 0.75:
        return "expert"
    if ratio >= 0.4:
        return "intermediate"
    return "beginner"


def build_payload(questions: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Serialize the question bank for the static JSON the client fetches."""
    questions = list(questions or DIAGNOSTIC_QUESTIONS)
    return {
        "generatedAt": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "total": len(questions),
        "pillars": [{"key": key, "label": label} for key, label in PILLARS],
        "levels": list(LEVELS),
        "questions": questions,
    }
