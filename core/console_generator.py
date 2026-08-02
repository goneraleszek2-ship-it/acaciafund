"""Scholar Console — aggregates build-time data into a unified knowledge cockpit."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from config import PILLAR_CONFIG, PROJECT_ROOT
from core.urls import canonical_path, slug_to_fspath, slug_to_path


def _safe_json(path: Path) -> dict[str, Any]:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def generate_console_payload(
    all_content: list[Any],
    ontology: Any | None,
    concept_cache: dict[str, set[str]] | None,
    build_hash: str,
    site_url: str,
) -> dict[str, Any]:
    pillars = []
    for pkey in ["aml", "stock", "data-engineering"]:
        pc = PILLAR_CONFIG.get(pkey, {})
        pillars.append({
            "key": pkey,
            "url": pc.get("url", ""),
            "label": pc.get("label", pkey),
            "emoji": pc.get("emoji", ""),
            "color": pc.get("color", "#6366f1"),
        })

    items = []
    for c in all_content:
        _slug = getattr(c, "slug", "")
        items.append({
            "slug": _slug,
            "url": f"/{canonical_path(slug_to_path(slug_to_fspath(_slug)))}" if _slug else "",
            "title": getattr(c, "title", ""),
            "description": (getattr(c, "description", "") or "")[:200],
            "pillar": getattr(c, "pillar", ""),
            "content_type": getattr(c, "content_type", "research"),
            "difficulty": getattr(c, "difficulty", "intermediate") or "intermediate",
            "sqi": getattr(c, "sqi", 0.0) or 0.0,
            "quality_badge": getattr(c, "quality_badge", ""),
            "knowledge_category": getattr(c, "knowledge_category", ""),
            "tags": getattr(c, "tags", []) or [],
            "technologies": getattr(c, "technologies", []) or [],
        })

    concepts = []
    if ontology and ontology.concept_count() > 0:
        for cid in sorted(ontology._concepts.keys()):
            concept = ontology.get_concept(cid)
            if concept is None:
                continue
            related = ontology.related_concepts(cid)
            relations_out: list[dict[str, Any]] = []
            for rel in related:
                if hasattr(rel, "source_id"):
                    relations_out.append({
                        "source_id": rel.source_id,
                        "target_id": rel.target_id,
                        "relation_type": rel.relation_type,
                        "strength": getattr(rel, "strength", 0.0),
                    })
            content_slugs: list[str] = []
            if concept_cache:
                content_slugs = sorted(slug for slug, cids in concept_cache.items() if cid in cids)

            concepts.append({
                "id": concept.id,
                "label": concept.label,
                "description": concept.description,
                "pillar": concept.pillar if hasattr(concept, "pillar") else "",
                "category": concept.category if hasattr(concept, "category") else "",
                "confidence_score": concept.confidence_score,
                "philosophical_lineage": getattr(concept, "philosophical_lineage", []),
                "epistemic_status": getattr(concept, "epistemic_status", ""),
                "normative_basis": getattr(concept, "normative_basis", ""),
                "ontological_commitment": getattr(concept, "ontological_commitment", ""),
                "temporal_ontology": getattr(concept, "temporal_ontology", ""),
                "uncertainty_class": getattr(concept, "uncertainty_class", ""),
                "governance_model": getattr(concept, "governance_model", ""),
                "semantic_contract_type": getattr(concept, "semantic_contract_type", ""),
                "philosophical_sources": getattr(concept, "philosophical_sources", []),
                "cross_pillar_analogs": getattr(concept, "cross_pillar_analogs", []),
                "eli5_explanation": getattr(concept, "eli5_explanation", ""),
                "analogy": getattr(concept, "analogy", ""),
                "concrete_example": getattr(concept, "concrete_example", ""),
                "feynman_difficulty": getattr(concept, "feynman_difficulty", 1),
                "explanation_quality": getattr(concept, "explanation_quality", 0.0),
                "gap_questions": getattr(concept, "gap_questions", []),
                "teach_back_prompt": getattr(concept, "teach_back_prompt", ""),
                "aliases": concept.aliases if hasattr(concept, "aliases") else [],
                "relations": relations_out,
                "content_slugs": content_slugs,
            })

    source_health = _safe_json(PROJECT_ROOT / "data" / "source_health.json")
    freshness_data = _safe_json(PROJECT_ROOT / "data" / "entry_freshness.json")
    philosophy = _safe_json(PROJECT_ROOT / "data" / "philosophy_metadata.json")

    # Computing aggregates
    pillar_counts: dict[str, dict[str, int]] = {}
    content_type_counts: dict[str, int] = {}
    sqi_by_pillar: dict[str, list[float]] = {"aml": [], "stock": [], "data-engineering": []}
    for c in all_content:
        p = getattr(c, "pillar", "") or ""
        ct = getattr(c, "content_type", "") or ""
        pillar_counts.setdefault(p, {"research": 0, "learn": 0, "knowledge": 0, "total": 0})
        pillar_counts[p]["total"] += 1
        pillar_counts[p][ct] = pillar_counts[p].get(ct, 0) + 1
        content_type_counts[ct] = content_type_counts.get(ct, 0) + 1
        sql = getattr(c, "sqi", None) or 0.0
        if sql and p in sqi_by_pillar:
            sqi_by_pillar[p].append(sql)

    pillar_quality: dict[str, dict[str, float]] = {}
    for pkey, vals in sqi_by_pillar.items():
        if vals:
            pillar_quality[pkey] = {
                "avg_sqi": round(sum(vals) / len(vals), 3),
                "min_sqi": round(min(vals), 3),
                "max_sqi": round(max(vals), 3),
            }

    origin_counts: dict[str, int] = {}
    concept_counts: dict[str, int] = {}
    if ontology:
        for cid in sorted(ontology._concepts.keys()):
            concept = ontology.get_concept(cid)
            if concept:
                p = concept.pillar if hasattr(concept, "pillar") else "cross-pillar"
                concept_counts[p] = concept_counts.get(p, 0) + 1
                ep = getattr(concept, "epistemic_status", "")
                if ep:
                    origin_counts[ep] = origin_counts.get(ep, 0) + 1

    source_summary: list[dict[str, Any]] = []
    for src in source_health.get("sources", []):
        source_summary.append({
            "key": src.get("key", ""),
            "name": src.get("name", ""),
            "pillar": src.get("pillar", ""),
            "status": src.get("status", "unknown"),
            "http_status": src.get("http_status", 0),
            "relevance": src.get("relevance", 0.0),
        })

    payload: dict[str, Any] = {
        "build_hash": build_hash,
        "site_url": site_url,
        "pillars": pillars,
        "pillar_data": pillars,
        "items": items,
        "items_total": len(items),
        "concepts": concepts,
        "concepts_total": len(concepts),
        "relations_total": ontology.relation_count() if ontology else 0,
        "pillar_counts": pillar_counts,
        "content_type_counts": content_type_counts,
        "pillar_quality": pillar_quality,
        "origin_counts": origin_counts,
        "concept_counts": concept_counts,
        "source_summary": source_summary,
        "source_total": source_health.get("total_sources", len(source_summary)),
        "source_active": source_health.get("active", 0),
        "source_degraded": source_health.get("degraded", 0),
        "source_error": source_health.get("error", 0),
        "freshness_summary": freshness_data.get("summary", {}),
        "philosophy_metadata_count": len(philosophy) if isinstance(philosophy, dict) else 0,
        "last_scored": freshness_data.get("generated_at", ""),
    }

    payload_hash = hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()
    payload["payload_hash"] = payload_hash
    return payload
