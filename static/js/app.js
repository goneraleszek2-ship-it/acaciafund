
/* main.js */
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
  function navState(open) {
    return {
      expanded: open ? 'true' : 'false',
      label: open ? 'Close navigation menu' : 'Open navigation menu',
    };
  }

  function initMobileNav() {
    var nav = document.querySelector('nav');
    if (!nav) return;
    var toggle = nav.querySelector('.nav-toggle');
    if (!toggle) return;
    var menu = nav.querySelector('ul:last-child');
    var overlay = document.getElementById('nav-overlay');
    if (!menu) return;

    function setOpen(open) {
      menu.classList.toggle('open', open);
      var state = navState(open);
      toggle.setAttribute('aria-expanded', state.expanded);
      toggle.setAttribute('aria-label', state.label);
      if (overlay) overlay.classList.toggle('open', open);
      document.body.classList.toggle('nav-open', open);
      if (open) {
        var first = menu.querySelector('a, button');
        if (first) first.focus();
      } else if (document.activeElement && menu.contains(document.activeElement)) {
        toggle.focus();
      }
    }

    toggle.addEventListener('click', function () {
      setOpen(!menu.classList.contains('open'));
    });

    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && menu.classList.contains('open')) {
        setOpen(false);
      }
    });
    if (overlay) {
      overlay.addEventListener('click', function () { setOpen(false); });
    }
    window.addEventListener('resize', function () {
      if (window.innerWidth > 768 && menu.classList.contains('open')) {
        setOpen(false);
      }
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

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
      navState: navState,
    };
  }

  if (typeof document !== 'undefined') {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', init);
    } else {
      init();
    }
  }

})();


/* reading.js */
(function () {
  'use strict';

  var KEYS = {
    density: 'acacia_density',
    focus: 'acacia_focus',
    guide: 'acacia_reading_guide',
  };
  var DENSITIES = ['compact', 'standard', 'comfortable'];

  function storeGet(key) {
    try { return localStorage.getItem(key); } catch (_) { return null; }
  }
  function storeSet(key, value) {
    try { localStorage.setItem(key, value); } catch (_) {}
  }

  /* ── Reading Settings Panel ── */
  function initSettingsPanel() {
    var panel = document.getElementById('settings-panel');
    var toggle = document.getElementById('settings-toggle');
    var close = document.getElementById('settings-close');
    if (!panel || !toggle) return;
    var lastFocus = null;

    function setOpen(open) {
      panel.classList.toggle('open', open);
      panel.setAttribute('aria-hidden', open ? 'false' : 'true');
      toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
      if (open) {
        lastFocus = document.activeElement;
        if (close) close.focus();
      } else if (lastFocus) {
        lastFocus.focus();
        lastFocus = null;
      }
    }

    function focusables() {
      return Array.prototype.slice.call(panel.querySelectorAll('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'));
    }

    function trapFocus(e) {
      if (!panel.classList.contains('open')) return;
      var f = focusables();
      if (f.length === 0) return;
      var first = f[0];
      var last = f[f.length - 1];
      if (e.key === 'Tab') {
        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault();
          last.focus();
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault();
          first.focus();
        }
      }
    }

    toggle.addEventListener('click', function () {
      setOpen(!panel.classList.contains('open'));
    });
    if (close) close.addEventListener('click', function () { setOpen(false); });

    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && panel.classList.contains('open')) setOpen(false);
    });
    document.addEventListener('keydown', trapFocus);
    document.addEventListener('click', function (e) {
      if (panel.classList.contains('open') && !panel.contains(e.target) && !toggle.contains(e.target)) {
        setOpen(false);
      }
    });
  }

  /* ── Information Density (compact / standard / comfortable) ── */
  function initDensity() {
    var html = document.documentElement;
    var saved = storeGet(KEYS.density) || 'standard';
    if (DENSITIES.indexOf(saved) === -1) saved = 'standard';

    function apply(density, persist) {
      if (DENSITIES.indexOf(density) === -1) density = 'standard';
      html.setAttribute('data-density', density);
      document.querySelectorAll('.density-btn').forEach(function (btn) {
        btn.classList.toggle('active', btn.getAttribute('data-density') === density);
      });
      if (persist !== false) storeSet(KEYS.density, density);
    }

    document.querySelectorAll('.density-btn').forEach(function (btn) {
      btn.addEventListener('click', function () {
        apply(btn.getAttribute('data-density'));
      });
    });
    apply(saved, false);

    window.addEventListener('storage', function (e) {
      if (e.key === KEYS.density) apply(e.newValue || 'standard', false);
    });
  }

  /* ── Focus Mode (hide chrome, center prose) ── */
  function initFocusMode() {
    var html = document.documentElement;
    var toggle = document.getElementById('focus-toggle');
    var saved = storeGet(KEYS.focus) === 'true';

    function apply(on) {
      html.setAttribute('data-focus', on ? 'true' : 'false');
      document.querySelectorAll('body > header, body > footer, .skip-link, .nav-overlay').forEach(function (el) {
        el.classList.toggle('focus-hide', on);
      });
      if (toggle) toggle.checked = on;
      storeSet(KEYS.focus, on ? 'true' : 'false');
    }

    if (toggle) toggle.addEventListener('change', function () { apply(toggle.checked); });
    apply(saved);

    window.addEventListener('storage', function (e) {
      if (e.key === KEYS.focus) apply(e.newValue === 'true');
    });
  }

  /* ── Guided Reading Line ── */
  function initReadingGuide() {
    var html = document.documentElement;
    var toggle = document.getElementById('guide-toggle');
    var saved = storeGet(KEYS.guide) === 'true';

    var guide = document.getElementById('reading-guide');
    if (!guide) {
      guide = document.createElement('div');
      guide.id = 'reading-guide';
      guide.className = 'reading-guide';
      document.body.appendChild(guide);
    }

    function position() {
      guide.style.top = (window.scrollY + window.innerHeight * 0.6) + 'px';
    }

    function apply(on) {
      html.setAttribute('data-guide', on ? 'true' : 'false');
      if (toggle) toggle.checked = on;
      storeSet(KEYS.guide, on ? 'true' : 'false');
      if (on) {
        position();
        window.addEventListener('scroll', position, { passive: true });
        window.addEventListener('resize', position);
        guide.classList.add('visible');
      } else {
        window.removeEventListener('scroll', position);
        window.removeEventListener('resize', position);
        guide.classList.remove('visible');
      }
    }

    if (toggle) toggle.addEventListener('change', function () { apply(toggle.checked); });
    apply(saved);

    window.addEventListener('storage', function (e) {
      if (e.key === KEYS.guide) apply(e.newValue === 'true');
    });
  }

  function init() {
    initSettingsPanel();
    initDensity();
    initFocusMode();
    initReadingGuide();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();


/* toc.js */
(function () {
  'use strict';

  /* Auto-generate a table of contents from .prose-body h2/h3 headings.
     Desktop: sticky sidebar (CSS grid). Mobile: inline card after the header. */

  /** Pure: assign ids and normalize headings for the TOC. */
  function createItems(raw) {
    return raw.map(function (r, i) {
      return {
        id: r.id || 'section-' + (i + 1),
        tag: (r.tag || 'h2').toLowerCase(),
        text: (r.text || '').trim(),
      };
    });
  }

  /** Pure: CSS class for a TOC link based on heading level. */
  function linkClassFor(item) {
    return item.tag === 'h3' ? 'toc-h3' : '';
  }

  function buildTOC() {
    var article = document.querySelector('article');
    if (!article) return;
    var body = article.querySelector('.prose-body');
    if (!body) return;

    var headings = body.querySelectorAll('h2, h3');
    if (headings.length < 2) return;

    var raw = [];
    headings.forEach(function (h, i) {
      if (!h.id) h.id = 'section-' + (i + 1);
      raw.push({ id: h.id, tag: h.tagName, text: h.textContent || '' });
    });
    var items = createItems(raw);

    var nav = document.createElement('nav');
    nav.className = 'article-toc';
    nav.setAttribute('aria-label', 'Table of contents');

    var inner = document.createElement('div');
    inner.className = 'article-toc-inner';

    var title = document.createElement('div');
    title.className = 'article-toc-title';
    title.textContent = 'On this page';
    inner.appendChild(title);

    var ol = document.createElement('ol');
    items.forEach(function (item) {
      var li = document.createElement('li');
      var a = document.createElement('a');
      a.href = '#' + item.id;
      a.textContent = item.text;
      var cls = linkClassFor(item);
      if (cls) a.className = cls;
      li.appendChild(a);
      ol.appendChild(li);
    });
    inner.appendChild(ol);
    nav.appendChild(inner);

    article.classList.add('article-with-toc');

    var header = article.querySelector('header');
    var anchor = header || body;
    anchor.insertAdjacentElement('afterend', nav);

    initScrollSpy(headings, nav);
  }

  function initScrollSpy(headings, nav) {
    var links = nav.querySelectorAll('a');
    var current = -1;

    function onScroll() {
      var marker = window.scrollY + window.innerHeight * 0.35;
      var next = -1;
      for (var i = 0; i < headings.length; i++) {
        var top = headings[i].getBoundingClientRect().top + window.scrollY;
        if (top <= marker) next = i;
        else break;
      }
      if (next !== current) {
        current = next;
        links.forEach(function (a, idx) {
          a.classList.toggle('active', idx === current);
        });
      }
    }

    window.addEventListener('scroll', onScroll, { passive: true });
    window.addEventListener('resize', onScroll);
    onScroll();
  }

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = { createItems: createItems, linkClassFor: linkClassFor };
  }

  if (typeof document !== 'undefined') {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', buildTOC);
    } else {
      buildTOC();
    }
  }
})();


