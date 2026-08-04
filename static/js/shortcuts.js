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
