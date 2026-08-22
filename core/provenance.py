"""Evidence-provenance chain for AcaciaFund content items.

Tracks the full lifecycle of each content item from source ingestion through
validation to ontology mapping and publication.

Western empirical philosophy commitment: make the evidentiary basis explicit
and traceable, not assumed or invisible.
"""

"""Evidence-provenance chain for AcaciaFund content items.

Tracks the full lifecycle of each content item from source ingestion through
validation to ontology mapping and publication.

Western empirical philosophy commitment: make the evidentiary basis explicit
and traceable, not assumed or invisible.
"""

from typing import Any, Dict, List, Optional, Tuple

import config
from config import PROJECT_ROOT, PHILOSOPHY_VERSION
from schemas import ContentItem

logger = __import__("logging").getLogger(__name__)


# ---- Source chain tracking ----

# Track which inspiration sources have been verified and when
# Key: source_url, Value: {last_verified, http_status, sqi_score}
_source_verification_cache: Dict[str, Dict[str, Any]] = {}


def get_source_provenance(item: Dict[str, Any]) -> Dict[str, Any]:
    """Get the source provenance chain for a content item.

    Returns a dict with:
    - source_origins: list of (url, type, first_seen) tuples
    - verification_chain: list of (checked_at, status, sqi) tuples
    - ontology_mappings: list of (concept_id, relation_type) tuples
    - validation_history: list of (track, score, timestamp) tuples
    """
    provenance: Dict[str, Any] = {
        "source_origins": [],
        "verification_chain": [],
        "ontology_mappings": [],
        "validation_history": [],
    }

    # 1. Source origins from source_breakdown and source_evidence
    source_breakdown = item.get("source_breakdown", {})
    source_evidence = item.get("source_evidence", [])

    for source_type, count in source_breakdown.items():
        provenance["source_origins"].append({
            "type": source_type,
            "count": count,
            "category": _source_category(source_type),
        })

    for evidence in source_evidence or []:
        if isinstance(evidence, dict):
            url = evidence.get("url", "")
            title = evidence.get("title", "")
            provenance["source_origins"].append({
                "url": url,
                "title": title,
                "verified": evidence.get("verified", False),
                "http_status": evidence.get("http_status"),
            })

    # 2. Verification chain from quality_metrics and signals
    signals = item.get("signals", {})
    quality_metrics = item.get("quality_metrics", {})

    avg_sqi = signals.get("avg_sqi")
    if avg_sqi is not None:
        provenance["verification_chain"].append({
            "checked_at": signals.get("last_checked"),
            "avg_sqi": float(avg_sqi),
            "domain_diversity": signals.get("domain_diversity", 0),
        })

    evidence_level = quality_metrics.get("evidence_level", "")
    provenance["verification_chain"].append({
        "checked_at": quality_metrics.get("last_verified"),
        "evidence_level": evidence_level,
        "sqi_score": quality_metrics.get("score"),
    })

    # 3. Ontology mappings from tags and concept extraction
    from core.ontology import OntologyManager

    try:
        m = OntologyManager.load("data/ontology.json")
        concept_tags = item.get("tags", [])
        for tag in concept_tags:
            concept = m.get_concept(tag)
            if concept:
                provenance["ontology_mappings"].append({
                    "concept_id": concept.id,
                    "label": concept.label,
                    "pillar": concept.pillar,
                    "relations": [
                        {"type": r.relation_type, "target": r.target_id}
                        for r in m.relations_for(tag)
                    ],
                })
    except Exception as e:
        logger.warning(f"Ontology provenance failed: {e}")

    # 4. Validation history from epistemic metadata
    provenance["validation_history"].append({
        "track": "empirical_fidelity",
        "score": item.get("empirical_fidelity"),
        "timestamp": item.get("last_verified"),
    })
    provenance["validation_history"].append({
        "track": "coherence",
        "score": item.get("coherence_score"),
        "timestamp": item.get("last_verified"),
    })
    provenance["validation_history"].append({
        "track": "philosophical_consistency",
        "score": item.get("philosophical_consistency"),
        "timestamp": item.get("last_verified"),
    })
    provenance["validation_history"].append({
        "track": "schema_validity",
        "score": item.get("schema_validity"),
        "timestamp": item.get("last_verified"),
    })
    provenance["validation_history"].append({
        "track": "test_suite_validity",
        "score": item.get("test_suite_validity"),
        "timestamp": item.get("last_verified"),
    })

    return provenance


def _source_category(source_type: str) -> str:
    """Category human-readable name for a source type."""
    categories = {
        "arxiv": "Preprint server",
        "hn": "Hacker News",
        "pubmed": " biomedical literature",
        "sec": "SEC filings",
        "fatf": "FATF guidelines",
        "openalex": "OpenAlex database",
        "crossref": "Crossref metadata",
        "default": "Unknown source",
    }
    return categories.get(source_type, categories["default"])


def format_provenance_for_display(provenance: Dict[str, Any]) -> str:
    """Format provenance chain as a human-readable string for display."""

    lines = ["**Source Provenance Chain**"]

    # Source origins
    if provenance["source_origins"]:
        lines.append("")
        lines.append("**Source Origins:**")
        for src in provenance["source_origins"][:5]:  # Show top 5
            count = src.get("count", 0)
            cat = src.get("category", "unknown")
            lines.append(f"  - {count} items from {cat}")

    # Verification chain
    if provenance["verification_chain"]:
        lines.append("")
        lines.append("**Verification History:**")
        for v in provenance["verification_chain"][:3]:  # Show top 3
            sqi = v.get("avg_sqi") or v.get("sqi_score")
            level = v.get("evidence_level", "?")
            lines.append(f"  - SQI: {sqi}, Evidence: {level}")

    # Ontology mappings
    if provenance["ontology_mappings"]:
        lines.append("")
        lines.append("**Ontology Mappings:**")
        for m in provenance["ontology_mappings"][:3]:  # Show top 3
            concept = m.get("label", "?")
            lines.append(f"  - Mapped to concept: {concept}")

    # Validation history summary
    lines.append("")
    lines.append("**Validation Summary:**")
    for v in provenance["validation_history"]:
        score = v.get("score")
        track = v.get("track")
        lines.append(f"  - {track}: {score}")

    return "\n".join(lines)


def attach_provenance_to_registry(
    registry_path: str = "registry.json",
) -> Dict[str, Any]:
    """Attach provenance chains to all items in the registry.

    Reads the registry, computes provenance for each item, and writes
    back the enriched registry with provenance data.

    Returns dict with stats: total, enriched, errors.
    """
    import json

    with open(registry_path) as f:
        reg = json.load(f)

    content = reg["content"]
    enriched = 0
    errors = 0

    for i, item in enumerate(content):
        if not isinstance(item, dict):
            errors += 1
            continue

        try:
            provenance = get_source_provenance(item)
            item["source_provenance"] = provenance
            # Attach philosophy version for change-tracking
            if "philosophy_version" not in item:
                item["philosophy_version"] = config.PHILOSOPHY_VERSION  # type: ignore
            enriched += 1
        except Exception as e:
            logger.error(f"Failed to enrich item {i} ({item.get('slug', 'unknown')}): {e}")
            errors += 1

    reg["provenance_enriched_at"] = __import__("datetime").datetime.now(
        __import__("datetime").timezone.utc
    ).isoformat()
    reg["provenance_tracked"] = True

    with open(registry_path, "w") as f:
        json.dump(reg, f, indent=2)

    return {"total": len(content), "enriched": enriched, "errors": errors}