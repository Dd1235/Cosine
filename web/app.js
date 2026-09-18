const input = document.getElementById("search-input");
const form = document.getElementById("search-form");
const resultsEl = document.getElementById("results");
const statusEl = document.getElementById("status");
const loadMoreEl = document.getElementById("load-more");
const filterSelect = document.getElementById("filter-select");
const filterWrap = document.getElementById("filter-wrap");
const rankerSelect = document.getElementById("ranker-select");
const authWidget = document.getElementById("auth-widget");
const authEmailEl = document.getElementById("auth-email");
const logoutBtn = document.getElementById("logout-btn");
const libBar = document.getElementById("lib-bar");
const libPathEl = document.getElementById("lib-path");
const libCountBookmarks = document.getElementById("lib-count-bookmarks");
const libCountDone = document.getElementById("lib-count-done");
// Command chips only. This used to be a bare `.lib-chips .lib-chip` catch-all
// whose handler runs `runSearch(chip.dataset.cmd || "")` — so any chip added to
// the bar that is not a command silently cleared the results on click. The age
// chips were caught by it once; the labels switch lives in the same bar and
// would be caught the same way.
const libChips = libBar.querySelectorAll(".lib-chips .lib-chip[data-cmd]");
const libBackChip = libBar.querySelector(".lib-chip-back");
const libAgeRow = document.getElementById("lib-age-row");
// Revision filters: "marked N+ days ago" and oldest-first. Library-only state,
// deliberately separate from the search filters — they mean nothing there.
let libAged = null;
let libOldest = false;
let libRecall = null;   // "again" | "hard" | "none" (unrated) | null (any)
let libNotes = null;    // "yes" | "no" | null — whether you wrote a note
let googleClientId = null;       // from /api/rankers; sheet feature hidden while null
let sheetSyncedThisSession = false;
let sheetSyncing = false;    // one write at a time; the sync sends everything
let sheetGeneration = 0;    // increments for every local mutation
let sheetDirty = false;      // something changed that the sheet hasn't got
let sheetSyncTimer = null;
let sheetErrorShown = false; // a background failure is said once, not forever

// :help works for everyone, signed in or not. Parsed by helpQuery() below,
// which also takes a section name — this set is only the "is it a command"
// check for the unknown-command hint.
const HELP_COMMANDS = new Set([":help", ":h"]);

// Comparing rankers is a thing you do while tuning the engine, not while
// looking for a problem. It used to be a checkbox sitting above every search;
// as a command it costs nothing until you ask for it.
const COMPARE_COMMANDS = [":compare ", ":cmp "];
function compareQuery(q) {
  const lower = q.toLowerCase();
  for (const cmd of COMPARE_COMMANDS) {
    if (lower.startsWith(cmd)) return q.slice(cmd.length).trim();
  }
  return lower.trim() === ":compare" || lower.trim() === ":cmp" ? "" : null;
}

// Shell-style library commands: typing one of these in the search box bypasses
// BM25 and lists the user's saved problems.
const LIBRARY_COMMANDS = {
  ":bookmarks": "bookmarked",
  ":b": "bookmarked",
  ":done": "done",
  ":d": "done",
  ":all": "all",
  ":library": "all",
  ":lib": "all",
  "ls bookmarks": "bookmarked",
  "ls done": "done",
};

// A library view, plus anything typed after it. `:done graph` is `:done`
// filtered to graph — the command used to be an exact map lookup, which meant
// a single extra word dropped you out of your saved problems and into a corpus
// search, exactly when your library got big enough to need searching.
//
// Every "am I in a library view?" check goes through this. There were nine of
// them doing their own `LIBRARY_COMMANDS[q.toLowerCase()]`, and leaving any one
// behind means that one stops recognising `:done graph` as the library.
function libraryCommand(query) {
  const q = (query || "").trim();
  if (!q) return null;
  const lower = q.toLowerCase();
  // Longest key first: "ls bookmarks" has to win over a hypothetical "ls".
  for (const key of LIBRARY_KEYS) {
    if (lower === key) return { type: LIBRARY_COMMANDS[key], q: "" };
    if (lower.startsWith(`${key} `)) {
      return { type: LIBRARY_COMMANDS[key], q: q.slice(key.length).trim() };
    }
  }
  return null;
}
const LIBRARY_KEYS = Object.keys(LIBRARY_COMMANDS).sort((a, b) => b.length - a.length);

const compareEl = document.getElementById("compare-results");
const judgeRow = document.getElementById("judge-row");
const difficultyRow = document.getElementById("difficulty-row");
const judgeClearBtn = document.getElementById("judge-clear");
const latencySummaryEl = document.getElementById("latency-summary");
// The compare view is a fixed pair — renderCompare's delta badges are pairwise.
// Other registered rankers stay reachable via /api/compare?rankers=….
const COMPARE_RANKERS = ["bm25", "dense"];

const DEBOUNCE_MS = 200;
// How long a search may take before we admit to it. Under this, the answer
// lands first and the user never sees a "searching" flash; over it (a sleeping
// free-tier instance takes ~a minute to wake) they get told what's happening.
const SEARCHING_AFTER_MS = 400;
const TOP_K = 20;
let debounceTimer = null;
let lastQueryAt = 0;
let typeTimer = null;
let searchingTimer = null;
let inFlight = null; // aborts the request a newer keystroke just superseded
let currentQuery = "";
let currentOffset = 0;
let currentTotal = 0;
let currentTopScore = 0;
let currentUser = null;
// Read from the DOM, not assumed: browsers can restore a <select> across a
// soft reload, and a hardcoded "all" here would silently disagree with it.
let currentFilter = filterSelect.value || "all";
let activePattern = "";
const activeCollections = new Set();
let collections = [];
let currentSimilar = null;
let similarLibrary = null;
let practiceMode = false;
// The contest page: one collection, listed as the contest it was, including
// the problems no statement could be indexed for. It is a view over exactly
// one collection, so anything that stops that being true leaves it.
let contestView = false;
let similarCorpusSize = 20000;
let csesLevel = null;
let csesLevelSaving = false;
// Technique labels are the answer. Every forum agrees that reading "binary
// search on the answer" before you attempt a problem is the spoiler, which is
// why Codeforces ships "hide tags" as an account setting — so they are hidden
// by default and the choice is remembered per user. Difficulty is NOT hidden:
// it is how you pick something to attempt, not how you solve it.
let showLabels = false;
let showLabelsSaving = false;
const revealedCards = new Set(); // problem ids opened by click, this session only
const activePlatforms = new Set(); // empty = every judge
let difficultyPayload = { named: [], rated: [], acceptance: null }; // controls, from /api/rankers
const bootRanges = []; // ?difficulty= ranges parked until the payload names their judge
let sortDir = null;    // null | "asc" | "desc" — difficulty order, one judge only
let sortWindow = 20;   // how many relevance-ranked results get reordered
let activeRanker = ""; // "" = server default (bm25); set by the picker or ?ranker=
let compareMode = false;  // entered with :compare, left by any other query
let bootNeedsAuth = false; // restored state that only means something signed in
let currentSearchId = null; // ties outcome beacons to the search that produced them
let currentRankerAnswered = "";

// Outcome beacon: fire-and-forget, survives page navigation via sendBeacon.
function track(type, props = {}) {
  const body = JSON.stringify({ type, props });
  try {
    if (navigator.sendBeacon) {
      navigator.sendBeacon("/api/track", new Blob([body], { type: "application/json" }));
      return;
    }
  } catch (_e) {}
  fetch("/api/track", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body,
    keepalive: true,
  }).catch(() => {});
}

const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

form.addEventListener("submit", (e) => {
  e.preventDefault();
  runSearch(input.value, { append: false });
});

input.addEventListener("input", () => {
  currentSimilar = null;
  similarLibrary = null;
  practiceMode = false;
  contestView = false;
  clearTimeout(debounceTimer);
  // Typing a new question ends the drill-down that produced the pattern.
  //
  // Judges and patterns look like the same kind of filter and aren't. A judge
  // is a standing preference over ~500 problems, so carrying it into a new
  // query always leaves you something: across 5 queries x 4 judges, the
  // emptiest cell was still 14 results. A pattern is a drill-down into the
  // results you were just reading, and the median one covers a single problem
  // — 9 of 25 query x pattern pairs return nothing at all. Keeping it turns
  // the next search into a dead end you have to notice and undo.
  //
  // Clearing the box is different and still keeps it: that's browsing the
  // label, not asking a new question.
  if (activePattern && input.value.trim()) {
    activePattern = "";
    updatePatternPill();
  }
  debounceTimer = setTimeout(() => runSearch(input.value, { append: false }), DEBOUNCE_MS);
});

loadMoreEl.addEventListener("click", () => {
  if (!currentQuery && !currentSimilar && !activePattern && !activePlatforms.size && !activeCollections.size) return;
  currentOffset += TOP_K;
  track("load_more", { searchId: currentSearchId, offset: currentOffset, ranker: currentRankerAnswered });
  runSearch(currentQuery, { append: true });
});

filterSelect.addEventListener("change", () => {
  currentFilter = filterSelect.value;
  currentOffset = 0;
  reissueCurrentView();
});



// Ranker picker. Plain word first (a newcomer picks by meaning), technical
// name second (this audience likes seeing it). tfidf and bm25-grpc are
// deliberately not offered — they're bench/debug rankers, still reachable
// with ?ranker= and on /debug.html.
const RANKER_LABELS = {
  bm25: "keyword · bm25",
  dense: "meaning · dense",
  hybrid: "both · hybrid",
  tfidf: "keyword · tfidf",
  "bm25-grpc": "keyword · go",
};
// On a phone the algorithm name is what breaks the layout: at the 16px the
// iOS zoom fix mandates, plus the caret padding, "meaning · dense" pushes the
// submit button onto a third row. The mode is the part that matters to the
// person choosing; the algorithm is still in :help and the status line.
const RANKER_LABELS_SHORT = {
  bm25: "keyword",
  dense: "meaning",
  hybrid: "both",
  tfidf: "keyword",
  "bm25-grpc": "keyword",
};
const NARROW = typeof matchMedia === "function" ? matchMedia("(max-width: 720px)") : null;
const rankerLabel = (name) =>
  (NARROW && NARROW.matches ? RANKER_LABELS_SHORT[name] : RANKER_LABELS[name]) || name;
let rankerRefreshTimer = null;

// hybrid is no longer registered server-side; the label stays in RANKER_LABELS
// so an old ?ranker=hybrid link still renders a sensible status line.
const PICKER_RANKERS = ["bm25", "dense"];

if (NARROW) {
  const relabel = () => {
    for (const opt of rankerSelect.options) opt.textContent = rankerLabel(opt.value);
  };
  if (NARROW.addEventListener) NARROW.addEventListener("change", relabel);
  else if (NARROW.addListener) NARROW.addListener(relabel); // older WebKit
}

async function populateRankerSelect() {
  let data;
  try {
    const res = await fetch("/api/rankers");
    data = await res.json();
  } catch (_e) {
    return; // keep the static bm25 option
  }
  rankerSelect.innerHTML = "";
  for (const name of (data.available || []).filter((r) => PICKER_RANKERS.includes(r))) {
    const opt = document.createElement("option");
    opt.value = name;
    opt.textContent = rankerLabel(name);
    rankerSelect.appendChild(opt);
  }
  difficultyPayload = data.difficulty || { named: [], rated: [], acceptance: null };
  googleClientId = data.googleClientId || null;
  maybeInitSheets();
  // A range in the URL names a judge by its short form ("cf"), which only the
  // payload can resolve — so it is applied here rather than at boot.
  for (const [, short, lo, hi] of bootRanges.splice(0)) {
    const meta = (difficultyPayload.rated || []).find((r) => r.short === short);
    if (meta) activeRanges.set(meta.judge, { min: Number(lo), max: Number(hi) });
  }
  syncDifficultyControls();
  if (data.corpusSize) {
    similarCorpusSize = data.corpusSize;
    const el = document.getElementById("corpus-size");
    if (el) el.textContent = data.corpusSize.toLocaleString();
  }
  rankerSelect.value = activeRanker || data.default || "bm25";
  if (!rankerSelect.value) rankerSelect.value = data.default || "bm25";
  clearTimeout(rankerRefreshTimer);
  rankerRefreshTimer = data.initializing
    ? setTimeout(populateRankerSelect, 1000)
    : null;
}

rankerSelect.addEventListener("change", () => {
  track("ranker_changed", { from: activeRanker || "bm25", to: rankerSelect.value });
  activeRanker = rankerSelect.value;
  currentOffset = 0;
  if (currentQuery) runSearch(currentQuery, { append: false });
});

// Clicking a library chip is the same as typing its command. Empty cmd means
// "leave library mode" — clears the input, returns to bm25 search.
libChips.forEach((chip) => {
  chip.addEventListener("click", () => {
    const cmd = chip.dataset.cmd || "";
    input.value = cmd;
    input.focus();
    if (cmd) runSearch(cmd, { append: false });
    else { currentSimilar = null; similarLibrary = null; practiceMode = false; runSearch("", { append: false }); }
  });
});

const sheetBtnEl = document.getElementById("sheet-btn");
if (sheetBtnEl) sheetBtnEl.addEventListener("click", () => { doSheetSync(); });

// The age chips and oldest-first re-issue whatever library view is open.
if (libAgeRow) {
  libAgeRow.querySelectorAll(".lib-age").forEach((chip) => {
    chip.addEventListener("click", () => {
      libAged = chip.dataset.aged ? Number(chip.dataset.aged) : null;
      track("library_aged", { days: libAged || 0 });
      syncUrl();
      reissueCurrentView();
    });
  });
  const oldest = document.getElementById("lib-oldest");
  if (oldest) oldest.addEventListener("click", () => {
    libOldest = !libOldest;
    track("library_order", { oldest: libOldest });
    syncUrl();
    reissueCurrentView();
  });
  const recallSel = document.getElementById("lib-recall");
  if (recallSel) recallSel.addEventListener("change", () => {
    libRecall = recallSel.value || null;
    track("library_recall", { value: libRecall || "any" });
    syncUrl();
    reissueCurrentView();
  });
  const notesSel = document.getElementById("lib-notes");
  if (notesSel) notesSel.addEventListener("change", () => {
    libNotes = notesSel.value || null;
    track("library_notes", { value: libNotes || "any" });
    syncUrl();
    reissueCurrentView();
  });
  const pickBtn = document.getElementById("lib-pick");
  if (pickBtn) pickBtn.addEventListener("click", pickOne);
}

// Tab inside the search input cycles through library commands when the user is
// signed in — picks up where they are in the LIBRARY_COMMANDS list.
const TAB_CYCLE = [":all", ":bookmarks", ":done"];
input.addEventListener("keydown", (e) => {
  if (e.key !== "Tab" || e.shiftKey || !currentUser) return;
  const cur = input.value.trim().toLowerCase();
  // Only cycle from an empty box or from a library command. With a real query
  // typed, Tab does its native job (move focus) instead of eating the query.
  if (cur && !TAB_CYCLE.includes(cur)) return;
  e.preventDefault();
  const idx = TAB_CYCLE.indexOf(cur);
  const next = TAB_CYCLE[(idx + 1) % TAB_CYCLE.length];
  input.value = next;
  runSearch(next, { append: false });
});

logoutBtn.addEventListener("click", async () => {
  try { await fetch("/api/auth/logout", { method: "POST" }); } catch (_e) {}
  // The profile page caches its whole response — handles included — under this
  // key so revisits paint instantly. It used to be cleared only when
  // /profile.html next loaded while signed out, so logging out from here left
  // someone's linked usernames sitting in localStorage on a shared machine.
  // Duplicated rather than imported: these two pages share no module.
  try { localStorage.removeItem("algolens_profile_v1"); } catch (_e) {}
  // Same shared-machine reasoning for the sheet pointer; the token itself was
  // never persisted, so dropping the in-memory state is the whole cleanup.
  if (typeof cosineSheets !== "undefined") cosineSheets.clearLocal({ signOut: true });
  sheetSyncedThisSession = false;
  currentUser = null;
  levelSuggest = null;
  levelSignalsUser = null;
  currentSimilar = null;
  similarLibrary = null;
  practiceMode = false;
  clearTimeout(sheetSyncTimer);
  sheetDirty = false;
  loadCsesLevel();
  // Back to whatever this browser remembers. No re-issue: the results are torn
  // down a few lines below anyway, and a re-render here would repaint the view
  // we are in the middle of clearing.
  revealedCards.clear();
  loadShowLabels({ reissue: false });
  applyAuthState();
  clearPatternFilter({ reissue: false });
  // Clear results and the input — old results were rendered with bookmark
  // buttons that no longer apply, and we want anon UX from this point.
  input.value = "";
  currentQuery = "";
  resultsEl.innerHTML = "";
  hideLoadMore();
  // The URL still carried similar=/practice= from the view we just tore down,
  // and the collection chips still claimed a filter nothing is applying.
  // Collections themselves are kept, for the same reason judges are: they are
  // a standing preference, not account state.
  renderCollectionControls();
  syncUrl();
  setStatus("logged out");
});

// Sheets needs the client id (from /api/rankers) AND the signed-in user id
// (from /auth/me); whichever resolves second completes the init.
function maybeInitSheets() {
  if (typeof cosineSheets === "undefined") return;
  cosineSheets.init({
    clientId: googleClientId,
    userId: currentUser && currentUser.id,
    onChange: syncSheetChip,
  });
  syncSheetChip();
  if (currentUser && cosineSheets.connected()) resumeSheet();
}

function syncSheetChip() {
  const wrap = document.getElementById("lib-sheet");
  if (!wrap) return;
  const usable = typeof cosineSheets !== "undefined" && cosineSheets.available();
  wrap.hidden = !usable;
  if (!usable) return;
  const btn = document.getElementById("sheet-btn");
  const open = document.getElementById("sheet-open");
  const connected = cosineSheets.connected();
  // The count is the nudge: unwritten notes are the one thing here that lives
  // in a single browser, and the button that fixes that should say so.
  const pending = cosineSheets.pendingCount();
  btn.textContent = connected
    ? (pending ? `sync sheet (${pending})` : "sync sheet")
    : "connect sheet";
  btn.title = pending
    ? `${pending} note${pending > 1 ? "s" : ""} written here and not yet in your sheet`
    : "notes live in your own Google Sheet — nothing is stored on this server";
  open.hidden = !connected;
  if (connected) open.href = cosineSheets.url();
}

// Connect on first use, then sync. A sync you PRESSED says what it did; one
// that ran on its own stays out of the way, because a status line announcing
// a background write every few seconds is just noise about something that
// worked.
async function doSheetSync({ quiet = false } = {}) {
  if (sheetSyncing) return;
  const btn = document.getElementById("sheet-btn");
  sheetSyncing = true;
  const generation = sheetGeneration;
  const userId = currentUser && currentUser.id;
  let succeeded = false;
  if (btn) btn.disabled = true;
  try {
    if (!cosineSheets.connected()) await cosineSheets.connect();
    sheetResumeFailed = false;   // a press is a fresh start for the silent path
    sheetErrorShown = false;
    const res = await fetch("/api/library?type=all");
    if (!res.ok) throw new Error(`library fetch failed (${res.status})`);
    const data = await res.json();
    if (!currentUser || currentUser.id !== userId) return;
    if (!Array.isArray(data.items)) throw new Error("invalid library response");
    const out = await cosineSheets.sync(data.items || [], { interactive: !quiet });
    if (!currentUser || currentUser.id !== userId) return;
    succeeded = true;
    sheetSyncedThisSession = true;
    sheetDirty = sheetGeneration !== generation;
    if (!quiet) {
      // A tidy-up that failed is worth saying even though the sync worked —
      // otherwise the columns silently stay wrong and nobody knows why.
      setStatus(out.layoutError
        ? `sheet: ${out.total} rows synced · layout not tidied (${out.layoutError})`
        : `sheet: ${out.total} rows · ${out.added} added · ${out.updated} updated`);
    }
    // Notes may have arrived from the sheet; a library view should show them.
    if (currentUser && libraryCommand(currentQuery)) reissueCurrentView();
  } catch (err) {
    // A failure is worth saying once. Repeating it on every background sync
    // would turn one broken grant into a status line that never stops
    // complaining about something the user isn't doing.
    if (!quiet || !sheetErrorShown) setStatus(`sheet: ${err.message || "sync failed"}`);
    if (quiet) sheetErrorShown = true;
  } finally {
    sheetSyncing = false;
    if (btn) btn.disabled = false;
    syncSheetChip();
    // A debounce may have fired while this write was in flight. Requeue it
    // after success, but do not repeatedly hammer a failed grant or endpoint.
    if (succeeded && sheetDirty) scheduleSheetSync();
  }
}

// Every change is a change the sheet should have. Debounced, because ticking
// four problems done in ten seconds is one write, not four — and coalescing
// them costs nothing since the sync always sends the whole library anyway.
const SHEET_SYNC_DELAY = 4000;
function markSheetDirty() {
  sheetGeneration += 1;
  sheetDirty = true;
  scheduleSheetSync();
}
function scheduleSheetSync() {
  if (typeof cosineSheets === "undefined" || !cosineSheets.connected()) return;
  clearTimeout(sheetSyncTimer);
  sheetSyncTimer = setTimeout(async () => {
    sheetSyncTimer = null;
    if (!sheetDirty || sheetSyncing) return;
    // A token lasts about an hour, so a long session runs out of one — ask
    // for another the same silent way rather than going quiet until the next
    // reload. Silent only: a background path must never be the thing that
    // puts a Google dialog on screen.
    if (!cosineSheets.hasToken() && !(await tryResume())) return;
    doSheetSync({ quiet: true });
  }, SHEET_SYNC_DELAY);
}

