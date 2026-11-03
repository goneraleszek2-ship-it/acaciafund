(function() {
  const allCards = JSON.parse(document.getElementById('queue-cards-data').textContent);
  const SM2_KEY = 'acacia_sm2';

  let sm2 = {};
  try { sm2 = JSON.parse(localStorage.getItem(SM2_KEY) || '{}'); } catch(_) {}

  const now = Date.now();
  const dueCards = allCards
    .filter(c => {
      const s = sm2[c.id] || { reps: 0, due: 0 };
      return s.due <= now;
    })
    .sort((a, b) => {
      const sa = sm2[a.id] || { due: 0 };
      const sb = sm2[b.id] || { due: 0 };
      return sa.due - sb.due;
    });

  const container = document.getElementById('queue-card-container');
  const emptyEl = document.getElementById('queue-empty');
  const activeEl = document.getElementById('queue-active');
  const progressEl = document.getElementById('queue-progress');
  const dueEl = document.getElementById('queue-due');
  const navEl = document.getElementById('queue-nav');

  if (!dueCards.length) {
    emptyEl.classList.remove('hidden');
    activeEl.classList.add('hidden');
    dueEl.textContent = '0 due';
    return;
  }

  dueEl.textContent = dueCards.length + ' due';
  let idx = 0;
  let reviewed = 0;

  function renderCard() {
    if (idx >= dueCards.length) {
      container.innerHTML = '<div class="ghost-card p-6 text-center"><p class="text-sm font-semibold text-default">Queue complete!</p></div>';
      navEl.classList.add('hidden');
      return;
    }

    const c = dueCards[idx];
    container.innerHTML = '';

    const fc = document.createElement('acacia-flashcard');
    fc.setAttribute('data-term', c.term);
    fc.setAttribute('data-definition', c.definition);
    fc.setAttribute('data-card-id', c.id);
    container.appendChild(fc);

    progressEl.textContent = `${reviewed} / ${dueCards.length} reviewed`;
    navEl.classList.remove('hidden');

    fc.addEventListener('card-graded', () => {
      reviewed++;
      idx++;
      setTimeout(renderCard, 200);
    });
  }

  renderCard();

  document.getElementById('queue-skip').addEventListener('click', () => {
    idx++;
    renderCard();
  });
  document.getElementById('queue-done').addEventListener('click', () => {
    window.location.href = '/review/';
  });

  document.addEventListener('keydown', (e) => {
    if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
    if (e.key === 'ArrowRight' || e.key === 'Escape') {
      idx++;
      renderCard();
    }
  });
})();
