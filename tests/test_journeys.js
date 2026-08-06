'use strict';
const jsFile = require.resolve('../static/js/journeys.js');
const j = require(jsFile);

function assert(cond, msg) {
  if (!cond) {
    console.error('FAIL: ' + (msg || 'assertion'));
    process.exit(1);
  }
}

// readState pads and clips to total
const storage = {};
const fakeStorage = {
  getItem: (k) => (k in storage ? storage[k] : null),
  setItem: (k, v) => { storage[k] = String(v); },
};
storage['acacia_journey_test'] = JSON.stringify([true, false]);
assert(j.readState(fakeStorage, 'test', 3).join(',') === 'true,false,false', 'readState pads');
storage['acacia_journey_test'] = JSON.stringify([true, true, true, true]);
assert(j.readState(fakeStorage, 'test', 3).join(',') === 'true,true,true', 'readState clips');
delete storage['acacia_journey_test'];
assert(j.readState(fakeStorage, 'test', 2).join(',') === 'false,false', 'readState default');

// toggleStep is immutable
const s = [false, true];
const t = j.toggleStep(s, 0);
assert(t[0] === true && s[0] === false, 'toggleStep immutable');
assert(j.toggleStep(s, 5) === s, 'toggleStep out of range returns same');
assert(j.toggleStep([true], 0)[0] === false, 'toggleStep unchecks');

// progressPercent
assert(j.progressPercent([true, false, true, false]) === 50, 'progress 50%');
assert(j.progressPercent([]) === 0, 'progress empty');
assert(j.progressPercent([true, true]) === 100, 'progress 100%');

// isComplete
assert(j.isComplete([true, true]) === true, 'complete');
assert(j.isComplete([true, false]) === false, 'incomplete');
assert(j.isComplete([]) === false, 'empty not complete');

// nextIncomplete
assert(j.nextIncomplete([false, false]) === 0, 'first incomplete');
assert(j.nextIncomplete([true, false]) === 1, 'second incomplete');
assert(j.nextIncomplete([true, true]) === -1, 'all complete');

// writeState round-trip
j.writeState(fakeStorage, 'roundtrip', [true, false]);
assert(j.readState(fakeStorage, 'roundtrip', 2).join(',') === 'true,false', 'writeState round-trip');

console.log('All journeys.js tests passed (' + 18 + ' assertions)');