// One silent attempt at a time, and none at all once one has failed — a
// revoked grant would otherwise be retried on every click for the rest of the
// session. Pressing `sync sheet` is the way back, and it clears this.
let sheetResumeTried = false;
let sheetResumeFailed = false;
async function tryResume() {
  if (sheetResumeFailed || sheetResumeTried) return cosineSheets.hasToken();
  sheetResumeTried = true;
  const ok = await cosineSheets.resume();
  sheetResumeTried = false;
  sheetResumeFailed = !ok;
  return ok;
}

// After a reload there is no token — it is never stored — so ask Google for
// one silently. If that works the sheet just keeps up on its own for the rest
// of the session; if it doesn't, nothing happened and the button still works.
async function resumeSheet() {
  if (typeof cosineSheets === "undefined" || !cosineSheets.connected()) return;
  if (!(await tryResume())) return;
  syncSheetChip();
  if (!sheetSyncedThisSession) doSheetSync({ quiet: true });
}

async function bootstrapAuth() {
  try {
    const res = await fetch("/api/auth/me");
    if (res.ok) {
      const data = await res.json();
      currentUser = data.user || null;
    }
  } catch (_e) {}
  applyAuthState();
  // The boot search deliberately fires before this resolves — waiting on
  // /auth/me would add a round trip to every deep link. Two pieces of restored
  // state need a user though: the done filter, and a library command like
  // :bookmarks (which would otherwise be searched as a literal string). Those
  // re-issue once here instead of being silently dropped.
  const wasPending = bootNeedsAuth;
  bootNeedsAuth = false;
  if (wasPending && currentUser) reissueCurrentView();
  loadLevelSignals();
  loadCsesLevel();
  loadShowLabels();
  maybeInitSheets();
}

function applyAuthState() {
  const anon = authWidget.querySelector("[data-anon]");
  const signed = authWidget.querySelector("[data-signed]");
  if (currentUser) {
    anon.hidden = true;
    signed.hidden = false;
    // Local part only — you know your own domain, and the full address is
    // what pushes the nav onto a second row (content caps at 720px).
    authEmailEl.textContent = String(currentUser.email).split("@")[0];
    authEmailEl.title = currentUser.email;
    filterWrap.hidden = false;
    libBar.hidden = false;
    libCountBookmarks.hidden = false;
    libCountDone.hidden = false;
    refreshLibraryCounts();
    setLibPath("~");
  } else {
    anon.hidden = false;
    signed.hidden = true;
    filterWrap.hidden = true;
    filterSelect.value = "all";
    currentFilter = "all";
    // The bar and its command chips stay visible signed out. They are the only
    // place these commands are advertised now the tagline is gone, and a
    // feature nobody can see is a feature nobody uses.
    libBar.hidden = false;
    libCountBookmarks.hidden = true;
    libCountDone.hidden = true;
  }
}

async function refreshLibraryCounts() {
  try {
    const res = await fetch("/api/user-state");
    if (!res.ok) return;
    const data = await res.json();
    libCountBookmarks.textContent = (data.bookmarked || []).length;
    libCountDone.textContent = (data.done || []).length;
  } catch (_e) {}
}

function setLibPath(path) {
  libPathEl.textContent = path;
  if (libBackChip) libBackChip.hidden = path === "~";
  // The age row exists only where timestamps do — the three library views.
  // `path === "~"` was the wrong test: a search sets the path to `~/search
  // "..."`, so the chips showed there too, where clicking one is a no-op
  // (the filter resets the moment a non-library view re-issues).
  if (libAgeRow) {
    // A practice list already excludes everything done, so the age chips there
    // could only ever empty it.
    const inLibrary = /^~\/(bookmarked|done|all)\b/.test(path) || (!!currentSimilar && !practiceMode);
    libAgeRow.hidden = !inLibrary || !currentUser;
    libAgeRow.querySelectorAll(".lib-age").forEach((c) => {
      c.classList.toggle("is-active", String(libAged ?? "") === c.dataset.aged);
    });
    const oldest = document.getElementById("lib-oldest");
    if (oldest) oldest.classList.toggle("is-active", libOldest);
    const recallSelect = document.getElementById("lib-recall");
    if (recallSelect) recallSelect.value = libRecall || "";
    // The notes filter needs a sheet to know the answer from. Without one it
    // would silently mean "nothing", which is worse than not being offered.
    const knowsNotes = typeof cosineSheets !== "undefined" && cosineSheets.connected();
    for (const id of ["lib-notes", "lib-notes-label"]) {
      const el = document.getElementById(id);
      if (el) el.hidden = !knowsNotes;
    }
    const notesSelect = document.getElementById("lib-notes");
    if (notesSelect) notesSelect.value = libNotes || "";
  }
  // Highlight the matching chip so the bar reads like a state indicator.
  libChips.forEach((c) => {
    const active =
      (path === "~/bookmarked" && c.dataset.cmd === ":bookmarks") ||
      (path === "~/done" && c.dataset.cmd === ":done") ||
      (path === "~/all" && c.dataset.cmd === ":all");
    c.classList.toggle("is-active", active);
  });
}

bootstrapAuth();

function collectionParam() {
  return activeCollections.size ? `&contest=${encodeURIComponent([...activeCollections].join(','))}` : '';
}

function safeResourceUrl(value) {
  try {
    const url = new URL(value);
    return /^https?:$/.test(url.protocol) ? url.href : '';
  } catch (_err) { return ''; }
}

// Collections are a facet, so their controls live where the other facets do:
// one chip per active collection in the judge row, and a "+ competition"
// button that opens a listbox of the rest. The button only exists once
// /api/collections has answered with something you could still add, so the row
// looks exactly as it did before when there is nothing to offer.
let collectionsLoaded = false;
// The one in-flight load, so a view that cannot start without the registry can
// wait for it rather than race it. A ?view=contest link does exactly that: it
// dispatches at boot, when /api/collections has not answered yet.
let collectionsReady = null;

async function loadCollections() {
  try {
    const res = await fetch('/api/collections');
    if (!res.ok) throw new Error('collections unavailable');
    const data = await res.json();
    collections = Array.isArray(data.collections) ? data.collections : [];
    collectionsLoaded = true;
    renderCollectionControls();
  } catch (_err) {
    // Never drop state on a failed load: a ?contest= link still selected those
    // collections, and the server is still filtering by them. Chips render by
    // id, and the add button stays hidden because we have nothing to list.
    collectionsLoaded = false;
    renderCollectionControls(false);
  }
}

function collectionById(id) {
  return collections.find(c => c.id === id) || null;
}

function collectionChipLabel(collection, id) {
  return collection ? (collection.short || collection.name) : id;
}

// "resources only" is the honest phrasing for a collection whose problems are
// all still unindexed — "0 problems" reads like a bug.
// One phrase for "how much of this collection is here", used by the picker
// option and the resources panel alike. They used to be two strings, and the
// panel's read "0 searchable problems" for exactly the collections the picker
// had been taught to call "resources only".
function collectionCountPhrase(collection) {
  const count = collection.count || 0;
  const base = count ? `${count} problem${count === 1 ? '' : 's'}` : 'resources only';
  return collection.unavailableCount ? `${base} · ${collection.unavailableCount} not yet indexed` : base;
}

function collectionOptionLabel(collection) {
  return `${collection.name} · ${collectionCountPhrase(collection)}`;
}

// The registry vocabulary is public | inaccessible | not-verified, so "public"
// is the unremarkable case and gets no suffix. This used to compare against
// "available", a value the validator never accepts, so every link said
// "· public".
function resourceAvailabilityNote(availability) {
  if (!availability || availability === 'public') return '';
  return ` · ${String(availability).replace(/[_-]/g, ' ')}`;
}

// Only the similarity view needs a caveat: a recommendation is not a PYQ, and
// saying so is the honest part. A collection view needs no sentence — the chip
// already says which competition you are looking at.
function collectionNote(similar = currentSimilar) {
  return similar ? 'Related practice · recommendations are not necessarily PYQs.' : '';
}

function renderCollectionControls(loaded = collectionsLoaded) {
  renderCollectionChips();
  renderCollectionPicker(loaded);
  renderCollectionPanel();
}

function renderCollectionChips() {
  const chips = document.getElementById('collection-chips');
  if (!chips) return;
  chips.innerHTML = '';
  for (const id of activeCollections) {
    const item = collectionById(id);
    const label = collectionChipLabel(item, id);
    const chip = document.createElement('button');
    chip.type = 'button';
    chip.className = 'judge-chip active collection-chip';
    chip.dataset.collection = id;
    chip.textContent = `${label} ×`;
    chip.title = item ? item.name : id;
    chip.setAttribute('aria-label', `remove ${item ? item.name : id}`);
    chip.addEventListener('click', () => removeCollection(id));
    chips.appendChild(chip);
  }
}

function inactiveCollections() {
  return collections.filter(c => !activeCollections.has(c.id));
}

function renderCollectionPicker(loaded = collectionsLoaded) {
  const add = document.getElementById('collection-add');
  const picker = document.getElementById('collection-picker');
  if (!add || !picker) return;
  const options = loaded ? inactiveCollections() : [];
  add.classList.toggle('hidden', options.length === 0);
  if (!options.length) {
    closeCollectionPicker({ focus: false });
    picker.innerHTML = '';
    return;
  }
  picker.innerHTML = '';
  for (const c of options) {
    const option = document.createElement('button');
    option.type = 'button';
    option.className = 'collection-option';
    option.setAttribute('role', 'option');
    option.setAttribute('aria-selected', 'false');
    option.dataset.collection = c.id;
    option.textContent = collectionOptionLabel(c);
    // Safari does not focus a button on mousedown. Without this the click
    // would pull focus out of the listbox, the focusout handler below would
    // hide the picker, and the option would be display:none by the time the
    // click landed — so the mouse did nothing while the keyboard worked.
    // Keeping focus put is also the standard listbox behaviour.
    option.addEventListener('mousedown', (e) => { e.preventDefault(); });
    option.addEventListener('click', () => {
      closeCollectionPicker({ focus: false });
      addCollection(c.id);
    });
    picker.appendChild(option);
  }
}

function collectionPickerOptions() {
  const picker = document.getElementById('collection-picker');
  return picker ? [...picker.querySelectorAll('.collection-option')] : [];
}

function openCollectionPicker() {
  const add = document.getElementById('collection-add');
  const picker = document.getElementById('collection-picker');
  if (!add || !picker || add.classList.contains('hidden')) return;
  picker.hidden = false;
  add.setAttribute('aria-expanded', 'true');
  const first = collectionPickerOptions()[0];
  if (first) first.focus();
}

function closeCollectionPicker({ focus = false } = {}) {
  const add = document.getElementById('collection-add');
  const picker = document.getElementById('collection-picker');
  if (!picker || picker.hidden) {
    if (add) add.setAttribute('aria-expanded', 'false');
    return;
  }
  picker.hidden = true;
  if (add) {
    add.setAttribute('aria-expanded', 'false');
    if (focus) add.focus();
  }
}

function collectionPickerOpen() {
  const picker = document.getElementById('collection-picker');
  return !!picker && !picker.hidden;
}

function moveCollectionFocus(delta, absolute) {
  const options = collectionPickerOptions();
  if (!options.length) return;
  const current = options.indexOf(document.activeElement);
  let next;
  if (absolute === 'first') next = 0;
  else if (absolute === 'last') next = options.length - 1;
  else next = (current + delta + options.length) % options.length;
  options[next].focus();
}

function addCollection(id) {
  if (!id || activeCollections.has(id)) return;
  activeCollections.add(id);
  track("collection_added", { collection: id });
  // A second competition is a union of two sets, which is not a contest.
  if (activeCollections.size !== 1) contestView = false;
  currentOffset = 0;
  renderCollectionControls();
  syncUrl({ push: true });
  reissueCurrentView();
}

function removeCollection(id) {
  if (!activeCollections.delete(id)) return;
  track("collection_removed", { collection: id });
  // Dropping the chip drops the page it was the subject of.
  contestView = false;
  currentOffset = 0;
  renderCollectionControls();
  syncUrl({ push: true });
  // Dropping the last facet is a return to the empty state, not a browse of
  // nothing — the same fall-through the chip has always had.
  if (!activeCollections.size && !activePlatforms.size && !activePattern && !currentQuery && !currentSimilar) runSearch('');
  else reissueCurrentView();
}

function renderCollectionPanel() {
  const panel = document.getElementById('collection-resources');
  if (!panel) return;
  // Which resource lists were expanded is the reader's state, not ours, and a
  // re-render happens on every chip change — so it is carried across.
  const open = new Set([...panel.querySelectorAll('details[open]')].map(d => d.dataset.collection));
  panel.hidden = activeCollections.size === 0;
  panel.innerHTML = '';
  if (!activeCollections.size) return;
  const heading = document.createElement('div');
  heading.className = 'collection-heading';
  const note = document.createElement('span');
  note.id = 'collection-note';
  note.textContent = collectionNote();
  heading.appendChild(note);
  // With exactly one competition selected there is a contest to look at, so
  // the panel that already names it offers the way in — and, once you are
  // there, the way back out. Two chips is a union, not a contest, so the
  // button is simply absent.
  if (activeCollections.size === 1) {
    const id = [...activeCollections][0];
    const open = document.createElement('button');
    open.type = 'button';
    open.id = 'contest-open';
    open.className = 'lib-chip';
    open.textContent = contestView ? '← results' : 'contest page →';
    open.title = contestView
      ? 'back to the ranked list'
      : 'every problem in the set, including the ones not indexed yet';
    open.addEventListener('click', () => {
      if (contestView) {
        contestView = false;
        syncUrl({ push: true });
        runSearch('');
        renderCollectionPanel();
        return;
      }
      contestView = true;
      syncUrl({ push: true });
      runContest(id);
    });
    heading.appendChild(open);
  }
  if (heading.childNodes.length > 1 || note.textContent) panel.appendChild(heading);
  // The contest page's own header already lists these links, editorials first.
  // Printing them twice, six inches apart, reads as two different lists.
  if (contestView) return;
  for (const id of activeCollections) {
    const collection = collectionById(id);
    if (!collection) continue;
    const details = document.createElement('details');
    details.dataset.collection = id;
    if (open.has(id)) details.open = true;
    const summary = document.createElement('summary');
    summary.textContent = `${collection.name} · ${collectionCountPhrase(collection)} · resources`;
    details.appendChild(summary);
    const list = document.createElement('ul');
    for (const resource of collection.resources || []) {
      const url = safeResourceUrl(resource.url);
      if (!url) continue;
      const li = document.createElement('li');
      const link = document.createElement('a');
      link.href = url;
      link.target = '_blank';
      link.rel = 'noopener';
      link.textContent = resource.title || resource.kind || 'contest resource';
      li.appendChild(link);
      const availability = resourceAvailabilityNote(resource.availability);
      if (availability) li.appendChild(document.createTextNode(availability));
      list.appendChild(li);
    }
    if (!list.childNodes.length) {
      const li = document.createElement('li');
      li.textContent = 'No additional resource links have been verified yet.';
      list.appendChild(li);
    }
    details.appendChild(list);
    panel.appendChild(details);
  }
}

const collectionAddBtn = document.getElementById('collection-add');
if (collectionAddBtn) {
  collectionAddBtn.addEventListener('click', () => {
    if (collectionPickerOpen()) closeCollectionPicker({ focus: true });
    else openCollectionPicker();
  });
  collectionAddBtn.addEventListener('keydown', (e) => {
    if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
      e.preventDefault();
      openCollectionPicker();
    }
  });
}

const collectionPickerEl = document.getElementById('collection-picker');
if (collectionPickerEl) {
  collectionPickerEl.addEventListener('keydown', (e) => {
    if (e.key === 'ArrowDown') { e.preventDefault(); moveCollectionFocus(1); }
    else if (e.key === 'ArrowUp') { e.preventDefault(); moveCollectionFocus(-1); }
    else if (e.key === 'Home') { e.preventDefault(); moveCollectionFocus(0, 'first'); }
    else if (e.key === 'End') { e.preventDefault(); moveCollectionFocus(0, 'last'); }
    else if (e.key === 'Escape') { e.preventDefault(); closeCollectionPicker({ focus: true }); }
    else if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      const id = document.activeElement && document.activeElement.dataset
        ? document.activeElement.dataset.collection : null;
      if (id) { closeCollectionPicker({ focus: false }); addCollection(id); }
    }
  });
  // Tabbing past the last option leaves the listbox, so it should not stay
  // open behind you.
  collectionPickerEl.addEventListener('focusout', (e) => {
    const to = e.relatedTarget;
    if (to && (collectionPickerEl.contains(to) || to === collectionAddBtn)) return;
    // relatedTarget is null whenever focus goes nowhere in particular, which
    // includes the middle of a Safari click on an option. Closing on the spot
    // would destroy the option before its click fired, so settle first and
    // close only if focus really did leave.
    setTimeout(() => {
      const active = typeof document !== 'undefined' ? document.activeElement : null;
      if (active && (collectionPickerEl.contains(active) || active === collectionAddBtn)) return;
      closeCollectionPicker({ focus: false });
    }, 0);
  });
  document.addEventListener('pointerdown', (e) => {
    if (!collectionPickerOpen()) return;
    if (collectionPickerEl.contains(e.target) || (collectionAddBtn && collectionAddBtn.contains(e.target))) return;
    closeCollectionPicker({ focus: false });
  });
}

function syncCsesLevelControl() {
  const row = document.getElementById('cses-level-row');
  const select = document.getElementById('cses-level-select');
  if (!row || !select) return;
  row.hidden = !activePlatforms.has('cses');
  select.value = csesLevel ? String(csesLevel) : '';
  select.disabled = csesLevelSaving;
  const note = document.getElementById('cses-level-note');
  if (note) note.textContent = currentUser ? 'Your choice is saved to this account.' : 'Saved in this browser · CSES uses its own scale.';
}

function setCsesLevelSuggestion(band) {
  csesLevel = Number.isInteger(band) && band >= 1 && band <= 5 ? band : null;
  if (csesLevel) {
    const label = cosineDifficulty.bands[csesLevel - 1];
    const token = cosineDifficulty.tokens[csesLevel - 1];
    const meta = (difficultyPayload.named || []).find(b => b.id === token);
    levelSuggest = levelSuggest || {};
    levelSuggest.cses = { difficulty: token, why: `Your selected CSES band: ${label}`, count: meta ? meta.count : 0 };
  } else if (levelSuggest) {
    // Clearing must not leave an empty object behind. loadLevelSignals used to
    // read any truthy levelSuggest as "already loaded" and skip /api/level, so
    // a sign-in after a clear would never show the cf/atc/lc "my level" chips.
    delete levelSuggest.cses;
    if (!Object.keys(levelSuggest).length) levelSuggest = null;
  }
  syncDifficultyControls();
}

async function loadCsesLevel() {
  const userId = currentUser && currentUser.id;
  if (!userId) {
    let band = null;
    try { band = Number(localStorage.getItem('cosine_cses_level_anon_v1')); } catch (_err) {}
    setCsesLevelSuggestion(band);
    return;
  }
  try {
    const res = await fetch('/api/preferences/cses-level');
    if (!res.ok) return;
    const data = await res.json();
    if (currentUser && currentUser.id === userId) setCsesLevelSuggestion(data.band);
  } catch (_err) {}
}

const csesLevelSelect = document.getElementById('cses-level-select');
if (csesLevelSelect) csesLevelSelect.addEventListener('change', async () => {
  const band = csesLevelSelect.value ? Number(csesLevelSelect.value) : null;
  track("cses_level_set", band ? { band } : {});
  if (!currentUser) {
    try {
      if (band) localStorage.setItem('cosine_cses_level_anon_v1', String(band));
      else localStorage.removeItem('cosine_cses_level_anon_v1');
      setCsesLevelSuggestion(band);
      applyCsesLevelFilter(band);
    } catch (_err) { setStatus('Could not save your CSES level in this browser.'); }
    return;
  }
  const userId = currentUser.id;
  csesLevelSaving = true;
  syncCsesLevelControl();
  try {
    const res = await fetch('/api/preferences/cses-level', {
      method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ band }),
    });
    if (!res.ok) throw new Error(`save failed (${res.status})`);
    if (currentUser && currentUser.id === userId) {
      setCsesLevelSuggestion(band);
      applyCsesLevelFilter(band);
    }
  } catch (err) { setStatus(`CSES level: ${err.message}`); }
  finally { csesLevelSaving = false; syncCsesLevelControl(); }
});

// ── the labels switch ───────────────────────────────────────────────────────
// Same storage shape as the CSES band: a column on the account when signed in,
// a localStorage mirror when not. A reading mode, not a facet, so it sits in
// the library bar next to :help rather than in the judge row.
const labelsToggle = document.getElementById('labels-toggle');

function syncLabelsToggle() {
  if (!labelsToggle) return;
  labelsToggle.textContent = showLabels ? 'labels: shown' : 'labels: hidden';
  labelsToggle.setAttribute('aria-pressed', String(showLabels));
  labelsToggle.classList.toggle('is-active', showLabels);
  labelsToggle.disabled = showLabelsSaving;
  labelsToggle.title = showLabels
    ? 'technique labels are showing on every result'
    : 'technique labels stay hidden while you attempt a problem';
}

