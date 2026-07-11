"""Ontology framework for AcaciaFund — structured knowledge representation.

Defines entities, relationships, and hierarchies for the three pillars
(Compliance, Markets, Data Engineering). Integrates with the knowledge graph
and provides concept extraction/matching utilities for ingestion pipelines.
"""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class Concept(BaseModel):
    """A named knowledge entity within the ontology."""

    id: str = Field(..., min_length=1, description="Unique concept identifier (slug-style)")
    label: str = Field(..., min_length=1, description="Human-readable name")
    description: str = ""
    pillar: str = Field(
        ..., description="Owning pillar: aml | stock | data-engineering | cross-pillar"
    )
    category: str = Field(
        default="reference",
        description="Knowledge category key matching KNOWLEDGE_CATEGORIES or PILLAR_SUBCATEGORIES",
    )
    aliases: List[str] = Field(default_factory=list)
    properties: Dict[str, Any] = Field(default_factory=dict)
    source_inspiration: str = Field(
        default="",
        description="Originating source URL or organisation name",
    )
    confidence_score: float = Field(default=1.0, ge=0.0, le=1.0)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    model_config = {"extra": "allow"}


class Relation(BaseModel):
    """A directed relationship between two concepts."""

    source_id: str = Field(..., min_length=1)
    target_id: str = Field(..., min_length=1)
    relation_type: str = Field(
        ...,
        min_length=1,
        description="e.g. requires, part_of, influences, supersedes, enables, detects",
    )
    strength: float = Field(default=1.0, ge=0.0, le=1.0)
    evidence: List[str] = Field(default_factory=list)
    pillar: str = Field(default="cross-pillar")
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    model_config = {"extra": "allow"}


class ResourceLink(BaseModel):
    """A link from a concept to an external authoritative resource."""

    concept_id: str = Field(..., min_length=1)
    url: str = Field(..., min_length=1)
    title: str = ""
    description: str = ""
    source_org: str = Field(default="", description="Organisation that owns the resource")
    credibility_score: float = Field(default=0.5, ge=0.0, le=1.0)
    access_date: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%d")
    )
    license_info: str = ""

    model_config = {"extra": "allow"}


class InspirationSource(BaseModel):
    """An external knowledge source configured per pillar."""

    url: str
    name: str
    frequency: str = Field(default="weekly", description="Scrape/sync frequency")
    relevance: float = Field(default=0.5, ge=0.0, le=1.0)
    description: str = ""
    last_fetched: Optional[str] = None
    enabled: bool = True

    model_config = {"extra": "allow"}


# ---------------------------------------------------------------------------
# OntologyManager — central registry
# ---------------------------------------------------------------------------

# Canonical relation types used across the system
RELATION_TYPES = {
    "requires": "Target concept is a prerequisite for source",
    "part_of": "Source concept is a component of target",
    "influences": "Source concept has measurable impact on target",
    "enables": "Source concept unlocks or facilitates target",
    "detects": "Source concept is used to identify target",
    "supersedes": "Source concept replaces or improves upon target",
    "related_to": "General topical similarity (weaker than others)",
    "implements": "Source concept is a concrete implementation of target",
    "regulates": "Source concept governs or constrains target",
    "measures": "Source concept quantifies or evaluates target",
}

# Valid pillar keys
PILLAR_KEYS = {"aml", "stock", "data-engineering", "cross-pillar"}

