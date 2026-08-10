"""Rule-based structured extraction for research syntheses.

Produces two artifacts from an article body, with no LLM dependency:

- ``key_variables``: metric → value pairs (accuracy, AUC, R², p-values,
  sample sizes, latency, throughput, ...) with the supporting sentence as
  evidence. Used for the "Extracted Variables" table on research pages.
- ``prisma``: a PRISMA-style study-flow trail (screened / excluded /
  included counts) where the synthesis reports a screening process.

Both are computed at build time from ``body_html`` and attached to Content
items via ``attach_extraction()`` — deterministic, cheap, and offline-safe.
"""

import re
from typing import Any, Dict, List, Optional

# Canonical metric name → display label + aliases (longest first for matching).
METRIC_PATTERNS: Dict[str, Dict[str, Any]] = {
    "accuracy": {"label": "Accuracy", "aliases": ["accuracy"]},
    "precision": {"label": "Precision", "aliases": ["precision"]},
    "recall": {"label": "Recall", "aliases": ["recall", "sensitivity"]},
    "f1": {"label": "F1-score", "aliases": ["f1-score", "f1 score", "f1"]},
    "auc": {"label": "AUC", "aliases": ["area under the curve", "auc"]},
    "r2": {"label": "R²", "aliases": ["r-squared", "r squared", "coefficient of determination", "r²", "r2"]},
    "correlation": {"label": "Correlation", "aliases": ["correlation coefficient", "correlation"]},
    "p_value": {"label": "p-value", "aliases": ["p-value", "p value"]},
    "sample_size": {"label": "Sample size", "aliases": ["sample size", "sample of", "participants", "patients", "records"]},
    "false_positive_rate": {"label": "False positive rate", "aliases": ["false positive rate", "fpr"]},
    "error_rate": {"label": "Error rate", "aliases": ["error rate", "misclassification rate"]},
    "latency": {"label": "Latency", "aliases": ["latency"]},
    "throughput": {"label": "Throughput", "aliases": ["transactions per second", "tps", "throughput"]},
    "confidence": {"label": "Confidence", "aliases": ["confidence interval"]},
}

MAX_VARIABLES = 12
EVIDENCE_CHARS = 160

_PERCENT_RE = re.compile(r"([0-9][0-9,]*(?:\.[0-9]+)?)\s*(?:%|percent)")
_DECIMAL_RE = re.compile(r"([0-9]+\.[0-9]+)")
_NUMBER_RE = re.compile(r"[0-9][0-9,]*(?:\.[0-9]+)?")
_UNIT_RE = re.compile(
    r"(?:ms|s|sec|seconds?|minutes?|hours?|days?|years?|tps|ops|rps|records?|transactions?|"
    r"events?|rows?|bytes?|kb|mb|gb|tb|db|bps|gps|%|x|×|k|m|b|thousand|million|billion)",
    flags=re.IGNORECASE,
)
_PVALUE_RE = re.compile(r"\bp\s*([<≤=]+)\s*([0-9][0-9]*(?:\.[0-9]+)?)", flags=re.IGNORECASE)
_SAMPLE_RE = re.compile(r"(?:^|[\s(N=;])(?:n|N)\s*=\s*([0-9][0-9,]*(?:\.[0-9]+)?)")
_RANGE_RE = re.compile(r"([0-9]+\.[0-9]+)\s*(?:-|–|to)\s*([0-9]+\.[0-9]+)")

PRISMA_STAGES = {
    "identified": ["identified", "retrieved from"],
    "screened": ["screened", "screening", "reviewed"],
    "excluded": ["excluded", "removed", "duplicates removed"],
    "eligible": ["eligible", "full-text assessed"],
    "included": ["included", "selected"],
}
_PRISMA_NUM_RE = re.compile(r"([0-9][0-9,]*)")

_STRIP_TAGS_RE = re.compile(r"<[a-zA-Z!/][^>]*>")
_WS_RE = re.compile(r"\s+")


def _plain_text(html: str) -> str:
    """Strip tags and collapse whitespace from body_html."""
    return _WS_RE.sub(" ", _STRIP_TAGS_RE.sub(" ", html or "")).strip()


def _clean_number(raw: str) -> float:
    return float(raw.replace(",", ""))


def _plausible_value(metric: str, value: float, raw: str) -> bool:
    """Reject implausible captures (false-positive guard)."""
    if metric == "p_value":
        return 0.0 < value <= 1.0
    if metric in {"accuracy", "precision", "recall", "f1", "auc", "r2", "correlation", "false_positive_rate", "error_rate"}:
        # decimal in [0, 1] or a percentage-style number
        if "%" in raw or "percent" in raw:
            return value <= 100.0
        return 0.0 < value <= 1.0
    return value >= 0.0


def _sentence_around(text: str, start: int, end: int) -> str:
    """Return the sentence containing [start, end), trimmed to EVIDENCE_CHARS."""
    left = text.rfind(". ", 0, start)
    left = text.rfind(".\n", 0, start) if left < 0 else left
    if left < 0:
        left = 0
    else:
        left += 2
    right = text.find(". ", end)
    if right < 0:
        right = len(text)
    else:
        right += 1
    evidence = text[left:right].strip()
    if len(evidence) > EVIDENCE_CHARS:
        evidence = evidence[: EVIDENCE_CHARS].rsplit(" ", 1)[0] + "…"
    return evidence


