# Knowledge Repository Design — MathWorld-Inspired Architecture

> **Status: Design Proposal**
> **Implemented:** A–Z browse (`/letters/` via `templates/alpha_index.j2` + `scripts/generate_alpha_index.py`), "See Also" and "Explore With" partials (`see_also.j2`, `explore_tools.j2`), freshness badges (`freshness_badge.j2`).
> **Not yet implemented:** Contributor attribution footer, standardized citation format, hierarchical subject-classification tags, per-entry contributor credit in registry.
> **Last reviewed:** 2026-07-30

## 1. Design Philosophy

MathWorld succeeds because it is:
- **Authoritative** — single stewards, cited references, rigorous editing
- **Encyclopedic** — one entry per concept, densely cross-linked
- **Navigable** — topic hierarchy, A-Z index, search, and "see also" chains
- **Fresh** — every entry has a last-updated timestamp
- **Pedagogical** — Classroom layer sits on top of the encyclopedia
- **Computable** — Wolfram|Alpha integration makes every entry interactive

AcaciaFund already exceeds MathWorld in some dimensions (cognitive architecture, spaced repetition, dual coding, Bloom taxonomy), but can adopt MathWorld's proven patterns to become a genuinely canonical knowledge repo for Compliance, Markets, and Data Engineering.

## 2. Synthesis: MathWorld Patterns × AcaciaFund Cognitive Architecture

| MathWorld Feature | AcaciaFund Equivalent | Gap | Priority |
|---|---|---|---|
| Topic hierarchy (11 topics) | 3 pillars + 14 subcategories each | Equivalent | - |
| Alphabetical index (`/letters/A`) | **Missing** | Add A-Z browse across all entries | P1 |
| Entry: definition + properties + examples | Varied per template | Standardize entry anatomy | P1 |
| "See also" cross-references | `related_research` / `related_learn` | Add dedicated "See also" section | P1 |
| Contributor attribution | **Missing** | Add to entry metadata + footer | P2 |
| "Last Updated: date" | `date_str` but not prominent | Highlight freshness on every entry | P1 |
| Subject classifications | Concept badges (partial) | Add hierarchical classification tags | P2 |
| Classroom (prerequisites + examples) | Learn modules + ontology! | Already strong, minor enhancements | P3 |
| Wolfram|Alpha "Explore with" | **Missing** | Add "Explore with notebook/tool" | P2 |
| References (books, papers) | `external_references` | Already strong, add citation format | P2 |
| SVG diagrams per entry | Visual abstracts + concept maps | Already strong | - |
| "What's New" / recent changes | Weekly refresh CI | Enhance freshness page | P3 |
| "See also" with direct concept links | No explicit editorial "See also" | New curated cross-linking section | P1 |

## 3. New Entry Anatomy (Standardized Across All Content Types)

```
┌──────────────────────────────────────────────────────────────┐
│ [Breadcrumb]  Pillar > Subcategory > Topic                  │
│ [Pillar Badge] [Content Type Badge] [Difficulty Badge]      │
│ [Epistemic Badge] [Normative Badge]                         │
│                                                              │
│ # Entry Title                                                │
│ Last Updated: 2026-07-25 · 12 min read · v2.3.1             │
│ By: Eric Weisstein, Todd Rowland (MathWorld-style credit)   │
│                                                              │
│ ┌──────────────────────────────────────────────────────────┐ │
│ │ Visual Abstract (SVG icon + 3-bullet summary)            │ │
│ └──────────────────────────────────────────────────────────┘ │
│                                                              │
│ ## Definition (expanded, canonical)                          │
│ Prose body of the entry.                                     │
│                                                              │
│ ## Key Properties                                            │
│ Bulleted list of defining characteristics.                   │
│                                                              │
│ ## Formal Statement (if applicable)                          │
│ Mathematical/regulatory/algorithmic formalization.           │
│                                                              │
│ ## Examples                                                  │
│ Worked examples with code, data, or case studies.            │
│                                                              │
│ ## Visual Explanation                                        │
│ [Concept Map] [Timeline] [Flow Diagram] [Comparison]        │
│                                                              │
│ ## Prerequisites                                             │
│ [Concept A] → [Concept B] → THIS CONCEPT → [Concept C]      │
│ (From ontology + schema builder)                             │
│                                                              │
│ ## Bloom Taxonomy Questions                                  │
│ [Remember] [Understand] [Apply] [Analyze] [Evaluate] [Create]│
│                                                              │
│ ## Feynman Concept Cards                                     │
│ [ELI5] [Analogy] [Example] [Gap Check] [Teach Back]         │
│                                                              │
│ ## See Also (curated editorial links, like MathWorld)         │
│ • [Related Concept A] — brief description                    │
│ • [Related Concept B] — brief description                    │
│ • [Advanced Topic X] — brief description                     │
│                                                              │
│ ## Explore With                                              │
│ • Python notebook: [link]                                     │
│ • SQL query: [link]                                           │
│ • Regulatory database: [link]                                 │
│                                                              │
│ ## Source Synthesis                                          │
│ [arXiv paper] [HN discussion] [PubMed article]               │
│                                                              │
│ ## References                                                │
│ 1. Author. *Title*. Publisher, Year. (canonical citation)    │
│ 2. Author. *Title*. Publisher, Year.                         │
│ 3. Regulatory text, §X.Y.Z                                   │
│                                                              │
│ ## Subject Classifications                                   │
│ • Compliance > AML > KYC > Beneficial Ownership             │
│ • Markets > Trading Strategies > Algorithmic Trading        │
│ • Data Engineering > Pipeline Architecture > Streaming      │
│ • Tags: [ontology concepts as badges]                        │
│                                                              │
│ ## Philosophical Foundations                                 │
│ [Epistemic Status] [Lineage] [Cross-Pillar Analog]           │
│                                                              │
│ ## Cite This Entry As                                        │
│ "Beneficial Ownership." *AcaciaFund Knowledge Repository*.   │
│ https://www.acaciafund.org/compliance/knowledge/beneficial-ownership. │
│                                                              │
│ [Related Research] [Related Lessons] [Related Knowledge]     │
│ [Previous] ← Concept A  |  Concept Z → [Next]               │
└──────────────────────────────────────────────────────────────┘
```

