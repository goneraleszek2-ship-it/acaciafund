(function() {
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
    });
  });

  // Concept search live filter
  var conceptInput = document.getElementById('concept-search');
  if (conceptInput) {
    conceptInput.addEventListener('input', function() {
      var q = this.value.toLowerCase();
      document.querySelectorAll('.concept-card').forEach(function(card) {
        card.style.display = q && !card.textContent.toLowerCase().includes(q) ? 'none' : '';
      });
    });
  }

  var pFilter = document.getElementById('concept-pillar-filter');
  if (pFilter) {
    pFilter.addEventListener('change', function() {
      var val = this.value;
      document.querySelectorAll('.concept-card').forEach(function(card) {
        if (!val) { card.style.display = ''; return; }
        card.style.display = card.dataset.pillar === val ? '' : 'none';
      });
    });
  }

  // Content filters
  var itemSearch = document.getElementById('item-search');
  var cpFilter = document.getElementById('content-pillar-filter');
  var ctFilter = document.getElementById('content-type-filter');
  function filterContent() {
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
  if (itemSearch) itemSearch.addEventListener('input', filterContent);
  if (cpFilter) cpFilter.addEventListener('change', filterContent);
  if (ctFilter) ctFilter.addEventListener('change', filterContent);
})();
