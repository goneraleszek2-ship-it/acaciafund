# AcaciaFund UI/UX Design Specification

**Version:** 1.0
**Status:** Adopted (adaptation decisions below)
**Methodology:** Atomic Design (Frost, 2016)
**Pedagogical Model:** Bloom + Feynman + SM-2
**Device Target:** Mobile-first, responsive continuum (320px → 2560px)

---

## 1. Design Principles

Derived from the platform audit and competitive analysis:

1. **Systems, Not Pages:** Every UI element must be a reusable component. We design the ingredient, not the meal.
2. **Trust Through Transparency:** Provenance badges, sentence-level citations, and SQI scores are visible by default. A learner must know why they should believe what they read.
3. **Progress Over Perfection:** The UI celebrates incremental learning. Streaks, mastery rings, and SM-2 queues make partial completion feel valuable.
4. **Context-Agnostic Naming:** Components are named by structure (`card`, `badge`, `timeline`) not by content (`aml-card`, `market-badge`).
5. **Cognitive Load Budget:** The Feynman stack (ELI5 → Analogy → Detail) maps directly to progressive disclosure in the UI. Never show everything at once.

## 2. Visual Language

### 2.1 Color System (Atoms)

| Token | Hex | Usage |
|---|---|---|
| `--compliance` | `#4F46E5` (Indigo 600) | Compliance pillar, badges, graph nodes |
| `--markets` | `#059669` (Emerald 600) | Markets pillar, badges, graph nodes |
| `--data` | `#D97706` (Amber 600) | Data Engineering pillar, badges, graph nodes |
| `--neutral-900` | `#111827` | Primary text, headings |
| `--neutral-600` | `#4B5563` | Secondary text, captions |
| `--neutral-200` | `#E5E7EB` | Borders, dividers |
| `--neutral-50` | `#F9FAFB` | Page backgrounds |
| `--surface` | `#FFFFFF` | Card backgrounds |
| `--accent` | `#0EA5E9` (Sky 500) | Interactive elements, links, study queue |

