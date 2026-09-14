// Exercise production sync orchestration with delayed I/O and fake timers.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync(`${__dirname}/app.js`, 'utf8');
const block = source.slice(source.indexOf('async function doSheetSync('), source.indexOf('// One silent attempt'));
function setup(fetchImpl, syncImpl) {
  const timers = [];
  const status = [];
  const ctx = vm.createContext({
    document: { getElementById: () => ({}) },
    currentUser: { id: 'a' }, currentQuery: '', sheetSyncing: false,
    sheetGeneration: 0, sheetDirty: false, sheetSyncTimer: null,
    sheetErrorShown: false, sheetSyncedThisSession: false, sheetResumeFailed: false,
    fetch: fetchImpl, cosineSheets: { connected: () => true, hasToken: () => true, sync: syncImpl },
    setTimeout: (fn) => { timers.push(fn); return timers.length; }, clearTimeout() {},
    syncSheetChip() {}, setStatus: (text) => status.push(text), libraryCommand: () => false,
  });
  vm.runInContext(block, ctx);
  return { ctx, timers, status };
}
(async () => {
  let finish;
  const firstWrite = new Promise(resolve => { finish = resolve; });
  let writes = 0;
  const { ctx, timers } = setup(async () => ({ ok: true, json: async () => ({ items: [] }) }), async () => {
    writes++;
    return writes === 1 ? firstWrite : { total: 1 };
  });
  ctx.markSheetDirty();
  const first = ctx.doSheetSync({ quiet: true });
  await new Promise(setImmediate);
  ctx.markSheetDirty();
  await timers.at(-1)(); // debounce expires while first write is outstanding
  assert.equal(writes, 1);
  finish({ total: 1 });
  await first;
  assert.equal(ctx.sheetDirty, true, 'newer mutation remains dirty');
  await timers.at(-1)();
  await new Promise(setImmediate);
  assert.equal(writes, 2, 'success schedules the mutation missed by the first write');
  assert.equal(ctx.sheetDirty, false);

  let called = false;
  const failed = setup(async () => ({ ok: false, status: 503 }), async () => { called = true; });
  failed.ctx.markSheetDirty();
  await failed.ctx.doSheetSync({ quiet: true });
  assert.equal(called, false, 'HTTP errors never sync an empty library');
  assert.equal(failed.ctx.sheetDirty, true);
  assert.match(failed.status[0], /503/);

  let fetched;
  const response = new Promise(resolve => { fetched = resolve; });
  const account = setup(() => response, async () => { throw new Error('cross-account write'); });
  const inflight = account.ctx.doSheetSync();
  account.ctx.currentUser = { id: 'b' };
  fetched({ ok: true, json: async () => ({ items: [] }) });
  await inflight;
  assert.equal(account.ctx.sheetSyncedThisSession, false);

  // Notes edited during a Google batch write must survive its acknowledgement.
  const sheetSource = fs.readFileSync(`${__dirname}/sheets.js`, 'utf8');
  const notesBlock = sheetSource.slice(sheetSource.indexOf('async function flushNotes()'), sheetSource.indexOf('// ── Notes on a single problem'));
  let acknowledge;
  const notes = vm.createContext({
    pendingNotes: new Map([['p', 'old']]), sheetsUserId: 'a',
    sheetLayout: { user: new Map([['notes', 0]]) }, NOTE_FIELD: 'notes',
    rowByProblem: new Map([['p', { rowIndex: 2 }]]), SHEET_TAB: 'Practice',
    spreadsheetId: 'sheet', colLetter: () => 'A', rememberPending() {},
    gapi: () => new Promise(resolve => { acknowledge = resolve; }),
  });
  vm.runInContext(notesBlock, notes);
  const flushing = notes.flushNotes();
  notes.pendingNotes.set('p', 'new');
  acknowledge({});
  await flushing;
  assert.equal(notes.pendingNotes.get('p'), 'new');
  const flushingAgain = notes.flushNotes();
  acknowledge({});
  await flushingAgain;
  assert.equal(notes.pendingNotes.size, 0);
  // A late Google response cannot populate the next account's row cache.
  const apiBlock = sheetSource.slice(sheetSource.indexOf('async function gapi('), sheetSource.indexOf('// True only while a sync'));
  let responseReady;
  const api = vm.createContext({
    sheetSession: 1, interactiveWindow: false, accessToken: 'local-test-token',
    getToken: async () => 'local-test-token',
    fetch: () => new Promise(resolve => { responseReady = resolve; }),
    googleError: async () => new Error('unexpected HTTP error'),
  });
  vm.runInContext(apiBlock, api);
  const oldRequest = api.gapi('https://sheets.invalid/local-test');
  await new Promise(setImmediate);
  api.sheetSession = 2;
  responseReady({ ok: true, status: 200, json: async () => ({ oldAccount: true }) });
  await assert.rejects(oldRequest, /account changed/);

  console.log('sheet sync race tests passed');
})().catch(err => { console.error(err); process.exitCode = 1; });
