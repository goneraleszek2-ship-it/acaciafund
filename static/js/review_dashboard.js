(function() {
  const cards = JSON.parse(document.getElementById('review-cards-data').textContent);
  const SM2_KEY = 'acacia_sm2';
  const HIST_KEY = 'acacia_review_history';

  let sm2 = {};
  try { sm2 = JSON.parse(localStorage.getItem(SM2_KEY) || '{}'); } catch(_) {}

  let hist = [];
  try { hist = JSON.parse(localStorage.getItem(HIST_KEY) || '[]'); } catch(_) {}

  const now = Date.now();
  let due = 0, learning = 0, mastered = 0;
  const pillarDue = { aml: 0, stock: 0, 'data-engineering': 0 };

  for (const c of cards) {
    const s = sm2[c.id] || { reps: 0, interval: 0, due: 0 };
    if (s.due <= now) {
      due++;
      pillarDue[c.pillar] = (pillarDue[c.pillar] || 0) + 1;
    } else if (s.reps > 0 && s.interval < 21) learning++;
    else if (s.reps > 0) mastered++;
  }

  document.getElementById('stat-due').textContent = due;
  document.getElementById('stat-mastered').textContent = mastered;

  let streak = 0;
  if (hist.length) {
    const today = new Date().toISOString().slice(0, 10);
    const yesterday = new Date(Date.now() - 86400000).toISOString().slice(0, 10);
    if (hist.includes(today) || hist.includes(yesterday)) {
      let d = hist.includes(today) ? new Date() : new Date(Date.now() - 86400000);
      while (hist.includes(d.toISOString().slice(0, 10))) {
        streak++;
        d = new Date(d.getTime() - 86400000);
      }
    }
  }
  document.getElementById('stat-streak').textContent = streak;

  const pillarCards = document.getElementById('pillar-due').children;
  const pkeys = ['aml', 'stock', 'data-engineering'];
  for (let i = 0; i < 3; i++) {
    pillarCards[i].querySelector('div:first-child').textContent = pillarDue[pkeys[i]] || 0;
  }

  const heatmap = document.getElementById('heatmap');
  const today = new Date();
  for (let i = 89; i >= 0; i--) {
    const d = new Date(today.getTime() - i * 86400000);
    const key = d.toISOString().slice(0, 10);
    const active = hist.includes(key);
    const cell = document.createElement('div');
    cell.title = key;
    cell.style.cssText = 'width:12px;height:12px;border-radius:2px;' +
      (active ? 'background:var(--color-accent)' : 'background:var(--color-border)');
    cell.setAttribute('aria-label', key + (active ? ' (reviewed)' : ''));
    heatmap.appendChild(cell);
  }
})();