# Pre-defined concept seeds per pillar (expandable)
PILLAR_CONCEPT_SEEDS: Dict[str, List[Dict[str, Any]]] = {
    "aml": [
        {"id": "kyc", "label": "Know Your Customer (KYC)", "category": "cdd-kyc",
         "aliases": ["KYC", "know-your-customer"]},
        {"id": "cdd", "label": "Customer Due Diligence", "category": "cdd-kyc",
         "aliases": ["CDD"]},
        {"id": "edd", "label": "Enhanced Due Diligence", "category": "cdd-kyc",
         "aliases": ["EDD"]},
        {"id": "sar", "label": "Suspicious Activity Report", "category": "sar-str",
         "aliases": ["SAR", "suspicious-activity-reporting"]},
        {"id": "str", "label": "Suspicious Transaction Report", "category": "sar-str",
         "aliases": ["STR"]},
        {"id": "ctr", "label": "Currency Transaction Report", "category": "sar-str",
         "aliases": ["CTR"]},
        {"id": "pep", "label": "Politically Exposed Person", "category": "risk-assessment",
         "aliases": ["PEP", "politically-exposed-person"]},
        {"id": "sanctions-screening", "label": "Sanctions Screening", "category": "sanctions",
         "aliases": ["OFAC screening", "sanctions list check"]},
        {"id": "transaction-monitoring", "label": "Transaction Monitoring", "category": "transaction-monitoring",
         "aliases": ["TM", "transaction surveillance"]},
        {"id": "entity-resolution", "label": "Entity Resolution", "category": "advanced-techniques",
         "aliases": ["entity matching", "record linkage"]},
        {"id": "network-analysis", "label": "Network Analysis for AML", "category": "advanced-techniques",
         "aliases": ["graph analytics", "network forensics"]},
        {"id": "beneficial-ownership", "label": "Beneficial Ownership", "category": "regulations",
         "aliases": ["UBO", "ultimate beneficial ownership", "BO"]},
        {"id": "fatf-recommendations", "label": "FATF Recommendations", "category": "regulations",
         "aliases": ["FATF 40 Recommendations"]},
        {"id": "bsa", "label": "Bank Secrecy Act", "category": "regulations",
         "aliases": ["BSA", "Currency and Foreign Transactions Act"]},
        {"id": "tbml", "label": "Trade-Based Money Laundering", "category": "risk-assessment",
         "aliases": ["TBML", "trade-based-ml"]},
        {"id": "regtech", "label": "Regulatory Technology", "category": "regtech",
         "aliases": ["RegTech"]},
    ],
    "stock": [
        {"id": "lob", "label": "Limit Order Book", "category": "foundations",
         "aliases": ["LOB", "order book"]},
        {"id": "market-microstructure", "label": "Market Microstructure", "category": "foundations",
         "aliases": ["microstructure"]},
        {"id": "volatility-surface", "label": "Implied Volatility Surface", "category": "market-analysis",
         "aliases": ["IV surface", "vol surface"]},
        {"id": "hawkes-process", "label": "Hawkes Process", "category": "advanced-techniques",
         "aliases": ["Hawkes self-exciting process"]},
        {"id": "vpin", "label": "VPIN Toxicity", "category": "advanced-techniques",
         "aliases": ["Volume-Synchronized Probability of Informed Trading"]},
        {"id": "supply-chain-analysis", "label": "Supply Chain Analysis", "category": "industry-analysis",
         "aliases": ["supply chain risk"]},
        {"id": "earnings-analysis", "label": "Earnings Analysis", "category": "market-analysis",
         "aliases": ["earnings season", "earnings reports"]},
        {"id": "commodity-trading", "label": "Commodity Trading Strategies", "category": "strategies",
         "aliases": ["commodity futures", "commodity hedging"]},
        {"id": "semiconductor-industry", "label": "Semiconductor Industry", "category": "industry-analysis",
         "aliases": ["chip industry", "semiconductor supply chain"]},
        {"id": "ai-hardware", "label": "AI Hardware Trends", "category": "industry-analysis",
         "aliases": ["AI chips", "GPU market", "AI accelerators"]},
        {"id": "portfolio-optimization", "label": "Portfolio Optimization", "category": "strategies",
         "aliases": ["asset allocation", "portfolio construction"]},
        {"id": "risk-parity", "label": "Risk Parity", "category": "strategies",
         "aliases": ["risk-balanced portfolio"]},
        {"id": "factor-investing", "label": "Factor Investing", "category": "strategies",
         "aliases": ["smart beta", "factor models"]},
        {"id": "technical-analysis", "label": "Technical Analysis", "category": "market-analysis",
         "aliases": ["chart patterns", "technical indicators"]},
        {"id": "macro-analysis", "label": "Macroeconomic Analysis", "category": "market-analysis",
         "aliases": ["macro analysis", "economic indicators"]},
    ],
    "data-engineering": [
        {"id": "etl", "label": "Extract-Transform-Load", "category": "foundations",
         "aliases": ["ETL", "extract transform load"]},
        {"id": "elt", "label": "Extract-Load-Transform", "category": "foundations",
         "aliases": ["ELT"]},
        {"id": "cdc", "label": "Change Data Capture", "category": "advanced-techniques",
         "aliases": ["CDC", "change-data-capture"]},
        {"id": "data-lake", "label": "Data Lake", "category": "foundations",
         "aliases": ["data lakehouse"]},
        {"id": "data-warehouse", "label": "Data Warehouse", "category": "foundations",
         "aliases": ["DWH", "analytical data store"]},
        {"id": "data-mesh", "label": "Data Mesh", "category": "architecture",
         "aliases": ["data mesh architecture"]},
        {"id": "streaming", "label": "Stream Processing", "category": "advanced-techniques",
         "aliases": ["real-time processing", "stream processing"]},
        {"id": "batch-processing", "label": "Batch Processing", "category": "foundations",
         "aliases": ["batch jobs", "scheduled processing"]},
        {"id": "dbt", "label": "dbt (data build tool)", "category": "advanced-techniques",
         "aliases": ["data build tool"]},
        {"id": "dagster", "label": "Dagster Orchestrator", "category": "advanced-techniques",
         "aliases": ["dagster"]},
        {"id": "apache-flink", "label": "Apache Flink", "category": "advanced-techniques",
         "aliases": ["Flink"]},
        {"id": "apache-kafka", "label": "Apache Kafka", "category": "advanced-techniques",
         "aliases": ["Kafka"]},
        {"id": "apache-iceberg", "label": "Apache Iceberg", "category": "advanced-techniques",
         "aliases": ["Iceberg", "table format"]},
        {"id": "schema-registry", "label": "Schema Registry", "category": "architecture",
         "aliases": ["schema evolution", "schema management"]},
        {"id": "data-contracts", "label": "Data Contracts", "category": "architecture",
         "aliases": ["data contract", "SLA for data"]},
        {"id": "data-quality", "label": "Data Quality", "category": "best-practices",
         "aliases": ["data observability", "data validation"]},
        {"id": "arrow-parquet", "label": "Apache Arrow / Parquet", "category": "advanced-techniques",
         "aliases": ["Arrow", "Parquet", "columnar storage"]},
    ],
}

