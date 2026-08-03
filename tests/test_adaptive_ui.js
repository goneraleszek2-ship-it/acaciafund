'use strict';

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const jsFile = path.join(__dirname, '..', 'static', 'js', 'adaptive.js');
let moduleCache = require.resolve(jsFile);
delete require.cache[moduleCache];

// Load the module under Node (the UMD guard exposes module.exports)
const adaptive = require(jsFile);

let passed = 0;
let failed = 0;

function assert(cond, msg) {
  if (cond) {
    passed++;
  } else {
    failed++;
    console.error('  FAIL: ' + msg);
  }
}

function deepEq(a, b, msg) {
  assert(JSON.stringify(a) === JSON.stringify(b), msg + ' (got ' + JSON.stringify(a) + ', want ' + JSON.stringify(b) + ')');
}

/* ── computeDifficulty ── */

deepEq(adaptive.computeDifficulty([]), 'intermediate', 'empty answers default to intermediate');

const beginnerAnswers = [
  { target: 'beginner', value: 3 },
  { target: 'beginner', value: 3 },
  { target: 'intermediate', value: 0 },
  { target: 'advanced', value: 0 },
  { target: 'advanced', value: 0 },
];
assert(adaptive.computeDifficulty(beginnerAnswers) === 'beginner', 'strong beginner answers -> beginner');

const advancedAnswers = [
  { target: 'beginner', value: 0 },
  { target: 'beginner', value: 1 },
  { target: 'intermediate', value: 2 },
  { target: 'advanced', value: 3 },
  { target: 'advanced', value: 3 },
];
assert(adaptive.computeDifficulty(advancedAnswers) === 'advanced', 'strong advanced answers -> advanced');

const midAnswers = [
  { target: 'beginner', value: 1 },
  { target: 'beginner', value: 1 },
  { target: 'intermediate', value: 3 },
  { target: 'advanced', value: 1 },
  { target: 'advanced', value: 1 },
];
assert(adaptive.computeDifficulty(midAnswers) === 'intermediate', 'mixed answers -> intermediate');

assert(adaptive.computeDifficulty([{ target: 'beginner', value: 9 }]) === 'beginner', 'out-of-range values clamp to 3');

/* ── pickInterests ── */

const concepts = [
  { pillar: 'aml', category: 'cdd-kyc' },
  { pillar: 'aml', category: 'cdd-kyc' },
  { pillar: 'stock', category: 'market-microstructure' },
  { pillar: 'data-engineering', category: 'pipeline-architecture' },
];

deepEq(adaptive.pickInterests(concepts, [{ pillar: 'aml', category: 'cdd-kyc' }]), [{ pillar: 'aml', category: 'cdd-kyc' }], 'valid selection kept');
deepEq(adaptive.pickInterests(concepts, [{ pillar: 'aml', category: 'nope' }]), [], 'unknown category filtered');
deepEq(adaptive.pickInterests(concepts, [{ pillar: 'aml', category: 'cdd-kyc' }, { pillar: 'bogus', category: 'x' }]), [{ pillar: 'aml', category: 'cdd-kyc' }], 'mixed valid/invalid filtered');
deepEq(adaptive.pickInterests(concepts, [{ pillar: 'aml', category: 'cdd-kyc' }], 0), [], 'max=0 yields empty');
deepEq(adaptive.pickInterests(concepts, null), [], 'null selection handled');
deepEq(adaptive.pickInterests([], [{ pillar: 'aml', category: 'cdd-kyc' }]), [], 'no concepts -> empty');

/* ── buildInterestOptions ── */

const opts = adaptive.buildInterestOptions(concepts);
assert(opts.length === 3, 'three distinct pillar:category groups');
assert(opts[0].pillar === 'aml' && opts[0].category === 'cdd-kyc' && opts[0].count === 2, 'highest-count group first');
deepEq(adaptive.buildInterestOptions([]), [], 'no concepts -> no options');
deepEq(adaptive.buildInterestOptions([{ pillar: 'aml' }]), [], 'concepts without category skipped');

/* ── pathStatus ── */

const now = Date.now();
const savedPath = [
  { id: 'c1', label: 'A', pillar: 'aml' },
  { id: 'c2', label: 'B', pillar: 'stock' },
  { id: 'c3', label: 'C', pillar: 'data-engineering' },
];
const mastery = {
  c1: { due: now - 1000, reps: 3 },
  c2: { due: now + 86400000, reps: 1 },
  c3: { due: 0, reps: 0 },
};
const statuses = adaptive.pathStatus(savedPath, mastery, now);
assert(statuses.length === 3, 'every path entry decorated');
deepEq(statuses.map(function (s) { return s.status; }), ['due', 'scheduled', 'new'], 'status mapping correct');
assert(statuses[0].due === now - 1000, 'due timestamp passed through');

const emptyStatus = adaptive.pathStatus([], {}, now);
deepEq(emptyStatus, [], 'empty path -> empty result');

console.log('');
console.log('Adaptive UI tests: ' + passed + ' passed, ' + failed + ' failed');
process.exit(failed ? 1 : 0);
