// test_pyodide_sandbox.js — node tests for pyodide_sandbox.js pure helpers.
'use strict';

const assert = require('assert');
const py = require(require.resolve('../static/js/pyodide_sandbox.js'));

assert(py.normalizePy('  import polars as pl\n') === 'import polars as pl', 'normalizePy trims');
assert(py.normalizePy('a\r\nb') === 'a\nb', 'normalizePy normalizes CRLF');
assert(py.countWords('') === 0, 'empty word count');
assert(py.countWords('  one   two three ') === 3, 'word count');

console.log('All pyodide_sandbox.js tests passed.');
