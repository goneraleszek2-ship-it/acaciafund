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
