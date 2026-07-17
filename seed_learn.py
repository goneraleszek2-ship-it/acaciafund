"""Seed learn data for AcaciaFund."""

# Curated relations between topics
CURATED_RELATIONS: Dict[str, List[str]] = {
    "aml": ["kyc", "compliance", "regulations"],
    "data-engineering": ["pipelines", "etl", "warehousing"],
    "docs": ["api", "guides", "reference"],
}

# Prerequisites for learning paths (pillar-level topics)
PREREQUISITES: Dict[str, List[str]] = {
    "aml": ["financial-regulations", "compliance"],
    "data-engineering": ["python", "sql"],
    "docs": ["technical-writing", "api-design"],
}

# Learning path prerequisites are auto-derived from ontology 'requires' relations
# at build time by core/schema_builder.py → build_prerequisite_graph().
# See data/ontology.json → relations[].relation_type == "requires" for the source of truth.
# Run: python3 -c "
# from core.ontology import OntologyManager
# from core.schema_builder import build_prerequisite_graph
# m = OntologyManager.load('data/ontology.json')
# g = build_prerequisite_graph(m)
# for s, t in g.edges():
#     print(f'  {s} -> {t}')
# "
