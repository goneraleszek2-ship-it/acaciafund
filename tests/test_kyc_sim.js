// test_kyc_sim.js — node tests for kyc_sim.js pure helpers.
'use strict';

const assert = require('assert');
const kyc = require(require.resolve('../static/js/kyc_sim.js'));

const multiStep = {
  id: 'identity',
  kind: 'multi',
  correct: ['A', 'B', 'C'],
};
const singleStep = {
  id: 'ubo',
  kind: 'single',
  correct: 'Option D',
};

// isComplete
assert(kyc.isComplete(multiStep, ['A', 'B', 'C']), 'multi complete');
assert(!kyc.isComplete(multiStep, ['A', 'B']), 'multi incomplete');
assert(!kyc.isComplete(multiStep, undefined), 'multi no selection');
assert(kyc.isComplete(singleStep, 'Option D'), 'single complete');
assert(!kyc.isComplete(singleStep, null), 'single incomplete');

// correctSet
let v = kyc.correctSet(multiStep, ['A', 'B', 'C']);
assert(v.pass && v.missing.length === 0, 'exact multi passes');
v = kyc.correctSet(multiStep, ['A', 'B', 'C', 'D']);
assert(!v.pass, 'extra multi selection fails');
v = kyc.correctSet(multiStep, ['A', 'B']);
assert(!v.pass && v.missing.join(',') === 'C', 'missing reported');
v = kyc.correctSet(singleStep, 'Option D');
assert(v.pass, 'single correct');
v = kyc.correctSet(singleStep, 'Wrong');
assert(!v.pass, 'single wrong');

// progress
assert(kyc.progress(0, 3) === 33, 'progress first step');
assert(kyc.progress(2, 3) === 100, 'progress last step');

console.log('All kyc_sim.js tests passed.');
