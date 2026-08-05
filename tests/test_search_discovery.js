'use strict';

const jsFile = require.resolve('../static/js/search.js');
delete require.cache[jsFile];

const search = require(jsFile);

let passed = 0;
let failed = 0;

function assert(cond, msg) {
  if (cond) passed++;
  else { failed++; console.error('  FAIL: ' + msg); }
}

const vocab = ['compliance', 'sanctions', 'monitoring', 'transaction', 'reporting', 'transaction-monitoring'];

/* ── bestCorrection ── */

assert(search.bestCorrection('compilance', vocab, 2) === 'compliance', 'one-edit typo corrected');
assert(search.bestCorrection('compilance', vocab, 1) === 'compliance', 'one-edit typo corrected with maxEdits 1');
assert(search.bestCorrection('monitoring', vocab, 2) === null, 'exact match -> null (no correction)');
assert(search.bestCorrection('xyz', vocab, 2) === null, 'no candidate -> null');
assert(search.bestCorrection('tr', vocab, 2) === null, 'token shorter than 3 chars -> null');
assert(search.bestCorrection('transaction', vocab, 1) === null, 'exact match with maxEdits 1 -> null');

/* ── didYouMean ── */

assert(search.didYouMean('compilance', vocab) === 'compliance', 'single typo corrected');
assert(search.didYouMean('santion', vocab) === 'sanctions', 'another single typo corrected');
assert(search.didYouMean('compilance monitorng', vocab) === 'compliance monitoring', 'multi-token correction');
assert(search.didYouMean('compliance', vocab) === null, 'already correct -> null');
assert(search.didYouMean('transaction monitoring', vocab) === null, 'already correct multi-token -> null');
assert(search.didYouMean('', vocab) === null, 'empty query -> null');
assert(search.didYouMean('foo bar baz', vocab) === null, 'no close matches -> null');
assert(search.didYouMean('x', vocab) === null, 'single short token -> null');
assert(search.didYouMean('compilance baz', vocab) === null, 'only half the tokens corrected -> null');
assert(search.didYouMean('transaction', vocab, 1) === null, 'exact match multi-token guard');

/* prefix-extension guard: a short valid term must not be "corrected" into a
   longer vocab word it is merely a prefix of (e.g. "aml" vs "amla") */
assert(search.bestCorrection('aml', ['amla'], 2) === null, 'prefix extension -> no correction');
assert(search.bestCorrection('amla', ['aml'], 2) === null, 'prefix extension (reversed) -> no correction');
assert(search.didYouMean('aml', ['amla']) === null, 'didYouMean skips prefix-extension candidates');
assert(search.bestCorrection('volatilty', ['volatility'], 2) === 'volatility', 'real typo still corrected after prefix guard');

/* ── buildVocabulary ── */

const index = [
  { title: 'Compliance monitoring with AI', tags: ['aml', 'machine-learning'], ontology_concepts: ['transaction monitoring'], technologies: ['python'], use_cases: ['sanctions-screening'] },
  { title: 'Markets', tags: ['volatility'], ontology_concepts: [], technologies: [], use_cases: [] },
];
const built = search.buildVocabulary(index, [{ label: 'Beneficial Ownership', aliases: ['ubo', 'ownership'] }]);
assert(built.indexOf('compliance') !== -1, 'title words included');
assert(built.indexOf('monitoring') !== -1, 'concept words included');
assert(built.indexOf('python') !== -1, 'technology words included');
assert(built.indexOf('aml') === -1, 'short words filtered');
assert(built.indexOf('ownership') !== -1, 'concept aliases included');

const emptyVocab = search.buildVocabulary([], []);
assert(Array.isArray(emptyVocab) && emptyVocab.length === 0, 'empty index -> empty vocabulary');

/* vocabulary-aware correction */
const strictVocab = ['sanctions', 'screening'];
assert(search.didYouMean('santion', strictVocab) === 'sanctions', 'vocabulary-driven correction works');

/* ── matchLevel ── */

