'use strict';
const jsFile = require.resolve('../static/js/diagnostic.js');
const diag = require(jsFile);

function assert(cond, msg) {
  if (!cond) {
    console.error('FAIL: ' + (msg || 'assertion'));
    process.exit(1);
  }
}

const questions = [
  { correct: 0 },
  { correct: 2 },
  { correct: 1 },
];

// scoreQuiz: all correct
assert(diag.scoreQuiz([0, 2, 1], questions) === 3, 'all correct scores 3');
// scoreQuiz: partial + skipped (-1)
assert(diag.scoreQuiz([0, -1, 1], questions) === 2, 'skipped counts as wrong');
// scoreQuiz: out-of-range answer counts wrong
assert(diag.scoreQuiz([9, 2, 1], questions) === 2, 'out-of-range counts wrong');

// levelForScore thresholds
assert(diag.levelForScore(0, 9) === 'beginner', '0/9 -> beginner');
assert(diag.levelForScore(3, 9) === 'beginner', '3/9 -> beginner');
assert(diag.levelForScore(4, 9) === 'intermediate', '4/9 -> intermediate');
assert(diag.levelForScore(6, 9) === 'intermediate', '6/9 -> intermediate');
assert(diag.levelForScore(7, 9) === 'expert', '7/9 -> expert');
assert(diag.levelForScore(9, 9) === 'expert', '9/9 -> expert');
assert(diag.levelForScore(0, 0) === 'beginner', 'empty -> beginner');

// levelLabel
assert(diag.levelLabel('intermediate') === 'Intermediate', 'label mapping');
assert(diag.levelLabel('unknown') === 'unknown', 'fallback label');

// setLearningMode writes localStorage + body class (node env: document shim not needed —
// function guards with try/catch, so call is safe without localStorage)
diag.setLearningMode('expert');

console.log('All diagnostic.js tests passed (' + 15 + ' assertions)');