# Pre-defined relation seeds (source_id, target_id, relation_type, pillar)
PILLAR_RELATION_SEEDS: List[Tuple[str, str, str, str]] = [
    # Compliance
    ("cdd", "kyc", "part_of", "aml"),
    ("edd", "cdd", "part_of", "aml"),
    ("sar", "transaction-monitoring", "enables", "aml"),
    ("str", "transaction-monitoring", "enables", "aml"),
    ("ctr", "transaction-monitoring", "enables", "aml"),
    ("pep", "edd", "requires", "aml"),
    ("sanctions-screening", "kyc", "part_of", "aml"),
    ("entity-resolution", "network-analysis", "related_to", "aml"),
    ("beneficial-ownership", "cdd", "requires", "aml"),
    ("fatf-recommendations", "kyc", "regulates", "aml"),
    ("fatf-recommendations", "sar", "regulates", "aml"),
    ("bsa", "sar", "regulates", "aml"),
    ("bsa", "ctr", "regulates", "aml"),
    ("tbml", "transaction-monitoring", "detects", "aml"),
    ("regtech", "transaction-monitoring", "enables", "aml"),
    ("regtech", "kyc", "enables", "aml"),
    # Markets
    ("market-microstructure", "lob", "requires", "stock"),
    ("hawkes-process", "market-microstructure", "influences", "stock"),
    ("vpin", "market-microstructure", "measures", "stock"),
    ("volatility-surface", "market-microstructure", "related_to", "stock"),
    ("earnings-analysis", "macro-analysis", "related_to", "stock"),
    ("commodity-trading", "macro-analysis", "related_to", "stock"),
    ("portfolio-optimization", "risk-parity", "implements", "stock"),
    ("factor-investing", "portfolio-optimization", "implements", "stock"),
    ("technical-analysis", "market-microstructure", "influences", "stock"),
    ("semiconductor-industry", "supply-chain-analysis", "part_of", "stock"),
    ("ai-hardware", "semiconductor-industry", "influences", "stock"),
    # Data Engineering
    ("elt", "etl", "supersedes", "data-engineering"),
    ("cdc", "batch-processing", "related_to", "data-engineering"),
    ("streaming", "batch-processing", "related_to", "data-engineering"),
    ("dbt", "elt", "implements", "data-engineering"),
    ("dagster", "etl", "implements", "data-engineering"),
    ("dagster", "elt", "implements", "data-engineering"),
    ("apache-flink", "streaming", "implements", "data-engineering"),
    ("apache-kafka", "streaming", "enables", "data-engineering"),
    ("apache-iceberg", "data-lake", "implements", "data-engineering"),
    ("schema-registry", "data-contracts", "implements", "data-engineering"),
    ("data-contracts", "data-quality", "enables", "data-engineering"),
    ("arrow-parquet", "data-lake", "enables", "data-engineering"),
    ("data-mesh", "data-contracts", "requires", "data-engineering"),
]

