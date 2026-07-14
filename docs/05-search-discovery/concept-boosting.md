# Concept Boosting

Ontology concepts provide a significant ranking boost in search results.

## How It Works

1. During build, each content item is scanned with `extract_concepts_from_text()`
2. Matching concept IDs are stored in the search index under `concept_boost`
3. When a user's search query matches a concept name/alias, items with that concept in their `concept_boost` array receive a +6 score boost
4. Items without matching concepts are ranked lower

## Score Impact

| Field | Base Weight | With Concept Match |
|-------|-------------|-------------------|
| Title | +10 | +10 (concept boost is additive) |
| Ontology concepts | +6 | +6 (already includes ontology match) |
| Tags | +4 | +4 |
| Description | +2 | +2 |

The concept boost doesn't replace the base weights — it's an additional boost applied at query time in `search.js`.

## Implementation in search.js

```javascript
// During Fuse.js search, when a result is found:
if (result.item.concept_boost) {
    const conceptMatch = result.item.concept_boost.some(c =>
        query.toLowerCase().includes(c.replace(/-/g, ' '))
    );
    if (conceptMatch) {
        result.score -= 0.06; // Equivalent to +6 in scoring
    }
}
```

## Benefits

- **Recall improvement:** Items with matching ontology concepts rank higher even if the concept name doesn't appear in the title
- **Cross-pillar discovery:** A search for "KYC" boosts items tagged with `kyc` concept across all pillars
- **Niche concept support:** Rare or specialized concepts receive appropriate ranking

## Tuning

If concept boosting is too aggressive (over-ranking edge-match items), adjust the boost magnitude in `search.js`:

```javascript
const CONCEPT_BOOST = 0.06; // Lower = less boost
```

If too weak, increase the value.

> **See also:** [Concept Extraction](../04-ontology-knowledge-graph/concept-extraction.md), [Client-Side Search](client-side-search.md)