assert(search.matchLevel('sanctions', 'sanctions screening') === 2, 'substring match -> level 2');
assert(search.matchLevel('monitoring', 'monitored systems') === 2, 'stem match -> level 2');
assert(search.matchLevel('compliance', 'complicance reports') === 1, 'fuzzy match -> level 1');
assert(search.matchLevel('zebra', 'sanctions screening') === 0, 'no match -> level 0');
assert(search.matchLevel('aml', 'anti money laundering') === 0, 'short token no substring match');

/* ── synonyms + expansion ── */

const synMap = search.getSynonymMap();
assert(Array.isArray(synMap['aml']) && synMap['aml'].indexOf('anti-money-laundering') !== -1, 'synonym map: aml -> anti-money-laundering');
assert(synMap['aml'].indexOf('anti money laundering') !== -1, 'synonym map: aml -> spaced variant');
assert(synMap['kyc'].indexOf('cdd') !== -1, 'synonym map: kyc -> cdd');
assert(synMap['knowyourcustomer'].indexOf('kyc') !== -1, 'synonym map: reverse direction works');

const expanded = search.expandTerm('kyc', synMap, {});
assert(expanded.indexOf('know-your-customer') !== -1, 'expandTerm includes hyphenated synonym');
assert(expanded.indexOf('know your customer') !== -1, 'expandTerm includes spaced synonym');
assert(expanded.indexOf('kyc') === 0, 'expandTerm keeps original token first');

const aliasMap = search.buildAliasMap([{ label: 'Beneficial Ownership', aliases: ['ubo', 'ownership'] }]);
assert(aliasMap['ubo'] && aliasMap['ubo'].indexOf('beneficial ownership') !== -1, 'buildAliasMap maps alias -> label');
const expandedAlias = search.expandTerm('ubo', {}, aliasMap);
assert(expandedAlias.indexOf('beneficial ownership') !== -1, 'expandTerm uses concept aliases');

/* ── entryHasAllTerms (multi-term AND) ── */

const andEntry = { title: 'Kafka Streams Transformation', tags: ['kafka'], ontology_concepts: [], technologies: [], use_cases: [], description: '' };
assert(search.entryHasAllTerms(andEntry, ['kafka', 'transformation'], {}, {}) === true, 'AND: both terms present -> true');
assert(search.entryHasAllTerms(andEntry, ['kafka', 'spark'], {}, {}) === false, 'AND: missing term -> false');
assert(search.entryHasAllTerms({ title: 'Know Your Customer onboarding', tags: [], ontology_concepts: [], technologies: [], use_cases: [], description: '' }, ['kyc'], synMap, {}) === true, 'AND via synonym phrase matches');

/* ── scoreEntry: fuzzy cap, title bonus, synonym scoring ── */

const sEntry = { title: 'Compliance reporting', description: 'compliance reporting basics', tags: [], ontology_concepts: [], technologies: [], use_cases: [], difficulty: 'beginner', avg_sqi: 0, date_str: '' };
const fuzzyScore = search.scoreEntry(sEntry, ['complicance'], {}, {});
assert(fuzzyScore === 2.5, 'fuzzy-only term capped at +2 (+0.5 difficulty) -> ' + fuzzyScore);
const exactScore = search.scoreEntry(sEntry, ['compliance'], {}, {});
assert(exactScore === 14.5, 'exact term scores normally (10+2 desc+2 bonus+0.5) -> ' + exactScore);
assert(exactScore > fuzzyScore * 2, 'exact matches rank far above fuzzy-only matches');

const kycEntry = { title: 'Know Your Customer onboarding', description: '', tags: [], ontology_concepts: [], technologies: [], use_cases: [], difficulty: 'beginner', avg_sqi: 0, date_str: '' };
assert(search.scoreEntry(kycEntry, ['kyc'], synMap, {}) === 10.5, 'synonym query scores on phrase title match -> ' + search.scoreEntry(kycEntry, ['kyc'], synMap, {}));

const firstTokenEntry = { title: 'Kafka pipelines', description: '', tags: [], ontology_concepts: [], technologies: [], use_cases: [], difficulty: '', avg_sqi: 0, date_str: '' };
assert(search.scoreEntry(firstTokenEntry, ['kafka', 'pipelines'], {}, {}) === 22, 'first-token title bonus applied once -> ' + search.scoreEntry(firstTokenEntry, ['kafka', 'pipelines'], {}, {}));