function applyLabelVisibility({ reissue = true } = {}) {
  document.body.classList.toggle('labels-hidden', !showLabels);
  // Showing them all makes every per-card reveal redundant, and keeping the
  // set would leave those cards open when the switch goes back to hidden.
  if (showLabels) revealedCards.clear();
  syncLabelsToggle();
  if (reissue) reissueCurrentView();
}

async function loadShowLabels({ reissue = true } = {}) {
  const userId = currentUser && currentUser.id;
  const before = showLabels;
  let stored = null;
  try { stored = localStorage.getItem('cosine_show_labels_v1'); } catch (_err) {}
  showLabels = stored === '1';
  applyLabelVisibility({ reissue: reissue && showLabels !== before });
  if (!userId) return;
  try {
    const res = await fetch('/api/preferences/show-labels');
    if (!res.ok) return;
    const data = await res.json();
    if (!currentUser || currentUser.id !== userId) return;
    // null means this account never chose, so whatever this browser remembers
    // stands — signing in must not silently flip a switch someone set.
    if (typeof data.showLabels !== 'boolean') return;
    const wasShowing = showLabels;
    showLabels = data.showLabels;
    applyLabelVisibility({ reissue: reissue && showLabels !== wasShowing });
  } catch (_err) {}
}

async function saveShowLabels(next) {
  if (!currentUser) {
    try { localStorage.setItem('cosine_show_labels_v1', next ? '1' : '0'); }
    catch (_err) { setStatus('Could not remember the labels switch in this browser.'); }
    return;
  }
  const userId = currentUser.id;
  showLabelsSaving = true;
  syncLabelsToggle();
  try {
    const res = await fetch('/api/preferences/show-labels', {
      method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ showLabels: next }),
    });
    if (!res.ok) throw new Error(`save failed (${res.status})`);
  } catch (err) {
    setStatus(`Labels switch: ${err.message}`);
    // The switch still holds for this session; only the account copy failed.
    try { localStorage.setItem('cosine_show_labels_v1', next ? '1' : '0'); } catch (_e) {}
  } finally {
    showLabelsSaving = false;
    if (!currentUser || currentUser.id === userId) syncLabelsToggle();
  }
}

if (labelsToggle) labelsToggle.addEventListener('click', () => {
  showLabels = !showLabels;
  track("labels_toggled", { shown: showLabels });
  saveShowLabels(showLabels);
  applyLabelVisibility();
});

// Choosing a CSES band is choosing a filter. This used to only make the
// "my level" chip appear, which read as a control that did nothing. It goes
// through the same token path the chip uses, so "my level ✓" agrees with it.
function applyCsesLevelFilter(band) {
  for (const id of [...activeTiers]) if (id.startsWith('cses-')) activeTiers.delete(id);
  if (band) applyDifficultyToken(cosineDifficulty.tokens[band - 1]);
  afterDifficultyChange();
}

// Judge chips. Multi-select on purpose: "codeforces + atcoder" is a real way
// to think about practice, and the single-pick dropdown this replaced couldn't
// express it. Lives here rather than in the library bar so anonymous users get
// it too, and so it composes with :bookmarks / :done instead of fighting them.
judgeRow.querySelectorAll(".judge-chip[data-platform]").forEach((chip) => {
  chip.addEventListener("click", () => togglePlatformFilter(chip.dataset.platform));
});
judgeClearBtn.addEventListener("click", () => clearPlatformFilter());

// Names whatever is narrowing the current view, so a short or empty library
// listing explains itself instead of looking broken.
//
// This was deleted by accident when the browse shuffle was reverted — the
// removal was done by slicing between two source markers, and this function sat
// between them. runLibrary still called it, so :bookmarks / :done / :all threw
// a ReferenceError and rendered nothing at all.
function orderNote() {
  if (sortDir) return ` · ${sortDir === "desc" ? "hardest" : "easiest"} first`;
  return libOldest ? " · oldest first" : "";
}

// Cache-only on the server, so this costs one indexed read and never makes the
// search page wait on leetcode.com. A signed-out user, or one who has never
// opened the profile page, simply doesn't get the button.
async function loadLevelSignals() {
  // Keyed by user, not by whether levelSuggest is truthy: the CSES preference
  // writes into the same object, so truthiness never meant "fetched".
  if (!currentUser || levelSignalsUser === currentUser.id) return;
  const userId = currentUser.id;
  try {
    const res = await fetch("/api/level");
    if (!res.ok) return;
    const data = await res.json();
    if (!currentUser || currentUser.id !== userId) return;
    if (!data.suggest || !Object.keys(data.suggest).length) return;
    levelSuggest = { ...data.suggest, ...(csesLevel && levelSuggest?.cses ? { cses: levelSuggest.cses } : {}) };
    levelSignalsUser = userId;
    syncDifficultyControls();
  } catch (_err) {
    // A missing button is the right failure here — never block the page.
  }
}

function activeFacets() {
  const bits = [];
  if (activePattern) bits.push(activePattern);
  for (const id of activeCollections) bits.push(collections.find(c => c.id === id)?.name || id);
  if (activePlatforms.size) bits.push([...activePlatforms].map((p) => (PLATFORM_LABELS[p] || [p])[0]).join("+"));
  for (const id of activeTiers) {
    const b = (difficultyPayload.named || []).find((x) => x.id === id);
    if (b) bits.push(b.label);
  }
  for (const [judge, r] of activeRanges) {
    const short = (PLATFORM_LABELS[judge] || [judge])[0];
    bits.push(r.min === r.max ? `${short} ${r.min}` : `${short} ${r.min}-${r.max}`);
  }
  if (activeAcceptance) bits.push(`ac ${activeAcceptance.min}-${activeAcceptance.max}%`);
  if (currentUser && currentFilter !== "all") bits.push(currentFilter === "done" ? "done" : "not done");
  if (libAged) bits.push(`marked ${libAged >= 180 ? "6mo" : libAged >= 90 ? "3mo" : "1mo"}+ ago`);
  if (libRecall) bits.push(libRecall === "none" ? "unrated" : `recall ${libRecall}`);
  if (libNotes) bits.push(libNotes === "yes" ? "written up" : "no note");
  return bits;
}

// Difficulty only means something inside one judge, so the row is built from
// whichever judges are currently selected. No judge selected means "all
// judges", and there is no scale that spans all four — so the row stays hidden
// rather than offering a choice that can't be honoured.
//
// Two control shapes, because the two kinds of scale differ in kind: LeetCode's
// three named tiers are chips, while Codeforces and AtCoder ratings get a
// from/to range. Fixed coarse bands could not express "only 1500-rated", and on
// Codeforces — where every rating is a multiple of 100 — that is a reasonable
// thing to want.
const activeTiers = new Set();     // named tiers, e.g. lc-hard
const activeRanges = new Map();    // judge -> { min, max }
let activeAcceptance = null;       // { min, max } — leetcode acceptance rate
let levelSuggest = null;           // judge -> { difficulty, why, count }, from /api/level
let levelSignalsUser = null;       // whose /api/level answer levelSuggest currently holds

function difficultyParam() {
  const parts = [...activeTiers];
  for (const [judge, r] of activeRanges) {
    const meta = (difficultyPayload.rated || []).find((x) => x.judge === judge);
    if (meta) parts.push(`${meta.short}:${r.min}-${r.max}`);
  }
  if (activeAcceptance) parts.push(`ac:${activeAcceptance.min}-${activeAcceptance.max}`);
  return parts.join(",");
}

// Applies one `difficulty=` token to the live controls. The URL restore and
// the "my level" button both produce these tokens, so they parse in one place.
function applyDifficultyToken(token) {
  const t = String(token || "").trim().toLowerCase();
  if (!t) return;
  const range = /^([a-z]{2,4}):(-?\d+)-(-?\d+)$/.exec(t);
  if (range && range[1] === "ac") {
    activeAcceptance = { min: Number(range[2]), max: Number(range[3]) };
  } else if (range) {
    const meta = (difficultyPayload.rated || []).find((r) => r.short === range[1]);
    if (meta) activeRanges.set(meta.judge, { min: Number(range[2]), max: Number(range[3]) });
  } else if (/^[a-z]{2,4}-[a-z]+$/.test(t)) {
    activeTiers.add(t);
  }
}

// The suggestions that apply to what's on screen: a judge you haven't selected
// shouldn't have its band silently set behind a control you can't see.
function levelForSelection() {
  if (!levelSuggest) return [];
  return [...activePlatforms].map((j) => levelSuggest[j]).filter(Boolean);
}

function levelIsApplied() {
  const suggested = levelForSelection();
  if (!suggested.length) return false;
  const want = suggested.flatMap((s) => s.difficulty.split(",")).sort().join(",");
  const have = (difficultyParam() || "").split(",").filter(Boolean).sort().join(",");
  return want === have;
}

function syncDifficultyControls() {
  syncCsesLevelControl();
  if (!difficultyRow) return;
  const payloadLoaded =
    (difficultyPayload.named || []).length ||
    (difficultyPayload.rated || []).length ||
    difficultyPayload.acceptance;
  if (!payloadLoaded) {
    // Boot order: this runs once before /api/rankers responds. Hide the row
    // but touch NO state — sortDir and boot-restored tiers must survive until
    // the payload can actually render them. Clearing here is how
    // ?platform=atcoder&sort=difficulty-asc used to boot unsorted.
    difficultyRow.classList.add("hidden");
    difficultyRow.innerHTML = "";
    return;
  }
  const judges = [...activePlatforms];
  const named = (difficultyPayload.named || []).filter((b) => activePlatforms.has(b.judge));
  const rated = (difficultyPayload.rated || []).filter((r) => activePlatforms.has(r.judge));

  if (!judges.length || (!named.length && !rated.length)) {
    // Dropping a judge drops its difficulty with it. Leaving a live "cf 1500"
    // filter active with Codeforces switched off would filter by something the
    // user can no longer see or clear.
    activeTiers.clear();
    activeRanges.clear();
    activeAcceptance = null;
    sortDir = null; // no scale on screen, so no order to sort by
    difficultyRow.classList.add("hidden");
    difficultyRow.innerHTML = "";
    return;
  }
  for (const id of [...activeTiers]) if (!named.some((b) => b.id === id)) activeTiers.delete(id);
  for (const j of [...activeRanges.keys()]) if (!rated.some((r) => r.judge === j)) activeRanges.delete(j);

  // Acceptance rate is only offered once a tier is chosen, because across tiers
  // it isn't comparable in this corpus — the Mediums here were selected FOR a
  // low acceptance rate and the Hards weren't. Picking the tier first is what
  // makes "the hardest Mediums" an honest question. So the control comes and
  // goes with the tier selection, and its value goes with it.
  const acc = difficultyPayload.acceptance;
  const accTiers = acc
    ? [...activeTiers].map((id) => named.find((b) => b.id === id)).filter((b) => b && b.judge === acc.judge)
    : [];
  if (!accTiers.length) activeAcceptance = null;

  // Acceptance rate belongs to LeetCode, so it is rendered as part of
  // LeetCode's group rather than appended after every judge — it used to sit
  // past the Codeforces rating range, which read as a third judge's control.
  let acceptanceHtml = "";
  if (accTiers.length) {
    // Bounds are the union of the SELECTED tiers, not of all LeetCode: the
    // Easies top out at 65% and the Mediums reach 90%, so a shared range would
    // offer stops that can never match what's on screen.
    const lo = Math.min(...accTiers.map((b) => (acc.tiers[b.label] || acc).min));
    const hi = Math.max(...accTiers.map((b) => (acc.tiers[b.label] || acc).max));
    const stops = acc.stops.filter((v) => v >= lo && v <= hi);
    const cur = activeAcceptance || { min: lo, max: hi };
    const opts = (selected) =>
      stops.map((v) => `<option value="${v}"${v === selected ? " selected" : ""}>${v}%</option>`).join("");
    acceptanceHtml =
      '<span class="difficulty-group acceptance-group"><span class="difficulty-label" title="acceptance rate — lower is harder">ac</span>' +
      '<select class="filter-select acceptance-select" data-edge="min" aria-label="minimum acceptance rate">' +
      `${opts(cur.min)}</select><span class="range-dash">to</span>` +
      '<select class="filter-select acceptance-select" data-edge="max" aria-label="maximum acceptance rate">' +
      `${opts(cur.max)}</select></span>`;
  }

  const groups = [];
  for (const judge of judges) {
    const short = (PLATFORM_LABELS[judge] || [judge])[0];
    const tiers = named.filter((b) => b.judge === judge);
    const range = rated.find((r) => r.judge === judge);
    if (!tiers.length && !range) continue;

    let body = "";
    if (tiers.length) {
      body = tiers
        .map(
          (b) =>
            `<button type="button" class="judge-chip difficulty-chip${activeTiers.has(b.id) ? " active" : ""}"` +
            ` data-tier="${escapeHtml(b.id)}"${b.count ? "" : " disabled"}>` +
            `${escapeHtml(b.judge === "cses" ? b.label.replace(/\s*\(estimate\)$/i, "") : b.label)}<span class="chip-count">${b.count}</span></button>`
        )
        .join("");
    } else {
      const cur = activeRanges.get(judge) || { min: range.min, max: range.max };
      const opts = (selected) =>
        range.stops
          .map((v) => `<option value="${v}"${v === selected ? " selected" : ""}>${v}</option>`)
          .join("");
      body =
        `<select class="filter-select rating-select" data-judge="${escapeHtml(judge)}" data-edge="min"` +
        ` aria-label="${escapeHtml(judge)} minimum rating">${opts(cur.min)}</select>` +
        `<span class="range-dash">to</span>` +
        `<select class="filter-select rating-select" data-judge="${escapeHtml(judge)}" data-edge="max"` +
        ` aria-label="${escapeHtml(judge)} maximum rating">${opts(cur.max)}</select>`;
    }
    groups.push(
      `<span class="difficulty-group"><span class="difficulty-label">${escapeHtml(judge === "cses" ? "cses estimates" : short)}</span>${body}</span>`
    );
    if (acceptanceHtml && acc && judge === acc.judge) groups.push(acceptanceHtml);
  }

  // Sorting shares the difficulty row's rule — one judge, because there is no
  // order between "Medium" and 1600 — so it lives here rather than in the
  // search bar where it would look available all the time.
  const canSort = activePlatforms.size === 1 && (named.length > 0 || rated.length > 0);
  if (canSort) {
    const typed = (input.value.trim() || currentQuery || "").toLowerCase();
    // A ranking only exists for a real query. `:bookmarks` is a command, and the
    // library sorts the whole saved list — offering it a "top 20" would lie.
    const searching = !!currentSimilar || (!!typed && !(currentUser && libraryCommand(typed)));
    groups.push(
      '<span class="difficulty-group sort-group"><span class="difficulty-label">sort</span>' +
        `<select class="filter-select" id="sort-select" aria-label="sort by difficulty">` +
        `<option value=""${!sortDir ? " selected" : ""}>${searching ? "relevance" : "default"}</option>` +
        `<option value="asc"${sortDir === "asc" ? " selected" : ""}>easiest first</option>` +
        `<option value="desc"${sortDir === "desc" ? " selected" : ""}>hardest first</option>` +
        "</select>" +
        // The window only exists while searching: with a query there IS a
        // relevance order worth protecting, so we reorder its top N rather
        // than discarding it. Browsing has no such order to protect.
        (sortDir && searching
          ? `<select class="filter-select" id="sort-window" aria-label="how many results to sort">` +
            [20, 50, 100].map((n) => `<option value="${n}"${n === sortWindow ? " selected" : ""}>top ${n}</option>`).join("") +
            "</select>"
          : "") +
        "</span>"
    );
  } else if (sortDir) {
    sortDir = null; // the judge that made it legal is gone
  }

  // "my level" sets each selected judge's band from that judge's own stats. It
  // only shows when there IS a suggestion for something on screen, so it can
  // never be a button that does nothing.
  const suggested = levelForSelection();
  if (suggested.length) {
    const applied = levelIsApplied();
    const why = suggested.map((x) => `${x.why} → ${x.count} problems`).join("; ");
    groups.push(
      `<button type="button" class="judge-chip level-chip${applied ? " active" : ""}" id="level-apply"` +
        ` title="${escapeHtml(why)}">${applied ? "my level ✓" : "my level"}</button>`
    );
  }

  if (activeTiers.size || activeRanges.size || activeAcceptance) {
    groups.push('<button type="button" class="judge-chip judge-clear" id="difficulty-clear" title="any difficulty">any ✕</button>');
  }
  difficultyRow.innerHTML = groups.join("");
  difficultyRow.classList.toggle("hidden", groups.length === 0);

  difficultyRow.querySelectorAll(".difficulty-chip").forEach((btn) => {
    btn.addEventListener("click", () => {
      const id = btn.dataset.tier;
      if (activeTiers.has(id)) activeTiers.delete(id);
      else activeTiers.add(id);
      track("difficulty_selected", { tier: id });
      afterDifficultyChange();
    });
  });
  difficultyRow.querySelectorAll(".rating-select").forEach((sel) => {
    sel.addEventListener("change", () => {
      const judge = sel.dataset.judge;
      const meta = rated.find((r) => r.judge === judge);
      const cur = activeRanges.get(judge) || { min: meta.min, max: meta.max };
      const v = Number(sel.value);
      const next = sel.dataset.edge === "min" ? { min: v, max: cur.max } : { min: cur.min, max: v };
      // Dragging one edge past the other is a slip, not an empty-set request.
      if (next.min > next.max) {
        if (sel.dataset.edge === "min") next.max = next.min;
        else next.min = next.max;
      }
      if (next.min === meta.min && next.max === meta.max) activeRanges.delete(judge);
      else activeRanges.set(judge, next);
      track("difficulty_selected", { judge, min: next.min, max: next.max });
      afterDifficultyChange();
    });
  });
  difficultyRow.querySelectorAll(".acceptance-select").forEach((sel) => {
    sel.addEventListener("change", () => {
      const lo = Math.min(...accTiers.map((b) => (acc.tiers[b.label] || acc).min));
      const hi = Math.max(...accTiers.map((b) => (acc.tiers[b.label] || acc).max));
      const cur = activeAcceptance || { min: lo, max: hi };
      const v = Number(sel.value);
      const next = sel.dataset.edge === "min" ? { min: v, max: cur.max } : { min: cur.min, max: v };
      if (next.min > next.max) {
        if (sel.dataset.edge === "min") next.max = next.min;
        else next.min = next.max;
      }
      activeAcceptance = next.min === lo && next.max === hi ? null : next;
      track("difficulty_selected", { acceptance: `${next.min}-${next.max}` });
      afterDifficultyChange();
    });
  });

  const sortSel = difficultyRow.querySelector("#sort-select");
  if (sortSel) sortSel.addEventListener("change", () => {
    sortDir = sortSel.value || null;
    track("sort_changed", { dir: sortDir || "relevance" });
    afterDifficultyChange();
  });
  const windowSel = difficultyRow.querySelector("#sort-window");
  if (windowSel) windowSel.addEventListener("change", () => {
    sortWindow = Number(windowSel.value) || 20;
    afterDifficultyChange();
  });

  const level = difficultyRow.querySelector("#level-apply");
  if (level) level.addEventListener("click", () => {
    const suggestions = levelForSelection();
    if (levelIsApplied()) {
      activeTiers.clear();
      activeRanges.clear();
      activeAcceptance = null;
      track("level_cleared", {});
    } else {
      activeTiers.clear();
      activeRanges.clear();
      activeAcceptance = null;
      for (const s of suggestions) for (const tok of s.difficulty.split(",")) applyDifficultyToken(tok);
      // Say what it did and why. A filter that changes the page without
      // explaining itself reads as a bug, and the reasoning is a guess worth
      // showing: these are proxies for your level, not measurements of it.
      setStatus(`my level · ${suggestions.map((x) => `${x.why} → ${x.count} problems`).join(" · ")}`);
      track("level_applied", { judges: suggestions.length });
    }
    afterDifficultyChange();
  });

  const clear = difficultyRow.querySelector("#difficulty-clear");
  if (clear) clear.addEventListener("click", () => {
    activeTiers.clear();
    activeRanges.clear();
    activeAcceptance = null;
    afterDifficultyChange();
  });
}

function afterDifficultyChange() {
  syncDifficultyControls();
  syncUrl();
  currentOffset = 0;
  reissueCurrentView();
}

// Re-runs whatever the user is looking at — a search, a browse, or a library
// listing — so a filter change behaves the same in all three. This used to
// hardcode runSearch, which meant changing a filter inside :bookmarks bounced
// you back to search results.
function reissueCurrentView() {
  if (currentSimilar) return runSimilar(currentSimilar, { append: false });
  const typed = input.value.trim();
  if (currentUser && libraryCommand(typed)) return runSearch(typed, { append: false });
  if (typed || currentQuery) return runSearch(typed || currentQuery, { append: false });
  if (activePattern || activePlatforms.size || activeCollections.size) return runBrowse({ append: false });
  return undefined;
}

function syncJudgeControls() {
  // An empty set means "every judge" — the server collapses none and all-four
  // to the same no-filter query. So the default has to render every chip as on:
  // showing them all off said "nothing is included", which is a state this
  // filter cannot actually reach and which implies an empty result set.
  const unfiltered = activePlatforms.size === 0;
  judgeRow.querySelectorAll(".judge-chip[data-platform]").forEach((chip) => {
    const on = unfiltered || activePlatforms.has(chip.dataset.platform);
    chip.classList.toggle("active", on);
    chip.setAttribute("aria-pressed", String(on));
  });
  // Quieter styling while it's the default, so four lit chips don't read as
  // four filters someone applied.
  judgeRow.classList.toggle("all-on", unfiltered);
  judgeClearBtn.classList.toggle("hidden", unfiltered);
  syncDifficultyControls();
}

