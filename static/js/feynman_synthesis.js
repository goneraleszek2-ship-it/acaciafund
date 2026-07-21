/* Feynman Synthesis — Save & Submit for Learn Module pages */

(function () {
  'use strict';

  const SYNTHESIS_KEY_PREFIX = 'acacia_feynman_synthesis_';
  const HISTORY_KEY = 'acacia_feynman_submissions';

  function getPageSlug() {
    const path = window.location.pathname.replace(/\/$/, '');
    const parts = path.split('/');
    return parts.filter(Boolean).join('_') || 'home';
  }

  function getSynthesisKey() {
    return SYNTHESIS_KEY_PREFIX + getPageSlug();
  }

  function loadSynthesis() {
    try {
      return JSON.parse(localStorage.getItem(getSynthesisKey()) || '{}');
    } catch (_) {
      return {};
    }
  }

  function saveSynthesis(data) {
    try {
      localStorage.setItem(getSynthesisKey(), JSON.stringify(data));
    } catch (_) {}
  }

  function restoreSynthesis() {
    const data = loadSynthesis();
    const onepager = document.getElementById('feynman-onepager');
    const gaps = document.getElementById('feynman-gaps');
    if (onepager && data.onepager) onepager.value = data.onepager;
    if (gaps && data.gaps) gaps.value = data.gaps;
  }

  function saveCurrentSynthesis() {
    const onepager = document.getElementById('feynman-onepager');
    const gaps = document.getElementById('feynman-gaps');
    saveSynthesis({
      onepager: onepager ? onepager.value : '',
      gaps: gaps ? gaps.value : '',
      updatedAt: new Date().toISOString(),
    });
  }

  function showToast(message, type) {
    type = type || 'success';
    const existing = document.getElementById('feynman-toast');
    if (existing) existing.remove();

    const toast = document.createElement('div');
    toast.id = 'feynman-toast';
    toast.textContent = message;
    toast.style.cssText =
      'position:fixed;bottom:1.5rem;right:1.5rem;z-index:9999;padding:0.75rem 1.25rem;border-radius:8px;font-size:0.8rem;font-weight:600;' +
      (type === 'success'
        ? 'background:#22c55e;color:#fff;'
        : 'background:var(--color-surface,#1a1a2e);color:var(--color-text,#e8e6e3);border:1px solid var(--color-border,#333);');
    document.body.appendChild(toast);
    setTimeout(function () { toast.remove(); }, 3000);
  }

  document.addEventListener('DOMContentLoaded', function () {
    const saveBtn = document.getElementById('save-feynman-synthesis');
    const submitBtn = document.getElementById('submit-feynman-synthesis');

    restoreSynthesis();

    const autoSave = function () {
      saveCurrentSynthesis();
    };
    const debounce = function (fn, delay) {
      let timer;
      return function () {
        clearTimeout(timer);
        timer = setTimeout(fn, delay);
      };
    };

    const onepager = document.getElementById('feynman-onepager');
    const gaps = document.getElementById('feynman-gaps');
    if (onepager) onepager.addEventListener('input', debounce(autoSave, 500));
    if (gaps) gaps.addEventListener('input', debounce(autoSave, 500));

    if (saveBtn) {
      saveBtn.addEventListener('click', function () {
        saveCurrentSynthesis();
        showToast('Synthesis saved locally', 'success');
      });
    }

    if (submitBtn) {
      submitBtn.addEventListener('click', function () {
        saveCurrentSynthesis();
        const data = loadSynthesis();
        const history = JSON.parse(localStorage.getItem(HISTORY_KEY) || '[]');
        history.push({
          page: getPageSlug(),
          onepager: data.onepager || '',
          gaps: data.gaps || '',
          submittedAt: new Date().toISOString(),
        });
        try {
          localStorage.setItem(HISTORY_KEY, JSON.stringify(history));
        } catch (_) {}
        showToast('Submitted for review — stored locally', 'success');
      });
    }
  });
})();
