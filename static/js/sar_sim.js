
/* sar_sim.js */

/* sar_sim.js */

/* sar_sim.js */
/* sar_sim.js */

/* sar_sim.js */

/* sar_sim.js */
(function () {
  'use strict';

  /* ── Pure helpers (unit-tested via tests/test_sar_sim.js) ── */

  function countWords(text) {
    var words = String(text || '').trim().split(/\s+/).filter(function (w) { return w.length > 0; });
    return words.length;
  }

  function validateSar(input) {
    var issues = [];
    if (!String(input.subject || '').trim()) issues.push('Subject is required.');
    var flags = input.flags || [];
    if (!flags.length) issues.push('Select at least one red flag.');
    if (countWords(input.narrative) < (input.minWords || 20)) {
      issues.push('Narrative must be at least ' + (input.minWords || 20) + ' words.');
    }
    if (!/[a-z0-9]/i.test(input.narrative)) issues.push('Narrative must describe the activity.');
    return {
      valid: issues.length === 0,
      issues: issues,
      wordCount: countWords(input.narrative),
    };
  }

  function referenceNumber() {
    var d = new Date();
    var ymd = d.toISOString().slice(0, 10).replace(/-/g, '');
    var rand = String(Math.floor(Math.random() * 90000) + 10000);
    return 'SAR-' + ymd + '-' + rand;
  }

  /* ── Page wiring ── */

  function init() {
    var cards = document.querySelectorAll('[data-sar-sim]');
    if (!cards.length) return;

    cards.forEach(function (card) {
      var ex = {};
      try { ex = JSON.parse(card.getAttribute('data-ex') || '{}'); } catch (_) {}
      var minWords = ex.narrative_min_words || 20;

      var form = card.querySelector('[data-sar-form]');
      var status = card.querySelector('[data-sar-status]');
      var result = card.querySelector('[data-sar-result]');
      var flagStatus = card.querySelector('[data-sar-flag-status]');
      var wordStatus = card.querySelector('[data-sar-word-status]');
      var narrative = card.querySelector('[data-sar-field="narrative"]');
      var flagBoxes = card.querySelectorAll('[data-sar-flag]');

      function updateCounters() {
        flagStatus.textContent = Array.prototype.filter.call(flagBoxes, function (b) { return b.checked; }).length + ' of ' + flagBoxes.length + ' flags selected';
        wordStatus.textContent = countWords(narrative.value) + ' / ' + minWords + ' words';
      }
      Array.prototype.forEach.call(flagBoxes, function (b) {
        b.addEventListener('change', updateCounters);
      });
      narrative.addEventListener('input', updateCounters);
      updateCounters();

      form.addEventListener('submit', function (ev) {
        ev.preventDefault();
        var flags = Array.prototype.filter.call(flagBoxes, function (b) { return b.checked; })
          .map(function (b) { return b.value; });
        var verdict = validateSar({
          subject: card.querySelector('[data-sar-field="subject"]').value,
          flags: flags,
          narrative: narrative.value,
          minWords: minWords,
        });
        if (!verdict.valid) {
          status.textContent = verdict.issues.join(' ');
          status.className = 'text-xs font-semibold sandbox-err';
          return;
        }
        var ref = referenceNumber();
        status.textContent = '✓ Draft validated — filed.';
        status.className = 'text-xs font-semibold sandbox-ok';
        var out = document.createElement('div');
        out.className = 'sandbox-ok-card';
        var h = document.createElement('h4');
        h.className = 'text-sm font-bold mb-2';
        h.textContent = 'SAR draft complete';
        out.appendChild(h);
        var rows = [
          ['Reference', ref],
          ['Subject', card.querySelector('[data-sar-field="subject"]').value],
          ['Red flags', flags.join('; ')],
          ['Narrative words', String(verdict.wordCount)],
          ['Status', 'Draft ready for filing — regulator submission is out of scope for this simulator'],
        ];
        rows.forEach(function (r) {
          var p = document.createElement('p');
          p.className = 'text-sm mb-1';
          var b = document.createElement('span');
          b.className = 'font-semibold';
          b.textContent = r[0] + ': ';
          p.appendChild(b);
          p.appendChild(document.createTextNode(r[1]));
          out.appendChild(p);
        });
        var again = document.createElement('button');
        again.type = 'button';
        again.className = 'btn-ghost-sm mt-3';
        again.textContent = 'New draft';
        again.addEventListener('click', function () {
          form.reset();
          result.innerHTML = '';
          status.textContent = '';
          updateCounters();
        });
        out.appendChild(again);
        result.innerHTML = '';
        result.appendChild(out);
      });
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
      countWords: countWords,
      validateSar: validateSar,
    };
  }
})();