## 4. New Feature Specifications

### 4.1 Alphabetical Index (A-Z Browser)

**File**: `scripts/generate_alpha_index.py`

```
Generates:
  /letters/A/index.html  → All entries starting with 'A'
  /letters/B/index.html  → All entries starting with 'B'
  ...
  /letters/index.html    → Letter grid with entry counts per letter
```

**Data flow**: Reads `registry.json` + `data/ontology.json`, groups all titles by first letter. Each entry shows: title, pillar badge, content type, description (1-line), date.

**Integration**: Called during build in `build.py` after content generation. Adds links to `search-index.json`.

**Template**: `templates/alpha_index.j2`
- Letter grid at top (A–Z with counts)
- Entries listed alphabetically under each letter
- Each entry: [pillar badge] [content type] Title — Description
- Sticky letter nav for jumping

### 4.2 "See Also" Section

**Model**: Add `see_also` field to registry items / content metadata:
```python
see_also: list[dict] = [
    {"slug": "aml/knowledge/beneficial-ownership", "label": "Beneficial Ownership", "reason": "Core prerequisite"},
    {"slug": "data-engineering/knowledge/graph-databases", "label": "Graph Databases", "reason": "Implementation technology"},
]
```

**Generation**: Can be auto-suggested from ontology (shared concepts) or manually curated. Auto-generation from `related_concepts()` in ontology — concepts that co-occur on the same entry. Manual curation via registry.

**Template**: New partial `templates/partials/see_also.j2` rendered in `knowledge.j2`, `learn.j2`, `blog_post.j2`.

### 4.3 Contributor Attribution

**Model**: Add `contributors` field to registry items:
```python
contributors: list[dict] = [
    {"name": "Eric Weisstein", "role": "Author", "url": "/about/"},
    {"name": "Todd Rowland", "role": "Contributor", "url": "/about/todd-rowland"},
]
```

**Template**: Footer section on every entry showing:
- "Authored by [Name] · Contributions by [Name], [Name]"
- Links to contributor pages

**Admin**: Add contributor management to admin ontology page.

### 4.4 Freshness Indicators

Every entry gets at minimum:
- **Last Updated**: `YYYY-MM-DD` (from `date_str` or git log)
- **Last Verified**: from `source_health.json` or separate freshness sweep
- **Freshness Badge**: 🟢 Fresh (<30d) / 🟡 Stale (30-90d) / 🔴 Outdated (>90d) / ⚪ Never verified

**Implementation**:
```python
def compute_freshness(last_verified: date) -> str:
    days = (date.today() - last_verified).days
    if days < 30: return "fresh"
    if days < 90: return "stale"
    return "outdated"
```

**Script**: `scripts/check_entry_freshness.py` — walks registry, checks each item's freshness, writes `dist/freshness.json`.

