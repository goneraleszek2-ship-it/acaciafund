(function() {
  'use strict';

  function badgeStyle() {
    return 'display:none;background:var(--color-accent,#818cf8);color:#fff;font-size:0.65rem;line-height:1;padding:2px 5px;border-radius:9999px;margin-left:4px;vertical-align:middle';
  }

  function dueCountFor(store, entries, idField) {
    var now = Date.now();
    var due = 0;
    for (var i = 0; i < entries.length; i++) {
      var e = entries[i];
      var st = store[e[idField]] || {};
      var dueAt = st.due || 0;
      var reps = st.reps || 0;
      if (reps === 0 || (dueAt > 0 && dueAt <= now)) due++;
    }
    return due;
  }

  function countDue() {
    var mastery = {};
    try { mastery = JSON.parse(localStorage.getItem('acacia_concept_mastery') || '{}'); } catch (_) {}
    var sm2 = {};
    try { sm2 = JSON.parse(localStorage.getItem('acacia_sm2') || '{}'); } catch (_) {}

    var base = document.querySelector('script[src*="review_badge.js"]');
    var prefix = base ? base.src.replace(/js\/\w+\.js.*$/, '') : '';

    Promise.all([
      fetch(prefix + 'static/review_concepts.json').then(function(r) { if (!r.ok) throw new Error(r.status); return r.json(); }),
      fetch(prefix + 'static/flashcard_index.json').then(function(r) { if (!r.ok) throw new Error(r.status); return r.json(); }),
    ])
      .then(function(results) {
        var concepts = (results[0] && results[0].concepts) || [];
        var cards = (results[1] && results[1].cards) || [];
        var due = dueCountFor(mastery, concepts, 'id') + dueCountFor(sm2, cards, 'id');
        updateBadge(due);
      })
      .catch(function() {});
  }

  function updateBadge(count) {
    document.querySelectorAll('a[href="/review/"], a[href="/study/"]').forEach(function(link) {
      var badge = link.querySelector('.review-badge');
      if (!badge) {
        badge = document.createElement('span');
        badge.className = 'review-badge';
        badge.style.cssText = badgeStyle();
        link.appendChild(badge);
      }
      if (count > 0) {
        badge.textContent = count > 99 ? '99+' : count;
        badge.style.display = 'inline-block';
      } else {
        badge.style.display = 'none';
      }
    });
    document.querySelectorAll('[data-tab-badge]').forEach(function(el) {
      el.classList.remove('hidden');
      el.textContent = count > 99 ? '99+' : count;
      el.classList.toggle('is-hot', count > 0);
      if (count <= 0) el.classList.add('hidden');
    });
  }

  document.addEventListener('DOMContentLoaded', function() {
    var link = document.querySelector('a[href="/review/"], a[href="/study/"]');
    if (!link) return;
    var badge = document.createElement('span');
    badge.className = 'review-badge';
    badge.style.cssText = badgeStyle();
    link.appendChild(badge);
    countDue();
    window.addEventListener('storage', countDue);
    document.addEventListener('review-badge-update', function() { countDue(); });
  });
})();
