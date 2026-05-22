// Minimal interactive Bayes demo
// Finds SVG paths with ids priorPath, likePath, postPath and two sliders
(function(){
  function qPath(x0,y0, cx,cy, x1,y1){ return `M ${x0},${y0} Q ${cx},${cy} ${x1},${y1}`; }

  function updateBayes(){
    var prior = parseFloat(document.getElementById('priorVal').value);
    var like = parseFloat(document.getElementById('likeVal').value);
    // map 0..1 to control peak positions
    var w = 300, h=80, ybase=70;
    var priorX = 40; var likeX = 160; var postX = 100;
    var priorH = Math.max(6, 70 - prior*60);
    var likeH = Math.max(6, 70 - like*60);
    // Compute simple bezier control points
    var priorD = qPath(0,ybase, priorX, priorH, 80,ybase);
    var likeD  = qPath(40,ybase, likeX, likeH, 200,ybase);
    // Posterior as weighted average of peaks (simple visualization)
    var postPeak = (prior*40 + like*160) / Math.max(1e-6, (prior+like));
    var postH = Math.max(6, 70 - ((prior+like)/2)*60);
    var postD = qPath(20,ybase, postPeak, postH, 220,ybase);

    var p = document.getElementById('priorPath'); if(p) p.setAttribute('d', priorD);
    var l = document.getElementById('likePath'); if(l) l.setAttribute('d', likeD);
    var o = document.getElementById('postPath'); if(o) o.setAttribute('d', postD);

    // Update textual probabilities
    var posterior = (prior*like) / Math.max(1e-6, (prior*like + (1-prior)*(1-like)));
    document.getElementById('posteriorVal').textContent = posterior.toFixed(3);
    document.getElementById('priorLabel').textContent = prior.toFixed(2);
    document.getElementById('likeLabel').textContent = like.toFixed(2);
  }

  document.addEventListener('DOMContentLoaded', function(){
    var s1 = document.getElementById('priorVal');
    var s2 = document.getElementById('likeVal');
    if(s1 && s2){
      s1.addEventListener('input', updateBayes);
      s2.addEventListener('input', updateBayes);
      updateBayes();
    }
  });
})();
