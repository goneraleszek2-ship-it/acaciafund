(function() {
  'use strict';

  function badgeStyle() {
    return 'display:none;background:var(--color-accent,#818cf8);color:#fff;font-size:0.65rem;line-height:1;padding:2px 5px;border-radius:9999px;margin-left:4px;vertical-align:middle';
  }

  function countDue() {
    var mastery = {};
    try { mastery = JSON.parse(localStorage.getItem('acacia_concept_mastery') || '{}'); } catch (_) {}
    var sm2 = {};
    try { sm2 = JSON.parse(localStorage.getItem('acacia_sm2') || '{}'); } catch (_) {}

    var base = document.querySelector('script[src*="review_badge.js"]');
    var prefix = base ? base.src.replace(/js\/\w+\.js.*$/, '') : '';

    fetch(prefix + 'static/review_concepts.json')
      .then(function(r) { if (!r.ok) throw new Error(r.status); return r.json(); })
      .then(function(data) {
        var concepts = data.concepts || [];
        var now = Date.now();
        var due = 0;
        for (var i = 0; i < concepts.length; i++) {
          var c = concepts[i];
          var m = mastery[c.id] || {};
          var s = sm2[c.id] || {};
          var conceptDue = m.due || s.due || 0;
          var reps = (m.reps || 0) + (s.reps || 0);
          if (reps === 0 || (conceptDue > 0 && conceptDue <= now)) due++;
        }
        updateBadge(due);
      })
      .catch(function() {});
  }

  function updateBadge(count) {
    document.querySelectorAll('a[href="/review/"]').forEach(function(link) {
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
  }

  document.addEventListener('DOMContentLoaded', function() {
    var link = document.querySelector('a[href="/review/"]');
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
