/**
 * AcaciaFund Animation Module
 * Handles scroll animations, particle effects, and interactive elements
 */

(function() {
  'use strict';

  // ── DOM Ready ───────────────────────────────────────────────
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  function init() {
    initScrollAnimations();
    initCounterAnimation();
    initHeroTypewriter();
    initSmoothScroll();
    initIntersectionObserver();
  }

  // ── Scroll Animations ───────────────────────────────────────
  function initScrollAnimations() {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            entry.target.classList.add('visible');
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.1, rootMargin: '0px 0px -50px 0px' }
    );

    // Observe cards and sections
    document.querySelectorAll('.research-card, .pillar-card, .section-header').forEach(el => {
      el.classList.add('fade-in');
      observer.observe(el);
    });
  }

  // ── Counter Animation ───────────────────────────────────────
  function initCounterAnimation() {
    const counters = document.querySelectorAll('.hero-stat-value');
    const speed = 200;

    const animateCounter = (counter) => {
      const target = parseInt(counter.textContent);
      const increment = target / speed;

      const updateCount = () => {
        const count = Math.ceil(counter.dataset.count || 0);
        if (count < target) {
          counter.dataset.count = count + increment;
          counter.textContent = Math.ceil(counter.dataset.count);
          setTimeout(updateCount, 10);
        } else {
          counter.textContent = target;
        }
      };

      updateCount();
    };

    const counterObserver = new IntersectionObserver(
      (entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting && entry.target.classList.contains('hero-stat')) {
            const valueEl = entry.target.querySelector('.hero-stat-value');
            if (valueEl && !valueEl.dataset.count) {
              valueEl.dataset.count = valueEl.textContent;
              animateCounter(valueEl);
            }
          }
        });
      },
      { threshold: 0.5 }
    );

    counters.forEach(counter => counterObserver.observe(counter));
  }

  // ── Hero Typewriter Effect ──────────────────────────────────
  function initHeroTypewriter() {
    const title = document.querySelector('.hero-subtitle');
    if (!title) return;

    const text = title.textContent;
    title.textContent = '';
    title.innerHTML = '<span class="typing-text"></span><span class="cursor">|</span>';

    let i = 0;
    const typeWriter = () => {
      if (i < text.length) {
        const char = text.charAt(i);
        title.querySelector('.typing-text').textContent += char;
        i++;
        setTimeout(typeWriter, 50);
      } else {
        // Remove cursor after typing
        setTimeout(() => {
          title.querySelector('.cursor').style.display = 'none';
        }, 2000);
      }
    };

    setTimeout(typeWriter, 1000);
  }

  // ── Smooth Scroll ───────────────────────────────────────────
  function initSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
      anchor.addEventListener('click', function(e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
          target.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
      });
    });
  }

  // ── Intersection Observer for Fade-in ───────────────────────
  function initIntersectionObserver() {
    const fadeElements = document.querySelectorAll('.fade-in');
    
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            entry.target.classList.add('visible');
          }
        });
      },
      { threshold: 0.1 }
    );

    fadeElements.forEach(el => observer.observe(el));
  }

  // ── Add visible class styles dynamically ────────────────────
  if (!document.getElementById('animation-styles')) {
    const style = document.createElement('style');
    style.id = 'animation-styles';
    style.textContent = `
      .fade-in {
        opacity: 0;
        transform: translateY(30px);
        transition: opacity 0.6s ease, transform 0.6s ease;
      }
      .fade-in.visible {
        opacity: 1;
        transform: translateY(0);
      }
      .typing-text {
        display: inline;
      }
      .cursor {
        display: inline-block;
        animation: blink 1s infinite;
      }
      @keyframes blink {
        0%, 49% { opacity: 1; }
        50%, 100% { opacity: 0; }
      }
    `;
    document.head.appendChild(style);
  }

})();
