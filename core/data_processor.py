"""Data processor module - enriches data with trend, source, and quality information."""

from typing import Any, Dict, List

from core.dto import KnowledgeDTO, LearnDTO, QualityInfo, ResearchDTO, SourceInfo, TrendInfo


def enrich_knowledge_item(item: Any, enrichment_data: Dict[str, Any]) -> KnowledgeDTO:
    """Convert a raw knowledge item to a DTO with enrichment data.

    Args:
        item: Raw knowledge content item
        enrichment_data: Dictionary with trend_detection, source_verification, quality_scores

    Returns:
        KnowledgeDTO with all enrichment data applied
    """
    slug = item.slug
    trend_data = enrichment_data.get("trend_detection", {}).get(slug, {})
    source_data = enrichment_data.get("source_verification", {}).get(slug, {})
    quality_data = enrichment_data.get("quality_scores", {}).get(slug, {})

    return KnowledgeDTO(
        slug=slug,
        title=item.title or "",
        body_html=item.body_html or "",
        description=item.description or "",
        pillar=item.pillar or "",
        tags=item.tags or [],
        knowledge_category=item.knowledge_category or "",
        bloom_questions=getattr(item, "bloom_questions", []) or [],
        # Enrichment
        trend=TrendInfo(
            trend_strength=trend_data.get("trend_strength", 0),
            adoption_level=trend_data.get("adoption_level", "mainstream"),
            impact_level=trend_data.get("impact_level", "low"),
            trend_categories=trend_data.get("trend_categories", ""),
        ),
        source=SourceInfo(
            source_score=source_data.get("source_score", 0),
            source_type=source_data.get("source_type", ""),
            verified=source_data.get("verified", False),
            evidence_level=source_data.get("evidence_level", ""),
            evidence=source_data.get("evidence", []),
        ),
        quality=QualityInfo(
            quality_score=quality_data.get("quality_score", 0),
            quality_badge="",
            sqi=quality_data.get("sqi", 0),
            avg_sqi=quality_data.get("avg_sqi", 0),
        ),
    )


def enrich_learn_item(item: Any, enrichment_data: Dict[str, Any]) -> LearnDTO:
    """Convert a raw learn item to a DTO with enrichment data.

    Args:
        item: Raw learn content item
        enrichment_data: Dictionary with trend_detection, source_verification, quality_scores

    Returns:
        LearnDTO with all enrichment data applied
    """
    slug = item.slug
    trend_data = enrichment_data.get("trend_detection", {}).get(slug, {})
    source_data = enrichment_data.get("source_verification", {}).get(slug, {})
    quality_data = enrichment_data.get("quality_scores", {}).get(slug, {})

    return LearnDTO(
        slug=slug,
        title=item.title or "",
        body_html=item.body_html or "",
        description=item.description or "",
        pillar=item.pillar or "",
        tags=item.tags or [],
        difficulty=getattr(item, "difficulty", "") or "",
        bloom_questions=getattr(item, "bloom_questions", []) or [],
        # Enrichment
        trend=TrendInfo(
            trend_strength=trend_data.get("trend_strength", 0),
            adoption_level=trend_data.get("adoption_level", "mainstream"),
            impact_level=trend_data.get("impact_level", "low"),
            trend_categories=trend_data.get("trend_categories", ""),
        ),
        source=SourceInfo(
            source_score=source_data.get("source_score", 0),
            source_type=source_data.get("source_type", ""),
            verified=source_data.get("verified", False),
            evidence_level=source_data.get("evidence_level", ""),
            evidence=source_data.get("evidence", []),
        ),
        quality=QualityInfo(
            quality_score=quality_data.get("quality_score", 0),
            quality_badge="",
            sqi=quality_data.get("sqi", 0),
            avg_sqi=quality_data.get("avg_sqi", 0),
        ),
    )


def enrich_research_item(item: Any, enrichment_data: Dict[str, Any]) -> ResearchDTO:
    """Convert a raw research item to a DTO with enrichment data.

    Args:
        item: Raw research content item
        enrichment_data: Dictionary with trend_detection, source_verification, quality_scores

    Returns:
        ResearchDTO with all enrichment data applied
    """
    slug = item.slug
    trend_data = enrichment_data.get("trend_detection", {}).get(slug, {})
    source_data = enrichment_data.get("source_verification", {}).get(slug, {})
    quality_data = enrichment_data.get("quality_scores", {}).get(slug, {})

    return ResearchDTO(
        slug=slug,
        title=item.title or "",
        body_html=item.body_html or "",
        description=item.description or "",
        pillar=item.pillar or "aml",
        tags=item.tags or [],
        bloom_questions=getattr(item, "bloom_questions", []) or [],
        # Enrichment
        trend=TrendInfo(
            trend_strength=trend_data.get("trend_strength", 0),
            adoption_level=trend_data.get("adoption_level", "mainstream"),
            impact_level=trend_data.get("impact_level", "low"),
            trend_categories=trend_data.get("trend_categories", ""),
        ),
        source=SourceInfo(
            source_score=source_data.get("source_score", 0),
            source_type=source_data.get("source_type", ""),
            verified=source_data.get("verified", False),
            evidence_level=source_data.get("evidence_level", ""),
            evidence=source_data.get("evidence", []),
        ),
        quality=QualityInfo(
            quality_score=quality_data.get("quality_score", 0),
            quality_badge="",
            sqi=quality_data.get("sqi", 0),
            avg_sqi=quality_data.get("avg_sqi", 0),
        ),
    )


def prepare_lessons_list(learn_items: List[LearnDTO]) -> List[LearnDTO]:
    """Prepare learn lessons list for prev/next navigation.

    Args:
        learn_items: List of LearnDTO items

    Returns:
        List of lessons (excluding the meta "learn" page), sorted by difficulty, pillar, title
    """
    lessons = [li for li in learn_items if li.slug != "learn"]
    # Sort by difficulty, pillar, title
    return sorted(
        lessons,
        key=lambda x: (
            {"beginner": 0, "intermediate": 1, "advanced": 2}.get(x.difficulty, 3),
            x.pillar or "",
            x.title or "",
        ),
    )