def extract_key_variables(body_html: str) -> List[Dict[str, Any]]:
    """Extract metric → value pairs from an article body.

    A variable is recorded only when a known metric keyword and a plausible
    value appear within a short window of each other. Returns up to
    MAX_VARIABLES variables, most-specific metrics first.
    """
    text = _plain_text(body_html)
    if not text:
        return []

    variables: List[Dict[str, Any]] = []
    seen: set[tuple[str, Optional[str]]] = set()

    for metric, spec in METRIC_PATTERNS.items():
        if metric == "p_value":
            pm = _PVALUE_RE.search(text)
            if pm:
                value = _clean_number(pm.group(2))
                value_raw = f"p {pm.group(1)} {value:g}"
                variables.append(
                    {
                        "metric": metric,
                        "name": spec["label"],
                        "value": value_raw,
                        "evidence": _sentence_around(text, pm.start(), pm.end()),
                    }
                )
            continue
        aliases = sorted(spec["aliases"], key=len, reverse=True)
        for alias in aliases:
            for match in re.finditer(re.escape(alias), text, flags=re.IGNORECASE):
                start = match.start()
                window = text[start : start + 60]
                value_raw: Optional[str] = None
                value: float | None = None

                if metric == "p_value":
                    m = _PVALUE_RE.search(window)
                    if m:
                        value = _clean_number(m.group(2))
                        value_raw = f"p {m.group(1)} {value:g}"
                elif metric == "sample_size":
                    m = _SAMPLE_RE.search(text[max(0, start - 30) : start + 60])
                    if m:
                        value = _clean_number(m.group(1))
                        value_raw = f"n = {value:,.0f}"
                    else:
                        m = re.search(r"sample of\s+([0-9][0-9,]*)", window, flags=re.IGNORECASE)
                        if m:
                            value = _clean_number(m.group(1))
                            value_raw = f"n = {value:,.0f}"
                else:
                    rate_metric = metric in ("latency", "throughput")
                    pct = None if rate_metric else _PERCENT_RE.search(window)
                    decimal = _DECIMAL_RE.search(window)
                    if pct:
                        value = _clean_number(pct.group(1))
                        value_raw = f"{value:g}%"
                    elif decimal:
                        value = _clean_number(decimal.group(1))
                        value_raw = f"{value:g}"
                    else:
                        # bare numbers only count when followed by a unit
                        m = _NUMBER_RE.search(window)
                        if m:
                            after = window[m.end() : m.end() + 12]
                            unit = _UNIT_RE.match(after.strip())
                            if unit:
                                value = _clean_number(m.group(0))
                                value_raw = f"{value:g} {unit.group(0).strip()}"

                if value is None or not _plausible_value(metric, value, value_raw or ""):
                    continue

                key = (metric, value_raw)
                if key in seen:
                    continue
                seen.add(key)

                variables.append(
                    {
                        "metric": metric,
                        "name": spec["label"],
                        "value": value_raw,
                        "evidence": _sentence_around(text, start, match.end() + len(value_raw or "")),
                    }
                )
                break  # one variable per metric alias, first occurrence wins
            if len(variables) >= MAX_VARIABLES:
                return variables

    # Prefer strong captures (p-values, percentages, ranges) and keep order stable.
    variables.sort(key=lambda v: v["metric"])
    return variables[:MAX_VARIABLES]


def extract_prisma_trail(body_html: str) -> Dict[str, int]:
    """Extract a PRISMA-style screening flow from the body.

    Counts the first number found near each stage keyword. A stage is only
    reported when its keyword is actually present. Returns {} when the body
    does not describe a screening process.
    """
    text = _plain_text(body_html)
    trail: Dict[str, int] = {}
    if not text:
        return trail

    for stage, keywords in PRISMA_STAGES.items():
        for keyword in keywords:
            match = re.search(re.escape(keyword), text, flags=re.IGNORECASE)
            if not match:
                continue
            # number may follow ("excluded 312") or precede ("47 studies included")
            num_match = _PRISMA_NUM_RE.search(text[match.end() : match.end() + 40])
            if not num_match:
                num_match = _PRISMA_NUM_RE.search(text[max(0, match.start() - 40) : match.start()])
            if not num_match:
                continue
            trail[stage] = int(num_match.group(1).replace(",", ""))
            break
    return trail


def extract_from_item(item: Any) -> Dict[str, Any]:
    """Return {key_variables, prisma} for a content item (empty-safe)."""
    body = getattr(item, "body_html", None) or ""
    result: Dict[str, Any] = {"key_variables": extract_key_variables(body), "prisma": extract_prisma_trail(body)}
    if not result["key_variables"] and not result["prisma"]:
        return {}
    return result


def attach_extraction(
    items: List[Any],
    slug_extraction: Optional[Dict[str, Dict[str, Any]]] = None,
) -> int:
    """Attach precomputed extraction data to content items by slug.

    Items without a matching entry get their extraction computed from the
    body. Returns the number of items that end up with extraction data.
    """
    slug_extraction = slug_extraction or {}
    attached = 0
    for item in items:
        slug = getattr(item, "slug", "") or ""
        data = slug_extraction.get(slug)
        if data is None:
            data = extract_from_item(item)
        if data:
            item.extraction_data = data
            attached += 1
        else:
            item.extraction_data = None
    return attached
