const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const difficulty = require('./difficulty');
const source = fs.readFileSync(`${__dirname}/app.js`, 'utf8');
const similar = source.slice(source.indexOf('async function runSimilar('), source.indexOf('// "Was this useful?"'));
const syncUrl = source.slice(source.indexOf('function syncUrl({'), source.indexOf('function updatePatternPill()'));
const collectionState = source.slice(source.indexOf('function addCollection('), source.indexOf('function renderCollectionPanel('));
const token = source.slice(source.indexOf('function applyDifficultyToken('), source.indexOf('function levelForSelection('));

assert.equal(difficulty.format({ platform: 'cses', cses_difficulty: { band: 4 } }), 'Advanced · CSES estimate');
assert.equal(difficulty.format({ platform: 'cses', difficulty: 1900 }), '', 'never map a foreign rating to CSES');
assert.equal(difficulty.format({ platform: 'codeforces', difficulty: 1900 }), '1900');
assert.equal(difficulty.value({ platform: 'cses', cses_difficulty: { band: 6 } }), null);
const sheets = fs.readFileSync(`${__dirname}/sheets.js`, 'utf8');
const cellsSource = sheets.slice(sheets.indexOf('function appCells('), sheets.indexOf('// A brand-new row'));
const cellsCtx = vm.createContext({ cosineDifficulty: difficulty });
vm.runInContext(cellsSource, cellsCtx);
assert.equal(cellsCtx.appCells({ problem: { platform: 'cses', cses_difficulty: { band: 4 } } }).difficulty,
  difficulty.format({ platform: 'cses', cses_difficulty: { band: 4 } }), 'cards and Sheets use identical wording');


// A DOM thin enough to answer "what did the empty-similar branch build, and
// what does its reset button do" without pretending to be a browser.
function fakeDom() {
  const made = [];
  const node = () => {
    const n = {
      children: [], listeners: {},
      classList: { add() {}, remove() {}, toggle() {} },
      setAttribute() {},
      appendChild(child) { this.children.push(child); },
      addEventListener(name, fn) { (this.listeners[name] = this.listeners[name] || []).push(fn); },
    };
    made.push(n);
    return n;
  };
  return { made, document: { createElement: node, getElementById: () => null } };
}

