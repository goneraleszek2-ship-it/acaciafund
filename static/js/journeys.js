
/* journeys.js */
(function () {
  'use strict';

  /* ── Pure helpers (unit-tested via tests/test_journeys.js) ── */

  function readState(storage, journeyId, total) {
    var state = [];
    try {
      state = JSON.parse(storage.getItem('acacia_journey_' + journeyId) || 'null') || [];
    } catch (_) {}
    state = state.slice(0, total);
    while (state.length < total) state.push(false);
    return state;
  }

  function writeState(storage, journeyId, state) {
    try { storage.setItem('acacia_journey_' + journeyId, JSON.stringify(state)); } catch (_) {}
  }

  function toggleStep(state, index) {
    if (index < 0 || index >= state.length) return state;
    var next = state.slice();
    next[index] = !next[index];
    return next;
  }

  function progressPercent(state) {
    if (!state.length) return 0;
    var done = state.filter(Boolean).length;
    return Math.round((done / state.length) * 100);
  }

  function isComplete(state) {
    return state.length > 0 && state.every(Boolean);
  }

  function nextIncomplete(state) {
    for (var i = 0; i < state.length; i++) {
      if (!state[i]) return i;
    }
    return -1;
  }

  /* ── Page wiring ── */

  function init() {
    var app = document.getElementById('journey-app');
    if (!app) return;
    var journeyId = app.getAttribute('data-journey');
    var total = parseInt(app.getAttribute('data-total') || '0', 10);
    if (!journeyId || !total) return;

    var state = readState(localStorage, journeyId, total);
    var toggles = app.querySelectorAll('[data-step]');
    var bar = document.getElementById('journey-progress-bar');
    var pct = document.getElementById('journey-progress-pct');
    var nextBtn = document.getElementById('journey-next');
    var doneMsg = document.getElementById('journey-done');

    function render() {
      toggles.forEach(function (box, i) {
        if (!box) return;
        box.checked = !!state[i];
        var row = box.closest('.journey-step');
        if (row) row.classList.toggle('is-done', !!state[i]);
      });
      var p = progressPercent(state);
      if (bar) bar.style.width = p + '%';
      if (pct) pct.textContent = p + '%';
      var next = nextIncomplete(state);
      if (nextBtn) {
        if (next < 0) {
          nextBtn.classList.add('hidden');
          if (doneMsg) doneMsg.classList.remove('hidden');
        } else {
          nextBtn.classList.remove('hidden');
          nextBtn.setAttribute('href', app.querySelector('[data-step="' + next + '"]') ?
            app.querySelector('[data-step="' + next + '"]').closest('a.journey-step-link') ?
              app.querySelector('[data-step="' + next + '"]').closest('a.journey-step-link').getAttribute('href') :
              '#' : '#');
        }
      }
    }

    toggles.forEach(function (box, i) {
      box.addEventListener('change', function () {
        state = toggleStep(state, i);
        writeState(localStorage, journeyId, state);
        render();
      });
    });

    render();
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
      readState: readState,
      writeState: writeState,
      toggleStep: toggleStep,
      progressPercent: progressPercent,
      isComplete: isComplete,
      nextIncomplete: nextIncomplete,
    };
  }
})();
