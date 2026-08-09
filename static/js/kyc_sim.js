
/* kyc_sim.js */

/* kyc_sim.js */

/* kyc_sim.js */
/* kyc_sim.js */

/* kyc_sim.js */

/* kyc_sim.js */
(function () {
  'use strict';

  /* ── Pure helpers (unit-tested via tests/test_kyc_sim.js) ── */

  function isComplete(step, selections) {
    if (step.kind === 'multi') {
      var picked = selections || [];
      var req = step.correct || [];
      return req.every(function (r) { return picked.indexOf(r) !== -1; });
    }
    if (step.kind === 'single') {
      return !!selections;
    }
    return false;
  }

  function correctSet(step, selections) {
    if (step.kind === 'multi') {
      var picked = selections || [];
      var req = step.correct || [];
      var ok = req.every(function (r) { return picked.indexOf(r) !== -1; });
      var noExtra = picked.length === req.length;
      return { pass: ok && noExtra, missing: req.filter(function (r) { return picked.indexOf(r) === -1; }) };
    }
    return { pass: (selections || '') === step.correct, missing: [] };
  }

  function progress(stepIdx, total) {
    return Math.round(((stepIdx + 1) / total) * 100);
  }

  /* ── Page wiring ── */

  function init() {
    var cards = document.querySelectorAll('[data-kyc-sim]');
    if (!cards.length) return;

    cards.forEach(function (card) {
      var ex = {};
      try { ex = JSON.parse(card.getAttribute('data-ex') || '{}'); } catch (_) {}
      if (!ex.steps || !ex.steps.length) return;

      var steps = ex.steps;
      var state = { idx: 0, selections: {}, revealed: {} };

      var stepsEl = card.querySelector('[data-sim-steps]');
      var bodyEl = card.querySelector('[data-sim-body]');
      var outcomeEl = card.querySelector('[data-sim-outcome]');

      function renderSteps() {
        stepsEl.innerHTML = '';
        steps.forEach(function (s, i) {
          var el = document.createElement('span');
          el.className = 'sim-step' + (i < state.idx ? ' sim-step-done' : '') + (i === state.idx ? ' sim-step-active' : '');
          el.textContent = String(i + 1);
          el.setAttribute('aria-label', s.question);
          stepsEl.appendChild(el);
        });
      }

      function renderStep() {
        var step = steps[state.idx];
        bodyEl.innerHTML = '';
        var wrap = document.createElement('div');
        var q = document.createElement('p');
        q.className = 'text-sm font-semibold mb-3 text-default';
        q.textContent = 'Step ' + (state.idx + 1) + ': ' + step.question;
        wrap.appendChild(q);

        if (step.kind === 'multi') {
          step.options.forEach(function (opt) {
            var label = document.createElement('label');
            label.className = 'sandbox-check';
            var box = document.createElement('input');
            box.type = 'checkbox';
            box.value = opt;
            var sel = state.selections[step.id] || [];
            box.checked = sel.indexOf(opt) !== -1;
            box.addEventListener('change', function () {
              var cur = state.selections[step.id] || [];
              if (box.checked) {
                if (cur.indexOf(opt) === -1) cur.push(opt);
              } else {
                cur = cur.filter(function (v) { return v !== opt; });
              }
              state.selections[step.id] = cur;
            });
            label.appendChild(box);
            label.appendChild(document.createTextNode(opt));
            wrap.appendChild(label);
          });
        } else {
          step.options.forEach(function (opt) {
            var label = document.createElement('label');
            label.className = 'sandbox-check';
            var radio = document.createElement('input');
            radio.type = 'radio';
            radio.name = step.id;
            radio.value = opt;
            if (state.selections[step.id] === opt) radio.checked = true;
            radio.addEventListener('change', function () {
              state.selections[step.id] = opt;
            });
            label.appendChild(radio);
            label.appendChild(document.createTextNode(opt));
            wrap.appendChild(label);
          });
        }

        var feedback = document.createElement('p');
        feedback.className = 'sandbox-feedback hidden text-sm mt-3';
        wrap.appendChild(feedback);

        var row = document.createElement('div');
        row.className = 'flex flex-wrap items-center gap-2 mt-4';
        var nextBtn = document.createElement('button');
        nextBtn.type = 'button';
        nextBtn.className = 'btn-primary-sm';
        nextBtn.textContent = state.idx === steps.length - 1 ? 'Finish' : 'Check answer';
        var checked = false;
        nextBtn.addEventListener('click', function () {
          var step2 = steps[state.idx];
          if (checked) {
            state.idx++;
            if (state.idx < steps.length) {
              renderStep();
            } else {
              renderOutcome();
            }
            return;
          }
          var sel = state.selections[step2.id];
          if (!isComplete(step2, sel)) {
            feedback.textContent = 'Select ' + (step2.kind === 'multi' ? 'all required documents' : 'an answer') + ' first.';
            feedback.className = 'sandbox-feedback sandbox-err text-sm mt-3';
            return;
          }
          var verdict = correctSet(step2, sel);
          if (verdict.pass) {
            feedback.textContent = 'Correct. ' + step2.feedback;
            feedback.className = 'sandbox-feedback sandbox-ok text-sm mt-3';
            checked = true;
            nextBtn.textContent = state.idx === steps.length - 1 ? 'Finish' : 'Next step';
          } else {
            var miss = verdict.missing.length ? ' Missing: ' + verdict.missing.join(', ') + '.' : '';
            feedback.textContent = 'Not quite.' + miss + ' ' + step2.feedback;
            feedback.className = 'sandbox-feedback sandbox-err text-sm mt-3';
          }
        });

        var skipBtn = document.createElement('button');
        skipBtn.type = 'button';
        skipBtn.className = 'btn-ghost-sm';
        skipBtn.textContent = 'Reveal answer';
        skipBtn.addEventListener('click', function () {
          state.revealed[step2.id] = true;
          var sel = state.selections[step2.id];
          var verdict = correctSet(step2, sel);
          if (verdict.pass) {
            feedback.textContent = 'Correct. ' + step2.feedback;
            feedback.className = 'sandbox-feedback sandbox-ok text-sm mt-3';
          } else {
            feedback.textContent = 'Reference answer: ' + (step2.kind === 'multi' ? step2.correct.join(', ') : step2.correct) + '. ' + step2.feedback;
            feedback.className = 'sandbox-feedback text-sm mt-3';
          }
        });

        row.appendChild(nextBtn);
        row.appendChild(skipBtn);
        wrap.appendChild(row);
        bodyEl.appendChild(wrap);
        renderSteps();
      }

      function renderOutcome() {
        bodyEl.innerHTML = '';
        stepsEl.innerHTML = '';
        var out = document.createElement('div');
        out.className = 'sandbox-ok-card';
        var h = document.createElement('h4');
        h.className = 'text-sm font-bold mb-2';
        h.textContent = ex.outcome.title;
        out.appendChild(h);
        var p = document.createElement('p');
        p.className = 'text-sm';
        p.textContent = ex.outcome.text;
        out.appendChild(p);
        var again = document.createElement('button');
        again.type = 'button';
        again.className = 'btn-ghost-sm mt-3';
        again.textContent = 'Restart simulator';
        again.addEventListener('click', function () {
          state = { idx: 0, selections: {}, revealed: {} };
          renderStep();
          outcomeEl.innerHTML = '';
        });
        out.appendChild(again);
        outcomeEl.innerHTML = '';
        outcomeEl.appendChild(out);
      }

      renderStep();
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
      isComplete: isComplete,
      correctSet: correctSet,
      progress: progress,
    };
  }
})();
