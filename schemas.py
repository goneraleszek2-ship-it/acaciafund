import re
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Any
from datetime import datetime, timezone

PLACEHOLDER_PATTERNS = [
    r'Key Concept\s*\d',
    r'Lorem ipsum',
    r'\[TODO\]',
    r'\[PLACEHOLDER\]',
    r'\[INSERT',
]


class AcaciaContent(BaseModel):
    slug: str
    language: str = "en"
    title: str
    description: str = ""
    body_html: str = ""
    category: str = "post"
    content_type: str = ""  # research | learn | knowledge
    knowledge_category: str = ""  # platform | guide | reference | architecture
    tags: List[str] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None
    pillar: str = ""
    difficulty: str = ""  # beginner | intermediate | advanced
    date_str: str = ""
    thumbnail_svg: str = ""
    og_svg: str = ""
    featured_image: str = ""
    trending_html: str = ""
    analysis_html: str = ""
    cross_pillar_html: str = ""
    bloom_questions: List[dict] = []
    flashcards: List[dict] = []
    signals: dict = {}
    source_breakdown: dict = {}
    quality_metrics: dict = {}
    lineage: dict = {}
    quality_flags: List[str] = []

    @validator('slug')
    def slug_must_be_alphanumeric_dashes_slashes(cls, v):
        if not all(c.isalnum() or c in '-/' for c in v):
            raise ValueError('slug must be alphanumeric, hyphen, or slash')
        return v.lower()

    @validator('language')
    def language_must_be_valid_code(cls, v):
        if not (v.isalpha() and len(v) == 2 and v.islower()):
            raise ValueError('language must be a two-letter lowercase code (e.g., en, pl)')
        return v

    @validator('body_html')
    def reject_placeholder_content(cls, v):
        if not v:
            return v
        stripped = re.sub(r'<[^>]+>', '', v)
        for pat in PLACEHOLDER_PATTERNS:
            if re.search(pat, stripped, re.IGNORECASE):
                print(f'  WARNING: body_html contains placeholder ({pat}) — stripping')
                v = re.sub(r'(?i)' + pat, '', v)
        stripped = re.sub(r'<[^>]+>', '', v)
        if len(stripped.strip()) < 200:
            print(f'  WARNING: body_html too short ({len(stripped.strip())} chars, minimum 200)')
        return v


class PipelineStage(BaseModel):
    id: str
    title: str
    description: str


class MCPIntegration(BaseModel):
    name: str
    status: str
    description: str


class PlannedFeature(BaseModel):
    name: str
    description: str


class RegistryData(BaseModel):
    last_run: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    content: List[AcaciaContent] = []
    pipeline_stages: List[PipelineStage] = []
    mcp_integrations: List[MCPIntegration] = []
    planned_features: List[PlannedFeature] = []
