(function() {
  var root = document.getElementById('lp-progress-bar');
  var STORAGE_KEY = 'acacia_lp_progress_' + root.dataset.startConcept;
  var totalNodes = parseInt(root.dataset.totalNodes, 10) || 0;

  function loadProgress() {
    try { return JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]'); } catch(e) { return []; }
  }

  function saveProgress(done) {
    try { localStorage.setItem(STORAGE_KEY, JSON.stringify(done)); } catch(e) {}
  }

  function updateUI(done) {
    var fill = document.getElementById('lp-progress-fill');
    var text = document.getElementById('lp-progress-text');
    var pct = totalNodes > 0 ? Math.round((done.length / totalNodes) * 100) : 0;
    if (fill) fill.style.width = pct + '%';
    if (text) text.textContent = done.length + ' / ' + totalNodes + ' complete';

    document.querySelectorAll('.lp-complete-btn').forEach(function(btn, i) {
      var isDone = done.indexOf(i) !== -1;
      if (isDone) {
        btn.style.borderColor = '#22c55e';
        btn.style.color = '#22c55e';
        btn.style.background = 'color-mix(in srgb, #22c55e 10%, transparent)';
        btn.innerHTML = '<svg class="icon-sm" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg> Done';
      } else {
        btn.style.borderColor = '';
        btn.style.color = '';
        btn.style.background = '';
        btn.innerHTML = '<svg class="icon-sm" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg> Mark Done';
      }
    });
  }

  var done = loadProgress();
  updateUI(done);

  document.querySelectorAll('.lp-complete-btn').forEach(function(btn, i) {
    btn.addEventListener('click', function() {
      var idx = parseInt(this.closest('.path-node').dataset.nodeIdx);
      if (done.indexOf(idx) === -1) {
        done.push(idx);
      } else {
        done = done.filter(function(d) { return d !== idx; });
      }
      saveProgress(done);
      updateUI(done);
    });
  });
})();
