'use strict';
const fs = require('fs');
const path = require('path');

const src = fs.readFileSync(path.join(__dirname, '..', 'static', 'js', 'learning_hub.js'), 'utf8');

let failures = 0;
function assert(cond, msg) {
  if (!cond) {
    console.error('FAIL: ' + msg);
    failures++;
  }
}

// addToQueue exists on SM2Scheduler and seeds unscheduled cards
assert(/addToQueue\(ids\)/.test(src), 'SM2Scheduler.addToQueue(ids) defined');
assert(/reps === 0 && c\.lastReview === 0/.test(src), 'addToQueue only seeds never-reviewed cards');
assert(/this\.save\(\)/.test(src), 'addToQueue persists');

// DOM wiring for prerequisite banner + CTA
assert(/data-prereq-banner/.test(src), 'prerequisite banner selector');
assert(/acacia_prereq_dismissed_/.test(src), 'prereq dismiss localStorage key');
assert(/data-add-to-queue/.test(src), 'add-to-queue button selector');
assert(/review-badge-update/.test(src), 'badge refresh after add');

if (failures) {
  console.error(failures + ' assertion(s) failed');
  process.exit(1);
}
console.log('All learning_hub.js integration tests passed (7 assertions)');
