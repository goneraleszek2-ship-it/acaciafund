(function(){
  var idx = null;
  var searchInput = document.getElementById('search-input');
  var resultsEl = document.getElementById('search-results');
  var countEl = document.getElementById('search-count');
  if (!searchInput || !resultsEl) return;

  function score(query, item) {
    var q = query.toLowerCase();
    var t = (item.title || '').toLowerCase();
    var d = (item.description || '').toLowerCase();
    var tags = (item.tags || []).join(' ').toLowerCase();
    var s = 0;
    if (t === q) s += 20;
    if (t.indexOf(q) !== -1) s += 10;
    if (tags.indexOf(q) !== -1) s += 5;
    if (d.indexOf(q) !== -1) s += 2;
    q.split(' ').forEach(function(word){
      if (word.length < 2) return;
      if (t.indexOf(word) !== -1) s += 3;
      if (tags.indexOf(word) !== -1) s += 2;
      if (d.indexOf(word) !== -1) s += 1;
    });
    return s;
  }

  function render(query) {
    if (!idx) { resultsEl.innerHTML = '<p class="text-sm py-8 text-center" style="color:var(--color-text-muted)">Loading search index...</p>'; return; }
    if (!query || query.length < 2) { resultsEl.innerHTML = ''; if (countEl) countEl.textContent = ''; return; }
    var results = [];
    idx.forEach(function(item){
      var s = score(query, item);
      if (s > 0) results.push({score: s, item: item});
    });
    results.sort(function(a,b){ return b.score - a.score; });
    results = results.slice(0, 20);
    if (countEl) countEl.textContent = results.length + ' result' + (results.length !== 1 ? 's' : '');
    if (results.length === 0) {
      resultsEl.innerHTML = '<p class="text-sm py-8 text-center" style="color:var(--color-text-muted)">No results for "' + query + '"</p>';
      return;
    }
    var pillarColors = {aml:'#d97706', stock:'#22c55e', science:'#a855f7'};
    var typeLabels = {research:'Research', learn:'Learn', knowledge:'Knowledge'};
    var html = '';
    results.forEach(function(r){
      var item = r.item;
      var pc = pillarColors[item.pillar] || '#6366f1';
      var tl = typeLabels[item.content_type] || item.content_type;
      html += '<a href="/' + item.slug + '/" class="block rounded-lg p-4 transition hover:shadow-md" style="background:var(--color-surface);border:1px solid var(--color-border);text-decoration:none">';
      html += '<div class="flex items-center gap-2 mb-1">';
      html += '<span class="inline-block w-2 h-2 rounded-full" style="background:' + pc + '"></span>';
      html += '<span class="text-xs font-medium" style="color:' + pc + '">' + tl + '</span>';
      if (item.content_type === 'learn' && item.difficulty) {
        var dEmoji = {beginner:'🌱', intermediate:'📘', advanced:'🔥'};
        html += '<span class="text-xs" style="color:var(--color-text-muted)">' + (dEmoji[item.difficulty] || '') + ' ' + item.difficulty.charAt(0).toUpperCase() + item.difficulty.slice(1) + '</span>';
      }
      if (item.date_str) html += '<span class="text-xs" style="color:var(--color-text-muted)">' + item.date_str + '</span>';
      html += '</div>';
      html += '<h3 class="font-semibold" style="color:var(--color-text)">' + item.title + '</h3>';
      if (item.description) html += '<p class="mt-1 text-sm" style="color:var(--color-text-secondary)">' + item.description.slice(0, 200) + '</p>';
      if (item.tags && item.tags.length) html += '<div class="mt-2 flex flex-wrap gap-1">' + item.tags.slice(0, 5).map(function(t){ return '<span class="px-2 py-0.5 text-xs rounded" style="background:var(--color-bg);color:var(--color-text-muted)">' + t + '</span>'; }).join('') + '</div>';
      html += '</a>';
    });
    resultsEl.innerHTML = html;
  }

  // Fetch index
  var xhr = new XMLHttpRequest();
  xhr.open('GET', '/static/search-index.json', true);
  xhr.onload = function(){
    if (xhr.status === 200) {
      try { idx = JSON.parse(xhr.responseText); } catch(e) { idx = []; }
      render(searchInput.value);
    } else {
      resultsEl.innerHTML = '<p class="text-sm py-8 text-center" style="color:var(--color-text-muted)">Failed to load search index.</p>';
    }
  };
  xhr.onerror = function(){
    resultsEl.innerHTML = '<p class="text-sm py-8 text-center" style="color:var(--color-text-muted)">Network error loading search.</p>';
  };
  xhr.send();

  var debounceTimer = null;
  searchInput.addEventListener('input', function(){
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(function(){ render(searchInput.value); }, 150);
  });
  searchInput.addEventListener('keydown', function(e){
    if (e.key === 'Escape') { searchInput.blur(); resultsEl.innerHTML = ''; if (countEl) countEl.textContent = ''; }
  });
})();
