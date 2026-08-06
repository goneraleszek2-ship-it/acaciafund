'use strict';
const jsFile = require.resolve('../static/js/study_dashboard.js');
const s = require(jsFile);

function assert(cond, msg) {
  if (!cond) {
    console.error('FAIL: ' + (msg || 'assertion'));
    process.exit(1);
  }
}

const NOW = new Date('2026-08-06T12:00:00Z').getTime();
const day = (offset) => new Date(NOW - offset * 86400000).toISOString().slice(0, 10);

// streakFromHistory
assert(s.streakFromHistory([day(0), day(1), day(2)], NOW) === 3, '3-day streak');
assert(s.streakFromHistory([day(1), day(2)], NOW) === 2, 'yesterday-anchored streak');
assert(s.streakFromHistory([day(2), day(4)], NOW) === 0, 'broken streak');
assert(s.streakFromHistory([day(3)], NOW) === 0, 'stale history');
assert(s.streakFromHistory([], NOW) === 0, 'empty history');

// weekBars
const bars = s.weekBars([day(0), day(2)], NOW);
assert(bars.length === 7, '7 bars');
assert(bars[6].active === true, 'today active');
assert(bars[4].active === true, 'two days ago active');
assert(bars[0].active === false, 'six days ago inactive');
assert(typeof bars[0].day === 'string' && bars[0].day.length > 0, 'day label');

// nextUp
const store = {
  a: { reps: 1, due: NOW + 2 * 86400000 },
  b: { reps: 0, due: 0 },
  c: { reps: 2, due: NOW + 10 * 86400000 },
  d: { reps: 1, due: NOW - 1000 },
};
const cards = [{ id: 'a' }, { id: 'b' }, { id: 'c' }, { id: 'd' }];
const up = s.nextUp(cards, store, 3, NOW);
assert(up.length === 3, 'top 3 upcoming');
assert(up[0].id === 'b', 'unseen sorts first');
assert(up[2].id === 'c', 'long-dated last');
assert(up.indexOf({ id: 'd' }) === -1, 'due card excluded');

// dueInLabel
assert(s.dueInLabel(NOW - 5, NOW) === 'due', 'overdue label');
assert(s.dueInLabel(NOW + 86400000, NOW) === 'tomorrow', 'tomorrow label');
assert(s.dueInLabel(NOW + 4 * 86400000, NOW) === 'in 4d', '4d label');

// weakConcepts
const weakStore = {
  w1: { reps: 5, ease: 1.6 },
  w2: { reps: 2, ease: 1.9 },
  ok: { reps: 3, ease: 2.5 },
  fresh: { reps: 0, ease: 1.5 },
};
const weak = s.weakConcepts(weakStore, 2.0);
assert(weak.length === 2, 'only reviewed under-ease');
assert(weak[0].id === 'w1', 'sorted by ease');
assert(s.weakConcepts({}, 2.0).length === 0, 'empty store');

console.log('All study_dashboard.js tests passed (' + 22 + ' assertions)');
