(function () {
  'use strict';

  function initPretestGate() {
    var gateEl = document.getElementById('pretest-gate');
    var bodyEl = document.getElementById('lesson-body');
    if (!gateEl || !bodyEl) return;

    var quizSection = document.querySelector('[data-quiz]');
    if (!quizSection) {
      bodyEl.style.display = 'block';
      gateEl.style.display = 'none';
      return;
    }

    var key = 'acacia_pretest_' + (window.location.pathname || '');
    var attempted = false;
    try { attempted = sessionStorage.getItem(key) === 'true'; } catch (_) {}

    if (attempted) {
      gateEl.style.display = 'none';
      bodyEl.style.display = 'block';
      return;
    }

    bodyEl.style.display = 'none';

    var quizData;
    try { quizData = JSON.parse(quizSection.getAttribute('data-quiz') || '[]'); } catch (_) {}
    if (!quizData || !quizData.length) {
      bodyEl.style.display = 'block';
      gateEl.style.display = 'none';
      return;
    }

    var firstQuestion = quizData[0];
    if (!firstQuestion || !firstQuestion.question || !firstQuestion.options) {
      bodyEl.style.display = 'block';
      gateEl.style.display = 'none';
      return;
    }

    var questionEl = document.getElementById('pretest-question');
    var feedbackEl = document.getElementById('pretest-feedback');
    var revealBtn = document.getElementById('pretest-reveal');
    var showBtn = document.getElementById('pretest-show-content');

    var qHtml = '<p class="text-sm font-semibold mb-2" style="color:var(--color-text)">' +
      (firstQuestion.question || '') + '</p><div class="space-y-2">';

    (firstQuestion.options || []).forEach(function (opt, i) {
      var correct = false;
      if (typeof opt === 'object') {
        correct = opt.correct === true;
        opt = opt.label || opt.text || opt.answer || '';
      } else if (Array.isArray(firstQuestion.correct) && firstQuestion.correct.indexOf(i) >= 0) {
        correct = true;
      }
      qHtml += '<div class="pretest-option p-3 rounded text-sm cursor-pointer transition" ' +
        'data-correct="' + correct + '" data-index="' + i + '" ' +
        'style="background:var(--color-surface);border:2px solid var(--color-border);color:var(--color-text)">' +
        opt + '</div>';
    });
    qHtml += '</div>';
    questionEl.innerHTML = qHtml;

    var correctIndexes = [];
    (firstQuestion.options || []).forEach(function (opt, i) {
      if (typeof opt === 'object' && opt.correct === true) correctIndexes.push(i);
    });
    if (Array.isArray(firstQuestion.correct)) correctIndexes = firstQuestion.correct;

    function showCorrect() {
      var options = questionEl.querySelectorAll('.pretest-option');
      options.forEach(function (opt, i) {
        opt.style.pointerEvents = 'none';
        if (correctIndexes.indexOf(i) >= 0) {
          opt.style.borderColor = '#22c55e';
          opt.style.background = 'color-mix(in srgb, #22c55e 10%, transparent)';
        }
      });
    }

    function handleAnswer(selected) {
      showCorrect();
      var selectedCorrect = selected && selected.dataset.correct === 'true';
      var feedback = firstQuestion.feedback || '';
      if (!feedback) {
        feedback = selectedCorrect
          ? 'Correct! You can skip ahead or read the lesson to reinforce.'
          : 'Not quite. Read the lesson below to learn more.';
      }
      feedbackEl.textContent = feedback;
      feedbackEl.classList.remove('hidden');
      revealBtn.classList.add('hidden');
      showBtn.classList.remove('hidden');
    }

    questionEl.querySelectorAll('.pretest-option').forEach(function (opt) {
      opt.addEventListener('click', function () {
        if (!showBtn.classList.contains('hidden')) return;
        handleAnswer(opt);
      });
    });

    revealBtn.addEventListener('click', function () {
      showCorrect();
      var feedback = firstQuestion.feedback || 'The correct answer is highlighted. Read the lesson below to deepen your understanding.';
      feedbackEl.textContent = feedback;
      feedbackEl.classList.remove('hidden');
      revealBtn.classList.add('hidden');
      showBtn.classList.remove('hidden');
    });

    if (firstQuestion.options && firstQuestion.options.length > 0) {
      revealBtn.classList.remove('hidden');
    }

    showBtn.addEventListener('click', function () {
      try { sessionStorage.setItem(key, 'true'); } catch (_) {}
      gateEl.style.display = 'none';
      bodyEl.style.display = 'block';
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initPretestGate);
  } else {
    initPretestGate();
  }
})();
