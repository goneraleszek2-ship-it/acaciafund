"""Data Transfer Objects for AcaciaFund - clean data structures for templates."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class TrendInfo:
    """Trend detection information for an article."""

    trend_strength: float = 0.0
    adoption_level: str = "mainstream"
    impact_level: str = "low"
    trend_categories: str = ""


@dataclass
class SourceInfo:
    """Source verification information for an article."""

    source_score: float = 0.0
    source_type: str = ""
    verified: bool = False
    evidence_level: str = ""
    evidence: List[str] = field(default_factory=list)


@dataclass
class QualityInfo:
    """Quality metrics for an article."""

    quality_score: float = 0.0
    quality_badge: str = ""
    sqi: float = 0.0
    avg_sqi: float = 0.0


@dataclass
class KnowledgeDTO:
    """DTO for knowledge articles - clean data for templates."""

    slug: str
    title: str
    body_html: str
    description: str
    pillar: str
    tags: List[str]
    knowledge_category: str
    bloom_questions: List[Dict[str, Any]] = field(default_factory=list)

    # Enriched data
    trend: TrendInfo = field(default_factory=TrendInfo)
    source: SourceInfo = field(default_factory=SourceInfo)
    quality: QualityInfo = field(default_factory=QualityInfo)

    # Computed
    related_research: List["KnowledgeDTO"] = field(default_factory=list)
    related_learn: List["KnowledgeDTO"] = field(default_factory=list)
    visual_fingerprint: str = ""
    layer_badge: str = ""
    layer_sub: str = ""
    quality_badge: str = ""
    trend_strength: float = 0.0
    adoption_level: str = ""
    impact_level: str = ""
    trend_categories: str = ""
    source_verified: bool = False
    source_evidence: List[str] = field(default_factory=list)
    quiz_json: str = ""


@dataclass
class LearnLesson:
    """DTO for learn lessons."""

    slug: str
    title: str
    pillar: str
    difficulty: str


@dataclass
class LearnDTO:
    """DTO for learn articles - clean data for templates."""

    slug: str
    title: str
    body_html: str
    description: str
    pillar: str
    tags: List[str]
    difficulty: str
    bloom_questions: List[Dict[str, Any]] = field(default_factory=list)

    # Enriched data
    trend: TrendInfo = field(default_factory=TrendInfo)
    source: SourceInfo = field(default_factory=SourceInfo)
    quality: QualityInfo = field(default_factory=QualityInfo)

    # Computed
    prev_lesson: Optional[LearnLesson] = None
    next_lesson: Optional[LearnLesson] = None
    related_research: List["LearnDTO"] = field(default_factory=list)
    related_knowledge: List["LearnDTO"] = field(default_factory=list)
    visual_fingerprint: str = ""
    layer_badge: str = ""
    quality_badge: str = ""
    trend_strength: float = 0.0
    adoption_level: str = ""
    impact_level: str = ""
    trend_categories: str = ""
    source_verified: bool = False
    source_evidence: List[str] = field(default_factory=list)
    quiz_json: str = ""


@dataclass
class ResearchDTO:
    """DTO for research articles - clean data for templates."""

    slug: str
    title: str
    body_html: str
    description: str
    pillar: str
    tags: List[str]
    bloom_questions: List[Dict[str, Any]] = field(default_factory=list)

    # Enriched data
    trend: TrendInfo = field(default_factory=TrendInfo)
    source: SourceInfo = field(default_factory=SourceInfo)
    quality: QualityInfo = field(default_factory=QualityInfo)

    # Computed
    prev_post: Optional["ResearchDTO"] = None
    next_post: Optional["ResearchDTO"] = None
    related: List["ResearchDTO"] = field(default_factory=list)
    related_learn: List["ResearchDTO"] = field(default_factory=list)
    visual_fingerprint: str = ""
    layer_badge: str = ""
    sqi_svg: str = ""
    topic_icon_html: str = ""
    quality_badge: str = ""
    trend_strength: float = 0.0
    adoption_level: str = ""
    impact_level: str = ""
    trend_categories: str = ""
    source_verified: bool = False
    source_evidence: List[str] = field(default_factory=list)
    r_quiz_json: str = ""


@dataclass
class TemplateContext:
    """Complete context passed to templates."""

    # Basic info
    site_name: str = ""
    site_url: str = ""
    site_description: str = ""

    # Content
    knowledge_items: List[KnowledgeDTO] = field(default_factory=list)
    learn_items: List[LearnDTO] = field(default_factory=list)
    research_items: List[ResearchDTO] = field(default_factory=list)
    learn_lessons: List[LearnLesson] = field(default_factory=list)

    # Navigation
    current_item: Optional[Any] = None
    prev_item: Optional[Any] = None
    next_item: Optional[Any] = None

    # Page info
    page_path: str = ""
    page_body: str = ""
    toc_items: List[Dict[str, Any]] = field(default_factory=list)

    # UI components
    visual_fingerprint: str = ""
    layer_badge: str = ""
    quality_badge: str = ""
    sqi_svg: str = ""
    topic_icon_html: str = ""

    # Metadata
    trend_strength: float = 0.0
    adoption_level: str = ""
    impact_level: str = ""
    trend_categories: str = ""
    source_verified: bool = False
    source_evidence: List[str] = field(default_factory=list)
    quiz_json: str = ""
    r_quiz_json: str = ""
    k_quiz_json: str = ""