function applyMode() {
  if (compareMode) {
    resultsEl.classList.add("hidden");
    compareEl.classList.remove("hidden");
    hideLoadMore();
  } else {
    resultsEl.classList.remove("hidden");
    compareEl.classList.add("hidden");
    latencySummaryEl.textContent = "";
  }
}

async function runSearch(rawQuery, { append = false } = {}) {
  contestView = false;
  const q = rawQuery.trim();
  if (currentSimilar && !q) return runSimilar(currentSimilar, { append });
  currentSimilar = null;
  similarLibrary = null;
  practiceMode = false;
  rankerSelect.disabled = false;
  // An empty box with a filter still on isn't "nothing to show" — it's a
  // browse. Clearing your query keeps the active label and judges and lists
  // everything they select, which is what they claim to be doing.
  if (!q && (activePattern || activePlatforms.size || activeCollections.size)) {
    currentQuery = "";
    if (!append) currentOffset = 0;
    return runBrowse({ append });
  }
  if (!q) {
    setStatus("");
    resultsEl.innerHTML = "";
    currentQuery = "";
    currentOffset = 0;
    currentTotal = 0;
    hideLoadMore();
    hideFeedback();
    if (currentUser) setLibPath("~");
    syncUrl();
    return;
  }

  // :compare <query> — one-shot, leaves compare mode as soon as you search
  // for something else.
  const cmp = compareQuery(q);
  if (cmp !== null) {
    compareMode = true;
    applyMode();
    if (!cmp) {
      setStatus("compare: type a query after :compare");
      compareEl.innerHTML = "";
      return;
    }
    currentQuery = q;
    return runCompare(cmp);
  }
  if (compareMode) {
    compareMode = false;
    applyMode();
  }

  const helpArg = helpQuery(q);
  if (helpArg !== null) {
    // Keep the query rather than blanking it, so syncUrl writes ?q=:help sheet
    // and a shared or refreshed link lands on the section it names.
    currentQuery = q;
    currentOffset = 0;
    currentTotal = 0;
    renderHelp(helpArg);
    syncUrl();
    return;
  }

  // Shell-style library commands.
  const lib = currentUser ? libraryCommand(q) : null;
  const libraryType = lib && lib.type;
  if (!libraryType && (libAged || libOldest || libRecall || libNotes)) {
    libAged = null;
    libOldest = false;
    libRecall = null;
    libNotes = null;
  }
  // A leading colon means "command", and every real one has been matched by
  // now — so this is a typo or a half-typed command, not a question about
  // problems. Searching the corpus for ":bo" costs a round trip to say nothing.
  // Also stops the debounce firing a query per keystroke while someone types
  // ":bookmarks" one character at a time.
  if (!currentUser && libraryCommand(q)) {
    // It IS a command — it just needs somewhere to save things to. Calling it
    // "not a command" (as the branch below would) reads as a broken feature.
    //
    // Keep currentQuery: on a refresh of `?q=:bookmarks` this runs BEFORE
    // /auth/me resolves, and bootstrapAuth re-issues only `if (wasPending &&
    // currentUser && currentQuery)`. Blanking it here made that condition
    // false, so the page sat on "needs an account" until you pressed enter
    // yourself — while signed in the whole time.
    currentQuery = q;
    currentOffset = 0;
    currentTotal = 0;
    hideLoadMore();
    hideFeedback();
    resultsEl.innerHTML = "";
    setStatus(`${q} needs an account — sign in to bookmark and track what you have solved`);
    return;
  }
  if (!libraryType && q.startsWith(":")) {
    currentQuery = "";
    currentOffset = 0;
    currentTotal = 0;
    hideLoadMore();
    hideFeedback();
    resultsEl.innerHTML = "";
    const known = currentUser
      ? ":help :bookmarks :done :all :compare"
      : ":help :compare  (sign in for :bookmarks, :done, :all)";
    setStatus(`${q} is not a command · try ${known}`);
    return;
  }
  if (libraryType) {
    if (!append) {
      currentQuery = q;
      currentOffset = 0;
    }
    syncUrl();
    return runLibrary(libraryType, lib.q);
  }

  if (compareMode) return runCompare(q);

  // Search mode: path drops the leading tilde and shows the query so the bar
  // reads like a real shell prompt: ~/search "graph cycle".
  if (currentUser) setLibPath(`~/search "${q.length > 24 ? q.slice(0, 24) + "…" : q}"`);

  if (!append) {
    currentQuery = q;
    currentOffset = 0;
    currentTopScore = 0;
  }
  syncUrl();

  const issuedAt = ++lastQueryAt;
  // Deliberately not setStatus(): that runs the typewriter, so every keystroke
  // animated `searching: "..."` one character at a time and then the result
  // line restarted the animation on top of it. Two typewriters racing per
  // keystroke read as noise. This waits, and prints plainly if it fires.
  clearTimeout(searchingTimer);
  searchingTimer = setTimeout(() => {
    if (issuedAt !== lastQueryAt) return;
    clearTimeout(typeTimer);
    statusEl.textContent = `searching: "${q}"`;
  }, SEARCHING_AFTER_MS);
  const filterParam = currentUser && currentFilter !== "all" ? `&filter=${currentFilter}` : "";
  const patternParam = activePattern ? `&pattern=${encodeURIComponent(activePattern)}` : "";
  const rankerParam = activeRanker ? `&ranker=${encodeURIComponent(activeRanker)}` : "";
  const platformParam = activePlatforms.size ? `&platform=${encodeURIComponent([...activePlatforms].join(","))}` : "";
  const dp = difficultyParam();
  const bandParam = dp ? `&difficulty=${encodeURIComponent(dp)}` : "";
  const sortParam = sortDir ? `&sort=difficulty-${sortDir}` : "";
  // Sorting reorders a fixed window of the best matches, so the window size
  // replaces the page size — and paging is withdrawn, not silently broken.
  const pageSize = sortDir ? sortWindow : TOP_K;
  const url = `/api/search?q=${encodeURIComponent(q)}&k=${pageSize}&offset=${sortDir ? 0 : currentOffset}${filterParam}${patternParam}${rankerParam}${platformParam}${bandParam}${sortParam}${collectionParam()}`;

  let data;
  try {
    if (inFlight) inFlight.abort();
    inFlight = new AbortController();
    const res = await fetch(url, { signal: inFlight.signal });
    data = await res.json();
  } catch (err) {
    // A superseded request is the normal case while typing, not an error.
    if (err.name === "AbortError" || issuedAt !== lastQueryAt) return;
    clearTimeout(searchingTimer);
    setStatus(`error: ${err.message || "search failed"}`);
    return;
  }

  if (issuedAt !== lastQueryAt) return;

  currentTotal = data.total || 0;
  if (!append) {
    currentSearchId = data.searchId || null;
    currentRankerAnswered = data.ranker || "";
  }
  renderSingle(data, q, append);
  // A sorted search is one fixed window of the best matches, not page 1 of
  // many — there is no coherent next page to offer.
  if (data.sortWindow) hideLoadMore();
  else updateLoadMore();
  if (!append) offerFeedback(data);
}

// "+extra words" when the expansion only added, "-> rewritten" when a phrase
// alias replaced what was typed. Showing the rewrite matters: the results for
// "square root decomposition" are really the results for "sqrt decomposition",
// and the user should be able to see that.
function describeExpansion(q, expandedQuery) {
  if (!expandedQuery || expandedQuery === q) return "";
  const lower = String(q).toLowerCase();
  if (expandedQuery.startsWith(lower)) {
    const extra = expandedQuery.slice(lower.length).trim();
    return extra ? ` · +${extra}` : "";
  }
  if (expandedQuery.startsWith(q)) {
    const extra = expandedQuery.slice(q.length).trim();
    return extra ? ` · +${extra}` : "";
  }
  return ` · → ${expandedQuery}`;
}

function renderSingle(data, q, append) {
  if (!data.hits || data.hits.length === 0) {
    if (!append) {
      // Name the words that matched nothing. "0 hits" reads as a broken search;
      // "no problem mentions deepya" tells you the corpus is finite and that
      // your query, not the engine, is the thing to change.
      const unknown = data.unknownTerms || [];
      setStatus(
        unknown.length
          ? `no problem mentions ${unknown.map((t) => `"${t}"`).join(" or ")} — try a technique, a title, or describe the problem`
          : `0 hits for "${q}"`
      );
      resultsEl.innerHTML = "";
    }
    return;
  }
  // "ranked in", not a bare number. This clock wraps index.search() only — no
  // network, no JSON, no user-state read — so it ran 13-66x faster than the
  // round trip even on localhost, and far more than that over the wire. A bare
  // "0.373ms" next to results you waited a beat for is the same false precision
  // the per-result similarity scores had before they moved to /debug.
  const lat = typeof data.latencyMs === "number" ? ` · ranked in ${data.latencyMs.toFixed(3)}ms` : "";
  // Alias expansion is server-side; show what was added so the vocabulary is
  // learnable ("aliens trick" → +wqs binary search).
  // Expansion used to only ever append, so slicing the original off the front
  // was enough. A phrase alias now REPLACES its span ("square root
  // decomposition" -> "sqrt decomposition"), which is shorter than the input
  // and shares no prefix with it — that slice produced a bare " · +".
  const expanded = describeExpansion(q, data.expandedQuery);
  // Nothing in the corpus uses these words — what came back is the nearest by
  // meaning, which is a weaker claim than a match and has to read as one.
  const stretched = (data.noLiteralMatch || []).length
    ? ` · nothing uses ${data.noLiteralMatch.map((w) => `"${w}"`).join(", ")} — nearest by meaning`
    : "";
  // Say when a word was corrected. Silently searching for something the user
  // didn't type is the kind of helpfulness that reads as a bug.
  const fixed = (data.corrected || []).length
    ? ` · read ${data.corrected.map((c) => `${c.from} as ${c.to}`).join(", ")}`
    : "";
  const shown = currentOffset + data.hits.length;
  const total = currentTotal;
  const modeName = { bm25: "keyword", dense: "meaning", hybrid: "both" }[data.ranker] || data.ranker;
  // Dropped from this line: the query (it's in the box two rows up) and the
  // raw ranker id in parens. On a phone the picker shortens to just "keyword",
  // so this is the only place the mode is spelled out — keep it.
  if (data.sortWindow) {
    // Deliberately not "1-20 of 142": this is the top N by relevance, then
    // reordered. Saying "of 142" would imply a page 2 that cannot exist.
    setStatus(
      `top ${data.sortWindow} of ${total} by ${modeName}, ${sortDir === "desc" ? "hardest" : "easiest"} first${lat}${expanded}${fixed}${stretched}`
    );
  } else {
    setStatus(`showing 1–${shown} of ${total} · ${modeName}${lat}${expanded}${fixed}${stretched}`);
  }
  renderHitsList(resultsEl, data.hits, { append, startIndex: currentOffset });
}

// Filters with no query. Same wire format and the same result renderer as a
// search — only the ranking is absent, so results come back in corpus order
// and the status line says "browsing" rather than quoting a query nobody typed.
async function runBrowse({ append = false } = {}) {
  contestView = false;
  const issuedAt = ++lastQueryAt;
  hideFeedback();
  currentSearchId = null;
  currentRankerAnswered = "";
  const facets = activeFacets();
  const label = facets.filter(Boolean).join(" · ");
  if (currentUser) setLibPath(`~/browse ${label}`);
  syncUrl();

  const patternParam = activePattern ? `&pattern=${encodeURIComponent(activePattern)}` : "";
  const platformParam = activePlatforms.size ? `&platform=${encodeURIComponent([...activePlatforms].join(","))}` : "";
  const filterParam = currentUser && currentFilter !== "all" ? `&filter=${currentFilter}` : "";
  const dp = difficultyParam();
  const bandParam = dp ? `&difficulty=${encodeURIComponent(dp)}` : "";
  const sortParam = sortDir ? `&sort=difficulty-${sortDir}` : "";
  const url = `/api/search?q=&k=${TOP_K}&offset=${currentOffset}${patternParam}${platformParam}${filterParam}${bandParam}${sortParam}${collectionParam()}`;

  let data;
  try {
    if (inFlight) inFlight.abort();
    inFlight = new AbortController();
    const res = await fetch(url, { signal: inFlight.signal });
    data = await res.json();
  } catch (err) {
    if (err.name === "AbortError" || issuedAt !== lastQueryAt) return;
    setStatus(`error: ${err.message || "browse failed"}`);
    return;
  }
  if (issuedAt !== lastQueryAt) return;

  currentTotal = data.total || 0;
  if (!append) currentTopScore = 0;
  const hits = data.hits || [];
  if (!hits.length) {
    // Three collections are resource-only shells by design — an archive page
    // and a scoreboard, no indexed problems. "nothing matches" reads like a
    // broken filter; the panel below it is the whole point of the selection.
    const active = [...activeCollections].map(collectionById).filter(Boolean);
    const resourceOnly = active.length === 1 && !(active[0].count || 0) ? active[0] : null;
    setStatus(
      currentTotal === 0 && resourceOnly
        ? `${resourceOnly.name} has no indexed problems yet — its resources are listed below.`
        : `nothing matches ${label}`
    );
    resultsEl.innerHTML = "";
    hideLoadMore();
    return;
  }
  renderHitsList(resultsEl, hits, { append, startIndex: currentOffset, unranked: true });
  const shown = currentOffset + hits.length;
  setStatus(`browsing ${label} · ${shown} of ${currentTotal}${orderNote()}`);
  updateLoadMore();
}

async function runLibrary(type, q) {
  const issuedAt = ++lastQueryAt;
  currentSearchId = null;
  currentRankerAnswered = "";
  hideFeedback();
  const facets = activeFacets();
  const shown = q ? `"${q}"` : "";
  setLibPath(`~/${type}${shown ? " " + shown : ""}${facets.length ? " " + facets.join(" ") : ""}`);
  setStatus(`ls ~/${type}${shown ? " " + shown : ""}${facets.length ? " · " + facets.join(" · ") : ""}`);
  hideLoadMore();

  let data;
  try {
    // Judge and done filters carry into the library: "my bookmarked AtCoder
    // problems I haven't finished" is one of the reasons to save things at all.
    const platformParam = activePlatforms.size ? `&platform=${encodeURIComponent([...activePlatforms].join(","))}` : "";
    const doneParam = currentFilter !== "all" ? `&filter=${currentFilter}` : "";
    const dp = difficultyParam();
    const bandParam = dp ? `&difficulty=${encodeURIComponent(dp)}` : "";
    const sortParam = sortDir ? `&sort=difficulty-${sortDir}` : "";
    const agedParam = libAged ? `&aged=${libAged}` : "";
    const orderParam = libOldest ? "&order=oldest" : "";
    const recallParam = libRecall ? `&recall=${encodeURIComponent(libRecall)}` : "";
    const qParam = q ? `&q=${encodeURIComponent(q)}` : "";
    const res = await fetch(`/api/library?type=${encodeURIComponent(type)}${platformParam}${doneParam}${bandParam}${sortParam}${agedParam}${orderParam}${recallParam}${qParam}${collectionParam()}${activePattern ? `&pattern=${encodeURIComponent(activePattern)}` : ""}`);
    data = await res.json();
  } catch (err) {
    if (issuedAt !== lastQueryAt) return;
    setStatus(`error: ${err.message || "library failed"}`);
    return;
  }
  if (issuedAt !== lastQueryAt) return;

  // Adapt library items to the renderHitsList hit shape.
  const all = (data.items || []).map((it) => ({
    problem: it.problem,
    done: it.done,
    bookmarked: it.bookmarked,
    recall: it.recall,
    matchedTerms: [],
    markedAt: it.markedAt,
  }));

  // The notes filter runs HERE, not on the server, because the server has
  // never seen a note and this design is the reason. `noteText` already merges
  // the sheet's cached rows with anything typed here and not yet synced, so a
  // note written thirty seconds ago counts.
  const knowsNotes = typeof cosineSheets !== "undefined" && cosineSheets.connected();
  const hits = (libNotes && knowsNotes)
    ? all.filter((h) => {
        const has = !!cosineSheets.noteText(h.problem.id).trim();
        return libNotes === "yes" ? has : !has;
      })
    : all;
  // Say "18 of 62" when the client dropped rows the server counted — a total
  // that silently disagrees with the one the server sent reads as a bug.
  const dropped = all.length - hits.length;

  currentTotal = hits.length;

  if (hits.length === 0) {
    // An empty list under a filter is a filter result, not an empty library —
    // say which, or it reads as data loss.
    const empty = q
      ? `ls: nothing in ~/${type} matches "${q}"${facets.length ? " · " + facets.join(" · ") : ""}`
      : facets.length
      ? `ls: nothing in ~/${type} matches ${facets.join(" · ")}`
      : type === "bookmarked"
      ? "ls: ~/bookmarked is empty — star ☆ a problem to save it here"
      : type === "done"
      ? "ls: ~/done is empty — mark ○ a problem to track it"
      : "ls: ~ is empty — bookmark or mark problems done from search";
    setStatus(empty);
    resultsEl.innerHTML = "";
    return;
  }

  setStatus(`${hits.length}${dropped ? ` of ${all.length}` : ""} ${type === "all" ? "saved" : type}${shown ? ` matching ${shown}` : ""}${facets.length ? " · " + facets.join(" · ") : ""}${orderNote()}`);
  renderHitsList(resultsEl, hits, { append: false, startIndex: 0, libraryMode: true });
  // A backstop sync on the first library view, for the case where the silent
  // token resume landed after this page had already loaded. The normal path
  // is now: resume a token on load, then sync a few seconds after any change.
  // Still gated on a token ALREADY in memory — no background path may be the
  // thing that puts a Google dialog on screen.
  if (!sheetSyncedThisSession && typeof cosineSheets !== "undefined"
      && cosineSheets.connected() && cosineSheets.hasToken()) {
    sheetSyncedThisSession = true;
    doSheetSync({ quiet: true });
  }
}

// Similarity is its own addressable view. Facets apply before pagination.
async function runSimilar(problem, { append = false, practice = false } = {}) {
  contestView = false;
  const entering = !currentSimilar || currentSimilar.id !== problem.id;
  if (entering) {
    similarLibrary = currentUser ? libraryCommand(currentQuery)?.type || null : null;
    practiceMode = false;
  }
  if (practice) {
    activeCollections.clear();
    similarLibrary = null;
    libAged = null;
    libOldest = false;
    libNotes = null;
    libRecall = null;
    currentFilter = 'notdone';
    filterSelect.value = 'notdone';
    practiceMode = true;
  }
  currentSimilar = problem;
  rankerSelect.disabled = true;
  currentQuery = '';
  input.value = '';
  compareMode = false;
  applyMode();
  if (!append) currentOffset = 0;
  currentTopScore = 0;
  currentSearchId = null;
  currentRankerAnswered = '';
  hideFeedback();
  syncDifficultyControls();
  renderCollectionControls();
  syncUrl();
  const issuedAt = ++lastQueryAt;
  const sourceTitle = problem.title || problem.id;
  if (currentUser) setLibPath(`~/similar/${problem.id}`);
  setStatus(`finding related practice for "${sourceTitle}"`);
  const notesActive = libNotes && typeof cosineSheets !== 'undefined' && cosineSheets.connected();
  const pageSize = sortDir ? sortWindow : TOP_K;
  const params = new URLSearchParams({ k: String(notesActive ? similarCorpusSize : pageSize), offset: String(notesActive || sortDir ? 0 : currentOffset) });
  if (practiceMode) params.set('practice', '1');
  if (activePlatforms.size) params.set('platform', [...activePlatforms].join(','));
  if (activePattern) params.set('pattern', activePattern);
  if (activeCollections.size) params.set('contest', [...activeCollections].join(','));
  const difficulty = difficultyParam();
  if (difficulty) params.set('difficulty', difficulty);
  if (sortDir && !notesActive) params.set('sort', `difficulty-${sortDir}`);
  if (currentUser) {
    if (currentFilter !== 'all') params.set('filter', currentFilter);
    if (similarLibrary) params.set('library', similarLibrary);
    if (libRecall) params.set('recall', libRecall);
    if (libAged) params.set('aged', String(libAged));
    if (libOldest) params.set('order', 'oldest');
  }
  try {
    if (inFlight) inFlight.abort();
    inFlight = new AbortController();
    const res = await fetch(`/api/similar/${encodeURIComponent(problem.id)}?${params}`, { signal: inFlight.signal });
    const data = await res.json();
    if (issuedAt !== lastQueryAt) return;
    if (!res.ok) throw new Error(data.error || `similar unavailable (${res.status})`);
    if (data.source) currentSimilar = data.source;
    let hits = data.hits || [];
    currentTotal = data.total || hits.length;
    if (notesActive) {
      hits = hits.filter(h => {
        const has = !!cosineSheets.noteText(h.problem.id).trim();
        return libNotes === 'yes' ? has : !has;
      });
      currentTotal = hits.length;
      if (sortDir) {
        hits = hits.slice(0, sortWindow).sort((a, b) => {
          const av = cosineDifficulty.value(a.problem), bv = cosineDifficulty.value(b.problem);
          if (av == null || bv == null) return av == null ? (bv == null ? 0 : 1) : -1;
          return sortDir === 'desc' ? bv - av : av - bv;
        });
      } else hits = hits.slice(currentOffset, currentOffset + TOP_K);
    }
    currentRankerAnswered = data.ranker || 'dense';
    const label = (currentSimilar && currentSimilar.title) || sourceTitle;
    const context = practiceMode
      ? ` · recommended practice beyond the source contest${currentUser ? ' · not done' : ' · sign in to exclude solved problems'}`
      : ` · ${activeFacets().join(' · ') || 'all problems'}${similarLibrary ? ` · saved: ${similarLibrary}` : ''}`;
    if (!hits.length) {
      if (!append) {
        resultsEl.innerHTML = '';
        const empty = document.createElement('li');
        empty.className = 'similar-empty';
        // The server knows which filter emptied the list; its sentence is
        // better than ours whenever it sends one.
        empty.textContent = `${data.emptyReason || 'No related problems match these filters.'} `;
        const relax = document.createElement('button');
        relax.type = 'button';
        relax.className = 'lib-chip';
        relax.textContent = 'clear filters and search again';
        relax.addEventListener('click', () => {
          activePattern = '';
          activePlatforms.clear();
          activeCollections.clear();
          activeTiers.clear();
          activeRanges.clear();
          activeAcceptance = null;
          // "Clear filters" has to clear the controls too, or the difficulty
          // row and the competition chips keep claiming a filter that is gone.
          sortDir = null;
          similarLibrary = null;
          libAged = null;
          libOldest = false;
          libRecall = null;
          libNotes = null;
          currentFilter = practiceMode ? 'notdone' : 'all';
          filterSelect.value = currentFilter;
          updatePatternPill();
          syncJudgeControls();
          syncDifficultyControls();
          renderCollectionControls();
          runSimilar(currentSimilar);
        });
        empty.appendChild(relax);
        resultsEl.appendChild(empty);
      }
      hideLoadMore();
      setStatus(`0 related to "${label}"${context}`);
      return;
    }
    renderHitsList(resultsEl, hits, { append, startIndex: currentOffset, unranked: true, similarMode: true, libraryMode: !!similarLibrary });
    setStatus(`${sortDir ? `top ${hits.length}` : `showing 1–${currentOffset + hits.length}`} of ${currentTotal} related to "${label}"${context}${orderNote()}`);
    if (sortDir || data.sortWindow) hideLoadMore();
    else updateLoadMore();
  } catch (err) {
    if (err.name === 'AbortError' || issuedAt !== lastQueryAt) return;
    setStatus(`error: ${err.message || 'similar unavailable'}`);
    hideLoadMore();
  }
}

