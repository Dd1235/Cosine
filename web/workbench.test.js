const assert = require("node:assert/strict");
const fs = require("node:fs");
const {JSDOM} = require("jsdom");
const source = fs.readFileSync(`${__dirname}/app.js`, "utf8");
const difficulty = {named: [{id: "cses-advanced", judge: "cses", label: "Advanced (estimate)", count: 5}],
  rated: [{judge: "codeforces", short: "cf", min: 800, max: 3500, stops: [800, 1500, 1700, 3500]},
    {judge: "atcoder", short: "atc", min: 0, max: 3000, stops: [0, 800, 1000, 3000]}]};
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
    if (url === "/api/level") return {suggest: {codeforces: {difficulty: "cf:1500-1700", count: 3, why: "test"},
      atcoder: {difficulty: "atc:800-1000", count: 2, why: "test"}}};
    if (url.startsWith("/api/preferences")) return {};
    return {hits: [], items: [], total: 0};
  }});
  w.eval(fs.readFileSync(`${__dirname}/difficulty.js`, "utf8"));
  w.eval(fs.readFileSync(`${__dirname}/sheets.js`, "utf8") + "\nwindow.cosineSheets = cosineSheets;");
  w.eval(fs.readFileSync(`${__dirname}/notes-export.js`, "utf8"));
  w.eval(source + `\nwindow.workbenchState = () => ({
    query: currentQuery, platforms: [...activePlatforms], tiers: [...activeTiers], ranges: [...activeRanges],
    collections: [...activeCollections], acceptance: activeAcceptance, pattern: activePattern, ranker: activeRanker,
    aged: libAged, oldest: libOldest, recall: libRecall, notes: libNotes, filter: currentFilter,
    similar: currentSimilar, practice: practiceMode, contest: contestView, compare: compareMode,
    sort: sortDir, sortWindow, offset: currentOffset, user: currentUser, pendingAuth: bootNeedsAuth
  });
  window.seedWorkbench = (view) => {
    currentUser = {id: 'u'}; currentQuery = view === 'library' ? ':bookmarks' : view === 'search' ? 'graphs' : ''; input.value = currentQuery;
    activePlatforms.add('codeforces'); activeTiers.add('cses-advanced'); activeRanges.set('codeforces', {min: 1500, max: 1700});
    activeCollections.add('contest'); activeAcceptance = {min: 20, max: 50}; activePattern = 'graph';
    libAged = 90; libOldest = true; libRecall = 'again'; libNotes = 'yes'; currentFilter = 'done';
    currentSimilar = view === 'similar' ? {id: 'p'} : null; practiceMode = view === 'similar'; contestView = view === 'contest'; compareMode = false;
    sortDir = 'desc'; sortWindow = 100; activeRanker = 'dense'; rankerSelect.value = 'dense'; currentOffset = 40; bootNeedsAuth = false;
    showLabels = true; syncLabelsToggle();
  };`);
  await settle();
  const style = doc.createElement("style"); style.textContent = fs.readFileSync(`${__dirname}/styles.css`, "utf8"); doc.head.appendChild(style);
  const level = doc.getElementById("level-apply");
  assert.equal(doc.querySelectorAll("#level-apply").length, 1);
  assert.ok(level.closest(".filter-actions"), "shortcut is outside conditional judge controls");
  assert.equal(level.disabled, false, "usable without selecting a judge first");
  level.click(); await settle();
  assert.deepEqual([...w.workbenchState().platforms], ["codeforces", "atcoder"]);
  assert.equal(w.workbenchState().ranges.length, 2, "all available native targets applied in one click");
  assert.equal(level.getAttribute("aria-pressed"), "true");
  level.click(); await settle();
  assert.equal(w.workbenchState().ranges.length, 0, "second click clears level ranges");
  assert.equal(level.getAttribute("aria-pressed"), "false");
  doc.getElementById("reset-filters").click(); await settle();
  doc.querySelector('[data-platform="codeforces"]').click(); await settle();
  level.click(); await settle();
  assert.deepEqual([...w.workbenchState().platforms], ["codeforces"], "explicit judge choice is respected");
  assert.equal(w.workbenchState().ranges.length, 1);
  doc.getElementById("reset-filters").click(); await settle();
  assert.equal(level.disabled, false);
  assert.equal(doc.querySelector('a[href="/profile.html#practice-levels"]'), null);
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
  assert.equal(doc.getElementById("reset-search"), null);
  assert.equal(doc.querySelector(".search-toolbar"), null);
  assert.ok(doc.getElementById("reset-filters").closest(".filter-panel"));
  for (const view of ["search", "library", "similar", "contest"]) {
    w.seedWorkbench(view);
    assert.equal(doc.getElementById("labels-toggle").getAttribute("aria-pressed"), "true");
    assert.equal(doc.getElementById("labels-toggle").classList.contains("is-active"), false);
    doc.getElementById("search-filters").open = true;
    doc.getElementById("reset-filters").click();
    await settle();
    const state = JSON.parse(JSON.stringify(w.workbenchState()));
    for (const key of ["platforms", "tiers", "ranges", "collections"]) assert.deepEqual(state[key], [], key);
    for (const key of ["acceptance", "aged", "recall", "notes", "sort"]) assert.equal(state[key], null, key);
    for (const key of ["oldest", "contest", "compare", "pendingAuth"]) assert.equal(state[key], false, key);
    assert.equal(state.query, view === "library" ? ":bookmarks" : view === "search" ? "graphs" : "");
    assert.equal(state.practice, view === "similar");
    assert.deepEqual(state.similar, view === "similar" ? {id: "p"} : null);
    assert.equal(state.pattern, ""); assert.equal(state.ranker, "dense");
    assert.equal(state.filter, "all"); assert.equal(state.sortWindow, 20); assert.equal(state.offset, 0);
    assert.equal(state.user.id, "u", "reset does not log out or clear account preferences");
    const params = new URLSearchParams(w.location.search);
    assert.equal(params.get("ranker"), "dense");
    for (const key of ["platform", "difficulty", "contest", "pattern", "sort", "aged", "order", "recall", "notes", "filter"]) assert.equal(params.has(key), false, key);
    assert.equal(params.get("q") || "", state.query);
    assert.equal(doc.getElementById("search-filters").open, true);
    assert.equal(doc.getElementById("ranker-select").value, "dense");
    assert.equal(doc.getElementById("filter-summary").textContent, "all judges · any difficulty");
    assert.equal(doc.getElementById("notes-export").hidden, false, "the current view can be exported");
  }
  dom.window.close();
  console.log("workbench full-bundle DOM tests passed (visibility, reset, defaults, account preservation)");
}
main().catch(error => {console.error(error); process.exitCode = 1;});