document.addEventListener('DOMContentLoaded', function() {
  if (window.AcaciaRetention) {
    var feynmanEngine = new AcaciaRetention();
    feynmanEngine.loadConceptData().then(function() {
      var feynmanMasteryContainer = document.getElementById('feynman-mastery-container');
      if (feynmanMasteryContainer) {
        var breakdown = feynmanEngine.getPillarBreakdown();
        var feynmanHistory = JSON.parse(localStorage.getItem('acacia_feynman_history') || '[]');
        var html = '';
        for (var pKey in breakdown) {
          var p = breakdown[pKey];
          var pillarInfo = { aml: { label: 'Compliance', color: '#ef4444' }, stock: { label: 'Markets', color: '#f59e0b' }, 'data-engineering': { label: 'Data Engineering', color: '#3b82f6' } }[pKey] || { label: pKey, color: '#6366f1' };
          var masteredCount = p.mastered || 0;
          var pct = p.total ? Math.round((masteredCount / p.total) * 100) : 0;
          html += '<div class="ghost-card p-3"><div class="flex items-center justify-between mb-1"><span class="text-xs font-semibold" style="color:' + pillarInfo.color + '">' + pillarInfo.label + '</span><span class="text-xs" style="color:var(--color-text-muted)">' + feynmanHistory.filter(function(h) { return h.quality >= 3; }).length + ' quality attempts</span></div><div class="h-2 rounded-full overflow-hidden" style="background:color-mix(in srgb, ' + pillarInfo.color + ' 15%, transparent)"><div class="h-full rounded-full transition-all" style="width:' + pct + '%;background:' + pillarInfo.color + '"></div></div><div class="flex justify-between mt-1"><span class="text-[10px]" style="color:var(--color-text-muted)">Feynman mode mastery</span><span class="text-[10px]" style="color:' + pillarInfo.color + '">' + pct + '%</span></div></div>';
        }
        feynmanMasteryContainer.innerHTML = html;
      }

      document.getElementById('start-feynman-session').addEventListener('click', function() {
        var selectedMode = document.querySelector('.feynman-mode-btn.active')?.dataset.feynmanMode || null;
        var items = [];
        var concepts = feynmanEngine.concepts;
        var feynmanHistory = JSON.parse(localStorage.getItem('acacia_feynman_history') || '[]');
        if (selectedMode) {
          for (var i = 0; i < concepts.length; i++) {
            var feynmanItems = feynmanEngine.generateFeynmanReviewItems(concepts[i]);
            for (var j = 0; j < feynmanItems.length; j++) {
              if (feynmanItems[j].mode === selectedMode) items.push(feynmanItems[j]);
            }
          }
          feynmanEngine.startFeynmanSession(items, 'Feynman: ' + selectedMode);
        } else {
          for (var i = 0; i < concepts.length; i++) {
            var mode = feynmanEngine.selectFeynmanMode(concepts[i], feynmanHistory);
            var feynmanItems = feynmanEngine.generateFeynmanReviewItems(concepts[i]);
            var match = null;
            for (var j = 0; j < feynmanItems.length; j++) {
              if (feynmanItems[j].mode === mode) { match = feynmanItems[j]; break; }
            }
            if (match) items.push(match);
          }
          feynmanEngine.startFeynmanSession(items, 'Adaptive Feynman');
        }
      });

      document.querySelectorAll('.feynman-mode-btn').forEach(function(btn) {
        btn.addEventListener('click', function() {
          document.querySelectorAll('.feynman-mode-btn').forEach(function(b) { b.classList.remove('active'); b.style.opacity = '0.6'; });
          this.classList.add('active');
          this.style.opacity = '1';
        });
      });
    });
  }
});

document.querySelectorAll('.review-tab').forEach(function(tab) {
  tab.addEventListener('click', function() {
    document.querySelectorAll('.review-tab').forEach(function(t) {
      t.style.background = '';
      t.style.color = 'var(--color-text-muted)';
      t.setAttribute('aria-selected', 'false');
    });
    this.style.background = 'var(--color-surface)';
    this.style.color = 'var(--color-text)';
    this.setAttribute('aria-selected', 'true');
    var mode = this.dataset.tab;
    var flashcardSec = document.getElementById('review-flashcard-section');
    var conceptSec = document.getElementById('review-concept-section');
    var feynmanSec = document.getElementById('review-feynman-section');
    var pathSec = document.getElementById('review-path-section');
    if (mode === 'all') {
      flashcardSec.style.display = ''; conceptSec.style.display = ''; feynmanSec.style.display = ''; pathSec.style.display = '';
    } else if (mode === 'flashcards') {
      flashcardSec.style.display = ''; conceptSec.style.display = 'none'; feynmanSec.style.display = 'none'; pathSec.style.display = 'none';
    } else if (mode === 'concepts') {
      flashcardSec.style.display = 'none'; conceptSec.style.display = ''; feynmanSec.style.display = 'none'; pathSec.style.display = '';
    } else if (mode === 'feynman') {
      flashcardSec.style.display = 'none'; conceptSec.style.display = 'none'; feynmanSec.style.display = ''; pathSec.style.display = 'none';
    }
  });
});
