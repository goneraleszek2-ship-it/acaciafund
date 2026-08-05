'use strict';

const jsFile = require.resolve('../static/js/search.js');
delete require.cache[jsFile];

const search = require(jsFile);

let passed = 0;
let failed = 0;

function assert(cond, msg) {
  if (cond) passed++;
  else { failed++; console.error('  FAIL: ' + msg); }
}

const vocab = ['compliance', 'sanctions', 'monitoring', 'transaction', 'reporting', 'transaction-monitoring'];

/* ── bestCorrection ── */

assert(search.bestCorrection('compilance', vocab, 2) === 'compliance', 'one-edit typo corrected');
assert(search.bestCorrection('compilance', vocab, 1) === 'compliance', 'one-edit typo corrected with maxEdits 1');
assert(search.bestCorrection('monitoring', vocab, 2) === null, 'exact match -> null (no correction)');
assert(search.bestCorrection('xyz', vocab, 2) === null, 'no candidate -> null');
assert(search.bestCorrection('tr', vocab, 2) === null, 'token shorter than 3 chars -> null');
assert(search.bestCorrection('transaction', vocab, 1) === null, 'exact match with maxEdits 1 -> null');

/* ── didYouMean ── */

assert(search.didYouMean('compilance', vocab) === 'compliance', 'single typo corrected');
assert(search.didYouMean('santion', vocab) === 'sanctions', 'another single typo corrected');
assert(search.didYouMean('compilance monitorng', vocab) === 'compliance monitoring', 'multi-token correction');
assert(search.didYouMean('compliance', vocab) === null, 'already correct -> null');
assert(search.didYouMean('transaction monitoring', vocab) === null, 'already correct multi-token -> null');
assert(search.didYouMean('', vocab) === null, 'empty query -> null');
assert(search.didYouMean('foo bar baz', vocab) === null, 'no close matches -> null');
assert(search.didYouMean('x', vocab) === null, 'single short token -> null');
assert(search.didYouMean('compilance baz', vocab) === null, 'only half the tokens corrected -> null');
assert(search.didYouMean('transaction', vocab, 1) === null, 'exact match multi-token guard');

/* prefix-extension guard: a short valid term must not be "corrected" into a
   longer vocab word it is merely a prefix of (e.g. "aml" vs "amla") */
assert(search.bestCorrection('aml', ['amla'], 2) === null, 'prefix extension -> no correction');
assert(search.bestCorrection('amla', ['aml'], 2) === null, 'prefix extension (reversed) -> no correction');
assert(search.didYouMean('aml', ['amla']) === null, 'didYouMean skips prefix-extension candidates');
assert(search.bestCorrection('volatilty', ['volatility'], 2) === 'volatility', 'real typo still corrected after prefix guard');

/* ── buildVocabulary ── */

const index = [
  { title: 'Compliance monitoring with AI', tags: ['aml', 'machine-learning'], ontology_concepts: ['transaction monitoring'], technologies: ['python'], use_cases: ['sanctions-screening'] },
  { title: 'Markets', tags: ['volatility'], ontology_concepts: [], technologies: [], use_cases: [] },
];
const built = search.buildVocabulary(index, [{ label: 'Beneficial Ownership', aliases: ['ubo', 'ownership'] }]);
assert(built.indexOf('compliance') !== -1, 'title words included');
assert(built.indexOf('monitoring') !== -1, 'concept words included');
assert(built.indexOf('python') !== -1, 'technology words included');
assert(built.indexOf('aml') === -1, 'short words filtered');
assert(built.indexOf('ownership') !== -1, 'concept aliases included');

const emptyVocab = search.buildVocabulary([], []);
assert(Array.isArray(emptyVocab) && emptyVocab.length === 0, 'empty index -> empty vocabulary');

/* vocabulary-aware correction */
const strictVocab = ['sanctions', 'screening'];
assert(search.didYouMean('santion', strictVocab) === 'sanctions', 'vocabulary-driven correction works');

console.log('');
console.log('Search discovery tests: ' + passed + ' passed, ' + failed + ' failed');
process.exit(failed ? 1 : 0);
