/**
 * Tests for static/js/toc.js pure functions
 * Run with: node tests/test_toc.js
 */

const { createItems, linkClassFor } = require('../static/js/toc.js');

let passed = 0;
let failed = 0;

function assert(cond, name) {
  if (cond) {
    passed++;
    console.log(`  ✓ ${name}`);
  } else {
    failed++;
    console.error(`  ✗ ${name}`);
  }
}

console.log('toc.js pure function tests:');

// createItems — assigns sequential ids when missing
{
  const items = createItems([
    { tag: 'h2', text: 'Overview' },
    { tag: 'h2', text: 'Examples' },
    { tag: 'h3', text: 'Nested' },
  ]);
  assert(items.length === 3, 'testCreateItemsCount');
  assert(items[0].id === 'section-1' && items[1].id === 'section-2', 'testCreateItemsAssignsIds');
  assert(items[0].tag === 'h2' && items[2].tag === 'h3', 'testCreateItemsNormalizesTag');
  assert(items[1].text === 'Examples', 'testCreateItemsKeepsText');
}

// createItems — preserves provided ids
{
  const items = createItems([
    { id: 'intro', tag: 'H2', text: 'Intro' },
    { tag: 'h2', text: 'Body' },
  ]);
  assert(items[0].id === 'intro', 'testCreateItemsKeepsProvidedId');
  assert(items[0].tag === 'h2', 'testCreateItemsLowercasesTag');
}

// createItems — empty input
{
  const items = createItems([]);
  assert(Array.isArray(items) && items.length === 0, 'testCreateItemsEmpty');
}

// createItems — trims whitespace text, fills empty tags
{
  const items = createItems([{ tag: '', text: '  padded  ' }]);
  assert(items[0].text === 'padded', 'testCreateItemsTrimsText');
  assert(items[0].tag === 'h2', 'testCreateItemsDefaultsTag');
}

// linkClassFor — h3 gets toc-h3, h2 gets nothing
{
  assert(linkClassFor({ tag: 'h3' }) === 'toc-h3', 'testLinkClassForH3');
  assert(linkClassFor({ tag: 'h2' }) === '', 'testLinkClassForH2');
  assert(linkClassFor({ tag: 'h1' }) === '', 'testLinkClassForH1');
}

console.log(`\n${passed} passed, ${failed} failed`);
if (failed > 0) process.exit(1);