function harness({ empty = false } = {}) {
  const requests = [], rendered = [], addresses = [], ops = [];
  const dom = fakeDom();
  const ctx = vm.createContext({
    currentSimilar: null, similarLibrary: null, currentUser: { id: 'u' },
    currentQuery: ':bookmarks', input: { value: ':bookmarks' },
    activeCollections: new Set(['india-prelims']), activePlatforms: new Set(['codeforces']), activePattern: 'graph',
    activeTiers: new Set(), activeRanges: new Map(), activeAcceptance: null,
    libRecall: 'again', libNotes: null, libAged: 30, libOldest: true,
    currentFilter: 'all', filterSelect: {}, rankerSelect: {}, currentOffset: 0, practiceMode: false,
    sortDir: null, sortWindow: 20, TOP_K: 20, similarCorpusSize: 200,
    currentTopScore: 0, currentSearchId: null, currentRankerAnswered: '', compareMode: false,
    currentTotal: 0, lastQueryAt: 0, inFlight: null, activeRanker: '',
    difficultyPayload: { named: [], rated: [] },
    location: { pathname: '/', search: '', hash: '' }, lastAppliedSearch: '',
    history: {
      replaceState: (_a, _b, address) => { addresses.push(address); ops.push(['replace', address]); },
      pushState: (_a, _b, address) => { addresses.push(address); ops.push(['push', address]); },
    },
    collections: [{ id: 'india-prelims', name: 'ICPC India Prelims', count: 5 }],
    document: dom.document,
    resultsEl: { innerHTML: '', appendChild() {} },
    // Beacons are fire-and-forget in the browser and irrelevant here, but
    // addCollection/removeCollection call track() and the vm has no window.
    track() {},
    applyMode() {}, hideFeedback() {}, syncDifficultyControls() {}, renderCollectionControls() {},
    updatePatternPill() {}, syncJudgeControls() {}, reissueCurrentView() {}, runSearch() {},
    // addCollection/removeCollection fire outcome beacons; without this the
    // slice throws a ReferenceError before it reaches a single assertion.
    track() {},
    setLibPath() {}, setStatus() {}, hideLoadMore() {}, updateLoadMore() {},
    libraryCommand: q => q === ':bookmarks' ? { type: 'bookmarked' } : null,
    difficultyParam: () => 'cf:1200-1800', activeFacets: () => [], orderNote: () => '',
    cosineDifficulty: difficulty, URLSearchParams, AbortController,
    cosineSheets: { connected: () => true, hasContent: id => id === 'p1', noteText: id => id === 'p1' ? 'private note' : '' },
    renderHitsList: (_el, hits, opts) => rendered.push({ hits, opts }),
    fetch: async url => {
      requests.push(new URL(url, 'http://local'));
      return { ok: true, json: async () => (empty
        ? { source: { id: 'source', title: 'Source' }, total: 0, hits: [], ranker: 'dense' }
        : { source: { id: 'source', title: 'Source' }, total: 60,
            hits: [{ problem: { id: 'p1' } }, { problem: { id: 'p2' } }], ranker: 'dense' }) };
    },
  });
  vm.runInContext(syncUrl + token + collectionState + similar, ctx);
  return { ctx, requests, rendered, addresses, ops, made: dom.made };
}
(async () => {
  const { ctx, requests, rendered, addresses, ops } = harness();
  ctx.applyDifficultyToken('cses-advanced');
  assert.ok(ctx.activeTiers.has('cses-advanced'));
  await ctx.runSimilar({ id: 'source', title: 'Source' });
  const params = requests[0].searchParams;
  assert.equal(params.get('contest'), 'india-prelims');
  assert.equal(params.get('pattern'), 'graph');
  assert.equal(params.get('library'), 'bookmarked');
  assert.equal(params.get('recall'), 'again');
  assert.equal(params.get('aged'), '30');
  assert.equal(params.get('order'), 'oldest');
  assert.equal(params.get('platform'), 'codeforces');
  assert.equal(params.get('difficulty'), 'cf:1200-1800');
  assert.ok(addresses[0].includes('similar=source'));
  assert.ok(addresses[0].includes('contest=india-prelims'));
  ctx.currentOffset = 20;
  await ctx.runSimilar(ctx.currentSimilar, { append: true });
  assert.equal(requests.at(-1).searchParams.get('offset'), '20');
  assert.equal(rendered.at(-1).opts.append, true);

  ctx.libNotes = 'yes';
  await ctx.runSimilar(ctx.currentSimilar);
  assert.equal(requests.at(-1).searchParams.get('k'), '200');
  assert.equal(requests.at(-1).searchParams.has('notes'), false);
  assert.equal(rendered.at(-1).hits.length, 1);
  assert.equal(ctx.currentTotal, 1);

  await ctx.runSimilar(ctx.currentSimilar, { practice: true });
  const practice = requests.at(-1).searchParams;
  for (const name of ['contest', 'library', 'recall', 'aged', 'order', 'notes']) assert.equal(practice.has(name), false, name);
  assert.equal(practice.get('filter'), 'notdone');
  assert.equal(practice.get('pattern'), 'graph');
  assert.equal(practice.get('platform'), 'codeforces');
  assert.equal(ctx.libNotes, null);
  assert.ok(addresses.at(-1).includes('practice=1'));

  // History: picking a competition is one deliberate act, so it earns an entry
  // and Back undoes exactly it. Typing is not — the debounced box replaces, or
  // "g", "gr", "gra" would bury the page you came from under three entries.
  ctx.currentSimilar = null;
  ctx.practiceMode = false;
  ctx.similarLibrary = null;
  ctx.activeCollections.clear();
  ops.length = 0;
  ctx.addCollection('india-prelims');
  assert.deepEqual(ops.map(o => o[0]), ['push'], 'adding a collection pushes');
  assert.ok(ops[0][1].includes('contest=india-prelims'));
  assert.ok(ctx.activeCollections.has('india-prelims'));

  ops.length = 0;
  ctx.currentQuery = 'graph';
  ctx.syncUrl();
  assert.deepEqual(ops.map(o => o[0]), ['replace'], 'a typed query replaces');
  assert.ok(ops[0][1].includes('q=graph'));

  ops.length = 0;
  ctx.removeCollection('india-prelims');
  assert.deepEqual(ops.map(o => o[0]), ['push'], 'removing one pushes too');
  assert.equal(ctx.activeCollections.size, 0);
  console.log('practice, collection, CSES display and URL tests passed');
})().catch(err => { console.error(err); process.exitCode = 1; });

