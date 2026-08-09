'use strict';
const jsFile = require.resolve('../static/js/concept_tabs.js');
const p = require(jsFile);

function assert(cond, msg) {
  if (!cond) {
    console.error('FAIL: ' + (msg || 'assertion'));
    process.exit(1);
  }
}

function mockEl(attrs) {
  return {
    getAttribute: function (attr) { return attrs[attr] === undefined ? null : attrs[attr]; },
  };
}

// tabNames
const panels = [
  mockEl({ 'data-tabpanel': 'overview' }),
  mockEl({ 'data-tabpanel': 'articles' }),
  mockEl({ 'data-tabpanel': 'prerequisites' }),
  mockEl({ 'data-tabpanel': 'advanced' }),
];
assert(JSON.stringify(p.tabNames(panels)) === JSON.stringify(['overview', 'articles', 'prerequisites', 'advanced']), 'tabNames order');
assert(p.tabNames([]).length === 0, 'tabNames empty');
assert(p.tabNames([mockEl({})]).length === 0, 'tabNames filters nulls');

// nextTab (wrap-around keyboard navigation)
assert(p.nextTab(0, 1, 4) === 1, 'next forward');
assert(p.nextTab(3, 1, 4) === 0, 'wrap forward');
assert(p.nextTab(0, -1, 4) === 3, 'wrap backward');
assert(p.nextTab(2, -1, 4) === 1, 'backward');
assert(p.nextTab(0, 1, 0) === -1, 'zero count');
assert(p.nextTab(0, 2, 4) === 2, 'multi-step');
assert(p.nextTab(1, 2, 4) === 3, 'multi-step wrap');

// filterItems
function mockCard(type) {
  return { getAttribute: function (attr) { return attr === 'data-content-type' ? type : null; } };
}
const cards = [mockCard('research'), mockCard('learn'), mockCard('knowledge'), mockCard('research')];
assert(p.filterItems(cards, 'research').length === 2, 'filter research');
assert(p.filterItems(cards, 'learn').length === 1, 'filter learn');
assert(p.filterItems(cards, 'all').length === 4, 'filter all');
assert(p.filterItems(cards, '').length === 4, 'filter empty means all');
assert(p.filterItems(cards, 'x').length === 0, 'filter unknown');
assert(p.filterItems(cards, 'research')[0] === cards[0], 'filter keeps order');

console.log('All concept_tabs.js tests passed.');
