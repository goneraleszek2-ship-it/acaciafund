"""Seed learn data for AcaciaFund."""

from typing import Dict, List

# Curated relations between topics
CURATED_RELATIONS: Dict[str, List[str]] = {
    "aml": ["kyc", "compliance", "regulations"],
    "data-engineering": ["pipelines", "etl", "warehousing"],
    "docs": ["api", "guides", "reference"],
}

# Prerequisites for learning paths
PREREQUISITES: Dict[str, List[str]] = {
    "aml": ["financial-regulations", "compliance"],
    "data-engineering": ["python", "sql"],
    "docs": ["technical-writing", "api-design"],
}
