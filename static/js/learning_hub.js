(function(){
  'use strict';

  var PROGRESS_KEY = 'acacia_progress_v1';
  var SM2_KEY = 'acacia_sm2_v1';
  var REVIEWS_KEY = 'acacia_reviews_v1';
  var FOCUS_KEY = 'acacia_focus_mode';
  var ADAPTIVE_KEY = 'acacia_adaptive_v1';

  // ── Helpers ──────────────────────────────────────────────────────────
  function loadJSON(key, def) {
    try { return JSON.parse(localStorage.getItem(key) || 'null') || def; }
    catch(e) { return def; }
  }
  function saveJSON(key, val) {
    try { localStorage.setItem(key, JSON.stringify(val)); } catch(e) {}
  }

  // ── Progress API sync (best-effort, localStorage fallback) ────────────
  var API_BASE = '/api';
  function syncProgress() {
    var p = loadJSON(PROGRESS_KEY, {});
    var slug = null;
    var btn = document.getElementById('mark-complete-btn');
    if (btn) slug = btn.getAttribute('data-track-lesson');
    if (!slug || !p[slug]) return;
    try {
      var body = JSON.stringify({url: slug, done: p[slug].done || false, ts: p[slug].ts || Date.now()});
      fetch(API_BASE + '/progress', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: body}).catch(function(){});
    } catch(e) {}
  }

  function loadProgressFromAPI() {
    var btn = document.getElementById('mark-complete-btn');
    var slug = btn ? btn.getAttribute('data-track-lesson') : null;
    if (!slug) return;
    try {
      fetch(API_BASE + '/progress?url=' + encodeURIComponent(slug)).then(function(r) { return r.json(); }).then(function(data) {
        if (data && data.result) {
          var p = loadJSON(PROGRESS_KEY, {});
          p[slug] = {done: data.result.done, ts: data.result.ts, date: data.result.ts ? new Date(data.result.ts).toISOString() : ''};
          saveJSON(PROGRESS_KEY, p);
        }
      }).catch(function(){});
    } catch(e) {}
  }

  // ── 1. Reading progress bar ──────────────────────────────────────────
  function initProgressBar() {
    var bar = document.getElementById('reading-progress');
    if (!bar) return;
    window.addEventListener('scroll', function() {
      var h = document.documentElement;
      var pct = (h.scrollTop || document.body.scrollTop) / (h.scrollHeight - h.clientHeight) * 100;
      bar.style.width = Math.min(pct, 100) + '%';
    }, {passive: true});
  }

  // ── 2. TOC scroll-spy ───────────────────────────────────────────────
  function initTocSpy() {
    var tocLinks = document.querySelectorAll('.toc-link');
    if (!tocLinks.length) return;
    var headings = [];
    tocLinks.forEach(function(link) {
      var id = link.getAttribute('href').slice(1);
      var el = document.getElementById(id);
      if (el) headings.push({el: el, link: link});
    });
    window.addEventListener('scroll', function() {
      var scrollY = window.scrollY + 120;
      var current = null;
      for (var i = headings.length - 1; i >= 0; i--) {
        if (headings[i].el.offsetTop <= scrollY) { current = headings[i]; break; }
      }
      tocLinks.forEach(function(l) { l.style.background = ''; l.style.color = ''; });
      if (current) {
        current.link.style.background = 'var(--color-bg)';
        current.link.style.color = 'var(--color-accent)';
      }
    }, {passive: true});
  }

  // ── 3. Focus mode ────────────────────────────────────────────────────
  function initFocusMode() {
    var btn = document.getElementById('focus-toggle');
    if (!btn) return;
    if (sessionStorage.getItem(FOCUS_KEY) === 'on') {
      document.body.classList.add('focus-mode');
    }
    btn.addEventListener('click', function() {
      document.body.classList.toggle('focus-mode');
      sessionStorage.setItem(FOCUS_KEY, document.body.classList.contains('focus-mode') ? 'on' : 'off');
    });
  }

  // ── 4. Inline flashcards (accordion in lesson body) ──────────────────
  function initInlineFlashcards() {
    document.querySelectorAll('.lesson-body .flashcard-card').forEach(function(card) {
      card.style.cursor = 'pointer';
      var def = card.querySelector('.mt-1');
      if (def) {
        def.style.display = 'none';
        def.style.marginTop = '0.75rem';
        def.style.paddingTop = '0.75rem';
        def.style.borderTop = '1px solid var(--color-border)';
      }
      var term = card.querySelector('.font-semibold');
      if (term) {
        var arrow = document.createElement('span');
        arrow.className = 'ml-auto text-xs transition-transform';
        arrow.style.color = 'var(--color-text-muted)';
        arrow.textContent = '\u25BC';
        term.style.display = 'flex';
        term.style.alignItems = 'center';
        term.appendChild(arrow);
      }
      card.addEventListener('click', function() {
        this.classList.toggle('active');
        if (def) def.style.display = def.style.display === 'none' ? 'block' : 'none';
        if (arrow) arrow.style.transform = this.classList.contains('active') ? 'rotate(180deg)' : '';
      });
    });
  }

  // ── 5. Flashcard grid shuffle ────────────────────────────────────────
  function initFlashcardShuffle() {
    var btn = document.getElementById('flashcard-shuffle');
    var grid = document.getElementById('flashcard-grid');
    if (!btn || !grid) return;
    btn.addEventListener('click', function() {
      var cards = Array.from(grid.children);
      for (var i = cards.length - 1; i > 0; i--) {
        var j = Math.floor(Math.random() * (i + 1));
        grid.appendChild(cards[j]);
        cards.splice(j, 1);
      }
    });
  }

  // ── 6. Section collapse: open parent details on TOC click ────────────
  function initSectionCollapse() {
    document.querySelectorAll('.toc-link').forEach(function(link) {
      link.addEventListener('click', function(e) {
        var id = this.getAttribute('href').slice(1);
        var target = document.getElementById(id);
        if (target) {
          var details = target.closest('details');
          if (details) details.open = true;
        }
      });
    });
  }

  // ── 7. Section progress tracking via IntersectionObserver ─────────────
  function initSectionProgress() {
    if (!('IntersectionObserver' in window)) return;
    var sections = document.querySelectorAll('.section-harvester');
    if (!sections.length) return;
    var obs = new IntersectionObserver(function(entries) {
      entries.forEach(function(entry) {
        var harvester = entry.target.closest('.section-harvester');
        if (!harvester) return;
        if (entry.isIntersecting) {
          harvester.classList.add('section-read');
        }
      });
    }, {threshold: 0.3});
    sections.forEach(function(s) { obs.observe(s); });
  }

  // ── 8. Flashcard review tracking ─────────────────────────────────────
  function initReviewTracking() {
    var btn = document.getElementById('mark-complete-btn');
    var slug = btn ? btn.getAttribute('data-track-lesson') : null;
    if (!slug || !document.querySelector('.flashcard-card-flip')) return;
    var reviews = loadJSON(REVIEWS_KEY, {});
    var key = '/' + slug.replace(/\/?index\.html$/, '') + '/';
    reviews[key] = { lastReview: Date.now() };
    saveJSON(REVIEWS_KEY, reviews);
  }

  // ── 7. Mark Complete ─────────────────────────────────────────────────
  function initMarkComplete() {
    var btn = document.getElementById('mark-complete-btn');
    if (!btn) return;
    var slug = btn.getAttribute('data-track-lesson');
    var textEl = document.getElementById('complete-btn-text');

    function loadProgress() { return loadJSON(PROGRESS_KEY, {}); }
    function saveProgress(p) { saveJSON(PROGRESS_KEY, p); }

    var p = loadProgress();
    if (p[slug] && p[slug].done) {
      textEl.textContent = 'Completed \u2713';
      btn.style.background = 'var(--color-text-muted)';
    }
    btn.addEventListener('click', function() {
      var p = loadProgress();
      if (!p[slug]) p[slug] = {};
      if (p[slug].done) {
        delete p[slug].done;
        textEl.textContent = 'Mark Complete';
        btn.style.background = 'var(--color-accent)';
      } else {
        p[slug].done = true;
        p[slug].date = new Date().toISOString();
        p[slug].ts = Date.now();
        textEl.textContent = 'Completed \u2713';
        btn.style.background = 'var(--color-text-muted)';
      }
      saveProgress(p);
      syncProgress();
    });
  }

  // ── 8. Quiz engine with SM-2 ─────────────────────────────────────────
  function initQuiz() {
    var section = document.getElementById('quiz-section');
    if (!section) return;
    try {
      var quizData = JSON.parse(section.getAttribute('data-quiz') || '{}');
      var lessonSlug = section.getAttribute('data-quiz-lesson') || 'unknown';
      if (!quizData.questions || !quizData.questions.length) return;

      var container = document.getElementById('quiz-container');
      var scoreEl = document.getElementById('quiz-score');
      var summaryEl = document.getElementById('quiz-summary');
      var retryBtn = document.getElementById('quiz-retry');
      var totalQ = quizData.questions.length;
      var answered = 0;
      var correct = 0;
      var questionStates = {};

      var sm2 = loadJSON(SM2_KEY, {});
      if (!sm2[lessonSlug]) sm2[lessonSlug] = {};
      quizData.questions.forEach(function(q, i) {
        if (!sm2[lessonSlug][i]) {
          sm2[lessonSlug][i] = {ef: 2.5, interval: 0, rep: 0, nextReview: 0};
        }
      });
      saveJSON(SM2_KEY, sm2);

      var now = Date.now();
      var dueCount = 0;
      for (var k in sm2[lessonSlug]) {
        if (sm2[lessonSlug][k].nextReview <= now) dueCount++;
      }
      if (dueCount === 0 && totalQ > 0) {
        for (var k in sm2[lessonSlug]) sm2[lessonSlug][k].nextReview = 0;
        saveJSON(SM2_KEY, sm2);
      }

      function resetQuiz() {
        answered = 0;
        correct = 0;
        questionStates = {};
        if (scoreEl) scoreEl.textContent = '';
        if (summaryEl) { summaryEl.className = 'mt-6 p-4 rounded-lg hidden'; summaryEl.innerHTML = ''; }
        if (retryBtn) retryBtn.className = 'mt-3 hidden px-4 py-2 text-sm font-semibold rounded-lg transition hover:opacity-80';
        container.querySelectorAll('input[type="radio"], input[type="checkbox"]').forEach(function(r){ r.checked = false; });
        container.querySelectorAll('label').forEach(function(l){ l.style.color = ''; l.style.fontWeight = ''; });
        container.querySelectorAll('.open-ended-reveal').forEach(function(el){ el.remove(); });
      }

      function updateScore() {
        if (scoreEl) scoreEl.textContent = correct + ' / ' + answered + ' correct';
        if (answered === totalQ && summaryEl) {
          var pct = Math.round(correct / totalQ * 100);
          var grade = pct >= 80 ? 'Excellent' : pct >= 60 ? 'Good' : pct >= 40 ? 'Fair' : 'Needs review';
          summaryEl.className = 'mt-6 p-4 rounded-lg';
          summaryEl.style.cssText = 'background:var(--color-surface);border:1px solid var(--color-border)';
          summaryEl.innerHTML = '<p class="text-lg font-bold" tabindex="-1" style="color:var(--color-text)">' + grade + ' \u2014 ' + correct + '/' + totalQ + ' (' + pct + '%)</p>';
          summaryEl.scrollIntoView({behavior:'smooth',block:'center'});
          setTimeout(function(){ summaryEl.querySelector('p').focus(); }, 100);
          if (retryBtn) retryBtn.className = 'mt-3 px-4 py-2 text-sm font-semibold rounded-lg transition hover:opacity-80';
        }
      }

      function sm2Update(i, isCorrect) {
        var s = sm2[lessonSlug][i];
        if (isCorrect) {
          s.rep++;
          if (s.rep === 1) s.interval = 1;
          else if (s.rep === 2) s.interval = 6;
          else s.interval = Math.round(s.interval * s.ef);
          if (s.rep > 1) s.ef = Math.max(1.3, s.ef + 0.1);
        } else {
          s.rep = 0;
          s.interval = 1;
          s.ef = Math.max(1.3, s.ef - 0.2);
        }
        s.nextReview = Date.now() + s.interval * 86400000;
        saveJSON(SM2_KEY, sm2);
        trackAdaptive(isCorrect);
      }

      // ── Adaptive difficulty tracking ──────────────────────────────
      function trackAdaptive(correct) {
        try {
          var ad = loadJSON(ADAPTIVE_KEY, {scores: [], level: 'beginner'});
          ad.scores.push(correct ? 1 : 0);
          if (ad.scores.length > 20) ad.scores = ad.scores.slice(-20);
          var sum = 0;
          for (var si = 0; si < ad.scores.length; si++) sum += ad.scores[si];
          var avg = sum / ad.scores.length;
          if (avg >= 0.8 && ad.level === 'beginner') ad.level = 'intermediate';
          else if (avg >= 0.8 && ad.level === 'intermediate') ad.level = 'advanced';
          else if (avg < 0.5 && ad.level === 'advanced') ad.level = 'intermediate';
          else if (avg < 0.5 && ad.level === 'intermediate') ad.level = 'beginner';
          saveJSON(ADAPTIVE_KEY, ad);
          document.querySelectorAll('.learn-card').forEach(function(card) {
            var diff = (card.getAttribute('data-difficulty') || 'beginner').toLowerCase();
            if (diff === ad.level) { card.style.opacity = '1'; card.style.filter = 'none'; }
            else { card.style.opacity = '0.5'; card.style.filter = 'grayscale(0.5)'; }
          });
        } catch(e) {}
      }

      if (retryBtn) retryBtn.addEventListener('click', resetQuiz);

      quizData.questions.forEach(function(q, i) {
        var div = document.createElement('div');
        div.className = 'mb-6 p-4 rounded-lg';
        div.style.background = 'var(--color-bg)';
        div.style.border = '1px solid var(--color-border)';

        var sch = sm2[lessonSlug][i];
        var nextIn = Math.max(0, Math.round((sch.nextReview - now) / 86400000));
        var schBadge = document.createElement('span');
        schBadge.className = 'float-right text-[10px] px-1.5 py-0.5 rounded ml-2';
        schBadge.style.cssText = 'background:var(--color-surface);color:var(--color-text-muted);border:1px solid var(--color-border)';
        if (sch.nextReview > now) {
          schBadge.textContent = 'Due in ' + (nextIn === 0 ? 'today' : nextIn + 'd');
        } else {
          schBadge.textContent = 'Due now';
          schBadge.style.borderColor = '#22c55e44';
        }

        var qP = document.createElement('p');
        qP.className = 'text-sm font-semibold mb-3';
        qP.style.color = 'var(--color-text)';
        qP.textContent = (i + 1) + '. ' + q.q;
        qP.appendChild(schBadge);
        div.appendChild(qP);

        var qtype = q.type || 'mc';

        if (qtype === 'open-ended') {
          var revealBtn = document.createElement('button');
          revealBtn.className = 'text-xs px-3 py-1.5 rounded-lg font-medium transition hover:opacity-80 mt-1';
          revealBtn.style.cssText = 'background:var(--color-surface);color:var(--color-accent);border:1px solid var(--color-border)';
          revealBtn.textContent = 'Reveal Answer';
          revealBtn.dataset.revealed = 'false';
          revealBtn.addEventListener('click', function() {
            if (this.dataset.revealed === 'true') return;
            this.dataset.revealed = 'true';
            if (questionStates[i]) return;
            questionStates[i] = true;
            answered++;
            correct++;
            var ans = document.createElement('div');
            ans.className = 'open-ended-reveal mt-3 p-3 rounded-lg text-sm';
            ans.style.cssText = 'background:#22c55e15;border:1px solid #22c55e44;color:var(--color-text)';
            ans.innerHTML = '<strong>Answer:</strong> ' + (q.answer_text || 'See article');
            this.parentNode.insertBefore(ans, this.nextSibling);
            this.textContent = 'Revealed \u2713';
            this.style.borderColor = '#22c55e44';
            sm2Update(i, true);
            updateScore();
          });
          div.appendChild(revealBtn);
        } else {
          // Multiple choice or True/False
          if (q.options && q.options.length) {
            q.options.forEach(function(opt, oi) {
              var label = document.createElement('label');
              label.className = 'flex items-center gap-3 py-2.5 px-3 rounded cursor-pointer text-sm transition min-h-[44px]';
              label.style.color = 'var(--color-text-secondary)';
              label.addEventListener('mouseenter', function(){ label.style.background = 'var(--color-surface)'; });
              label.addEventListener('mouseleave', function(){ label.style.background = ''; });

              var input = document.createElement('input');
              input.type = qtype === 'tf' ? 'checkbox' : 'radio';
              input.name = 'quiz-' + i;
              input.value = oi;
              input.className = 'shrink-0 w-4 h-4';

              input.addEventListener('change', function() {
                if (questionStates[i]) return;
                questionStates[i] = true;
                answered++;
                var isCorrect = (oi === q.a);
                var parent = this.closest('.mb-6');
                parent.querySelectorAll('label').forEach(function(l){ l.style.color = 'var(--color-text-secondary)'; });
                parent.querySelectorAll('input').forEach(function(r){ r.style.outline = 'none'; });
                if (isCorrect) {
                  label.style.color = '#22c55e';
                  label.style.fontWeight = '600';
                  correct++;
                } else {
                  label.style.color = '#ef4444';
                  var correctLabel = parent.querySelector('input[value="' + q.a + '"]');
                  if (correctLabel) {
                    correctLabel = correctLabel.closest('label');
                    if (correctLabel) { correctLabel.style.color = '#22c55e'; correctLabel.style.fontWeight = '600'; }
                  }
                }
                sm2Update(i, isCorrect);
                if (schBadge) schBadge.textContent = 'Next in ' + sm2[lessonSlug][i].interval + 'd';
                updateScore();
              });
              label.appendChild(input);
              label.appendChild(document.createTextNode(' ' + opt));
              div.appendChild(label);
            });
          }
        }
        container.appendChild(div);
      });
      updateScore();
    } catch(e) {}
  }

  // ── 9. Flashcard SM-2 rating (for flip-card flashcards) ──────────────
  function initFlashcardSM2() {
    var lessonSlug = null;
    var btn = document.getElementById('mark-complete-btn');
    if (btn) lessonSlug = btn.getAttribute('data-track-lesson');
    if (!lessonSlug) return;
    var grid = document.getElementById('flashcard-grid');
    if (!grid || !grid.querySelector('.flashcard-card-flip')) return;

    var sm2 = loadJSON(SM2_KEY, {});
    if (!sm2['fc_' + lessonSlug]) sm2['fc_' + lessonSlug] = {};
    saveJSON(SM2_KEY, sm2);

    grid.querySelectorAll('.flashcard-card-flip').forEach(function(card, idx) {
      var key = 'fc_' + idx;
      if (!sm2['fc_' + lessonSlug][key]) {
        sm2['fc_' + lessonSlug][key] = {ef: 2.5, interval: 0, rep: 0, nextReview: 0};
      }
      // Rating buttons appear on back side
      var back = card.querySelector('.flashcard-back');
      if (!back) return;

      var ratingDiv = document.createElement('div');
      ratingDiv.className = 'flex gap-2 mt-3 justify-center';
      var labels = ['Hard', 'Good', 'Easy'];
      var multipliers = [1.0, 1.5, 2.5];
      labels.forEach(function(label, li) {
        var btn = document.createElement('button');
        btn.textContent = label;
        btn.className = 'text-[10px] px-2 py-1 rounded font-medium';
        btn.style.cssText = 'background:var(--color-bg);color:var(--color-text-muted);border:1px solid var(--color-border);transition:all 0.15s';
        btn.addEventListener('mouseenter', function() { this.style.borderColor = 'var(--color-accent)'; });
        btn.addEventListener('mouseleave', function() { this.style.borderColor = 'var(--color-border)'; });
        btn.addEventListener('click', function(e) {
          e.stopPropagation();
          var s = sm2['fc_' + lessonSlug][key];
          s.rep++;
          if (s.rep === 1) s.interval = Math.round(1 * multipliers[li]);
          else if (s.rep === 2) s.interval = Math.round(6 * multipliers[li]);
          else s.interval = Math.round(s.interval * s.ef * multipliers[li] / 2.5);
          s.ef = Math.max(1.3, s.ef + (li - 1) * 0.15);
          s.nextReview = Date.now() + s.interval * 86400000;
          saveJSON(SM2_KEY, sm2);
          btn.textContent = '\u2713 ' + label;
          btn.style.opacity = '0.5';
          btn.style.pointerEvents = 'none';
          ratingDiv.querySelectorAll('button').forEach(function(b) { b.style.opacity = '0.4'; });
          this.style.opacity = '1';
          // Update review tracking
          var reviews = loadJSON(REVIEWS_KEY, {});
          var reviewKey = '/' + lessonSlug.replace(/\/?index\.html$/, '') + '/';
          if (!reviews[reviewKey]) reviews[reviewKey] = {};
          reviews[reviewKey][key] = { lastReview: Date.now(), interval: s.interval, ef: s.ef };
          saveJSON(REVIEWS_KEY, reviews);
        });
        ratingDiv.appendChild(btn);
      });
      back.appendChild(ratingDiv);
    });
  }

  // ── Init everything on DOMContentLoaded ──────────────────────────────
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  function init() {
    initProgressBar();
    initTocSpy();
    initFocusMode();
    initInlineFlashcards();
    initFlashcardShuffle();
    initReviewTracking();
    initMarkComplete();
    loadProgressFromAPI();
    initSectionCollapse();
    initSectionProgress();
    initQuiz();
    initFlashcardSM2();
  }

})();
