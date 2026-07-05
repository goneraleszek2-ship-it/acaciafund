"""Schemas for AcaciaFund registry data."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class RegistryData(BaseModel):
    """Registry data schema."""

    last_run: Optional[str] = None
    content: Optional[List[Dict[str, Any]]] = None
    pipeline_stages: Optional[List[Dict[str, Any]]] = None
    mcp_integrations: Optional[List[Dict[str, Any]]] = None
    planned_features: Optional[List[Dict[str, Any]]] = None
    last_updated: Optional[str] = None
    learn: Optional[List[Dict[str, Any]]] = None
