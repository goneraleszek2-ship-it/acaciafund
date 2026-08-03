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
