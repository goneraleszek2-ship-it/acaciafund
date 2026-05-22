// Learning hub: local progress, simple calibration, quiz renderer
(function(){
  var STORAGE_KEY = 'acacia_progress_v1';

  function loadProgress(){
    try{ return JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}'); }catch(e){return {};}
  }
  function saveProgress(p){ localStorage.setItem(STORAGE_KEY, JSON.stringify(p)); }

  function markDone(url){ var p = loadProgress(); p[url] = {done:true, ts:Date.now()}; saveProgress(p); renderProgress(); }

  function renderProgress(){
    var p = loadProgress();
    document.querySelectorAll('[data-track-lesson]').forEach(function(btn){
      var url = btn.getAttribute('data-track-lesson');
      if(p[url] && p[url].done) { btn.textContent = 'Completed'; btn.disabled=true; }
    });
  }

  function renderQuizzes(){
    document.querySelectorAll('.quiz').forEach(function(el){
      if(el.dataset.rendered) return; el.dataset.rendered = '1';
      var data = JSON.parse(el.getAttribute('data-quiz'));
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
        alert('Score: '+score+' / '+total);
        // Mark lesson done if score >= 1 (simple rule)
        var p = loadProgress(); var url = window.location.pathname; p[url]=p[url]||{}; p[url].score=score; p[url].ts=Date.now(); if(score>=1) p[url].done=true; saveProgress(p); renderProgress();
      });
      wrapper.appendChild(submit);
      el.appendChild(wrapper);
    });
  }

  document.addEventListener('DOMContentLoaded', function(){
    document.querySelectorAll('[data-track-lesson]').forEach(function(btn){ btn.addEventListener('click', function(){ markDone(btn.getAttribute('data-track-lesson')) }); });
    renderProgress(); renderQuizzes();
  });
})();
