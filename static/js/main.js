(function () {
  'use strict';

  /* ── Reading Progress Bar ── */
  function initReadingProgress() {
    var bar = document.getElementById('reading-progress');
    if (!bar) {
      bar = document.createElement('div');
      bar.id = 'reading-progress';
      document.body.prepend(bar);
    }
    function update() {
      var scrollTop = window.scrollY;
      var docHeight = document.documentElement.scrollHeight - window.innerHeight;
      var progress = docHeight > 0 ? (scrollTop / docHeight) * 100 : 0;
      bar.style.width = progress + '%';
    }
    window.addEventListener('scroll', update);
    window.addEventListener('resize', update);
  }

  /* ── Scroll to Top ── */
  function initScrollTop() {
    var btn = document.getElementById('scroll-top');
    if (!btn) {
      btn = document.createElement('button');
      btn.id = 'scroll-top';
      btn.setAttribute('aria-label', 'Scroll to top');
      btn.innerHTML = '<svg width="18" height="18" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 15l7-7 7 7"/></svg>';
      document.body.appendChild(btn);
    }
    function toggle() {
      btn.classList.toggle('visible', window.scrollY > 300);
    }
    window.addEventListener('scroll', toggle);
    btn.addEventListener('click', function () {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
  }

  /* ── Mobile Nav Toggle ── */
  function initMobileNav() {
    var nav = document.querySelector('nav');
    if (!nav) return;
    var toggle = nav.querySelector('.nav-toggle');
    if (!toggle) {
      toggle = document.createElement('button');
      toggle.className = 'nav-toggle';
      toggle.setAttribute('aria-label', 'Toggle navigation');
      toggle.setAttribute('aria-expanded', 'false');
      toggle.innerHTML = '<svg width="24" height="24" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"/></svg>';
      var firstUl = nav.querySelector('ul');
      if (firstUl) firstUl.after(toggle);
    }
    var menu = nav.querySelector('ul:last-child');
    if (!menu) return;
    toggle.addEventListener('click', function () {
      var open = menu.classList.toggle('open');
      toggle.setAttribute('aria-expanded', open);
    });
  }

  /* ── Tooltip Handler ── */
  function initTooltips() {
    document.querySelectorAll('[data-tooltip]').forEach(function (el) {
      if (!el.getAttribute('aria-label')) {
        el.setAttribute('aria-label', el.getAttribute('data-tooltip'));
      }
    });
  }

  /* ── Feynman Card Stage Tracking ── */
  function initFeynmanTracking() {
    document.querySelectorAll('.feynman-card').forEach(function (card) {
      var conceptId = card.getAttribute('data-concept');
      if (!conceptId) return;
      var storageKey = 'acacia_feynman_' + conceptId;
      var completed;
      try {
        completed = JSON.parse(localStorage.getItem(storageKey)) || [];
      } catch (_) { completed = []; }
      var stages = card.querySelectorAll('.feynman-layer');
      stages.forEach(function (layer) {
        var cls = layer.className;
        var stageType = 'unknown';
        if (cls.indexOf('eli5-layer') !== -1) stageType = 'eli5';
        else if (cls.indexOf('analogy-layer') !== -1) stageType = 'analogy';
        else if (cls.indexOf('example-layer') !== -1) stageType = 'example';
        else if (cls.indexOf('diagram-layer') !== -1) stageType = 'diagram';
        else if (cls.indexOf('gaps-layer') !== -1) stageType = 'gaps';
        else if (cls.indexOf('teachback-layer') !== -1) stageType = 'teachback';
        else if (cls.indexOf('build-layer') !== -1) stageType = 'build';
        if (completed.indexOf(stageType) !== -1) {
          layer.classList.add('stage-completed');
          var summary = layer.querySelector('summary');
          if (summary) summary.innerHTML = '<span class="stage-check">✓</span> ' + summary.textContent.trim();
        }
        var toggle = layer.querySelector('summary') || layer;
        toggle.addEventListener('click', function () {
          if (completed.indexOf(stageType) === -1) {
            completed.push(stageType);
            try { localStorage.setItem(storageKey, JSON.stringify(completed)); } catch (_) {}
            layer.classList.add('stage-completed');
            updateStageProgress(conceptId, completed.length, stages.length);
          }
        });
      });
    });
  }

  function updateStageProgress(conceptId, done, total) {
    var progressBar = document.querySelector('[data-concept-progress="' + conceptId + '"]');
    if (progressBar) {
      progressBar.style.width = ((done / total) * 100) + '%';
    }
  }

  /* ── Learning Mode Toggle ── */
  function initLearningMode() {
    var select = document.getElementById('mode-select');
    if (!select) return;
    var currentMode;
    try { currentMode = localStorage.getItem('acacia_learning_mode') || 'beginner'; } catch (_) { currentMode = 'beginner'; }
    function setMode(mode) {
      document.body.classList.remove('mode-beginner', 'mode-intermediate', 'mode-expert');
      document.body.classList.add('mode-' + mode);
      select.value = mode;
      try { localStorage.setItem('acacia_learning_mode', mode); } catch (_) {}
    }
    select.addEventListener('change', function () { setMode(select.value); });
    setMode(currentMode);
  }

  /* ── "Was this helpful?" Feedback ── */
  function initFeedback() {
    document.querySelectorAll('[data-feedback]').forEach(function (container) {
      var conceptId = container.getAttribute('data-feedback');
      var storageKey = 'acacia_feedback_' + conceptId;
      var voted;
      try { voted = localStorage.getItem(storageKey); } catch (_) { voted = null; }
      container.querySelectorAll('.feedback-btn').forEach(function (btn) {
        var value = btn.getAttribute('data-value');
        if (voted === value) btn.classList.add('active');
        btn.addEventListener('click', function () {
          container.querySelectorAll('.feedback-btn').forEach(function (b) { b.classList.remove('active'); });
          btn.classList.add('active');
          try { localStorage.setItem(storageKey, value); } catch (_) {}
        });
      });
    });
  }

  /* ── Deep Dive Toggle (philosophical metadata) ── */
  function initDeepDive() {
    var toggle = document.getElementById('deep-dive-toggle');
    if (!toggle) return;
    var content = document.getElementById('deep-dive-content');
    if (!content) return;
    toggle.addEventListener('click', function () {
      var expanded = content.style.display !== 'none';
      content.style.display = expanded ? 'none' : 'block';
      toggle.classList.toggle('active', !expanded);
      toggle.setAttribute('aria-expanded', !expanded);
    });
  }

  /* ── Continue Where You Left Off ── */
  function initContinueReading() {
    var article = document.querySelector('[data-article-slug]');
    if (!article) return;
    var slug = article.getAttribute('data-article-slug');
    var storageKey = 'acacia_last_read_' + slug;
    var lastScroll;
    try { lastScroll = parseInt(localStorage.getItem(storageKey), 10); } catch (_) { lastScroll = null; }
    if (lastScroll) {
      var banner = document.createElement('div');
      banner.className = 'ghost-card p-3 mb-4 text-sm';
      banner.style.cssText = 'border-left:3px solid var(--color-accent);cursor:pointer';
      banner.innerHTML = '<span style="color:var(--color-text-muted)">↻ Continue where you left off</span>';
      banner.addEventListener('click', function () {
        window.scrollTo({ top: lastScroll, behavior: 'smooth' });
        banner.remove();
      });
      article.prepend(banner);
    }
    function saveScroll() {
      try { localStorage.setItem(storageKey, String(window.scrollY)); } catch (_) {}
    }
    var scrollTimer;
    window.addEventListener('scroll', function () {
      clearTimeout(scrollTimer);
      scrollTimer = setTimeout(saveScroll, 500);
    });
  }

  /* ── Theme Toggle ── */
  function initTheme() {
    var btn = document.getElementById('theme-toggle');
    if (!btn) return;
    var moon = document.getElementById('theme-icon-moon');
    var sun = document.getElementById('theme-icon-sun');
    var html = document.documentElement;
    function apply(theme) {
      html.classList.remove('dark', 'light');
      if (theme) {
        html.classList.add(theme);
        html.setAttribute('data-theme', theme);
      } else {
        html.removeAttribute('data-theme');
      }
      try { localStorage.setItem('acacia_theme', theme || ''); } catch (_) {}
      if (moon && sun) {
        moon.style.display = theme === 'light' ? 'none' : '';
        sun.style.display = theme === 'light' ? '' : 'none';
      }
    }
    btn.addEventListener('click', function () {
      var isDark = html.classList.contains('dark') || (!html.classList.contains('light') && window.matchMedia('(prefers-color-scheme: dark)').matches);
      apply(isDark ? 'light' : 'dark');
    });
    var saved;
    try { saved = localStorage.getItem('acacia_theme'); } catch (_) {}
    if (saved) {
      apply(saved);
    } else if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
      apply('dark');
    } else {
      apply('');
    }
  }

  /* ── Init All ── */
  function init() {
    initTheme();
    initReadingProgress();
    initScrollTop();
    initMobileNav();
    initTooltips();
    initFeynmanTracking();
    initLearningMode();
    initFeedback();
    initDeepDive();
    initContinueReading();
    /* Keyboard nav indicator */
    document.addEventListener('keydown', function(e) {
      if (e.key === 'Tab') document.body.classList.add('keyboard-nav');
    });
    document.addEventListener('mousedown', function() {
      document.body.classList.remove('keyboard-nav');
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

})();
