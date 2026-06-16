(function(){
  'use strict';

  var PROGRESS_KEY = 'acacia_progress_v1';
  var SM2_KEY = 'acacia_sm2_v1';
  var REVIEWS_KEY = 'acacia_reviews_v1';
  var FOCUS_KEY = 'acacia_focus_mode';
  var ADAPTIVE_KEY = 'acacia_adaptive_v1';
  var XP_KEY = 'acacia_xp_v1';
  var STREAK_KEY = 'acacia_streak_v1';
  var BADGES_KEY = 'acacia_badges_v1';
  var CONFIDENCE_KEY = 'acacia_confidence_v1';

  // ── Toast Notification System ────────────────────────────────────────
  function showToast(message, type) {
    var toast = document.createElement('div');
    toast.className = 'toast-notification';
    toast.style.cssText = 'position:fixed;bottom:24px;right:24px;z-index:9999;padding:16px 20px;border-radius:12px;font-size:14px;font-weight:500;box-shadow:0 4px 20px rgba(0,0,0,0.15);animation:toastSlide 0.3s ease;transition:all 0.3s;';
    
    if (type === 'success') {
      toast.style.background = 'var(--color-surface)';
      toast.style.border = '2px solid #22c55e';
      toast.style.color = '#1a1a2e';
    } else if (type === 'error') {
      toast.style.background = 'var(--color-surface)';
      toast.style.border = '2px solid #ef4444';
      toast.style.color = '#1a1a2e';
    } else {
      toast.style.background = 'var(--color-surface)';
      toast.style.border = '2px solid var(--color-accent)';
      toast.style.color = '#1a1a2e';
    }
    
    toast.textContent = message;
    document.body.appendChild(toast);
    
    setTimeout(function() {
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(20px)';
      setTimeout(function() { toast.remove(); }, 300);
    }, 3000);
  }
  
  // Toast animation
  var toastStyle = document.createElement('style');
  toastStyle.textContent = '@keyframes toastSlide { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }';
  document.head.appendChild(toastStyle);

  // ── Gamification System ──────────────────────────────────────────────
  function getXPTotal() {
    var xp = loadJSON(XP_KEY, {total: 0, level: 1});
    return xp.total || 0;
  }
  function addXP(amount) {
    var xp = loadJSON(XP_KEY, {total: 0, level: 1});
    var oldTotal = xp.total || 0;
    var newTotal = oldTotal + amount;
    var oldLevel = xp.level || 1;
    var newLevel = Math.floor(newTotal / 100) + 1;
    
    xp.total = newTotal;
    xp.level = newLevel;
    saveJSON(XP_KEY, xp);
    
    // Level up animation
    if (newLevel > oldLevel) {
      showToast('Level Up! 🎉 You reached Level ' + newLevel, 'success');
    }
    
    // Update display
    updateXPDisplay();
    return {total: newTotal, level: newLevel, oldLevel: oldLevel};
  }
  function updateXPDisplay() {
    var xp = loadJSON(XP_KEY, {total: 0, level: 1});
    var total = xp.total || 0;
    var level = xp.level || 1;
    var bar = document.getElementById('xp-progress-bar');
    var text = document.getElementById('xp-text');
    var levelEl = document.getElementById('level-text');
    if (bar) {
      var progress = (total % 100) + '%';
      bar.style.width = progress;
    }
    if (text) text.textContent = total + ' XP';
    if (levelEl) levelEl.textContent = 'Level ' + level;
  }
  function getXPLockLevel() {
    var xp = loadJSON(XP_KEY, {total: 0, level: 1});
    return (xp.total || 0) >= 50 ? 2 : 1;
  }

  function checkStreak() {
    var streak = loadJSON(STREAK_KEY, {count: 0, lastDate: null});
    var today = new Date().toISOString().slice(0, 10);
    
    if (streak.lastDate === today) return streak.count;
    
    var yesterday = new Date(Date.now() - 86400000).toISOString().slice(0, 10);
    
    if (streak.lastDate === yesterday) {
      streak.count++;
      streak.lastDate = today;
      saveJSON(STREAK_KEY, streak);
      return streak.count;
    } else if (!streak.lastDate || streak.lastDate < yesterday) {
      streak.count = 1;
      streak.lastDate = today;
      saveJSON(STREAK_KEY, streak);
      return streak.count;
    }
    return streak.count;
  }
  function getStreakDisplay() {
    var count = checkStreak();
    var fire = count >= 7 ? '🔥' : count >= 3 ? '✨' : '📖';
    return fire + ' ' + count + ' day' + (count !== 1 ? 's' : '');
  }
  function updateStreakDisplay() {
    var el = document.getElementById('streak-text');
    if (el) el.textContent = getStreakDisplay();
  }

  function checkBadge(badgeId, title, desc) {
    var badges = loadJSON(BADGES_KEY, {});
    if (badges[badgeId]) return false;
    
    badges[badgeId] = {
      title: title,
      desc: desc,
      earned: Date.now()
    };
    saveJSON(BADGES_KEY, badges);
    
    showToast('🏆 Badge Unlocked: ' + title, 'success');
    return true;
  }
  function getUnlockedBadges() {
    var badges = loadJSON(BADGES_KEY, {});
    return Object.keys(badges).filter(function(k) { return badges[k]; }).length;
  }

  function addConfidenceAnswer(cardId, rating) {
    var conf = loadJSON(CONFIDENCE_KEY, {});
    if (!conf[cardId]) conf[cardId] = {hard: 0, good: 0, easy: 0};
    conf[cardId][rating]++;
    saveJSON(CONFIDENCE_KEY, conf);
  }
  function getConfidenceStats(cardId) {
    var conf = loadJSON(CONFIDENCE_KEY, {});
    return conf[cardId] || {hard: 0, good: 0, easy: 0};
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

  // ── Enhanced Search ─────────────────────────────────────────────────
  function initEnhancedSearch() {
    var paletteInput = document.getElementById('palette-input');
    var paletteResults = document.getElementById('palette-results');
    var paletteDialog = document.getElementById('search-palette');
    
    if (!paletteInput || !paletteResults) return;
    
    var MIN_CHARS = 0;
    var debounceTimer = null;
    
    // Open search on Cmd+K
    document.addEventListener('keydown', function(e) {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        if (paletteDialog && !paletteDialog.open) {
          paletteDialog.showModal();
          setTimeout(function() {
            paletteInput.focus();
          }, 0);
        }
      }
    });
    
    // Input handling
    paletteInput.addEventListener('input', function(e) {
      var query = e.target.value.trim();
      
      if (query.length < MIN_CHARS) {
        paletteResults.innerHTML = '<p class="text-sm py-8 text-center text-gray-500">Start typing to search...</p>';
        return;
      }
      
      // Debounce search
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(function() {
        performSearch(query);
      }, 150);
    });
    
    // ESC to close
    paletteInput.addEventListener('keydown', function(e) {
      if (e.key === 'Escape') {
        if (paletteDialog && paletteDialog.open) {
          paletteDialog.close();
        }
      }
    });
    
    // Perform search
    function performSearch(query) {
      // Fetch from search index
      fetch('/search/search-index.json')
        .then(function(res) { return res.json(); })
        .then(function(index) {
          var results = searchIndex(query, index);
          displayResults(results);
        })
        .catch(function() {
          // Fallback
          var results = searchClientSide(query);
          displayResults(results);
        });
    }
    
    function searchIndex(query, index) {
      var results = [];
      var queryLower = query.toLowerCase();
      
      for (var slug in index) {
        var entry = index[slug];
        var title = (entry.title || '').toLowerCase();
        var description = (entry.description || '').toLowerCase();
        
        if (title.includes(queryLower) || description.includes(queryLower)) {
          results.push({
            slug: slug,
            title: entry.title || slug,
            description: entry.description || '',
            type: entry.type || 'research',
            pillar: entry.pillar || 'general',
            sqi: entry.sqi || 0.5,
            url: '/' + slug + '/'
          });
        }
      }
      
      return results.sort(function(a, b) {
        return relevanceScore(b.title, b.description, query) - relevanceScore(a.title, a.description, query);
      }).slice(0, 10);
    }
    
    function searchClientSide(query) {
      var results = [];
      document.querySelectorAll('a[href^="/"]').forEach(function(link) {
        var href = link.getAttribute('href');
        if (href.startsWith('/')) {
          results.push({
            slug: href.substring(1),
            title: link.textContent.trim().substring(0, 60),
            description: '',
            type: 'page',
            pillar: 'general',
            sqi: 0.5,
            url: href
          });
        }
      });
      
      return results.filter(function(r) { return r.title.toLowerCase().includes(query.toLowerCase()); }).slice(0, 10);
    }
    
    function relevanceScore(title, description, query) {
      var score = 0;
      var queryLower = query.toLowerCase();
      var titleLower = title.toLowerCase();
      var descLower = description.toLowerCase();
      
      if (titleLower.includes(queryLower)) score += 10;
      
      var words = queryLower.split(/\s+/);
      for (var i = 0; i < words.length; i++) {
        var word = words[i];
        if (titleLower.startsWith(word)) score += 5;
        if (descLower.startsWith(word)) score += 3;
      }
      
      if (titleLower === queryLower) score += 20;
      
      return score;
    }
    
    function displayResults(results) {
      if (!results || results.length === 0) {
        paletteResults.innerHTML = '<p class="text-sm py-8 text-center text-gray-500">No results found</p>';
        return;
      }
      
      paletteResults.innerHTML = results.map(function(result, index) {
        return '<a href="' + result.url + '" class="block px-4 py-3 hover:bg-gray-100 dark:hover:bg-gray-800 transition">\n' +
               '  <div class="font-semibold text-sm dark:text-white mb-1">' + result.title + '</div>\n' +
               '  <div class="text-xs text-gray-500">' + result.type + 
               (result.pillar ? ' • ' + result.pillar.charAt(0).toUpperCase() + result.pillar.slice(1) : '') +
               (result.sqi ? ' • SQI: ' + result.sqi.toFixed(2) : '') + '</div>\n' +
               '</a>';
      }).join('');
    }
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
        
        // Add XP for completing lesson
        addXP(25);
        
        // Check for badge
        var totalCompleted = Object.keys(p).filter(function(k) { return p[k].done; }).length;
        if (totalCompleted === 1) checkBadge('first-step', 'First Step', 'Complete your first lesson');
        if (totalCompleted === 10) checkBadge('bloom-advanced', 'Bloom Advanced', 'Complete 10 lessons');
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
        // Add XP for correct answer
        addXP(5);
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
          // Add XP for correct answer
          addXP(5);
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
        
        // Add XP based on confidence rating
        var xpAmount = li === 2 ? 5 : li === 3 ? 10 : 1;
        addXP(xpAmount);
        
        addConfidenceAnswer('fc_' + idx, labels[li].toLowerCase());
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
    initEnhancedSearch();
    initTocToggle();
    initMobileSectionAutoExpand();
    
    // Initialize gamification display
    updateXPDisplay();
    updateStreakDisplay();
  }

  // ── TOC Toggle for Mobile ────────────────────────────────────────────
  function initTocToggle() {
    var toggleBtn = document.getElementById('toc-toggle');
    var tocPanel = document.getElementById('toc-panel');
    
    if (!toggleBtn || !tocPanel) return;
    
    // Check if TOC has items
    var tocLinks = tocPanel.querySelectorAll('.toc-link');
    if (!tocLinks.length) {
      toggleBtn.style.display = 'none';
      return;
    }
    
    toggleBtn.addEventListener('click', function() {
      var isExpanded = toggleBtn.getAttribute('aria-expanded') === 'true';
      var newState = !isExpanded;
      
      toggleBtn.setAttribute('aria-expanded', newState);
      toggleBtn.classList.toggle('active', newState);
      tocPanel.classList.toggle('active', newState);
      
      // Toggle icons
      toggleBtn.querySelector('.toc-icon-closed').classList.toggle('hidden', newState);
      toggleBtn.querySelector('.toc-icon-open').classList.toggle('hidden', !newState);
    });
    
    // Close TOC when clicking links
    tocPanel.querySelectorAll('.toc-link').forEach(function(link) {
      link.addEventListener('click', function() {
        var isExpanded = toggleBtn.getAttribute('aria-expanded') === 'true';
        if (isExpanded) {
          toggleBtn.click();
        }
      });
    });
  }

  // ── Mobile Section Auto-Expand ───────────────────────────────────────
  function initMobileSectionAutoExpand() {
    // Only apply to mobile devices
    if (window.innerWidth >= 640) return;
    
    var sections = document.querySelectorAll('.section-harvester details');
    if (!sections.length) return;
    
    // Auto-expand all sections on mobile
    sections.forEach(function(section) {
      if (!section.open) {
        section.open = true;
      }
    });
    
    // Add "Read All" button for mobile
    var article = document.querySelector('article');
    if (!article) return;
    
    // Check if we have sections
    var harvesterCount = article.querySelectorAll('.section-harvester').length;
    if (harvesterCount < 2) return;
    
    var readAllBtn = document.createElement('button');
    readAllBtn.className = 'mobile-read-all-btn';
    readAllBtn.textContent = 'Read All Sections';
    readAllBtn.style.cssText = 'display:none;margin:1.5rem 0 2rem;padding:0.75rem 1.5rem;background:var(--color-accent);color:#fff;border-radius:0.5rem;font-weight:600;cursor:pointer;border:none;transition:all 0.2s';
    readAllBtn.addEventListener('click', function() {
      var sections = article.querySelectorAll('.section-harvester details');
      var shouldExpand = this.textContent === 'Read All Sections';
      
      sections.forEach(function(section) {
        section.open = shouldExpand;
      });
      
      this.textContent = shouldExpand ? 'Collapse All' : 'Read All Sections';
      this.style.background = shouldExpand ? 'var(--color-text-muted)' : 'var(--color-accent)';
    });
    
    article.insertBefore(readAllBtn, article.firstChild);
    
    // Show button only on mobile with multiple sections
    function updateReadAllButton() {
      if (window.innerWidth < 640 && harvesterCount >= 2) {
        readAllBtn.style.display = 'block';
      } else {
        readAllBtn.style.display = 'none';
      }
    }
    
    window.addEventListener('resize', updateReadAllButton);
    updateReadAllButton();
  }
})();