/* shortcuts.js */
(function () {
  'use strict';

  var SHORTCUTS = [
    { key: '?', desc: 'Toggle shortcut help' },
    { key: 's', desc: 'Focus search' },
    { key: 't', desc: 'Toggle theme' },
    { key: 'd', desc: 'Cycle info density' },
    { key: 'f', desc: 'Toggle focus mode' },
    { key: 'g', desc: 'Toggle reading guide' },
    { key: 'n', desc: 'Next section' },
    { key: 'p', desc: 'Previous section' },
    { key: 'Esc', desc: 'Close dialogs' },
  ];

  var overlay = null;
  var lastFocus = null;

  function isTyping(e) {
    var t = e.target;
    if (!t) return false;
    var tag = t.tagName;
    if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return true;
    return !!t.isContentEditable;
  }

  /* ── Cheat Sheet Overlay ── */
  function buildOverlay() {
    var ov = document.createElement('div');
    ov.className = 'shortcuts-overlay';
    ov.setAttribute('role', 'dialog');
    ov.setAttribute('aria-modal', 'true');
    ov.setAttribute('aria-label', 'Keyboard shortcuts');

    var modal = document.createElement('div');
    modal.className = 'shortcuts-modal';

    var header = document.createElement('div');
    header.className = 'shortcuts-header';
    var title = document.createElement('span');
    title.className = 'shortcuts-title';
    title.textContent = 'Keyboard shortcuts';
    var close = document.createElement('button');
    close.type = 'button';
    close.className = 'shortcuts-close';
    close.setAttribute('aria-label', 'Close');
    close.textContent = '\u00d7';
    header.appendChild(title);
    header.appendChild(close);

    var body = document.createElement('div');
    body.className = 'shortcuts-body';
    SHORTCUTS.forEach(function (s) {
      var row = document.createElement('div');
      row.className = 'shortcut-row';
      var kbd = document.createElement('kbd');
      kbd.textContent = s.key;
      var span = document.createElement('span');
      span.textContent = s.desc;
      row.appendChild(kbd);
      row.appendChild(span);
      body.appendChild(row);
    });

    modal.appendChild(header);
    modal.appendChild(body);
    ov.appendChild(modal);

    close.addEventListener('click', hideCheatSheet);
    ov.addEventListener('click', function (e) {
      if (e.target === ov) hideCheatSheet();
    });
    return ov;
  }

  function showCheatSheet() {
    if (!overlay) overlay = buildOverlay();
    lastFocus = document.activeElement;
    document.body.appendChild(overlay);
    var closeBtn = overlay.querySelector('.shortcuts-close');
    if (closeBtn) closeBtn.focus();
  }

  function hideCheatSheet() {
    if (overlay && overlay.parentNode) overlay.parentNode.removeChild(overlay);
    if (lastFocus) {
      lastFocus.focus();
      lastFocus = null;
    }
  }

  function trapCheatSheetFocus(e) {
    if (!overlay || !overlay.parentNode) return;
    if (e.key !== 'Tab') return;
    var f = overlay.querySelectorAll('button, [href], [tabindex]:not([tabindex="-1"])');
    if (f.length === 0) return;
    var first = f[0];
    var last = f[f.length - 1];
    if (e.shiftKey && document.activeElement === first) {
      e.preventDefault();
      last.focus();
    } else if (!e.shiftKey && document.activeElement === last) {
      e.preventDefault();
      first.focus();
    }
  }

  /* ── Actions ── */
  function focusSearch() {
    var input = document.getElementById('search-input');
    if (input) {
      input.focus();
      input.select();
      return;
    }
    var link = document.querySelector('a[href="/search/"]');
    if (link) window.location.href = link.getAttribute('href');
  }

  function toggleTheme() {
    var btn = document.getElementById('theme-toggle');
    if (btn) btn.click();
  }

  function cycleDensity() {
    var html = document.documentElement;
    var current = html.getAttribute('data-density') || 'standard';
    var order = ['compact', 'standard', 'comfortable'];
    var idx = order.indexOf(current);
    var next = order[(idx + 1) % order.length];
    var btn = document.querySelector('.density-btn[data-density="' + next + '"]');
    if (btn) btn.click();
  }

  function toggleSetting(id) {
    var input = document.getElementById(id);
    if (!input) return;
    input.checked = !input.checked;
    input.dispatchEvent(new Event('change', { bubbles: true }));
  }

  function scrollToSection(dir) {
    var headings = document.querySelectorAll('.prose-body h2, .prose-body h3');
    if (!headings.length) return;
    var viewport = window.scrollY + window.innerHeight * 0.4;
    var target = null;
    for (var i = 0; i < headings.length; i++) {
      var top = headings[i].getBoundingClientRect().top + window.scrollY;
      if (dir > 0) {
        if (top > viewport) { target = headings[i]; break; }
      } else if (top < viewport) {
        target = headings[i];
      }
    }
    if (!target) target = dir > 0 ? headings[0] : headings[headings.length - 1];
    var dest = target.getBoundingClientRect().top + window.scrollY - 80;
    window.scrollTo({ top: dest, behavior: 'smooth' });
  }

  function onKeydown(e) {
    if (isTyping(e)) return;

    switch (e.key) {
      case '?':
        e.preventDefault();
        showCheatSheet();
        break;
      case 'Escape':
        hideCheatSheet();
        break;
      case 's':
        e.preventDefault();
        focusSearch();
        break;
      case 't':
        e.preventDefault();
        toggleTheme();
        break;
      case 'd':
        e.preventDefault();
        cycleDensity();
        break;
      case 'f':
        e.preventDefault();
        toggleSetting('focus-toggle');
        break;
      case 'g':
        e.preventDefault();
        toggleSetting('guide-toggle');
        break;
      case 'n':
        e.preventDefault();
        scrollToSection(1);
        break;
      case 'p':
        e.preventDefault();
        scrollToSection(-1);
        break;
      default:
        break;
    }
  }

  document.addEventListener('keydown', onKeydown);
  document.addEventListener('keydown', trapCheatSheetFocus);
})();


/* motion.js */
(function () {
  'use strict';

  var REDUCED = !!(window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches);

  function initMotion() {
    var targets = document.querySelectorAll('.entrance-stagger, .reveal-on-scroll');
    if (!targets.length) return;

    /* Set stagger index on children before any reveal so delays are stable. */
    document.querySelectorAll('.entrance-stagger').forEach(function (container) {
      Array.prototype.slice.call(container.children).forEach(function (child, i) {
        child.style.setProperty('--stagger-index', String(i));
      });
    });

    if (REDUCED || !('IntersectionObserver' in window)) {
      targets.forEach(function (el) {
        el.classList.add('is-revealed');
        el.classList.add('revealed');
      });
      return;
    }

    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-revealed');
          entry.target.classList.add('revealed');
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.1, rootMargin: '0px 0px -40px 0px' });

    targets.forEach(function (el) { observer.observe(el); });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initMotion);
  } else {
    initMotion();
  }
})();


