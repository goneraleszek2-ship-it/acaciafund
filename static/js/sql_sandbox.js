
/* sql_sandbox.js */

/* sql_sandbox.js */

/* sql_sandbox.js */

/* sql_sandbox.js */

/* sql_sandbox.js */

/* sql_sandbox.js */
/* sql_sandbox.js */

/* sql_sandbox.js */

/* sql_sandbox.js */
(function () {
  'use strict';

  /* ── Pure helpers (unit-tested via tests/test_sql_sandbox.js) ── */

  function normalizeSql(sql) {
    return String(sql || '')
      .replace(/;?\s*$/, '')
      .replace(/\s+/g, ' ')
      .trim()
      .toLowerCase();
  }

  function canonicalRow(row) {
    return row.map(function (v) {
      if (v === null || v === undefined) return '\u0000null';
      if (typeof v === 'number') return String(Math.round(v * 10000) / 10000);
      return '\u0001' + String(v);
    }).sort().join('\u0002');
  }

  function rowsEqual(student, expected) {
    if (student.length !== expected.length) return false;
    var a = student.map(canonicalRow).sort();
    var b = expected.map(canonicalRow).sort();
    for (var i = 0; i < a.length; i++) {
      if (a[i] !== b[i]) return false;
    }
    return true;
  }

  function checkAnswer(studentSql, expectedSql, runner) {
    var student = runner(studentSql);
    var expected = runner(expectedSql);
    var match = rowsEqual(student.rows, expected.rows);
    return {
      pass: match,
      studentColumns: student.columns,
      expectedColumns: expected.columns,
      studentRows: student.rows,
      expectedRows: expected.rows,
    };
  }

  /* ── Engine loading (sql.js from CDN with fallbacks) ── */

  var CDNS = [
    'https://cdn.jsdelivr.net/npm/sql.js@1.10.3/dist/sql-wasm.js',
    'https://unpkg.com/sql.js@1.10.3/dist/sql-wasm.js',
  ];
  var WASM = 'https://cdn.jsdelivr.net/npm/sql.js@1.10.3/dist/sql-wasm.wasm';
  var _enginePromise = null;

  function loadSQLJS() {
    if (typeof window.initSqlJs === 'function') {
      return Promise.resolve(window.initSqlJs);
    }
    if (_enginePromise) return _enginePromise;
    _enginePromise = new Promise(function (resolve, reject) {
      var tried = 0;
      var fail = function (e) {
        tried++;
        if (tried >= CDNS.length) {
          reject(new Error('SQLite engine could not be loaded (network unavailable?).'));
        } else {
          loadFrom(CDNS[tried]);
        }
      };
      var loadFrom = function (src) {
        var s = document.createElement('script');
        s.src = src;
        s.onload = function () {
          if (typeof window.initSqlJs === 'function') {
            resolve(window.initSqlJs);
          } else {
            fail(new Error('initSqlJs missing'));
          }
        };
        s.onerror = fail;
        document.head.appendChild(s);
      };
      loadFrom(CDNS[0]);
    });
    return _enginePromise;
  }

  /* ── Result rendering ── */

  function renderTable(container, columns, rows) {
    container.innerHTML = '';
    var table = document.createElement('table');
    table.className = 'sandbox-table';
    var thead = document.createElement('thead');
    var tr = document.createElement('tr');
    columns.forEach(function (c) {
      var th = document.createElement('th');
      th.textContent = c;
      tr.appendChild(th);
    });
    thead.appendChild(tr);
    table.appendChild(thead);
    var tbody = document.createElement('tbody');
    rows.forEach(function (row) {
      var r = document.createElement('tr');
      row.forEach(function (cell) {
        var td = document.createElement('td');
        td.textContent = cell === null ? 'NULL' : String(cell);
        r.appendChild(td);
      });
      tbody.appendChild(r);
    });
    table.appendChild(tbody);
    container.appendChild(table);
    return table;
  }

  function renderMessage(container, text, kind) {
    container.innerHTML = '';
    var p = document.createElement('p');
    p.className = 'sandbox-msg ' + (kind || '');
    p.textContent = text;
    container.appendChild(p);
  }

  /* ── Page wiring ── */

  function init() {
    var cards = document.querySelectorAll('[data-sql-sandbox]');
    if (!cards.length) return;

    cards.forEach(function (card) {
      var ex = {};
      try { ex = JSON.parse(card.getAttribute('data-ex') || '{}'); } catch (_) {}
      if (!ex.expected) return;

      var editor = card.querySelector('[data-sql-editor]');
      var runBtn = card.querySelector('[data-sql-run]');
      var hintBtn = card.querySelector('[data-sql-hint]');
      var resetBtn = card.querySelector('[data-sql-reset]');
      var status = card.querySelector('[data-sql-status]');
      var hintText = card.querySelector('[data-sql-hint-text]');
      var result = card.querySelector('[data-sql-result]');

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
        var sql = editor.value;
        if (!normalizeSql(sql)) {
          status.textContent = 'Enter a query first.';
          return;
        }
        status.textContent = 'Loading SQLite…';
        loadSQLJS().then(function () {
          var db = new window.SQL.Database();
          try {
            db.exec(ex.dataset.schema);
            db.exec(ex.dataset.seed);
          } catch (e) {
            status.textContent = '';
            renderMessage(result, 'Dataset failed to load: ' + e.message, 'sandbox-err');
            return;
          }
          var run = function (q) {
            try {
              var stmt = db.prepare(q);
              var cols = stmt.getColumnNames();
              var rows = [];
              while (stmt.step()) rows.push(stmt.get());
              stmt.free();
              return { columns: cols, rows: rows };
            } catch (e) {
              return { error: e.message };
            }
          };
          var student = run(sql);
          if (student.error) {
            status.textContent = '';
            renderMessage(result, 'Query error: ' + student.error, 'sandbox-err');
            return;
          }
          var verdict = checkAnswer(sql, ex.expected, run);
          renderTable(result, verdict.studentColumns, verdict.studentRows);
          if (verdict.pass) {
            status.textContent = '✓ Correct!';
            status.className = 'text-xs font-semibold sandbox-ok';
          } else {
            status.textContent = '✗ Not quite — expected rows differ.';
            status.className = 'text-xs font-semibold sandbox-err';
          }
          db.close();
        }).catch(function (e) {
          status.textContent = '';
          renderMessage(result, e.message, 'sandbox-err');
        });
      });
    });
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
      normalizeSql: normalizeSql,
      canonicalRow: canonicalRow,
      rowsEqual: rowsEqual,
      checkAnswer: checkAnswer,
    };
  }
})();
