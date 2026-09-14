// applyUrlState / dispatchUrlView / popstate, sliced out of app.js and driven
// in a vm — the same trick web/practice.test.js uses, for the same reason:
// these functions are the whole of the app's navigation model and they need a
// browser for nothing but `location.search`.
//
// What is actually being guarded here is that applyUrlState RESETS. It used to
// run once, at boot, against empty state; popstate calls it again against a
// fully populated app, and anything it forgets to clear survives the
// navigation and keeps filtering results the URL no longer mentions.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

const source = fs.readFileSync(`${__dirname}/app.js`, 'utf8');
const state = source.slice(
  source.indexOf('function applyUrlState('),
  source.indexOf('const bootParams = new URLSearchParams')
);
const token = source.slice(
  source.indexOf('function applyDifficultyToken('),
  source.indexOf('// The suggestions that apply')
);
const popstate = source.slice(
  source.indexOf('window.addEventListener("popstate"'),
  source.indexOf('// Put the caret where typing actually goes.')
);

function harness(search = '') {
  const calls = [];
  let popHandler = null;
  const ctx = vm.createContext({
    // facet state
    activeCollections: new Set(), activePlatforms: new Set(),
    activeTiers: new Set(), activeRanges: new Map(), activeAcceptance: null,
    bootRanges: [], sortDir: null, activePattern: '',
    currentSimilar: null, similarLibrary: null, practiceMode: false,
    collectionSpoilers: false,
    libAged: null, libOldest: false, libRecall: null, libNotes: null,
    currentFilter: 'all', currentQuery: '', currentTotal: 0, currentOffset: 0,
    bootNeedsAuth: false, lastAppliedSearch: search,
    // things applyUrlState is not allowed to touch
    activeRanker: 'dense', currentUser: { id: 'u' },
    // environment
    location: { pathname: '/', search, hash: '' },
    input: { value: 'stale' }, filterSelect: { value: 'done' },
    resultsEl: { innerHTML: 'stale', classList: { toggle() {} } },
    difficultyPayload: { named: [], rated: [{ short: 'cf', judge: 'codeforces' }] },
    PLATFORM_LABELS: { leetcode: ['lc'], codeforces: ['cf'], cses: ['cses'] },
    libraryCommand: q => (q === ':bookmarks' ? { type: 'bookmarked' } : null),
    URLSearchParams, Number,
    window: { addEventListener: (name, fn) => { if (name === 'popstate') popHandler = fn; } },
    runSimilar: p => calls.push(['similar', p.id]),
    runSearch: q => calls.push(['search', q]),
    applyPatternFilter: p => calls.push(['pattern', p]),
    syncJudgeControls: () => calls.push(['judges']),
    updatePatternPill: () => calls.push(['pill']),
    renderCollectionControls: () => calls.push(['collections']),
    hideLoadMore() {}, hideFeedback() {}, setStatus: t => calls.push(['status', t]),
  });
  vm.runInContext(token + state + popstate, ctx);
  const apply = search => {
    ctx.location.search = search;
    ctx.applyUrlState(new URLSearchParams(search));
  };
  return { ctx, calls, apply, pop: () => popHandler() };
}

