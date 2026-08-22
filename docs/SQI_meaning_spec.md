# SQI Meaning Specification

## Operational Definitions per Dimension

### source_credibility (weight: 0.25)
- **arXiv** presence in `source_breakdown` → score 0.95
- **PubMed** presence in `source_breakdown` → score 0.95
- **HN** (Hacker News) presence → score 0.65
- **Single distinct source** (count == 1) → score 0.70
- **3+ distinct sources** (count >= 3) → score 1.0
- **Unknown / absent** (no `source_breakdown` or empty) → default score 0.5
- **Tie-breaking**: when multiple source types present, take the maximum score applicable; do not sum.

### technical_accuracy (weight: 0.25)
- **Depth markers** (case-insensitive substrings in `title`+`body_html`):
  - `architecture`, `algorithm`, `pattern`, `design` → +0.15 each (maximum one bonus per marker type to avoid double-counting)
- **Code markers**:
  - `code`, `example`, `implementation`, `api`, `function`, `class`, `import`, `def `, `return` → +0.10 each (maximum one bonus per marker type)
- **Reference markers**:
  - `documentation`, `specification`, `rfc`, `standard`, `citation`, `paper`, `study` → +0.15 each (maximum one bonus per marker type)
- **Length bonus**: `body_html` character count > 2000 → +0.10 **only if** at least one depth marker is present; otherwise length alone contributes 0.
- **Scoring floor**: minimum 0.5 when no markers present; maximum 1.0 when all applicable markers present.
- **Testable mark**: given a content item, exactly compute `technical_accuracy` by the above rules; the result must be reproducible across runs.

### practical_value (weight: 0.20)
- **Practical markers** (case-insensitive, in `title`+`body_html`):
  - `how to`, `tutorial`, `guide`, `step-by-step`, `best practices`, `case study`, `real-world`, `production`, `deployment` → +0.20 total (applied once if any present)
- **Tool markers** (case-insensitive):
  - `tool`, `library`, `framework`, `platform`, `software`, `database` → +0.15 total (applied once if any present)
  - **Exclusion**: tool markers are not added if practical markers are also present (avoid double-counting the same conceptual content).
- **Learn marker**: `content_type == "learn"` → +0.10
- **Scoring floor**: 0.5 when no markers present; maximum 1.0 when all applicable markers present.
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

### educational_quality (computed, unweighted; currently excluded from final weighted sum)
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
| I2 | **Freshness Floor for Foundational** | Items with `knowledge_category == "foundations"` OR tagged `foundational` must have `sqi >= 0.6` at age 365 days. | Prevents catastrophic decay of foundational knowledge that should remain reliable. |
| I3 | **No Marker Gaming** | Remove all `practical_markers` from content currently scoring >0.80 → `final_sqi` reduction >= 0.10 (if technical_accuracy and source_credibility unchanged). | Ensures `practical_value` marker has real impact, not just decorative presence. |
| I4 | **Technical Depth Lower Bound** | `final_sqi >= (source_credibility * 0.5 + technical_accuracy * 0.25 + practical_value * 0.20 + freshness * 0.15 + trend_relevance * 0.10)` (i.e., weighted sum of individual dimension minima). | Guarantees a minimum SQI even with worst-case individual dimensions. |
| I5 | **No Negative Dimensions** | Each sub-score `source_credibility`, `technical_accuracy`, `practical_value`, `freshness`, `trend_relevance` ∈ [0, 1]. | Prevents implementation bugs that produce out-of-range values. |
| I6 | **Composite Monotonicity (Partial)** | If exactly one dimension's sub-score increases (all others fixed), `final_sqi` must increase. | Simple sanity check that the weighted sum construction works as expected. |

**Test Implementation**: `tests/test_sqi_meaning.py` — each invariant I1–I6 gets at least 3 test cases (positive, boundary, negative), total >= 18 test functions.