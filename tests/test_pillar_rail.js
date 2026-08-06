'use strict';
const jsFile = require.resolve('../static/js/pillar_rail.js');
const p = require(jsFile);

function assert(cond, msg) {
  if (!cond) {
    console.error('FAIL: ' + (msg || 'assertion'));
    process.exit(1);
  }
}

// ringPath
const ring = p.ringPath(50, 9);
assert(Math.abs(ring.circumference - 2 * Math.PI * 9) < 1e-6, 'circumference');
assert(Math.abs(ring.offset - ring.circumference * 0.5) < 1e-6, '50% offset');
assert(p.ringPath(0, 9).offset === p.ringPath(0, 9).circumference, '0% full offset');
assert(p.ringPath(120, 9).offset === 0, 'clamp >100');
assert(p.ringPath(-5, 9).offset === p.ringPath(-5, 9).circumference, 'clamp <0');

// masteryPct
const store = { c1: { reps: 3 }, c2: { reps: 0 }, c3: {} };
assert(p.masteryPct([{ id: 'c1' }, { id: 'c2' }, { id: 'c3' }], store, 'id') === 33, '33% mastery');
assert(p.masteryPct([], store, 'id') === 0, 'empty entries');

// dueEntries
const now = 1000;
const dueStore = {
  a: { reps: 1, due: 500 },
  b: { reps: 0, due: 0 },
  c: { reps: 2, due: 2000 },
};
const entries = [{ id: 'a' }, { id: 'b' }, { id: 'c' }];
const due = p.dueEntries(entries, dueStore, 'id', now);
assert(due.length === 2 && due[0].id === 'b' && due[1].id === 'a', 'due sorted, unseen first');

// nextDue
const next = p.nextDue([1, 2, 3, 4], 2);
assert(next.length === 2 && next[0] === 1 && next[1] === 2, 'nextDue slice');
assert(p.nextDue([], 3).length === 0, 'nextDue empty');

console.log('All pillar_rail.js tests passed (' + 14 + ' assertions)');