// "Was this useful?" — the one-line prompt under results. One answer per
// search; a "no" reveals an optional reason box. Reasons land in the events
// log and surface on /stats.html as the improvement backlog.
const feedbackRow = document.getElementById("feedback-row");
const feedbackAsk = feedbackRow.querySelector(".feedback-ask");
const fbYes = document.getElementById("fb-yes");
const fbNo = document.getElementById("fb-no");
const fbReason = document.getElementById("fb-reason");
const fbSend = document.getElementById("fb-send");
let feedbackSearchId = null;

function hideFeedback() {
  feedbackRow.classList.add("hidden");
}

function offerFeedback(data) {
  if (!data.searchId || !(data.hits || []).length) return hideFeedback();
  feedbackSearchId = data.searchId;
  feedbackAsk.textContent = "// useful?";
  fbYes.classList.remove("hidden");
  fbNo.classList.remove("hidden");
  fbReason.classList.add("hidden");
  fbSend.classList.add("hidden");
  fbReason.value = "";
  feedbackRow.classList.remove("hidden");
}

function sendFeedback(useful, reason) {
  track("search_feedback", {
    searchId: feedbackSearchId,
    useful,
    reason: reason || undefined,
    ranker: currentRankerAnswered || undefined,
    q: (currentQuery || "").slice(0, 100),
  });
  feedbackAsk.textContent = "// thanks, logged.";
  for (const el of [fbYes, fbNo, fbReason, fbSend]) el.classList.add("hidden");
}

fbYes.addEventListener("click", () => sendFeedback(true));
fbNo.addEventListener("click", () => {
  fbYes.classList.add("hidden");
  fbNo.classList.add("hidden");
  fbReason.classList.remove("hidden");
  fbSend.classList.remove("hidden");
  fbReason.focus();
});
fbSend.addEventListener("click", () => sendFeedback(false, fbReason.value.trim()));
fbReason.addEventListener("keydown", (e) => {
  if (e.key === "Enter") {
    e.preventDefault();
    sendFeedback(false, fbReason.value.trim());
  }
});

const patternPill = document.getElementById("pattern-pill");
patternPill.addEventListener("click", () => clearPatternFilter());

// Pattern chips narrow search results to problems carrying that label (the
// server filters post-rank). The pill under the status line shows the active
// label; clicking it clears it. Judges need no such pill — their own chips
// show which are on and carry the clear button.
function applyPatternFilter(pattern) {
  track("pattern_selected", { pattern });
  activePattern = pattern;
  updatePatternPill();
  // No slug-as-query substitution any more. It used to put "line sweep" in the
  // box so BM25 had something to rank, which meant the search box filled with
  // words you never typed — and clearing them dead-ended on a blank page. The
  // server browses a filter with no query now, so the box stays yours.
  currentOffset = 0;
  reissueCurrentView();
}

function clearPatternFilter({ reissue = true } = {}) {
  if (!activePattern) return;
  activePattern = "";
  updatePatternPill();
  syncUrl();
  if (reissue) {
    currentOffset = 0;
    reissueCurrentView();
  }
}

// The address bar mirrors what you're looking at. It used to be read-only —
// deep links worked, but only if you typed one by hand, so a refresh threw away
// your query, your judges and your filter.
//
// replaceState by default: runSearch fires on every debounced keystroke, so
// pushing would bury the real previous page under "g", "gr", "gra". Back still
// leaves the app in one step, which is what people expect from a search box.
//
// push:true is the one exception, and only adding or removing a competition
// passes it. Picking a collection is a deliberate, discrete act — you clicked
// one thing, once — so it earns a history entry, and Back undoes exactly it.
// Judges and patterns stay on replaceState for now; extending this is a
// follow-up, not an oversight.
//
// Offset is deliberately absent — restoring page 5 would silently refetch
// everything above it.
function syncUrl({ push = false } = {}) {
  const p = new URLSearchParams();
  if (currentQuery) p.set("q", currentQuery);
  if (currentSimilar) {
    p.set("similar", currentSimilar.id);
    if (similarLibrary) p.set("library", similarLibrary);
    if (practiceMode) p.set("practice", "1");
  }
  if (activeCollections.size) p.set("contest", [...activeCollections].join(","));
  if (contestView) p.set("view", "contest");
  if (activePattern) p.set("pattern", activePattern);
  if (activePlatforms.size) p.set("platform", [...activePlatforms].join(","));
  const dParam = difficultyParam();
  if (dParam) p.set("difficulty", dParam);
  if (sortDir) p.set("sort", `difficulty-${sortDir}`);
  // Library-only state, written only when a library view is open so a plain
  // search URL never carries stale revision filters.
  if (currentUser && (libraryCommand(currentQuery) || currentSimilar)) {
    if (libAged) p.set("aged", String(libAged));
    if (libOldest) p.set("order", "oldest");
    if (libRecall) p.set("recall", libRecall);
    if (libNotes) p.set("notes", libNotes);
  }
  if (activeRanker) p.set("ranker", activeRanker);
  if (currentUser && currentFilter !== "all") p.set("filter", currentFilter);
  const qs = p.toString();
  const search = qs ? `?${qs}` : "";
  const next = location.pathname + search + location.hash;
  // Whatever we just wrote is, by definition, already applied — popstate
  // compares against this so a hash change never re-runs the whole view.
  lastAppliedSearch = search;
  if (next !== location.pathname + location.search + location.hash) {
    if (push) history.pushState({ cosine: 1 }, "", next);
    else history.replaceState(null, "", next);
  }
}

function updatePatternPill() {
  if (activePattern) {
    patternPill.textContent = `pattern: ${activePattern} ✕`;
    patternPill.classList.remove("hidden");
  } else {
    patternPill.classList.add("hidden");
  }
}

// The [lc] [cf] [atc] [cses] badge on every card doubles as the judge filter —
// click to narrow, click again to drop it, several at once to union them. Same
// post-rank filter as pattern chips, so it composes with them for free.
function togglePlatformFilter(platform) {
  if (activePlatforms.size === 0) {
    // Everything was included, so clicking one judge means "just this one" —
    // not "all except this one", which is what a plain checkbox would do and
    // is almost never what someone clicking a judge wants.
    activePlatforms.add(platform);
  } else if (activePlatforms.has(platform)) {
    // Turning off the last active judge lands back on "all", never on none.
    activePlatforms.delete(platform);
  } else {
    activePlatforms.add(platform);
  }
  track("platform_selected", { platform, active: [...activePlatforms].join(",") });
  syncJudgeControls();
  currentOffset = 0;
  reissueCurrentView();
}

function clearPlatformFilter({ reissue = true } = {}) {
  if (!activePlatforms.size) return;
  activePlatforms.clear();
  syncJudgeControls();
  syncUrl();
  if (reissue) {
    currentOffset = 0;
    reissueCurrentView();
  }
}

// The manual, as sections rather than one scroll. `:help` is an index plus
// the three lines that get someone searching; `:help filters` is one section.
// Addressable on purpose: the previous 180-line wall meant the answer to
// "can I see what I bookmarked but never solved?" was in there and nobody
// read far enough to find it.
//
// Kept as plain text in a <pre> (no HTML, so nothing here can inject) and
// wrapped to 64 columns, because `white-space: pre` scrolls sideways on a
// phone at any width the wrapper doesn't control.
const HELP_SECTIONS = [
  {
    name: "search",
    blurb: "the three modes, and similar vs practice",
    body: `SEARCH — pick a mode next to the box

  keyword   matches words in the title, the statement AND our
            technique labels. A problem that opens "Alice and
            Bob play a game..." never says "dp" — but its label
            does, so "game theory dp" still finds it. Best when
            you know the terms.

  meaning   describe it in plain english. "thief robbing
            houses" finds House Robber; "check if brackets
            close in order" finds Valid Parentheses. Best when
            you remember the story, not the words. It will also
            answer a word no problem contains — "rat" finds Cat
            and Mouse — and says so, because "nearest by
            meaning" is a weaker claim than a match.

  A problem's exact name goes to the top: "two sum" and "2 sum"
  both land on Two Sum. In keyword mode a word that appears
  nowhere in the corpus says so rather than guessing; a
  keyboard mash gets nothing in either mode.

  Community names expand on their own: type "aliens trick" and
  the status line shows "+wqs binary search" — you get the
  results and the real name.

FIND SIMILAR vs PRACTICE THIS IDEA
  both links sit inside an expanded result and both rank the
  corpus by how close a problem is to that one. The difference
  is what each leaves out.

  "find similar problems" leaves out nothing. Your judge,
  label, difficulty, competition chips and saved scope all stay
  on, problems from the same contest still appear, and so do
  ones you have already done. Use it to read around a problem.

  "practice this idea" is for training, so it removes what you
  would be practising against unfairly. It drops the contest
  and collection the problem came from, clears your competition
  chips and saved scope, and hides anything you have marked
  done. Judge, label and difficulty stay. Use it when you want
  the same technique on a problem you have not seen.

  So: same problem, wider net vs same idea, somewhere new.

  Either way the source and your filters stay in the URL, so
  the view is shareable and Back returns you to it. Results
  paginate, shared techniques show inside expanded cards, and
  a recommendation is never dressed up as a real past question.

BROWSE
  a filter with no query lists everything it selects. Clear the
  box while a label or a judge is on and you get the whole set,
  paged.

CORPUS
  Judge badges identify the original platform. Verified PYQs
  also include narrow CodeChef and Kattis collections.
  Deliberately hard: no LeetCode Easy, Codeforces and AtCoder
  stratified from 1300 up — the number on the card is the
  rating.`,
  },
  {
    name: "patterns",
    blurb: "the technique vocabulary",
    body: `PATTERNS — what a problem IS, not what it says

  Statements hide their technique on purpose. The labels don't,
  which is why searching for one works at all.

  /patterns.html lists every label with counts, filterable.
  Type "dp" there and you get the whole family: digit-dp,
  tree-dp, slope-trick, state-compression. Click one to browse
  the problems carrying it. Useful when your exposure stops at
  one sheet and you don't yet know what to search for.

  Every expanded result lists its labels — click one to narrow
  to it; the pill clears it.

  They start hidden, because the label IS the answer: reading
  "binary search on the answer" before you attempt a problem
  ends the problem. A card offers "3 technique labels · show"
  instead — click that to open one card, or the "labels:"
  switch beside :help to open every card.

  Only the labels are hidden. The difficulty, the judge's own
  tags and the statement all stay. The switch is remembered on
  your account when you are signed in, in this browser when
  you are not; a card you opened by hand lasts this visit.

  Clear the query and the label stays: you are browsing every
  problem carrying it. Type a new query and the label drops —
  it was a drill-down into what you were reading, and most
  labels are narrow enough that keeping it would find nothing.
  Judges are not like this: they stay until you drop them.
  A card that says "labels pending review" is a problem we
  have indexed by its statement and the judge's own tags and
  have not solved ourselves yet. It never matches a technique
  filter, because it carries none of our labels; it does
  match the words in it.
`,
  },
  {
    name: "filters",
    blurb: "judges, CSES bands, difficulty, level, PYQs",
    body: `FILTERS — they stack

  A filter is a set, not a radio button: pick as many as you
  like. The status line spells out what is narrowing the view,
  and all of it lands in the URL, so a refresh keeps it and the
  link shares exactly what you see.

  judges       the platform chips above the results, or the
               [lc] tag on any card. All judges are included
               until you narrow. Turning the last one off
               returns to all judges, so this filter can
               never find nothing. "all ✕" resets.

  difficulty   appears under the judges, in each judge's own
               scale: lc has three tiers, cf and atc a rating
               range you set both ends of — "cf 1500 to 1500"
               is exactly 1500. There is no shared scale across
               judges, so a difficulty only ever filters its
               own judge: narrowing cf to 1500 leaves your
               LeetCode results untouched rather than deleting
               them. Drop the judge and its difficulty goes
               with it.

  CSES         five estimated bands, independent of ratings:
               Foundation, Standard, Intermediate, Advanced,
               Expert. CSES publishes no difficulty, so these
               are estimates and every card says so: two
               independent solution reviews per task, the band
               is their rounded mean, and 14 specialist checks
               with a proof or a computation re-examined the
               hardest ones; six of those moved a band.
               Confidence is how far the two reviews agreed —
               high, both chose the band; medium, one band
               apart; low, a computation had to settle it. That
               is agreement between reviews, not human
               calibration, and it converts to no Codeforces
               rating. Choose "my CSES level" explicitly and it
               filters at once; your account saves the choice,
               or it stays in this browser while signed out.

  PYQs         add one or more competition collections. These
               combine with every other filter, and a card shows
               which competition it came from. Resource links
               stay available even when a round has no
               searchable problem statements.
               With one competition on, "contest page" in the
               resources panel lists every problem in the set,
               indexed or not.

  ac           pick a LeetCode tier and an acceptance-rate
               range appears under it: "hard" + "ac 10% to 30%"
               is the hardest Hards. Lower acceptance means
               harder. It appears only after a tier is chosen,
               because across tiers it doesn't compare — most
               Mediums here were picked FOR a low acceptance
               rate and every Hard came in regardless, so a 15%
               Medium outranking a 60% Hard would say more
               about how this corpus was built than about the
               problems.

  sort         with ONE judge selected: easiest or hardest
               first. Two judges have no shared order — nothing
               places a Medium against a 1600 — so it is
               offered only when it means something. Unrated
               problems sort last either way. While searching
               it reorders the top N (20/50/100) rather than
               discarding the ranking, so there is no next
               page; browsing sorts everything and pages. On
               LeetCode, acceptance rate breaks the tie inside
               a tier — otherwise "easiest first" is 661
               Mediums in no particular order.

  my level     appears when your profile has stats for a judge
               you have selected, and sets that judge's band
               from its own scale: Codeforces and AtCoder from
               your rating (your rating to +200 — a problem at
               your rating is roughly a coin flip, so the band
               is winnable but not free), LeetCode from your
               solved counts, since it publishes no rating.
               Hover it for the reasoning and the count; press
               it again to drop it.

  pattern      click a technique label inside a result

  IN THE LIBRARY                                   (signed in)

  all / not done / done   the dropdown next to the ranker

  marked       1mo+ / 3mo+ / 6mo+ keep only problems you marked
               at least that long ago, and "oldest first"
               starts from the longest ago. The age follows the
               view: :done by when you finished, :bookmarks by
               when you saved.

  recall       a dropdown beside the age chips: again / hard /
               medium / easy, or "unrated" for everything you
               never rated. See ":help saving".

  notes        written up / no note. Appears once a sheet is
               connected, because the note is in the sheet and
               this is the only filter the server can't answer.

  pick one     opens one of whatever is on screen, at random.
               Composes with everything above, so ":done" +
               "again" + "3mo+" + pick one is a revision
               session in four clicks.

  A LIBRARY VIEW TAKES A QUERY. ":done graph" lists the graph
  problems you have finished; ":bookmarks segment tree" the
  ones you saved. It matches titles and technique labels, not
  statements — a filter, not a search — and every word has to
  be there. Plurals work the way they do everywhere else.

  These compose. ":bookmarks" with cf+atc selected and "not
  done" is your unfinished Codeforces and AtCoder saves.
  ":done" with "again" and "3mo+" is a revision queue.

  Library filters are library-only: type an ordinary query and
  they drop, so a rating or an age can never quietly follow you
  into a search and delete results you meant to see.`,
  },
  {
    name: "saving",
    blurb: "bookmarks, done, and how the solve went",
    body: `SAVING                                             (signed in)

  ☆ / ★   bookmark a problem, on any result card
  ○ / ✓   mark it done — done marks feed your heatmap

  In your library, a saved problem grows a third chip: how it
  went. Tap it to cycle

    ·  →  A again  →  H hard  →  M medium  →  E easy  →  ·

  One letter, so the buttons don't change size under your
  thumb as you rate a page; the colour is the part you read.
  It only appears in :bookmarks / :done / :all — an ordinary
  search result keeps its two buttons.

  It saves as you tap, without waiting. If the save fails the
  letter goes back to what it was and the status line says so.

  It is optional and nothing is scheduled off it — it exists
  so that ":done" plus "again" is a list worth reopening.

  Rating does NOT change when you solved it, so re-rating an
  old solve never moves it out of "marked 3mo+".

  Un-bookmark AND un-mark the same problem and it leaves your
  library — but the rating is KEPT. Save it again months later
  and your "again" is still on it.

  ✎       write a note. It appears on the card you just
          marked, and on every card in your library.

  The editor is a plain box with markers that survive being
  put in a spreadsheet cell:

    **bold**   \`code\`   \`\`\` fenced blocks   - bullets

  ctrl+b, ctrl+e and the buttons above the box insert them;
  Tab indents, ctrl+enter saves. What you type is exactly
  what lands in the cell — no formatting to lose.

  Saving is instant and local. The note is in this browser
  the moment you press save, shows on the card straight away,
  and the next sync carries it into your sheet. You never
  press sync to save a note; the button only exists for the
  case where the sheet cannot be reached.

  Two things people ask for that already exist:

    ":bookmarks" with "not done" is everything you saved and
    never solved.

    Your sheet already has columns for status, time taken,
    concept, tactics, solution summary and notes — and you
    never type a row into it by hand. See ":help sheet".`,
  },
  {
    name: "sheet",
    blurb: "your notes, in your own Google Sheet",
    body: `SHEET — the sheet is the notebook, the site is the index

  "connect sheet" in the library bar makes a Google Sheet named
  "cosine notes" in YOUR Drive. This app created it, and it is
  the only file this app can see (drive.file scope — not your
  Drive). Nothing is stored here: the Google token lives in
  your browser tab and the notes live in your sheet. This
  server never sees either.

  You never add a row by hand. Bookmark or tick done on the
  site and sync writes the row for you. It writes six columns
  and no more:

    problem_id  title  link  judge  difficulty  recall

  — enough to know which problem a row is and to open it. It
  does NOT write "bookmarked" or "done": the site owns those,
  the site shows them, and a column reading "yes" is a second
  place to look for something you already know.

  EVERYTHING ELSE IS YOURS. A new sheet starts with one more
  column, "solution summary", because it is the one people
  reread — and it is the ONE column the app will write into,
  only ever with a note you typed here, only in the cell for
  that problem (see ":help saving").

  Add whatever else you want — concept, time taken, revision
  date, a column of your own name for anything — and
  the site reads it and shows it on the card under the header
  you gave it. It never writes, blanks or deletes a cell of
  yours.

  Only one thing flows from the sheet back to the site:
  DISPLAY. What you write shows up on the expanded card (✎
  marks an annotated problem). Nothing you type in the sheet
  bookmarks a problem, marks it done or rates it — one writer
  per cell, in one direction, which is why there is nothing to
  merge and no conflict to resolve.

  Rows are never removed. Un-bookmark a problem and its row
  stays exactly as you left it, with everything you wrote —
  the app simply stops updating it. Delete the row yourself if
  you want it gone; save the problem again and the app finds
  the row by its problem_id and picks up where it left off.

  Sync keeps one layout: the site's columns first, then yours
  in the order you have them. Columns are MOVED, not rewritten,
  so formulas and formatting travel with them. It removes only
  two kinds of column: a duplicate with nothing in it, and one
  of its OWN columns it no longer writes (older sheets have
  "done", "done_at" and "bookmarked" — a frozen "yes" is worse
  than no column at all).

  Google asks for your permission exactly ONCE, the first time
  you connect, on a click. After that the sheet keeps itself
  up to date: a few seconds after you bookmark, tick done or
  rate something, the row is written. You should not have to
  press sync again, and you should never see a Google dialog
  again.

  How that works, since the token is never stored anywhere:
  each page load asks Google for a new one in the mode that is
  not allowed to display anything. If it can be answered
  without a question, the sheet syncs; if it can't — signed
  out, permission revoked, several Google accounts and no way
  to know which — it fails, nothing appears, and nothing
  syncs. The sync button is there for exactly that case, and
  pressing it puts things back.

  A refresh must never put a Google dialog in front of you. If
  one ever does, the app stops asking on this browser from
  then on.

  Notes you have already synced are cached in this browser, so
  a refresh shows them without contacting Google at all.

  Your cosine login and the Google account holding the sheet
  are independent. Connect a DIFFERENT Google account and the
  site says so plainly: that account cannot see the sheet,
  which is sitting safely in the first one.`,
  },
  {
    name: "commands",
    blurb: "everything that starts with a colon",
    body: `COMMANDS — a leading ":" means command, never a search

  So a typo like ":bo" tells you it isn't a command instead of
  spending a round trip searching the corpus for it.

  :help :h          this manual
  :help <section>   one section: search, patterns, filters,
                    saving, sheet, commands
  :compare :cmp     ":compare knapsack" runs the query in
                    keyword and meaning mode side by side, with
                    rank deltas. Any ordinary search leaves
                    compare mode.
  :bookmarks :b     starred problems              (signed in)
  :done :d          problems marked done          (signed in)
  :all :lib         everything saved              (signed in)
  :done <words>     the saved problems that match, e.g.
                    ":done graph" or ":bookmarks segment tree"
  Tab               cycle library views           (signed in)

LINKS
  the address bar follows what you are looking at — query,
  judges, difficulty, sort, pattern, ranker and library filters
  all land in it, so a refresh keeps your view and copying the
  URL shares exactly what you see:

    /?q=knapsack&platform=codeforces,atcoder&ranker=dense

MORE
  handles + combined heatmap: /profile.html
  live usage + latency:       /stats.html
  scoring math:               /debug.html
  404 page game:              /404.html`,
  },
];

