
/* pillar_rail.js */

/* pillar_rail.js */

/* pillar_rail.js */

/* pillar_rail.js */

/* pillar_rail.js */

/* pillar_rail.js */
(function () {
  'use strict';

  /* ── Pure helpers (unit-tested via tests/test_pillar_rail.js) ── */

  function ringPath(pct, radius) {
    var circumference = 2 * Math.PI * radius;
    var clamped = Math.max(0, Math.min(100, pct));
    return { circumference: circumference, offset: circumference * (1 - clamped / 100) };
  }

  function masteryPct(entries, store, idField) {
    if (!entries.length) return 0;
    var seen = 0;
    for (var i = 0; i < entries.length; i++) {
      var st = store[entries[i][idField]] || {};
      if ((st.reps || 0) > 0) seen++;
    }
    return Math.round((seen / entries.length) * 100);
  }

  function dueEntries(entries, store, idField, now) {
    var due = [];
    for (var i = 0; i < entries.length; i++) {
      var e = entries[i];
      var st = store[e[idField]] || {};
      var dueAt = st.due || 0;
      if ((st.reps || 0) === 0 || (dueAt > 0 && dueAt <= now)) due.push(e);
    }
    due.sort(function (a, b) {
      return ((store[a[idField]] || {}).due || 0) - ((store[b[idField]] || {}).due || 0);
    });
    return due;
  }

  function nextDue(entries, n) {
    return entries.slice(0, n);
  }

  /* ── Page wiring ── */

  function setRing(el, pct, label) {
    var circle = el.querySelector('[data-ring-circle]');
    var labelEl = el.querySelector('[data-ring-label]');
    if (circle && circle.getBoundingClientRect) {
      var path = ringPath(pct, 9);
      circle.style.strokeDasharray = path.circumference.toFixed(2);
      circle.style.strokeDashoffset = path.offset.toFixed(2);
    }
    if (labelEl && label !== undefined && label !== null) {
      labelEl.textContent = label;
    }
  }

  function renderQueue(el, items, kindLabel) {
    if (!items.length) {
      el.innerHTML = '<p class="text-sm text-muted">Nothing due right now.</p>';
      return;
    }
    var html = '';
    for (var i = 0; i < items.length; i++) {
      var it = items[i];
      html += '<div class="rail-item">' +
        '<span class="text-xs font-meta text-muted">' + (kindLabel ? kindLabel + ' ' : '') + (i + 1) + '</span>' +
        '<span class="rail-item-title">' + it.term + '</span>' +
        '</div>';
    }
    el.innerHTML = html;
  }

  function init() {
    var rail = document.querySelector('.pillar-rail');
    if (!rail) return;
    var pillar = rail.getAttribute('data-pillar');
    var base = document.querySelector('script[src*="pillar_rail.js"]');
    var prefix = base ? base.src.replace(/js\/\w+\.js.*$/, '') : '';

    var sm2 = {};
    var mastery = {};
    try { sm2 = JSON.parse(localStorage.getItem('acacia_sm2') || '{}'); } catch (_) {}
    try { mastery = JSON.parse(localStorage.getItem('acacia_concept_mastery') || '{}'); } catch (_) {}

    var ringEls = rail.querySelectorAll('[data-mastery]');
    var queueEl = document.getElementById('rail-queue');

    Promise.all([
      fetch(prefix + 'static/review_concepts.json').then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); }),
      fetch(prefix + 'static/flashcard_index.json').then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); }),
    ])
      .then(function (results) {
        var concepts = (results[0] && results[0].concepts) || [];
        var cards = (results[1] && results[1].cards) || [];

        var pillarConcepts = concepts.filter(function (c) { return c.pillar === pillar; });
        var pillarCards = cards.filter(function (c) { return c.pillar === pillar; });

        var fcPct = masteryPct(pillarCards, sm2, 'id');
        var coPct = masteryPct(pillarConcepts, mastery, 'id');
        var allCards = cards.concat(concepts.map(function (c) {
          return { id: c.id, term: c.label };
        }));

        var dueFlash = dueEntries(pillarCards, sm2, 'id', Date.now());
        var dueConcepts = dueEntries(pillarConcepts, mastery, 'id', Date.now());

        var mixed = nextDue(
          dueFlash.map(function (c) { return { term: c.term, due: (sm2[c.id] || {}).due || 0 }; })
            .concat(dueConcepts.map(function (c) { return { term: c.label, due: (mastery[c.id] || {}).due || 0 }; }))
            .sort(function (a, b) { return a.due - b.due; }),
          3
        );

        ringEls.forEach(function (el) {
          var kind = el.getAttribute('data-mastery');
          if (kind === 'flashcards') setRing(el, fcPct, 'Flash ' + fcPct + '%');
          if (kind === 'concepts') setRing(el, coPct, 'Concepts ' + coPct + '%');
        });

        if (queueEl) renderQueue(queueEl, mixed, '');
      })
      .catch(function () {
        if (queueEl) queueEl.innerHTML = '<p class="text-sm text-muted">Queue unavailable.</p>';
      });
  }

  if (typeof document !== 'undefined') {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', init);
    } else {
      init();
    }
  }

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
      ringPath: ringPath,
      masteryPct: masteryPct,
      dueEntries: dueEntries,
      nextDue: nextDue,
    };
  }
})();