/* adaptive.js */
(function () {
  'use strict';

  var KEYS = {
    modality: 'acacia_modality',
    difficulty: 'acacia_difficulty_profile',
    interests: 'acacia_interests',
    myPath: 'acacia_my_path',
    onboardingSeen: 'acacia_onboarding_seen',
  };
  var MAX_INTERESTS = 5;
  var MODALITIES = ['visual', 'balanced', 'verbal'];

  var QUESTIONS = [
    { target: 'beginner', text: 'I am new to compliance, markets, or data engineering and usually need concepts explained from scratch.' },
    { target: 'beginner', text: 'I prefer plain-language explanations with concrete examples before any formulas or jargon.' },
    { target: 'intermediate', text: 'I can connect ideas across pillars (e.g., how a model, a rule, and a pipeline fit together).' },
    { target: 'advanced', text: 'I build or tune models, pipelines, or trading logic in production.' },
    { target: 'advanced', text: 'I regularly read research papers in these domains and follow the methods.' },
  ];
  var ANSWER_LABELS = [
    ['Not me', 0],
    ['A little', 1],
    ['Mostly', 2],
    ['Very much', 3],
  ];

  function storeGet(key) {
    try { return localStorage.getItem(key); } catch (_) { return null; }
  }
  function storeSet(key, value) {
    try { localStorage.setItem(key, value); } catch (_) {}
  }
  function storeJson(key, def) {
    try { return JSON.parse(storeGet(key)) || def; } catch (_) { return def; }
  }

  /* ── Pure helpers (exported for tests) ── */

  /** Map {target, value}[] answers to a difficulty level. */
  function computeDifficulty(answers) {
    var buckets = { beginner: 0, intermediate: 0, advanced: 0 };
    (answers || []).forEach(function (a) {
      var v = Math.max(0, Math.min(3, Number(a.value) || 0));
      if (buckets[a.target] !== undefined) buckets[a.target] += v;
    });
    var order = ['beginner', 'intermediate', 'advanced'];
    var best = 'intermediate';
    var bestScore = 0;
    order.forEach(function (lvl) {
      if (buckets[lvl] > bestScore) { bestScore = buckets[lvl]; best = lvl; }
    });
    return best;
  }

  /** Validate a saved interest selection against available options. */
  function pickInterests(all, selected, max) {
    var limit = (typeof max === 'number' && isFinite(max)) ? Math.max(0, Math.floor(max)) : MAX_INTERESTS;
    var valid = {};
    (all || []).forEach(function (c) {
      if (c && c.category) valid[c.pillar + ':' + c.category] = true;
    });
    return (selected || [])
      .filter(function (s) { return s && valid[s.pillar + ':' + s.category]; })
      .slice(0, limit);
  }

  /** Group review concepts into interest options. */
  function buildInterestOptions(concepts) {
    var map = {};
    (concepts || []).forEach(function (c) {
      if (!c || !c.category) return;
      var key = c.pillar + ':' + c.category;
      if (!map[key]) {
        map[key] = { pillar: c.pillar, category: c.category, label: '', count: 0 };
      }
      map[key].count++;
    });
    return Object.keys(map).map(function (k) { return map[k]; })
      .sort(function (a, b) { return b.count - a.count; });
  }

  /** Decorate path entries with review status. */
  function pathStatus(path, mastery, now) {
    now = now || Date.now();
    return (path || []).map(function (p) {
      var m = (mastery || {})[p.id] || {};
      var due = Number(m.due) || 0;
      var reps = Number(m.reps) || 0;
      var status;
      if (reps === 0) status = 'new';
      else if (due > 0 && due <= now) status = 'due';
      else if (due > 0) status = 'scheduled';
      else status = 'new';
      return { id: p.id, label: p.label, pillar: p.pillar, status: status, due: due };
    });
  }

  /* ── Data helpers ── */

  var conceptsCache = null;

  function fetchConcepts() {
    if (conceptsCache) return Promise.resolve(conceptsCache);
    var base = document.querySelector('script[src*="app.js"], script[src*="search.js"]');
    var prefix = base ? base.src.replace(/js\/[\w.-]+\.js.*$/, '') : '';
    return fetch(prefix + 'static/review_concepts.json')
      .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
      .then(function (data) {
        conceptsCache = data.concepts || [];
        return conceptsCache;
      })
      .catch(function () { conceptsCache = []; return conceptsCache; });
  }

  function masteryData() {
    return storeJson('acacia_concept_mastery', {});
  }

  /* ── Modality ── */
  function initModality() {
    var html = document.documentElement;
    var saved = storeGet(KEYS.modality) || 'balanced';
    if (MODALITIES.indexOf(saved) === -1) saved = 'balanced';

    function apply(mode, persist) {
      if (MODALITIES.indexOf(mode) === -1) mode = 'balanced';
      html.setAttribute('data-modality', mode);
      document.querySelectorAll('[data-modality]').forEach(function (btn) {
        btn.classList.toggle('active', btn.getAttribute('data-modality') === mode);
      });
      if (persist !== false) storeSet(KEYS.modality, mode);
    }
    document.querySelectorAll('[data-modality]').forEach(function (btn) {
      btn.addEventListener('click', function () {
        apply(btn.getAttribute('data-modality'));
      });
    });
    apply(saved, false);
  }

  /* ── Calibration modal ── */
  function openCalibration() {
    var overlay = buildOverlay('Calibrate difficulty', 'How much do these describe you?');
    var body = overlay.querySelector('.shortcuts-body');

    var intro = document.createElement('p');
    intro.className = 'adaptive-note';
    intro.textContent = 'Answer 5 quick questions — this tunes content difficulty to your level.';
    body.appendChild(intro);

    var current = storeGet(KEYS.difficulty) || 'not set';
    var meta = document.createElement('p');
    meta.className = 'adaptive-note adaptive-current';
    meta.textContent = 'Current profile: ' + current;
    body.appendChild(meta);

    var answers = {};
    QUESTIONS.forEach(function (q, qi) {
      var row = document.createElement('div');
      row.className = 'adaptive-question';
      var text = document.createElement('div');
      text.className = 'adaptive-question-text';
      text.textContent = (qi + 1) + '. ' + q.text;
      row.appendChild(text);

      var opts = document.createElement('div');
      opts.className = 'adaptive-options';
      ANSWER_LABELS.forEach(function (pair) {
        var label = pair[0];
        var value = pair[1];
        var btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'mini-btn';
        btn.textContent = label;
        btn.addEventListener('click', function () {
          opts.querySelectorAll('.mini-btn').forEach(function (b) { b.classList.remove('active'); });
          btn.classList.add('active');
          answers[qi] = { target: q.target, value: value };
        });
        opts.appendChild(btn);
      });
      row.appendChild(opts);
      body.appendChild(row);
    });

    var actions = document.createElement('div');
    actions.className = 'adaptive-actions';

    var reset = document.createElement('button');
    reset.type = 'button';
    reset.className = 'mini-btn ghost';
    reset.textContent = 'Reset';
    reset.addEventListener('click', function () {
      storeSet(KEYS.difficulty, '');
      html_set('data-difficulty-profile', '');
      overlay.remove();
    });

    var save = document.createElement('button');
    save.type = 'button';
    save.className = 'mini-btn primary';
    save.textContent = 'Save profile';
    save.addEventListener('click', function () {
      var allAnswered = QUESTIONS.every(function (_, qi) { return answers[qi]; });
      if (!allAnswered) {
        meta.textContent = 'Please answer every question.';
        meta.classList.add('warn');
        return;
      }
      var level = computeDifficulty(Object.keys(answers).map(function (k) { return answers[k]; }));
      storeSet(KEYS.difficulty, level);
      html_set('data-difficulty-profile', level);
      meta.textContent = 'Profile saved: ' + level;
      meta.classList.remove('warn');
      setTimeout(function () { overlay.remove(); }, 600);
    });

    actions.appendChild(reset);
    actions.appendChild(save);
    body.appendChild(actions);
  }

  function html_set(attr, val) {
    var html = document.documentElement;
    if (val) html.setAttribute(attr, val);
    else html.removeAttribute(attr);
  }

  /* ── Interests onboarding + management ── */
  function openInterests(firstVisit) {
    var overlay = buildOverlay('Your interests', firstVisit
      ? 'Pick a few topics to personalise review sessions and recommendations.'
      : 'Pick topics to personalise your learning.');
    var body = overlay.querySelector('.shortcuts-body');

    var options = [];
    var selected = storeJson(KEYS.interests, []);

    function renderSelected() {
      body.querySelectorAll('.interest-chip').forEach(function (chip) {
        var key = chip.getAttribute('data-key');
        chip.classList.toggle('active', selected.some(function (s) { return s.pillar + ':' + s.category === key; }));
      });
    }

    fetchConcepts().then(function (concepts) {
      options = buildInterestOptions(concepts);
      var grid = document.createElement('div');
      grid.className = 'interest-grid';
      options.forEach(function (opt) {
        var key = opt.pillar + ':' + opt.category;
        var label = (opt.category || '').replace(/-/g, ' ');
        var chip = document.createElement('button');
        chip.type = 'button';
        chip.className = 'interest-chip';
        chip.setAttribute('data-key', key);
        chip.textContent = label + ' (' + opt.count + ')';
        chip.addEventListener('click', function () {
          var idx = selected.findIndex(function (s) { return s.pillar + ':' + s.category === key; });
          if (idx !== -1) {
            selected.splice(idx, 1);
          } else if (selected.length < MAX_INTERESTS) {
            selected.push({ pillar: opt.pillar, category: opt.category, label: label, count: opt.count });
          }
          renderSelected();
        });
        grid.appendChild(chip);
      });
      body.appendChild(grid);

      var hint = document.createElement('p');
      hint.className = 'adaptive-note';
      hint.textContent = 'Up to ' + MAX_INTERESTS + ' topics.';
      body.appendChild(hint);

      var actions = document.createElement('div');
      actions.className = 'adaptive-actions';
      var skip = document.createElement('button');
      skip.type = 'button';
      skip.className = 'mini-btn ghost';
      skip.textContent = firstVisit ? 'Skip for now' : 'Close';
      skip.addEventListener('click', function () { overlay.remove(); });
      var save = document.createElement('button');
      save.type = 'button';
      save.className = 'mini-btn primary';
      save.textContent = 'Save interests';
      save.addEventListener('click', function () {
        storeSet(KEYS.interests, JSON.stringify(pickInterests(concepts, selected)));
        renderInterestStrip();
        overlay.remove();
      });
      actions.appendChild(skip);
      actions.appendChild(save);
      body.appendChild(actions);
    });

    function syncSelected() {
      selected = storeJson(KEYS.interests, []);
    }
    overlay.addEventListener('keydown', function (e) { if (e.key === 'Escape') overlay.remove(); });
    syncSelected();
  }

  function initInterests() {
    var seen = storeGet(KEYS.onboardingSeen) === '1';
    if (!seen) {
      storeSet(KEYS.onboardingSeen, '1');
      setTimeout(function () {
        var saved = storeJson(KEYS.interests, []);
        if (!saved.length) openInterests(true);
      }, 1200);
    }
    renderInterestStrip();
  }

  /* ── Interest strip ── */
  function renderInterestStrip() {
    var main = document.getElementById('main-content');
    if (!main) return;
    var saved = storeJson(KEYS.interests, []);
    var existing = document.getElementById('interests-bar');
    if (existing) existing.remove();
    if (!saved.length) return;

    var bar = document.createElement('div');
    bar.id = 'interests-bar';
    bar.className = 'interests-bar';
    var label = document.createElement('span');
    label.className = 'interests-label';
    label.textContent = 'Your interests:';
    bar.appendChild(label);

    saved.forEach(function (s) {
      var a = document.createElement('a');
      a.className = 'interest-chip static';
      a.href = '/search/?q=' + encodeURIComponent(s.label || s.category || '');
      a.textContent = s.label || s.category;
      bar.appendChild(a);
    });

    var manage = document.createElement('button');
    manage.type = 'button';
    manage.className = 'mini-btn ghost';
    manage.textContent = 'Edit';
    manage.setAttribute('aria-label', 'Edit interests');
    manage.addEventListener('click', function () { openInterests(false); });
    bar.appendChild(manage);

    main.insertBefore(bar, main.firstChild);
  }

  /* ── Concept next-actions (Phase F) ── */
  function initConceptActions() {
    var host = document.querySelector('[data-concept-actions]');
    if (!host) return;
    var id = host.getAttribute('data-concept-id') || '';
    var label = host.getAttribute('data-concept-label') || id;
    var pillar = host.getAttribute('data-concept-pillar') || 'aml';

    var path = storeJson(KEYS.myPath, []);
    var onPath = path.some(function (p) { return p.id === id; });
    var mastery = masteryData()[id] || {};
    var due = Number(mastery.due) || 0;
    var reps = Number(mastery.reps) || 0;
    var now = Date.now();
    var dueLabel = reps === 0 ? 'New to you' : (due > 0 && due <= now ? 'Due now' : 'Not due yet');

    var actions = [
      { key: 'review', label: 'Review now', desc: dueLabel, href: '/review/' },
      { key: 'gaps', label: 'Find gaps', desc: 'Targeted review', href: '/review/' },
      { key: 'graph', label: 'See connections', desc: 'Knowledge graph', href: '/graph/?concept=' + encodeURIComponent(id) },
    ];
    if (onPath) {
      actions.unshift({ key: 'path', label: 'In My Path', desc: 'Remove', href: null });
    } else {
      actions.unshift({ key: 'path', label: 'Add to My Path', desc: 'Track this concept', href: null });
    }

    var grid = document.createElement('div');
    grid.className = 'concept-actions';

    actions.forEach(function (act) {
      var el = document.createElement('a');
      el.className = 'ghost-card p-3 block transition text-decoration-none hover:shadow-sm concept-action';
      var title = document.createElement('span');
      title.className = 'block text-sm font-semibold text-default';
      title.textContent = act.label;
      var desc = document.createElement('span');
      desc.className = 'block text-xs text-muted mt-0.5';
      desc.textContent = act.desc;
      el.appendChild(title);
      el.appendChild(desc);

      if (act.key === 'path') {
        el.href = '#';
        el.addEventListener('click', function (e) {
          e.preventDefault();
          togglePath(id, label, pillar);
        });
        el.classList.toggle('path-active', onPath);
      } else {
        el.href = act.href;
      }
      grid.appendChild(el);
    });

    host.appendChild(grid);
  }

  function togglePath(id, label, pillar) {
    var path = storeJson(KEYS.myPath, []);
    var idx = path.findIndex(function (p) { return p.id === id; });
    if (idx !== -1) path.splice(idx, 1);
    else path.push({ id: id, label: label, pillar: pillar, addedAt: Date.now() });
    storeSet(KEYS.myPath, JSON.stringify(path));
    renderMyPath();
    initConceptActions();
  }

  /* ── My Path widget (review page) ── */
  function renderMyPath() {
    var container = document.getElementById('my-path-list');
    if (!container) return;
    var path = storeJson(KEYS.myPath, []);
    var mastery = masteryData();
    var now = Date.now();
    var decorated = pathStatus(path, mastery, now);

    container.innerHTML = '';

    if (!path.length) {
      container.innerHTML = '<p class="text-sm text-muted">No concepts yet. Open any concept page and use \u201cAdd to My Path\u201d to build a personal learning path.</p>';
      return;
    }

    var list = document.createElement('ul');
    list.className = 'space-y-2';
    decorated.forEach(function (p) {
      var li = document.createElement('li');
      li.className = 'ghost-card p-3 flex items-center justify-between gap-3';

      var link = document.createElement('a');
      link.href = '/concepts/' + encodeURIComponent(p.id) + '/';
      link.className = 'block no-underline min-w-0';
      var title = document.createElement('span');
      title.className = 'block text-sm font-semibold text-default truncate';
      title.textContent = p.label;
      var meta = document.createElement('span');
      meta.className = 'block text-xs text-muted mt-0.5';
      meta.textContent = statusLabel(p.status);
      link.appendChild(title);
      link.appendChild(meta);

      var remove = document.createElement('button');
      remove.type = 'button';
      remove.className = 'mini-btn ghost';
      remove.setAttribute('aria-label', 'Remove from path');
      remove.textContent = '\u00d7';
      remove.addEventListener('click', function () {
        var list2 = storeJson(KEYS.myPath, []).filter(function (x) { return x.id !== p.id; });
        storeSet(KEYS.myPath, JSON.stringify(list2));
        renderMyPath();
      });

      li.appendChild(link);
      li.appendChild(remove);
      list.appendChild(li);
    });
    container.appendChild(list);

    var done = decorated.filter(function (p) { return p.status === 'new'; }).length;
    var summary = document.createElement('p');
    summary.className = 'text-xs text-muted mt-3';
    summary.textContent = path.length + ' concept' + (path.length !== 1 ? 's' : '') + ' on your path \u00b7 ' + done + ' not yet reviewed';
    container.appendChild(summary);
  }

  function statusLabel(status) {
    if (status === 'due') return '\u26a0 Due for review';
    if (status === 'scheduled') return '\u23f3 Scheduled';
    return '\u2728 Not yet reviewed';
  }

  /* ── Shared modal builder ── */
  function buildOverlay(titleText, subtitle) {
    var overlay = document.createElement('div');
    overlay.className = 'shortcuts-overlay';
    overlay.setAttribute('role', 'dialog');
    overlay.setAttribute('aria-modal', 'true');
    overlay.setAttribute('aria-label', titleText);

    var modal = document.createElement('div');
    modal.className = 'shortcuts-modal adaptive-modal';

    var header = document.createElement('div');
    header.className = 'shortcuts-header';
    var title = document.createElement('span');
    title.className = 'shortcuts-title';
    title.textContent = titleText;
    var close = document.createElement('button');
    close.type = 'button';
    close.className = 'shortcuts-close';
    close.setAttribute('aria-label', 'Close');
    close.textContent = '\u00d7';
    close.addEventListener('click', function () { overlay.remove(); });
    header.appendChild(title);
    header.appendChild(close);

    var body = document.createElement('div');
    body.className = 'shortcuts-body adaptive-body';
    if (subtitle) {
      var sub = document.createElement('p');
      sub.className = 'adaptive-note';
      sub.textContent = subtitle;
      body.appendChild(sub);
    }

    modal.appendChild(header);
    modal.appendChild(body);
    overlay.appendChild(modal);

    overlay.addEventListener('click', function (e) { if (e.target === overlay) overlay.remove(); });
    document.body.appendChild(overlay);
    return overlay;
  }

  /* ── Init ── */
  function init() {
    initModality();
    initInterests();

    var calibrateBtn = document.getElementById('calibrate-btn');
    if (calibrateBtn) calibrateBtn.addEventListener('click', openCalibration);

    var interestsBtn = document.getElementById('interests-btn');
    if (interestsBtn) interestsBtn.addEventListener('click', function () { openInterests(false); });

    initConceptActions();
    renderMyPath();
  }

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
      computeDifficulty: computeDifficulty,
      pickInterests: pickInterests,
      buildInterestOptions: buildInterestOptions,
      pathStatus: pathStatus,
    };
  }

  if (typeof document !== 'undefined') {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', init);
    } else {
      init();
    }
  }
})();