const HELP_INDEX = `COSINE(1)                                          the manual

  A search engine for practice problems. Ask for a technique,
  describe the problem in plain english, or type the name you
  half-remember — it handles all three, and says so when a word
  appears nowhere in the corpus.

SECTIONS
${HELP_SECTIONS.map((s) => `  :help ${s.name.padEnd(11)}${s.blurb}`).join("\n")}

TRY
  two sum                exact names go to the top
  thief robbing houses   describe it, in "meaning" mode
  monotonic stack        a technique, not a word in the
                         statement
  :bookmarks             what you saved            (signed in)`;

// ":help", ":h", or either with one section name after it. Returns null when
// this isn't a help command at all, "" for the index, or the argument as
// typed — an unknown one falls back to the index rather than an error, since
// the index is the answer to "what can I ask for?" anyway.
function helpQuery(q) {
  const t = q.trim();
  // Bare "help" counts too: it showed up in the zero-hit query log, typed by
  // someone who did not know about the colon. Bare "h" does not — it is one
  // keystroke from a real query.
  const m = /^:(?:help|h)(?:\s+(.*))?$/i.exec(t) || /^help(?:\s+(.*))?$/i.exec(t);
  return m ? (m[1] || "").trim().toLowerCase() : null;
}

function renderHelp(sectionName) {
  track("help_opened", { section: sectionName || "" });
  if (compareMode) {
    compareMode = false;
    applyMode();
  }
  clearPatternFilter({ reissue: false });
  hideLoadMore();
  hideFeedback();
  currentSearchId = null;
  currentRankerAnswered = "";
  const section = HELP_SECTIONS.find((sec) => sec.name === sectionName);
  if (currentUser) setLibPath(section ? `~/help/${section.name}` : "~/help");
  setStatus(section ? `man cosine ${section.name}` : "man cosine");
  resultsEl.innerHTML = "";
  const li = document.createElement("li");
  li.className = "result help-block";
  li.setAttribute("data-rank", "[man]");
  const pre = document.createElement("pre");
  pre.className = "help-man";
  pre.textContent = section
    ? `${section.body}\n\n  ← :help for the index`
    : HELP_INDEX;
  li.appendChild(pre);
  resultsEl.appendChild(li);
}

function updateLoadMore() {
  const shown = currentOffset + TOP_K;
  if (currentTotal > 0 && shown < currentTotal) {
    loadMoreEl.classList.remove("hidden");
    const remaining = currentTotal - shown;
    loadMoreEl.textContent = `load more (${remaining} remaining)`;
  } else {
    hideLoadMore();
  }
}

function hideLoadMore() {
  loadMoreEl.classList.add("hidden");
}

async function runCompare(q) {
  const issuedAt = ++lastQueryAt;
  hideFeedback();
  if (currentUser) setLibPath(`~/compare "${q.length > 24 ? q.slice(0, 24) + "…" : q}"`);
  // Same deal as runSearch: compare runs on every keystroke too, so announcing
  // it up front animated a line nobody had time to read.
  clearTimeout(searchingTimer);
  searchingTimer = setTimeout(() => {
    if (issuedAt !== lastQueryAt) return;
    clearTimeout(typeTimer);
    statusEl.textContent = `comparing: "${q}"`;
  }, SEARCHING_AFTER_MS);
  hideLoadMore();

  let data;
  try {
    if (inFlight) inFlight.abort();
    inFlight = new AbortController();
    const res = await fetch(
      `/api/compare?q=${encodeURIComponent(q)}&k=10&rankers=${COMPARE_RANKERS.join(",")}`,
      { signal: inFlight.signal }
    );
    data = await res.json();
  } catch (err) {
    if (err.name === "AbortError" || issuedAt !== lastQueryAt) return;
    clearTimeout(searchingTimer);
    setStatus(`error: ${err.message || "compare failed"}`);
    return;
  }
  if (issuedAt !== lastQueryAt) return;
  renderCompare(data, q);
}

function renderCompare(data, q) {
  hideLoadMore(); // compare has no pagination; clear any leftover button
  const results = data.results || [];
  if (results.length === 0) { setStatus("no rankers configured"); compareEl.innerHTML = ""; return; }
  const rankMaps = results.map((r) => {
    const m = new Map();
    r.hits.forEach((h, i) => m.set(h.problem.id, i + 1));
    return m;
  });
  const totalHits = results.reduce((s, r) => s + r.hits.length, 0);
  if (totalHits === 0) { setStatus(`0 hits for "${q}"`); compareEl.innerHTML = ""; latencySummaryEl.textContent = ""; return; }
  const expanded = describeExpansion(q, data.expandedQuery);
  const contestNote = activeCollections.size ? " · collections do not apply to :compare" : "";
  setStatus(`compare: "${q}"${expanded}${contestNote}`);
  latencySummaryEl.textContent = results.map((r) => `${r.ranker} ${r.latencyMs.toFixed(3)}ms`).join("  ·  ");
  compareEl.innerHTML = "";
  results.forEach((r, idx) => {
    const col = document.createElement("section");
    col.className = "compare-col";
    const head = document.createElement("div");
    head.className = "compare-col-head";
    head.innerHTML = `<span class="ranker-name">${escapeHtml(r.ranker)}</span><span class="ranker-latency" title="scoring latency for this query">${r.latencyMs.toFixed(3)}ms</span>`;
    col.appendChild(head);
    const list = document.createElement("ul");
    list.className = "compare-list";
    col.appendChild(list);
    if (r.hits.length === 0) {
      const empty = document.createElement("li"); empty.className = "compare-empty"; empty.textContent = "no hits"; list.appendChild(empty);
    } else {
      const otherIdx = idx === 0 ? 1 : 0;
      const otherMap = rankMaps[otherIdx];
      const otherName = results[otherIdx]?.ranker || "other";
      renderHitsList(list, r.hits, { otherRankMap: otherMap, otherName });
    }
    compareEl.appendChild(col);
  });
}

function setStatus(text) {
  clearTimeout(typeTimer);
  clearTimeout(searchingTimer);
  // The cursor shows only while the line is typing itself out. A blinking
  // block sitting under the box at rest reads as "type here" — a real user
  // lost minutes to exactly that.
  if (reduceMotion) {
    statusEl.textContent = text;
    return;
  }
  let i = 0;
  const tick = () => {
    i = Math.min(i + 1, text.length);
    const done = i >= text.length;
    statusEl.innerHTML = escapeHtml(text.slice(0, i)) + (done ? "" : '<span class="cursor">_</span>');
    if (!done) typeTimer = setTimeout(tick, 12);
  };
  tick();
}

// Two difficulty scales share one column: LeetCode's Easy/Medium/Hard (stored
// capitalized — this compared lowercase and silently coloured nothing) and the
// numeric ratings Codeforces and AtCoder use. Rating cuts follow div2 shape:
// A/B grade, C/D, then E and up.
function diffClass(d) {
  if (typeof d === "number") return d < 1600 ? "easy" : d < 2100 ? "medium" : "hard";
  const k = String(d || "").toLowerCase();
  return k === "easy" || k === "medium" || k === "hard" ? k : "";
}

// How each community actually refers to its judge, short enough to sit inline.
const PLATFORM_LABELS = {
  leetcode: ["lc", "LeetCode"],
  codeforces: ["cf", "Codeforces"],
  atcoder: ["atc", "AtCoder"],
  cses: ["cses", "CSES"],
  codechef: ["cc", "CodeChef"],
  kattis: ["kattis", "Kattis"],
};

function platformBadge(platform) {
  const [short, full] = PLATFORM_LABELS[platform] || [platform, platform];
  if (!short) return "";
  const on = activePlatforms.has(platform);
  return `<button type="button" class="platform-badge${on ? " active" : ""}" data-platform="${escapeHtml(platform)}"
    title="${escapeHtml(on ? `stop filtering to ${full}` : `only ${full}`)}">${escapeHtml(short)}</button>`;
}

// Where a problem came from, when it came from a contest we track. Three
// endpoints have shipped hit.competitions for a while and nothing rendered it,
// so the only way to discover that a problem you found by searching was an
// ICPC World Finals question was to already have the collection selected.
//
// A problem can genuinely belong to two contests — Luxor ran the 2022 and 2023
// World Finals together and five problems were in both — so the first two
// memberships get a chip each; only past two does it compress to "+N".
function competitionTag(competitions) {
  const list = competitions || [];
  if (!list.length) return "";
  const shown = list.slice(0, 2);
  const rest = list.length - shown.length;
  const chips = shown.map((c) => `<button type="button" class="competition-tag" data-collection="${escapeHtml(c.id)}"
    title="${escapeHtml(`${c.name} — filter to this collection`)}">${escapeHtml(c.short || c.name)}</button>`);
  if (rest > 0) {
    const others = list.slice(2).map((c) => c.name).join(" · ");
    chips.push(`<span class="competition-tag competition-more" title="${escapeHtml(others)}">+${rest}</span>`);
  }
  return chips.join("");
}

// Badge wording deliberately leads with "vs <other>" — the old form put the
// other ranker's name first and read as a label for the card's own column.
function rankDeltaBadge(thisRank, otherRank, otherName) {
  if (otherRank == null) return `<span class="rank-delta absent" title="not in ${escapeHtml(otherName)}'s top 10">vs ${escapeHtml(otherName)}: –</span>`;
  if (otherRank === thisRank) return `<span class="rank-delta same" title="same rank in ${escapeHtml(otherName)}">vs ${escapeHtml(otherName)}: =</span>`;
  if (otherRank > thisRank) return `<span class="rank-delta up" title="${escapeHtml(otherName)} ranks this #${otherRank}">vs ${escapeHtml(otherName)}: ↑${otherRank - thisRank}</span>`;
  return `<span class="rank-delta down" title="${escapeHtml(otherName)} ranks this #${otherRank}">vs ${escapeHtml(otherName)}: ↓${thisRank - otherRank}</span>`;
}

// A matched term that IS one of this card's labels is the hint, spelled out on
// the card while the labels themselves are withheld. Searching for "dp" must
// not be the way around the switch. Title and statement words still show.
function visibleMatchedTerms(hit, revealed) {
  const terms = hit.matchedTerms || [];
  if (revealed || showLabels) return terms;
  const labels = new Set((hit.problem.patterns || []).map((p) => String(p).toLowerCase()));
  return terms.filter((t) => !labels.has(String(t).toLowerCase()));
}

// Hidden means the labels are not in the document at all. A blur or a
// `color: transparent` is still selectable, copyable, findable with ctrl-F and
// read aloud by a screen reader — which is not hiding anything, it is only
// making it awkward to read for the people who can read it at all.
//
// `onReveal` lets the card repaint the other two places its labels leak into
// (the matched line and the "Also labelled" caption) when this one is opened.
function renderPatternsInto(el, problem, revealed, onReveal) {
  const patterns = problem.patterns || [];
  // A labels-pending record (scripts/publish_pending.py) has the statement
  // and the judge's tags and none of our labels yet. A reveal button that
  // reveals nothing would be worse than the honest sentence.
  if (problem.review_status === 'labels-pending') {
    el.hidden = false;
    el.innerHTML = '<span class="labels-pending">labels pending review</span>';
    return;
  }
  // No labels at all: no paragraph, and above all no "0 technique labels"
  // button promising something to reveal.
  el.hidden = patterns.length === 0;
  if (!patterns.length) { el.innerHTML = ''; return; }
  if (!revealed && !showLabels) {
    const n = patterns.length;
    el.innerHTML = `<button type="button" class="reveal-labels" data-problem-id="${escapeHtml(problem.id)}">${n} technique label${n === 1 ? '' : 's'} · show</button>`;
    el.querySelector('.reveal-labels').addEventListener('click', (e) => {
      // The card header toggles the panel on click; revealing a label is not
      // asking to collapse the problem you are reading.
      e.stopPropagation();
      revealedCards.add(problem.id);
      track("labels_revealed", { problemId: problem.id });
      renderPatternsInto(el, problem, true, onReveal);
      if (onReveal) onReveal();
    });
    return;
  }
  el.innerHTML = `<strong>patterns:</strong> ${patterns
    .map((p) => `<button type="button" class="pattern-chip" data-pattern="${escapeHtml(p)}" title="filter results by this label">${escapeHtml(p)}</button>`)
    .join(' ')}`;
  el.querySelectorAll('.pattern-chip').forEach((btn) => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      applyPatternFilter(btn.dataset.pattern);
    });
  });
}

function renderHitsList(container, hits, opts = {}) {
  if (!opts.append) container.innerHTML = "";
  const startIndex = opts.startIndex || 0;
  const libraryMode = !!opts.libraryMode;
  // A browse has no ranking, so a relevance bar would be drawing a number that
  // doesn't exist. Library lists are the same — they're ordered by when you
  // saved something, not by score.
  const ranked = !opts.unranked && !libraryMode && !opts.similarMode;
  // :compare ignores the contest filter on the server — it is a ranker lens,
  // not a browse — so hiding hints there would blank half the comparison for a
  // filter that isn't being applied.
  // The resources panel is rendered by the chip lifecycle, which runs before a
  // view resolves — so its one sentence is refreshed here, where we finally
  // know whether these results are collection members or recommendations.
  const collectionNoteEl = document.getElementById("collection-note");
  if (collectionNoteEl) collectionNoteEl.textContent = collectionNote();
  currentTopScore = hits.reduce(
    (m, h) => (typeof h.score === "number" ? Math.max(m, h.score) : m),
    currentTopScore
  );
  const topScore = currentTopScore;

  hits.forEach((hit, i) => {
    const li = document.createElement("li");
    li.className = "result";
    li.dataset.problemId = hit.problem.id;   // so a saved note can repaint one card
    const rank = String(startIndex + i + 1).padStart(2, "0");
    li.setAttribute("data-rank", `[${rank}]`);
    li.style.animationDelay = `${Math.min(i, 8) * 35}ms`;

    const header = document.createElement("div");
    header.className = "result-header";

    const title = document.createElement("span");
    title.className = "result-title";
    title.textContent = hit.problem.title;

    const meta = document.createElement("span");
    meta.className = "result-meta";
    const diff = cosineDifficulty.format(hit.problem);
    // No raw score on cards. It read as a precise "similarity %" it never was,
    // and the same 4-decimal number meant a BM25 score in one view and a
    // cosine in another. The bar below still shows relative strength; exact
    // numbers live on /debug.html where they're explained.
    const trailing = libraryMode ? formatRelative(hit.markedAt) : "";
    // CSES ships no difficulty, so this used to render an empty bordered chip —
    // visible furniture standing in for nothing.
    // CSES bands are estimates, so the chip carries how much the two reviews
    // agreed: the class for CSS, the title for the person reading it.
    const isCses = hit.problem.platform === "cses";
    const csesConfidence = isCses ? cosineDifficulty.confidence(hit.problem) : null;
    const csesClass = `cses-estimate${csesConfidence ? ` cses-confidence-${csesConfidence}` : ""}`;
    const csesTitle = csesConfidence ? ` title="${escapeHtml(cosineDifficulty.confidenceTitle(csesConfidence))}"` : "";
    // Kattis's own score rides the same three colour classes; the title says
    // whose number it is, since a "7.4" next to Codeforces ratings invites a
    // comparison it cannot bear.
    const isKattis = hit.problem.platform === "kattis";
    const kattisClass = isKattis ? cosineDifficulty.kattisLabel(hit.problem) : "";
    const kattisTitle = isKattis ? ' title="Kattis\u2019s own 1\u201310 difficulty score \u2014 not a rating"' : "";
    const diffClassName = isCses ? csesClass : isKattis ? kattisClass : diffClass(hit.problem.difficulty);
    const diffTitle = isCses ? csesTitle : isKattis ? kattisTitle : "";
    const diffHtml = diff === "" ? "" : `<span class="difficulty ${diffClassName}"${diffTitle}>${escapeHtml(String(diff))}</span>`;
    // Tier one of the CodeChef ingest: searchable, but nobody here has solved
    // it, so it says so where the labels would otherwise be trusted.
    const pendingChip = hit.problem.review_status === "labels-pending"
      ? '<span class="review-pending" title="statement and judge tags only \u2014 nobody here has solved this yet">pending</span>'
      : "";
    let metaHtml = platformBadge(hit.problem.platform) + competitionTag(hit.competitions) + pendingChip + diffHtml + escapeHtml(trailing);
    if (typeof cosineSheets !== "undefined" && cosineSheets.connected()) {
      const note = cosineSheets.noteFor(hit.problem.id);
      const hasNotes = note && cosineSheets.userColumns().some((fld) => (note[fld.key] || "").trim());
      if (hasNotes) metaHtml += '<span class="note-mark" title="has notes in your sheet">✎</span>';
    }
    if (opts.otherRankMap) {
      const other = opts.otherRankMap.get(hit.problem.id);
      metaHtml = rankDeltaBadge(i + 1, other, opts.otherName) + metaHtml;
    }
    meta.innerHTML = metaHtml;
    // The badge lives inside the header, which toggles the card open — so the
    // filter click has to stop there or every judge filter also expands a result.
    meta.querySelectorAll(".platform-badge").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        e.stopPropagation();
        togglePlatformFilter(btn.dataset.platform);
      });
    });
    meta.querySelectorAll(".competition-tag").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        e.stopPropagation();
        addCollection(btn.dataset.collection);
      });
    });

    header.appendChild(title);
    header.appendChild(meta);

    if (currentUser) {
      header.appendChild(buildActions(hit, libraryMode));
    }

    const bar = document.createElement("div");
    bar.className = "score-bar";
    const fill = document.createElement("div");
    fill.className = "score-bar-fill";
    bar.appendChild(fill);
    if (!ranked) bar.classList.add("hidden");

    const matched = document.createElement("div");
    matched.className = "result-matched";
    // Repainted on reveal: the line is built from the terms this card is
    // allowed to name, and revealing the labels changes that set.
    const paintMatched = () => {
      matched.innerHTML = "";
      const terms = visibleMatchedTerms(hit, revealedCards.has(hit.problem.id));
      for (const t of terms) {
        const chip = document.createElement("span");
        chip.className = "matched-chip";
        chip.textContent = t;
        matched.appendChild(chip);
      }
      // Every term was a label: the line has nothing left to say, but the node
      // stays so a reveal can fill it back in.
      matched.hidden = terms.length === 0;
    };
    paintMatched();

    const detail = document.createElement("div");
    // Only the labels are hints. Blacking out the whole panel also hid the
    // statement — the thing you are meant to sit and attempt — and the
    // "find similar / practice this idea" links out of it.
    detail.className = "result-detail hidden";
    detail.id = `detail-${hit.problem.id}-${startIndex + i}`;
    title.tabIndex = 0;
    title.setAttribute("role", "button");
    title.setAttribute("aria-expanded", "false");
    title.setAttribute("aria-controls", detail.id);
    // The CSES band and how confident it is already sit on the card, in the
    // difficulty chip and its tooltip. A provenance paragraph repeating them
    // with a review date and a link to the write-up was furniture; what the
    // bands mean now lives in :help, where someone actually goes to ask.
    detail.innerHTML = `
      <p>${escapeHtml(hit.problem.statement || "")}</p>
      <p class="tags"><strong>tags:</strong> ${(hit.problem.tags || []).map(escapeHtml).join(", ")}</p>
      <p class="patterns"></p>
      <p><a href="#" class="similar-link">find similar problems &rarr;</a> · <a href="#" class="practice-link">practice this idea &rarr;</a>${
        hit.problem.source_url
          ? ` · <a href="${escapeHtml(hit.problem.source_url)}" class="external-link" target="_blank" rel="noopener">open original problem &rarr;</a>`
          : ""
      }</p>
    `;
    detail.querySelector(".similar-link").addEventListener("click", (e) => {
      e.preventDefault();
      e.stopPropagation();
      track("similar_opened", { problemId: hit.problem.id, kind: "similar" });
      runSimilar(hit.problem);
    });
    detail.querySelector(".practice-link").addEventListener("click", (e) => {
      e.preventDefault();
      e.stopPropagation();
      track("similar_opened", { problemId: hit.problem.id, kind: "practice" });
      runSimilar(hit.problem, { practice: true });
    });
    // "Also labelled: …" names the labels outright, so it is label content and
    // goes behind the same switch. "Also labelled", not "shared techniques":
    // the overlap is real information, but the order is dense cosine
    // (techniqueWeight is 0), so it must not read as the reason for the ranking.
    const hasSharedTechniques = !!opts.similarMode && (hit.sharedTechniques || []).length > 0;
    const paintSimilarExplanation = () => {
      if (!hasSharedTechniques) return;
      const existing = detail.querySelector(".similar-explanation");
      if (!(revealedCards.has(hit.problem.id) || showLabels)) {
        if (existing) existing.remove();
        return;
      }
      if (existing) return;
      const explanation = document.createElement("p");
      explanation.className = "similar-explanation";
      explanation.textContent = `Also labelled: ${hit.sharedTechniques.join(", ")}`;
      detail.prepend(explanation);
    };
    paintSimilarExplanation();
    renderPatternsInto(
      detail.querySelector(".patterns"),
      hit.problem,
      revealedCards.has(hit.problem.id),
      () => { paintMatched(); paintSimilarExplanation(); }
    );
    // Not gated on a connected sheet any more: a note typed here exists
    // whether or not Google has heard about it yet, and hiding it until it
    // syncs would make saving look like it did nothing.
    if (typeof cosineSheets !== "undefined") {
      const noteView = buildNoteView(hit.problem.id);
      if (noteView) detail.appendChild(noteView);
      detail.classList.add("has-note-slot");
    }

    header.addEventListener("click", () => {
      const opening = detail.classList.contains("hidden");
      detail.classList.toggle("hidden");
      title.setAttribute("aria-expanded", String(opening));
      // The outcome signal: someone cared enough to open this result. Logged
      // once per card; position + searchId make CTR-per-ranker computable.
      if (opening && !li.dataset.opened) {
        li.dataset.opened = "1";
        track("result_open", {
          kind: "expand",
          problemId: hit.problem.id,
          position: startIndex + i + 1,
          searchId: currentSearchId || undefined,
          ranker: currentRankerAnswered || undefined,
        });
      }
    });
    title.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        header.click();
      }
    });
    const externalLink = detail.querySelector(".external-link");
    if (externalLink) {
      externalLink.addEventListener("click", () => {
        track("result_open", {
          kind: "external",
          problemId: hit.problem.id,
          position: startIndex + i + 1,
          searchId: currentSearchId || undefined,
          ranker: currentRankerAnswered || undefined,
        });
      });
    }

    li.appendChild(header);
    if (!libraryMode) li.appendChild(bar);
    // Appended on "were there terms at all", not "are any visible now" — a
    // card whose every match was a label still needs the node to repaint into.
    if ((hit.matchedTerms || []).length > 0) li.appendChild(matched);
    li.appendChild(detail);
    container.appendChild(li);

    if (ranked && topScore > 0 && typeof hit.score === "number") {
      const pct = Math.max(2, Math.round((hit.score / topScore) * 100));
      requestAnimationFrame(() => {
        fill.style.width = `${pct}%`;
      });
    }
  });
}

