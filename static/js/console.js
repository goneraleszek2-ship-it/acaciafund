(function() {
  var DATA_URL = '/static/scholar.json';
  var dataPromise = null;

  function esc(value) {
    return String(value == null ? '' : value).replace(/[&<>"']/g, function (ch) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[ch];
    });
  }

  function titleCase(value) {
    return String(value || '').replace(/_/g, ' ').replace(/\b\w/g, function (c) { return c.toUpperCase(); });
  }

  function pillarMap(pillars) {
    var map = {};
    (pillars || []).forEach(function (p) { map[p.key] = p; });
    return map;
  }

  function loadData() {
    if (!dataPromise) {
      dataPromise = fetch(DATA_URL).then(function (r) {
        if (!r.ok) throw new Error(r.status);
        return r.json();
      });
    }
    return dataPromise;
  }

  function renderConcepts(concepts, pillars) {
    var list = document.getElementById('concept-list');
    if (!list) return;
    var pmap = pillarMap(pillars);
    list.innerHTML = concepts.map(function (c) {
      var quality = c.explanation_quality || 0;
      var qualityStyle = quality >= 0.8
        ? 'background:#22c55e20;color:#22c55e'
        : (quality >= 0.5 ? 'background:#f59e0b20;color:#f59e0b' : 'background:#ef444420;color:#ef4444');
      var meta = pmap[c.pillar] || {};
      return '<div class="ghost-card p-4 concept-card" data-pillar="' + esc(c.pillar) + '">' +
        '<div class="flex items-start justify-between gap-3">' +
          '<div class="flex-1 min-w-0">' +
            '<a href="/concepts/' + encodeURIComponent(c.id) + '/" class="text-sm font-semibold text-accent">' + esc(c.label) + '</a>' +
            '<p class="text-xs text-muted mt-1">' + esc(c.description) + '</p>' +
            '<div class="flex flex-wrap gap-1.5 mt-2 text-[10px]">' +
              '<span class="badge-outline">' + esc(titleCase(c.pillar)) + '</span>' +
              '<span class="badge-outline">' + esc(titleCase(c.category)) + '</span>' +
              (c.epistemic_status ? '<span class="badge-outline opacity-70">' + esc(titleCase(c.epistemic_status)) + '</span>' : '') +
              (quality ? '<span class="badge-outline opacity-70" style="' + qualityStyle + '">F:' + Math.round(quality * 100) + '</span>' : '') +
              (c.cross_pillar_analogs ? '<span class="badge-outline opacity-70" style="color:#6366f1">' + c.cross_pillar_analogs + ' analogs</span>' : '') +
            '</div>' +
            (c.eli5_explanation ? '<details class="mt-2"><summary class="text-xs cursor-pointer text-muted">ELI5</summary><p class="text-xs mt-1 italic text-muted">' + esc(c.eli5_explanation) + '</p></details>' : '') +
          '</div>' +
          '<div class="flex flex-col items-end gap-1 text-[10px] text-muted shrink-0">' +
            '<span>Score: ' + Math.round((c.confidence_score || 0) * 100) + '</span>' +
            '<span>' + (c.relations || 0) + ' rel.</span>' +
            '<span>' + (c.content_count || 0) + ' content</span>' +
          '</div>' +
        '</div>' +
      '</div>';
    }).join('');
  }

  function renderContent(items, pillars) {
    var list = document.getElementById('content-list');
    if (!list) return;
    var pmap = pillarMap(pillars);
    list.innerHTML = items.map(function (item) {
      var meta = pmap[item.pillar] || {};
      return '<div class="ghost-card p-3 content-item" data-pillar="' + esc(item.pillar) + '" data-type="' + esc(item.content_type) + '">' +
        '<a href="' + esc(item.url) + '" class="text-xs font-semibold text-accent">' + esc(item.title) + '</a>' +
        '<div class="flex flex-wrap items-center gap-2 mt-1 text-[10px] text-muted">' +
          '<span style="color:' + esc(meta.color || 'var(--color-text-muted)') + '">' + esc(meta.label || titleCase(item.pillar)) + '</span>' +
          '<span>' + esc(titleCase(item.content_type)) + '</span>' +
          '<span>' + esc(titleCase(item.difficulty)) + '</span>' +
          '<span>SQI: ' + Math.round((item.sqi || 0) * 100) + '</span>' +
        '</div>' +
      '</div>';
    }).join('');
  }

  function renderFeynman(concepts) {
    var list = document.getElementById('feynman-list');
    if (!list) return;
    var withExplanations = concepts.filter(function (c) {
      return c.eli5_explanation || c.analogy || c.concrete_example;
    });
    list.innerHTML = withExplanations.map(function (c) {
      var quality = c.explanation_quality || 0;
      var qualityClass = quality >= 0.8 ? 'text-green-500' : (quality >= 0.5 ? 'text-yellow-500' : 'text-red-400');
      var qualityLabel = quality >= 0.8 ? 'High' : (quality >= 0.5 ? 'Med' : 'Low');
      return '<div class="ghost-card p-3">' +
        '<div class="flex items-start justify-between gap-2">' +
          '<div class="flex-1 min-w-0">' +
            '<a href="/concepts/' + encodeURIComponent(c.id) + '/" class="text-xs font-semibold text-accent">' + esc(c.label) + '</a>' +
            '<p class="text-[10px] text-muted mt-0.5">' + esc(titleCase(c.pillar)) + '</p>' +
            (c.eli5_explanation ? '<p class="text-xs text-muted italic mt-1">&ldquo;' + esc(c.eli5_explanation) + '&rdquo;</p>' : '') +
            (c.analogy ? '<p class="text-[10px] text-muted mt-1">' + esc(c.analogy) + '</p>' : '') +
            (c.gap_questions ? '<div class="text-[10px] text-muted mt-1">' + c.gap_questions + ' gap question' + (c.gap_questions === 1 ? '' : 's') + '</div>' : '') +
          '</div>' +
          '<div class="text-center shrink-0" style="min-width:48px">' +
            '<div class="text-lg font-bold ' + qualityClass + '">' + Math.round(quality * 100) + '</div>' +
            '<p class="text-[10px] text-muted">' + qualityLabel + '</p>' +
          '</div>' +
        '</div>' +
      '</div>';
    }).join('');
  }

  function renderPanel(name) {
    var panel = document.querySelector('.console-panel[data-panel="' + name + '"]');
    if (!panel || panel.dataset.loaded) return;
    loadData().then(function (data) {
      if (name === 'ontology') renderConcepts(data.concepts || [], data.pillars || []);
      if (name === 'content') renderContent(data.content || [], data.pillars || []);
      if (name === 'feynman') renderFeynman(data.concepts || []);
      panel.dataset.loaded = '1';
      filterConcepts();
      filterContent();
    }).catch(function () {
      var list = panel.querySelector('[data-loading]');
      if (list) list.textContent = 'Could not load data. Reload the page to retry.';
    });
  }

  var tabs = document.querySelectorAll('.console-tab');
  var panels = document.querySelectorAll('.console-panel');

  tabs.forEach(function(tab) {
    tab.addEventListener('click', function() {
      var target = this.dataset.tab;
      tabs.forEach(function(t) {
        t.style.background = '';
        t.style.color = 'var(--color-text-muted)';
        t.setAttribute('aria-selected', 'false');
      });
      this.style.background = 'var(--color-surface)';
      this.style.color = 'var(--color-text)';
      this.setAttribute('aria-selected', 'true');
      panels.forEach(function(p) {
        p.style.display = p.dataset.panel === target ? '' : 'none';
      });
      renderPanel(target);
    });
  });

  function filterConcepts() {
    var input = document.getElementById('concept-search');
    var select = document.getElementById('concept-pillar-filter');
    var q = (input ? input.value : '').toLowerCase();
    var p = select ? select.value : '';
    document.querySelectorAll('.concept-card').forEach(function(card) {
      var ok = (!q || card.textContent.toLowerCase().includes(q))
        && (!p || card.dataset.pillar === p);
      card.style.display = ok ? '' : 'none';
    });
  }

  function filterContent() {
    var itemSearch = document.getElementById('item-search');
    var cpFilter = document.getElementById('content-pillar-filter');
    var ctFilter = document.getElementById('content-type-filter');
    var q = (itemSearch ? itemSearch.value : '').toLowerCase();
    var p = cpFilter ? cpFilter.value : '';
    var t = ctFilter ? ctFilter.value : '';
    document.querySelectorAll('.content-item').forEach(function(row) {
      var ok = (!q || row.textContent.toLowerCase().includes(q))
        && (!p || row.dataset.pillar === p)
        && (!t || row.dataset.type === t);
      row.style.display = ok ? '' : 'none';
    });
  }

  var conceptInput = document.getElementById('concept-search');
  var conceptFilter = document.getElementById('concept-pillar-filter');
  if (conceptInput) conceptInput.addEventListener('input', filterConcepts);
  if (conceptFilter) conceptFilter.addEventListener('change', filterConcepts);

  var itemSearch = document.getElementById('item-search');
  var cpFilter = document.getElementById('content-pillar-filter');
  var ctFilter = document.getElementById('content-type-filter');
  if (itemSearch) itemSearch.addEventListener('input', filterContent);
  if (cpFilter) cpFilter.addEventListener('change', filterContent);
  if (ctFilter) ctFilter.addEventListener('change', filterContent);
})();
