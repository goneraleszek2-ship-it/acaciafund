/* ═══════════════════════════════════════════════════════════════
   AcaciaFund Learning Hub — SM-2 Spaced Repetition + Quiz + Flashcards
   ═══════════════════════════════════════════════════════════════ */

(function () {
  'use strict';

  /* ── SM-2 Scheduler ─────────────────────────────────────────── */

  const STORAGE_KEY = 'acacia_sm2';
  const HISTORY_KEY = 'acacia_review_history';
  const STREAK_KEY  = 'acacia_streak';

  class SM2Scheduler {
    constructor() {
      this.cards = {};
      this._load();
    }

    _load() {
      try {
        const raw = localStorage.getItem(STORAGE_KEY);
        if (raw) this.cards = JSON.parse(raw);
      } catch (_) { this.cards = {}; }
    }

    save() {
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(this.cards));
      } catch (_) {}
    }

    getCard(id) {
      if (!this.cards[id]) {
        this.cards[id] = {
          ease: 2.5,
          interval: 0,
          reps: 0,
          due: Date.now(),
          lastReview: 0,
        };
      }
      return this.cards[id];
    }

    /* grade: 0=Again, 1=Hard, 2=Good, 3=Easy */
    review(id, grade) {
      const c = this.getCard(id);
      const now = Date.now();

      if (grade < 2) {
        c.reps = 0;
        c.interval = 1;
      } else {
        if (c.reps === 0) {
          c.interval = 1;
        } else if (c.reps === 1) {
          c.interval = 6;
        } else {
          c.interval = Math.round(c.interval * c.ease);
        }
        c.reps++;
      }

      c.ease += 0.1 - (3 - grade) * (0.08 + (3 - grade) * 0.02);
      c.ease = Math.max(1.3, c.ease);

      c.due = now + c.interval * 86400000;
      c.lastReview = now;
      this.save();
      this._recordHistory(now);
      return c;
    }

    isDue(id) {
      return this.getCard(id).due <= Date.now();
    }

    getDueCards(ids) {
      const now = Date.now();
      return ids
        .filter(id => this.getCard(id).due <= now)
        .sort((a, b) => this.getCard(a).due - this.getCard(b).due);
    }

    getStats(ids) {
      const now = Date.now();
      let due = 0, learning = 0, mastered = 0;
      for (const id of ids) {
        const c = this.getCard(id);
        if (c.due <= now) due++;
        else if (c.reps > 0 && c.interval < 21) learning++;
        else if (c.reps > 0) mastered++;
      }
      return { total: ids.length, due, learning, mastered };
    }

    /* ── History / streak ── */
    _recordHistory(ts) {
      const day = new Date(ts).toISOString().slice(0, 10);
      let hist = [];
      try { hist = JSON.parse(localStorage.getItem(HISTORY_KEY) || '[]'); } catch (_) {}
      if (!hist.includes(day)) hist.push(day);
      if (hist.length > 365) hist = hist.slice(-365);
      localStorage.setItem(HISTORY_KEY, JSON.stringify(hist));
    }

    getStreak() {
      let hist = [];
      try { hist = JSON.parse(localStorage.getItem(HISTORY_KEY) || '[]'); } catch (_) {}
      if (!hist.length) return 0;
      const today = new Date().toISOString().slice(0, 10);
      const yesterday = new Date(Date.now() - 86400000).toISOString().slice(0, 10);
      if (!hist.includes(today) && !hist.includes(yesterday)) return 0;
      let streak = 0;
      let d = hist.includes(today) ? new Date() : new Date(Date.now() - 86400000);
      while (true) {
        const key = d.toISOString().slice(0, 10);
        if (hist.includes(key)) {
          streak++;
          d = new Date(d.getTime() - 86400000);
        } else break;
      }
      return streak;
    }

    getHistory() {
      try { return JSON.parse(localStorage.getItem(HISTORY_KEY) || '[]'); } catch (_) { return []; }
    }

    reset(id) {
      delete this.cards[id];
      this.save();
    }
  }

  /* ── Quiz Engine ────────────────────────────────────────────── */

  class QuizEngine {
    constructor(data, lessonPath) {
      this.questions = (data && data.questions) || [];
      this.lessonPath = lessonPath || '';
      this.current = 0;
      this.score = 0;
      this.answered = [];
    }

    render(container, scoreEl, summaryEl, retryBtn) {
      if (!this.questions.length) return;
      container.innerHTML = '';

      const q = this.questions[this.current];
      const div = document.createElement('div');
      div.className = 'ghost-card p-4';
      div.setAttribute('role', 'group');
      div.setAttribute('aria-label', `Question ${this.current + 1} of ${this.questions.length}`);

      const level = q.level || '';
      const levelColors = {
        remember: '#3b82f6', understand: '#22c55e', apply: '#f59e0b',
        analyze: '#a855f7', evaluate: '#ef4444', create: '#6366f1',
      };
      const lc = levelColors[level] || 'var(--color-accent)';

      let html = '';
      if (level) {
        html += `<span class="inline-block px-2 py-0.5 text-xs font-semibold rounded mb-3" style="background:color-mix(in srgb, ${lc} 15%, transparent);color:${lc}">${level.charAt(0).toUpperCase() + level.slice(1)}</span>`;
      }
      html += `<p class="text-sm font-medium mb-4" style="color:var(--color-text)">${this._esc(q.q)}</p>`;

      if (q.type === 'open-ended') {
        html += `<textarea id="quiz-open-input" class="w-full p-3 text-sm rounded-lg border" style="background:var(--color-bg);border-color:var(--color-border);color:var(--color-text)" rows="3" placeholder="Type your answer..."></textarea>`;
        html += `<button class="quiz-submit mt-3 px-4 py-2 text-sm font-semibold rounded-lg" style="background:var(--color-accent);color:#fff">Submit</button>`;
      } else {
        html += '<div class="space-y-2">';
        (q.options || []).forEach((opt, i) => {
          html += `<label class="quiz-option flex items-center gap-3 p-3 rounded-lg cursor-pointer transition" style="background:var(--color-bg);border:1px solid var(--color-border)" tabindex="0" data-idx="${i}">
            <span class="quiz-radio shrink-0" style="width:1.25em;height:1.25em;border-radius:50%;border:2px solid var(--color-text-muted);display:inline-flex;align-items:center;justify-content:center"></span>
            <span class="text-sm" style="color:var(--color-text)">${this._esc(opt)}</span>
          </label>`;
        });
        html += '</div>';
      }

      div.innerHTML = html;
      container.appendChild(div);

      if (q.type === 'open-ended') {
        div.querySelector('.quiz-submit').addEventListener('click', () => this._submitOpen(container, scoreEl, summaryEl, retryBtn));
      } else {
        div.querySelectorAll('.quiz-option').forEach(opt => {
          opt.addEventListener('click', () => this._selectOption(opt, div));
          opt.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); this._selectOption(opt, div); }});
        });
      }

      scoreEl.textContent = `Question ${this.current + 1} / ${this.questions.length}`;
    }

    _selectOption(opt, container) {
      const idx = parseInt(opt.dataset.idx);
      const q = this.questions[this.current];
      const correct = q.a;
      const options = container.querySelectorAll('.quiz-option');
      options.forEach((o, i) => {
        o.style.pointerEvents = 'none';
        if (i === correct) {
          o.style.borderColor = '#22c55e';
          o.style.background = 'color-mix(in srgb, #22c55e 10%, transparent)';
          o.querySelector('.quiz-radio').style.borderColor = '#22c55e';
          o.querySelector('.quiz-radio').innerHTML = '<svg class="icon-sm" fill="none" stroke="#22c55e" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7"/></svg>';
        } else if (i === idx && i !== correct) {
          o.style.borderColor = '#ef4444';
          o.style.background = 'color-mix(in srgb, #ef4444 10%, transparent)';
          o.querySelector('.quiz-radio').style.borderColor = '#ef4444';
          o.querySelector('.quiz-radio').innerHTML = '<svg class="icon-sm" fill="none" stroke="#ef4444" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M6 18L18 6M6 6l12 12"/></svg>';
        }
      });

      if (idx === correct) this.score++;
      this.answered.push({ q: this.current, correct: idx === correct });

      setTimeout(() => this._advance(), 800);
    }

    _submitOpen(container, scoreEl, summaryEl, retryBtn) {
      this.answered.push({ q: this.current, correct: true });
      this.score++;
      this._advance();
    }

    _advance() {
      this.current++;
      if (this.current >= this.questions.length) {
        this._showSummary();
      }
    }

    _showSummary() {
      const pct = Math.round((this.score / this.questions.length) * 100);
      const summaryEl = document.getElementById('quiz-summary');
      const retryBtn = document.getElementById('quiz-retry');
      const scoreEl = document.getElementById('quiz-score');
      const container = document.getElementById('quiz-container');

      if (summaryEl) {
        summaryEl.classList.remove('hidden');
        summaryEl.innerHTML = `<p class="text-sm font-semibold" style="color:var(--color-text)">You scored <strong>${this.score}/${this.questions.length}</strong> (${pct}%)</p>`;
      }
      if (retryBtn) retryBtn.classList.remove('hidden');
      if (scoreEl) scoreEl.textContent = `Final Score: ${this.score}/${this.questions.length}`;
      if (container) container.innerHTML = '';

      this._persistResult(pct);
    }

    _persistResult(pct) {
      try {
        const key = 'acacia_quiz_results';
        let results = JSON.parse(localStorage.getItem(key) || '[]');
        results.push({ lesson: this.lessonPath, score: pct, date: new Date().toISOString() });
        if (results.length > 500) results = results.slice(-500);
        localStorage.setItem(key, JSON.stringify(results));
      } catch (_) {}
    }

    _esc(s) {
      const d = document.createElement('div');
      d.textContent = s || '';
      return d.innerHTML;
    }
  }

  /* ── Flashcard Web Component ────────────────────────────────── */

  class AcaciaFlashcard extends HTMLElement {
    connectedCallback() {
      const term = this.getAttribute('data-term') || '';
      const def  = this.getAttribute('data-definition') || '';
      const id   = this.getAttribute('data-card-id') || '';
      const generate = this.hasAttribute('data-generate');

      if (generate) {
        this._renderGeneration(term, def, id);
      } else {
        this._renderStandard(term, def, id);
      }
    }

    _renderStandard(term, def, id) {
      this.innerHTML = `
        <div class="flashcard-card-flip ghost-card cursor-pointer" role="button" tabindex="0"
             aria-label="Flashcard: ${this._esc(term)}. Press Space to flip."
             style="min-height:140px">
          <div class="flashcard-inner">
            <div class="flashcard-front rounded-lg p-4" style="background:var(--color-surface);border:1px solid var(--color-border)">
              <div class="flex items-start gap-2">
                <svg class="icon-inline mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" style="color:var(--color-accent)"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"/></svg>
                <span class="font-semibold text-sm" style="color:var(--color-text)">${this._esc(term)}</span>
              </div>
              <p class="mt-2 text-[11px]" style="color:var(--color-text-muted)">Tap or press Space to reveal</p>
            </div>
            <div class="flashcard-back rounded-lg p-4" style="background:var(--color-accent);color:#fff">
              <div class="flex items-start gap-2">
                <svg class="icon-inline mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
                <span class="text-sm flashcard-back-text">${this._esc(def)}</span>
              </div>
            </div>
          </div>
          <div class="flashcard-grade-bar hidden mt-2 flex gap-2 justify-center" role="group" aria-label="Grade this card">
            <button data-grade="0" class="grade-btn px-3 py-1.5 text-xs font-semibold rounded-lg" style="background:color-mix(in srgb, #ef4444 15%, transparent);color:#ef4444;min-width:44px;min-height:44px">Again</button>
            <button data-grade="1" class="grade-btn px-3 py-1.5 text-xs font-semibold rounded-lg" style="background:color-mix(in srgb, #f59e0b 15%, transparent);color:#f59e0b;min-width:44px;min-height:44px">Hard</button>
            <button data-grade="2" class="grade-btn px-3 py-1.5 text-xs font-semibold rounded-lg" style="background:color-mix(in srgb, #22c55e 15%, transparent);color:#22c55e;min-width:44px;min-height:44px">Good</button>
            <button data-grade="3" class="grade-btn px-3 py-1.5 text-xs font-semibold rounded-lg" style="background:color-mix(in srgb, #3b82f6 15%, transparent);color:#3b82f6;min-width:44px;min-height:44px">Easy</button>
          </div>
        </div>`;

      this._attachStandardEvents(id);
    }

    _renderGeneration(term, def, id) {
      this.innerHTML = `
        <div class="flashcard-card-flip ghost-card" style="min-height:140px">
          <div class="flashcard-inner">
            <div class="flashcard-front rounded-lg p-4" style="background:var(--color-surface);border:1px solid var(--color-border)">
              <div class="flex items-start gap-2 mb-3">
                <svg class="icon-inline mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" style="color:var(--color-accent)"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/></svg>
                <span class="font-semibold text-sm" style="color:var(--color-text)">${this._esc(term)}</span>
              </div>
              <textarea class="gen-answer w-full rounded p-2 text-sm" rows="3"
                placeholder="Write your answer here..."
                style="background:var(--color-bg);color:var(--color-text);border:1px solid var(--color-border);resize:vertical;font-family:inherit;width:100%;box-sizing:border-box"></textarea>
              <button class="gen-reveal mt-2 px-3 py-1.5 text-xs font-semibold rounded-lg" style="background:var(--color-accent);color:#fff;border:none;cursor:pointer">Reveal Answer</button>
            </div>
            <div class="flashcard-back rounded-lg p-4" style="background:var(--color-accent);color:#fff">
              <div class="space-y-3">
                <div>
                  <p class="text-[11px] opacity-80 mb-1">Your answer:</p>
                  <div class="gen-user-answer text-sm rounded p-2" style="background:rgba(0,0,0,0.15)"></div>
                </div>
                <div>
                  <p class="text-[11px] opacity-80 mb-1">Correct answer:</p>
                  <div class="flex items-start gap-2">
                    <svg class="icon-inline mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
                    <span class="text-sm flashcard-back-text">${this._esc(def)}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div class="flashcard-grade-bar hidden mt-2 flex gap-2 justify-center" role="group" aria-label="Grade this card">
            <button data-grade="0" class="grade-btn px-3 py-1.5 text-xs font-semibold rounded-lg" style="background:color-mix(in srgb, #ef4444 15%, transparent);color:#ef4444;min-width:44px;min-height:44px">Again</button>
            <button data-grade="1" class="grade-btn px-3 py-1.5 text-xs font-semibold rounded-lg" style="background:color-mix(in srgb, #f59e0b 15%, transparent);color:#f59e0b;min-width:44px;min-height:44px">Hard</button>
            <button data-grade="2" class="grade-btn px-3 py-1.5 text-xs font-semibold rounded-lg" style="background:color-mix(in srgb, #22c55e 15%, transparent);color:#22c55e;min-width:44px;min-height:44px">Good</button>
            <button data-grade="3" class="grade-btn px-3 py-1.5 text-xs font-semibold rounded-lg" style="background:color-mix(in srgb, #3b82f6 15%, transparent);color:#3b82f6;min-width:44px;min-height:44px">Easy</button>
          </div>
        </div>`;

      this._attachGenerationEvents(id);
    }

    _attachStandardEvents(id) {
      const flipEl = this.querySelector('.flashcard-card-flip');
      const gradeBar = this.querySelector('.flashcard-grade-bar');

      flipEl.addEventListener('click', () => this._flip(flipEl, gradeBar));
      flipEl.addEventListener('keydown', (e) => {
        if (e.key === ' ' || e.key === 'Enter') { e.preventDefault(); this._flip(flipEl, gradeBar); }
        if (gradeBar && !gradeBar.classList.contains('hidden')) {
          if (e.key >= '0' && e.key <= '3') {
            e.preventDefault();
            this._grade(parseInt(e.key), id);
          }
        }
      });

      if (gradeBar) {
        gradeBar.querySelectorAll('.grade-btn').forEach(btn => {
          btn.addEventListener('click', (e) => {
            e.stopPropagation();
            this._grade(parseInt(btn.dataset.grade), id);
          });
        });
      }
    }

    _attachGenerationEvents(id) {
      const flipEl = this.querySelector('.flashcard-card-flip');
      const gradeBar = this.querySelector('.flashcard-grade-bar');
      const textarea = this.querySelector('.gen-answer');
      const revealBtn = this.querySelector('.gen-reveal');

      function doReveal() {
        const userAnswer = (textarea.value || '').trim();
        const userDisplay = flipEl.querySelector('.gen-user-answer');
        if (userDisplay) {
          userDisplay.textContent = userAnswer || '(no answer written)';
        }
        flipEl.classList.add('flipped');
        if (gradeBar) gradeBar.classList.remove('hidden');
      }

      revealBtn.addEventListener('click', (e) => { e.stopPropagation(); doReveal(); });
      textarea.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
          e.preventDefault();
          doReveal();
        }
        e.stopPropagation();
      });

      if (gradeBar) {
        gradeBar.querySelectorAll('.grade-btn').forEach(btn => {
          btn.addEventListener('click', (e) => {
            e.stopPropagation();
            this._grade(parseInt(btn.dataset.grade), id);
          });
        });
      }
    }

    _flip(flipEl, gradeBar) {
      flipEl.classList.toggle('flipped');
      if (flipEl.classList.contains('flipped') && gradeBar) {
        gradeBar.classList.remove('hidden');
      }
    }

    _grade(grade, id) {
      if (id && window._acaciaSM2) {
        window._acaciaSM2.review(id, grade);
      }
      this.dispatchEvent(new CustomEvent('card-graded', { detail: { grade, id }, bubbles: true }));
      this.classList.add('card-graded');
      setTimeout(() => this.remove(), 300);
    }

    _esc(s) {
      const d = document.createElement('div');
      d.textContent = s || '';
      return d.innerHTML;
    }
  }

  customElements.define('acacia-flashcard', AcaciaFlashcard);

  /* ── Global Init ────────────────────────────────────────────── */

  window._acaciaSM2 = new SM2Scheduler();
  window.AcaciaQuizEngine = QuizEngine;

  /* ── Quiz auto-init on page load ────────────────────────────── */
  document.addEventListener('DOMContentLoaded', () => {
    const quizSection = document.getElementById('quiz-section');
    if (quizSection) {
      try {
        const data = JSON.parse(quizSection.dataset.quiz);
        const lesson = quizSection.dataset.quizLesson || '';
        const engine = new QuizEngine(data, lesson);
        const container = document.getElementById('quiz-container');
        const scoreEl = document.getElementById('quiz-score');
        const summaryEl = document.getElementById('quiz-summary');
        const retryBtn = document.getElementById('quiz-retry');

        if (container) engine.render(container, scoreEl, summaryEl, retryBtn);
        if (retryBtn) retryBtn.addEventListener('click', () => {
          const e2 = new QuizEngine(data, lesson);
          e2.render(container, scoreEl, summaryEl, retryBtn);
          summaryEl.classList.add('hidden');
          retryBtn.classList.add('hidden');
        });
      } catch (_) {}
    }

    /* ── Mark Complete button ── */
    const markBtn = document.getElementById('mark-complete-btn');
    if (markBtn) {
      const path = markBtn.dataset.trackLesson;
      const key = 'acacia_completed';
      let completed = [];
      try { completed = JSON.parse(localStorage.getItem(key) || '[]'); } catch (_) {}
      if (completed.includes(path)) {
        document.getElementById('complete-btn-text').textContent = 'Completed';
        markBtn.style.opacity = '0.6';
        markBtn.disabled = true;
      }
      markBtn.addEventListener('click', () => {
        if (!completed.includes(path)) completed.push(path);
        localStorage.setItem(key, JSON.stringify(completed));
        document.getElementById('complete-btn-text').textContent = 'Completed';
        markBtn.style.opacity = '0.6';
        markBtn.disabled = true;
      });
    }

    /* ── Keyboard shortcuts (global) ── */
    document.addEventListener('keydown', (e) => {
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.isContentEditable) return;
      const focused = document.activeElement;
      if (focused && focused.closest('.flashcard-card-flip')) {
        if (e.key === ' ') { e.preventDefault(); focused.click(); }
      }
    });
  });

})();
