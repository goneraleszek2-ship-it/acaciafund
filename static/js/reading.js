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

    function setOpen(open) {
      panel.classList.toggle('open', open);
      panel.setAttribute('aria-hidden', open ? 'false' : 'true');
      toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
      if (open && close) close.focus();
    }

    toggle.addEventListener('click', function () {
      setOpen(!panel.classList.contains('open'));
    });
    if (close) close.addEventListener('click', function () { setOpen(false); });

    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && panel.classList.contains('open')) setOpen(false);
    });
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
