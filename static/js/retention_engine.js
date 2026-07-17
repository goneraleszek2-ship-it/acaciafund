/* ═══════════════════════════════════════════════════════════════
   AcaciaFund Retention Engine — Concept Review, Gap Detection, Interleaved Practice
   ═══════════════════════════════════════════════════════════════ */

(function () {
  'use strict';

  /* ── Constants ──────────────────────────────────────────────── */

  const CONCEPT_DATA_URL = '/static/review_concepts.json';
  const MASTERY_KEY = 'acacia_concept_mastery';
  const GAP_SEEN_KEY = 'acacia_gap_dismissed';

  /* ── Pillar config ──────────────────────────────────────────── */

  const PILLARS = [
    { key: 'aml', label: 'Compliance', color: '#ef4444' },
    { key: 'stock', label: 'Markets', color: '#f59e0b' },
    { key: 'data-engineering', label: 'Data Engineering', color: '#3b82f6' },
  ];

  const PILLAR_MAP = Object.fromEntries(PILLARS.map(p => [p.key, p]));

  /* ── RetentionEngine ────────────────────────────────────────── */

  class RetentionEngine {
    constructor() {
      this.concepts = [];
      this.loaded = false;
      this.mastery = {};
      this._loadMastery();
    }

    /* ── Data loading ── */

    async loadConceptData() {
      try {
        const resp = await fetch(CONCEPT_DATA_URL);
        const data = await resp.json();
        this.concepts = data.concepts || [];
        this.loaded = true;
        return this.concepts;
      } catch (e) {
        console.warn('RetentionEngine: failed to load concept data', e);
        this.loaded = true;
        return [];
      }
    }

    /* ── Mastery persistence ── */

    _loadMastery() {
      try {
        this.mastery = JSON.parse(localStorage.getItem(MASTERY_KEY) || '{}');
      } catch (_) {
        this.mastery = {};
      }
    }

    _saveMastery() {
      try {
        localStorage.setItem(MASTERY_KEY, JSON.stringify(this.mastery));
      } catch (_) {}
    }

    getMastery(conceptId) {
      if (!this.mastery[conceptId]) {
        this.mastery[conceptId] = {
          ease: 2.5,
          interval: 0,
          reps: 0,
          due: 0,
          lastReview: 0,
          qualityHistory: [],
        };
      }
      return this.mastery[conceptId];
    }

    /* grade: 0=Again, 1=Hard, 2=Good, 3=Easy */
    review(conceptId, grade) {
      const m = this.getMastery(conceptId);
      const now = Date.now();

      if (grade < 2) {
        m.reps = 0;
        m.interval = 1;
      } else {
        if (m.reps === 0) m.interval = 1;
        else if (m.reps === 1) m.interval = 6;
        else m.interval = Math.round(m.interval * m.ease);
        m.reps++;
      }

      m.ease += 0.1 - (3 - grade) * (0.08 + (3 - grade) * 0.02);
      m.ease = Math.max(1.3, m.ease);

      m.due = now + m.interval * 86400000;
      m.lastReview = now;
      m.qualityHistory.push(grade);
      if (m.qualityHistory.length > 20) m.qualityHistory = m.qualityHistory.slice(-20);

      this._saveMastery();
      return m;
    }

    /* ── Mastery computation ── */

    calculateScore(conceptId) {
      const m = this.getMastery(conceptId);
      if (m.reps === 0) return 0;
      const base = Math.min(m.reps / 10, 1) * 0.5;
      const intervalFactor = Math.min(m.interval / 90, 1) * 0.3;
      const easeFactor = Math.min((m.ease - 1.3) / 2, 1) * 0.2;
      return Math.round((base + intervalFactor + easeFactor) * 1000) / 1000;
    }

    masteryLabel(score) {
      if (score === 0) return 'unseen';
      if (score < 0.3) return 'learning';
      if (score < 0.6) return 'reviewing';
      if (score < 0.85) return 'consolidating';
      return 'mastered';
    }

    masteryColor(label) {
      const colors = {
        unseen: '#6b7280',
        learning: '#f59e0b',
        reviewing: '#3b82f6',
        consolidating: '#22c55e',
        mastered: '#8b5cf6',
      };
      return colors[label] || '#6b7280';
    }

    /* ── Gap detection ── */

    getGaps() {
      const now = Date.now();
      const unseen = [];
      const overdue = [];
      const lowMastery = [];

      for (const c of this.concepts) {
        const m = this.getMastery(c.id);
        if (m.reps === 0) {
          unseen.push(c);
          continue;
        }
        const score = this.calculateScore(c.id);
        if (m.due > 0 && m.due <= now && (now - m.due) > 7 * 86400000) {
          overdue.push(c);
          continue;
        }
        if (score < 0.3) {
          lowMastery.push(c);
        }
      }

      return { unseen, overdue, lowMastery, total: unseen.length + overdue.length + lowMastery.length };
    }

    getPillarBreakdown() {
      const breakdown = {};
      for (const c of this.concepts) {
        const score = this.calculateScore(c.id);
        const label = this.masteryLabel(score);
        if (!breakdown[c.pillar]) {
          breakdown[c.pillar] = { unseen: 0, learning: 0, reviewing: 0, consolidating: 0, mastered: 0, total: 0 };
        }
        breakdown[c.pillar][label]++;
        breakdown[c.pillar].total++;
      }
      return breakdown;
    }

    getOverallStats() {
      const now = Date.now();
      let due = 0, learning = 0, mastered = 0;
      for (const c of this.concepts) {
        const m = this.getMastery(c.id);
        if (m.due <= now && m.reps > 0) due++;
        else if (m.reps > 0 && m.interval < 21) learning++;
        else if (m.reps > 0) mastered++;
      }
      return { total: this.concepts.length, due, learning, mastered, unseen: this.concepts.length - due - learning - mastered };
    }

    /* ── Interleaved session ── */

    buildInterleavedSession(sessionSize) {
      sessionSize = sessionSize || 10;
      const now = Date.now();
      const due = [];
      const unseen = [];
      const other = [];

      for (const c of this.concepts) {
        const m = this.getMastery(c.id);
        if (m.reps === 0) unseen.push(c);
        else if (m.due <= now) due.push(c);
        else other.push(c);
      }

      this._shuffle(due);
      this._shuffle(unseen);
      this._shuffle(other);

      const candidates = [...due, ...unseen, ...other];
      const selected = [];
      const pillarCount = {};
      const maxPerPillar = Math.max(1, Math.ceil(sessionSize / 3));

      for (const c of candidates) {
        if (selected.length >= sessionSize) break;
        const pc = pillarCount[c.pillar] || 0;
        if (pc >= maxPerPillar) continue;
        selected.push(c);
        pillarCount[c.pillar] = pc + 1;
      }

      return selected;
    }

    _shuffle(arr) {
      for (let i = arr.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [arr[i], arr[j]] = [arr[j], arr[i]];
      }
    }

    /* ── Concept card rendering ── */

    renderConceptCard(container, item, onGrade) {
      const pillar = PILLAR_MAP[item.pillar] || { label: item.pillar, color: '#6366f1' };
      const m = this.getMastery(item.id);
      const score = this.calculateScore(item.id);
      const label = this.masteryLabel(score);
      const labelColor = this.masteryColor(label);

      const lineage = item.philosophicalLineage || [];
      const lineageTags = lineage.slice(0, 3).map(l => {
        const short = l.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
        return `<span class="inline-block px-1.5 py-0.5 text-[10px] rounded" style="background:color-mix(in srgb, ${labelColor} 10%, transparent);color:${labelColor}">${short}</span>`;
      }).join('');

      container.innerHTML = `
        <div class="ghost-card rounded-lg overflow-hidden" role="group" aria-label="Review concept: ${this._esc(item.label)}">
          <div class="p-5">
            <div class="flex items-center gap-2 mb-3">
              <span class="text-xs font-semibold px-2 py-0.5 rounded" style="background:color-mix(in srgb, ${pillar.color} 15%, transparent);color:${pillar.color}">${pillar.label}</span>
              <span class="text-xs font-mono px-1.5 py-0.5 rounded" style="background:color-mix(in srgb, ${labelColor} 10%, transparent);color:${labelColor}">${label}</span>
              <span class="text-xs" style="color:var(--color-text-muted)">${item.bloomLevel}</span>
            </div>

            <div class="concept-card-front">
              <h3 class="text-lg font-bold mb-1" style="color:var(--color-text)">${this._esc(item.label)}</h3>
              ${item.aliases && item.aliases.length ? `<p class="text-xs mb-2" style="color:var(--color-text-muted)">Also: ${item.aliases.slice(0, 4).map(a => this._esc(a)).join(', ')}</p>` : ''}
              <p class="text-sm leading-relaxed" style="color:var(--color-text-secondary)">${this._esc(item.definition)}</p>
              ${lineageTags ? `<div class="flex flex-wrap gap-1 mt-3">${lineageTags}</div>` : ''}
            </div>
          </div>

          <div class="flex gap-1 p-3 pt-0 justify-center">
            <button data-grade="0" class="grade-btn px-3 py-2 text-xs font-semibold rounded-lg transition hover:opacity-80" style="background:color-mix(in srgb, #ef4444 15%, transparent);color:#ef4444;min-width:48px;min-height:48px">Again</button>
            <button data-grade="1" class="grade-btn px-3 py-2 text-xs font-semibold rounded-lg transition hover:opacity-80" style="background:color-mix(in srgb, #f59e0b 15%, transparent);color:#f59e0b;min-width:48px;min-height:48px">Hard</button>
            <button data-grade="2" class="grade-btn px-3 py-2 text-xs font-semibold rounded-lg transition hover:opacity-80" style="background:color-mix(in srgb, #22c55e 15%, transparent);color:#22c55e;min-width:48px;min-height:48px">Good</button>
            <button data-grade="3" class="grade-btn px-3 py-2 text-xs font-semibold rounded-lg transition hover:opacity-80" style="background:color-mix(in srgb, #3b82f6 15%, transparent);color:#3b82f6;min-width:48px;min-height:48px">Easy</button>
          </div>
        </div>
      `;

      container.querySelectorAll('.grade-btn').forEach(btn => {
        btn.addEventListener('click', () => {
          const grade = parseInt(btn.dataset.grade);
          this.review(item.id, grade);
          if (onGrade) onGrade(grade, item);
        });
      });
    }

    /* ── Dashboard rendering ── */

    renderMasteryDashboard(container) {
      if (!this.concepts.length) {
        container.innerHTML = '<p class="text-sm" style="color:var(--color-text-muted)">Loading concept data...</p>';
        return;
      }

      const stats = this.getOverallStats();
      const gaps = this.getGaps();
      const breakdown = this.getPillarBreakdown();

      let html = '';

      html += `<div class="grid gap-4 sm:grid-cols-4 mb-6">
        <div class="ghost-card p-4 text-center">
          <div class="text-3xl font-bold" style="color:var(--color-accent)">${stats.total}</div>
          <div class="text-xs font-meta mt-1" style="color:var(--color-text-muted)">Total Concepts</div>
        </div>
        <div class="ghost-card p-4 text-center">
          <div class="text-3xl font-bold" style="color:var(--color-accent)">${stats.due}</div>
          <div class="text-xs font-meta mt-1" style="color:var(--color-text-muted)">Due for Review</div>
        </div>
        <div class="ghost-card p-4 text-center">
          <div class="text-3xl font-bold" style="color:#22c55e">${stats.mastered}</div>
          <div class="text-xs font-meta mt-1" style="color:var(--color-text-muted)">Mastered</div>
        </div>
        <div class="ghost-card p-4 text-center">
          <div class="text-3xl font-bold" style="color:#f59e0b">${gaps.total}</div>
          <div class="text-xs font-meta mt-1" style="color:var(--color-text-muted)">Knowledge Gaps</div>
        </div>
      </div>`;

      html += '<h3 class="text-sm font-semibold mb-3" style="color:var(--color-text)">Mastery by Pillar</h3>';
      html += '<div class="space-y-3 mb-6">';
      for (const p of PILLARS) {
        const bd = breakdown[p.key] || { unseen: 0, learning: 0, reviewing: 0, consolidating: 0, mastered: 0, total: 0 };
        const masteredPct = bd.total ? Math.round((bd.mastered / bd.total) * 100) : 0;
        const unseenPct = bd.total ? Math.round((bd.unseen / bd.total) * 100) : 0;
        html += `<div class="ghost-card p-3">
          <div class="flex items-center justify-between mb-1">
            <span class="text-xs font-semibold" style="color:${p.color}">${p.label}</span>
            <span class="text-xs" style="color:var(--color-text-muted)">${bd.mastered} mastered / ${bd.unseen} unseen</span>
          </div>
          <div class="h-2 rounded-full overflow-hidden" style="background:color-mix(in srgb, ${p.color} 15%, transparent)">
            <div class="h-full rounded-full transition-all" style="width:${masteredPct}%;background:${p.color}"></div>
          </div>
          <div class="flex justify-between mt-1">
            <span class="text-[10px]" style="color:var(--color-text-muted)">${this.masteryLabel(0)}</span>
            <span class="text-[10px]" style="color:${p.color}">${masteredPct}% mastered</span>
          </div>
        </div>`;
      }
      html += '</div>';

      if (gaps.unseen.length || gaps.overdue.length || gaps.lowMastery.length) {
        html += '<h3 class="text-sm font-semibold mb-2" style="color:var(--color-text)">Knowledge Gaps</h3>';
        html += '<div class="space-y-2 mb-6">';

        if (gaps.unseen.length) {
          html += `<div class="ghost-card p-3 flex items-center justify-between">
            <div>
              <span class="text-xs font-semibold" style="color:#f59e0b">${gaps.unseen.length} unseen concepts</span>
              <p class="text-[10px]" style="color:var(--color-text-muted)">Never reviewed</p>
            </div>
            <button class="gap-review-btn text-xs font-semibold px-3 py-1.5 rounded-lg" style="background:var(--color-accent);color:#fff" data-gap-type="unseen">Review</button>
          </div>`;
        }

        if (gaps.overdue.length) {
          html += `<div class="ghost-card p-3 flex items-center justify-between">
            <div>
              <span class="text-xs font-semibold" style="color:#ef4444">${gaps.overdue.length} overdue concepts</span>
              <p class="text-[10px]" style="color:var(--color-text-muted)">Overdue by 7+ days</p>
            </div>
            <button class="gap-review-btn text-xs font-semibold px-3 py-1.5 rounded-lg" style="background:var(--color-accent);color:#fff" data-gap-type="overdue">Review</button>
          </div>`;
        }

        if (gaps.lowMastery.length) {
          html += `<div class="ghost-card p-3 flex items-center justify-between">
            <div>
              <span class="text-xs font-semibold" style="color:#3b82f6">${gaps.lowMastery.length} low-mastery concepts</span>
              <p class="text-[10px]" style="color:var(--color-text-muted)">Score below 0.3</p>
            </div>
            <button class="gap-review-btn text-xs font-semibold px-3 py-1.5 rounded-lg" style="background:var(--color-accent);color:#fff" data-gap-type="low-mastery">Review</button>
          </div>`;
        }

        html += '</div>';
      }

      html += '<div class="text-center">';
      html += '<button id="start-interleaved-session" class="inline-flex items-center gap-2 px-6 py-3 text-sm font-semibold rounded-lg transition hover:opacity-80" style="background:var(--color-accent);color:#fff">';
      html += '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/></svg>';
      html += 'Start Interleaved Practice';
      html += '</button>';
      html += '</div>';

      container.innerHTML = html;

      container.querySelectorAll('.gap-review-btn').forEach(btn => {
        btn.addEventListener('click', () => {
          const type = btn.dataset.gapType;
          this._startGapSession(type);
        });
      });

      const sessionBtn = document.getElementById('start-interleaved-session');
      if (sessionBtn) {
        sessionBtn.addEventListener('click', () => this._startInterleaved());
      }
    }

    /* ── Session modes ── */

    _startGapSession(type) {
      let items = [];
      const gaps = this.getGaps();
      if (type === 'unseen') items = gaps.unseen;
      else if (type === 'overdue') items = gaps.overdue;
      else if (type === 'low-mastery') items = gaps.lowMastery;

      this._openSession(items, `Gap: ${type}`);
    }

    _startInterleaved() {
      const items = this.buildInterleavedSession(10);
      this._openSession(items, 'Interleaved Practice');
    }

    _openSession(items, title) {
      const overlay = document.createElement('div');
      overlay.id = 'retention-session-overlay';
      overlay.style.cssText = 'position:fixed;inset:0;z-index:9999;background:rgba(0,0,0,0.6);display:flex;align-items:center;justify-content:center;padding:1rem;';

      const modal = document.createElement('div');
      modal.style.cssText = 'max-width:600px;width:100%;max-height:90vh;overflow-y:auto;border-radius:12px;padding:1.5rem;';

      overlay.appendChild(modal);
      document.body.appendChild(overlay);

      this._renderSession(modal, items, 0, title, overlay);
    }

    _renderSession(container, items, idx, title, overlay) {
      if (idx >= items.length) {
        container.innerHTML = `
          <div class="ghost-card p-6 text-center">
            <svg class="w-12 h-12 mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" style="color:var(--color-accent)"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
            <p class="text-sm font-semibold mb-1" style="color:var(--color-text)">Session Complete!</p>
            <p class="text-xs" style="color:var(--color-text-muted)">${title}</p>
            <button id="session-close-btn" class="mt-4 px-4 py-2 text-xs font-semibold rounded-lg" style="background:var(--color-accent);color:#fff">Done</button>
          </div>`;
        container.querySelector('#session-close-btn').addEventListener('click', () => overlay.remove());
        return;
      }

      container.innerHTML = `
        <div class="ghost-card p-4 mb-4">
          <div class="flex items-center justify-between">
            <span class="text-xs font-semibold" style="color:var(--color-accent)">${title}</span>
            <span class="text-xs" style="color:var(--color-text-muted)" aria-live="polite">${idx + 1} / ${items.length}</span>
          </div>
        </div>
        <div id="session-card-container" aria-live="polite"></div>
        <div class="flex justify-center gap-3 mt-4">
          <button id="session-skip-btn" class="px-4 py-2 text-xs font-semibold rounded-lg" style="background:var(--color-bg);color:var(--color-text-muted);border:1px solid var(--color-border);min-width:44px;min-height:44px">Skip</button>
          <button id="session-exit-btn" class="px-4 py-2 text-xs font-semibold rounded-lg" style="background:color-mix(in srgb, #ef4444 15%, transparent);color:#ef4444;min-width:44px;min-height:44px">Exit</button>
        </div>`;

      const cardContainer = document.getElementById('session-card-container');
      this.renderConceptCard(cardContainer, items[idx], () => {
        setTimeout(() => this._renderSession(container, items, idx + 1, title, overlay), 200);
      });

      document.getElementById('session-skip-btn').addEventListener('click', () => {
        this._renderSession(container, items, idx + 1, title, overlay);
      });
      document.getElementById('session-exit-btn').addEventListener('click', () => overlay.remove());

      document.addEventListener('keydown', function sessionKeydown(e) {
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
        if (e.key === 'Escape') { overlay.remove(); document.removeEventListener('keydown', sessionKeydown); }
        if (e.key === 'ArrowRight' || e.key === 'n') {
          document.removeEventListener('keydown', sessionKeydown);
          container.querySelector('#session-skip-btn')?.click();
        }
        if (e.key === '1') { document.removeEventListener('keydown', sessionKeydown); var gb = container.querySelector('[data-grade="0"]'); if (gb) gb.click(); }
        if (e.key === '2') { document.removeEventListener('keydown', sessionKeydown); var gb = container.querySelector('[data-grade="1"]'); if (gb) gb.click(); }
        if (e.key === '3') { document.removeEventListener('keydown', sessionKeydown); var gb = container.querySelector('[data-grade="2"]'); if (gb) gb.click(); }
        if (e.key === '4') { document.removeEventListener('keydown', sessionKeydown); var gb = container.querySelector('[data-grade="3"]'); if (gb) gb.click(); }
      });

      // Swipe support
      var touchStartX = 0;
      container.addEventListener('touchstart', function(e) { touchStartX = e.changedTouches[0].screenX; }, { passive: true });
      container.addEventListener('touchend', function(e) {
        var dx = e.changedTouches[0].screenX - touchStartX;
        if (Math.abs(dx) > 80) {
          var skipBtn = document.getElementById('session-skip-btn');
          if (skipBtn) skipBtn.click();
        }
      }, { passive: true });
    }

    _esc(s) {
      const d = document.createElement('div');
      d.textContent = s || '';
      return d.innerHTML;
    }
  }

  /* ── Exports ─────────────────────────────────────────────────── */

  window.AcaciaRetention = RetentionEngine;

  /* ── Auto-init on dashboard pages ── */

  document.addEventListener('DOMContentLoaded', () => {
    const dashboardEl = document.getElementById('concept-mastery-dashboard');
    if (dashboardEl) {
      const engine = new RetentionEngine();
      engine.loadConceptData().then(() => {
        engine.renderMasteryDashboard(dashboardEl);
      });
    }
  });

})();
