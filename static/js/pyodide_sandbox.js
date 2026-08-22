
/* pyodide_sandbox.js */

/* pyodide_sandbox.js */

/* pyodide_sandbox.js */

/* pyodide_sandbox.js */

/* pyodide_sandbox.js */

/* pyodide_sandbox.js */
/* pyodide_sandbox.js */

/* pyodide_sandbox.js */

/* pyodide_sandbox.js */
(function () {
  'use strict';

  var PYODIDE_URL = 'https://cdn.jsdelivr.net/pyodide/v0.26.4/full/pyodide.js';
  var POLARS_WHEEL = 'https://cdn.jsdelivr.net/pyodide/v0.26.4/full/polars-1.4.1-cp311-cp311-emscripten_3_1_45_wasm32.whl';
  var _pyodidePromise = null;

  /* ── Pure helpers (unit-tested via tests/test_pyodide_sandbox.js) ── */

  function normalizePy(src) {
    return String(src || '').replace(/\r\n/g, '\n').trim();
  }

  function countWords(text) {
    var words = String(text || '').trim().split(/\s+/).filter(function (w) { return w.length > 0; });
    return words.length;
  }

  /* ── Pyodide loading ── */

  function loadPyodide() {
    if (_pyodidePromise) return _pyodidePromise;
    _pyodidePromise = new Promise(function (resolve, reject) {
      var s = document.createElement('script');
      s.src = PYODIDE_URL;
      s.onload = function () {
        if (typeof window.loadPyodide !== 'function') {
          reject(new Error('Pyodide loader unavailable.'));
          return;
        }
        window.loadPyodide({ indexURL: 'https://cdn.jsdelivr.net/pyodide/v0.26.4/full/' })
          .then(function (py) {
            return py.loadPackage(POLARS_WHEEL).then(function () { return py; });
          })
          .then(resolve, reject);
      };
      s.onerror = function () {
        reject(new Error('Pyodide could not be loaded (network unavailable?).'));
      };
      document.head.appendChild(s);
    });
    return _pyodidePromise;
  }

  /* ── Page wiring ── */

  function init() {
    var cards = document.querySelectorAll('[data-py-sandbox]');
    if (!cards.length) return;

    cards.forEach(function (card) {
      var ex = {};
      try { ex = JSON.parse(card.getAttribute('data-ex') || '{}'); } catch (_) {}
      if (!ex.expected) return;

      var editor = card.querySelector('[data-py-editor]');
      var runBtn = card.querySelector('[data-py-run]');
      var hintBtn = card.querySelector('[data-py-hint]');
      var resetBtn = card.querySelector('[data-py-reset]');
      var status = card.querySelector('[data-py-status]');
      var engineStatus = card.querySelector('[data-py-engine-status]');
      var hintText = card.querySelector('[data-py-hint-text]');
      var result = card.querySelector('[data-py-result]');

      resetBtn.addEventListener('click', function () {
        editor.value = ex.starter || '';
        hintText.classList.add('hidden');
        result.innerHTML = '';
        status.textContent = '';
      });
      hintBtn.addEventListener('click', function () {
        hintText.classList.toggle('hidden');
      });

      runBtn.addEventListener('click', function () {
        var src = normalizePy(editor.value);
        if (!src) {
          status.textContent = 'Enter some Python first.';
          return;
        }
        status.textContent = 'Loading Pyodide + Polars (large download)…';
        loadPyodide().then(function (py) {
          engineStatus.textContent = 'Pyodide ready — Python ' + py.version;
          var files = {
            'transactions.csv': [
              'id,account_id,txn_type,amount,currency,txn_date',
              '1,1,cash_deposit,12500,USD,2026-06-02',
              '2,2,wire_in,8000,USD,2026-06-03',
              '3,3,cash_deposit,9500,USD,2026-06-04',
              '4,3,cash_deposit,9200,USD,2026-06-05',
              '5,3,cash_deposit,9400,USD,2026-06-06',
              '6,3,cash_deposit,9100,USD,2026-06-08',
              '7,3,cash_deposit,9300,USD,2026-06-09',
              '8,4,cash_deposit,6500,USD,2026-06-03',
              '9,4,wire_out,50000,USD,2026-06-05',
              '10,5,wire_in,250000,USD,2026-06-01',
              '11,5,wire_out,240000,USD,2026-06-02',
              '12,6,cash_deposit,11000,USD,2026-06-04',
              '13,7,cash_deposit,3000,USD,2026-06-06',
              '14,7,cash_deposit,2800,USD,2026-06-07',
              '15,7,cash_deposit,3100,USD,2026-06-08',
              '16,8,wire_in,90000,USD,2026-06-05',
              '17,8,wire_out,89000,USD,2026-06-06',
              '18,9,ach,4500,USD,2026-06-07',
              '19,10,wire_in,60000,USD,2026-06-08',
              '20,10,wire_out,59000,USD,2026-06-09',
              '21,11,cash_deposit,15000,USD,2026-06-10',
              '22,12,transfer,30000,USD,2026-06-11',
              '23,13,cash_deposit,4500,USD,2026-06-12',
              '24,13,cash_deposit,4600,USD,2026-06-12',
              '25,13,cash_deposit,4400,USD,2026-06-13',
              '26,13,cash_deposit,4700,USD,2026-06-14',
              '27,14,cash_deposit,12000,USD,2026-06-15',
              '28,14,cash_deposit,11800,USD,2026-06-16',
              '29,15,cash_deposit,11500,USD,2026-06-17',
              '30,15,cash_deposit,11200,USD,2026-06-18',
              '31,16,transfer,2000,USD,2026-06-18',
              '32,17,cash_deposit,9000,USD,2026-06-19',
              '33,18,cash_deposit,7000,USD,2026-06-20',
              '34,19,wire_in,15000,USD,2026-06-21',
              '35,20,cash_deposit,13500,USD,2026-06-22',
              '36,5,ach,12000,USD,2026-06-23',
            ].join('\n'),
            'accounts.csv': 'id,customer_id,account_type\n1,1,checking\n2,1,savings\n3,2,checking\n4,3,checking\n5,4,foreign\n6,5,checking\n7,6,checking\n8,7,business\n9,8,checking\n10,9,foreign\n11,10,checking\n12,11,checking\n13,12,checking\n14,13,checking\n15,14,business\n16,15,checking\n17,3,savings\n18,7,checking\n19,5,savings\n20,13,foreign\n',
            'customers.csv': [
              'id,name,jurisdiction,risk_rating,is_pep',
              '1,Ana Ruiz,Spain,low,0',
              '2,Jean-Claude Moreau,France,low,0',
              '3,Yusuf Demir,Turkey,medium,0',
              '4,Elena Volkov,Russia,high,1',
              '5,Chen Wei,China,medium,0',
              '6,Grace Adeyemi,Nigeria,medium,0',
              '7,Viktor Petrov,Cyprus,high,1',
              '8,Sofia Bianchi,Italy,low,0',
              '9,Omar Haddad,Lebanon,high,0',
              '10,Lena Novak,Czechia,low,0',
              '11,Marcus Weber,Germany,low,0',
              '12,Priya Sharma,India,medium,0',
              '13,Carlos Mendez,Mexico,high,0',
              '14,Ahmed Al-Farsi,UAE,medium,0',
              '15,Ivan Kuznetsov,Latvia,medium,0',
            ].join('\n'),
          };
          try {
            Object.keys(files).forEach(function (name) {
              py.FS.writeFile('/' + name, files[name]);
              py.runPython('import shutil; shutil.copy(/' + name + ', ' + JSON.stringify(name) + ')');
            });
            var studentNs = py.toPy({});
            var expNs = py.toPy({});
            py.runPython(src, { globals: studentNs });
            py.runPython(ex.expected, { globals: expNs });
            var got = capturePrint(py, studentNs);
            var expected = capturePrint(py, expNs);
            var pass = got === expected;
            var out = document.createElement('pre');
            out.className = 'sandbox-output';
            out.textContent = got;
            result.innerHTML = '';
            result.appendChild(out);
            if (pass) {
              status.textContent = '✓ Output matches the reference.';
              status.className = 'text-xs font-semibold sandbox-ok';
            } else {
              status.textContent = '✗ Output differs from the reference — compare and adjust.';
              status.className = 'text-xs font-semibold sandbox-err';
            }
          } catch (e) {
            var msg = (e.message || String(e)).split('\n').slice(-6).join('\n');
            renderPyError(result, msg);
            status.textContent = '';
          }
        }).catch(function (e) {
          engineStatus.textContent = 'Engine failed to load.';
          status.textContent = '';
          renderPyError(result, e.message);
        });
      });
    });
  }

  function capturePrint(py, ns) {
    var lines = [];
    py.setStdout({ batched: function (s) { lines.push(String(s)); } });
    py.runPython('print(summary)', { globals: ns });
    return lines.join('\n').trim();
  }

  function renderPyError(container, msg) {
    var pre = document.createElement('pre');
    pre.className = 'sandbox-output sandbox-err';
    pre.textContent = msg;
    container.innerHTML = '';
    container.appendChild(pre);
  }

  if (typeof document !== 'undefined') {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', init);
    } else {
      init();
    }
  }

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
      normalizePy: normalizePy,
      countWords: countWords,
    };
  }
})();
