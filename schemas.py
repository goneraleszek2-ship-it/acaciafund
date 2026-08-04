"""Schemas for AcaciaFund registry data."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ContentItem(BaseModel):
    """A single content item in the registry."""

    slug: str = Field(..., min_length=1, pattern=r"^[a-z0-9][a-z0-9/-]*[a-z0-9]$")
    title: str = Field(..., min_length=1)
    content_type: str = Field(..., pattern=r"^(research|learn|knowledge)$")
    pillar: str = Field(..., min_length=1)
    tags: List[str] = Field(default_factory=list)
    category: Optional[str] = None
    body_html: str = ""
    description: str = ""
    date_str: Optional[str] = None
    source_breakdown: Optional[Dict[str, int]] = None
    sqi: Optional[float] = Field(None, ge=0.0, le=1.0)
    enriched: bool = False
    enriched_at: Optional[str] = None
    citations: Optional[List[str]] = None

    # MathWorld-inspired fields
    contributors: Optional[List[dict]] = None
    see_also: Optional[List[dict]] = None
    explore_tools: Optional[List[dict]] = None
    subject_classifications: Optional[List[List[str]]] = None
    last_verified: Optional[str] = None

    model_config = {"extra": "allow"}


class RegistryData(BaseModel):
    """Registry data schema with constrained content items."""

    last_run: Optional[str] = None
    content: Optional[List[ContentItem]] = None
    pipeline_stages: Optional[List[Dict[str, Any]]] = None
    mcp_integrations: Optional[List[Dict[str, Any]]] = None
    planned_features: Optional[List[Dict[str, Any]]] = None
    last_updated: Optional[str] = None
    learn: Optional[List[Dict[str, Any]]] = None

    model_config = {"extra": "allow"}
