// The manual is a product surface, so it gets a test.
//
// app.js needs a DOM, but the help sections are pure data and a pure parser —
// so this lifts just that slice out of the file and runs it. Three things are
// worth guarding: `:help <section>` keeps parsing (it is the only way to reach
// five of the six sections), the index keeps listing every section that
// exists (a section nobody can find is the wall-of-text problem again), and
// nothing exceeds the wrap width (`white-space: pre` means one long line
// scrolls the whole manual sideways on a phone).
const assert = require("node:assert/strict");
const fs = require("fs");
const path = require("path");
const vm = require("vm");

const WIDTH = 64;

const src = fs.readFileSync(path.join(__dirname, "app.js"), "utf8");
const start = src.indexOf("const HELP_SECTIONS = [");
const end = src.indexOf("function renderHelp(");
assert.ok(start > -1 && end > start, "could not find the help block in app.js");

const ctx = vm.createContext({});
vm.runInContext(
  src.slice(start, end) + "\n;this.help = { HELP_SECTIONS, HELP_INDEX, helpQuery };",
  ctx
);
const { HELP_SECTIONS, HELP_INDEX, helpQuery } = ctx.help;

// ── the parser ───────────────────────────────────────────────────────────────
for (const q of [":help", ":h", " :HELP ", ":help   ", "help", " Help "]) {
  assert.equal(helpQuery(q), "", `${JSON.stringify(q)} should open the index`);
}
assert.equal(helpQuery(":help filters"), "filters");
assert.equal(helpQuery("help filters"), "filters", "bare help takes a section too");
assert.equal(helpQuery(":h Sheet"), "sheet", "section names are case-insensitive");
// Not help. ":hard" matters most: a greedy prefix match would swallow it.
for (const q of [":helpx", ":hard", ":bookmarks", "h", "helpful", "binary search", ""]) {
  assert.equal(helpQuery(q), null, `${JSON.stringify(q)} is not a help command`);
}
// An unknown section falls back to the index rather than erroring — renderHelp
// looks it up and finds nothing, which is the documented behaviour.
assert.equal(helpQuery(":help wat"), "wat");
assert.equal(HELP_SECTIONS.find((s) => s.name === "wat"), undefined);

// ── every section is reachable ───────────────────────────────────────────────
const names = HELP_SECTIONS.map((s) => s.name);
assert.ok(names.length >= 5, "expected the manual to be split into sections");
assert.equal(new Set(names).size, names.length, "duplicate section name");
for (const name of names) {
  assert.ok(HELP_INDEX.includes(`:help ${name}`), `the index never mentions :help ${name}`);
}
// The commands section repeats the list; keep the two in step.
const commands = HELP_SECTIONS.find((s) => s.name === "commands");
assert.ok(commands, "expected a commands section");
const listed = commands.body.match(/one section: ([\s\S]*?)\n\s*:compare/);
assert.ok(listed, "commands section no longer lists the section names");
const listedNames = listed[1].split(/[,\s]+/).map((s) => s.trim()).filter(Boolean);
assert.deepEqual(listedNames.sort(), [...names].sort(), "commands list vs actual sections");

// ── the manual may only name controls that exist ────────────────────────────
// It drifted twice in two weeks: a "both" ranker mode after hybrid stopped
// being served, and a "to write up" chip five weeks after it was deleted. The
// manual is the only place several behaviours are described, so it is
// load-bearing, and this is the assertion that keeps it honest. Add a row when
// the manual starts naming a new control.
const indexHtml = fs.readFileSync(path.join(__dirname, "index.html"), "utf8");
const allHelp = HELP_INDEX + HELP_SECTIONS.map((s) => s.body).join("\n");
const MANUAL_CONTROLS = [
  // [phrase the manual uses, must exist in, pattern]
  ["pick one",         indexHtml, /id="lib-pick"/],
  ["connect sheet",    indexHtml, /id="sheet-btn"/],
  ["oldest first",     indexHtml, /id="lib-oldest"/],
  ["+ competition",    indexHtml, /id="collection-add"/],
  ["reset to search",  indexHtml, /id="reset-search"/],
  ["Practice levels", indexHtml, /href="\/profile.html#practice-levels"/],
  ["labels:",          indexHtml, /id="labels-toggle"/],
  ["written up",       indexHtml, /<option value="yes">written up<\/option>/],
  ["my level",         src,       /"level-apply"/],
  ["contest page",     src,       /'contest-open'/],
];
for (const [phrase, where, pattern] of MANUAL_CONTROLS) {
  if (!allHelp.includes(phrase)) continue; // the manual stopped mentioning it; nothing to guard
  assert.match(where, pattern, `the manual names "${phrase}" but no such control exists any more`);
}
// The ranker modes the manual lists must be exactly the ones the picker offers.
const searchBody = HELP_SECTIONS.find((s) => s.name === "search").body;
const documentedModes = [...searchBody.matchAll(/^  (keyword|meaning|both)\s{2,}\S/gm)].map((m) => m[1]).sort();
const pickerRankers = JSON.parse(src.match(/const PICKER_RANKERS = (\[[^\]]*\]);/)[1]);
const shortLabels = {};
for (const m of src.matchAll(/^\s+("?[\w-]+"?):\s+"(\w+)",$/gm)) {
  // RANKER_LABELS_SHORT rows look like `  bm25: "keyword",`
  shortLabels[m[1].replace(/"/g, "")] = m[2];
}
const offeredModes = [...new Set(pickerRankers.map((r) => shortLabels[r]))].sort();
assert.deepEqual(documentedModes, offeredModes, "the manual documents a ranker mode the picker does not offer, or misses one it does");

// ── it fits a phone ──────────────────────────────────────────────────────────
for (const [label, text] of [["index", HELP_INDEX], ...HELP_SECTIONS.map((s) => [s.name, s.body])]) {
  for (const line of text.split("\n")) {
    assert.ok(line.length <= WIDTH, `${label}: line over ${WIDTH} cols: ${JSON.stringify(line)}`);
  }
}

// ── the answers people could not find ────────────────────────────────────────
const all = HELP_INDEX + HELP_SECTIONS.map((s) => s.body).join("\n");
assert.match(all, /not done/, "bookmarked-but-never-solved should be spelled out");
assert.match(all, /recall|again/, "the rating should be documented");
assert.match(all, /solution summary/, "the sheet's own columns should be listed");

console.log(`help tests passed (${names.length} sections, ${HELP_INDEX.split("\n").length}-line index)`);
