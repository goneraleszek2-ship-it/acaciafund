from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import datetime, timezone

class AcaciaContent(BaseModel):
    slug: str = Field(..., description="Slug without language prefix, e.g., 'blog/2026-06-01-aml' or 'about'")
    language: str = Field(..., description="Language code, e.g., 'en', 'pl'")
    title: str = Field(..., min_length=1)
    body_html: str = Field(..., description="Pre-rendered HTML from Markdown")
    category: str = Field(..., description="e.g., 'aml', 'markets', 'science'")
    tags: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None

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
    content: List[AcaciaContent] = Field(default_factory=list)
    pipeline_stages: List[PipelineStage] = Field(default_factory=list)
    mcp_integrations: List[MCPIntegration] = Field(default_factory=list)
    planned_features: List[PlannedFeature] = Field(default_factory=list)
