const assert = require("node:assert/strict");
const fs = require("node:fs");
const {JSDOM} = require("jsdom");
const source = fs.readFileSync(`${__dirname}/app.js`, "utf8");
const difficulty = {named: [{id: "cses-advanced", judge: "cses", label: "Advanced (estimate)", count: 5}],
  rated: [{judge: "codeforces", short: "cf", min: 800, max: 3500, stops: [800, 1500, 1700, 3500]}]};
const settle = async () => { for (let i = 0; i < 6; i++) await new Promise(setImmediate); };

async function main() {
  const dom = new JSDOM(fs.readFileSync(`${__dirname}/index.html`, "utf8"), {url: "http://local/", runScripts: "outside-only"});
  const w = dom.window, doc = w.document;
  w.matchMedia = () => ({matches: false, addEventListener() {}, addListener() {}});
  w.scrollTo = () => {};
  w.HTMLElement.prototype.scrollIntoView = () => {};
  w.fetch = async url => ({ok: true, json: async () => {
    if (url === "/api/auth/me") return {user: {id: "u", email: "test@example.invalid"}};
    if (url === "/api/rankers") return {available: ["bm25", "dense"], default: "bm25", difficulty, googleClientId: "test"};
    if (url === "/api/user-state") return {bookmarked: [], done: []};
    if (url === "/api/collections") return {collections: []};
    if (url === "/api/level") return {suggest: {codeforces: {difficulty: "cf:1500-1700", count: 3, why: "test"}}};
    if (url.startsWith("/api/preferences")) return {};
    return {hits: [], items: [], total: 0};
  }});
  w.eval(fs.readFileSync(`${__dirname}/difficulty.js`, "utf8"));
  w.eval(fs.readFileSync(`${__dirname}/sheets.js`, "utf8") + "\nwindow.cosineSheets = cosineSheets;");
  w.eval(source + `\nwindow.workbenchState = () => ({
    query: currentQuery, platforms: [...activePlatforms], tiers: [...activeTiers], ranges: [...activeRanges],
    collections: [...activeCollections], acceptance: activeAcceptance, pattern: activePattern, ranker: activeRanker,
    aged: libAged, oldest: libOldest, recall: libRecall, notes: libNotes, filter: currentFilter,
    similar: currentSimilar, practice: practiceMode, contest: contestView, compare: compareMode,
    sort: sortDir, sortWindow, offset: currentOffset, user: currentUser, pendingAuth: bootNeedsAuth
  });
  window.seedWorkbench = () => {
    currentUser = {id: 'u'}; currentQuery = ':bookmarks'; input.value = currentQuery;
    activePlatforms.add('codeforces'); activeTiers.add('cses-advanced'); activeRanges.set('codeforces', {min: 1500, max: 1700});
    activeCollections.add('contest'); activeAcceptance = {min: 20, max: 50}; activePattern = 'graph';
    libAged = 90; libOldest = true; libRecall = 'again'; libNotes = 'yes'; currentFilter = 'done';
    currentSimilar = {id: 'p'}; practiceMode = true; contestView = true; compareMode = true;
    sortDir = 'desc'; sortWindow = 100; activeRanker = 'dense'; currentOffset = 40; bootNeedsAuth = true;
  };`);
  await settle();
  const style = doc.createElement("style"); style.textContent = fs.readFileSync(`${__dirname}/styles.css`, "utf8"); doc.head.appendChild(style);
  assert.equal(doc.querySelectorAll("#sheet-btn").length, 1);
  assert.equal(doc.getElementById("cses-level-select"), null, "no persistent settings in search filters");
  w.setLibPath("~/search graphs");
  assert.equal(doc.getElementById("lib-age-row").hidden, true);
  assert.equal(w.getComputedStyle(doc.getElementById("lib-age-row")).display, "none", "CSS honors conditional visibility");
  w.setLibPath("~/bookmarked");
  assert.equal(doc.getElementById("lib-age-row").hidden, false);
  assert.equal(doc.getElementById("lib-sheet").hidden, false);
  w.setLibPath("~/similar graph");
  assert.equal(doc.getElementById("lib-sheet").hidden, true, "no Sheets control in related search");
  w.seedWorkbench();
  doc.getElementById("search-filters").open = true;
  doc.getElementById("reset-search").click();
  await settle();
  const state = JSON.parse(JSON.stringify(w.workbenchState()));
  for (const key of ["platforms", "tiers", "ranges", "collections"]) assert.deepEqual(state[key], [], key);
  for (const key of ["acceptance", "aged", "recall", "notes", "similar", "sort"]) assert.equal(state[key], null, key);
  for (const key of ["oldest", "practice", "contest", "compare", "pendingAuth"]) assert.equal(state[key], false, key);
  assert.equal(state.query, ""); assert.equal(state.pattern, ""); assert.equal(state.ranker, "");
  assert.equal(state.filter, "all"); assert.equal(state.sortWindow, 20); assert.equal(state.offset, 0);
  assert.equal(state.user.id, "u", "reset does not log out or clear account preferences");
  assert.equal(w.location.search, "");
  assert.equal(doc.getElementById("search-filters").open, false);
  assert.equal(doc.getElementById("lib-age-row").hidden, true);
  assert.equal(doc.getElementById("ranker-select").value, "bm25");
  assert.equal(doc.getElementById("filter-summary").textContent, "all judges · any difficulty");
  dom.window.close();
  console.log("workbench full-bundle DOM tests passed (visibility, reset, defaults, account preservation)");
}
main().catch(error => {console.error(error); process.exitCode = 1;});
