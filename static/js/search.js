(function() {
  'use strict';

  const PILLAR_URL_MAP = { aml: 'compliance', stock: 'markets', 'data-engineering': 'data' };
  const PILLAR_LABELS = { aml: 'Compliance', stock: 'Markets', 'data-engineering': 'Data' };
  const PILLAR_COLORS = { aml: '#f59e0b', stock: '#16a34a', 'data-engineering': '#6366f1' };
  const CT_LABELS = { research: 'Research', learn: 'Learn', knowledge: 'Knowledge' };
  const DIFF_LABELS = { beginner: 'Beginner', intermediate: 'Intermediate', advanced: 'Advanced' };
  const PAGE_SIZE = 20;

  function slugToUrl(slug) {
    const parts = slug.split('/');
    const pillar = PILLAR_URL_MAP[parts[0]] || parts[0];
    if (parts.length === 1) return '/' + parts[0] + '/';
    return '/' + [pillar].concat(parts.slice(1)).join('/') + '/';
  }

  function escapeHtml(s) {
    const d = document.createElement('div');
    d.textContent = s;
    return d.innerHTML;
  }

  function highlightTerms(text, terms) {
    if (!terms.length) return escapeHtml(text);
    let safe = escapeHtml(text);
    for (const t of terms) {
      const re = new RegExp('(' + t.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + ')', 'gi');
      safe = safe.replace(re, '<mark>$1</mark>');
    }
    return safe;
  }

  function tokenize(q) {
    return q.toLowerCase().split(/\s+/).filter(Boolean);
  }

  function scoreEntry(entry, terms) {
    const title = (entry.title || '').toLowerCase();
    const desc = (entry.description || '').toLowerCase();
    const tags = (entry.tags || []).join(' ').toLowerCase();
    const concepts = (entry.ontology_concepts || []).join(' ').toLowerCase();
    const technologies = (entry.technologies || []).join(' ').toLowerCase();
    const use_cases = (entry.use_cases || []).join(' ').toLowerCase();
    let score = 0;

    for (const t of terms) {
      if (title.includes(t)) score += 10;
      if (tags.includes(t)) score += 4;
      if (concepts.includes(t)) score += 6;
      if (technologies.includes(t)) score += 3;
      if (use_cases.includes(t)) score += 2;
      if (desc.includes(t)) score += 2;
    }

    score += (entry.concept_boost || 0) * 5;

    const sqi = entry.avg_sqi || 0;
    if (sqi >= 0.8) score += 0.5;
    else if (sqi >= 0.65) score += 0.25;

    if (entry.difficulty) score += 0.5;

    return score;
  }

  function matchesFilters(entry, filters) {
    if (filters.pillar.length && !filters.pillar.includes(entry.pillar || '')) return false;
    if (filters.type.length && !filters.type.includes(entry.content_type || '')) return false;
    if (filters.difficulty.length && !filters.difficulty.includes(entry.difficulty || '')) return false;
    return true;
  }

  function readFilters() {
    const filters = { pillar: [], type: [], difficulty: [] };
    document.querySelectorAll('.filter-checkbox:checked').forEach(cb => {
      const group = cb.getAttribute('data-group');
      if (group && filters.hasOwnProperty(group)) filters[group].push(cb.value);
    });
    return filters;
  }

  function syncFiltersToUrl(filters) {
    const url = new URL(window.location);
    for (const key of ['pillar', 'type', 'difficulty']) {
      if (filters[key].length) url.searchParams.set('f_' + key, filters[key].join(','));
      else url.searchParams.delete('f_' + key);
    }
    history.replaceState(null, '', url);
  }

  const STORAGE_KEY = 'ac_search_history';
  const MAX_SUGGESTIONS = 10;

  function getHistory() {
    try { return JSON.parse(localStorage.getItem(STORAGE_KEY)) || []; } catch { return []; }
  }

  function saveQuery(q) {
    const trimmed = q.trim().toLowerCase();
    if (!trimmed) return;
    let history = getHistory().filter(h => h !== trimmed);
    history.unshift(trimmed);
    if (history.length > MAX_SUGGESTIONS) history = history.slice(0, MAX_SUGGESTIONS);
    try { localStorage.setItem(STORAGE_KEY, JSON.stringify(history)); } catch {}
  }

  function renderSuggestions(filter) {
    const el = document.getElementById('search-suggestions');
    if (!el) return;
    const history = getHistory();
    const matching = filter ? history.filter(h => h.includes(filter.toLowerCase())) : history;
    if (!matching.length) { el.innerHTML = ''; el.style.display = 'none'; return; }
    el.innerHTML = matching.map((h, i) =>
      '<div class="suggestion-item" data-suggestion="' + escapeHtml(h) + '" data-idx="' + i + '" style="padding:0.5rem 0.75rem;cursor:pointer;font-size:0.9rem;border-bottom:1px solid var(--color-border, #333)">' +
      highlightTerms(escapeHtml(h), filter ? filter.split(/\s+/) : []) +
      '</div>'
    ).join('');
    el.style.display = 'block';
  }

  function firePlausible(event, props) {
    if (typeof plausible === 'function') {
      try { plausible(event, { props: props || {} }); } catch {}
    }
  }

  let searchIndex = null;
  let allScored = [];
  let displayedCount = 0;
  let currentTerms = [];
  let selectedIndex = -1;

  function fetchIndex() {
    if (searchIndex) return Promise.resolve(searchIndex);
    const base = document.querySelector('script[src*="search.js"], script[src*="app.js"]');
    const prefix = base ? base.src.replace(/js\/\w+\.js.*$/, '') : '';

    // If a single pillar is pre-filtered, load just that chunk
    const filters = readFilters();
    let url = prefix + 'static/search-index.json';
    if (filters.pillar.length === 1) {
      url = prefix + 'static/search-index.' + filters.pillar[0] + '.json';
    }

    return fetch(url)
      .then(r => { if (!r.ok) throw new Error(r.status); return r.json(); })
      .then(data => { searchIndex = data; return data; });
  }

  function renderResult(entry, terms, idx) {
    const url = slugToUrl(entry.slug);
    const pillar = entry.pillar || '';
    const color = PILLAR_COLORS[pillar] || '#888';
    const pLabel = PILLAR_LABELS[pillar] || pillar;
    const ct = entry.content_type || '';
    const ctLabel = CT_LABELS[ct] || ct;
    const difficulty = entry.difficulty || '';
    const diffLabel = DIFF_LABELS[difficulty] || '';
    const concepts = entry.ontology_concepts || [];
    const sqi = entry.avg_sqi || 0;
    const isSelected = idx === selectedIndex;

    let html = '<a href="' + url + '" class="search-result" data-idx="' + idx + '" data-slug="' + escapeHtml(entry.slug) + '" data-pillar="' + escapeHtml(pillar) + '" style="display:block;padding:1rem;margin-bottom:0.5rem;border:1px solid ' + (isSelected ? 'var(--color-accent, #818cf8)' : 'var(--color-border, #333)') + ';border-left:3px solid ' + color + ';border-radius:8px;text-decoration:none;color:var(--color-text, #e8e6e3);transition:border-color 0.2s' + (isSelected ? ';background:color-mix(in srgb, var(--color-accent, #818cf8) 8%, transparent)' : '') + '">';
    html += '<div style="display:flex;gap:0.5rem;align-items:center;margin-bottom:0.25rem;flex-wrap:wrap">';
    html += '<span style="display:inline-block;padding:2px 8px;border-radius:9999px;font-size:0.7rem;font-weight:600;color:#fff;background:' + color + '">' + escapeHtml(pLabel) + '</span>';
    if (ctLabel) html += '<span style="font-size:0.7rem;color:var(--color-text-muted, #888)">' + escapeHtml(ctLabel) + '</span>';
    if (diffLabel) html += '<span style="font-size:0.7rem;color:var(--color-text-muted, #888)">' + escapeHtml(diffLabel) + '</span>';
    if (entry.date_str) html += '<span style="font-size:0.7rem;color:var(--color-text-muted, #888)">' + escapeHtml(entry.date_str) + '</span>';
    if (sqi > 0) {
      const sqiColor = sqi >= 0.8 ? '#22c55e' : sqi >= 0.65 ? '#d97706' : '#ef4444';
      html += '<span style="font-size:0.65rem;padding:1px 6px;border-radius:9999px;background:color-mix(in srgb, ' + sqiColor + ' 15%, transparent);color:' + sqiColor + ';font-family:monospace">' + sqi.toFixed(2) + '</span>';
    }
    html += '</div>';
    html += '<div style="font-weight:600;margin-bottom:0.25rem">' + highlightTerms(entry.title || '', terms) + '</div>';
    if (entry.description) {
      html += '<div style="font-size:0.85rem;color:var(--color-text-secondary, #aaa);display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden">' + highlightTerms(entry.description, terms) + '</div>';
    }
    if (concepts.length) {
      html += '<div style="display:flex;gap:0.25rem;flex-wrap:wrap;margin-top:0.35rem">';
      for (const c of concepts.slice(0, 5)) {
        html += '<span style="font-size:0.65rem;padding:1px 6px;border-radius:9999px;background:color-mix(in srgb, var(--color-accent, #818cf8) 12%, transparent);color:var(--color-accent, #818cf8);border:1px solid color-mix(in srgb, var(--color-accent, #818cf8) 25%, transparent)">' + escapeHtml(c) + '</span>';
      }
      if (concepts.length > 5) html += '<span style="font-size:0.65rem;color:var(--color-text-muted, #888)">+' + (concepts.length - 5) + '</span>';
      html += '</div>';
    }
    if (entry.technologies && entry.technologies.length) {
      html += '<div style="display:flex;gap:0.25rem;flex-wrap:wrap;margin-top:0.3rem">';
      for (const tech of entry.technologies.slice(0, 4)) {
        html += '<span style="font-size:0.65rem;padding:1px 6px;border-radius:4px;background:color-mix(in srgb, #22c55e 12%, transparent);color:#22c55e;border:1px solid color-mix(in srgb, #22c55e 25%, transparent)">&#9881; ' + escapeHtml(tech) + '</span>';
      }
      if (entry.technologies.length > 4) html += '<span style="font-size:0.65rem;color:var(--color-text-muted, #888)">+' + (entry.technologies.length - 4) + '</span>';
      html += '</div>';
    }
    if (entry.use_cases && entry.use_cases.length) {
      html += '<div style="display:flex;gap:0.25rem;flex-wrap:wrap;margin-top:0.25rem">';
      for (const uc of entry.use_cases.slice(0, 3)) {
        html += '<span style="font-size:0.6rem;padding:1px 5px;border-radius:9999px;background:color-mix(in srgb, var(--color-accent, #818cf8) 10%, transparent);color:var(--color-text-muted, #bbb)">' + escapeHtml(uc.replace(/-/g, ' ')) + '</span>';
      }
      if (entry.use_cases.length > 3) html += '<span style="font-size:0.6rem;color:var(--color-text-muted, #888)">+' + (entry.use_cases.length - 3) + '</span>';
      html += '</div>';
    }
    if (entry.tags && entry.tags.length) {
      html += '<div style="display:flex;gap:0.25rem;flex-wrap:wrap;margin-top:0.35rem">';
      for (const tag of entry.tags.slice(0, 4)) {
        html += '<kbd style="font-size:0.65rem">' + escapeHtml(tag) + '</kbd>';
      }
      html += '</div>';
    }
    html += '</a>';
    return html;
  }

  function renderPage() {
    const container = document.getElementById('search-results');
    if (!container) return;
    const batch = allScored.slice(0, displayedCount);
    container.innerHTML = batch.map((x, i) => renderResult(x.entry, currentTerms, i)).join('');
    const existing = document.getElementById('search-show-more');
    if (existing) existing.remove();
    if (displayedCount < allScored.length) {
      const btn = document.createElement('button');
      btn.id = 'search-show-more';
      btn.textContent = 'Show more (' + (allScored.length - displayedCount) + ' remaining)';
      btn.style.cssText = 'display:block;width:100%;padding:0.75rem;margin-top:0.5rem;background:var(--color-bg, #1a1a2e);border:1px solid var(--color-border, #333);border-radius:8px;color:var(--color-accent, #818cf8);cursor:pointer;font-size:0.85rem';
      btn.addEventListener('click', function() {
        displayedCount += PAGE_SIZE;
        renderPage();
      });
      container.appendChild(btn);
    }
  }

  function runSearch(query, tagFilter) {
    const container = document.getElementById('search-results');
    const statsEl = document.getElementById('search-stats');
    if (!container) return;

    if (!query.trim() && !tagFilter) {
      container.innerHTML = '<p style="color:var(--color-text-muted, #888);text-align:center;margin-top:2rem">Type to search across all content...</p>';
      if (statsEl) statsEl.textContent = '';
      return;
    }

    const terms = query.trim() ? tokenize(query) : [];

    fetchIndex().then(index => {
      const filters = readFilters();
      allScored = index
        .filter(function(e) {
          if (!matchesFilters(e, filters)) return false;
          if (tagFilter) {
            var concepts = e.ontology_concepts || [];
            var tags = e.tags || [];
            var matchesTag = concepts.some(function(c) { return c.toLowerCase() === tagFilter.toLowerCase(); })
              || tags.some(function(t) { return t.toLowerCase() === tagFilter.toLowerCase(); });
            if (!matchesTag) return false;
          }
          return true;
        })
        .map(function(e) {
          return { entry: e, score: terms.length ? scoreEntry(e, terms) : 1 };
        })
        .filter(function(x) { return x.score > 0; })
        .sort(function(a, b) { return b.score - a.score; });
      currentTerms = terms;
      displayedCount = PAGE_SIZE;
      selectedIndex = -1;

      if (statsEl) {
        statsEl.textContent = allScored.length
          ? allScored.length + ' result' + (allScored.length !== 1 ? 's' : '')
          : 'No results';
      }

      if (query.trim()) {
        saveQuery(query);
        firePlausible('search', { query: query, results: allScored.length, terms: terms.length });
      }

      if (!allScored.length) {
        var msg = tagFilter ? 'No results tagged "' + escapeHtml(tagFilter) + '"' : 'No results for "' + escapeHtml(query) + '"';
        container.innerHTML = '<div style="text-align:center;margin-top:2rem"><p style="color:var(--color-text-muted, #888)">' + msg + '</p><p style="font-size:0.8rem;color:var(--color-text-muted, #888);margin-top:0.5rem">Try different keywords or browse by pillar:</p><div style="display:flex;gap:0.5rem;justify-content:center;margin-top:0.75rem"><a href="/compliance/" class="inline-block px-3 py-1.5 text-xs font-semibold rounded-lg" style="background:var(--color-surface,#f0f0f0);color:var(--color-text,#333)">Compliance</a><a href="/markets/" class="inline-block px-3 py-1.5 text-xs font-semibold rounded-lg" style="background:var(--color-surface,#f0f0f0);color:var(--color-text,#333)">Markets</a><a href="/data/" class="inline-block px-3 py-1.5 text-xs font-semibold rounded-lg" style="background:var(--color-surface,#f0f0f0);color:var(--color-text,#333)">Data</a></div></div>';
        return;
      }

      renderPage();
    }).catch(function(err) {
      container.innerHTML = '<p style="color:#ef4444;text-align:center;margin-top:2rem">Failed to load search index</p>';
    });
  }

  function doSearch() {
    const input = document.getElementById('search-input');
    if (!input) return;
    const params = new URLSearchParams(window.location.search);
    runSearch(input.value, params.get('f_tags') || '');
  }

  document.addEventListener('DOMContentLoaded', function() {
    const input = document.getElementById('search-input');
    if (!input) return;

    // Restore filters from URL
    const params = new URLSearchParams(window.location.search);
    const q = params.get('q') || '';
    const tagFilter = params.get('f_tags') || '';
    document.querySelectorAll('.filter-checkbox').forEach(cb => {
      const group = cb.getAttribute('data-group');
      const urlVal = params.get('f_' + group);
      if (urlVal && urlVal.split(',').includes(cb.value)) cb.checked = true;
    });

    // Show active tag filter badge
    if (tagFilter) {
      var tagBar = document.getElementById('tag-filter-bar') || (function() {
        var el = document.createElement('div');
        el.id = 'tag-filter-bar';
        el.className = 'flex flex-wrap items-center gap-2 mb-4';
        var container = document.getElementById('search-results');
        if (container) container.parentNode.insertBefore(el, container);
        return el;
      })();
      tagBar.innerHTML = '<span class="text-xs font-semibold" style="color:var(--color-text-muted)">Tagged:</span>'
        + '<span class="inline-flex items-center gap-1 text-xs px-2 py-1 rounded-full" style="background:color-mix(in srgb, var(--color-accent) 12%, transparent);color:var(--color-accent)">'
        + tagFilter
        + '<button id="clear-tag-filter" class="ml-1" style="background:none;border:none;cursor:pointer;color:inherit;padding:0;line-height:1" aria-label="Clear tag filter">&times;</button></span>';
      document.getElementById('clear-tag-filter').addEventListener('click', function() {
        var url = new URL(window.location);
        url.searchParams.delete('f_tags');
        history.replaceState(null, '', url);
        tagBar.innerHTML = '';
        runSearch(input.value);
      });
    }

    if (q || tagFilter) {
      input.value = q;
      runSearch(q, tagFilter);
    }

    // Filter checkbox change handler
    document.querySelectorAll('.filter-checkbox').forEach(cb => {
      cb.addEventListener('change', function() {
        const filters = readFilters();
        syncFiltersToUrl(filters);
        // Invalidate search index cache when pillar filters change
        if (cb.getAttribute('data-group') === 'pillar') {
          searchIndex = null;
        }
        doSearch();
      });
    });

    // Reset filters
    const resetBtn = document.getElementById('reset-filters');
    if (resetBtn) {
      resetBtn.addEventListener('click', function() {
        document.querySelectorAll('.filter-checkbox:checked').forEach(cb => cb.checked = false);
        const filters = readFilters();
        syncFiltersToUrl(filters);
        searchIndex = null;
        doSearch();
      });
    }

    let debounce = null;
    input.addEventListener('input', function() {
      clearTimeout(debounce);
      const val = input.value;
      renderSuggestions(val);
      debounce = setTimeout(() => {
        const url = new URL(window.location);
        if (val) url.searchParams.set('q', val);
        else url.searchParams.delete('q');
        history.replaceState(null, '', url);
        runSearch(val);
      }, 200);
    });

    input.addEventListener('focus', function() { renderSuggestions(this.value); });
    input.addEventListener('blur', function() {
      setTimeout(function() {
        const el = document.getElementById('search-suggestions');
        if (el) el.style.display = 'none';
      }, 200);
    });

    // Click delegation for result clicks (Plausible tracking)
    document.getElementById('search-results').addEventListener('click', function(e) {
      const result = e.target.closest('.search-result');
      if (result) {
        const slug = result.getAttribute('data-slug');
        const query = input.value;
        firePlausible('Search Result Click', { query: query, slug: slug });
      }
    });

    // Suggestion click handler
    document.getElementById('search-suggestions').addEventListener('click', function(e) {
      const item = e.target.closest('.suggestion-item');
      if (item) {
        const suggestion = item.getAttribute('data-suggestion');
        if (suggestion) {
          input.value = suggestion;
          this.style.display = 'none';
          const url = new URL(window.location);
          url.searchParams.set('q', suggestion);
          history.replaceState(null, '', url);
          runSearch(suggestion);
        }
      }
    });

    // Keyboard navigation
    document.addEventListener('keydown', function(e) {
      if (e.key === '/' && document.activeElement !== input) {
        e.preventDefault();
        input.focus();
      }
      if (e.key === 'Escape' && document.activeElement === input) {
        input.value = '';
        input.blur();
        selectedIndex = -1;
        runSearch('');
        return;
      }
      if (e.key === 'Escape' && selectedIndex >= 0) {
        selectedIndex = -1;
        renderPage();
        e.preventDefault();
        return;
      }
      if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
        if (!allScored.length) return;
        e.preventDefault();
        const dir = e.key === 'ArrowDown' ? 1 : -1;
        selectedIndex = Math.max(-1, Math.min(displayedCount - 1, selectedIndex + dir));
        renderPage();
        const selectedEl = document.querySelector('.search-result[data-idx="' + selectedIndex + '"]');
        if (selectedEl) selectedEl.scrollIntoView({ block: 'nearest' });
      }
      if (e.key === 'Enter' && selectedIndex >= 0 && selectedIndex < allScored.length) {
        e.preventDefault();
        const entry = allScored[selectedIndex].entry;
        window.location.href = slugToUrl(entry.slug);
      }
    });
  });
})();
