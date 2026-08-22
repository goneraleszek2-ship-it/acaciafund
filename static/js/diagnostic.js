
/* diagnostic.js */

/* diagnostic.js */

/* diagnostic.js */

/* diagnostic.js */

/* diagnostic.js */

/* diagnostic.js */

/* diagnostic.js */

/* diagnostic.js */
(function () {
  'use strict';

  /* ── Pure helpers (unit-tested via tests/test_diagnostic.js) ── */

  function scoreQuiz(answers, questions) {
    var correct = 0;
    for (var i = 0; i < questions.length; i++) {
      if (i >= answers.length) break;
      if (answers[i] === questions[i].correct) correct++;
    }
    return correct;
  }

  function levelForScore(correct, total) {
    if (!total) return 'beginner';
    var ratio = correct / total;
    if (ratio >= 0.75) return 'expert';
    if (ratio >= 0.4) return 'intermediate';
    return 'beginner';
  }

  function levelLabel(level) {
    var labels = { beginner: 'Beginner', intermediate: 'Intermediate', expert: 'Expert' };
    return labels[level] || level;
  }

  function setLearningMode(mode) {
    try {
      localStorage.setItem('acacia_learning_mode', mode);
    } catch (_) {}
    if (typeof document !== 'undefined') {
      document.body.classList.remove('mode-beginner', 'mode-intermediate', 'mode-expert');
      document.body.classList.add('mode-' + mode);
    }
  }

  /* ── Page wiring ── */

  function renderQuestion(container, q, index) {
    var fieldset = document.createElement('fieldset');
    fieldset.className = 'diagnostic-question';
    fieldset.dataset.index = index;
    fieldset.innerHTML =
      '<legend class="diagnostic-qtext"><span class="diagnostic-tier diagnostic-tier-' + q.tier + '">' + q.tier +
      '</span> ' + (index + 1) + '. ' + q.question + '</legend>';
    for (var o = 0; o < q.options.length; o++) {
      var label = document.createElement('label');
      label.className = 'diagnostic-option';
      label.innerHTML = '<input type="radio" name="q' + index + '" value="' + o + '"> ' + q.options[o];
      fieldset.appendChild(label);
    }
    container.appendChild(fieldset);
  }

  function renderResults(root, questions, correct) {
    var level = levelForScore(correct, questions.length);
    setLearningMode(level);
    var done = { level: level, correct: correct, total: questions.length, at: Date.now() };
    try { localStorage.setItem('acacia_diagnostic_done', JSON.stringify(done)); } catch (_) {}

    var card = document.createElement('section');
    card.className = 'diagnostic-results';
    card.innerHTML =
      '<h2>Your placement: ' + levelLabel(level) + '</h2>' +
      '<p class="diagnostic-score">You answered <strong>' + correct + ' / ' + questions.length +
      '</strong> correctly.</p>' +
      '<p class="diagnostic-note">Your learning mode is set to <strong>' + levelLabel(level) +
      '</strong> site-wide (adjustable via the mode selector in the footer). ' +
      'Your Study Queue is now tuned to your level.</p>' +
      '<p class="diagnostic-cta"><a class="btn" href="/study/">Open Study Queue</a> ' +
      '<a class="btn btn-secondary" href="/review/">Review Dashboard</a></p>';
    root.appendChild(card);
  }

  function init() {
    var app = document.getElementById('diagnostic-app');
    if (!app) return;
    var script = document.querySelector('script[src*="diagnostic.js"]');
    var prefix = script ? script.src.replace(/js\/\w+\.js.*$/, '') : '';
    var list = document.createElement('div');
    list.id = 'diagnostic-list';
    app.appendChild(list);

    var payloadPath = (prefix || '') + 'static/diagnostic_questions.json';
    var answers = [];
    var questions = [];
    var submit = document.getElementById('diagnostic-submit');
    var status = document.getElementById('diagnostic-status');
    var done = null;
    try { done = JSON.parse(localStorage.getItem('acacia_diagnostic_done') || 'null'); } catch (_) {}

    fetch(payloadPath)
      .then(function (r) { return r.json(); })
      .then(function (payload) {
        questions = payload.questions || [];
        payload.pillars.forEach(function (p) {
          var group = document.createElement('h3');
          group.className = 'diagnostic-pillar';
          group.textContent = p.label;
          list.appendChild(group);
          questions.forEach(function (q, i) {
            if (q.pillar === p.key) renderQuestion(list, q, i);
          });
        });
        if (submit && done && done.level) {
          status.textContent = 'Completed ' + new Date(done.at).toLocaleDateString() + ' — placement: ' + levelLabel(done.level) + '. Retake to update.';
        }
      })
      .catch(function () {
        if (status) status.textContent = 'Could not load diagnostic questions.';
      });

    if (submit) {
      submit.addEventListener('click', function () {
        answers = questions.map(function (q, i) {
          var selected = list.querySelector('input[name="q' + i + '"]:checked');
          return selected === null ? -1 : parseInt(selected.value, 10);
        });
        var skipped = answers.filter(function (a) { return a < 0; }).length;
        if (skipped > 0) {
          if (status) status.textContent = skipped + ' question(s) unanswered — answer all questions to place yourself.';
          return;
        }
        var correct = scoreQuiz(answers, questions);
        list.style.display = 'none';
        if (submit) submit.disabled = true;
        renderResults(app, questions, correct);
      });
    }
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
      scoreQuiz: scoreQuiz,
      levelForScore: levelForScore,
      levelLabel: levelLabel,
      setLearningMode: setLearningMode,
    };
  }
})();
