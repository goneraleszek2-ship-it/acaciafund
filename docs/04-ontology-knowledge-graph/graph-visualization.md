# Graph Visualization

The knowledge graph is rendered using **Cytoscape.js** at `/graph/`, providing an interactive visualization of content nodes, ontology concepts, and their relationships.

## Template

`templates/graph.j2` renders the graph view with:

1. **Toolbar** — Pillar filter, relation-type filter, layout selector, inline search, reset button
2. **Main canvas** — Cytoscape.js interactive graph
3. **Node detail panel** — Shows selected node info on click

## Layout Options

| Layout | Description | Algorithm |
|--------|-------------|-----------|
| Force-directed | Default. Pulls connected nodes together, pushes unconnected apart | `cose-bilkent` |
| Hierarchical | Tree-like layout showing parent-child structure | `dagre` |
| Concentric | Circular layout by centrality | `concentric` |
| Breadth-first | Level-based layout from root nodes | `breadthfirst` |

## Filters

### Pillar Filter

Dropdown to show/hide nodes by pillar:
- All (default)
- Compliance
- Markets
- Data Engineering
- Cross-pillar

### Relation-Type Filter

Dropdown to filter edges by relation type:
- All (default)
- `part_of`
- `enables`
- `mitigates`
- `requires`
- `competes_with`
- `cross-reference`
- 10 edge types total

## Node Detail Panel

When a node is clicked, a side panel shows:
- **Title** (node label)
- **Pillar badge** (pillar-specific color)
- **Content type** (research / learn / knowledge)
- **SQI badge** (if available)
- **Tags** (if available)
- **Connected nodes** — List of linked nodes with relation labels
- **Link** to the actual content page

## Inline Search

The toolbar includes a search input that:
- Filters nodes by label/title in real-time
- Highlights matching nodes
- Dims non-matching nodes

## Reset Button

Restores all filters to defaults:
- Pillar: All
- Relation type: All
- Layout: Force-directed
- Search: Cleared

## Color Coding

| Node Type | Color |
|-----------|-------|
| Ontology concept | Teal |
| Compliance content | Amber |
| Markets content | Green |
| Data Engineering content | Blue |

## Performance

The graph is rendered client-side using Cytoscape.js. For optimal performance:
- Pre-computed layout data in `graph-data.json`
- Lazy-rendered detail panel (only on click)
- Debounced search (200ms)

> **See also:** [Cytoscape Export](cytograph-export.md), [Ontology Model](ontology-model.md)