// ── the contest page ────────────────────────────────────────────────────────
// A collection is a filter, and a filter answers "which of the problems I can
// search came from here". That is not how anyone picks a past set to attempt:
// they want the set, in order, with the ones we could not index still in it,
// and the labels OUT OF SIGHT until they ask. So this view walks the registry
// members rather than the search hits, and the hits are what it merges IN.

// "A" is 1, matching a hand-written `order` of 1, so a registry that mixes the
// two still sorts sensibly. "B2" is the second part of B, hence 2.2.
function contestLetterRank(letter) {
  return (letter.charCodeAt(0) - 64) + (letter.length > 1 ? Number(letter[1]) / 10 : 0);
}

// Explicit order wins, then a letter, then the position the registry gave it.
// Registry position is the honest fallback and usually the only thing there
// is: the Kattis source pages seven of these collections came from list their
// problems alphabetically and print no letters at all.
function contestRank(member, index) {
  if (Number.isInteger(member.order) && member.order > 0) return member.order;
  if (typeof member.letter === "string" && /^[A-Z][0-9]?$/.test(member.letter)) return contestLetterRank(member.letter);
  return index + 1;
}

function contestRows(members, hits) {
  const byId = new Map((hits || []).map((h) => [h.problem.id, h]));
  return (members || [])
    .map((member, index) => ({ member, hit: byId.get(member.id) || null, rank: contestRank(member, index), index }))
    .sort((a, b) => a.rank - b.rank || a.index - b.index);
}

function contestDoneCount(ids, doneIds) {
  const done = doneIds instanceof Set ? doneIds : new Set(doneIds || []);
  return (ids || []).filter((id) => done.has(id)).length;
}

// "listed alphabetically" is a caveat about our data, not a fact about the
// contest, so it is only said when nothing in the data orders the set. A
// Codeforces gym id ends in the problem's real letter, so those are ordered
// even with no `letter` field anywhere.
function contestOrderUnverified(members) {
  const list = members || [];
  if (!list.length) return false;
  if (list.some((m) => m.letter || Number.isInteger(m.order))) return false;
  return !list.every((m) => /^codeforces-\d+-[a-z][0-9]?$/.test(m.id || ""));
}

// Where the statements came from, when we can say it without guessing. Family
// alone cannot answer it — every one of these is family "icpc" — so it reads
// the links the registry already had to verify.
function contestProvenance(collection) {
  const links = [
    ...(collection.resources || []).map((r) => r.url || ""),
    ...(collection.evidence || []),
  ].join(" ");
  if (/kattis\.com/.test(links)) return "Statements from Kattis; this is the original judge.";
  if (/codeforces\.com\/gym\//.test(links)) return "Statements from the Codeforces gym.";
  return "";
}

function contestTopicTally(hits) {
  const counts = new Map();
  for (const hit of hits || []) {
    for (const p of hit.problem.patterns || []) counts.set(p, (counts.get(p) || 0) + 1);
  }
  return [...counts.entries()].sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]));
}

// Labels are hints. Whoever is hiding them has not stopped wanting to know
// what a set is made of afterwards, so the tally stays — behind a summary that
// says out loud what opening it will show.
function contestTopicsHidden() {
  return typeof showLabels !== "undefined" && !showLabels;
}

// A member with no indexed statement. It still ran, it is still part of the
// set, and the hard ones are exactly the ones that are missing — 9.2, 9.1 and
// 8.4 on Kattis's own scale — so a bare "3 not yet indexed" count hides the
// shape of the contest rather than reporting it.
function renderContestUnindexedRow(member) {
  const kattis = member.kattis_difficulty ? { platform: "kattis", kattis_difficulty: member.kattis_difficulty } : null;
  const score = kattis ? cosineDifficulty.format(kattis) : "";
  const band = kattis ? cosineDifficulty.kattisLabel(kattis) : "";
  const url = safeResourceUrl(member.url || "");
  const parts = [`<span class="contest-title">${escapeHtml(member.title || member.id)}</span>`];
  if (score) {
    parts.push(`<span class="difficulty ${band}" title="Kattis’s own 1–10 difficulty score — not a rating">${escapeHtml(score)}</span>`);
  }
  if (url) parts.push(`<a href="${escapeHtml(url)}" class="external-link" target="_blank" rel="noopener">open original &rarr;</a>`);
  parts.push('<span class="contest-unlabelled">not yet labelled</span>');
  return `<div class="contest-unindexed">${parts.join("")}</div>`;
}

function contestHeaderHtml(collection, hits, members, doneIds) {
  const dim = [collection.held_date, collection.location, collection.organizer].filter(Boolean).join(" · ");
  const rows = [`<div class="contest-name">${escapeHtml(collection.name || collection.id)}</div>`];
  if (dim) rows.push(`<div class="contest-dim">${escapeHtml(dim)}</div>`);
  const provenance = contestProvenance(collection);
  if (provenance) rows.push(`<div class="contest-dim">${escapeHtml(provenance)}</div>`);
  if (contestOrderUnverified(members)) {
    rows.push('<div class="contest-caveat">problem order not verified — listed alphabetically</div>');
  }
  // Signed out there is no answer, and "0 of 13 done" would be a wrong one.
  if (doneIds) {
    const total = (collection.problems || []).length;
    rows.push(`<div class="contest-progress">${contestDoneCount(collection.problems, doneIds)} of ${total} done</div>`);
  }
  // Editorials and booklets first: they are what you want after attempting a
  // set, and the judge link is already on every row.
  const kindOrder = (kind) => (["editorial", "pdf"].includes(kind) ? 0 : 1);
  const links = (collection.resources || [])
    .map((r) => ({ r, url: safeResourceUrl(r.url) }))
    .filter((x) => x.url)
    .sort((a, b) => kindOrder(a.r.kind) - kindOrder(b.r.kind));
  if (links.length) {
    rows.push('<ul class="contest-resources">' + links.map(({ r, url }) =>
      `<li><a href="${escapeHtml(url)}" target="_blank" rel="noopener">${escapeHtml(r.title || r.kind || "contest resource")}</a>${escapeHtml(resourceAvailabilityNote(r.availability))}</li>`
    ).join("") + "</ul>");
  }
  const topics = contestTopicTally(hits);
  if (topics.length) {
    const summary = contestTopicsHidden() ? "by topic · reveals labels" : "by topic";
    rows.push(`<details class="contest-topics"><summary>${escapeHtml(summary)}</summary><div class="contest-topic-list">` +
      topics.map(([pattern, n]) =>
        `<span class="contest-topic"><button type="button" class="pattern-chip" data-pattern="${escapeHtml(pattern)}" title="filter results by this label">${escapeHtml(pattern)}</button> × ${n}</span>`
      ).join("") + "</div></details>");
  }
  return rows.join("");
}

function renderContestList(collection, hits, members, doneIds) {
  resultsEl.innerHTML = "";
  const header = document.createElement("li");
  header.className = "contest-header";
  header.innerHTML = contestHeaderHtml(collection, hits, members, doneIds);
  header.querySelectorAll(".pattern-chip").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      applyPatternFilter(btn.dataset.pattern);
    });
  });
  const topics = header.querySelector(".contest-topics");
  if (topics) {
    topics.addEventListener("toggle", () => {
      if (!topics.open || topics.dataset.counted) return;
      topics.dataset.counted = "1";
      track("contest_viewed", { collection: collection.id, topics: true });
    });
  }
  resultsEl.appendChild(header);

  for (const row of contestRows(members, hits)) {
    const li = document.createElement("li");
    li.className = "result contest-row";
    const cell = document.createElement("span");
    cell.className = "contest-letter";
    cell.textContent = row.member.letter || row.member.code || "";
    li.appendChild(cell);
    if (row.hit) {
      // One card, drawn by the one renderer that knows how to draw a card —
      // bookmark, done, statement, the lot. Duplicating it here is how the two
      // would drift.
      const holder = document.createElement("ul");
      holder.className = "contest-card";
      renderHitsList(holder, [row.hit], { unranked: true });
      li.appendChild(holder);
    } else {
      const holder = document.createElement("div");
      holder.className = "contest-card";
      holder.innerHTML = renderContestUnindexedRow(row.member);
      li.appendChild(holder);
    }
    resultsEl.appendChild(li);
  }
}

// Done ids come from the same endpoint the library counts read. Signed out
// there is nothing to intersect with, and null means "say nothing".
async function contestDoneIds() {
  if (!currentUser) return null;
  try {
    const res = await fetch("/api/user-state");
    if (!res.ok) return null;
    const data = await res.json();
    return new Set(data.done || []);
  } catch (_e) {
    return null;
  }
}

async function runContest(collectionId) {
  // A ?view=contest link dispatches at boot, before /api/collections answers,
  // and this view is built out of the registry rather than out of the hits —
  // so it waits for the registry instead of falling back to a browse.
  let collection = collectionById(collectionId);
  if (!collection && collectionsReady) {
    await collectionsReady;
    collection = collectionById(collectionId);
  }
  // Not one of ours, or the registry never loaded. Either way there is no
  // contest to draw, so fall through to the browse the chip means.
  if (!collection) return runSearch("");
  const issuedAt = ++lastQueryAt;
  hideFeedback();
  hideLoadMore();
  currentSearchId = null;
  currentRankerAnswered = "";
  currentQuery = "";
  currentOffset = 0;
  currentTopScore = 0;
  input.value = "";
  if (currentUser) setLibPath(`~/contest ${collectionId}`);
  syncUrl();
  renderCollectionPanel();

  // One page: the largest collection here is fifteen problems, so paging would
  // be furniture over a list that always fits.
  const k = Math.max(collection.count || 0, 1);
  const rankerParam = activeRanker ? `&ranker=${encodeURIComponent(activeRanker)}` : "";
  const url = `/api/search?q=&k=${k}&contest=${encodeURIComponent(collectionId)}${rankerParam}`;
  let data;
  try {
    if (inFlight) inFlight.abort();
    inFlight = new AbortController();
    const res = await fetch(url, { signal: inFlight.signal });
    data = await res.json();
  } catch (err) {
    if (err.name === "AbortError" || issuedAt !== lastQueryAt) return;
    setStatus(`error: ${err.message || "contest view failed"}`);
    return;
  }
  if (issuedAt !== lastQueryAt) return;

  const hits = data.hits || [];
  currentTotal = data.total || hits.length;
  track("contest_viewed", { collection: collectionId });
  const doneIds = await contestDoneIds();
  if (issuedAt !== lastQueryAt) return;
  renderContestList(collection, hits, collection.members || [], doneIds);
  setStatus(`${collection.name} · contest view`);
}

function buildActions(hit, libraryMode) {
  const actions = document.createElement("span");
  actions.className = "result-actions";

  const bookmark = document.createElement("button");
  bookmark.type = "button";
  bookmark.className = "result-action bookmark";
  bookmark.title = hit.bookmarked ? "remove bookmark" : "bookmark this problem";
  bookmark.setAttribute("aria-pressed", String(!!hit.bookmarked));
  bookmark.textContent = hit.bookmarked ? "★" : "☆";
  bookmark.addEventListener("click", (e) => {
    e.stopPropagation();
    toggleFlag(hit, "bookmarked", bookmark);
  });

  const done = document.createElement("button");
  done.type = "button";
  done.className = "result-action done";
  done.title = hit.done ? "unmark as done" : "mark as done";
  done.setAttribute("aria-pressed", String(!!hit.done));
  done.textContent = hit.done ? "✓" : "○";
  done.addEventListener("click", (e) => {
    e.stopPropagation();
    toggleFlag(hit, "done", done);
  });

  actions.appendChild(bookmark);
  actions.appendChild(done);
  // The rating shows up in the LIBRARY only, and only on a row that is
  // actually saved. Searching is the busy surface — a third chip on every
  // result there is chrome you have to look past to read a title — while the
  // library is exactly where "how did that go?" is the question being asked.
  if (libraryMode && (hit.done || hit.bookmarked)) actions.appendChild(buildRecall(hit));
  // The note button follows the same rule as the rating — the library, where
  // you are looking at your own problems — plus the card you JUST marked,
  // wherever you marked it. That second case is the whole point: the moment
  // you tick something done is the moment you have something to write, and
  // making you go find it in the library afterwards is how notes don't get
  // written.
  if ((libraryMode || hit.justMarked) && (hit.done || hit.bookmarked)) {
    actions.appendChild(buildNoteButton(hit));
  }
  return actions;
}

function buildNoteButton(hit) {
  const btn = document.createElement("button");
  btn.type = "button";
  const has = typeof cosineSheets !== "undefined" && cosineSheets.noteText(hit.problem.id).trim();
  btn.className = `result-action note-btn${has ? " has-note" : ""}`;
  btn.textContent = "✎";
  btn.title = has ? "edit your note" : "add a note";
  btn.setAttribute("aria-label", btn.title);
  btn.addEventListener("click", (e) => {
    e.stopPropagation();   // the header click toggles the card open
    openNoteEditor(hit);
  });
  return btn;
}

// After a save, repaint the card for that problem so the note and the ✎ state
// show without re-running the search.
function refreshNoteOnCard(problemId) {
  const li = resultsEl.querySelector(`[data-problem-id="${CSS.escape(problemId)}"]`);
  if (!li) return;
  const btn = li.querySelector(".note-btn");
  if (btn) {
    const has = cosineSheets.noteText(problemId).trim();
    btn.classList.toggle("has-note", !!has);
    btn.title = has ? "edit your note" : "add a note";
  }
  const existing = li.querySelector(".note-view");
  const fresh = buildNoteView(problemId);
  const slot = li.querySelector(".has-note-slot");
  if (existing && fresh) existing.replaceWith(fresh);
  else if (existing) existing.remove();
  else if (fresh && slot) slot.appendChild(fresh);
}

// One cycling chip rather than four buttons — the card grows by a single
// element, and "how did it go" is a one-tap answer at the moment you tick
// something done, which was the whole point (a separate sheet is friction
// nobody pays twice).
//
// It shows ONE character, always the same width as ☆ and ✓. The first cut
// wrote the word ("again", "med"), which made the chip a different size in
// every row and shoved the whole action group left and right as you rated
// things. The letter is explained by its tooltip, by the colour, and by
// `:help saving`.
const RECALL_CYCLE = [null, "again", "hard", "medium", "easy"];
const RECALL_LETTER = { again: "A", hard: "H", medium: "M", easy: "E" };
const RECALL_WORD = { again: "again", hard: "hard", medium: "medium", easy: "easy" };

function buildRecall(hit) {
  const btn = document.createElement("button");
  btn.type = "button";
  const paint = () => {
    const v = hit.recall || null;
    btn.className = `result-action recall${v ? ` recall-${v}` : ""}`;
    btn.textContent = v ? RECALL_LETTER[v] : "·";
    btn.title = v
      ? `how it went: ${RECALL_WORD[v]} — tap to change`
      : "rate how it went: again / hard / medium / easy";
    btn.setAttribute("aria-label", btn.title);
  };
  paint();
  btn.addEventListener("click", (e) => {
    e.stopPropagation(); // the header click toggles the card open
    const before = hit.recall || null;
    const next = RECALL_CYCLE[(RECALL_CYCLE.indexOf(before) + 1) % RECALL_CYCLE.length];
    // Optimistic: paint first, ask after. Four taps to get from unrated to
    // "easy" behind a disabled button and a spinner is unusable — and there
    // is nothing to lose by being wrong, since the only recovery a failure
    // needs is putting the old letter back.
    hit.recall = next || undefined;
    paint();
    track("recall_set", { problemId: hit.problem.id, value: next || "none" });
    fetch(`/api/recall/${encodeURIComponent(hit.problem.id)}/${next || "none"}`, { method: "PUT" })
      .then((res) => {
        if (res.ok) {
          markSheetDirty();
          // A recall filter may mean this row no longer belongs in the view.
          // Re-issue on the way out, never mid-cycle.
          if (libRecall && currentUser && libraryCommand(currentQuery)) {
            reissueCurrentView();
          }
          return;
        }
        hit.recall = before || undefined;
        paint();
        setStatus(res.status === 409 ? "rating needs a saved problem" : "could not save that rating");
      })
      .catch(() => {
        hit.recall = before || undefined;
        paint();
        setStatus("offline — rating not saved");
      });
  });
  return btn;
}

async function toggleFlag(hit, flag, btn) {
  const next = !hit[flag];
  const path = flag === "done" ? "done" : "bookmark";
  btn.disabled = true;
  let res;
  try {
    res = await fetch(`/api/${path}/${encodeURIComponent(hit.problem.id)}`, {
      method: next ? "POST" : "DELETE",
    });
  } catch (_e) {
    btn.disabled = false;
    return;
  }
  btn.disabled = false;
  if (!res.ok) return;

  hit[flag] = next;
  hit.justMarked = next || hit.done || hit.bookmarked;
  if (flag === "bookmarked") {
    btn.textContent = next ? "★" : "☆";
    btn.title = next ? "remove bookmark" : "bookmark this problem";
  } else {
    btn.textContent = next ? "✓" : "○";
    btn.title = next ? "unmark as done" : "mark as done";
  }
  btn.setAttribute("aria-pressed", String(next));

  // Un-saving something you had rated: the row leaves your library but the
  // rating is kept, and saying so beats letting someone discover it later.
  if (!next && !hit.done && !hit.bookmarked && hit.recall) {
    setStatus(`unsaved — your "${RECALL_WORD[hit.recall] || hit.recall}" rating is kept if you save it again`);
  }

  if (currentUser) refreshLibraryCounts();
  markSheetDirty();

  // If the active filter or library view would no longer include this row,
  // re-run so the listing and the total stay honest.
  if (currentFilter === "done" && flag === "done" && !next) reissueSearch();
  if (currentFilter === "notdone" && flag === "done" && next) reissueSearch();
  if (currentUser && libraryCommand(currentQuery)) reissueSearch();
}

