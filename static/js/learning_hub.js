// Learning hub: modular client for quizzes, local progress and optional server sync
(function (global) {
  var NS = 'AcaciaLearning';
  if (global[NS]) return; // idempotent
  var module = {};

  var STORAGE_KEY = 'acacia_progress_v1';
  // API endpoint can be configured via <body data-api-endpoint="https://..."> or falls back to origin + :8000
  function detectApiEndpoint() {
    try {
      var b = document && document.body;
      if (b && b.dataset && b.dataset.apiEndpoint) return b.dataset.apiEndpoint.replace(/\/+$/,'');
    } catch (e) {}
    var origin = window.location.origin.replace(/\/+$/,'');
    // only append :8000 when it appears to be a local dev host
    if (/localhost|127\.0\.0\.1/.test(origin)) return origin.replace(/:\d+$/,'') + ':8000';
    return '';
  }

  var API_ENDPOINT = detectApiEndpoint();

  function loadProgress(){
    try{ return JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}'); }catch(e){return {};}
  }
  function saveProgress(p){ localStorage.setItem(STORAGE_KEY, JSON.stringify(p)); }

  function lessonKeyFor(btnOrUrl){
    if (!btnOrUrl) return window.location.pathname;
    if (typeof btnOrUrl === 'string') return btnOrUrl;
    var v = btnOrUrl.getAttribute && (btnOrUrl.getAttribute('data-track-lesson') || btnOrUrl.getAttribute('data-lesson-id'));
    return v || window.location.pathname;
  }

  function markDone(target){
    var key = lessonKeyFor(target);
    var p = loadProgress(); p[key] = p[key] || {};
    p[key].done = true; p[key].ts = Date.now(); saveProgress(p); renderProgress(); trySync(key);
  }

  // Exponential backoff simple sync
  function trySync(key, attempt){
    attempt = (attempt || 0) + 1;
    if (!API_ENDPOINT) return; // no server configured
    var p = loadProgress(); var entry = p[key]; if(!entry) return;
    var payload = {url: key, done: !!entry.done, score: entry.score||0, ts: entry.ts||Date.now()};
    fetch(API_ENDPOINT + '/progress', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)})
      .then(function(res){ if(!res.ok) throw new Error('sync failed: '+res.status); })
      .catch(function(err){
        // Retry a few times with backoff
        if (attempt < 4) {
          var delay = Math.pow(2, attempt) * 250;
          setTimeout(function(){ trySync(key, attempt); }, delay);
        }
      });
  }

  function renderProgress(){
    var p = loadProgress();
    document.querySelectorAll('[data-track-lesson]').forEach(function(btn){
      var url = lessonKeyFor(btn);
      if(p[url] && p[url].done) { btn.textContent = 'Completed'; btn.disabled=true; btn.classList.add('lesson-completed'); }
    });
  }

  function renderQuizzes(){
    document.querySelectorAll('.quiz').forEach(function(el){
      if(el.dataset.rendered) return; el.dataset.rendered = '1';
      var data;
      try { data = JSON.parse(el.getAttribute('data-quiz')); } catch(e){ return; }
      var wrapper = document.createElement('div');
      data.questions.forEach(function(q,i){
        var qDiv = document.createElement('div'); qDiv.style.marginBottom='12px';
        var qh = document.createElement('div'); qh.textContent = (i+1)+'. '+q.q; qh.style.fontWeight='600'; qDiv.appendChild(qh);
        q.options.forEach(function(opt,j){
          var lbl = document.createElement('label'); lbl.style.display='block';
          var inp = document.createElement('input'); inp.type='radio'; inp.name='q_'+i; inp.value=j;
          lbl.appendChild(inp); lbl.appendChild(document.createTextNode(' '+opt)); qDiv.appendChild(lbl);
        });
        wrapper.appendChild(qDiv);
      });
      var submit = document.createElement('button'); submit.textContent='Submit'; submit.className='btn btn-primary';
      submit.addEventListener('click', function(){
        var score=0, total=data.questions.length;
        data.questions.forEach(function(q,i){
          var chosen = el.querySelector('input[name=q_'+i+']:checked');
          if(chosen && parseInt(chosen.value)===q.a) score++;
        });
        // minimal UI: replace alert with inline result
        var res = el.querySelector('.quiz-result'); if(!res){ res = document.createElement('div'); res.className='quiz-result mt-2'; el.appendChild(res); }
        res.textContent = 'Score: '+score+' / '+total;
        // Mark lesson done if score >= 1 (simple rule)
        var url = lessonKeyFor(window.location.pathname);
        var p = loadProgress(); p[url]=p[url]||{}; p[url].score=score; p[url].ts=Date.now(); if(score>=1) p[url].done=true; saveProgress(p); renderProgress(); trySync(url);
      });
      wrapper.appendChild(submit);
      el.appendChild(wrapper);
    });
  }

  document.addEventListener('DOMContentLoaded', function(){
    document.querySelectorAll('[data-track-lesson]').forEach(function(btn){ btn.addEventListener('click', function(){ markDone(btn); }); });
    renderProgress(); renderQuizzes();
  });

  module.markDone = markDone;
  module.renderProgress = renderProgress;
  global[NS] = module;
})(window);