// setCsesLevelSuggestion / loadLevelSignals: clearing the CSES band must not
// leave an empty levelSuggest behind (it used to read as "already fetched"), and
// /api/level is fetched once per user rather than once per truthy object.
{
  const lvl = source.slice(source.indexOf('function setCsesLevelSuggestion('), source.indexOf('async function loadCsesLevel('));
  const sig = source.slice(source.indexOf('async function loadLevelSignals('), source.indexOf('function activeFacets('));
  const fetches = [];
  const ctx = vm.createContext({
    csesLevel: null, levelSuggest: null, levelSignalsUser: null, currentUser: { id: 'u1' },
    difficultyPayload: { named: [{ id: 'cses-intermediate', count: 7 }] },
    cosineDifficulty: difficulty, syncDifficultyControls() {},
    fetch: async (url) => { fetches.push(url); return { ok: true, json: async () => ({ suggest: { codeforces: { difficulty: 'cf:1500-1700', why: 'x', count: 3 } } }) }; },
  });
  vm.runInContext(lvl + sig, ctx);
  ctx.setCsesLevelSuggestion(3);
  assert.equal(ctx.levelSuggest.cses.difficulty, 'cses-intermediate');
  ctx.setCsesLevelSuggestion(null);
  assert.equal(ctx.levelSuggest, null, 'clearing the band leaves no empty object behind');
  (async () => {
    await ctx.loadLevelSignals(); await ctx.loadLevelSignals();
    assert.equal(fetches.length, 1, 'level signals are fetched once per user');
    assert.ok(ctx.levelSuggest.codeforces);
    ctx.setCsesLevelSuggestion(2); ctx.setCsesLevelSuggestion(null);
    assert.ok(ctx.levelSuggest.codeforces, 'clearing CSES keeps the other judges');
    ctx.levelSignalsUser = null; ctx.currentUser = { id: 'u2' }; ctx.levelSuggest = null;
    await ctx.loadLevelSignals();
    assert.equal(fetches.length, 2, 'a different user fetches again');
    console.log('level suggestion tests passed');
  })();
}

// "Clear filters and search again" on an empty similarity view. It resets the
// state the fetch reads, so anything it misses is a filter you were told was
// gone and that the next request still carries.
(async () => {
  const { ctx, made } = harness({ empty: true });
  ctx.sortDir = 'desc';
  ctx.activeCollections.add('india-prelims');
  ctx.activeTiers.add('lc-hard');
  await ctx.runSimilar({ id: 'source', title: 'Source' });
  const relax = made.find(n => n.textContent === 'clear filters and search again');
  assert.ok(relax, 'the empty view offers a way out');
  relax.listeners.click[0]();
  assert.equal(ctx.sortDir, null, 'difficulty order is a filter and is cleared with them');
  assert.equal(ctx.activeCollections.size, 0);
  assert.equal(ctx.activeTiers.size, 0);
  assert.equal(ctx.activePattern, '');
  console.log('empty similarity reset tests passed');
})().catch(err => { console.error(err); process.exitCode = 1; });