/* ── dateBoost ── */

assert(search.dateBoost('') === 0, 'no date -> no boost');
assert(search.dateBoost('garbage') === 0, 'invalid date -> no boost');
assert(search.dateBoost('2026-06-09') > search.dateBoost('2024-01-01'), 'recent items boosted more than old ones');
assert(search.dateBoost('2024-01-01') >= 0.5, 'old items floor at +0.5');
const dated = { title: 'Sanctions Screening', description: '', tags: [], ontology_concepts: [], technologies: [], use_cases: [], difficulty: '', avg_sqi: 0, date_str: '2026-06-09' };
const undated = { title: 'Sanctions Screening', description: '', tags: [], ontology_concepts: [], technologies: [], use_cases: [], difficulty: '', avg_sqi: 0, date_str: '' };
assert(search.scoreEntry(dated, ['sanctions'], {}, {}) > search.scoreEntry(undated, ['sanctions'], {}, {}), 'newer item outscores undated item');

/* ── applySort ── */

const sortScored = [
  { entry: { title: 'Old', date_str: '2024-01-01', avg_sqi: 0.7 }, score: 5 },
  { entry: { title: 'New', date_str: '2026-06-09', avg_sqi: 0.6 }, score: 8 },
  { entry: { title: 'Undated', date_str: '', avg_sqi: 0.9 }, score: 10 },
];
const newest = search.applySort(sortScored, 'newest', true);
assert(newest[0].entry.title === 'New', 'newest: most recent first');
assert(newest[2].entry.title === 'Undated', 'newest: undated items last');
const sqiSorted = search.applySort(sortScored, 'sqi', true);
assert(sqiSorted[0].entry.title === 'Undated' && sqiSorted[0].entry.avg_sqi === 0.9, 'sqi: highest quality first');
const relQuery = search.applySort(sortScored, 'relevance', true);
assert(relQuery[0].entry.title === 'Undated' && relQuery[0].score === 10, 'relevance with query: score desc');
const relBrowse = search.applySort(sortScored, 'relevance', false);
assert(relBrowse[0].entry.title === 'Undated', 'relevance browse: SQI desc then date');
assert(relBrowse[1].entry.title === 'Old', 'relevance browse: SQI desc then date (second)');
const sortedCopy = search.applySort(sortScored, 'newest', false);
assert(sortedCopy !== sortScored && sortScored[0].entry.title === 'Old', 'applySort does not mutate input');

/* ── matchesFilters (category facet) ── */

const noFilter = { pillar: [], type: [], difficulty: [], bloom: [], category: [], technology: [] };
const catFilter = { pillar: [], type: [], difficulty: [], bloom: [], category: ['streaming'], technology: [] };
const catEntry = { pillar: 'data-engineering', content_type: 'research', difficulty: '', bloom: '', category: 'streaming', technologies: [] };
const plainEntry = { pillar: 'data-engineering', content_type: 'research', difficulty: '', bloom: '', category: '', technologies: [] };
assert(search.matchesFilters(catEntry, noFilter) === true, 'no filters -> everything matches');
assert(search.matchesFilters(catEntry, catFilter) === true, 'category filter: matching entry passes');
assert(search.matchesFilters({ ...catEntry, category: 'batch-processing' }, catFilter) === false, 'category filter: non-matching entry fails');
assert(search.matchesFilters(plainEntry, catFilter) === false, 'category filter: empty-category entry excluded when active');
assert(search.matchesFilters(plainEntry, noFilter) === true, 'no filter: empty-category entry passes');
const multiCat = { pillar: [], type: [], difficulty: [], bloom: [], category: ['streaming', 'batch-processing'], technology: [] };
assert(search.matchesFilters(catEntry, multiCat) === true, 'category filter: multiple values OR semantics');

console.log('');
console.log('Search discovery tests: ' + passed + ' passed, ' + failed + ' failed');
process.exit(failed ? 1 : 0);
