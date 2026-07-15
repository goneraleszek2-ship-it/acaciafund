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
