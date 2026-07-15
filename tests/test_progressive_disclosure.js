/**
 * Tests for static/js/progressive_disclosure.js pure functions
 * Run with: node tests/test_progressive_disclosure.js
 */
const assert = require('assert');
const { parseSections, toggleSection } = require('../static/js/progressive_disclosure.js');

// ── parseSections ────────────────────────────────────────────────────────────────

function testParseSectionsBasic() {
  const html = `
    <section class="prose-section"><h2>Introduction</h2><p>Content</p></section>
    <section class="prose-section"><h2>Methods</h2><p>Details</p></section>
    <section class="prose-section"><h3>Results</h3><p>Findings</p></section>
  `;
  const sections = parseSections(html);
  assert.strictEqual(sections.length, 3, 'should find 3 sections');
  assert.strictEqual(sections[0].title, 'Introduction');
  assert.strictEqual(sections[1].title, 'Methods');
  assert.strictEqual(sections[2].title, 'Results');
  assert.strictEqual(sections[0].isCollapsed, false, 'first section should be expanded');
  assert.strictEqual(sections[1].isCollapsed, true, 'second should be collapsed');
  assert.strictEqual(sections[2].isCollapsed, true, 'third should be collapsed');
  console.log('  ✓ testParseSectionsBasic');
}

function testParseSectionsEmpty() {
  const sections = parseSections('');
  assert.strictEqual(sections.length, 0);
  console.log('  ✓ testParseSectionsEmpty');
}

function testParseSectionsNoSections() {
  const html = '<div><p>No sections here</p></div>';
  const sections = parseSections(html);
  assert.strictEqual(sections.length, 0);
  console.log('  ✓ testParseSectionsNoSections');
}

function testParseSectionsWithoutHeadings() {
  const html = '<section class="prose-section"><p>Content without heading</p></section>';
  const sections = parseSections(html);
  assert.strictEqual(sections.length, 1);
  assert.strictEqual(sections[0].title, 'Section 1');
  console.log('  ✓ testParseSectionsWithoutHeadings');
}

// ── toggleSection ────────────────────────────────────────────────────────────────

function testToggleSection() {
  const sections = [
    { index: 0, title: 'A', isCollapsed: false },
    { index: 1, title: 'B', isCollapsed: true },
  ];
  const toggled = toggleSection(sections, 0);
  assert.strictEqual(toggled[0].isCollapsed, true, 'first should now be collapsed');
  assert.strictEqual(toggled[1].isCollapsed, true, 'second unchanged');
  console.log('  ✓ testToggleSection');
}

function testToggleSectionExpand() {
  const sections = [
    { index: 0, title: 'A', isCollapsed: false },
    { index: 1, title: 'B', isCollapsed: true },
  ];
  const toggled = toggleSection(sections, 1);
  assert.strictEqual(toggled[0].isCollapsed, false, 'first unchanged');
  assert.strictEqual(toggled[1].isCollapsed, false, 'second should now be expanded');
  console.log('  ✓ testToggleSectionExpand');
}

function testToggleSectionDoesNotMutate() {
  const sections = [
    { index: 0, title: 'A', isCollapsed: false },
  ];
  const toggled = toggleSection(sections, 0);
  assert.strictEqual(sections[0].isCollapsed, false, 'original unchanged');
  assert.strictEqual(toggled[0].isCollapsed, true, 'toggled changed');
  console.log('  ✓ testToggleSectionDoesNotMutate');
}

function testToggleSectionOutOfBounds() {
  const sections = [
    { index: 0, title: 'A', isCollapsed: false },
  ];
  const toggled = toggleSection(sections, 5);
  assert.strictEqual(toggled[0].isCollapsed, false, 'unchanged for out of bounds');
  console.log('  ✓ testToggleSectionOutOfBounds');
}

// ── Run ─────────────────────────────────────────────────────────────────────────

console.log('progressive_disclosure.js pure function tests:');
testParseSectionsBasic();
testParseSectionsEmpty();
testParseSectionsNoSections();
testParseSectionsWithoutHeadings();
testToggleSection();
testToggleSectionExpand();
testToggleSectionDoesNotMutate();
testToggleSectionOutOfBounds();
console.log('\n✓ All 8 tests passed');
