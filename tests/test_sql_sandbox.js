// test_sql_sandbox.js — node tests for sql_sandbox.js pure helpers.
'use strict';

const assert = require('assert');
const sqljs = require(require.resolve('../static/js/sql_sandbox.js'));

// normalizeSql
assert(sqljs.normalizeSql('  SELECT   a , b FROM t ;') === 'select a , b from t', 'normalizeSql trims/collapses');
assert(sqljs.normalizeSql(null) === '', 'normalizeSql null-safe');
assert(sqljs.normalizeSql('') === '', 'normalizeSql empty');

// rowsEqual
assert(sqljs.rowsEqual([[1, 'a']], [[1, 'a']]), 'identical rows');
assert(!sqljs.rowsEqual([[1, 'a']], [[1, 'b']]), 'different value');
assert(sqljs.rowsEqual([[1, 'a'], [2, 'b']], [[2, 'b'], [1, 'a']]), 'row order insensitive');
assert(!sqljs.rowsEqual([[1]], [[1], [1]]), 'row count matters');
assert(sqljs.rowsEqual([[1.5]], [[1.50001]]), 'numeric tolerance rounds to 4dp');

// checkAnswer with a stub runner
const runner = (q) => {
  if (q === 'SELECT x FROM t WHERE a > 1') return { columns: ['x'], rows: [[3], [2]] };
  if (q === 'SELECT 2;') return { columns: ['2'], rows: [[2]] };
  return { columns: ['x'], rows: [] };
};
let res = sqljs.checkAnswer('SELECT x FROM t WHERE a > 1', 'SELECT 2;', runner);
assert(res.pass === false, 'mismatch detected');
res = sqljs.checkAnswer('SELECT x FROM t WHERE a > 1', 'SELECT x FROM t WHERE a > 1', runner);
assert(res.pass === true, 'match detected');
assert(res.studentColumns.length === 1 && res.expectedRows.length === 2, 'result surfaces columns/rows');

console.log('All sql_sandbox.js tests passed.');
