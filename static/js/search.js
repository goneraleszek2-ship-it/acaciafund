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

  function stem(w) {
    w = w.toLowerCase();
    if (w.length > 5) {
      if (w.endsWith('ing')) w = w.slice(0, -3);
      else if (w.endsWith('ingly')) w = w.slice(0, -5);
      else if (w.endsWith('ed')) w = w.slice(0, -2);
      else if (w.endsWith('tion')) w = w.slice(0, -4);
      else if (w.endsWith('s') && !w.endsWith('ss')) w = w.slice(0, -1);
      else if (w.endsWith('ies')) w = w.slice(0, -3) + 'y';
    }
    return w;
  }

  function levenshtein(a, b) {
    if (a === b) return 0;
    if (!a.length) return b.length;
    if (!b.length) return a.length;
    const prev2 = new Array(b.length + 1).fill(0);
    const prev = new Array(b.length + 1).fill(0);
    const cur = new Array(b.length + 1).fill(0);
    for (let j = 0; j <= b.length; j++) prev[j] = j;
    for (let i = 1; i <= a.length; i++) {
      cur[0] = i;
      for (let j = 1; j <= b.length; j++) {
        cur[j] = Math.min(
          prev[j] + 1,
          cur[j - 1] + 1,
          prev[j - 1] + (a[i - 1] === b[j - 1] ? 0 : 1)
        );
        if (i > 1 && j > 1 && a[i - 1] === b[j - 2] && a[i - 2] === b[j - 1]) {
          cur[j] = Math.min(cur[j], prev2[j - 2] + 1);
        }
      }
      for (let j = 0; j <= b.length; j++) {
        prev2[j] = prev[j];
        prev[j] = cur[j];
      }
    }
    return prev[b.length];
  }

  function normalizeToken(w) {
    return String(w).toLowerCase().replace(/[^a-z0-9]+/g, '');
  }

  // Curated domain synonym pairs (both directions, hyphen + space variants handled by the map).
  const SYNONYM_PAIRS = [
    ['aml', 'anti-money-laundering'],
    ['aml', 'amla'],
    ['kyc', 'know-your-customer'],
    ['kyc', 'cdd'],
    ['cdd', 'customer-due-diligence'],
    ['sar', 'suspicious-activity-report'],
    ['str', 'suspicious-transaction-report'],
    ['etf', 'exchange-traded-fund'],
    ['etl', 'extract-transform-load'],
    ['elt', 'extract-load-transform'],
    ['dbt', 'data-build-tool'],
    ['sql', 'structured-query-language'],
    ['boi', 'beneficial-ownership-information'],
  ];

  let synonymMap = null;
  function getSynonymMap() {
    if (synonymMap) return synonymMap;
    const m = {};
    const add = function(key, value) {
      const k = normalizeToken(key);
      if (!k || k.length < 2) return;
      const v = String(value).toLowerCase();
      if (k === normalizeToken(v)) return;
      (m[k] = m[k] || []).push(v);
    };
    SYNONYM_PAIRS.forEach(function(pair) {
      const a = pair[0], b = pair[1];
      add(a, b); add(b, a);
      add(a, b.replace(/-/g, ' ')); add(b.replace(/-/g, ' '), a);
    });
    synonymMap = m;
    return m;
  }

  // Build an alias → concept-label map from review_concepts.json data.
  function buildAliasMap(concepts) {
    const m = {};
    (concepts || []).forEach(function(c) {
      const label = String(c.label || '').toLowerCase();
      const labelKey = normalizeToken(label);
      if (!labelKey) return;
      (c.aliases || []).forEach(function(a) {
        const key = normalizeToken(a);
        if (!key || key === labelKey || key.length < 2) return;
        (m[key] = m[key] || []).push(label);
      });
    });
    return m;
  }

  // Expand a query token into itself + synonyms + concept-label aliases.
  function expandTerm(token, synMap, aliasMap) {
    const out = [token];
    const seen = { [token]: true };
    const push = function(s) {
      if (!s) return;
      const v = String(s).toLowerCase();
      if (seen[v]) return;
      seen[v] = true;
      out.push(v);
    };
    const key = normalizeToken(token);
    ((synMap || {})[key] || []).forEach(push);
    ((aliasMap || {})[key] || []).forEach(push);
    return out;
  }

  // Returns 0 = no match, 1 = fuzzy-only (edit distance), 2 = substring/stem match.
  function matchLevel(term, text) {
    if (!text) return 0;
    if (text.includes(term)) return 2;
    const st = stem(term);
    if (st.length >= 3 && text.includes(st)) return 2;
    // Fuzzy: within 1 edit for terms >= 4 chars, and term length similar to a candidate word
    if (term.length >= 4) {
      const words = text.split(/[^a-z0-9+.-]+/);
      for (const w of words) {
        if (Math.abs(w.length - term.length) > 1) continue;
        if (levenshtein(w, term) <= 1) return 1;
      }
    }
    return 0;
  }

  // Returns true if term matches text via substring, stemming, or fuzzy edit distance.
  function termMatches(term, text) {
    return matchLevel(term, text) > 0;
  }

  /* ── "Did you mean?" spelling correction (pure) ── */

  function buildVocabulary(index, concepts) {
    const set = {};
    const add = function(text) {
      if (!text) return;
      String(text).toLowerCase().split(/[^a-z0-9+.-]+/).forEach(function(w) {
        if (w.length > 3) set[w] = true;
      });
    };
    (index || []).forEach(function(e) {
      add(e.title);
      (e.tags || []).forEach(add);
      (e.ontology_concepts || []).forEach(add);
      (e.technologies || []).forEach(add);
      (e.use_cases || []).forEach(add);
    });
    (concepts || []).forEach(function(c) {
      add(c.label);
      (c.aliases || []).forEach(add);
    });
    return Object.keys(set);
  }

  // Returns the closest vocabulary word within `maxEdits`, or null for an exact match / no candidate.
  function bestCorrection(token, vocab, maxEdits) {
    if (token.length < 3) return null;
    const limit = token.length >= 6 ? (maxEdits || 2) : Math.min(1, maxEdits || 1);
    let best = null;
    let bestDist = Infinity;
    for (let i = 0; i < vocab.length; i++) {
      const w = vocab[i];
      // Skip prefix-extension matches: a valid short term ("aml") must not be
      // "corrected" to a longer vocab word it is merely a prefix of ("amla").
      if (w.startsWith(token) || token.startsWith(w)) continue;
      const dist = levenshtein(w, token);
      if (dist === 0) return null;
      if (dist > limit) continue;
      if (dist < bestDist) { bestDist = dist; best = w; }
    }
    return best;
  }

  // Returns a corrected query string when most tokens have close vocabulary matches, else null.
  function didYouMean(query, vocab, maxEdits) {
    if (!query || !vocab || !vocab.length) return null;
    const tokens = tokenize(query);
    if (!tokens.length) return null;
    const corrected = [];
    let changed = 0;
    for (const t of tokens) {
      const w = bestCorrection(t, vocab, maxEdits);
      if (w) { corrected.push(w); changed++; }
      else corrected.push(t);
    }
    if (!changed) return null;
    if (changed * 2 <= tokens.length) return null;
    const out = corrected.join(' ');
    return out.toLowerCase() === query.toLowerCase() ? null : out;
  }

  function entryFieldText(entry) {
    return {
      title: (entry.title || '').toLowerCase(),
      desc: (entry.description || '').toLowerCase(),
      tags: (entry.tags || []).join(' ').toLowerCase(),
      concepts: (entry.ontology_concepts || []).join(' ').toLowerCase(),
      technologies: (entry.technologies || []).join(' ').toLowerCase(),
      use_cases: (entry.use_cases || []).join(' ').toLowerCase(),
    };
  }

  // Freshness bonus: recent items (by date_str) rank higher, decaying to a floor of +0.5 over a year.
  function dateBoost(dateStr) {
    if (!dateStr) return 0;
    const iso = String(dateStr).slice(0, 10);
    const d = new Date(iso + 'T00:00:00Z');
    if (isNaN(d.getTime())) return 0;
    const days = (Date.now() - d.getTime()) / 86400000;
    if (days < 0) return 0.5;
    return Math.max(0.5, 2 - days / 365);
  }

  // Multi-term AND: every term must match at least one field (via synonyms/aliases too).
  function entryHasAllTerms(entry, terms, synMap, aliasMap) {
    const fields = entryFieldText(entry);
    const fieldVals = Object.keys(fields).map(k => fields[k]);
    for (const t of terms) {
      const expanded = expandTerm(t, synMap, aliasMap);
      const anyMatch = fieldVals.some(function(f) {
        return expanded.some(function(e) { return matchLevel(e, f) > 0; });
      });
      if (!anyMatch) return false;
    }
    return true;
  }

  function scoreEntry(entry, terms, synMap, aliasMap) {
    const fields = entryFieldText(entry);
    const weights = { title: 10, tags: 4, concepts: 6, technologies: 3, use_cases: 2, desc: 2 };
    let score = 0;

    for (let i = 0; i < terms.length; i++) {
      const t = terms[i];
      const expanded = expandTerm(t, synMap, aliasMap);
      let bestLevel = 0;
      let fieldScore = 0;
      for (const key in weights) {
        let level = 0;
        for (let j = 0; j < expanded.length; j++) {
          level = Math.max(level, matchLevel(expanded[j], fields[key]));
        }
        if (!level) continue;
        if (level === 2) fieldScore += weights[key];
        bestLevel = Math.max(bestLevel, level);
      }
      if (bestLevel === 2) {
        score += fieldScore;
        // First-token title bonus: exact match of the leading query term in the title
        if (i === 0 && matchLevel(t, fields.title) === 2) score += 2;
      } else if (bestLevel === 1) {
        // Fuzzy-only matches are capped: typo recovery without fuzzy spam
        score += 2;
      }
    }

    score += (entry.concept_boost || 0) * 5;

    const sqi = entry.avg_sqi || 0;
    if (sqi >= 0.8) score += 0.5;
    else if (sqi >= 0.65) score += 0.25;

    if (entry.difficulty) score += 0.5;

    score += dateBoost(entry.date_str);

    return score;
  }

  // Pure sort for result lists. Modes: relevance (score when querying, SQI+date when
  // browsing), newest (date_str desc, undated last), sqi (avg_sqi desc, date tiebreak).
  function applySort(scored, mode, hasQuery) {
    const list = scored.slice();
    if (mode === 'newest') {
      list.sort(function(a, b) {
        const da = String(a.entry.date_str || '');
        const db = String(b.entry.date_str || '');
        if (da !== db) return db.localeCompare(da);
        return b.score - a.score;
      });
      return list;
    }
    if (mode === 'sqi' || !hasQuery) {
      list.sort(function(a, b) {
        const sa = a.entry.avg_sqi || 0;
        const sb = b.entry.avg_sqi || 0;
        if (sb !== sa) return sb - sa;
        return String(b.entry.date_str || '').localeCompare(String(a.entry.date_str || ''));
      });
      return list;
    }
    list.sort(function(a, b) { return b.score - a.score; });
    return list;
  }

  function readSort() {
    const v = new URLSearchParams(window.location.search).get('sort');
    return (v === 'newest' || v === 'sqi') ? v : 'relevance';
  }

  const FILTER_LABELS = { pillar: 'Pillar', type: 'Type', difficulty: 'Difficulty', bloom: 'Bloom', technology: 'Technology', category: 'Category' };
  const FILTER_VALUE_LABELS = {
    pillar: { aml: 'Compliance', stock: 'Markets', 'data-engineering': 'Data' },
    type: { research: 'Research', learn: 'Learn', knowledge: 'Knowledge' },
    difficulty: { beginner: 'Beginner', intermediate: 'Intermediate', advanced: 'Advanced' },
    bloom: { remember: 'Remember', understand: 'Understand', apply: 'Apply', analyze: 'Analyze', evaluate: 'Evaluate', create: 'Create' },
  };

  function renderFilterChips() {
    const el = document.getElementById('active-filter-chips');
    if (!el) return;
    const filters = readFilters();
    const chips = [];
    for (const group of ['pillar', 'type', 'difficulty', 'bloom', 'category', 'technology']) {
      (filters[group] || []).forEach(function(v) {
        const vLabel = (FILTER_VALUE_LABELS[group] && FILTER_VALUE_LABELS[group][v]) || v;
        chips.push({ group: group, value: v, text: (FILTER_LABELS[group] || group) + ': ' + vLabel });
      });
    }
    if (!chips.length) { el.innerHTML = ''; return; }
    el.innerHTML = chips.map(function(c) {
      return '<button type="button" class="filter-chip" data-group="' + escapeHtml(c.group) + '" data-value="' + escapeHtml(c.value) + '" aria-label="Remove filter ' + escapeHtml(c.text) + '" style="display:inline-flex;align-items:center;gap:0.3rem;font-size:0.75rem;padding:0.2rem 0.55rem;margin:0 0.25rem 0.25rem 0;border-radius:9999px;border:1px solid var(--color-border,#333);background:color-mix(in srgb, var(--color-accent,#818cf8) 10%, transparent);color:var(--color-text,#e8e6e3);cursor:pointer">&times; ' + escapeHtml(c.text) + '</button>';
    }).join('');
  }

  function matchesFilters(entry, filters) {
    if (filters.pillar.length && !filters.pillar.includes(entry.pillar || '')) return false;
    if (filters.type.length && !filters.type.includes(entry.content_type || '')) return false;
    if (filters.difficulty.length && !filters.difficulty.includes(entry.difficulty || '')) return false;
    if (filters.bloom.length && !filters.bloom.includes(entry.bloom || '')) return false;
    if (filters.category.length && !filters.category.includes(entry.category || '')) return false;
    if (filters.technology.length) {
      var techs = entry.technologies || [];
      var hasMatch = filters.technology.some(function(t) { return techs.indexOf(t) !== -1; });
      if (!hasMatch) return false;
    }
    return true;
  }

  function readFilters() {
    const filters = { pillar: [], type: [], difficulty: [], bloom: [], category: [], technology: [] };
    document.querySelectorAll('.filter-checkbox:checked').forEach(cb => {
      const group = cb.getAttribute('data-group');
      if (group && filters.hasOwnProperty(group)) filters[group].push(cb.value);
    });
    return filters;
  }

  function updateFacetCounts(index) {
    const counts = {};
    for (const group of ['pillar', 'type', 'difficulty', 'bloom']) {
      counts[group] = {};
      document.querySelectorAll('.filter-checkbox[data-group="' + group + '"]').forEach(cb => {
        counts[group][cb.value] = 0;
      });
    }
    for (const e of index) {
      const p = e.pillar || '';
      const t = e.content_type || '';
      const d = e.difficulty || '';
      const b = e.bloom || '';
      if (counts.pillar.hasOwnProperty(p)) counts.pillar[p] += 1;
      if (counts.type.hasOwnProperty(t)) counts.type[t] += 1;
      if (counts.difficulty.hasOwnProperty(d)) counts.difficulty[d] += 1;
      if (counts.bloom.hasOwnProperty(b)) counts.bloom[b] += 1;
    }
    document.querySelectorAll('.filter-count').forEach(el => {
      const g = el.getAttribute('data-group');
      const v = el.getAttribute('data-value');
      const n = (counts[g] && counts[g][v]) || 0;
      el.textContent = n ? '(' + n + ')' : '';
    });
  }

  function syncFiltersToUrl(filters) {
    const url = new URL(window.location);
    for (const key of ['pillar', 'type', 'difficulty', 'bloom', 'category', 'technology']) {
      if (filters[key].length) url.searchParams.set('f_' + key, filters[key].join(','));
      else url.searchParams.delete('f_' + key);
    }
    history.replaceState(null, '', url);
  }

  const STORAGE_KEY = 'ac_search_history';
  const MAX_SUGGESTIONS = 10;

  let conceptIndex = null;
  let aliasMap = null;

  function fetchConcepts() {
    if (conceptIndex) return Promise.resolve(conceptIndex);
    return fetch(staticBase() + 'review_concepts.json')
      .then(r => { if (!r.ok) throw new Error(r.status); return r.json(); })
      .then(data => {
        conceptIndex = (data.concepts || []).map(c => ({
          label: c.label || c.conceptSlug || '',
          slug: c.conceptSlug || (c.id || '').replace(/^concept:/, ''),
          aliases: (c.aliases || []).filter(a => typeof a === 'string' && a.length > 1),
          pillar: c.pillar || '',
          category: c.category || ''
        }));
        aliasMap = buildAliasMap(conceptIndex);
        vocabCache = null;
        return conceptIndex;
      })
      .catch(() => { conceptIndex = []; return conceptIndex; });
  }

  function getInterests() {
    try { return JSON.parse(localStorage.getItem('acacia_interests')) || []; } catch { return []; }
  }

  let vocabCache = null;
  function getVocabulary(index) {
    if (!vocabCache) vocabCache = buildVocabulary(index, conceptIndex || []);
    return vocabCache;
  }

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

  function setSuggestionsOpen(el, open) {
    el.style.display = open ? 'block' : 'none';
    const input = document.getElementById('search-input');
    if (input) input.setAttribute('aria-expanded', open ? 'true' : 'false');
  }

  function renderSuggestions(filter) {
    const el = document.getElementById('search-suggestions');
    if (!el) return;
    const needle = (filter || '').toLowerCase().trim();
    const needleTerms = needle ? tokenize(needle) : [];

    const history = getHistory();
    const matchingHistory = needle
      ? history.filter(h => h.toLowerCase().includes(needle))
      : history;

    const concepts = conceptIndex || [];

    let conceptHtml = '';
    if (needle) {
      const matchingConcepts = concepts.filter(c =>
        c.label.toLowerCase().includes(needle) ||
        c.aliases.some(a => a.toLowerCase().includes(needle)) ||
        needleTerms.every(t => c.label.toLowerCase().includes(t)));
      conceptHtml = matchingConcepts.slice(0, 6).map(c =>
        '<a class="suggestion-item" role="option" href="/concepts/' + encodeURIComponent(c.slug) + '/" data-kind="concept" style="display:flex;align-items:center;gap:0.5rem;padding:0.5rem 0.75rem;cursor:pointer;font-size:0.9rem;border-bottom:1px solid var(--color-border, #333);text-decoration:none;color:inherit">' +
        '<span style="font-size:0.75rem;opacity:0.6">&#128214;</span>' +
        '<span style="color:var(--color-accent, #818cf8);font-weight:600">' + highlightTerms(escapeHtml(c.label), needleTerms) + '</span>' +
        '<span style="font-size:0.7rem;opacity:0.6;margin-left:auto">Concept</span>' +
        '</a>'
      ).join('');
    } else {
      // Exploration prompts: prefer the user's interest categories, fall back to top concepts.
      const interests = getInterests();
      const pick = interests.length
        ? concepts.filter(c => interests.some(i => i.pillar === c.pillar && i.category === c.category))
        : concepts;
      const seen = {};
      const chips = [];
      pick.forEach(function(c) {
        if (seen[c.label]) return;
        seen[c.label] = true;
        chips.push(c);
      });
      conceptHtml = chips.slice(0, 5).map(c =>
        '<a class="suggestion-item" role="option" href="/concepts/' + encodeURIComponent(c.slug) + '/" data-kind="concept" style="display:flex;align-items:center;gap:0.5rem;padding:0.5rem 0.75rem;cursor:pointer;font-size:0.9rem;border-bottom:1px solid var(--color-border, #333);text-decoration:none;color:inherit">' +
        '<span style="font-size:0.75rem;opacity:0.6">&#128214;</span>' +
        '<span style="color:var(--color-accent, #818cf8);font-weight:600">' + escapeHtml(c.label) + '</span>' +
        '<span style="font-size:0.7rem;opacity:0.6;margin-left:auto">' + (interests.length ? 'For you' : 'Explore') + '</span>' +
        '</a>'
      ).join('');
    }

    const historyHtml = matchingHistory.slice(0, 4).map((h, i) =>
      '<div class="suggestion-item" role="option" data-suggestion="' + escapeHtml(h) + '" data-idx="' + i + '" data-kind="history" style="padding:0.5rem 0.75rem;cursor:pointer;font-size:0.9rem;border-bottom:1px solid var(--color-border, #333);display:flex;align-items:center;gap:0.5rem">' +
      '<span style="font-size:0.75rem;opacity:0.6">&#128337;</span>' +
      highlightTerms(escapeHtml(h), needle ? needleTerms : []) +
      '</div>'
    ).join('');

    let titleHtml = '';
    if (needle && searchIndex) {
      titleHtml = searchIndex
        .filter(function(e) { return e.title && e.title.toLowerCase().includes(needle); })
        .slice(0, 4)
        .map(function(e) {
          return '<div class="suggestion-item" role="option" data-suggestion="' + escapeHtml(e.title) + '" data-kind="title" style="padding:0.5rem 0.75rem;cursor:pointer;font-size:0.9rem;border-bottom:1px solid var(--color-border, #333);display:flex;align-items:center;gap:0.5rem">' +
            '<span style="font-size:0.75rem;opacity:0.6">&#128269;</span>' +
            highlightTerms(escapeHtml(e.title), needleTerms) +
            '<span style="font-size:0.7rem;opacity:0.6;margin-left:auto">' + escapeHtml(CT_LABELS[e.content_type] || e.content_type || '') + '</span>' +
            '</div>';
        })
        .join('');
    }

    if (!needle && !matchingHistory.length && !conceptHtml) {
      el.innerHTML = '';
      setSuggestionsOpen(el, false);
      return;
    }

    if (needle && !searchIndex) {
      fetchIndex().then(function() { renderSuggestions(filter); }).catch(function() {});
    }

    const combined = [];
    if (conceptHtml) combined.push(conceptHtml);
    if (titleHtml) combined.push(titleHtml);
    if (historyHtml) combined.push(historyHtml);
    if (!combined.length) { el.innerHTML = ''; setSuggestionsOpen(el, false); return; }
    el.innerHTML = combined.join('');
    setSuggestionsOpen(el, true);
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
  let suggestionIndex = -1;

  function populateTechFilters(index) {
    var container = document.getElementById('tech-filter-list');
    if (!container) return;
    // Preserve current selection across re-renders (this runs on every search)
    var checkedTechs = {};
    container.querySelectorAll('.filter-checkbox:checked').forEach(function(cb) {
      checkedTechs[cb.value] = true;
    });
    var techMap = {};
    for (var i = 0; i < index.length; i++) {
      var techs = index[i].technologies || [];
      for (var j = 0; j < techs.length; j++) {
        techMap[techs[j]] = (techMap[techs[j]] || 0) + 1;
      }
    }
    var sorted = Object.keys(techMap).sort(function(a, b) { return techMap[b] - techMap[a]; });
    var topTechs = sorted.slice(0, 20);
    if (!topTechs.length) {
      container.innerHTML = '<span style="font-size:0.75rem;color:var(--color-text-muted,#666)">No technologies detected</span>';
      return;
    }
    container.innerHTML = topTechs.map(function(t) {
      return '<label style="display:flex;align-items:center;gap:0.4rem;font-size:0.85rem;padding:0.2rem 0;cursor:pointer" title="' + techMap[t] + ' items">' +
        '<input type="checkbox" value="' + escapeHtml(t) + '" class="filter-checkbox" data-group="technology"> ' +
        escapeHtml(t) +
        '<span style="font-size:0.65rem;color:var(--color-text-muted,#888);margin-left:auto">' + techMap[t] + '</span>' +
        '</label>';
    }).join('') +
    (sorted.length > 20 ? '<details style="font-size:0.75rem;margin-top:0.25rem"><summary style="cursor:pointer;color:var(--color-text-muted,#888)">+' + (sorted.length - 20) + ' more</summary>' +
      sorted.slice(20).map(function(t) {
        return '<label style="display:flex;align-items:center;gap:0.4rem;font-size:0.8rem;padding:0.15rem 0;cursor:pointer" title="' + techMap[t] + ' items">' +
          '<input type="checkbox" value="' + escapeHtml(t) + '" class="filter-checkbox" data-group="technology"> ' +
          escapeHtml(t) +
          '<span style="font-size:0.65rem;color:var(--color-text-muted,#888);margin-left:auto">' + techMap[t] + '</span>' +
          '</label>';
      }).join('') + '</details>' : '');
    container.querySelectorAll('.filter-checkbox').forEach(function(cb) {
      if (checkedTechs[cb.value]) cb.checked = true;
    });
  }

  function prettyLabel(key) {
    return String(key || '').replace(/-/g, ' ').replace(/\b\w/g, function(m) { return m.toUpperCase(); });
  }

  // Dynamic category facet: top categories by count over entries matching the
  // current pillar/type selection (mirrors populateTechFilters behavior).
  function populateCategories(index) {
    const container = document.getElementById('category-filter-list');
    if (!container) return;
    const checkedCats = {};
    container.querySelectorAll('.filter-checkbox:checked').forEach(function(cb) {
      checkedCats[cb.value] = true;
    });
    const filters = readFilters();
    const catMap = {};
    for (let i = 0; i < index.length; i++) {
      const e = index[i];
      if (filters.pillar.length && !filters.pillar.includes(e.pillar || '')) continue;
      if (filters.type.length && !filters.type.includes(e.content_type || '')) continue;
      const cat = e.category || '';
      if (!cat) continue;
      catMap[cat] = (catMap[cat] || 0) + 1;
    }
    const sorted = Object.keys(catMap).sort(function(a, b) { return catMap[b] - catMap[a]; });
    const topCats = sorted.slice(0, 12);
    if (!topCats.length) {
      container.innerHTML = '<span style="font-size:0.75rem;color:var(--color-text-muted,#666)">No categories detected</span>';
      return;
    }
    container.innerHTML = topCats.map(function(c) {
      return '<label style="display:flex;align-items:center;gap:0.4rem;font-size:0.85rem;padding:0.2rem 0;cursor:pointer" title="' + catMap[c] + ' items">' +
        '<input type="checkbox" value="' + escapeHtml(c) + '" class="filter-checkbox" data-group="category"> ' +
        escapeHtml(prettyLabel(c)) +
        '<span style="font-size:0.65rem;color:var(--color-text-muted,#888);margin-left:auto">' + catMap[c] + '</span>' +
        '</label>';
    }).join('') +
    (sorted.length > 12 ? '<details style="font-size:0.75rem;margin-top:0.25rem"><summary style="cursor:pointer;color:var(--color-text-muted,#888)">+' + (sorted.length - 12) + ' more</summary>' +
      sorted.slice(12).map(function(c) {
        return '<label style="display:flex;align-items:center;gap:0.4rem;font-size:0.8rem;padding:0.15rem 0;cursor:pointer" title="' + catMap[c] + ' items">' +
          '<input type="checkbox" value="' + escapeHtml(c) + '" class="filter-checkbox" data-group="category"> ' +
          escapeHtml(prettyLabel(c)) +
          '<span style="font-size:0.65rem;color:var(--color-text-muted,#888);margin-left:auto">' + catMap[c] + '</span>' +
          '</label>';
      }).join('') + '</details>' : '');
    container.querySelectorAll('.filter-checkbox').forEach(function(cb) {
      if (checkedCats[cb.value]) cb.checked = true;
    });
  }

  function staticBase() {
    const base = document.querySelector('script[src*="search.js"], script[src*="app.js"]');
    if (base) {
      const m = base.src.match(/^(.*\/static\/)js\/[^/]+\.js(?:$|[?#])/);
      if (m) return m[1];
      const m2 = base.src.match(/^(.*\/)js\/[^/]+\.js(?:$|[?#])/);
      if (m2) return m2[1];
    }
    return window.location.origin + '/static/';
  }

  const INDEX_CACHE_VERSION = 'v2';

  function fetchIndex() {
    if (searchIndex) return Promise.resolve(searchIndex);

    // If a single pillar is pre-filtered, load just that chunk
    const filters = readFilters();
    let url = staticBase() + 'search-index.json';
    if (filters.pillar.length === 1) {
      url = staticBase() + 'search-index.' + filters.pillar[0] + '.json';
    }

    // sessionStorage cache: instant repeat searches within the same tab (version-stamped)
    const cacheKey = 'ac_search_index_' + INDEX_CACHE_VERSION + ':' + url;
    try {
      const cached = window.sessionStorage.getItem(cacheKey);
      if (cached) {
        const data = JSON.parse(cached);
        searchIndex = data;
        return Promise.resolve(data);
      }
    } catch (e) {}

    return fetch(url)
      .then(r => { if (!r.ok) throw new Error(r.status); return r.json(); })
      .then(data => {
        searchIndex = data;
        try { window.sessionStorage.setItem(cacheKey, JSON.stringify(data)); } catch (e) {}
        return data;
      });
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

    const filtersActive = (function() {
      const f = readFilters();
      return f.pillar.length || f.type.length || f.difficulty.length || f.bloom.length || f.category.length || f.technology.length;
    })();

    if (!query.trim() && !tagFilter && !filtersActive) {
      container.innerHTML = '<p style="color:var(--color-text-muted, #888);text-align:center;margin-top:2rem">Type to search across all content, or pick a filter to browse...</p>';
      if (statsEl) statsEl.textContent = '';
      renderFilterChips();
      return;
    }

    const terms = query.trim() ? tokenize(query) : [];

    container.setAttribute('aria-busy', 'true');
    container.innerHTML = '<div class="search-loading" role="status"><span class="search-spinner" aria-hidden="true"></span> Loading search index...</div>';

    fetchIndex().then(index => {
      populateTechFilters(index);
      populateCategories(index);
      updateFacetCounts(index);
      // Restore technology filter checkboxes from URL after populating
      var techParams = new URLSearchParams(window.location.search).get('f_technology');
      if (techParams) {
        var techVals = techParams.split(',');
        document.querySelectorAll('#tech-filter-list .filter-checkbox').forEach(function(cb) {
          if (techVals.indexOf(cb.value) !== -1) cb.checked = true;
        });
      }
      var catParams = new URLSearchParams(window.location.search).get('f_category');
      if (catParams) {
        var catVals = catParams.split(',');
        document.querySelectorAll('#category-filter-list .filter-checkbox').forEach(function(cb) {
          if (catVals.indexOf(cb.value) !== -1) cb.checked = true;
        });
      }
      const filters = readFilters();
      const synMap = getSynonymMap();
      const aliases = buildAliasMap(conceptIndex || []);
      let filtered = index.filter(function(e) {
        if (!matchesFilters(e, filters)) return false;
        if (tagFilter) {
          var concepts = e.ontology_concepts || [];
          var tags = e.tags || [];
          var matchesTag = concepts.some(function(c) { return c.toLowerCase() === tagFilter.toLowerCase(); })
            || tags.some(function(t) { return t.toLowerCase() === tagFilter.toLowerCase(); });
          if (!matchesTag) return false;
        }
        return true;
      });
      // Multi-term AND semantics: if every term matches somewhere, require all of them;
      // otherwise fall back to any-term (OR) so over-specific queries still surface hits.
      if (terms.length > 1) {
        const allTerm = filtered.filter(function(e) { return entryHasAllTerms(e, terms, synMap, aliases); });
        if (allTerm.length) filtered = allTerm;
      }
      allScored = filtered
        .map(function(e) {
          return { entry: e, score: terms.length ? scoreEntry(e, terms, synMap, aliases) : 1 };
        })
        .filter(function(x) { return x.score > 0; });
      allScored = applySort(allScored, readSort(), terms.length > 0);
      renderFilterChips();
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
        var suggestion = null;
        if (query.trim()) suggestion = didYouMean(query, getVocabulary(index), 2);
        var msg = tagFilter ? 'No results tagged "' + escapeHtml(tagFilter) + '"' : 'No results for "' + escapeHtml(query) + '"';
        var html = '<div style="text-align:center;margin-top:2rem"><p style="color:var(--color-text-muted, #888)">' + msg + '</p>';
        if (suggestion) {
          html += '<p style="font-size:0.9rem;margin-top:0.5rem;color:var(--color-text, #e8e6e3)">Did you mean: <a href="#" data-didyoumean="' + escapeHtml(suggestion) + '" style="color:var(--color-accent, #818cf8);font-weight:600;text-decoration:underline">' + escapeHtml(suggestion) + '</a>?</p>';
        }
        html += '<p style="font-size:0.8rem;color:var(--color-text-muted, #888);margin-top:0.5rem">Try different keywords or browse by pillar:</p><div style="display:flex;gap:0.5rem;justify-content:center;margin-top:0.75rem"><a href="/compliance/" class="inline-block px-3 py-1.5 text-xs font-semibold rounded-lg" style="background:var(--color-surface,#f0f0f0);color:var(--color-text,#333)">Compliance</a><a href="/markets/" class="inline-block px-3 py-1.5 text-xs font-semibold rounded-lg" style="background:var(--color-surface,#f0f0f0);color:var(--color-text,#333)">Markets</a><a href="/data/" class="inline-block px-3 py-1.5 text-xs font-semibold rounded-lg" style="background:var(--color-surface,#f0f0f0);color:var(--color-text,#333)">Data</a></div></div>';
        container.innerHTML = html;
        return;
      }

      renderPage();
      container.setAttribute('aria-busy', 'false');
    }).catch(function(err) {
      container.setAttribute('aria-busy', 'false');
      var retryBtn = '<button id="search-retry" type="button" style="margin-top:0.75rem;padding:0.5rem 1rem;background:var(--color-surface,#f0f0f0);border:1px solid var(--color-border,#333);border-radius:8px;color:var(--color-text,#333);cursor:pointer;font-size:0.85rem;font-weight:600">Retry</button>';
      container.innerHTML = '<div style="text-align:center;margin-top:2rem"><p style="color:#ef4444">Failed to load search index</p>' + retryBtn + '</div>';
      var retry = document.getElementById('search-retry');
      if (retry) retry.addEventListener('click', function() {
        searchIndex = null;
        runSearch(query, tagFilter);
      });
    });
  }

  function doSearch() {
    const input = document.getElementById('search-input');
    if (!input) return;
    const params = new URLSearchParams(window.location.search);
    runSearch(input.value, params.get('f_tags') || '');
  }

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
      didYouMean: didYouMean,
      bestCorrection: bestCorrection,
      buildVocabulary: buildVocabulary,
      scoreEntry: scoreEntry,
      matchLevel: matchLevel,
      termMatches: termMatches,
      expandTerm: expandTerm,
      entryHasAllTerms: entryHasAllTerms,
      dateBoost: dateBoost,
      buildAliasMap: buildAliasMap,
      entryFieldText: entryFieldText,
      getSynonymMap: getSynonymMap,
      applySort: applySort,
      matchesFilters: matchesFilters,
      prettyLabel: prettyLabel,
    };
  }

  if (typeof document !== 'undefined') {
    document.addEventListener('DOMContentLoaded', function() {
    const input = document.getElementById('search-input');
    if (!input) return;

    // Preload concepts early so synonym/alias expansion is ready before the first search
    fetchConcepts();

    // Restore sort control from URL
    const sortSel = document.getElementById('search-sort');
    if (sortSel) {
      sortSel.value = readSort();
      sortSel.addEventListener('change', function() {
        const url = new URL(window.location);
        if (this.value && this.value !== 'relevance') url.searchParams.set('sort', this.value);
        else url.searchParams.delete('sort');
        history.replaceState(null, '', url);
        runSearch(input.value);
      });
    }

    // Active-filter chips: click a chip to remove that filter
    const chipsEl = document.getElementById('active-filter-chips');
    if (chipsEl) {
      chipsEl.addEventListener('click', function(e) {
        const chip = e.target.closest('.filter-chip');
        if (!chip) return;
        const group = chip.getAttribute('data-group');
        const value = chip.getAttribute('data-value');
        document.querySelectorAll('.filter-checkbox[data-group="' + group + '"]').forEach(function(cb) {
          if (cb.value === value) cb.checked = false;
        });
        const filters = readFilters();
        syncFiltersToUrl(filters);
        if (group === 'pillar') searchIndex = null;
        doSearch();
      });
    }

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
    } else {
      renderFilterChips();
    }

    // Filter checkbox change handler (delegated: technology checkboxes are
    // injected dynamically by populateTechFilters after every search)
    document.addEventListener('change', function(e) {
      const cb = e.target && e.target.classList && e.target.classList.contains('filter-checkbox') ? e.target : null;
      if (!cb) return;
      const filters = readFilters();
      syncFiltersToUrl(filters);
      // Invalidate search index cache when pillar filters change
      if (cb.getAttribute('data-group') === 'pillar') {
        searchIndex = null;
      }
      doSearch();
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

    // Mobile filter toggle
    const filtersToggle = document.getElementById('search-filters-toggle');
    const filtersSidebar = document.getElementById('search-filters');
    if (filtersToggle && filtersSidebar) {
      if (document.querySelector('.filter-checkbox:checked') !== null) {
        filtersSidebar.classList.add('search-sidebar-open');
        filtersToggle.setAttribute('aria-expanded', 'true');
        filtersToggle.textContent = 'Hide filters';
      }
      filtersToggle.addEventListener('click', function() {
        const open = filtersSidebar.classList.toggle('search-sidebar-open');
        filtersToggle.setAttribute('aria-expanded', open ? 'true' : 'false');
        filtersToggle.textContent = open ? 'Hide filters' : 'Filters';
      });
    }

    let debounce = null;
    input.addEventListener('input', function() {
      clearTimeout(debounce);
      const val = input.value;
      fetchConcepts().then(() => renderSuggestions(val));
      debounce = setTimeout(() => {
        const url = new URL(window.location);
        if (val) url.searchParams.set('q', val);
        else url.searchParams.delete('q');
        history.replaceState(null, '', url);
        runSearch(val);
      }, 200);
    });

    input.addEventListener('focus', function() { fetchConcepts().then(() => renderSuggestions(this.value)); });
    input.addEventListener('blur', function() {
      setTimeout(function() {
        const el = document.getElementById('search-suggestions');
        if (el) setSuggestionsOpen(el, false);
      }, 200);
    });

    // Click delegation for result clicks (Plausible tracking) + "Did you mean?" correction
    document.getElementById('search-results').addEventListener('click', function(e) {
      const dym = e.target.closest('[data-didyoumean]');
      if (dym) {
        e.preventDefault();
        const corrected = dym.getAttribute('data-didyoumean');
        input.value = corrected;
        setSuggestionsOpen(document.getElementById('search-suggestions'), false);
        const url = new URL(window.location);
        url.searchParams.set('q', corrected);
        history.replaceState(null, '', url);
        runSearch(corrected);
        return;
      }
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
          setSuggestionsOpen(this, false);
          suggestionIndex = -1;
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
        suggestionIndex = -1;
        setSuggestionsOpen(document.getElementById('search-suggestions'), false);
        runSearch('');
        return;
      }
      const suggestionsEl = document.getElementById('search-suggestions');
      const suggestionsOpen = suggestionsEl && suggestionsEl.style.display === 'block';
      const sugItems = suggestionsOpen ? suggestionsEl.querySelectorAll('.suggestion-item') : [];
      if (suggestionsOpen && (e.key === 'ArrowDown' || e.key === 'ArrowUp')) {
        if (!sugItems.length) return;
        e.preventDefault();
        const dir = e.key === 'ArrowDown' ? 1 : -1;
        suggestionIndex = (suggestionIndex + dir + sugItems.length) % sugItems.length;
        sugItems.forEach(function(el, i) { el.classList.toggle('suggestion-active', i === suggestionIndex); });
        sugItems[suggestionIndex].scrollIntoView({ block: 'nearest' });
        return;
      }
      if (suggestionsOpen && e.key === 'Enter') {
        e.preventDefault();
        const target = sugItems.length ? (sugItems[suggestionIndex] || sugItems[0]) : null;
        if (target) target.click();
        return;
      }
      if (suggestionsOpen && e.key === 'Escape') {
        setSuggestionsOpen(suggestionsEl, false);
        suggestionIndex = -1;
        e.preventDefault();
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
      if (e.key === 'Enter' && allScored.length) {
        const idx = (selectedIndex >= 0 && selectedIndex < allScored.length) ? selectedIndex : 0;
        e.preventDefault();
        window.location.href = slugToUrl(allScored[idx].entry.slug);
      }
    });
  });
  }
})();