// One of these, at random, opened. For the moment where you want to revise and
// don't want to choose — and because it reads whatever is on screen, it
// composes with every filter for free: `:done · again · 3mo+ · pick one`.
function pickOne() {
  const cards = [...resultsEl.querySelectorAll(".result")];
  if (!cards.length) {
    setStatus("nothing to pick from — widen the filters");
    return;
  }
  const card = cards[Math.floor(Math.random() * cards.length)];
  const header = card.querySelector(".result-header");
  const detail = card.querySelector(".result-detail");
  if (detail && detail.classList.contains("hidden") && header) header.click();
  card.scrollIntoView({ behavior: "smooth", block: "center" });
  card.classList.add("picked");
  setTimeout(() => card.classList.remove("picked"), 1600);
  track("library_pick", { of: cards.length });
}

function reissueSearch() {
  currentOffset = 0;
  reissueCurrentView();
}

// Read-only view of a problem's sheet row. The sheet is the editing surface —
// status, time taken, whatever columns the user invents live there, and the
// site just shows what it finds. No form means no save path, which means the
// Google token is only ever requested when the user presses sync.
//
// A problem with no notes gets NOTHING — not an empty form. Status and
// time-taken make no sense on a problem you just searched for and never
// attempted; the fields appear exactly where the user chose to write them.
// ── The note editor ──────────────────────────────────────────────────────────
//
// The site used to be read-only about notes, on the reasoning that writing
// needs a Google token and asking for one needs a click. Local-first removes
// that: pressing save writes to this browser immediately and the sync — which
// already runs on its own a few seconds after any change — carries it to the
// sheet. So a note costs one click here and zero anywhere else, and the sheet
// is still the place it lives.
//
// The format is markdown-flavoured PLAIN TEXT, because the destination is a
// spreadsheet cell. Bold, inline code, fenced blocks and bullets are markers
// you can read in Sheets as easily as here — no HTML, no rich-text runs, and
// nothing that arrives in the cell as a tag soup.
let noteTarget = null;   // { problemId, title }

const CP_NOTE_TEMPLATE = `## Idea
- key insight

## Why it works

## Complexity
- Time: \`O(·)\`
- Space: \`O(·)\`

## Pitfalls
- `;

function noteDialog() {
  return document.getElementById("note-dialog");
}

function updateNotePreview() {
  const preview = document.getElementById("note-preview");
  const text = document.getElementById("note-text");
  if (!preview || !text) return;
  const value = text.value.trim();
  preview.innerHTML = "";
  preview.classList.toggle("is-empty", !value);
  if (!value) {
    preview.textContent = "Your formatted note will appear here.";
    return;
  }
  preview.appendChild(renderNoteMarkdown(text.value));
}

function setNoteMode(mode) {
  const previewing = mode === "preview";
  const text = document.getElementById("note-text");
  const preview = document.getElementById("note-preview");
  const tools = document.getElementById("note-tools");
  if (!text || !preview || !tools) return;
  if (previewing) updateNotePreview();
  text.hidden = previewing;
  tools.hidden = previewing;
  preview.hidden = !previewing;
  document.querySelectorAll("[data-note-mode]").forEach((btn) => {
    const active = btn.dataset.noteMode === mode;
    btn.classList.toggle("is-active", active);
    btn.setAttribute("aria-selected", String(active));
  });
  if (!previewing) text.focus();
}

function openNoteEditor(hit) {
  const dlg = noteDialog();
  if (!dlg || typeof cosineSheets === "undefined") return;
  noteTarget = { problemId: hit.problem.id, title: hit.problem.title || hit.problem.id };
  document.getElementById("note-problem").textContent = noteTarget.title;
  const text = document.getElementById("note-text");
  text.value = cosineSheets.noteText(noteTarget.problemId);
  setNoteMode("write");
  updateNotePreview();
  const link = document.getElementById("note-sheet-link");
  const url = cosineSheets.url();
  link.hidden = !url;
  if (url) link.href = url;
  paintNoteState();
  if (typeof dlg.showModal === "function") dlg.showModal();
  else dlg.setAttribute("open", "");
  text.focus();
  // Caret at the end, not selecting everything — this is usually an edit.
  text.setSelectionRange(text.value.length, text.value.length);
}

function paintNoteState(saved) {
  const el = document.getElementById("note-state");
  if (!el) return;
  if (!cosineSheets.available()) {
    el.textContent = "saved in this browser · sheet sync isn't configured here";
    return;
  }
  if (!cosineSheets.connected()) {
    el.textContent = "saved in this browser · connect a sheet to keep it in your Drive";
    return;
  }
  const pending = cosineSheets.pendingCount();
  el.textContent = saved
    ? "saved · goes to your sheet on the next sync"
    : pending
      ? `${pending} note${pending > 1 ? "s" : ""} waiting for the next sync`
      : "markdown: **bold**, `code`, ``` blocks, - bullets";
}

function closeNoteEditor() {
  const dlg = noteDialog();
  noteTarget = null;
  if (!dlg) return;
  if (typeof dlg.close === "function") dlg.close();
  else dlg.removeAttribute("open");
}

function saveNoteEditor() {
  if (!noteTarget) return;
  const text = document.getElementById("note-text").value;
  cosineSheets.saveNote(noteTarget.problemId, text);
  track("note_saved", { problemId: noteTarget.problemId, chars: text.length });
  markSheetDirty();
  paintNoteState(true);
  // Repaint whatever is on screen so the note shows without a round trip.
  const id = noteTarget.problemId;
  closeNoteEditor();
  refreshNoteOnCard(id);
  // Say what actually happens next. "syncing to your sheet" is a lie on a
  // browser where the silent token never lands, and the fix for that case is
  // one button press — so name it.
  setStatus(
    !cosineSheets.connected() ? "note saved in this browser"
      : cosineSheets.hasToken() ? "note saved · syncing to your sheet"
        : "note saved here · press sync sheet to put it in your sheet"
  );
}

// Wrap the selection in a marker, or drop a block at the caret. Everything
// here is a text edit on a textarea: no editor library, no contenteditable,
// and what you see is exactly what lands in the cell.
function applyNoteTool(btn) {
  const ta = document.getElementById("note-text");
  const { selectionStart: a, selectionEnd: b, value } = ta;
  const picked = value.slice(a, b);
  let out, caret, caretEnd;
  if (btn.dataset.insert != null) {
    const insertion = btn.dataset.insert;
    out = value.slice(0, a) + insertion + value.slice(b);
    const placeholder = insertion.indexOf("·");
    caret = a + (placeholder === -1 ? insertion.length : placeholder);
    caretEnd = placeholder === -1 ? caret : caret + 1;
  } else if (btn.dataset.template) {
    const before = a && value[a - 1] !== "\n" ? "\n\n" : "";
    const after = b < value.length && value[b] !== "\n" ? "\n\n" : "";
    out = value.slice(0, a) + before + CP_NOTE_TEMPLATE + after + value.slice(b);
    caret = a + before.length + CP_NOTE_TEMPLATE.indexOf("- ") + 2;
    caretEnd = caret + "key insight".length;
  } else if (btn.dataset.wrap) {
    const m = btn.dataset.wrap;
    out = value.slice(0, a) + m + picked + m + value.slice(b);
    caret = picked ? a + m.length * 2 + picked.length : a + m.length;
  } else if (btn.dataset.block) {
    const fence = btn.dataset.block;
    const before = a && value[a - 1] !== "\n" ? "\n" : "";
    const body = picked || "";
    out = `${value.slice(0, a)}${before}${fence}\n${body}\n${fence}\n${value.slice(b)}`;
    caret = a + before.length + fence.length + 1 + body.length;
  } else {
    const p = btn.dataset.prefix || "";
    // Prefix every selected line, so bulleting three lines is one press.
    const start = value.lastIndexOf("\n", a - 1) + 1;
    const chunk = value.slice(start, b) || "";
    const prefixed = chunk.split("\n").map((l) => (l.startsWith(p) ? l : p + l)).join("\n");
    out = value.slice(0, start) + prefixed + value.slice(b);
    caret = start + prefixed.length;
  }
  ta.value = out;
  ta.focus();
  ta.setSelectionRange(caret, caretEnd == null ? caret : caretEnd);
  updateNotePreview();
  if (btn.dataset.insert != null) {
    const palette = btn.closest && btn.closest("details");
    if (palette) palette.open = false;
  }
}

(function wireNoteEditor() {
  const dlg = noteDialog();
  if (!dlg) return;
  document.getElementById("note-save").addEventListener("click", saveNoteEditor);
  document.getElementById("note-cancel").addEventListener("click", closeNoteEditor);
  document.getElementById("note-tools").addEventListener("click", (e) => {
    const btn = e.target.closest(".note-tool");
    if (btn) applyNoteTool(btn);
  });
  document.querySelectorAll("[data-note-mode]").forEach((btn) => {
    btn.addEventListener("click", () => setNoteMode(btn.dataset.noteMode));
  });
  const ta = document.getElementById("note-text");
  ta.addEventListener("input", updateNotePreview);
  ta.addEventListener("keydown", (e) => {
    // Tab indents instead of leaving the box: this is where code goes.
    if (e.key === "Tab") {
      e.preventDefault();
      const { selectionStart: a, selectionEnd: b } = ta;
      ta.value = ta.value.slice(0, a) + "  " + ta.value.slice(b);
      ta.setSelectionRange(a + 2, a + 2);
      updateNotePreview();
      return;
    }
    const mod = e.metaKey || e.ctrlKey;
    if (mod && e.key === "Enter") { e.preventDefault(); saveNoteEditor(); return; }
    if (mod && e.key.toLowerCase() === "b") { e.preventDefault(); applyNoteTool({ dataset: { wrap: "**" } }); return; }
    if (mod && e.shiftKey && e.key.toLowerCase() === "c") { e.preventDefault(); applyNoteTool({ dataset: { block: "```" } }); return; }
    if (mod && e.key.toLowerCase() === "e") { e.preventDefault(); applyNoteTool({ dataset: { wrap: "`" } }); }
  });
  // Esc fires `cancel` on a <dialog>; keep our state in step with the browser's.
  dlg.addEventListener("close", () => { noteTarget = null; });
})();

function buildNoteView(problemId) {
  const note = cosineSheets.noteFor(problemId);
  if (!note) return null;
  // Whatever columns YOUR sheet has, in your order — not a fixed list of six.
  // Add a column called "revision date" and it shows up here.
  const filled = cosineSheets.userColumns().filter((fld) => (note[fld.key] || "").trim());
  if (!filled.length) return null;

  const wrap = document.createElement("div");
  wrap.className = "note-view";
  for (const fld of filled) {
    const row = document.createElement("div");
    row.className = "note-row";
    const cap = document.createElement("span");
    cap.className = "note-label";
    cap.textContent = fld.label;
    const val = fld.key === cosineSheets.NOTE_FIELD
      ? renderNoteMarkdown(note[fld.key])
      : document.createElement("span");
    val.className = "note-value";
    if (!val.childNodes.length) val.textContent = note[fld.key];
    row.appendChild(cap);
    row.appendChild(val);
    wrap.appendChild(row);
  }
  if (note.pending) {
    const flag = document.createElement("span");
    flag.className = "note-pending";
    flag.textContent = "not in your sheet yet";
    wrap.appendChild(flag);
  }
  const edit = document.createElement("a");
  edit.className = "note-edit-link";
  edit.href = cosineSheets.url() || "#";
  edit.target = "_blank";
  edit.rel = "noopener";
  edit.textContent = "open your sheet ↗";
  edit.addEventListener("click", (e) => e.stopPropagation());
  wrap.appendChild(edit);
  return wrap;
}

// The smallest markdown that a note actually needs, rendered with DOM nodes
// rather than innerHTML — the text came from a spreadsheet cell anyone could
// have typed anything into, and building elements means there is no string
// for a `<script>` to arrive in.
function renderNoteMarkdown(text) {
  const wrap = document.createElement("span");
  const lines = String(text || "").split("\n");
  let i = 0;
  let list = null;
  let listKind = null;
  const endList = () => { list = null; listKind = null; };
  while (i < lines.length) {
    const line = lines[i];
    if (line.trim().startsWith("```")) {
      endList();
      const lang = line.trim().slice(3).trim();
      const body = [];
      i++;
      while (i < lines.length && !lines[i].trim().startsWith("```")) body.push(lines[i++]);
      i++; // the closing fence
      const pre = document.createElement("pre");
      pre.className = "note-code";
      if (lang) pre.dataset.lang = lang;
      pre.textContent = body.join("\n");
      wrap.appendChild(pre);
      continue;
    }
    const bullet = /^\s*[-*]\s+/.test(line);
    const numbered = /^\s*\d+[.)]\s+/.test(line);
    if (bullet || numbered) {
      const kind = numbered ? "ol" : "ul";
      if (!list || listKind !== kind) {
        list = document.createElement(kind);
        list.className = "note-list";
        wrap.appendChild(list);
        listKind = kind;
      }
      const li = document.createElement("li");
      inlineNoteMarkdown(line.replace(numbered ? /^\s*\d+[.)]\s+/ : /^\s*[-*]\s+/, ""), li);
      list.appendChild(li);
      i++;
      continue;
    }
    endList();
    if (/^\s*#{1,6}\s+/.test(line)) {
      const h = document.createElement("strong");
      h.className = "note-heading";
      inlineNoteMarkdown(line.replace(/^\s*#{1,6}\s+/, ""), h);
      wrap.appendChild(h);
      i++;
      continue;
    }
    if (line.trim()) {
      const p = document.createElement("span");
      p.className = "note-para";
      inlineNoteMarkdown(line, p);
      wrap.appendChild(p);
    }
    i++;
  }
  return wrap;
}

// `code`, **bold** and *italic*, one pass, longest marker first so ** never
// matches as two single asterisks.
function inlineNoteMarkdown(text, into) {
  const re = /`([^`]+)`|\*\*([^*]+)\*\*|\*([^*]+)\*/g;
  let last = 0;
  let m;
  while ((m = re.exec(text))) {
    if (m.index > last) into.appendChild(document.createTextNode(text.slice(last, m.index)));
    const el = document.createElement(m[1] ? "code" : m[2] ? "strong" : "em");
    el.textContent = m[1] || m[2] || m[3];
    into.appendChild(el);
    last = m.index + m[0].length;
  }
  if (last < text.length) into.appendChild(document.createTextNode(text.slice(last)));
  return into;
}

function formatRelative(iso) {
  if (!iso) return "—";
  const ms = Date.now() - new Date(iso).getTime();
  if (!Number.isFinite(ms) || ms < 0) return "just now";
  const m = Math.floor(ms / 60000);
  if (m < 1) return "just now";
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h ago`;
  const d = Math.floor(h / 24);
  if (d < 30) return `${d}d ago`;
  const mo = Math.floor(d / 30);
  if (mo < 12) return `${mo}mo ago`;
  return `${Math.floor(mo / 12)}y ago`;
}

function escapeHtml(s) {
  return String(s)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

// Deep links, both directions: the URL is read here at boot and written by
// syncUrl() as you browse, so refresh, bookmark and share all keep the view.
//
// applyUrlState is the only reader of the query string, and it runs twice: at
// boot, and again on every popstate. That second caller is why it CLEARS every
// facet before parsing — going Back from "?contest=wf&platform=cf" to
// "?q=graph" is a different view, not that view with the collections still
// hanging off it. A reader that only ever ran once could get away with
// assuming the state was already empty; this one cannot.
//
// Two things it deliberately never touches. activeRanker is a preference about
// how to search rather than a description of what you are looking at, and the
// <select> carrying it is populated asynchronously — re-reading it per
// navigation would fight that. currentUser is not in the URL at all.
let lastAppliedSearch = location.search;

function applyUrlState(params) {
  lastAppliedSearch = location.search;
  activeCollections.clear();
  activePlatforms.clear();
  activeTiers.clear();
  activeRanges.clear();
  bootRanges.length = 0;
  activeAcceptance = null;
  sortDir = null;
  activePattern = "";
  currentSimilar = null;
  similarLibrary = null;
  practiceMode = false;
  contestView = false;
  libAged = null;
  libOldest = false;
  libRecall = null;
  libNotes = null;
  currentFilter = "all";
  filterSelect.value = "all";

  const q = (params.get("q") || "").trim();
  const similarId = (params.get("similar") || "").trim();
  if (/^[a-z0-9][a-z0-9-]{0,180}$/.test(similarId)) currentSimilar = { id: similarId, title: similarId };
  const library = params.get("library");
  if (currentSimilar && ["all", "bookmarked", "done"].includes(library)) { similarLibrary = library; bootNeedsAuth = true; }
  practiceMode = !!currentSimilar && params.get("practice") === "1";
  // practice=1 and contest= are a contradiction the server answers with zero
  // results: practice means "anything BUT the source contest", and runSimilar
  // clears the collections to say so. A hand-edited or stale link carrying
  // both is read as practice, and the first syncUrl writes the contest away.
  if (!practiceMode) {
    for (const id of (params.get("contest") || "").split(",")) {
      if (/^[a-z0-9][a-z0-9-]{0,120}$/.test(id)) activeCollections.add(id);
    }
  }
  // The contest page describes ONE contest. Two chips, or none, and the link
  // is describing a browse — so the view quietly reverts rather than picking
  // a collection for you.
  contestView = params.get("view") === "contest" && activeCollections.size === 1;
  const pattern = (params.get("pattern") || "").trim().toLowerCase();
  const aged = Number.parseInt(params.get("aged") || "", 10);
  if ([30, 90, 180].includes(aged)) libAged = aged;
  if ((params.get("order") || "").toLowerCase() === "oldest") libOldest = true;
  const recall = (params.get("recall") || "").trim().toLowerCase();
  if (["again", "hard", "medium", "easy", "none"].includes(recall)) libRecall = recall;
  const notes = (params.get("notes") || "").trim().toLowerCase();
  if (["yes", "no"].includes(notes)) libNotes = notes;
  const sort = (params.get("sort") || "").trim().toLowerCase();
  if (sort === "difficulty-asc" || sort === "difficulty") sortDir = "asc";
  else if (sort === "difficulty-desc") sortDir = "desc";
  const filter = (params.get("filter") || "").trim().toLowerCase();
  if (["done", "notdone"].includes(filter)) {
    currentFilter = filter;
    filterSelect.value = filter;
    bootNeedsAuth = true;
  }
  for (const p of (params.get("platform") || "").toLowerCase().split(",")) {
    if (PLATFORM_LABELS[p.trim()]) activePlatforms.add(p.trim());
  }
  // A judge range names its judge by a short form only /api/rankers can
  // resolve. At boot that payload has not landed yet, so the token is parked;
  // on a later popstate it has, and the token resolves immediately.
  const ratedKnown = (difficultyPayload.rated || []).length > 0;
  for (const tok of (params.get("difficulty") || "").toLowerCase().split(",")) {
    const t = tok.trim();
    const range = /^([a-z]{2,4}):(-?\d+)-(-?\d+)$/.exec(t);
    if (range && range[1] !== "ac" && !ratedKnown) bootRanges.push(range);
    else applyDifficultyToken(t);
  }
  if (/^[a-z0-9]+(-[a-z0-9]+)*$/.test(pattern)) activePattern = pattern;
  input.value = q;
  if (libraryCommand(q) || (currentSimilar && (libRecall || libAged || libNotes))) bootNeedsAuth = true;
  return q;
}

// Which view the parsed state describes. Separate from applyUrlState because
// popstate needs the controls repainted between the two.
function dispatchUrlView() {
  const q = input.value.trim();
  if (contestView && activeCollections.size === 1) {
    input.value = "";
    runContest([...activeCollections][0]);
  } else if (currentSimilar) {
    input.value = "";
    runSimilar(currentSimilar);
  } else if (activePattern) {
    applyPatternFilter(activePattern);
  } else if (q || activeCollections.size || activePlatforms.size) {
    runSearch(q, { append: false });
  } else {
    // Nothing selected and nothing typed. Back to a bare URL has to clear the
    // results too — at boot there are none, on popstate there are.
    currentQuery = "";
    currentTotal = 0;
    currentOffset = 0;
    resultsEl.innerHTML = "";
    hideLoadMore();
    hideFeedback();
    setStatus("");
  }
}

const bootParams = new URLSearchParams(location.search);
const urlRanker = (bootParams.get("ranker") || "").trim().toLowerCase();
if (/^[a-z0-9-]{1,24}$/.test(urlRanker)) activeRanker = urlRanker;
populateRankerSelect();
applyUrlState(bootParams);
collectionsReady = loadCollections();
syncJudgeControls();
updatePatternPill();
dispatchUrlView();

// Back / Forward. Without this the address bar and the page disagreed the
// moment you used either: syncUrl only ever replaced, so the only entries that
// existed were the ones the browser made, and pressing Back left a collection
// filtering results that the URL no longer mentioned.
window.addEventListener("popstate", () => {
  // A hash-only move (an in-page anchor) is not a change of view.
  if (location.search === lastAppliedSearch) return;
  applyUrlState(new URLSearchParams(location.search));
  syncJudgeControls();
  updatePatternPill();
  renderCollectionControls();
  dispatchUrlView();
});

// Put the caret where typing actually goes. Pointer-fine only, so mobile
// keyboards don't spring open on load.
if (window.matchMedia("(pointer: fine)").matches) input.focus();
