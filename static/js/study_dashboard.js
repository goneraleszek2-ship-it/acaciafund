
/* study_dashboard.js */

/* study_dashboard.js */

/* study_dashboard.js */

/* study_dashboard.js */

/* study_dashboard.js */

/* study_dashboard.js */
(function () {
  'use strict';

  /* ── Pure helpers (unit-tested via tests/test_study_dashboard.js) ── */

  function streakFromHistory(history, now) {
    if (!history || !history.length) return 0;
    var days = {};
    for (var i = 0; i < history.length; i++) days[history[i]] = true;
    var today = new Date(now).toISOString().slice(0, 10);
    var yesterday = new Date(now - 86400000).toISOString().slice(0, 10);
    if (!days[today] && !days[yesterday]) return 0;
    var streak = 0;
    var d = days[today] ? new Date(now) : new Date(now - 86400000);
    while (true) {
      var key = d.toISOString().slice(0, 10);
      if (days[key]) {
        streak++;
        d = new Date(d.getTime() - 86400000);
      } else break;
    }
    return streak;
  }

  function weekBars(history, now) {
    var days = {};
    for (var i = 0; i < (history || []).length; i++) days[history[i]] = true;
    var bars = [];
    var d = new Date(now);
    var today = new Date(Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), d.getUTCDate()));
    for (var offset = 6; offset >= 0; offset--) {
      var day = new Date(today.getTime() - offset * 86400000);
      var key = day.toISOString().slice(0, 10);
      bars.push({ day: day.toLocaleDateString(undefined, { weekday: 'narrow' }), active: !!days[key] });
    }
    return bars;
  }

  function nextUp(cards, store, n, now) {
    var upcoming = [];
    for (var i = 0; i < cards.length; i++) {
      var st = store[cards[i].id] || {};
      if ((st.reps || 0) === 0 || ((st.due || 0) > 0 && st.due > now)) upcoming.push(cards[i]);
    }
    upcoming.sort(function (a, b) {
      return ((store[a.id] || {}).due || 0) - ((store[b.id] || {}).due || 0);
    });
    return upcoming.slice(0, n);
  }

  function dueInLabel(due, now) {
    if (!due || due <= now) return 'due';
    var days = Math.ceil((due - now) / 86400000);
    if (days <= 1) return 'tomorrow';
    return 'in ' + days + 'd';
  }

  function weakConcepts(store, minEase) {
    var weak = [];
    var keys = Object.keys(store);
    for (var i = 0; i < keys.length; i++) {
      var st = store[keys[i]];
      if (st && (st.reps || 0) > 0 && st.ease < minEase) {
        weak.push({ id: keys[i], ease: st.ease, reps: st.reps });
      }
    }
    weak.sort(function (a, b) { return a.ease - b.ease; });
    return weak.slice(0, 5);
  }

  /* ── Page wiring ── */

  function init() {
    var app = document.getElementById('study-dashboard');
    if (!app) return;
    var base = document.querySelector('script[src*="study_dashboard.js"]');
    var prefix = base ? base.src.replace(/js\/\w+\.js.*$/, '') : '';

    var sm2 = {};
    var mastery = {};
    var history = [];
    try { sm2 = JSON.parse(localStorage.getItem('acacia_sm2') || '{}'); } catch (_) {}
    try { mastery = JSON.parse(localStorage.getItem('acacia_concept_mastery') || '{}'); } catch (_) {}
    try { history = JSON.parse(localStorage.getItem('acacia_review_history') || '[]'); } catch (_) {}

    var streakEl = document.getElementById('study-streak');
    if (streakEl) {
      var s = streakFromHistory(history, Date.now());
      streakEl.textContent = String(s);
      streakEl.closest('.study-streak-card').classList.toggle('is-live', s > 0);
    }

    var weekEl = document.getElementById('side-week');
    if (weekEl) {
      var bars = weekBars(history, Date.now());
      var max = 1;
      weekEl.innerHTML = bars.map(function (b) {
        return '<div class="week-bar" title="' + (b.active ? 'Reviewed' : 'No review') + '">' +
          '<div class="week-bar-fill' + (b.active ? ' is-active' : '') + '" style="height:' + (b.active ? 100 : 12) + '%"></div>' +
          '<span class="week-bar-day">' + b.day + '</span></div>';
      }).join('');
    }

    fetch(prefix + 'static/flashcard_index.json')
      .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
      .then(function (data) {
        var cards = (data && data.cards) || [];
        var up = nextUp(cards, sm2, 5, Date.now());
        var upEl = document.getElementById('side-upcoming');
        if (upEl) {
          if (!up.length) {
            upEl.innerHTML = '<p class="text-sm text-muted">All cards scheduled — nothing upcoming.</p>';
          } else {
            upEl.innerHTML = up.map(function (c) {
              var label = dueInLabel((sm2[c.id] || {}).due, Date.now());
              return '<div class="rail-item">' +
                '<span class="text-xs font-meta text-muted shrink-0">' + label + '</span>' +
                '<span class="rail-item-title">' + c.term + '</span></div>';
            }).join('');
          }
        }
        var weak = weakConcepts(sm2, 2.0);
        var weakEl = document.getElementById('side-weak');
        if (weakEl) {
          if (!weak.length) {
            weakEl.innerHTML = '<p class="text-sm text-muted">No weak cards — ease factors healthy.</p>';
          } else {
            weakEl.innerHTML = weak.map(function (w) {
              var label = w.id.split('#')[0].split('/').pop();
              return '<div class="rail-item">' +
                '<span class="text-xs font-meta text-muted shrink-0">ease ' + w.ease.toFixed(2) + '</span>' +
                '<span class="rail-item-title">' + label + '</span></div>';
            }).join('');
          }
        }
      })
      .catch(function () {});
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
      streakFromHistory: streakFromHistory,
      weekBars: weekBars,
      nextUp: nextUp,
      dueInLabel: dueInLabel,
      weakConcepts: weakConcepts,
    };
  }
})();
