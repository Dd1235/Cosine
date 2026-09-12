const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const difficulty = require('./difficulty');
const source = fs.readFileSync(`${__dirname}/app.js`, 'utf8');
const similar = source.slice(source.indexOf('async function runSimilar('), source.indexOf('// "Was this useful?"'));
const syncUrl = source.slice(source.indexOf('function syncUrl()'), source.indexOf('function updatePatternPill()'));
const token = source.slice(source.indexOf('function applyDifficultyToken('), source.indexOf('// The suggestions that apply'));

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


function harness() {
  const requests = [], rendered = [], addresses = [];
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
    location: { pathname: '/', search: '', hash: '' }, history: { replaceState: (_a, _b, address) => addresses.push(address) },
    resultsEl: {}, applyMode() {}, hideFeedback() {}, syncDifficultyControls() {}, renderCollectionControls() {},
    setLibPath() {}, setStatus() {}, hideLoadMore() {}, updateLoadMore() {},
    libraryCommand: q => q === ':bookmarks' ? { type: 'bookmarked' } : null,
    difficultyParam: () => 'cf:1200-1800', activeFacets: () => [], orderNote: () => '',
    cosineDifficulty: difficulty, URLSearchParams, AbortController,
    cosineSheets: { connected: () => true, noteText: id => id === 'p1' ? 'private note' : '' },
    renderHitsList: (_el, hits, opts) => rendered.push({ hits, opts }),
    fetch: async url => {
      requests.push(new URL(url, 'http://local'));
      return { ok: true, json: async () => ({ source: { id: 'source', title: 'Source' }, total: 60,
        hits: [{ problem: { id: 'p1' } }, { problem: { id: 'p2' } }], ranker: 'dense' }) };
    },
  });
  vm.runInContext(syncUrl + token + similar, ctx);
  return { ctx, requests, rendered, addresses };
}
(async () => {
  const { ctx, requests, rendered, addresses } = harness();
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
