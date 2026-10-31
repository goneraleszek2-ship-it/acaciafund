# SQI Meaning Specification

> **Canonical implementation.** The authoritative definitions are implemented in
> `scripts/archive/backfill_sqi.py` and exercised by `tests/test_sqi_meaning.py`.
> The archived module produced the `sqi` values stored in `registry.json`.
> `core/build_quality.py::_compute_sqi_for_item` is a **build-time fallback** for
> items missing a stored `sqi`; it mirrors `backfill_sqi.py`, including the
> `+0.2` `flashcards` term in `educational_quality`.
> `core/score.py::compute_signal_score` is a third, unrelated formula used only
> for news-ingestion *signals*, not item SQI.

## Operational Definitions per Dimension

### source_credibility (weight: 0.25)
- **Count-based (checked first)** on `signals.count` (falling back to `sum(source_breakdown.values())`):
  - **3+ distinct sources** → 1.0
  - **exactly 2 distinct sources** → 0.85
  - **exactly 1 distinct source** → 0.70
- **Type-based (only when count is 0/absent)**:
  - **arXiv** in `source_breakdown` → 0.95
  - **PubMed** in `source_breakdown` → 0.95
  - **HN** (Hacker News) → 0.65
  - **Unknown / absent** → 0.5

### technical_accuracy (weight: 0.25)
- **Depth markers** (case-insensitive substrings in `title`+`body_html`):
  `architecture`, `implementation`, `pattern`, `design`, `algorithm`, `framework`,
  `methodology`, `analysis`, `model`, `system` → +0.15 once if any is present
- **Code markers**:
  `code`, `example`, `implementation`, `api`, `function`, `class`, `import`, `def `, `return` → +0.10 (once if any present)
- **Reference markers**:
  `documentation`, `specification`, `rfc`, `standard`, `reference`, `citation`, `paper`, `study` → +0.15 (once if any present)
- **Length bonus**: `body_html` character count > 2000 → +0.10 (applied unconditionally).
- **Scoring floor**: base 0.5; ceiling 1.0.
- **Testable mark**: given a content item, exactly compute `technical_accuracy` by the above rules; the result must be reproducible across runs.

### practical_value (weight: 0.20)
- **Practical markers** (case-insensitive, in `title`+`body_html`):
  `how to`, `tutorial`, `guide`, `step-by-step`, `best practices`, `case study`, `real-world`, `production`, `deployment` → +0.20 (applied once if any present)
- **Tool markers** (case-insensitive):
  `tool`, `library`, `framework`, `platform`, `software`, `database` → +0.15 (applied once if any present; **additive** with practical markers — the implementation does not exclude them)
- **Learn marker**: `content_type == "learn"` → +0.10
- **Scoring floor**: 0.5 base; ceiling 1.0.
- **Testable mark**: given a content item, exactly compute `practical_value` by the above rules; the result must be reproducible.

### freshness (weight: 0.15)
- **Decay curve**: `max(0.2, 1.0 - (days_old / 360)` where `days_old = (now - pub_date).days` in UTC.
- **Foundational exception**: items with `knowledge_category == "foundations"` OR tagged with `foundational` use a **shallower decay**: floor at 365 days = 0.6 (not 0.2). At day 180, foundational items score ≥ 0.6; at day 365, score = 0.6 exactly.
- **Non-foundational items**: standard decay curve applies; at day 180 ≈ 0.5, at day 365 = 0.2.
- **No created_at**: return 0.5 (baseline unknown).
- **Testable mark**: given a content item with known `created_at` and `knowledge_category`, exactly compute `freshness` by the above rules; verify foundational exception at day 180 and day 365.

### trend_relevance (weight: 0.10)
- **Input**: `signals.trend_strength` (numeric, may be int or float).
- **Formula**: `min(1.0, trend_strength / 100)`.
- **Baseline**: when `trend_strength` is 0 or absent → score 0.5 (implicit floor in composite SQI calculation, not in this sub-score alone).
- **Cap**: `trend_strength = 150` → score 1.0; `trend_strength = 200` → score 1.0 (capped).
- **Testable mark**: given a content item with `signals.trend_strength`, exactly compute `trend_relevance` by the above rules.

### educational_quality (weight: 0.05 — included in the final weighted sum)
- **Bloom questions**: `article.get("bloom_questions")` present → +0.35
- **Flashcards**: `article.get("flashcards")` present → +0.20
- **Learn content type**: `article.get("content_type") == "learn"` → +0.15
- **Scoring**: sum of applicable markers; floor 0.3 (base) + markers; ceiling 1.0.
- **Testable mark**: given a content item, exactly compute `educational_quality` by the above rules.

---

## Invariants (Properties SQI Must Always Satisfy)

| # | Invariant | Formal Statement | Why It Matters |
|---|-----------|-----------------|----------------|
| I1 | **Monotonicity Sanity** | If `source_count` changes from 1 → 3+ (all other dimensions held constant), `final_sqi` must **not decrease**. | Guards against source-credibility reduction being masked by other factors. |
| I2 | **Freshness Floor for Foundational** | The `freshness` sub-score for items with `knowledge_category == "foundations"` OR a `foundations` tag floors at 0.6 (a *sub-score* floor, not a floor on `final_sqi`). | Prevents catastrophic decay of foundational knowledge that should remain reliable. |
| I3 | **No Marker Gaming** | Remove all `practical_markers` from content currently scoring >0.80 → `final_sqi` reduction >= 0.10 (if technical_accuracy and source_credibility unchanged). | Ensures `practical_value` marker has real impact, not just decorative presence. |
| I4 | **Technical Depth Lower Bound** | `final_sqi >= (source_credibility * 0.25 + technical_accuracy * 0.25 + practical_value * 0.20 + freshness * 0.15 + trend_relevance * 0.10 + educational_quality * 0.05)` (weighted sum of individual dimension minima). | Guarantees a minimum SQI even with worst-case individual dimensions. |
| I5 | **No Negative Dimensions** | Each sub-score `source_credibility`, `technical_accuracy`, `practical_value`, `freshness`, `trend_relevance`, `educational_quality` ∈ [0, 1]. | Prevents implementation bugs that produce out-of-range values. |
| I6 | **Composite Monotonicity (Partial)** | If exactly one dimension's sub-score increases (all others fixed), `final_sqi` must increase. | Simple sanity check that the weighted sum construction works as expected. |

**Test Implementation**: `tests/test_sqi_meaning.py` — one test per invariant I1–I6 plus a determinism check (7 tests). The suite imports the canonical `scripts/archive/backfill_sqi.py` sub-score functions. (The earlier claim of >= 18 tests was aspirational and is not met.)