# Cross-pillar relations
CROSS_PILLAR_SEEDS: List[Tuple[str, str, str]] = [
    ("transaction-monitoring", "streaming", "requires"),
    ("transaction-monitoring", "cdc", "requires"),
    ("entity-resolution", "data-quality", "requires"),
    ("network-analysis", "data-mesh", "related_to"),
    ("regtech", "dagster", "related_to"),
    ("market-microstructure", "streaming", "requires"),
    ("data-contracts", "fatf-recommendations", "related_to"),
]


class OntologyManager:
    """Central registry for concepts, relations, and resource links."""

    def __init__(self) -> None:
        self._concepts: Dict[str, Concept] = {}
        self._relations: List[Relation] = []
        self._resource_links: List[ResourceLink] = []
        self._alias_index: Dict[str, str] = {}  # alias_lower → concept_id
        self._pillar_index: Dict[str, Set[str]] = defaultdict(set)  # pillar → {concept_ids}
        self._category_index: Dict[str, Set[str]] = defaultdict(set)  # category → {concept_ids}

    # ---- Concepts ----

    def add_concept(self, concept: Concept, *, overwrite: bool = False) -> None:
        """Add or update a concept in the ontology."""
        existing = self._concepts.get(concept.id)
        if existing and not overwrite:
            # Merge aliases
            for alias in concept.aliases:
                if alias.lower() not in self._alias_index:
                    self._alias_index[alias.lower()] = concept.id
            existing.aliases = list(set(existing.aliases + concept.aliases))
            existing.properties.update(concept.properties)
            existing.updated_at = datetime.now(timezone.utc).isoformat()
            return
        self._concepts[concept.id] = concept
        self._pillar_index[concept.pillar].add(concept.id)
        self._category_index[concept.category].add(concept.id)
        for alias in concept.aliases:
            self._alias_index[alias.lower()] = concept.id

    def get_concept(self, concept_id: str) -> Optional[Concept]:
        return self._concepts.get(concept_id)

    def resolve_alias(self, name: str) -> Optional[Concept]:
        """Resolve a label or alias to a Concept."""
        cid = self._alias_index.get(name.lower())
        if cid:
            return self._concepts.get(cid)
        return None

    def find_concepts(
        self,
        *,
        pillar: Optional[str] = None,
        category: Optional[str] = None,
        text_query: Optional[str] = None,
    ) -> List[Concept]:
        """Filter concepts by pillar, category, or substring match on label."""
        candidates: Optional[Set[str]] = None
        if pillar:
            candidates = set(self._pillar_index.get(pillar, set()))
        if category:
            cat_set = set(self._category_index.get(category, set()))
            candidates = cat_set if candidates is None else candidates & cat_set
        if candidates is None:
            candidates = set(self._concepts.keys())
        results = [self._concepts[cid] for cid in candidates if cid in self._concepts]
        if text_query:
            tq = text_query.lower()
            results = [c for c in results if tq in c.label.lower() or any(tq in a.lower() for a in c.aliases)]
        return sorted(results, key=lambda c: c.label)

    def concepts_by_pillar(self) -> Dict[str, List[Concept]]:
        """Return concepts grouped by pillar."""
        out: Dict[str, List[Concept]] = defaultdict(list)
        for c in self._concepts.values():
            out[c.pillar].append(c)
        for k in out:
            out[k].sort(key=lambda c: c.label)
        return dict(out)

    # ---- Relations ----

    def add_relation(self, relation: Relation, *, allow_self: bool = False) -> None:
        """Add a relation, validating that both concepts exist."""
        if not allow_self and relation.source_id == relation.target_id:
            return
        key = (relation.source_id, relation.target_id, relation.relation_type)
        for existing in self._relations:
            if (existing.source_id, existing.target_id, existing.relation_type) == key:
                existing.strength = max(existing.strength, relation.strength)
                existing.evidence = list(set(existing.evidence + relation.evidence))
                return
        self._relations.append(relation)

    def relations_for(self, concept_id: str) -> List[Relation]:
        """Get all relations where concept_id is source or target."""
        return [
            r for r in self._relations
            if r.source_id == concept_id or r.target_id == concept_id
        ]

    def outgoing_relations(self, concept_id: str) -> List[Relation]:
        return [r for r in self._relations if r.source_id == concept_id]

    def incoming_relations(self, concept_id: str) -> List[Relation]:
        return [r for r in self._relations if r.target_id == concept_id]

    def related_concepts(self, concept_id: str) -> List[Concept]:
        """Get all concepts related (source or target) to concept_id."""
        ids: Set[str] = set()
        for r in self.relations_for(concept_id):
            other = r.target_id if r.source_id == concept_id else r.source_id
            ids.add(other)
        return [self._concepts[cid] for cid in ids if cid in self._concepts]

    # ---- Resource Links ----

    def add_resource_link(self, link: ResourceLink) -> None:
        self._resource_links.append(link)

    def resource_links_for(self, concept_id: str) -> List[ResourceLink]:
        return [rl for rl in self._resource_links if rl.concept_id == concept_id]

    # ---- Graph export / import ----

    def to_dict(self) -> Dict[str, Any]:
        """Serialise to a JSON-compatible dict."""
        return {
            "concepts": [c.model_dump() for c in self._concepts.values()],
            "relations": [r.model_dump() for r in self._relations],
            "resource_links": [rl.model_dump() for rl in self._resource_links],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OntologyManager":
        """Load from a serialised dict."""
        mgr = cls()
        for c_data in data.get("concepts", []):
            mgr.add_concept(Concept(**c_data))
        for r_data in data.get("relations", []):
            mgr.add_relation(Relation(**r_data))
        for rl_data in data.get("resource_links", []):
            mgr.add_resource_link(ResourceLink(**rl_data))
        return mgr

    def save(self, path: Path | str) -> None:
        Path(path).write_text(json.dumps(self.to_dict(), indent=2, default=str), encoding="utf-8")

    @classmethod
    def load(cls, path: Path | str) -> "OntologyManager":
        p = Path(path)
        if not p.exists():
            return cls()
        return cls.from_dict(json.loads(p.read_text(encoding="utf-8")))

    # ---- Integration with existing knowledge graph ----

    def to_cytograph_nodes(self) -> List[Dict[str, Any]]:
        """Export concepts as Cytoscape-compatible node dicts."""
        nodes = []
        for c in self._concepts.values():
            nodes.append({
                "data": {
                    "id": f"ont:{c.id}",
                    "label": c.label,
                    "type": "concept",
                    "domain": c.pillar,
                    "category": c.category,
                    "size": 30 + int(c.confidence_score * 20),
                }
            })
        return nodes

    def to_cytograph_edges(self) -> List[Dict[str, Any]]:
        """Export relations as Cytoscape-compatible edge dicts."""
        edges = []
        for i, r in enumerate(self._relations):
            edges.append({
                "data": {
                    "id": f"ont-rel:{i}",
                    "source": f"ont:{r.source_id}",
                    "target": f"ont:{r.target_id}",
                    "relation": r.relation_type,
                    "strength": r.strength,
                }
            })
        return edges

    def merge_into_cytograph(self, cytograph: Dict[str, Any]) -> Dict[str, Any]:
        """Merge ontology nodes/edges into an existing Cytoscape graph dict."""
        existing_ids = {
            n["data"]["id"] for n in cytograph.get("nodes", [])
        }
        for node in self.to_cytograph_nodes():
            if node["data"]["id"] not in existing_ids:
                cytograph.setdefault("nodes", []).append(node)
        existing_edges = {
            e["data"]["id"] for e in cytograph.get("edges", [])
        }
        for edge in self.to_cytograph_edges():
            if edge["data"]["id"] not in existing_edges:
                cytograph.setdefault("edges", []).append(edge)
        return cytograph

    # ---- Seeding from canonical data ----

    def seed_pillar(self, pillar: str) -> int:
        """Seed the ontology with canonical concepts for a pillar. Returns count added."""
        seeds = PILLAR_CONCEPT_SEEDS.get(pillar, [])
        added = 0
        for seed in seeds:
            if pillar not in self._pillar_index or seed["id"] not in self._concepts:
                self.add_concept(Concept(pillar=pillar, **seed))
                added += 1
        return added

    def seed_all_pillars(self) -> int:
        """Seed all pillars. Returns total concepts added."""
        total = 0
        for pillar in PILLAR_CONCEPT_SEEDS:
            total += self.seed_pillar(pillar)
        return total

    def seed_relations(self) -> int:
        """Seed canonical relations. Returns count added."""
        added = 0
        for src, tgt, rtype, pillar in PILLAR_RELATION_SEEDS:
            if src in self._concepts and tgt in self._concepts:
                self.add_relation(Relation(
                    source_id=src, target_id=tgt, relation_type=rtype, pillar=pillar,
                ))
                added += 1
        for src, tgt, rtype in CROSS_PILLAR_SEEDS:
            if src in self._concepts and tgt in self._concepts:
                self.add_relation(Relation(
                    source_id=src, target_id=tgt, relation_type=rtype, pillar="cross-pillar",
                ))
                added += 1
        return added

    # ---- Utility ----

    def concept_count(self) -> int:
        return len(self._concepts)

    def relation_count(self) -> int:
        return len(self._relations)

    def resource_link_count(self) -> int:
        return len(self._resource_links)

    def pillar_summary(self) -> Dict[str, Dict[str, int]]:
        """Return per-pillar counts of concepts and relations."""
        summary: Dict[str, Dict[str, int]] = {}
        for pillar in PILLAR_KEYS:
            c_count = len(self._pillar_index.get(pillar, set()))
            r_count = sum(1 for r in self._relations if r.pillar == pillar)
            summary[pillar] = {"concepts": c_count, "relations": r_count}
        return summary


# ---------------------------------------------------------------------------
# Text-based concept extraction (lightweight keyword matcher)
# ---------------------------------------------------------------------------

def extract_concepts_from_text(
    text: str,
    manager: OntologyManager,
    *,
    min_confidence: float = 0.5,
) -> List[Tuple[Concept, float]]:
    """Match text against known concepts (label + aliases). Returns (concept, confidence)."""
    if not text:
        return []
    text_lower = text.lower()
    seen: Dict[str, float] = {}
    for concept in manager._concepts.values():
        # Check label
        label = concept.label.lower()
        if label in text_lower:
            score = concept.confidence_score
            if score >= min_confidence and concept.id not in seen:
                seen[concept.id] = score
                continue
        # Check aliases
        for alias in concept.aliases:
            alias_lower = alias.lower()
            if alias_lower in text_lower and alias_lower != label:
                score = concept.confidence_score * 0.9
                if score >= min_confidence and concept.id not in seen:
                    seen[concept.id] = score
                    break
    return [(manager._concepts[cid], score) for cid, score in
            sorted(seen.items(), key=lambda x: -x[1])]