**Bloom Level Colors** (Accessibility-compliant):
- Beginner: `--emerald-500` (#10B981)
- Intermediate: `--amber-500` (#F59E0B)
- Advanced: `--rose-500` (#F43F5E)

### 2.2 Typography (Atoms)

| Role | Font | Size | Weight | Line Height |
|---|---|---|---|---|
| Display | Inter | 48px/3rem | 800 | 1.1 |
| H1 | Inter | 32px/2rem | 700 | 1.2 |
| H2 | Inter | 24px/1.5rem | 600 | 1.3 |
| H3 | Inter | 20px/1.25rem | 600 | 1.4 |
| Body | Merriweather | 18px/1.125rem | 400 | 1.7 |
| Caption | Inter | 14px/0.875rem | 500 | 1.5 |
| Mono | JetBrains Mono | 14px | 400 | 1.6 (code) |

Rationale: Merriweather for long-form reading (financial text is dense), Inter for UI chrome. JetBrains Mono for code exercises.

### 2.3 Spacing Scale (Atoms)

Base unit: `4px`. Scale: 4, 8, 12, 16, 24, 32, 48, 64, 96.

## 3. Component Library (Atomic Design Hierarchy)

### 3.1 Atoms

**Bloom Badge**
- Pill shape with icon + text: "Beginner", "Intermediate", "Advanced"
- Color-coded background at 10% opacity, solid text
- Size: height 24px, padding 8px 12px

**Provenance Badge**
- Small dot + label: "Synthesized" (hollow), "Curated" (half-filled), "Verified" (solid)
- Positioned adjacent to article title, never standalone

**Pillar Indicator**
- Vertical 4px bar on left edge of cards + icon in metadata
- Color maps to pillar token

**Progress Ring (SVG Atom)**
- 24px diameter, 3px stroke
- Background track: `--neutral-200`
- Fill: pillar color
- Used in cards and nav

**Concept Pill**
- Rounded rectangle, `--neutral-100` background, `--neutral-700` text
- Hover state: `--accent` background, white text
- Click navigates to concept hub

### 3.2 Molecules

**Article Card**

```
┌─────────────────────────────┐
│ [Pillar Bar]                │
│ [Bloom Badge] [Provenance]  │
│ Title (H3)                  │
│ Excerpt (2 lines)           │
│ [Concept Pill] [Concept]    │
│ [Progress Ring] 60%         │
└─────────────────────────────┘
```

- Shadow: `0 1px 3px rgba(0,0,0,0.1)` on hover
- Transition: `transform 0.2s ease, box-shadow 0.2s ease`

**Study Queue Item**

```
┌─────────────────────────────┐
│ [Concept Pill] Due: Today   │
│ Q: What is CDD?         [?] │
│ [Show Answer]               │
└─────────────────────────────┘
```

- Flip animation on "Show Answer" (CSS 3D transform)
- Rating buttons: Again (1) | Hard (2) | Good (3) | Easy (4) — color-coded

**Citation Block**

```
┌─────────────────────────────┐
│ [Quote Icon]                │
│ "Exact sentence from source"│
│ — Author (Year) [DOI] [Bib] │
└─────────────────────────────┘
```

- Left border: 3px `--accent`
- Background: `--sky-50`

**Search Bar**
- Expandable input with `/` keyboard shortcut
- Results dropdown grouped by content type (Learn / Research / Knowledge)
- Icon + title + pillar color indicator per result

### 3.3 Organisms

**Global Header**

```
┌─────────────────────────────────────────────┐
│ [Logo]  [Compliance] [Markets] [Data]  [🔔] [Search] [≡] │
└─────────────────────────────────────────────┘
```

- Study Queue Bell (🔔): Shows count of due SM-2 cards. Red dot if >0.
- Pillar Nav: Active state has underline matching pillar color.
- Mobile: Collapses to bottom tab bar (see Responsive section).

**Hero Section (Homepage)**

```
┌─────────────────────────────────────────────┐
│                                             │
│   Invest in understanding,                  │
│   to build resilience.                      │
│                                             │
│   [Diagnostic Quiz]  [Browse Paths]         │
│                                             │
│   [Three Pillar Cards]                      │
│                                             │
└─────────────────────────────────────────────┘
```

- Pillar cards use the Article Card molecule but oversized.
- Each card has a subtle gradient background using its pillar color at 5% opacity.

**Learning Path Timeline**

```
┌─────────────────────────────────────────────┐
│ ○─────●─────○─────○─────○                   │
│ KYC   CDD   EDD   SAR   RBA                 │
│       ↑ You are here                        │
└─────────────────────────────────────────────┘
```

- Horizontal on desktop, vertical on mobile
- Completed nodes: solid pillar color
- Current node: pulsing ring animation
- Locked nodes: `--neutral-300`
- Clicking a node opens a tooltip with title + estimated time

**Feynman Content Organism**
A structured article body with progressive disclosure:
1. ELI5 Banner: Full-width, `--amber-50` background, large friendly text. "Explain it to me like I'm 5."
2. Analogy Box: `--emerald-50` background, metaphorical explanation.
3. Detail Sections: Standard body text with H2/H3 hierarchy.
4. Self-Test Accordion: Collapsible quiz questions. Expands inline.
5. Build Something Real: `--sky-50` background, hands-on exercise or code sandbox call-to-action.

**Concept Graph (D3.js Organism)**
- Canvas-based force-directed graph
- Nodes: Concepts (colored by pillar), size by article count
- Edges: Prerequisite (solid) or Related (dashed)
- You Are Here: Pulsing node with ring
- Hover: Tooltip with concept name + 1-sentence definition
- Click: Navigate to concept hub
- Zoom/Pan: Enabled on desktop, simplified on mobile

**Knowledge Sidebar (Article Template)**

```
┌─────────────┐
│ On this page│
│ • ELI5      │
│ • Analogy   │
│ • Details   │
│ • Self-Test │
│             │
│ Prerequisites│
│ [Concept] → │
│             │
│ Related     │
│ [Concept]   │
│ [Concept]   │
└─────────────┘
```

- Sticky positioning, scrolls with content
- Table of contents highlights active section (IntersectionObserver)

## 4. Page Templates

### 4.1 Homepage Template

Layout: Single column, max-width 1200px, centered.

Sections (top to bottom):
1. Header Organism (global)
2. Hero Organism
3. How It Works: 3-step visual (Pick Topic → Learn Simply → Test Yourself) using icon molecules
4. Featured Paths: 3 Career Track cards (horizontal scroll on mobile)
5. Recent Research: 4 Article Cards in 2×2 grid
6. Knowledge Graph Teaser: Static SVG visualization of the ontology with CTA "Explore the Map"
7. Footer Organism

Mobile Adaptation: Bottom tab bar replaces header nav. Hero text scales to 32px. Featured paths become horizontal swipe carousel.

### 4.2 Pillar Landing Template

Layout: Two-column (66/33) on desktop, single column on mobile.

Left Column:
1. Pillar hero with color-themed background
2. Pillar description + icon
3. Diagnostic CTA: "Not sure where to start? Take the 2-minute quiz."
4. Learning Paths: Vertical stack of Path Timeline organisms
5. Latest Content: Article Card grid

Right Column (Sticky):
1. Mastery Dashboard: Progress rings for each track in this pillar
2. Study Queue Mini: Next 3 due cards with "Go to Study" button
3. Popular Concepts: Top 10 concept pills for this pillar

Critical Fix: This template must validate that `pillar.slug` exists in `config.py` before generation. This resolves the `/data-engineering/` 404.

### 4.3 Article / Learn Template

Layout: Two-column (60/40) on desktop. Content left, sidebar right.

Content Area:
1. Breadcrumb Molecule: Home > Pillar > Path > Article
2. Header: Title + Bloom Badge + Provenance Badge + reading time
3. Prerequisite Alert: If user hasn't completed prerequisites, show banner: "We recommend reading [Concept] first." (Dismissible)
4. Feynman Content Organism (full article body)
5. Cross-Pillar Resonance: "This concept also appears in: [Markets] [Data]" with article links
6. SM-2 CTA: "Add to Study Queue" button at bottom
7. Related Articles: 3 Article Cards

Sidebar:
1. Knowledge Sidebar Organism
2. Concept Navigator: Mini graph of this article's concepts

Mobile: Sidebar becomes collapsible bottom sheet or accordion below content.

### 4.4 Research Article Template

Layout: Single column, max-width 800px (optimized for reading).

Header:
- Title + Source badge (arXiv, SEC, HN, etc.)
- SQI Score visualization (small bar chart: Authority/Freshness/Consensus/Relevance)
- Authors, Year, DOI link

Body:
1. Executive Summary: 3-bullet TL;DR
2. Synthesis: Structured prose with inline Citation Block molecules
3. Key Data Table: Structured extraction (Sample, Method, Finding, Limitation)
4. Context: How this fits into the broader ontology
5. BibTeX / RIS Export: Buttons at bottom

### 4.5 Concept Hub Template

Layout: Full-width hero + two-column below.

Hero:
- Concept name (H1) + ELI5 definition
- Pillar color background (subtle)
- Graph Mini: Static SVG showing this node + immediate neighbors

Below:
- Left (70%): Tabbed interface
  - Overview (long-form explanation)
  - Articles (filtered by content type)
  - Prerequisites (visual path)
  - Advanced (deeper resources)
- Right (30%):
  - Mastery status (if in study queue)
  - Related concepts
  - "Start Learning" CTA (links to first prerequisite lesson)

### 4.6 Study Dashboard Template (`/study/`)

Layout: App-like, full-width.

Header:
- Today's due count
- Streak counter (flame icon)
- Settings (SM-2 algorithm preferences)

Main Area:
- Study Card Molecule (full screen on mobile, centered card on desktop)
- Card flips front/back for Q&A
- Rating bar at bottom: [Again] [Hard] [Good] [Easy]

Sidebar (Desktop):
- Upcoming queue (next 5 cards)
- Weekly progress chart (simple CSS bar chart)
- Weak concepts (cards with low ease factors)

## 5. User Flows

### 5.1 First-Time User Flow

```
Homepage → Diagnostic Quiz → Pillar Placement →
Recommended Path → First Lesson (ELI5 section) →
"Add to Study Queue" prompt → Study Dashboard
```

- Onboarding: 3-slide overlay explaining Bloom badges, SM-2, and the ontology.
- Goal: Get user to their first SM-2 review within 24 hours.

### 5.2 Returning User Flow

```
Homepage (or direct /study/) → Study Queue (if cards due) →
Review → Return to path OR Explore concept graph
```

- Smart Redirect: If user has due cards, homepage shows banner: "You have 12 cards ready for review."

### 5.3 Research-Discovery Flow

```
Search/Tag → Research Article → Citation Block →
Source Paper (external) OR Related Concept Hub →
Learn Article (deeper dive)
```

- Goal: Bridge casual research to structured learning.

## 6. Responsive Behavior

**Breakpoints**
- Mobile: < 768px
- Tablet: 768px – 1024px
- Desktop: > 1024px

**Mobile-Specific Patterns**

**Bottom Tab Bar (Navigation Molecule)**

```
┌─────────────────────────────┐
│ [Home] [Paths] [Study] [Me] │
└─────────────────────────────┘
```

- Study tab shows badge count
- Replaces desktop header nav entirely

**Card Carousels**
- Horizontal swipe for learning paths and related articles
- Snap scrolling with CSS `scroll-snap-type`

**Concept Graph (Simplified)**
- Radial layout instead of force-directed
- Single-tap to navigate, pinch to zoom
- "Explore Full Map" links to desktop view

**Article Reading**
- Sidebar becomes floating "Contents" button (bottom-right)
- Tap opens modal drawer with ToC + prerequisites

## 7. Accessibility (WCAG 2.1 AA)

1. **Color:** Never rely on color alone. Bloom badges use icon + text. Graph nodes use shape + color.
2. **Motion:** Respect `prefers-reduced-motion`. Disable graph physics and card flip animations if enabled.
3. **Focus:** All interactive elements have visible `:focus` rings (2px `--accent` outline).
4. **Contrast:** All text meets 4.5:1 ratio. Body text is `--neutral-900` on `--surface` (15:1).
5. **ARIA:**
   - Study cards: `role="dialog"` when active
   - Graph: `role="application"` with keyboard navigation (arrow keys)
   - Badges: `aria-label="Beginner level, Remember and Understand"`

## 8. Implementation Priority

Following the agent execution plan, implement templates in this order:

| Phase | Template | Key Organisms |
|---|---|---|
| 1 | Pillar Landing | Header, Article Card, Progress Ring |
| 2 | Article / Learn | Feynman Content, Knowledge Sidebar, Citation Block |
| 3 | Study Dashboard | Study Card, Progress Chart |
| 4 | Concept Hub | Concept Graph, Tab Interface |
| 5 | Research Article | SQI Viz, Data Table, BibTeX Export |
| 6 | Homepage | Hero, Path Timeline, Graph Teaser |

## 9. Atomic Design Compliance Checklist

Before any component is merged, verify:
- **Atom:** Is this the smallest possible unit? Can it be reused in at least 3 contexts?
- **Molecule:** Does this combine atoms without assuming page context?
- **Organism:** Is this a distinct section that could appear on multiple templates?
- **Template:** Does this define structure without final content?
- **Page:** Does this render with real representative content (not just lorem ipsum)?

Example: The "Study Queue Bell" is an Atom (icon + badge). It appears in the Header Organism (all templates), the Study Dashboard Template, and the Pillar Landing Template (sidebar mini-queue).

## 10. Success Metrics (Design KPIs)

| Metric | Measurement Method |
|---|---|
| Time to first SM-2 review | Analytics event on "Add to Study Queue" |
| Concept graph interactions | D3.js event logging (node clicks, zoom) |
| Feynman section engagement | Scroll depth tracking per section (ELI5 vs Detail) |
| Mobile completion rate | % of mobile users who finish a Learn article |
| Citation click-through | % of users who click DOI/BibTeX on Research pages |

---

## Adaptation Notes (adopted 2026-08-06)

The spec was adopted as the canonical design reference with these adaptations to the live platform:

1. **Palette & fonts: adapted, not adopted.** Current pillar accents (aml=amber `#d97706`, stock=green `#22c55e`, data=indigo `#818cf8`, accent `#4f46e5`) and type system (Fraunces + Manrope + JetBrains Mono) stay; spec semantics map onto existing tokens via CSS aliases in `static/css/design-system.css` (`--pillar-*`, `--bloom-*`). No `config.py` color changes.
2. **Concept Graph: Cytoscape retained.** `graph.j2` (199 nodes) stays; lightweight per-page concept maps use static SVG/HTML partials instead of a D3.js migration.
3. **KPIs:** Plausible analytics is installed (`PLAUSIBLE_DOMAIN`, `layout.j2`); event wiring is incremental, not part of the adoption commit.
4. **Implementation order:** Phases 1–3 (Pillar Landing, Article/Learn, Study Dashboard) shipped in the adoption cycle; Phases 4–6 (Concept Hub, Research, Homepage) follow per the priority table.
