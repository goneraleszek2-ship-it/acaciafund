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
import logging
import math
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger("acaciafund.enrich")
logging.basicConfig(level=logging.INFO, format="%(message)s")

ROOT = Path(__file__).resolve().parent.parent

# ── Environment bootstrap: propagate .env to os.environ ──
def _bootstrap_environment():
    """Force-load project .env into os.environ so child processes
    inherit variables like NVIDIA_API_KEY without shell export."""
    env_path = ROOT / ".env"
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if line.startswith("export "):
                    line = line[7:]
                if "=" in line:
                    key, value = line.split("=", 1)
                    value = value.strip("'\"")
                    os.environ[key.strip()] = value

_bootstrap_environment()

# Force offline mode for fastembed/HuggingFace Hub — prevents network
# hangs when querying snapshot metadata in restricted environments.
# Must be set before mem0/fastembed is initialized (happens lazily).
os.environ.setdefault("HF_HUB_OFFLINE", "1")
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

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
    "regulatory": 0.85,
    "finra": 0.85,
    "fatf": 0.85,
    "bloomberg": 0.80,
    "reuters": 0.80,
    "github": 0.75,
    "medium": 0.55,
    "youtube": 0.55,
    "hn": 0.50,
    "twitter": 0.30,
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
    (re.compile(r"(?i)\b(beneficial.ownership|shell.company|offshore|pep|cdd|edd)\b"), "aml"),
    (re.compile(r"(?i)\b(financial.intelligence|fiu|str|adverse.media)\b"), "financial-intelligence"),
    (re.compile(r"(?i)\b(crypto.aml|virtual.asset|vas.p|travel.rule|blockchain.forensic)\b"), "crypto-aml"),
    (re.compile(r"(?i)\b(trade.based|trade.finance|export.control|dual.use)\b"), "trade-finance-crime"),
    (re.compile(r"(?i)\b(entity.resolution|network.analysis|watchlist|screening)\b"), "transaction-monitoring"),
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
    # --- AML expansion ---
    (re.compile(r"(?i)\b(sar|ctr|suspicious.activity|regulatory.filing)\b"), "aml-reporting"),
    (re.compile(r"(?i)\b(shell.company|front.company|money.mule|layering)\b"), "aml-typologies"),
    (re.compile(r"(?i)\b(corruption|bribery|kleptocracy|illicit.financial)\b"), "financial-crime"),
    (re.compile(r"(?i)\b(trade.based|invoice.fraud|misinvoicing|trade.laundering)\b"), "trade-finance-crime"),
    # --- Markets expansion ---
    (re.compile(r"(?i)\b(supply.chain|logistics|procurement|vendor)\b"), "supply-chain"),
    (re.compile(r"(?i)\b(commodity|futures|derivatives|options)\b"), "derivatives"),
    (re.compile(r"(?i)\b(interest.rate|inflation|monetary.policy|central.bank)\b"), "macro-economics"),
    (re.compile(r"(?i)\b(earnings|revenue|profit.margin|valuation)\b"), "corporate-finance"),
    (re.compile(r"(?i)\b(manufacturing|production|assembly|factory)\b"), "manufacturing"),
    # --- Data Engineering expansion ---
    (re.compile(r"(?i)\b(data.mesh|data.fabric|data.product|data.marketplace)\b"), "data-architecture"),
    (re.compile(r"(?i)\b(event.driven|event.sourcing|cqrs|domain.event)\b"), "event-driven"),
    (re.compile(r"(?i)\b(real.time|streaming|cdc|debezium|change.data.capture)\b"), "streaming"),
    (re.compile(r"(?i)\b(data.lakehouse|data.warehouse|oltp|olap)\b"), "data-storage"),
    (re.compile(r"(?i)\b(data.catalog|data.discovery|data.lineage)\b"), "data-governance"),
    (re.compile(r"(?i)\b(orchestration|workflow|airflow|dag)\b"), "orchestration"),
    (re.compile(r"(?i)\b(schema.evolution|schema.registry|avro|protobuf|parquet)\b"), "schema-management"),
    # --- Cross-domain ---
    (re.compile(r"(?i)\b(monitoring|observability|telemetry|tracing|metrics)\b"), "observability"),
    (re.compile(r"(?i)\b(automation|robotics|rpa|bots)\b"), "automation"),
    (re.compile(r"(?i)\b(simulation|digital.twin|modeling|forecasting)\b"), "simulation"),
    (re.compile(r"(?i)\b(testing|quality.assurance|ci.cd|devops)\b"), "software-quality"),
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
    re.compile(r"(?i)\b(surveillance|detection|prevention|mitigation)\b"),
    re.compile(r"(?i)\b(compliance|regulatory|audit|oversight)\b"),
    re.compile(r"(?i)\b(latency|throughput|bandwidth|scalability)\b"),
    re.compile(r"(?i)\b(standardization|interoperability|portability)\b"),
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
        """Initialize mem0 memory backend + OpenAI client for NVIDIA NIM.

        Uses the NVIDIA_API_KEY env var (OpenAI-compatible endpoint) for
        LLM chat, and fastembed for local vector embeddings.
        """
        self._api_key = os.environ.get("NVIDIA_API_KEY") or os.environ.get("OPENAI_API_KEY") or ""
        self._api_base = "https://integrate.api.nvidia.com/v1"
        self._llm_model = "meta/llama-3.1-70b-instruct"

        if not self._api_key:
            logger.warning("  [warn] No NVIDIA_API_KEY set, falling back to deterministic mode")
            self.infer_mode = False
            return

        try:
            from mem0 import Memory  # pyright: ignore[reportAttributeAccessIssue]
            config = {
                "llm": {
                    "provider": "openai",
                    "config": {
                        "model": self._llm_model,
                        "temperature": 0.3,
                        "openai_base_url": self._api_base,
                        "api_key": self._api_key,
                    },
                },
                "embedder": {
                    "provider": "fastembed",
                    "config": {
                        "model": "sentence-transformers/all-MiniLM-L6-v2",
                    },
                },
            }
            self._memory = Memory.from_config(config)

            # Also create a raw OpenAI client (mem0.chat() is not implemented)
            from openai import OpenAI
            self._llm_client = OpenAI(
                api_key=self._api_key,
                base_url=self._api_base,
            )
        except ImportError as e:
            logger.warning(f"  [warn] Failed to initialize LLM: {e}, falling back to deterministic")
            self.infer_mode = False

    # ------------------------------------------------------------------
    # LLM retry helper
    # ------------------------------------------------------------------

    def _llm_call(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        temperature: float = 0.4,
        max_tokens: int = 500,
        max_retries: int = 3,
        base_delay: float = 2.0,
    ) -> str | None:
        """Call LLM with exponential backoff retry. Returns raw response text or None."""
        if not self._llm_client:
            return None
        import time as _time
        last_err = None
        for attempt in range(max_retries):
            try:
                resp = self._llm_client.chat.completions.create(
                    model=self._llm_model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=temperature,
                    max_tokens=max_tokens,
                    timeout=30,
                )
                return (resp.choices[0].message.content or "").strip()
            except Exception as e:
                last_err = e
                if attempt < max_retries - 1:
                    _time.sleep(base_delay * (2 ** attempt))
        logger.warning("LLM call failed after %d retries: %s", max_retries, last_err)
        return None

    @staticmethod
    def _parse_llm_json(raw: str) -> Any:
        """Strip markdown fences and parse JSON from LLM response."""
        if not raw:
            return None
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            lines = [line for line in lines if not line.strip().startswith("```")]
            cleaned = "\n".join(lines)
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            return None

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
            llm_tags = self._extract_with_llm(title, description, body)
            # Fall back to deterministic extraction if LLM returns nothing
            if llm_tags:
                return llm_tags
            return self._extract_deterministic(title, description, existing_tags)

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
            except Exception as e:
                logger.warning("mem0 search failed for %s: %s", title, e)

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
            """Extract a JSON array from LLM response, handling markdown
            fences, trailing commas, single quotes, and preamble text."""
            if not raw or not isinstance(raw, str):
                return None
            cleaned = raw.strip()
            # Strip markdown code fences
            cleaned = re.sub(r"```(?:json)?\s*", "", cleaned).strip()
            # Find the first [ ... ] block
            start = cleaned.find("[")
            end = cleaned.rfind("]")
            if start == -1 or end == -1 or end <= start:
                # Try to match a list-like pattern as last resort
                m = re.search(r'\[([^\]]*)\]', cleaned)
                if m:
                    start = m.start()
                    end = m.end()
                else:
                    return None
            candidate = cleaned[start : end + 1]
            # Remove trailing commas before closing bracket
            candidate = re.sub(r",\s*]", "]", candidate)
            # Replace single quotes with double quotes for valid JSON
            candidate = candidate.replace("'", '"')
            # Fix unquoted strings (bare words without quotes)
            candidate = re.sub(r'(?<=[\[,])\s*([a-zA-Z][a-zA-Z0-9_-]*)\s*(?=[,\]])', r'"\1"', candidate)
            try:
                parsed = json.loads(candidate)
                if isinstance(parsed, list):
                    return parsed
            except json.JSONDecodeError:
                pass
            # Fallback: extract all quoted strings
            strings = re.findall(r'"([^"]+)"', candidate)
            if strings:
                return strings
            return None

        def _validate_tags(tags: list[str]) -> list[str]:
            """Filter to valid kebab-case tags, minimum length 3."""
            valid = []
            for t in tags:
                if isinstance(t, list):
                    # LLM sometimes returns nested [[...]] arrays — flatten
                    valid.extend(_validate_tags(t))
                    continue
                if not isinstance(t, str):
                    continue
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
            if not self._llm_client:
                break
            try:
                response = self._llm_client.chat.completions.create(
                    model=self._llm_model,
                    messages=messages,  # pyright: ignore[reportArgumentType]
                    temperature=0.3,
                    max_tokens=200,
                    timeout=30,
                )
                raw = response.choices[0].message.content or ""
                parsed = _parse_json_array(raw)
                if parsed:
                    tags = _validate_tags(parsed)
                    if len(tags) >= 3:
                        return tags
            except Exception as e:
                logger.warning("LLM API call failed for %s: %s", title, e)
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

        sqi = max(SQI_MIN, min(SQI_MAX, sqi))
        if "glossary" in item.get("slug", ""):
            sqi = max(sqi, 0.68)
        return round(sqi, 3)

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
    # Bloom's Taxonomy Questions
    # ------------------------------------------------------------------

    def _generate_bloom_questions(self, item: dict[str, Any]) -> list[dict[str, str]]:
        """Generate 5 Bloom's taxonomy reading questions via LLM.

        Returns list of {"level": str, "question": str} or empty list
        if LLM is unavailable or fails.
        """
        if not self.infer_mode or not self._llm_client:
            return []

        title = item.get("title", "")
        desc = item.get("description", "")
        text = f"Title: {title}\nSummary: {desc}"

        system_prompt = (
            "You are a tutor creating Bloom's taxonomy questions. "
            "Given an article, generate exactly 5 questions at different cognitive levels: "
            "remember, understand, apply, analyze, evaluate, create. "
            "Respond with ONLY a JSON array of objects, each with 'level' and 'question' keys. "
            'Example: [{"level": "remember", "question": "What is..."}, ...]'
        )

        user_prompt = f"Article:\n{text}\n\nGenerate 5 Bloom's taxonomy questions as a JSON array:"

        try:
            response = self._llm_client.chat.completions.create(
                model=self._llm_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.4,
                max_tokens=500,
                timeout=30,
            )
            raw = response.choices[0].message.content or ""
            import json as _json
            cleaned = raw.strip()
            cleaned = re.sub(r"```(?:json)?\s*", "", cleaned).strip()
            start = cleaned.find("[")
            end = cleaned.rfind("]")
            if start == -1 or end == -1:
                return []
            parsed = _json.loads(cleaned[start:end+1])
            if isinstance(parsed, list):
                valid = [q for q in parsed if isinstance(q, dict) and "level" in q and "question" in q]
                return valid[:6]
        except Exception:
            logger = logging.getLogger("acaciafund.enrich")
            logger.warning("Bloom questions LLM call failed for %s", title)

        return []

    # ------------------------------------------------------------------
    # Flashcard Generation
    # ------------------------------------------------------------------

    def _generate_flashcards(self, item: dict[str, Any]) -> list[dict[str, str]]:
        """Generate 3-5 Q&A flashcards via LLM.

        Returns list of {"question": str, "answer": str} or empty list
        if LLM is unavailable or fails.
        """
        if not self.infer_mode or not self._llm_client:
            return []

        title = item.get("title", "")
        desc = item.get("description", "")
        body = item.get("body_html", "")
        text = f"Title: {title}\nSummary: {desc}\nBody: {body[:1500]}"

        system_prompt = (
            "You are a study aid generating flashcards. "
            "Given an article, create 3-5 Q&A flashcards that capture key concepts. "
            "Respond with ONLY a JSON array of objects, each with 'question' and 'answer' keys. "
            'Example: [{"question": "What is...", "answer": "It is..."}, ...]'
        )

        user_prompt = f"Article:\n{text}\n\nGenerate 3-5 flashcards as a JSON array:"

        try:
            response = self._llm_client.chat.completions.create(
                model=self._llm_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.4,
                max_tokens=600,
                timeout=30,
            )
            raw = response.choices[0].message.content or ""
            import json as _json
            cleaned = raw.strip()
            cleaned = re.sub(r"```(?:json)?\s*", "", cleaned).strip()
            start = cleaned.find("[")
            end = cleaned.rfind("]")
            if start == -1 or end == -1:
                return []
            parsed = _json.loads(cleaned[start:end+1])
            if isinstance(parsed, list):
                valid = [c for c in parsed if isinstance(c, dict) and "question" in c and "answer" in c]
                return valid[:6]
        except Exception:
            logger = logging.getLogger("acaciafund.enrich")
            logger.warning("Flashcard LLM call failed for %s", title)

        return []

    # ------------------------------------------------------------------
    # Reading Time
    # ------------------------------------------------------------------

    @staticmethod
    def _compute_reading_time(item: dict[str, Any]) -> int:
        """Estimate reading time in minutes based on body_html word count."""
        body = item.get("body_html", "")
        word_count = len(body.split())
        return max(1, word_count // 200)

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

        # 4. Bloom's taxonomy questions (LLM only)
        if not item.get("bloom_questions"):
            item["bloom_questions"] = self._generate_bloom_questions(item)

        # 5. Flashcards (LLM only)
        if not item.get("flashcards"):
            item["flashcards"] = self._generate_flashcards(item)

        # 6. Reading time (always computed)
        item["reading_time"] = self._compute_reading_time(item)

        item["enriched"] = True
        item["enriched_at"] = (
            datetime.now(timezone.utc)
            .replace(microsecond=0)
            .isoformat()
            .replace("+00:00", "Z")
        )

        return item

    # ----------------------------------------------------------------
    # LLM Feynman enrichment (--llm-feynman)
    # ----------------------------------------------------------------

    def generate_feynman_explanation(
        self, item: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Generate a Feynman-style explanation stub via LLM."""
        title = item.get("title", "")
        description = item.get("description", "")
        body = item.get("body_html", "")[:800]
        if not title:
            return None

        system_prompt = "You output only valid JSON."
        user_prompt = f"""You are generating a Feynman explanation for a research article.

Title: {title}
Description: {description}
Body excerpt: {body}

Return ONLY valid JSON with these fields:
{{
  "plain_english": "A 2-3 sentence explanation in plain language a college student could understand.",
  "key_intuition": "The single most important insight, stated simply.",
  "why_it_matters": "Why this matters for someone studying data, compliance, or markets.",
  "difficulty": "beginner|intermediate|advanced",
  "one_liner": "A single sentence capturing the essence."
}}
No markdown, no code fences, just JSON."""

        raw = self._llm_call(system_prompt, user_prompt, temperature=0.4, max_tokens=500)
        if raw is None:
            return None
        return self._parse_llm_json(raw)

    # ----------------------------------------------------------------
    # LLM Philosophy enrichment (--llm-philosophy)
    # ----------------------------------------------------------------

    def classify_philosophy(
        self, item: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Classify epistemic status and philosophical basis via LLM."""
        title = item.get("title", "")
        description = item.get("description", "")
        tags = item.get("tags", [])
        if not title:
            return None

        system_prompt = "You output only valid JSON."
        user_prompt = f"""Classify the philosophical and epistemic properties of this research article.

Title: {title}
Description: {description}
Tags: {', '.join(tags[:10])}

Return ONLY valid JSON:
{{
  "epistemic_status": "empirical|theoretical|normative|interpretive|speculative|review|meta-analytic",
  "epistemic_role": "Constitutive|Instrumental|Regulatory|Critical|Explanatory|Predictive|Prescriptive",
  "normative_basis": "None|Kantian|Utilitarian|Rawlsian|Virtue|Pragmatist|Deontological|Consequentialist|Feminist|Postcolonial",
  "uncertainty_class": "risk|ambiguity|deep-uncertainty|unknown-unknowns",
  "philosophical_sources": ["key thinkers referenced, e.g. Arrow, Kahneman"],
  "temporal_ontology": "static|process|teleological|cyclical"
}}
No markdown, no code fences, just JSON."""

        raw = self._llm_call(system_prompt, user_prompt, temperature=0.3, max_tokens=400)
        if raw is None:
            return None
        return self._parse_llm_json(raw)


# =========================================================================
# CLI Entry Point
# =========================================================================


from _registry_utils import load_registry, save_registry  # noqa: E402


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
        "--llm-feynman",
        action="store_true",
        help="Generate Feynman explanation stubs via LLM (requires --infer)",
    )
    parser.add_argument(
        "--llm-philosophy",
        action="store_true",
        help="Classify epistemic status and philosophical basis via LLM (requires --infer)",
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
    logger.info(f"Loaded {len(items)} items from registry")

    # Initialize enricher
    enricher = ResearchEnricher(infer_mode=args.infer)
    mode = "LLM" if args.infer else "deterministic"
    logger.info(f"Enricher mode: {mode}")

    # Process items
    enriched_count = 0
    skipped_count = 0

    for item in items:
        slug = item.get("slug", "unknown")

        # Skip already-enriched items unless --force
        if item.get("enriched") and not args.force:
            skipped_count += 1
            if args.verbose:
                logger.debug(f"  [skip] {slug} (already enriched)")
            continue

        # Enrich
        enricher.enrich_item(item)
        enriched_count += 1

        # LLM Feynman enrichment
        if args.llm_feynman and enricher._llm_client:
            feynman = enricher.generate_feynman_explanation(item)
            if feynman:
                item["feynman"] = {
                    "plain_english": feynman.get("plain_english", ""),
                    "key_intuition": feynman.get("key_intuition", ""),
                    "why_it_matters": feynman.get("why_it_matters", ""),
                    "difficulty": feynman.get("difficulty", "intermediate"),
                    "one_liner": feynman.get("one_liner", ""),
                    "source": "llm",
                }
                if args.verbose:
                    logger.debug(f"  [feynman] {slug}: {feynman.get('one_liner', '')[:60]}")

        # LLM Philosophy enrichment
        if args.llm_philosophy and enricher._llm_client:
            phil = enricher.classify_philosophy(item)
            if phil:
                item["philosophy"] = {
                    "epistemic_status": phil.get("epistemic_status", "empirical"),
                    "epistemic_role": phil.get("epistemic_role", ""),
                    "normative_basis": phil.get("normative_basis", "None"),
                    "uncertainty_class": phil.get("uncertainty_class", "risk"),
                    "philosophical_sources": phil.get("philosophical_sources", []),
                    "temporal_ontology": phil.get("temporal_ontology", "static"),
                    "source": "llm",
                }
                if args.verbose:
                    logger.debug(f"  [philosophy] {slug}: {phil.get('epistemic_status', '?')}")

        if args.verbose:
            tags = item.get("tags", [])
            sqi = item.get("sqi", 0.0)
            logger.debug(f"  [enrich] {slug}")
            logger.debug(f"           tags={tags[:5]}{'...' if len(tags) > 5 else ''}")
            logger.debug(f"           sqi={sqi:.3f}")

    # Update registry metadata
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    reg["last_enriched"] = now
    reg["enricher_mode"] = mode

    # Write changes
    if not args.dry_run:
        save_registry(reg)
        logger.info(f"  Written to {REGISTRY_PATH}")
    else:
        logger.info("  DRY RUN - no changes written")

    # Summary
    logger.info("")
    logger.info("=" * 60)
    logger.info("ENRICHMENT ENGINE REPORT")
    logger.info("=" * 60)
    logger.info(f"Total items:            {len(items)}")
    logger.info(f"Enriched this run:      {enriched_count}")
    logger.info(f"Skipped (already done): {skipped_count}")
    logger.info(f"Enricher mode:          {mode}")
    logger.info("")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
