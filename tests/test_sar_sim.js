// test_sar_sim.js — node tests for sar_sim.js pure helpers.
'use strict';

const assert = require('assert');
const sar = require(require.resolve('../static/js/sar_sim.js'));

const longNarrative = Array(40).fill('suspicious').join(' ');

// validateSar
let r = sar.validateSar({ subject: 'Acme', flags: ['f1'], narrative: longNarrative, minWords: 20 });
assert(r.valid && r.wordCount === 40, 'valid SAR passes');

r = sar.validateSar({ subject: '', flags: ['f1'], narrative: longNarrative, minWords: 20 });
assert(!r.valid && r.issues.some((i) => /Subject/.test(i)), 'missing subject flagged');

r = sar.validateSar({ subject: 'Acme', flags: [], narrative: longNarrative, minWords: 20 });
assert(!r.valid && r.issues.some((i) => /red flag/i.test(i)), 'no flags flagged');

r = sar.validateSar({ subject: 'Acme', flags: ['f1'], narrative: 'short', minWords: 20 });
assert(!r.valid && r.issues.some((i) => /20 words/.test(i)), 'short narrative flagged');

r = sar.validateSar({ subject: 'Acme', flags: ['f1'], narrative: ' '.repeat(500) + '  ', minWords: 20 });
assert(!r.valid, 'whitespace-only narrative rejected');

console.log('All sar_sim.js tests passed.');
