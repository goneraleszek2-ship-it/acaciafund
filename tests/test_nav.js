'use strict';
const assert = require('assert');
const { navState } = require('../static/js/main.js');

let passed = 0;
function t(name, fn) {
  fn();
  passed++;
  console.log('  \u2713 ' + name);
}

console.log('test_nav.js');

t('navState closed: expanded=false, label opens', () => {
  const s = navState(false);
  assert.strictEqual(s.expanded, 'false');
  assert.strictEqual(s.label, 'Open navigation menu');
});

t('navState open: expanded=true, label closes', () => {
  const s = navState(true);
  assert.strictEqual(s.expanded, 'true');
  assert.strictEqual(s.label, 'Close navigation menu');
});

t('navState returns stable objects (no shared state)', () => {
  const a = navState(true);
  const b = navState(false);
  assert.strictEqual(a.expanded, 'true');
  assert.strictEqual(b.expanded, 'false');
  assert.notStrictEqual(a, b);
});

t('navState label round-trips through both states', () => {
  const states = [navState(false), navState(true), navState(false), navState(true)];
  assert.deepStrictEqual(states.map(s => s.label), [
    'Open navigation menu',
    'Close navigation menu',
    'Open navigation menu',
    'Close navigation menu',
  ]);
});

console.log('\n  ' + passed + ' tests passed\n');