### 4.5 "Explore With" Computational Integration

Analogous to MathWorld's Wolfram|Alpha integration. For each entry, provide:
- **Python notebook** (Jupyter nbviewer link or inline)
- **SQL query** for the data-engineering pillar
- **Regulatory database search** for the compliance pillar
- **Market data API call** for the markets pillar

**Model**: `explore_tools: list[dict] = [...]` per entry in registry.

**Template**: Partial `templates/partials/explore_tools.j2` — rendered as a grid of tool cards.

### 4.6 Standardized Citation Format

Every entry ends with:

```
Cite this as:
"Entry Title." AcaciaFund Knowledge Repository.
https://www.acaciafund.org/{pillar}/{type}/{slug}.
Accessed 2026-07-26.
```

**Template**: `templates/partials/citation.j2`.

### 4.7 Subject Classifications (Hierarchical Tags)

Currently AcaciaFund has concept badges + tags. Enhance with hierarchical subject classification analogous to MathWorld's "Subject classifications":

```
Compliance > AML > CDD > Beneficial Ownership
Data Engineering > Data Architecture > Modeling > Graph Databases
```

**Model**: Add `subject_classifications: list[list[str]]` to registry — each element is a path from pillar to leaf.

**Visual**: Breadcrumb-style pills showing the hierarchy path.

**Auto-generation**: Can derive from `pillar` + `PILLAR_SUBCATEGORIES` + ontology categories.

## 5. Template Implementation Plan

### 5.1 New Templates

| Template | Purpose | Dependencies |
|---|---|---|
| `alpha_index.j2` | A-Z browser page | `registry.json`, letter grouping |
| `partials/see_also.j2` | Curated cross-reference list | `content.see_also` |
| `partials/citation.j2` | Standard citation footer | `content.title`, slug |
| `partials/explore_tools.j2` | Computational tool links | `content.explore_tools` |
| `partials/contributor.j2` | Author/contributor attribution | `content.contributors` |
| `partials/freshness_badge.j2` | Entry freshness indicator | `content.last_verified` |

### 5.2 Template Modifications

| Template | Change |
|---|---|
| `knowledge.j2` | Add see_also, citation, contributors, freshness, explore_tools sections |
| `learn.j2` | Add see_also, citation, contributors, freshness |
| `blog_post.j2` | Add see_also, citation, contributors, freshness |
| `layout.j2` | Add alpha index link to nav |
| `pillar_index.j2` | Add "Browse A-Z" link |

## 6. Build Pipeline Changes

```
scripts/knowledge_ingester.py  →  registry.json  →  build.py  →  dist/
                                                          |
                                              core/build_taxonomies.py
                                              scripts/generate_alpha_index.py  ← NEW
                                              scripts/check_entry_freshness.py ← NEW
```

### 6.1 `build.py` Integration Points

```python
# In build.py, after content rendering:
from scripts.generate_alpha_index import generate_alpha_index
generate_alpha_index(all_content, output_dir, render_template)

from scripts.check_entry_freshness import check_entry_freshness
check_entry_freshness(all_content, output_dir)
```

## 7. Registry Schema Enhancements

Add to `RegistryData` in `schemas.py`:

```python
class RegistryData(BaseModel):
    # ... existing fields ...
    
    # MathWorld-inspired additions
    see_also: list[SeeAlsoRef] = Field(default_factory=list)
    contributors: list[Contributor] = Field(default_factory=list)
    explore_tools: list[ExploreTool] = Field(default_factory=list)
    subject_classifications: list[list[str]] = Field(default_factory=list)
    last_verified: str | None = None
    citation_style: str | None = None
    
class SeeAlsoRef(BaseModel):
    slug: str
    label: str
    reason: str | None = None
    
class Contributor(BaseModel):
    name: str
    role: str = "Author"
    url: str | None = None
    
class ExploreTool(BaseModel):
    label: str
    url: str
    tool_type: str = "notebook"  # "notebook" | "sql" | "api" | "regulatory" | "market"
```

## 8. Implementation Timeline

| Phase | Deliverables | Depends On |
|---|---|---|
| **Phase A** | Alpha index generator + template, freshness badge, citation partial | Registry schema update |
| **Phase B** | See also section, contributor attribution, explore tools | Phase A |
| **Phase C** | Subject classifications enhancement, admin UI for new fields | Phase B |
| **Phase D** | Auto-generation of see_also from ontology co-occurrence | Phase C |

## 9. Architecture Diagram