// --- a second apply clears everything the first one set ----------------------
{
  const { ctx, apply } = harness();
  apply('?q=graph&contest=icpc-world-finals-2024&platform=codeforces,cses'
    + '&difficulty=lc-hard,cf:1200-1800&sort=difficulty-desc&pattern=binary-search'
    + '&filter=notdone&aged=30&order=oldest&recall=again&notes=yes');
  assert.deepEqual([...ctx.activeCollections], ['icpc-world-finals-2024']);
  assert.deepEqual([...ctx.activePlatforms].sort(), ['codeforces', 'cses']);
  assert.deepEqual([...ctx.activeTiers], ['lc-hard']);
  // JSON rather than deepEqual: vm objects are from another realm, so their
  // prototypes never compare strictly equal.
  assert.equal(JSON.stringify([...ctx.activeRanges.entries()]),
    JSON.stringify([['codeforces', { min: 1200, max: 1800 }]]));
  assert.equal(ctx.sortDir, 'desc');
  assert.equal(ctx.activePattern, 'binary-search');
  assert.equal(ctx.currentFilter, 'notdone');
  assert.equal(ctx.filterSelect.value, 'notdone');
  assert.equal(ctx.libAged, 30);
  assert.equal(ctx.libOldest, true);
  assert.equal(ctx.libRecall, 'again');
  assert.equal(ctx.libNotes, 'yes');
  assert.equal(ctx.input.value, 'graph');

  ctx.collectionSpoilers = true;
  apply('?q=trees');
  assert.equal(ctx.activeCollections.size, 0, 'collections');
  assert.equal(ctx.activePlatforms.size, 0, 'judges');
  assert.equal(ctx.activeTiers.size, 0, 'tiers');
  assert.equal(ctx.activeRanges.size, 0, 'ranges');
  assert.equal(ctx.activeAcceptance, null, 'acceptance');
  assert.equal(ctx.sortDir, null, 'sort');
  assert.equal(ctx.activePattern, '', 'pattern');
  assert.equal(ctx.currentSimilar, null, 'similar');
  assert.equal(ctx.similarLibrary, null, 'similar library');
  assert.equal(ctx.practiceMode, false, 'practice');
  assert.equal(ctx.collectionSpoilers, false, 'spoilers');
  assert.equal(ctx.libAged, null, 'aged');
  assert.equal(ctx.libOldest, false, 'oldest');
  assert.equal(ctx.libRecall, null, 'recall');
  assert.equal(ctx.libNotes, null, 'notes');
  assert.equal(ctx.currentFilter, 'all', 'filter');
  assert.equal(ctx.filterSelect.value, 'all', 'the filter control follows the filter');
  assert.equal(ctx.input.value, 'trees');
  // Not part of the view, and not reset with it.
  assert.equal(ctx.activeRanker, 'dense', 'the ranker is a preference, not a view');
  assert.equal(ctx.currentUser.id, 'u');
}

// --- practice=1 and contest= are a contradiction; practice wins --------------
{
  const { ctx, apply } = harness();
  apply('?similar=codeforces-1-a&practice=1&contest=icpc-world-finals-2024');
  assert.equal(ctx.practiceMode, true);
  assert.equal(ctx.currentSimilar.id, 'codeforces-1-a');
  assert.equal(ctx.activeCollections.size, 0,
    'practice means "anything but the source contest" — the pair returns 0 from the server');
  // Without practice the same link keeps its collection.
  apply('?similar=codeforces-1-a&contest=icpc-world-finals-2024');
  assert.equal(ctx.practiceMode, false);
  assert.deepEqual([...ctx.activeCollections], ['icpc-world-finals-2024']);
}

// --- dispatch picks the view the state describes -----------------------------
{
  const { ctx, calls, apply } = harness();
  apply('?similar=codeforces-1-a');
  ctx.dispatchUrlView();
  assert.deepEqual(calls.at(-1), ['similar', 'codeforces-1-a']);
  assert.equal(ctx.input.value, '', 'a similarity view owns the search box');

  apply('?pattern=binary-search');
  ctx.dispatchUrlView();
  assert.deepEqual(calls.at(-1), ['pattern', 'binary-search']);

  apply('?contest=icpc-world-finals-2024');
  ctx.dispatchUrlView();
  assert.deepEqual(calls.at(-1), ['search', ''], 'a collection with no query is a browse');

  ctx.currentQuery = 'graph';
  ctx.resultsEl.innerHTML = '<li>old</li>';
  apply('');
  ctx.dispatchUrlView();
  assert.deepEqual(calls.at(-1), ['status', '']);
  assert.equal(ctx.currentQuery, '');
  assert.equal(ctx.resultsEl.innerHTML, '', 'Back to a bare URL clears the results it no longer describes');
}

// --- popstate ignores a hash-only move ---------------------------------------
{
  const { ctx, calls, pop } = harness('?q=graph');
  ctx.lastAppliedSearch = '?q=graph';
  ctx.location.hash = '#filters';
  ctx.input.value = 'graph';
  pop();
  assert.deepEqual(calls, [], 'an in-page anchor is not a navigation');

  ctx.location.search = '?q=graph&contest=icpc-world-finals-2024';
  pop();
  assert.deepEqual(calls.map(c => c[0]), ['judges', 'pill', 'collections', 'search'],
    'a real navigation repaints the controls before it re-issues the view');
  assert.deepEqual([...ctx.activeCollections], ['icpc-world-finals-2024']);
  assert.equal(ctx.lastAppliedSearch, '?q=graph&contest=icpc-world-finals-2024');
}

console.log('url state, popstate and view dispatch tests passed');
