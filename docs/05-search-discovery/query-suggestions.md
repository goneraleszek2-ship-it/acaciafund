# Query Suggestions (Planned)

Query suggestions provide autocomplete functionality for the search bar using localStorage to track user search history.

## Design

```
┌─────────────────────────────────────┐
│ Search articles, topics...          │
│ ─────────────────────────────────── │
│ 🔍 suspicious transaction report    │ ← History
│ 🔍 KYC fundamentals                 │
│ 🔍 data pipeline architecture       │
│ ─────────────────────────────────── │
│ (results below)                     │
└─────────────────────────────────────┘
```

## Storage

- Top 10 recent queries stored in `localStorage` key `recent_searches`
- Queries are deduplicated (case-insensitive)
- Most recent query appears first
- Max 10 entries (oldest evicted on overflow)

## Implementation Plan

```javascript
// In search.js
function saveQuery(query) {
    let recent = JSON.parse(localStorage.getItem('recent_searches') || '[]');
    recent = recent.filter(q => q.toLowerCase() !== query.toLowerCase());
    recent.unshift(query);
    recent = recent.slice(0, 10);
    localStorage.setItem('recent_searches', JSON.stringify(recent));
}

function showSuggestions(input) {
    let recent = JSON.parse(localStorage.getItem('recent_searches') || '[]');
    let filtered = recent.filter(q =>
        q.toLowerCase().includes(input.value.toLowerCase())
    );
    // Render dropdown
}
```

## Future Enhancements

- **Trending queries** — Aggregate top queries from Plausible analytics
- **Concept suggestions** — Show matching ontology concepts as suggestions
- **Clear history** — Button to clear localStorage recent searches

> **See also:** [Client-Side Search](client-side-search.md), [Admin Telemetry Export](../06-admin-observability/telemetry-export.md)