```
┌────────────────────────────────────────────────────────────────┐
│                     AcaciaFund Knowledge Repository            │
├────────────────────────────────────────────────────────────────┤
│                                                               │
│  ENCYCLOPEDIC LAYER (MathWorld-inspired)                      │
│  ┌────────────┐ ┌──────────────┐ ┌──────────────────────┐   │
│  │ Alpha Index│ │ Entry Pages  │ │ Subject Classifica-  │   │
│  │ (A-Z)      │ │ (standard-   │ │ tions (hierarchical  │   │
│  │            │ │ ized anatomy)│ │ tags + badges)       │   │
│  └────────────┘ └──────────────┘ └──────────────────────┘   │
│                                                               │
│  PEDAGOGICAL LAYER (Cognitive Architecture)                   │
│  ┌────────────┐ ┌──────────────┐ ┌──────────────────────┐   │
│  │ Learn      │ │ Flashcards   │ │ Spaced Repetition    │   │
│  │ Modules    │ │ (SM-2)       │ │ (Retention Engine)   │   │
│  └────────────┘ └──────────────┘ └──────────────────────┘   │
│  ┌────────────┐ ┌──────────────┐ ┌──────────────────────┐   │
│  │ Bloom      │ │ Feynman      │ │ Progressive          │   │
│  │ Questions  │ │ Synthesis    │ │ Disclosure           │   │
│  └────────────┘ └──────────────┘ └──────────────────────┘   │
│                                                               │
│  ONTOLOGY LAYER (Concept Graph)                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 192 Concepts · 10 Relation Types · Philosophical     │   │
│  │ Metadata · Cross-Pillar Analogs · Schema Builder     │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
│  FOUNDATION LAYER (Build System)                             │
│  ┌────────────┐ ┌──────────────┐ ┌──────────────────────┐   │
│  │ registry   │ │ build.py     │ │ Jinja2 Templates     │   │
│  │ .json      │ │ (Python)     │ │ (layout.j2 + 40+)    │   │
│  └────────────┘ └──────────────┘ └──────────────────────┘   │
│  ┌────────────┐ ┌──────────────┐ ┌──────────────────────┐   │
│  │ Core/      │ │ Scripts/     │ │ Cloudflare Pages     │   │
│  │ (ontology, │ │ (alpha index,│ │ (deploy target)      │   │
│  │ urls, etc) │ │ freshness)   │ │                      │   │
│  └────────────┘ └──────────────┘ └──────────────────────┘   │
│                                                               │
└────────────────────────────────────────────────────────────────┘
```

## 10. Key Design Decisions

### 10.1 Alpha Index vs Full-Text Search
Both. Alpha index is for **browsing** (MathWorld-style discovery). Search is for **finding**. They serve different cognitive modes — exploration vs retrieval.

### 10.2 Manual vs Auto-Generated "See Also"
Start with auto-generated (from ontology shared concepts), then layer manual curation on top. The `see_also` field supports both — auto-populate at build time with override capability.

### 10.3 Freshness as Trust Signal
In a domain where regulations change (Compliance), markets shift (Markets), and tools evolve (Data Engineering), freshness is a **trust signal**. Every entry must show when it was last verified, not just when it was published.

### 10.4 Citation as Authority Marker
MathWorld entries are citable academic references. AcaciaFund should achieve the same authority by providing canonical citations, DOI-style URLs, and contributor attribution.

### 10.5 Computational Exploration
MathWorld's most powerful feature is that every entry connects to Wolfram|Alpha. AcaciaFund should offer equivalent computational exploration: Python notebooks for data pipelines, regulatory database queries for compliance, market data API calls for markets.

## 11. Success Metrics

| Metric | Current | Target |
|---|---|---|
| Entry pages with standard anatomy | ~260 (varied) | All 420+ standardized |
| A-Z browser available | No | Yes |
| Entries with freshness badges | 0% | 100% |
| Entries with "See also" | Auto-generated only | Auto + curated |
| Entries with citation footer | 0% | 100% |
| Entries with contributor attribution | 0% | 100% |
| Entries with explore tools | 0% | 100% |
| Subject classifications per entry | Implicit (tags) | Explicit (hierarchy) |

## 12. Generated vs Cached Design

| Component | Generated at Build | Cached/Persistent |
|---|---|---|
| Alpha index pages | From registry.json | static HTML in dist/ |
| Freshness badges | From freshness.json | data/entry_freshness.json |
| See also (auto) | From ontology co-occurrence | Registry-merged at build |
| Explore tools links | From registry field | registry.json |
| Citation footers | From entry metadata | Template-rendered |
| Contributor attribution | From registry field | registry.json |
