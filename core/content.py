"""Content wrapper for AcaciaFund registry data."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class Content:
    """Wrapper for content items from registry.json."""

    slug: str
    title: str
    pillar: str
    content_type: str
    category: str = ""
    created_at: Optional[datetime] = None
    date_str: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    body_html: str = ""
    description: str = ""
    bloom_questions: List[Dict[str, Any]] = field(default_factory=list)
    trend_strength: float = 0.0
    adoption_level: str = ""
    impact_level: str = ""
    trend_categories: str = ""
    source_verified: bool = False
    source_evidence: List[str] = field(default_factory=list)
    quality_badge: str = ""
    sqi_svg: str = ""
    topic_icon_html: str = ""
    visual_fingerprint: str = ""
    layer_badge: str = ""
    layer_sub: str = ""
    section_images: List[Dict[str, Any]] = field(default_factory=list)
    prev_post: Optional["Content"] = None
    next_post: Optional["Content"] = None
    related: List["Content"] = field(default_factory=list)
    related_learn: List["Content"] = field(default_factory=list)
    r_quiz_json: str = ""
    quiz_json: str = ""
    highest_bloom: int = 0
    knowledge_category: str = "reference"
    difficulty: Optional[str] = None
    featured_image: Optional[str] = None
    image_credit: Optional[str] = None
    author: str = "AcaciaFund"
    sqi: float = 0.0
    enriched: bool = False
    enriched_at: Optional[str] = None
    signals: Optional[Dict[str, Any]] = None
    source_breakdown: Optional[Dict[str, Any]] = None
    cross_pillar_html: Optional[str] = None
    updated_at: Optional[str] = None
    prerequisites: Optional[List[str]] = None
    curated_relations: Optional[List[Dict[str, Any]]] = None
    quality_flags: List[str] = field(default_factory=list)
    flashcards: List[Dict[str, Any]] = field(default_factory=list)
    technologies: List[str] = field(default_factory=list)
    use_cases: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Content":
        """Create Content instance from dictionary."""
        created_at = None
        date_str = None

        # Try to parse created_at
        if "created_at" in data and data["created_at"]:
            try:
                created_at = datetime.fromisoformat(data["created_at"].replace("Z", "+00:00"))
            except (ValueError, TypeError):
                pass

        # Try to parse date_str
        if "date_str" in data and data["date_str"]:
            date_str = data["date_str"]

        # Multi-tag migration: fall back to wrapping single category if tags are empty
        tags: List[str] = data.get("tags", [])
        if not tags and "category" in data and data["category"]:
            tags = [data["category"]]

        return cls(
            slug=data.get("slug", ""),
            title=data.get("title", ""),
            pillar=data.get("pillar", ""),
            content_type=data.get("content_type", "research"),
            category=data.get("category", ""),
            created_at=created_at,
            date_str=date_str,
            tags=tags,
            body_html=data.get("body_html", ""),
            description=data.get("description", ""),
            bloom_questions=data.get("bloom_questions", []),
            trend_strength=data.get("trend_strength", 0.0),
            adoption_level=data.get("adoption_level", ""),
            impact_level=data.get("impact_level", ""),
            trend_categories=data.get("trend_categories", ""),
            source_verified=data.get("source_verified", False),
            source_evidence=data.get("source_evidence", []),
            quality_badge=data.get("quality_badge", ""),
            sqi_svg=data.get("sqi_svg", ""),
            topic_icon_html=data.get("topic_icon_html", ""),
            visual_fingerprint=data.get("visual_fingerprint", ""),
            layer_badge=data.get("layer_badge", ""),
            layer_sub=data.get("layer_sub", ""),
            section_images=data.get("section_images", []),
            difficulty=data.get("difficulty"),
            featured_image=data.get("featured_image"),
            image_credit=data.get("image_credit"),
            author=data.get("author", "AcaciaFund"),
            sqi=data.get("sqi", 0.0),
            enriched=data.get("enriched", False),
            enriched_at=data.get("enriched_at"),
            signals=data.get("signals"),
            source_breakdown=data.get("source_breakdown"),
            cross_pillar_html=data.get("cross_pillar_html"),
            updated_at=data.get("updated_at"),
            prerequisites=data.get("prerequisites"),
            curated_relations=data.get("curated_relations"),
            quality_flags=data.get("quality_flags", []),
            knowledge_category=data.get("knowledge_category", "reference"),
            flashcards=data.get("flashcards", []),
            technologies=data.get("technologies", []),
            use_cases=data.get("use_cases", []),
        )
