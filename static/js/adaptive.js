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
