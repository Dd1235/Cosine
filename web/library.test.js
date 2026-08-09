// `libraryCommand` — the parse the whole library depends on.
//
// Nine places ask it "am I looking at a saved list?": the router in
// `runSearch`, `syncUrl`, the Tab cycle, the sheet's dirty check, and the
// re-issues after a bookmark, a done-mark and a rating. They used to each do
// their own exact-match lookup, which is why `:done graph` was impossible —
// one extra word and every one of them said no at once.
//
// So the interesting cases here are the boundaries: a command with a query
// after it, a word that merely starts with a command, and the two-word forms.
const assert = require("node:assert/strict");
const fs = require("fs");
const path = require("path");
const vm = require("vm");

const src = fs.readFileSync(path.join(__dirname, "app.js"), "utf8");
const start = src.indexOf("const LIBRARY_COMMANDS = {");
const end = src.indexOf("const compareEl =");
assert.ok(start > -1 && end > start, "could not find the library command block in app.js");
const ctx = vm.createContext({});
vm.runInContext(src.slice(start, end) + "\n;this.libraryCommand = libraryCommand;", ctx);
// Values cross a vm realm, so compare plain data rather than prototypes.
const parse = (q) => JSON.parse(JSON.stringify(ctx.libraryCommand(q) ?? null));

// ── the command alone ───────────────────────────────────────────────────────
assert.deepEqual(parse(":done"), { type: "done", q: "" });
assert.deepEqual(parse(":DONE"), { type: "done", q: "" }, "case-insensitive");
assert.deepEqual(parse("  :bookmarks  "), { type: "bookmarked", q: "" }, "trimmed");
assert.deepEqual(parse("ls bookmarks"), { type: "bookmarked", q: "" }, "the two-word form");
assert.deepEqual(parse(":lib"), { type: "all", q: "" });

// ── the command with something after it ─────────────────────────────────────
assert.deepEqual(parse(":done graph"), { type: "done", q: "graph" });
assert.deepEqual(parse(":b segment tree"), { type: "bookmarked", q: "segment tree" });
assert.deepEqual(parse("ls bookmarks dsu"), { type: "bookmarked", q: "dsu" },
  "the longest matching command wins, so the rest is the query");
assert.deepEqual(parse(":all Two Sum"), { type: "all", q: "Two Sum" },
  "the query keeps its case — it is text, not a command");
assert.deepEqual(parse(":done   spaced   out  "), { type: "done", q: "spaced   out" });

// ── not commands ────────────────────────────────────────────────────────────
// The space is what separates a command from a query, so a longer word that
// merely starts the same way must not match — otherwise `:donegraph` would
// silently become a library view.
for (const q of [":doneish", ":donegraph", ":bo", "done", "graph", "", "   ", null, undefined]) {
  assert.equal(parse(q), null, `${JSON.stringify(q)} is not a library command`);
}

console.log("library command tests passed");
