
/* concept_tabs.js */

/* concept_tabs.js */

/* concept_tabs.js */

/* concept_tabs.js */

/* concept_tabs.js */

/* concept_tabs.js */
(function () {
  'use strict';

  /* ── Tab molecule (spec §3.3 Organisms / §4.5 Concept Hub) ── */

  function tabNames(panels) {
    return (panels || []).map(function (p) {
      return p.getAttribute('data-tabpanel');
    }).filter(Boolean);
  }

  function nextTab(current, direction, count) {
    if (count <= 0) return -1;
    var next = (current + direction) % count;
    if (next < 0) next += count;
    return next;
  }

  function showTab(root, name) {
    var tabs = root.querySelectorAll('[data-tab]');
    var panels = root.querySelectorAll('[data-tabpanel]');
    var found = false;
    for (var i = 0; i < tabs.length; i++) {
      var active = tabs[i].getAttribute('data-tab') === name;
      if (active) found = true;
      tabs[i].classList.toggle('is-active', active);
      tabs[i].setAttribute('aria-selected', active ? 'true' : 'false');
      tabs[i].setAttribute('tabindex', active ? '0' : '-1');
    }
    for (var j = 0; j < panels.length; j++) {
      panels[j].classList.toggle('is-active', panels[j].getAttribute('data-tabpanel') === name);
    }
    if (!found) return;
    var evt = new CustomEvent('acacia:tabchange', { detail: { tab: name } });
    root.dispatchEvent(evt);
  }

  function initRoot(root) {
    var tabs = Array.prototype.slice.call(root.querySelectorAll('[data-tab]'));
    var names = tabNames(root.querySelectorAll('[data-tabpanel]'));
    if (!names.length) return;
    showTab(root, names[0]);

    tabs.forEach(function (tab) {
      tab.addEventListener('click', function () {
        showTab(root, tab.getAttribute('data-tab'));
      });
      tab.addEventListener('keydown', function (e) {
        var cur = names.indexOf(tab.getAttribute('data-tab'));
        var next = null;
        if (e.key === 'ArrowRight' || e.key === 'ArrowDown') next = names[nextTab(cur, 1, names.length)];
        else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') next = names[nextTab(cur, -1, names.length)];
        else if (e.key === 'Home') next = names[0];
        else if (e.key === 'End') next = names[names.length - 1];
        if (next !== null) {
          e.preventDefault();
          showTab(root, next);
          var el = root.querySelector('[data-tab="' + next + '"]');
          if (el) el.focus();
        }
      });
    });
  }

  /* ── Content-type filter chips (Articles tab) ── */

  function filterItems(items, type) {
    if (!type || type === 'all') return items.slice();
    return items.filter(function (it) {
      return String(it.getAttribute('data-content-type')) === type;
    });
  }

  function initFilters(root) {
    var bar = root.querySelector('[data-filter-bar]');
    if (!bar) return;
    var cards = Array.prototype.slice.call(root.querySelectorAll('[data-filter-item]'));
    bar.querySelectorAll('[data-filter]').forEach(function (chip) {
      chip.addEventListener('click', function () {
        bar.querySelectorAll('[data-filter]').forEach(function (c) { c.classList.remove('is-active'); });
        chip.classList.add('is-active');
        var type = chip.getAttribute('data-filter');
        cards.forEach(function (card) {
          var show = filterItems([card], type).length > 0;
          card.style.display = show ? '' : 'none';
        });
      });
    });
  }

  function init() {
    document.querySelectorAll('[data-tabs]').forEach(function (root) {
      initRoot(root);
      initFilters(root);
    });
  }

  if (typeof document !== 'undefined') {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', init);
    } else {
      init();
    }
  }

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
      tabNames: tabNames,
      nextTab: nextTab,
      showTab: showTab,
      filterItems: filterItems,
    };
  }
})();
