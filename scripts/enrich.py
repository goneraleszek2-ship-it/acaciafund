#!/usr/bin/env python3
"""Research Enrichment Engine for AcaciaFund.

A self-organizing semantic enrichment step that sits between data ingestion
and the static site build. Processes registry.json entries to:

  1. Extract cross-domain semantic tags from title + description
  2. Calculate a baseline multi-factor Signal Quality Index (SQI)

Architecture:
  [ Raw Feeds ] -> [ dbt/Ingestion ] -> [ registry.json (Raw) ]
                                              |
                                    [ enrich.py ]
                                      ├── Entity & Concept Extraction
                                      └── Multi-Factor SQI Scoring
                                              |
  [ Live Site ] <- [ build.py ] <--- [ registry.json (Enriched) ]

Usage:
    python3 scripts/enrich.py                         # Full run
    python3 scripts/enrich.py --dry-run               # Preview only
    python3 scripts/enrich.py --verbose               # Detailed output
    python3 scripts/enrich.py --force                 # Re-enrich all items
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

REGISTRY_PATH = ROOT / "registry.json"

# ---------------------------------------------------------------------------
# Multi-Factor SQI Weights
# ---------------------------------------------------------------------------
W_SOURCE_AUTHORITY = 0.40
W_TEMPORAL_DECAY = 0.30
W_INFO_DENSITY = 0.30

# Source authority scores (peer-reviewed > curated > forum)
SOURCE_SCORES: dict[str, float] = {
    "arxiv": 0.90,
    "pubmed": 0.85,
    "hn": 0.50,
}

# Temporal decay: half-life in days for the recency factor
TEMPORAL_HALF_LIFE = 90.0

# Clamp bounds
SQI_MIN = 0.01
SQI_MAX = 0.99

# ---------------------------------------------------------------------------
# Cross-Domain Keyword Dictionary (deterministic fallback)
# Maps concept patterns to canonical tags, bridging technical and
# philosophical domains as described in the Knowledge Fabric.
# ---------------------------------------------------------------------------
CONCEPT_PATTERNS: list[tuple[re.Pattern, str]] = [
    # --- Core Data / ML / AI ---
    (re.compile(r"(?i)\bpipeline"), "dataops"),
    (re.compile(r"(?i)\b(etl|elt|stream|kafka|flink)\b"), "dataops"),
    (re.compile(r"(?i)\b(dbt|sqlmesh|dataform)\b"), "dataops"),
    (re.compile(r"(?i)\b(data\s*quality|observability|lineage)\b"), "dataops"),
    (re.compile(r"(?i)\b(catalog|iceberg|delta|hudi)\b"), "dataops"),
    (re.compile(r"(?i)\b(ml|machine.learning|deep.learning|neural)\b"), "machine-learning"),
    (re.compile(r"(?i)\b(llm|transformer|attention|gpt|bert)\b"), "llm"),
    (re.compile(r"(?i)\b(vector|embedding|rag|semantic.search)\b"), "vector-search"),
    (re.compile(r"(?i)\b(agent|autonomous|self.healing)\b"), "agentic-systems"),
    # --- Cybernetic / Philosophical ---
    (re.compile(r"(?i)\b(cybernetics|feedback.loop|wiener)\b"), "cybernetics"),
    (re.compile(r"(?i)\b(entropy|information.theory|shannon)\b"), "information-theory"),
    (re.compile(r"(?i)\b(signal|noise|sq|sqi)\b"), "signal-quality"),
    (re.compile(r"(?i)\b(epistemology|ontology|semantic|knowledge.graph)\b"), "knowledge-fabric"),
    # --- AML / Financial Crime ---
    (re.compile(r"(?i)\b(aml|anti.money.launder|kyc|sanctions)\b"), "aml"),
    (re.compile(r"(?i)\b(transaction|fraud|anomaly|suspicious)\b"), "transaction-monitoring"),
    (re.compile(r"(?i)\b(regtech|regulatory|compliance)\b"), "regtech"),
    # --- Markets / Finance ---
    (re.compile(r"(?i)\b(stock|market|equity|trading)\b"), "markets"),
    (re.compile(r"(?i)\b(risk|volatility|portfolio|hedge)\b"), "risk-management"),
    (re.compile(r"(?i)\b(blockchain|crypto|defi|nft)\b"), "crypto-finance"),
    # --- Infrastructure / Cloud ---
    (re.compile(r"(?i)\b(k8s|kubernetes|docker|container|terraform|iac)\b"), "infrastructure"),
    (re.compile(r"(?i)\b(serverless|lambda|cloud|aws|gcp|azure)\b"), "cloud-infrastructure"),
    # --- Cybersecurity / Privacy ---
    (re.compile(r"(?i)\b(security|vulnerability|zero.day|penetration|threat|cyber)\b"), "cybersecurity"),
    (re.compile(r"(?i)\b(gdpr|privacy|consent|differential.privacy|ethics)\b"), "privacy-ethics"),
    # --- Biotech / Genomics ---
    (re.compile(r"(?i)\b(genomics|crispr|bioinformatics|clinical.trial|gene)\b"), "biotech-genomics"),
    # --- Semiconductors / Hardware ---
    (re.compile(r"(?i)\b(semiconductor|chip|foundry|tsmc|wafer|fabrication)\b"), "semiconductors"),
]

# Terms whose presence signals high information density
HIGH_INFO_TERMS: list[re.Pattern] = [
    re.compile(r"(?i)\b(framework|paradigm|architecture)\b"),
    re.compile(r"(?i)\b(algorithm|formula|theorem|proof)\b"),
    re.compile(r"(?i)\b(protocol|standard|contract|schema)\b"),
    re.compile(r"(?i)\b(convergence|divergence|emergence)\b"),
    re.compile(r"(?i)\b(predictive|generative|adaptive)\b"),
    re.compile(r"(?i)\b(scale|distributed|fault.tolerant)\b"),
    re.compile(r"(?i)\b(optimization|efficiency|throughput)\b"),
    re.compile(r"(?i)\b(governance|policy|ethics|privacy)\b"),
]


class ResearchEnricher:
    """Self-organizing enrichment engine for research content.

    Two modes:
      - infer=True  : Uses mem0ai + LLM for semantic extraction
      - infer=False : Deterministic keyword-based fallback for local dev
    """

    def __init__(self, infer_mode: bool = False):
        self.infer_mode = infer_mode
        self._memory = None

        if self.infer_mode:
            self._init_memory()

    def _init_memory(self) -> None:
        """Initialize mem0 memory backend (only when infer=True)."""
        try:
            from mem0 import Memory
            config = {
                "llm": {
                    "provider": "openai",
                    "config": {
                        "model": "gpt-4o",
                        "temperature": 0.3,
                    },
                },
                "embedder": {
                    "provider": "fastembed",
                },
            }
            self._memory = Memory.from_config(config)
        except ImportError:
            print("  [warn] mem0ai not installed, falling back to deterministic mode")
            self.infer_mode = False

    # ------------------------------------------------------------------
    # Tag Extraction
    # ------------------------------------------------------------------

    def extract_semantic_tags(
        self,
        title: str,
        description: str,
        body: str = "",
        existing_tags: list[str] | None = None,
    ) -> list[str]:
        """Extract 3-5 cross-domain semantic tags from content.

        In LLM mode, queries mem0 for knowledge fabric context and
        instructs the model to extract high-density tags bridging
        technical and philosophical domains.

        In deterministic mode, matches against the CONCEPT_PATTERNS
        dictionary.
        """
        if self.infer_mode and self._memory:
            return self._extract_with_llm(title, description, body)

        return self._extract_deterministic(title, description, existing_tags)

    def _extract_with_llm(
        self,
        title: str,
        description: str,
        body: str | None = None,
        max_body_chars: int = 2000,
    ) -> list[str]:
        """LLM-powered tag extraction via mem0 with retry and validation.

        Args:
            title: Article title.
            description: Short summary.
            body: Full body HTML (truncated to max_body_chars).
            max_body_chars: Max body characters to include in prompt.

        Returns:
            List of 3-6 kebab-case tags, or empty list on failure.
        """
        # Build a compact input for the model
        text = f"Title: {title}\nSummary: {description}"
        if body:
            text += f"\nBody: {body[:max_body_chars]}"

        # Query mem0 for relevant context from the knowledge fabric
        context = ""
        if self._memory:
            try:
                results = self._memory.search(text, limit=3)
                if results and isinstance(results, list):
                    snippets = []
                    for r in results:
                        if isinstance(r, dict):
                            meta = r.get("metadata", {})
                            t = meta.get("title", "")
                            d = meta.get("description", "")
                            part = t
                            if d:
                                part += f": {d[:120]}"
                            snippets.append(part)
                    if snippets:
                        context = "Related context:\n" + "\n".join(
                            f"- {s}" for s in snippets
                        )
            except Exception:
                pass

        system_prompt = (
            "You are a research tag extractor. Given an article title, "
            "summary, and optional body text, identify 3-5 cross-domain "
            "tags that bridge technical domains and reflect core concepts. "
            "Tags must be short, specific, kebab-case (e.g. "
            "'data-engineering', 'machine-learning', 'financial-crime'). "
            "Respond with ONLY a JSON array of strings."
        )

        user_prompt = f"""{context}

