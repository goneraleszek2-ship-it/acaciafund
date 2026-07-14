# Telemetry & Plausible Analytics

AcaciaFund uses **Plausible** for privacy-preserving analytics. Events are sent client-side from `search.js` and the build logs build metrics for observability.

## Plausible Configuration

```python
# config.py
PLAUSIBLE_DOMAIN = "plausible.io"  # Plausible server endpoint
```

Events are only sent when `PLAUSIBLE_DOMAIN` is configured (it's non-empty). The build checks:

```python
if PLAUSIBLE_DOMAIN:
    # Plausible script is included in layout.j2
    # Search events are sent from search.js
```

## Search Events

### `search` Event

Fired when a user performs a search:

```javascript
plausible('search', {
    props: {
        query: searchTerm,       // The search query text
        results: resultCount,    // Number of results found
        filters: activeFilters   // Active facet filters as JSON
    }
});
```

### `search_result_click` Event

Fired when a user clicks a search result:

```javascript
plausible('search_result_click', {
    props: {
        query: searchTerm,       // The search query
        slug: result.slug,       // Clicked result slug
        position: resultIndex    // Position in results (0-based)
    }
});
```

## Build Telemetry

The build records metrics in `dist/build-meta.json`:

```json
{
    "build_time_s": 26.9,
    "pages_total": 810,
    "registry_items": 280,
    "skipped_items": 0,
    "sqi_avg": 0.823,
    "sqi_below_threshold": [],
    "generated_at": "2026-07-13T12:00:00+00:00",
    "url_structure_version": "3.0"
}
```

## Admin Telemetry Page

The telemetry admin page (`admin/telemetry.html`) displays:
- Build metrics (time, pages, SQI)
- Plausible event counts (if available)
- Search query analytics
- Error counts from `build_errors.log`
- Trend charts (if historical data available)

> **See also:** [Admin Dashboard](admin-dashboard.md), [Client-Side Search](../05-search-discovery/client-side-search.md)