/* search.js */
(function() {
  'use strict';

  const PILLAR_URL_MAP = { aml: 'compliance', stock: 'markets', 'data-engineering': 'data' };
  const PILLAR_LABELS = { aml: 'Compliance', stock: 'Markets', 'data-engineering': 'Data' };
  const PILLAR_COLORS = { aml: '#f59e0b', stock: '#16a34a', 'data-engineering': '#6366f1' };
  const CT_LABELS = { research: 'Research', learn: 'Learn', knowledge: 'Knowledge' };
  const DIFF_LABELS = { beginner: 'Beginner', intermediate: 'Intermediate', advanced: 'Advanced' };
  const PAGE_SIZE = 20;

  function slugToUrl(slug) {
    const parts = slug.split('/');
    const pillar = PILLAR_URL_MAP[parts[0]] || parts[0];
    if (parts.length === 1) return '/' + parts[0] + '/';
    return '/' + [pillar].concat(parts.slice(1)).join('/') + '/';
  }

  function escapeHtml(s) {
    const d = document.createElement('div');
    d.textContent = s;
    return d.innerHTML;
  }

  function highlightTerms(text, terms) {
    if (!terms.length) return escapeHtml(text);
    let safe = escapeHtml(text);
    for (const t of terms) {
      const re = new RegExp('(' + t.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + ')', 'gi');
      safe = safe.replace(re, '<mark>$1</mark>');
    }
    return safe;
  }

  function tokenize(q) {
    return q.toLowerCase().split(/\s+/).filter(Boolean);
  }

  function stem(w) {
    w = w.toLowerCase();
    if (w.length > 5) {
      if (w.endsWith('ing')) w = w.slice(0, -3);
      else if (w.endsWith('ingly')) w = w.slice(0, -5);
      else if (w.endsWith('ed')) w = w.slice(0, -2);
      else if (w.endsWith('tion')) w = w.slice(0, -4);
      else if (w.endsWith('s') && !w.endsWith('ss')) w = w.slice(0, -1);
      else if (w.endsWith('ies')) w = w.slice(0, -3) + 'y';
    }
    return w;
  }

  function levenshtein(a, b) {
    if (a === b) return 0;
    if (!a.length) return b.length;
    if (!b.length) return a.length;
    const prev2 = new Array(b.length + 1).fill(0);
    const prev = new Array(b.length + 1).fill(0);
    const cur = new Array(b.length + 1).fill(0);
    for (let j = 0; j <= b.length; j++) prev[j] = j;
    for (let i = 1; i <= a.length; i++) {
      cur[0] = i;
      for (let j = 1; j <= b.length; j++) {
        cur[j] = Math.min(
          prev[j] + 1,
          cur[j - 1] + 1,
          prev[j - 1] + (a[i - 1] === b[j - 1] ? 0 : 1)
        );
        if (i > 1 && j > 1 && a[i - 1] === b[j - 2] && a[i - 2] === b[j - 1]) {
          cur[j] = Math.min(cur[j], prev2[j - 2] + 1);
        }
      }
      for (let j = 0; j <= b.length; j++) {
        prev2[j] = prev[j];
        prev[j] = cur[j];
      }
    }
    return prev[b.length];
  }

  // Returns true if term matches text via substring, stemming, or fuzzy edit distance.
  function termMatches(term, text) {
    if (!text) return false;
    if (text.includes(term)) return true;
    const st = stem(term);
    if (st.length >= 3 && text.includes(st)) return true;
    // Fuzzy: within 1 edit for terms >= 4 chars, and term length similar to a candidate word
    if (term.length >= 4) {
      const words = text.split(/[^a-z0-9+.-]+/);
      for (const w of words) {
        if (Math.abs(w.length - term.length) > 1) continue;
        if (levenshtein(w, term) <= 1) return true;
      }
    }
    return false;
  }

  /* ── "Did you mean?" spelling correction (pure) ── */

  function buildVocabulary(index, concepts) {
    const set = {};
    const add = function(text) {
      if (!text) return;
      String(text).toLowerCase().split(/[^a-z0-9+.-]+/).forEach(function(w) {
        if (w.length > 3) set[w] = true;
      });
    };
    (index || []).forEach(function(e) {
      add(e.title);
      (e.tags || []).forEach(add);
      (e.ontology_concepts || []).forEach(add);
      (e.technologies || []).forEach(add);
      (e.use_cases || []).forEach(add);
    });
    (concepts || []).forEach(function(c) {
      add(c.label);
      (c.aliases || []).forEach(add);
    });
    return Object.keys(set);
  }

  // Returns the closest vocabulary word within `maxEdits`, or null for an exact match / no candidate.
  function bestCorrection(token, vocab, maxEdits) {
    if (token.length < 3) return null;
    const limit = token.length >= 6 ? (maxEdits || 2) : Math.min(1, maxEdits || 1);
    let best = null;
    let bestDist = Infinity;
    for (let i = 0; i < vocab.length; i++) {
      const w = vocab[i];
      // Skip prefix-extension matches: a valid short term ("aml") must not be
      // "corrected" to a longer vocab word it is merely a prefix of ("amla").
      if (w.startsWith(token) || token.startsWith(w)) continue;
      const dist = levenshtein(w, token);
      if (dist === 0) return null;
      if (dist > limit) continue;
      if (dist < bestDist) { bestDist = dist; best = w; }
    }
    return best;
  }

  // Returns a corrected query string when most tokens have close vocabulary matches, else null.
  function didYouMean(query, vocab, maxEdits) {
    if (!query || !vocab || !vocab.length) return null;
    const tokens = tokenize(query);
    if (!tokens.length) return null;
    const corrected = [];
    let changed = 0;
    for (const t of tokens) {
      const w = bestCorrection(t, vocab, maxEdits);
      if (w) { corrected.push(w); changed++; }
      else corrected.push(t);
    }
    if (!changed) return null;
    if (changed * 2 <= tokens.length) return null;
    const out = corrected.join(' ');
    return out.toLowerCase() === query.toLowerCase() ? null : out;
  }

  function scoreEntry(entry, terms) {
    const title = (entry.title || '').toLowerCase();
    const desc = (entry.description || '').toLowerCase();
    const tags = (entry.tags || []).join(' ').toLowerCase();
    const concepts = (entry.ontology_concepts || []).join(' ').toLowerCase();
    const technologies = (entry.technologies || []).join(' ').toLowerCase();
    const use_cases = (entry.use_cases || []).join(' ').toLowerCase();
    let score = 0;

    for (const t of terms) {
      if (termMatches(t, title)) score += 10;
      if (termMatches(t, tags)) score += 4;
      if (termMatches(t, concepts)) score += 6;
      if (termMatches(t, technologies)) score += 3;
      if (termMatches(t, use_cases)) score += 2;
      if (termMatches(t, desc)) score += 2;
    }

    score += (entry.concept_boost || 0) * 5;

    const sqi = entry.avg_sqi || 0;
    if (sqi >= 0.8) score += 0.5;
    else if (sqi >= 0.65) score += 0.25;

    if (entry.difficulty) score += 0.5;

    return score;
  }

  function matchesFilters(entry, filters) {
    if (filters.pillar.length && !filters.pillar.includes(entry.pillar || '')) return false;
    if (filters.type.length && !filters.type.includes(entry.content_type || '')) return false;
    if (filters.difficulty.length && !filters.difficulty.includes(entry.difficulty || '')) return false;
    if (filters.bloom.length && !filters.bloom.includes(entry.bloom || '')) return false;
    if (filters.technology.length) {
      var techs = entry.technologies || [];
      var hasMatch = filters.technology.some(function(t) { return techs.indexOf(t) !== -1; });
      if (!hasMatch) return false;
    }
    return true;
  }

  function readFilters() {
    const filters = { pillar: [], type: [], difficulty: [], bloom: [], technology: [] };
    document.querySelectorAll('.filter-checkbox:checked').forEach(cb => {
      const group = cb.getAttribute('data-group');
      if (group && filters.hasOwnProperty(group)) filters[group].push(cb.value);
    });
    return filters;
  }

  function updateFacetCounts(index) {
    const counts = {};
    for (const group of ['pillar', 'type', 'difficulty', 'bloom']) {
      counts[group] = {};
      document.querySelectorAll('.filter-checkbox[data-group="' + group + '"]').forEach(cb => {
        counts[group][cb.value] = 0;
      });
    }
    for (const e of index) {
      const p = e.pillar || '';
      const t = e.content_type || '';
      const d = e.difficulty || '';
      const b = e.bloom || '';
      if (counts.pillar.hasOwnProperty(p)) counts.pillar[p] += 1;
      if (counts.type.hasOwnProperty(t)) counts.type[t] += 1;
      if (counts.difficulty.hasOwnProperty(d)) counts.difficulty[d] += 1;
      if (counts.bloom.hasOwnProperty(b)) counts.bloom[b] += 1;
    }
    document.querySelectorAll('.filter-count').forEach(el => {
      const g = el.getAttribute('data-group');
      const v = el.getAttribute('data-value');
      const n = (counts[g] && counts[g][v]) || 0;
      el.textContent = n ? '(' + n + ')' : '';
    });
  }

  function syncFiltersToUrl(filters) {
    const url = new URL(window.location);
    for (const key of ['pillar', 'type', 'difficulty', 'bloom', 'technology']) {
      if (filters[key].length) url.searchParams.set('f_' + key, filters[key].join(','));
      else url.searchParams.delete('f_' + key);
    }
    history.replaceState(null, '', url);
  }

  const STORAGE_KEY = 'ac_search_history';
  const MAX_SUGGESTIONS = 10;

  let conceptIndex = null;

  function fetchConcepts() {
    if (conceptIndex) return Promise.resolve(conceptIndex);
    return fetch(staticBase() + 'review_concepts.json')
      .then(r => { if (!r.ok) throw new Error(r.status); return r.json(); })
      .then(data => {
        conceptIndex = (data.concepts || []).map(c => ({
          label: c.label || c.conceptSlug || '',
          slug: c.conceptSlug || (c.id || '').replace(/^concept:/, ''),
          aliases: (c.aliases || []).filter(a => typeof a === 'string' && a.length > 1),
          pillar: c.pillar || '',
          category: c.category || ''
        }));
        return conceptIndex;
      })
      .catch(() => { conceptIndex = []; return conceptIndex; });
  }

  function getInterests() {
    try { return JSON.parse(localStorage.getItem('acacia_interests')) || []; } catch { return []; }
  }

  let vocabCache = null;
  function getVocabulary(index) {
    if (!vocabCache) vocabCache = buildVocabulary(index, conceptIndex || []);
    return vocabCache;
  }

  function getHistory() {
    try { return JSON.parse(localStorage.getItem(STORAGE_KEY)) || []; } catch { return []; }
  }

  function saveQuery(q) {
    const trimmed = q.trim().toLowerCase();
    if (!trimmed) return;
    let history = getHistory().filter(h => h !== trimmed);
    history.unshift(trimmed);
    if (history.length > MAX_SUGGESTIONS) history = history.slice(0, MAX_SUGGESTIONS);
    try { localStorage.setItem(STORAGE_KEY, JSON.stringify(history)); } catch {}
  }

  function setSuggestionsOpen(el, open) {
    el.style.display = open ? 'block' : 'none';
    const input = document.getElementById('search-input');
    if (input) input.setAttribute('aria-expanded', open ? 'true' : 'false');
  }

  function renderSuggestions(filter) {
    const el = document.getElementById('search-suggestions');
    if (!el) return;
    const needle = (filter || '').toLowerCase().trim();
    const needleTerms = needle ? tokenize(needle) : [];

    const history = getHistory();
    const matchingHistory = needle
      ? history.filter(h => h.toLowerCase().includes(needle))
      : history;

    const concepts = conceptIndex || [];

    let conceptHtml = '';
    if (needle) {
      const matchingConcepts = concepts.filter(c =>
        c.label.toLowerCase().includes(needle) ||
        c.aliases.some(a => a.toLowerCase().includes(needle)) ||
        needleTerms.every(t => c.label.toLowerCase().includes(t)));
      conceptHtml = matchingConcepts.slice(0, 6).map(c =>
        '<a class="suggestion-item" role="option" href="/concepts/' + encodeURIComponent(c.slug) + '/" data-kind="concept" style="display:flex;align-items:center;gap:0.5rem;padding:0.5rem 0.75rem;cursor:pointer;font-size:0.9rem;border-bottom:1px solid var(--color-border, #333);text-decoration:none;color:inherit">' +
        '<span style="font-size:0.75rem;opacity:0.6">&#128214;</span>' +
        '<span style="color:var(--color-accent, #818cf8);font-weight:600">' + highlightTerms(escapeHtml(c.label), needleTerms) + '</span>' +
        '<span style="font-size:0.7rem;opacity:0.6;margin-left:auto">Concept</span>' +
        '</a>'
      ).join('');
    } else {
      // Exploration prompts: prefer the user's interest categories, fall back to top concepts.
      const interests = getInterests();
      const pick = interests.length
        ? concepts.filter(c => interests.some(i => i.pillar === c.pillar && i.category === c.category))
        : concepts;
      const seen = {};
      const chips = [];
      pick.forEach(function(c) {
        if (seen[c.label]) return;
        seen[c.label] = true;
        chips.push(c);
      });
      conceptHtml = chips.slice(0, 5).map(c =>
        '<a class="suggestion-item" role="option" href="/concepts/' + encodeURIComponent(c.slug) + '/" data-kind="concept" style="display:flex;align-items:center;gap:0.5rem;padding:0.5rem 0.75rem;cursor:pointer;font-size:0.9rem;border-bottom:1px solid var(--color-border, #333);text-decoration:none;color:inherit">' +
        '<span style="font-size:0.75rem;opacity:0.6">&#128214;</span>' +
        '<span style="color:var(--color-accent, #818cf8);font-weight:600">' + escapeHtml(c.label) + '</span>' +
        '<span style="font-size:0.7rem;opacity:0.6;margin-left:auto">' + (interests.length ? 'For you' : 'Explore') + '</span>' +
        '</a>'
      ).join('');
    }

    const historyHtml = matchingHistory.slice(0, 4).map((h, i) =>
      '<div class="suggestion-item" role="option" data-suggestion="' + escapeHtml(h) + '" data-idx="' + i + '" data-kind="history" style="padding:0.5rem 0.75rem;cursor:pointer;font-size:0.9rem;border-bottom:1px solid var(--color-border, #333);display:flex;align-items:center;gap:0.5rem">' +
      '<span style="font-size:0.75rem;opacity:0.6">&#128337;</span>' +
      highlightTerms(escapeHtml(h), needle ? needleTerms : []) +
      '</div>'
    ).join('');

    let titleHtml = '';
    if (needle && searchIndex) {
      titleHtml = searchIndex
        .filter(function(e) { return e.title && e.title.toLowerCase().includes(needle); })
        .slice(0, 4)
        .map(function(e) {
          return '<div class="suggestion-item" role="option" data-suggestion="' + escapeHtml(e.title) + '" data-kind="title" style="padding:0.5rem 0.75rem;cursor:pointer;font-size:0.9rem;border-bottom:1px solid var(--color-border, #333);display:flex;align-items:center;gap:0.5rem">' +
            '<span style="font-size:0.75rem;opacity:0.6">&#128269;</span>' +
            highlightTerms(escapeHtml(e.title), needleTerms) +
            '<span style="font-size:0.7rem;opacity:0.6;margin-left:auto">' + escapeHtml(CT_LABELS[e.content_type] || e.content_type || '') + '</span>' +
            '</div>';
        })
        .join('');
    }

    if (!needle && !matchingHistory.length && !conceptHtml) {
      el.innerHTML = '';
      setSuggestionsOpen(el, false);
      return;
    }

    if (needle && !searchIndex) {
      fetchIndex().then(function() { renderSuggestions(filter); }).catch(function() {});
    }

    const combined = [];
    if (conceptHtml) combined.push(conceptHtml);
    if (titleHtml) combined.push(titleHtml);
    if (historyHtml) combined.push(historyHtml);
    if (!combined.length) { el.innerHTML = ''; setSuggestionsOpen(el, false); return; }
    el.innerHTML = combined.join('');
    setSuggestionsOpen(el, true);
  }

  function firePlausible(event, props) {
    if (typeof plausible === 'function') {
      try { plausible(event, { props: props || {} }); } catch {}
    }
  }

  let searchIndex = null;
  let allScored = [];
  let displayedCount = 0;
  let currentTerms = [];
  let selectedIndex = -1;
  let suggestionIndex = -1;

  function populateTechFilters(index) {
    var container = document.getElementById('tech-filter-list');
    if (!container) return;
    // Preserve current selection across re-renders (this runs on every search)
    var checkedTechs = {};
    container.querySelectorAll('.filter-checkbox:checked').forEach(function(cb) {
      checkedTechs[cb.value] = true;
    });
    var techMap = {};
    for (var i = 0; i < index.length; i++) {
      var techs = index[i].technologies || [];
      for (var j = 0; j < techs.length; j++) {
        techMap[techs[j]] = (techMap[techs[j]] || 0) + 1;
      }
    }
    var sorted = Object.keys(techMap).sort(function(a, b) { return techMap[b] - techMap[a]; });
    var topTechs = sorted.slice(0, 20);
    if (!topTechs.length) {
      container.innerHTML = '<span style="font-size:0.75rem;color:var(--color-text-muted,#666)">No technologies detected</span>';
      return;
    }
    container.innerHTML = topTechs.map(function(t) {
      return '<label style="display:flex;align-items:center;gap:0.4rem;font-size:0.85rem;padding:0.2rem 0;cursor:pointer" title="' + techMap[t] + ' items">' +
        '<input type="checkbox" value="' + escapeHtml(t) + '" class="filter-checkbox" data-group="technology"> ' +
        escapeHtml(t) +
        '<span style="font-size:0.65rem;color:var(--color-text-muted,#888);margin-left:auto">' + techMap[t] + '</span>' +
        '</label>';
    }).join('') +
    (sorted.length > 20 ? '<details style="font-size:0.75rem;margin-top:0.25rem"><summary style="cursor:pointer;color:var(--color-text-muted,#888)">+' + (sorted.length - 20) + ' more</summary>' +
      sorted.slice(20).map(function(t) {
        return '<label style="display:flex;align-items:center;gap:0.4rem;font-size:0.8rem;padding:0.15rem 0;cursor:pointer" title="' + techMap[t] + ' items">' +
          '<input type="checkbox" value="' + escapeHtml(t) + '" class="filter-checkbox" data-group="technology"> ' +
          escapeHtml(t) +
          '<span style="font-size:0.65rem;color:var(--color-text-muted,#888);margin-left:auto">' + techMap[t] + '</span>' +
          '</label>';
      }).join('') + '</details>' : '');
    container.querySelectorAll('.filter-checkbox').forEach(function(cb) {
      if (checkedTechs[cb.value]) cb.checked = true;
    });
  }

  function staticBase() {
    const base = document.querySelector('script[src*="search.js"], script[src*="app.js"]');
    if (base) {
      const m = base.src.match(/^(.*\/static\/)js\/[^/]+\.js(?:$|[?#])/);
      if (m) return m[1];
      const m2 = base.src.match(/^(.*\/)js\/[^/]+\.js(?:$|[?#])/);
      if (m2) return m2[1];
    }
    return window.location.origin + '/static/';
  }

  function fetchIndex() {
    if (searchIndex) return Promise.resolve(searchIndex);

    // If a single pillar is pre-filtered, load just that chunk
    const filters = readFilters();
    let url = staticBase() + 'search-index.json';
    if (filters.pillar.length === 1) {
      url = staticBase() + 'search-index.' + filters.pillar[0] + '.json';
    }

    return fetch(url)
      .then(r => { if (!r.ok) throw new Error(r.status); return r.json(); })
      .then(data => { searchIndex = data; return data; });
  }

  function renderResult(entry, terms, idx) {
    const url = slugToUrl(entry.slug);
    const pillar = entry.pillar || '';
    const color = PILLAR_COLORS[pillar] || '#888';
    const pLabel = PILLAR_LABELS[pillar] || pillar;
    const ct = entry.content_type || '';
    const ctLabel = CT_LABELS[ct] || ct;
    const difficulty = entry.difficulty || '';
    const diffLabel = DIFF_LABELS[difficulty] || '';
    const concepts = entry.ontology_concepts || [];
    const sqi = entry.avg_sqi || 0;
    const isSelected = idx === selectedIndex;

    let html = '<a href="' + url + '" class="search-result" data-idx="' + idx + '" data-slug="' + escapeHtml(entry.slug) + '" data-pillar="' + escapeHtml(pillar) + '" style="display:block;padding:1rem;margin-bottom:0.5rem;border:1px solid ' + (isSelected ? 'var(--color-accent, #818cf8)' : 'var(--color-border, #333)') + ';border-left:3px solid ' + color + ';border-radius:8px;text-decoration:none;color:var(--color-text, #e8e6e3);transition:border-color 0.2s' + (isSelected ? ';background:color-mix(in srgb, var(--color-accent, #818cf8) 8%, transparent)' : '') + '">';
    html += '<div style="display:flex;gap:0.5rem;align-items:center;margin-bottom:0.25rem;flex-wrap:wrap">';
    html += '<span style="display:inline-block;padding:2px 8px;border-radius:9999px;font-size:0.7rem;font-weight:600;color:#fff;background:' + color + '">' + escapeHtml(pLabel) + '</span>';
    if (ctLabel) html += '<span style="font-size:0.7rem;color:var(--color-text-muted, #888)">' + escapeHtml(ctLabel) + '</span>';
    if (diffLabel) html += '<span style="font-size:0.7rem;color:var(--color-text-muted, #888)">' + escapeHtml(diffLabel) + '</span>';
    if (entry.date_str) html += '<span style="font-size:0.7rem;color:var(--color-text-muted, #888)">' + escapeHtml(entry.date_str) + '</span>';
    if (sqi > 0) {
      const sqiColor = sqi >= 0.8 ? '#22c55e' : sqi >= 0.65 ? '#d97706' : '#ef4444';
      html += '<span style="font-size:0.65rem;padding:1px 6px;border-radius:9999px;background:color-mix(in srgb, ' + sqiColor + ' 15%, transparent);color:' + sqiColor + ';font-family:monospace">' + sqi.toFixed(2) + '</span>';
    }
    html += '</div>';
    html += '<div style="font-weight:600;margin-bottom:0.25rem">' + highlightTerms(entry.title || '', terms) + '</div>';
    if (entry.description) {
      html += '<div style="font-size:0.85rem;color:var(--color-text-secondary, #aaa);display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden">' + highlightTerms(entry.description, terms) + '</div>';
    }
    if (concepts.length) {
      html += '<div style="display:flex;gap:0.25rem;flex-wrap:wrap;margin-top:0.35rem">';
      for (const c of concepts.slice(0, 5)) {
        html += '<span style="font-size:0.65rem;padding:1px 6px;border-radius:9999px;background:color-mix(in srgb, var(--color-accent, #818cf8) 12%, transparent);color:var(--color-accent, #818cf8);border:1px solid color-mix(in srgb, var(--color-accent, #818cf8) 25%, transparent)">' + escapeHtml(c) + '</span>';
      }
      if (concepts.length > 5) html += '<span style="font-size:0.65rem;color:var(--color-text-muted, #888)">+' + (concepts.length - 5) + '</span>';
      html += '</div>';
    }
    if (entry.technologies && entry.technologies.length) {
      html += '<div style="display:flex;gap:0.25rem;flex-wrap:wrap;margin-top:0.3rem">';
      for (const tech of entry.technologies.slice(0, 4)) {
        html += '<span style="font-size:0.65rem;padding:1px 6px;border-radius:4px;background:color-mix(in srgb, #22c55e 12%, transparent);color:#22c55e;border:1px solid color-mix(in srgb, #22c55e 25%, transparent)">&#9881; ' + escapeHtml(tech) + '</span>';
      }
      if (entry.technologies.length > 4) html += '<span style="font-size:0.65rem;color:var(--color-text-muted, #888)">+' + (entry.technologies.length - 4) + '</span>';
      html += '</div>';
    }
    if (entry.use_cases && entry.use_cases.length) {
      html += '<div style="display:flex;gap:0.25rem;flex-wrap:wrap;margin-top:0.25rem">';
      for (const uc of entry.use_cases.slice(0, 3)) {
        html += '<span style="font-size:0.6rem;padding:1px 5px;border-radius:9999px;background:color-mix(in srgb, var(--color-accent, #818cf8) 10%, transparent);color:var(--color-text-muted, #bbb)">' + escapeHtml(uc.replace(/-/g, ' ')) + '</span>';
      }
      if (entry.use_cases.length > 3) html += '<span style="font-size:0.6rem;color:var(--color-text-muted, #888)">+' + (entry.use_cases.length - 3) + '</span>';
      html += '</div>';
    }
    if (entry.tags && entry.tags.length) {
      html += '<div style="display:flex;gap:0.25rem;flex-wrap:wrap;margin-top:0.35rem">';
      for (const tag of entry.tags.slice(0, 4)) {
        html += '<kbd style="font-size:0.65rem">' + escapeHtml(tag) + '</kbd>';
      }
      html += '</div>';
    }
    html += '</a>';
    return html;
  }

  function renderPage() {
    const container = document.getElementById('search-results');
    if (!container) return;
    const batch = allScored.slice(0, displayedCount);
    container.innerHTML = batch.map((x, i) => renderResult(x.entry, currentTerms, i)).join('');
    const existing = document.getElementById('search-show-more');
    if (existing) existing.remove();
    if (displayedCount < allScored.length) {
      const btn = document.createElement('button');
      btn.id = 'search-show-more';
      btn.textContent = 'Show more (' + (allScored.length - displayedCount) + ' remaining)';
      btn.style.cssText = 'display:block;width:100%;padding:0.75rem;margin-top:0.5rem;background:var(--color-bg, #1a1a2e);border:1px solid var(--color-border, #333);border-radius:8px;color:var(--color-accent, #818cf8);cursor:pointer;font-size:0.85rem';
      btn.addEventListener('click', function() {
        displayedCount += PAGE_SIZE;
        renderPage();
      });
      container.appendChild(btn);
    }
  }

  function runSearch(query, tagFilter) {
    const container = document.getElementById('search-results');
    const statsEl = document.getElementById('search-stats');
    if (!container) return;

    const filtersActive = (function() {
      const f = readFilters();
      return f.pillar.length || f.type.length || f.difficulty.length || f.bloom.length || f.technology.length;
    })();

    if (!query.trim() && !tagFilter && !filtersActive) {
      container.innerHTML = '<p style="color:var(--color-text-muted, #888);text-align:center;margin-top:2rem">Type to search across all content, or pick a filter to browse...</p>';
      if (statsEl) statsEl.textContent = '';
      return;
    }

    const terms = query.trim() ? tokenize(query) : [];

    container.setAttribute('aria-busy', 'true');
    container.innerHTML = '<div class="search-loading" role="status"><span class="search-spinner" aria-hidden="true"></span> Loading search index...</div>';

    fetchIndex().then(index => {
      populateTechFilters(index);
      updateFacetCounts(index);
      // Restore technology filter checkboxes from URL after populating
      var techParams = new URLSearchParams(window.location.search).get('f_technology');
      if (techParams) {
        var techVals = techParams.split(',');
        document.querySelectorAll('#tech-filter-list .filter-checkbox').forEach(function(cb) {
          if (techVals.indexOf(cb.value) !== -1) cb.checked = true;
        });
      }
      const filters = readFilters();
      allScored = index
        .filter(function(e) {
          if (!matchesFilters(e, filters)) return false;
          if (tagFilter) {
            var concepts = e.ontology_concepts || [];
            var tags = e.tags || [];
            var matchesTag = concepts.some(function(c) { return c.toLowerCase() === tagFilter.toLowerCase(); })
              || tags.some(function(t) { return t.toLowerCase() === tagFilter.toLowerCase(); });
            if (!matchesTag) return false;
          }
          return true;
        })
        .map(function(e) {
          return { entry: e, score: terms.length ? scoreEntry(e, terms) : 1 };
        })
        .filter(function(x) { return x.score > 0; })
        .sort(function(a, b) {
          if (terms.length) return b.score - a.score;
          const sa = a.entry.avg_sqi || 0;
          const sb = b.entry.avg_sqi || 0;
          if (sb !== sa) return sb - sa;
          return String(b.entry.date_str || '').localeCompare(String(a.entry.date_str || ''));
        });
      currentTerms = terms;
      displayedCount = PAGE_SIZE;
      selectedIndex = -1;

      if (statsEl) {
        statsEl.textContent = allScored.length
          ? allScored.length + ' result' + (allScored.length !== 1 ? 's' : '')
          : 'No results';
      }

      if (query.trim()) {
        saveQuery(query);
        firePlausible('search', { query: query, results: allScored.length, terms: terms.length });
      }

      if (!allScored.length) {
        var suggestion = null;
        if (query.trim()) suggestion = didYouMean(query, getVocabulary(index), 2);
        var msg = tagFilter ? 'No results tagged "' + escapeHtml(tagFilter) + '"' : 'No results for "' + escapeHtml(query) + '"';
        var html = '<div style="text-align:center;margin-top:2rem"><p style="color:var(--color-text-muted, #888)">' + msg + '</p>';
        if (suggestion) {
          html += '<p style="font-size:0.9rem;margin-top:0.5rem;color:var(--color-text, #e8e6e3)">Did you mean: <a href="#" data-didyoumean="' + escapeHtml(suggestion) + '" style="color:var(--color-accent, #818cf8);font-weight:600;text-decoration:underline">' + escapeHtml(suggestion) + '</a>?</p>';
        }
        html += '<p style="font-size:0.8rem;color:var(--color-text-muted, #888);margin-top:0.5rem">Try different keywords or browse by pillar:</p><div style="display:flex;gap:0.5rem;justify-content:center;margin-top:0.75rem"><a href="/compliance/" class="inline-block px-3 py-1.5 text-xs font-semibold rounded-lg" style="background:var(--color-surface,#f0f0f0);color:var(--color-text,#333)">Compliance</a><a href="/markets/" class="inline-block px-3 py-1.5 text-xs font-semibold rounded-lg" style="background:var(--color-surface,#f0f0f0);color:var(--color-text,#333)">Markets</a><a href="/data/" class="inline-block px-3 py-1.5 text-xs font-semibold rounded-lg" style="background:var(--color-surface,#f0f0f0);color:var(--color-text,#333)">Data</a></div></div>';
        container.innerHTML = html;
        return;
      }

      renderPage();
      container.setAttribute('aria-busy', 'false');
    }).catch(function(err) {
      container.setAttribute('aria-busy', 'false');
      var retryBtn = '<button id="search-retry" type="button" style="margin-top:0.75rem;padding:0.5rem 1rem;background:var(--color-surface,#f0f0f0);border:1px solid var(--color-border,#333);border-radius:8px;color:var(--color-text,#333);cursor:pointer;font-size:0.85rem;font-weight:600">Retry</button>';
      container.innerHTML = '<div style="text-align:center;margin-top:2rem"><p style="color:#ef4444">Failed to load search index</p>' + retryBtn + '</div>';
      var retry = document.getElementById('search-retry');
      if (retry) retry.addEventListener('click', function() {
        searchIndex = null;
        runSearch(query, tagFilter);
      });
    });
  }

  function doSearch() {
    const input = document.getElementById('search-input');
    if (!input) return;
    const params = new URLSearchParams(window.location.search);
    runSearch(input.value, params.get('f_tags') || '');
  }

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
      didYouMean: didYouMean,
      bestCorrection: bestCorrection,
      buildVocabulary: buildVocabulary,
    };
  }

  if (typeof document !== 'undefined') {
    document.addEventListener('DOMContentLoaded', function() {
    const input = document.getElementById('search-input');
    if (!input) return;

    // Restore filters from URL
    const params = new URLSearchParams(window.location.search);
    const q = params.get('q') || '';
    const tagFilter = params.get('f_tags') || '';
    document.querySelectorAll('.filter-checkbox').forEach(cb => {
      const group = cb.getAttribute('data-group');
      const urlVal = params.get('f_' + group);
      if (urlVal && urlVal.split(',').includes(cb.value)) cb.checked = true;
    });

    // Show active tag filter badge
    if (tagFilter) {
      var tagBar = document.getElementById('tag-filter-bar') || (function() {
        var el = document.createElement('div');
        el.id = 'tag-filter-bar';
        el.className = 'flex flex-wrap items-center gap-2 mb-4';
        var container = document.getElementById('search-results');
        if (container) container.parentNode.insertBefore(el, container);
        return el;
      })();
      tagBar.innerHTML = '<span class="text-xs font-semibold" style="color:var(--color-text-muted)">Tagged:</span>'
        + '<span class="inline-flex items-center gap-1 text-xs px-2 py-1 rounded-full" style="background:color-mix(in srgb, var(--color-accent) 12%, transparent);color:var(--color-accent)">'
        + tagFilter
        + '<button id="clear-tag-filter" class="ml-1" style="background:none;border:none;cursor:pointer;color:inherit;padding:0;line-height:1" aria-label="Clear tag filter">&times;</button></span>';
      document.getElementById('clear-tag-filter').addEventListener('click', function() {
        var url = new URL(window.location);
        url.searchParams.delete('f_tags');
        history.replaceState(null, '', url);
        tagBar.innerHTML = '';
        runSearch(input.value);
      });
    }

    if (q || tagFilter) {
      input.value = q;
      runSearch(q, tagFilter);
    }

    // Filter checkbox change handler (delegated: technology checkboxes are
    // injected dynamically by populateTechFilters after every search)
    document.addEventListener('change', function(e) {
      const cb = e.target && e.target.classList && e.target.classList.contains('filter-checkbox') ? e.target : null;
      if (!cb) return;
      const filters = readFilters();
      syncFiltersToUrl(filters);
      // Invalidate search index cache when pillar filters change
      if (cb.getAttribute('data-group') === 'pillar') {
        searchIndex = null;
      }
      doSearch();
    });

    // Reset filters
    const resetBtn = document.getElementById('reset-filters');
    if (resetBtn) {
      resetBtn.addEventListener('click', function() {
        document.querySelectorAll('.filter-checkbox:checked').forEach(cb => cb.checked = false);
        const filters = readFilters();
        syncFiltersToUrl(filters);
        searchIndex = null;
        doSearch();
      });
    }

    // Mobile filter toggle
    const filtersToggle = document.getElementById('search-filters-toggle');
    const filtersSidebar = document.getElementById('search-filters');
    if (filtersToggle && filtersSidebar) {
      if (document.querySelector('.filter-checkbox:checked') !== null) {
        filtersSidebar.classList.add('search-sidebar-open');
        filtersToggle.setAttribute('aria-expanded', 'true');
        filtersToggle.textContent = 'Hide filters';
      }
      filtersToggle.addEventListener('click', function() {
        const open = filtersSidebar.classList.toggle('search-sidebar-open');
        filtersToggle.setAttribute('aria-expanded', open ? 'true' : 'false');
        filtersToggle.textContent = open ? 'Hide filters' : 'Filters';
      });
    }

    let debounce = null;
    input.addEventListener('input', function() {
      clearTimeout(debounce);
      const val = input.value;
      fetchConcepts().then(() => renderSuggestions(val));
      debounce = setTimeout(() => {
        const url = new URL(window.location);
        if (val) url.searchParams.set('q', val);
        else url.searchParams.delete('q');
        history.replaceState(null, '', url);
        runSearch(val);
      }, 200);
    });

    input.addEventListener('focus', function() { fetchConcepts().then(() => renderSuggestions(this.value)); });
    input.addEventListener('blur', function() {
      setTimeout(function() {
        const el = document.getElementById('search-suggestions');
        if (el) setSuggestionsOpen(el, false);
      }, 200);
    });

    // Click delegation for result clicks (Plausible tracking) + "Did you mean?" correction
    document.getElementById('search-results').addEventListener('click', function(e) {
      const dym = e.target.closest('[data-didyoumean]');
      if (dym) {
        e.preventDefault();
        const corrected = dym.getAttribute('data-didyoumean');
        input.value = corrected;
        setSuggestionsOpen(document.getElementById('search-suggestions'), false);
        const url = new URL(window.location);
        url.searchParams.set('q', corrected);
        history.replaceState(null, '', url);
        runSearch(corrected);
        return;
      }
      const result = e.target.closest('.search-result');
      if (result) {
        const slug = result.getAttribute('data-slug');
        const query = input.value;
        firePlausible('Search Result Click', { query: query, slug: slug });
      }
    });

    // Suggestion click handler
    document.getElementById('search-suggestions').addEventListener('click', function(e) {
      const item = e.target.closest('.suggestion-item');
      if (item) {
        const suggestion = item.getAttribute('data-suggestion');
        if (suggestion) {
          input.value = suggestion;
          setSuggestionsOpen(this, false);
          suggestionIndex = -1;
          const url = new URL(window.location);
          url.searchParams.set('q', suggestion);
          history.replaceState(null, '', url);
          runSearch(suggestion);
        }
      }
    });

    // Keyboard navigation
    document.addEventListener('keydown', function(e) {
      if (e.key === '/' && document.activeElement !== input) {
        e.preventDefault();
        input.focus();
      }
      if (e.key === 'Escape' && document.activeElement === input) {
        input.value = '';
        input.blur();
        selectedIndex = -1;
        suggestionIndex = -1;
        setSuggestionsOpen(document.getElementById('search-suggestions'), false);
        runSearch('');
        return;
      }
      const suggestionsEl = document.getElementById('search-suggestions');
      const suggestionsOpen = suggestionsEl && suggestionsEl.style.display === 'block';
      const sugItems = suggestionsOpen ? suggestionsEl.querySelectorAll('.suggestion-item') : [];
      if (suggestionsOpen && (e.key === 'ArrowDown' || e.key === 'ArrowUp')) {
        if (!sugItems.length) return;
        e.preventDefault();
        const dir = e.key === 'ArrowDown' ? 1 : -1;
        suggestionIndex = (suggestionIndex + dir + sugItems.length) % sugItems.length;
        sugItems.forEach(function(el, i) { el.classList.toggle('suggestion-active', i === suggestionIndex); });
        sugItems[suggestionIndex].scrollIntoView({ block: 'nearest' });
        return;
      }
      if (suggestionsOpen && e.key === 'Enter') {
        e.preventDefault();
        const target = sugItems.length ? (sugItems[suggestionIndex] || sugItems[0]) : null;
        if (target) target.click();
        return;
      }
      if (suggestionsOpen && e.key === 'Escape') {
        setSuggestionsOpen(suggestionsEl, false);
        suggestionIndex = -1;
        e.preventDefault();
        return;
      }
      if (e.key === 'Escape' && selectedIndex >= 0) {
        selectedIndex = -1;
        renderPage();
        e.preventDefault();
        return;
      }
      if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
        if (!allScored.length) return;
        e.preventDefault();
        const dir = e.key === 'ArrowDown' ? 1 : -1;
        selectedIndex = Math.max(-1, Math.min(displayedCount - 1, selectedIndex + dir));
        renderPage();
        const selectedEl = document.querySelector('.search-result[data-idx="' + selectedIndex + '"]');
        if (selectedEl) selectedEl.scrollIntoView({ block: 'nearest' });
      }
      if (e.key === 'Enter' && allScored.length) {
        const idx = (selectedIndex >= 0 && selectedIndex < allScored.length) ? selectedIndex : 0;
        e.preventDefault();
        window.location.href = slugToUrl(allScored[idx].entry.slug);
      }
    });
  });
  }
})();


/* progressive_disclosure.js */
(function () {
  'use strict';

  /** Pure: parse section headings from an HTML string using regex. */
  function parseSections(html) {
    if (!html) return [];
    var sectionRegex = /<section[^>]*class="[^"]*prose-section[^"]*"[^>]*>[\s\S]*?<\/section>/gi;
    var headingRegex = /<h[23][^>]*>([\s\S]*?)<\/h[23]>/i;
    var sections = [];
    var match;
    while ((match = sectionRegex.exec(html)) !== null) {
      var headingMatch = headingRegex.exec(match[0]);
      var title = headingMatch
        ? headingMatch[1].replace(/<[^>]+>/g, '').trim()
        : 'Section ' + (sections.length + 1);
      sections.push({
        index: sections.length,
        title: title,
        isCollapsed: sections.length !== 0,
      });
    }
    return sections;
  }

  /** Pure: toggle a section's collapsed state */
  function toggleSection(sections, index) {
    return sections.map(function (s, i) {
      if (i === index) {
        return { index: s.index, title: s.title, isCollapsed: !s.isCollapsed };
      }
      return { index: s.index, title: s.title, isCollapsed: s.isCollapsed };
    });
  }

  /** Save per-page state to sessionStorage */
  function saveState(pageSlug, sections) {
    try {
      var key = 'acacia_disclosure_' + pageSlug;
      sessionStorage.setItem(key, JSON.stringify(sections));
    } catch (_) { /* quota exceeded — ignore */ }
  }

  /** Load per-page state from sessionStorage */
  function loadState(pageSlug) {
    try {
      var key = 'acacia_disclosure_' + pageSlug;
      var raw = sessionStorage.getItem(key);
      return raw ? JSON.parse(raw) : null;
    } catch (_) { return null; }
  }

  /** Attach event listeners and initialize disclosure on the page */
  function initDisclosure() {
    var sectionEls = document.querySelectorAll('section.prose-section');
    if (!sectionEls.length) return;

    var pageSlug = window.location.pathname.replace(/\//g, '_') || 'index';
    var saved = loadState(pageSlug);
    var initial = [];

    sectionEls.forEach(function (el, i) {
      var header = el.querySelector('h2, h3');
      if (!header) return;

      var collapsed = saved
        ? saved[i] ? saved[i].isCollapsed !== false : false
        : i !== 0;

      el.classList.toggle('is-collapsed', collapsed);

      var headerBar = document.createElement('div');
      headerBar.className = 'section-header' + (collapsed ? '' : ' is-expanded');
      headerBar.style.cssText = 'cursor:pointer;user-select:none;display:flex;align-items:center;gap:0.5rem;padding:0.5rem 0';

      header.parentNode.insertBefore(headerBar, header);
      headerBar.appendChild(header);

      initial.push({ index: i, title: header.textContent.trim(), isCollapsed: collapsed });

      headerBar.addEventListener('click', function () {
        var currentlyCollapsed = el.classList.contains('is-collapsed');
        el.classList.toggle('is-collapsed', !currentlyCollapsed);
        headerBar.classList.toggle('is-expanded', currentlyCollapsed);

        var currentSections = Array.from(sectionEls).map(function (se, idx) {
          return {
            index: idx,
            title: (se.querySelector('h2, h3') || {}).textContent || '',
            isCollapsed: se.classList.contains('is-collapsed'),
          };
        });
        saveState(pageSlug, currentSections);
      });
    });

    if (!saved) {
      saveState(pageSlug, initial);
    }
  }

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = { parseSections: parseSections, toggleSection: toggleSection };
  }

  if (typeof document !== 'undefined') {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', initDisclosure);
    } else {
      initDisclosure();
    }
  }
})();


/* review_badge.js */
(function() {
  'use strict';

  function badgeStyle() {
    return 'display:none;background:var(--color-accent,#818cf8);color:#fff;font-size:0.65rem;line-height:1;padding:2px 5px;border-radius:9999px;margin-left:4px;vertical-align:middle';
  }

  function countDue() {
    var mastery = {};
    try { mastery = JSON.parse(localStorage.getItem('acacia_concept_mastery') || '{}'); } catch (_) {}
    var sm2 = {};
    try { sm2 = JSON.parse(localStorage.getItem('acacia_sm2') || '{}'); } catch (_) {}

    var base = document.querySelector('script[src*="review_badge.js"]');
    var prefix = base ? base.src.replace(/js\/\w+\.js.*$/, '') : '';

    fetch(prefix + 'static/review_concepts.json')
      .then(function(r) { if (!r.ok) throw new Error(r.status); return r.json(); })
      .then(function(data) {
        var concepts = data.concepts || [];
        var now = Date.now();
        var due = 0;
        for (var i = 0; i < concepts.length; i++) {
          var c = concepts[i];
          var m = mastery[c.id] || {};
          var s = sm2[c.id] || {};
          var conceptDue = m.due || s.due || 0;
          var reps = (m.reps || 0) + (s.reps || 0);
          if (reps === 0 || (conceptDue > 0 && conceptDue <= now)) due++;
        }
        updateBadge(due);
      })
      .catch(function() {});
  }

  function updateBadge(count) {
    document.querySelectorAll('a[href="/review/"]').forEach(function(link) {
      var badge = link.querySelector('.review-badge');
      if (!badge) {
        badge = document.createElement('span');
        badge.className = 'review-badge';
        badge.style.cssText = badgeStyle();
        link.appendChild(badge);
      }
      if (count > 0) {
        badge.textContent = count > 99 ? '99+' : count;
        badge.style.display = 'inline-block';
      } else {
        badge.style.display = 'none';
      }
    });
  }

  document.addEventListener('DOMContentLoaded', function() {
    var link = document.querySelector('a[href="/review/"]');
    if (!link) return;
    var badge = document.createElement('span');
    badge.className = 'review-badge';
    badge.style.cssText = badgeStyle();
    link.appendChild(badge);
    countDue();
    window.addEventListener('storage', countDue);
    document.addEventListener('review-badge-update', function() { countDue(); });
  });
})();