Title: {title}
Description: {description[:1000]}

Respond with a JSON array of 3-5 kebab-case tags:"""

        def _parse_json_array(raw: str) -> list[str] | None:
            """Extract a JSON array from LLM response, handling markdown fences
            and trailing commas."""
            import json
            # Strip markdown code fences
            clean = re.sub(r"```(?:json)?\s*", "", raw).strip()
            # Find the first [ ... ] block
            start = clean.find("[")
            end = clean.rfind("]")
            if start == -1 or end == -1 or end <= start:
                return None
            candidate = clean[start : end + 1]
            # Remove trailing commas before closing bracket
            candidate = re.sub(r",\s*]", "]", candidate)
            try:
                parsed = json.loads(candidate)
                if isinstance(parsed, list):
                    return parsed
            except json.JSONDecodeError:
                pass
            return None

        def _validate_tags(tags: list[str]) -> list[str]:
            """Filter to valid kebab-case tags, minimum length 3."""
            valid = []
            for t in tags:
                t = t.strip()
                if len(t) > 2 and re.match(r"^[a-z][a-z0-9-]*[a-z0-9]$", t):
                    valid.append(t)
            return valid[:6]

        prompts_to_try = [
            # Primary: full prompt with context
            [{"role": "system", "content": system_prompt},
             {"role": "user", "content": user_prompt}],
            # Fallback: no system message, simplified prompt
            [{"role": "user", "content": (
                f"Extract 3-5 kebab-case tags from this article.\n\n"
                f"Title: {title}\nDescription: {description[:500]}\n\n"
                f"Return ONLY a JSON array like [\"tag1\", \"tag2\", \"tag3\"]."
            )}],
        ]

        for messages in prompts_to_try:
            if not self._memory:
                break
            try:
                response = self._memory.chat(messages)
                raw = (
                    response.get("response", "")
                    if isinstance(response, dict)
                    else str(response)
                )
                parsed = _parse_json_array(raw)
                if parsed:
                    tags = _validate_tags(parsed)
                    if len(tags) >= 3:
                        return tags
            except Exception:
                continue

        return []

    def _extract_deterministic(
        self,
        title: str,
        description: str,
        existing_tags: list[str] | None = None,
    ) -> list[str]:
        """Deterministic keyword-based tag extraction.

        Augments existing ingestion tags with cross-domain concepts
        detected via pattern matching on title + description.
        """
        combined = f"{title} {description}"
        found: set[str] = set()

        for pattern, tag in CONCEPT_PATTERNS:
            if pattern.search(combined):
                found.add(tag)

        # Merge with existing tags, preserving originals
        base = set(existing_tags or [])

        # Prefer existing tags; supplement with new cross-domain concepts
        merged = list(base) + [t for t in sorted(found) if t not in base]

        return merged[:10]

    # ------------------------------------------------------------------
    # Multi-Factor SQI Scoring
    # ------------------------------------------------------------------

    def calculate_sqi(self, item: dict[str, Any]) -> float:
        """Calculate a baseline Signal Quality Index using multi-factor formula.

        SQI = W1 * Source_Authority + W2 * Temporal_Recency + W3 * Info_Density

        All sub-scores normalized to [0, 1].
        """
        source_score = self._score_source_authority(item)
        recency_score = self._score_temporal_recency(item)
        density_score = self._score_info_density(item)

        sqi = (
            W_SOURCE_AUTHORITY * source_score
            + W_TEMPORAL_DECAY * recency_score
            + W_INFO_DENSITY * density_score
        )

        return max(SQI_MIN, min(SQI_MAX, sqi))

    def _score_source_authority(self, item: dict[str, Any]) -> float:
        """Evaluate source credibility (40% weight).

        arXiv papers and PubMed articles score highest; HackerNews
        discussion threads score lower. Mixed-source items get a
        weighted average.
        """
        sb: dict[str, int] = item.get("source_breakdown") or {}
        total = sum(sb.values())
        if total == 0:
            # Default for items without source breakdown
            content_type = item.get("content_type", "")
            if content_type == "research":
                return 0.60
            elif content_type == "learn":
                return 0.70
            return 0.50

        weighted = 0.0
        for source_key, count in sb.items():
            score = SOURCE_SCORES.get(source_key, 0.40)
            weighted += score * count

        return weighted / total

    def _score_temporal_recency(self, item: dict[str, Any]) -> float:
        """Evaluate content freshness (30% weight).

        Uses exponential decay with a 90-day half-life. Content
        created today scores 1.0; content older than ~1 year
        approaches 0.05.
        """
        date_str = item.get("date_str") or item.get("created_at")
        if not date_str:
            return 0.50

        try:
            if isinstance(date_str, str):
                clean = date_str.replace("Z", "+00:00")
                dt = datetime.fromisoformat(clean)
            else:
                return 0.50

            now = datetime.now(timezone.utc)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)

            days_old = max((now - dt).total_seconds() / 86400, 0.0)
            # Exponential decay: score = 2^(-days / half_life)
            return math.exp2(-days_old / TEMPORAL_HALF_LIFE)
        except (ValueError, TypeError):
            return 0.50

    def _score_info_density(self, item: dict[str, Any]) -> float:
        """Evaluate information density (30% weight).

        Combines:
          - Tag richness: more tags = higher density
          - Description depth: longer factual description
          - Technical term density: presence of high-information keywords
        """
        score = 0.0

        # Tag richness (max 0.3)
        tags = item.get("tags", [])
        tag_ratio = min(len(tags) / 6.0, 1.0)
        score += 0.30 * tag_ratio

        # Description depth (max 0.3)
        desc = item.get("description", "")
        if desc:
            word_count = len(desc.split())
            if word_count >= 80:
                desc_score = 1.0
            elif word_count >= 40:
                desc_score = 0.60
            elif word_count >= 15:
                desc_score = 0.30
            else:
                desc_score = 0.10
            score += 0.30 * desc_score

        # Technical term density (max 0.4)
        combined = f"{item.get('title', '')} {desc}"
        high_info_count = sum(
            1 for p in HIGH_INFO_TERMS if p.search(combined)
        )
        term_ratio = min(high_info_count / 4.0, 1.0)
        score += 0.40 * term_ratio

        return score

    # ------------------------------------------------------------------
    # Bulk Processing
    # ------------------------------------------------------------------

    def enrich_item(self, item: dict[str, Any]) -> dict[str, Any]:
        """Run full enrichment pipeline on a single item."""
        title = item.get("title", "")
        description = item.get("description", "")
        body = item.get("body_html", "")
        existing = item.get("tags", [])

        # 1. Extract semantic tags
        enriched_tags = self.extract_semantic_tags(
            title=title,
            description=description,
            body=body,
            existing_tags=existing,
        )

        # 2. Calculate baseline SQI
        baseline_sqi = self.calculate_sqi(item)

        # 3. Store enrichment outputs
        # Set baseline SQI only if not already present — the Bayesian
        # update engine refines from here. Preserving an existing SQI
        # on re-enrich (--force) avoids wiping out Bayesian posteriors.
        if "sqi" not in item:
            item["sqi"] = baseline_sqi
        item["tags"] = enriched_tags
        item["enriched"] = True
        item["enriched_at"] = (
            datetime.now(timezone.utc)
            .replace(microsecond=0)
            .isoformat()
            .replace("+00:00", "Z")
        )

        return item


# =========================================================================
# CLI Entry Point
# =========================================================================


def load_registry() -> dict:
    """Load registry.json."""
    if not REGISTRY_PATH.exists():
        print(f"Error: {REGISTRY_PATH} not found.")
        sys.exit(1)
    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_registry(reg: dict) -> None:
    """Save registry.json."""
    with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
        json.dump(reg, f, indent=2, ensure_ascii=False)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="AcaciaFund Research Enrichment Engine"
    )
    parser.add_argument(
        "--registry",
        default=str(REGISTRY_PATH),
        help="Path to registry.json",
    )
    parser.add_argument(
        "--infer",
        action="store_true",
        help="Use LLM inference (requires API key; default: deterministic)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-enrich all items, ignoring enriched flag",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show changes without writing to registry",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed per-item output",
    )
    args = parser.parse_args()

    # Load registry
    reg = load_registry()
    items: list[dict] = reg.get("content", [])
    print(f"Loaded {len(items)} items from registry")

    # Initialize enricher
    enricher = ResearchEnricher(infer_mode=args.infer)
    mode = "LLM" if args.infer else "deterministic"
    print(f"Enricher mode: {mode}")

    # Process items
    enriched_count = 0
    skipped_count = 0

    for item in items:
        slug = item.get("slug", "unknown")

        # Skip already-enriched items unless --force
        if item.get("enriched") and not args.force:
            skipped_count += 1
            if args.verbose:
                print(f"  [skip] {slug} (already enriched)")
            continue

        # Enrich
        enricher.enrich_item(item)
        enriched_count += 1

        if args.verbose:
            tags = item.get("tags", [])
            sqi = item.get("sqi", 0.0)
            print(f"  [enrich] {slug}")
            print(f"           tags={tags[:5]}{'...' if len(tags) > 5 else ''}")
            print(f"           sqi={sqi:.3f}")

    # Update registry metadata
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    reg["last_enriched"] = now
    reg["enricher_mode"] = mode

    # Write changes
    if not args.dry_run:
        save_registry(reg)
        print(f"  Written to {REGISTRY_PATH}")
    else:
        print("  DRY RUN - no changes written")

    # Summary
    print()
    print("=" * 60)
    print("ENRICHMENT ENGINE REPORT")
    print("=" * 60)
    print(f"Total items:            {len(items)}")
    print(f"Enriched this run:      {enriched_count}")
    print(f"Skipped (already done): {skipped_count}")
    print(f"Enricher mode:          {mode}")
    print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
