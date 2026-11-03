(function () {
  var btns = document.querySelectorAll('.cite-copy-btn');
  btns.forEach(function (btn) {
    btn.addEventListener('click', function () {
      var type = btn.getAttribute('data-cite-type');
      var tpl = document.querySelector('.cite-template[data-cite-type="' + type + '"]');
      if (!tpl) return;
      var text = tpl.innerHTML.trim();
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(function () {
          var prev = btn.textContent;
          btn.textContent = 'Copied';
          setTimeout(function () { btn.textContent = prev; }, 1500);
        });
      }
    });
  });
})();
