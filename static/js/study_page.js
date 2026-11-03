(function() {
  const flashCards = JSON.parse(document.getElementById('study-cards-data').textContent);
  const FLASH_SM2_KEY = 'acacia_sm2';
  const CONCEPT_SM2_KEY = 'acacia_concept_mastery';

  function readStore(key) {
    try { return JSON.parse(localStorage.getItem(key) || '{}'); } catch (_) { return {}; }
  }

  const now = Date.now();
  const dueFlash = flashCards.filter(c => {
    const s = readStore(FLASH_SM2_KEY)[c.id] || { reps: 0, due: 0 };
    return s.due <= now;
  });

  const container = document.getElementById('queue-card-container');
  const emptyEl = document.getElementById('queue-empty');
  const activeEl = document.getElementById('queue-active');
  const progressEl = document.getElementById('queue-progress');
  const dueEl = document.getElementById('queue-due');
  const navEl = document.getElementById('queue-nav');

  function buildQueue(concepts) {
    const conceptMastery = readStore(CONCEPT_SM2_KEY);
    const dueConcepts = (concepts || []).filter(c => {
      const m = conceptMastery[c.id] || { reps: 0, due: 0 };
      return m.reps === 0 || (m.due > 0 && m.due <= now);
    });

    const queue = dueFlash.map(c => ({ kind: 'flash', data: c }));
    queue.push(...dueConcepts.map(c => ({ kind: 'concept', data: c })));

    return queue;
  }

  fetch('/static/review_concepts.json')
    .then(function(r) { if (!r.ok) throw new Error(r.status); return r.json(); })
    .then(function(data) { start(data.concepts || []); })
    .catch(function() { start([]); });

  function start(concepts) {
    const queue = buildQueue(concepts);

    if (!queue.length) {
      emptyEl.classList.remove('hidden');
      activeEl.classList.add('hidden');
      dueEl.textContent = '0 due';
      return;
    }

    dueEl.textContent = queue.length + ' due';
    let idx = 0;
    let reviewed = 0;

    function renderCard() {
      if (idx >= queue.length) {
        container.innerHTML = '<div class="ghost-card p-6 text-center"><p class="text-sm font-semibold text-default">Queue complete!</p></div>';
        navEl.classList.add('hidden');
        container.setAttribute('role', 'region');
        container.removeAttribute('aria-modal');
        return;
      }

      const item = queue[idx];
      container.innerHTML = '';
      progressEl.textContent = `${reviewed} / ${queue.length} reviewed`;
      navEl.classList.remove('hidden');
      container.setAttribute('role', 'dialog');
      container.setAttribute('aria-modal', 'false');
      container.setAttribute('aria-label', 'Study card — review and grade your recall');

      if (item.kind === 'flash') {
        const c = item.data;
        const fc = document.createElement('acacia-flashcard');
        fc.setAttribute('data-term', c.term);
        fc.setAttribute('data-definition', c.definition);
        fc.setAttribute('data-card-id', c.id);
        fc.setAttribute('data-source', c.pillar);
        container.appendChild(fc);
        fc.addEventListener('card-graded', () => advance());
        return;
      }

      const c = item.data;
      const card = document.createElement('div');
      card.className = 'ghost-card p-6';
      card.innerHTML = `
        <p class="text-xs font-meta text-muted mb-1">Concept · ${c.category || 'ontology'}</p>
        <h2 class="text-lg font-extrabold text-default mb-2">${c.label}</h2>
        <p class="text-sm text-muted mb-4">Recall what this concept means, then reveal the definition and grade yourself.</p>
        <details class="mb-4"><summary class="cursor-pointer text-sm font-semibold text-accent">Reveal definition</summary>
          <p class="mt-2 text-sm text-default">${c.definition || c.eli5Explanation || ''}</p>
        </details>
        <div class="flex justify-center gap-2" role="group" aria-label="Grade your recall">
          <button class="btn btn-ghost btn-sm" data-grade="0">Again</button>
          <button class="btn btn-ghost btn-sm" data-grade="1">Hard</button>
          <button class="btn btn-primary btn-sm" data-grade="2">Good</button>
          <button class="btn btn-primary btn-sm" data-grade="3">Easy</button>
        </div>`;
      container.appendChild(card);
      card.querySelectorAll('[data-grade]').forEach(btn => {
        btn.addEventListener('click', () => {
          if (window.AcaciaRetention && typeof window.AcaciaRetention.review === 'function') {
            window.AcaciaRetention.review(c.id, parseInt(btn.getAttribute('data-grade'), 10));
          }
          advance();
        });
      });
    }

    function advance() {
      reviewed++;
      idx++;
      setTimeout(renderCard, 200);
    }

    renderCard();

    document.getElementById('queue-skip').addEventListener('click', () => { idx++; renderCard(); });
    document.getElementById('queue-done').addEventListener('click', () => {
      window.location.href = '/review/';
    });

    document.addEventListener('keydown', (e) => {
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
      if (e.key === 'ArrowRight' || e.key === 'Escape') { idx++; renderCard(); }
    });
  }
})();
