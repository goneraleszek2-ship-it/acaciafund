"""Learning paths — structured journeys from prerequisite DAG with content linking."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import networkx as nx

from core.ontology import OntologyManager
from core.schema_builder import (
    LearningPath,
    build_prerequisite_graph,
    categorize_by_bloom,
    compute_learning_paths,
)


@dataclass
class PathNode:
    concept_id: str
    label: str
    pillar: str
    bloom_level: str
    content: dict = field(default_factory=dict)


@dataclass
class LearningJourney:
    start_concept_id: str
    start_label: str
    start_pillar: str
    paths: list[LearningPath]
    nodes: list[PathNode]


def build_all_learning_paths(
    manager: OntologyManager,
    max_depth: int = 3,
) -> dict[str, LearningJourney]:
    """Build journeys for every concept with outgoing 'requires' edges."""
    graph = build_prerequisite_graph(manager)
    journeys = {}

    for node_id in graph.nodes():
        if not list(graph.successors(node_id)):
            continue
        paths = compute_learning_paths(graph, node_id, max_depth)
        if not paths:
            continue
        start_node = graph.nodes[node_id]
        nodes = _build_path_nodes(graph, paths)
        journeys[node_id] = LearningJourney(
            start_concept_id=node_id,
            start_label=start_node.get("label", node_id),
            start_pillar=start_node.get("pillar", ""),
            paths=paths,
            nodes=nodes,
        )

    return journeys


def _build_path_nodes(
    graph: nx.DiGraph,
    paths: list[LearningPath],
) -> list[PathNode]:
    seen = set()
    nodes = []
    for path in paths:
        for concept in path.concepts:
            cid = concept["id"]
            if cid in seen:
                continue
            seen.add(cid)
            bloom = categorize_by_bloom(cid, graph)
            nodes.append(PathNode(
                concept_id=cid,
                label=concept["label"],
                pillar=concept.get("pillar", ""),
                bloom_level=bloom,
            ))
    return nodes


def enrich_journeys_with_content(
    journeys: dict[str, LearningJourney],
    concept_content_map: dict[str, list[dict]],
) -> dict[str, LearningJourney]:
    """Link content to each path node using pre-built concept→content map."""
    for journey in journeys.values():
        for node in journey.nodes:
            items = concept_content_map.get(node.concept_id, [])
            by_type: dict[str, list] = {"research": [], "learn": [], "knowledge": []}
            for item in items:
                ctype = item.get("content_type", "research")
                by_type[ctype].append(item)
            node.content = {k: v[:4] for k, v in by_type.items()}
    return journeys


def generate_learning_path_context(
    journey: LearningJourney,
    pillar_config: dict,
) -> dict[str, Any]:
    """Build template context for learning_path.j2."""
    pc = pillar_config.get(journey.start_pillar, pillar_config.get("aml", {}))

    enriched_nodes = []
    for node in journey.nodes:
        enriched_nodes.append({
            "concept_id": node.concept_id,
            "label": node.label,
            "pillar": node.pillar,
            "bloom_level": node.bloom_level,
            "research": node.content.get("research", []),
            "learn": node.content.get("learn", []),
            "knowledge": node.content.get("knowledge", []),
            "total_content": sum(len(v) for v in node.content.values()),
        })

    path_viz = []
    for path in journey.paths:
        path_viz.append({
            "concepts": path.concepts,
            "depth": path.total_depth,
            "pillar_span": path.pillar_span,
            "start": path.start,
            "end": path.end,
            "concept_ids": [c["id"] for c in path.concepts],
        })

    return {
        "journey_label": journey.start_label,
        "start_concept_id": journey.start_concept_id,
        "start_pillar": journey.start_pillar,
        "pillar_color": pc.get("color", "#6366f1"),
        "pillar_label": pc.get("label", journey.start_pillar),
        "nodes": enriched_nodes,
        "paths": path_viz,
        "path_count": len(path_viz),
        "total_nodes": len(enriched_nodes),
        "pillar_span": max((p.pillar_span for p in journey.paths), default=1),
    }


def generate_cross_pillar_synthesis(
    all_content: list,
    concept_content_map: dict[str, list[dict]],
    pillar_config: dict,
) -> dict[str, Any]:
    """Build cross-pillar data: concept bridges, timeline, content counts."""
    by_pillar: dict[str, list] = {}
    for item in all_content:
        p = item.pillar or "aml"
        by_pillar.setdefault(p, []).append(item)

    concept_pillars: dict[str, set] = {}
    for cid, items in concept_content_map.items():
        for item in items:
            p = item.get("pillar", "aml")
            concept_pillars.setdefault(cid, set()).add(p)

    bridges = {}
    for cid, pillars in concept_pillars.items():
        if len(pillars) >= 2:
            bridges[cid] = {
                "concept_id": cid,
                "pillars": sorted(pillars),
                "span": len(pillars),
                "total_content": len(concept_content_map.get(cid, [])),
            }

    timeline = {}
    for item in all_content:
        ds = item.date_str
        if ds and len(ds) >= 7:
            month = ds[:7]
            if month not in timeline:
                timeline[month] = {"aml": 0, "stock": 0, "data-engineering": 0}
            p = item.pillar or "aml"
            if p in timeline[month]:
                timeline[month][p] += 1

    return {
        "bridges": dict(sorted(bridges.items(), key=lambda x: -x[1]["total_content"])),
        "timeline": dict(sorted(timeline.items())),
        "pillar_counts": {p: len(items) for p, items in by_pillar.items()},
        "total_bridges": len(bridges),
    }