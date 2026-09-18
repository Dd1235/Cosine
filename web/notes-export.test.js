const assert = require("node:assert/strict");
const fs = require("node:fs");
const {JSDOM} = require("jsdom");
const difficulty = require("./difficulty");
const plain = value => JSON.parse(JSON.stringify(value));
const settle = async () => {for (let i = 0; i < 5; i++) await new Promise(setImmediate);};

(async () => {
  const dom = new JSDOM(fs.readFileSync(`${__dirname}/index.html`, "utf8"), {url: "http://local/?q=:bookmarks&order=oldest", runScripts: "outside-only"});
  const w = dom.window, doc = w.document;
  w.eval(fs.readFileSync(require.resolve("katex"), "utf8"));
  w.eval(fs.readFileSync(`${__dirname}/sheets.js`, "utf8") + `
    window.cosineSheets = cosineSheets;
    window.seedExportSheet = () => {
      spreadsheetId = 'test-sheet';
      sheetLayout = readLayout([['problem_id', 'Proof', 'solution_summary', 'Attempts', 'pending', 'constructor']]);
      rowByProblem.set('b', {rowIndex: 2, proof: '**custom**', solution_summary: 'old', attempts: 0, pending: 'review tomorrow'});
      remember(); rememberRows();
    };`);
  const app = fs.readFileSync(`${__dirname}/app.js`, "utf8");
  w.eval(app.slice(app.indexOf("function renderNoteMarkdown("), app.indexOf("function formatRelative(")));
  w.eval(fs.readFileSync(`${__dirname}/notes-export.js`, "utf8"));
  w.cosineDifficulty = difficulty;
  const api = w.cosineNotesExport;
  const hits = [
    {problem: {id: "b", title: "<script>unsafe</script>", url: "javascript:alert(1)", platform: "codeforces", difficulty: 1800}},
    {problem: {id: "a", title: "Summation", url: "https://example.com/problem", platform: "codeforces", difficulty: 1200}},
    {problem: {id: "empty", title: "Blank", platform: "codeforces", difficulty: 800}},
  ];
  const notes = {
    b: {solution_summary: "", proof: "**Only a custom column**\n<script>alert(1)</script>", attempts: 0},
    a: {solution_summary: "# Idea\n$\\sum_{i=1}^{n} i$ and $\\pi$\n$$\n\\log n\n$$\n```cpp\nif (x < y) return 0;\n```", pending: true},
    empty: {solution_summary: " \n\t", proof: ""},
  };
  const sheets = {noteFor: id => notes[id], userColumns: () => [
    {key: "proof", label: "Proof <img src=x>"}, {key: "solution_summary", label: "Notes"}, {key: "attempts", label: "Attempts"},
  ]};
  sheets.noteFields = id => sheets.userColumns().map(c => ({...c, value: String(notes[id]?.[c.key] ?? "")}));
  sheets.hasPendingNote = id => !!notes[id]?.pending;
  const selected = {complete: true, hits, userId: "test", context: "Bookmarked · oldest first", viewUrl: w.location.href};
  const plan = api.snapshot([...hits, hits[0]], sheets, selected, false, difficulty);
  assert.deepEqual(plain(plan.rows.map(r => r.problem.id)), ["b", "a"], "keeps app order, includes custom-only rows, deduplicates");
  assert.equal(plan.skipped, 1);
  assert.deepEqual(plain(plan.rows[0].fields.map(f => f.value)), [notes.b.proof, "0"], "zero is not blank");
  const full = api.snapshot(hits, sheets, selected, true, difficulty);
  assert.equal(full.rows.length, 3);
  const text = api.markdown(plan);
  assert.ok(text.indexOf("## 1.") < text.indexOf("## 2. Summation"));
  assert.ok(text.includes(notes.a.solution_summary), "original LaTeX and code preserved in Markdown");
  assert.ok(!text.includes("javascript:"));
  const built = api.html(plan, w.renderNoteMarkdown, w.katex);
  const exported = new JSDOM(built.text).window.document;
  assert.equal(exported.querySelectorAll("article").length, 2);
  assert.equal(exported.querySelectorAll("math").length, 3, "self-contained native MathML for inline and block formulas");
  assert.match(exported.querySelector("pre").textContent, /x < y/);
  assert.equal(exported.querySelectorAll("img,iframe,script[src],link").length, 0, "no injected tags or external assets");
  assert.equal(exported.querySelectorAll("script").length, 1, "only the fixed print handler runs");
  assert.match(exported.querySelector("article h2").textContent, /<script>/);
  assert.equal(exported.querySelectorAll('a[href^="javascript:"]').length, 0);
  assert.equal(built.formulasAsText, 0);
  assert.equal(api.html(plan, w.renderNoteMarkdown, null).formulasAsText, 3, "offline math failure preserves formulas");
  const broken = {...plan, rows: [{...plan.rows[0], fields: [{label: "math", value: "$\\unknowncommand{x}$"}]}]};
  assert.equal(api.html(broken, w.renderNoteMarkdown, w.katex).formulasAsText, 1);
  const withNotes = api.snapshot(hits, sheets, {...selected, notesFilter: "yes"}, true, difficulty);
  assert.deepEqual(plain(withNotes.rows.map(r => r.problem.id)), ["b", "a"]);
  const without = api.snapshot(hits, sheets, {...selected, notesFilter: "no"}, true, difficulty);
  assert.deepEqual(plain(without.rows.map(r => r.problem.id)), ["empty"]);
  const sorted = api.snapshot(hits, sheets, {...selected, clientSort: {direction: "asc", limit: 2}}, true, difficulty);
  assert.deepEqual(plain(sorted.rows.map(r => r.problem.id)), ["a", "b"], "sorts within the selected top window, excluding lower matches");

  let requested;
  const fetched = await api.collect({url: "/api/search?q=dp&k=20&offset=20&platform=codeforces&ranker=dense&sort=difficulty-asc", total: 83},
    async url => {requested = new URL(url, "http://local"); return {ok: true, json: async () => ({hits, total: 3})};});
  assert.equal(fetched.length, 3);
  assert.equal(requested.searchParams.get("offset"), "0");
  assert.equal(requested.searchParams.get("k"), "83");
  assert.equal(requested.searchParams.get("platform"), "codeforces");
  assert.equal(requested.searchParams.get("sort"), "difficulty-asc");
  assert.equal(requested.searchParams.get("ranker"), "dense");
  assert.equal(await api.collect(selected, () => {throw new Error("must not refetch a complete window");}), hits);
  await assert.rejects(api.collect({url: "/api/search", total: 80}, async () => ({ok: true, json: async () => ({hits, total: 80})})), /incomplete/);
  await assert.rejects(api.collect({url: "/api/search", total: 80}, async () => ({ok: false, status: 401})), /401/);
  await assert.rejects(api.collect({url: "/api/search", total: 3, hits}, async () => ({ok: true, json: async () => ({hits: [...hits].reverse(), total: 3})})), /order changed/);

  // Real Sheets module: pending clears override stale text, and cached custom
  // headers/values survive reload in order without leaking across accounts.
  w.eval(`cosineSheets.init({clientId: '', userId: 'one'});
    seedExportSheet();
    cosineSheets.saveNote('b', '');
    cosineSheets.init({clientId: '', userId: 'two'});`);
  assert.equal(w.cosineSheets.noteFor("b"), null);
  w.eval("cosineSheets.init({clientId: '', userId: 'one'});");
  assert.equal(w.cosineSheets.noteText("b"), "");
  assert.equal(w.cosineSheets.hasContent("b"), true, "custom content survives a cleared primary note");
  assert.deepEqual(plain(w.cosineSheets.userColumns().map(c => c.label)), ["Proof", "solution summary", "Attempts", "pending", "constructor"]);
  assert.equal(w.cosineSheets.noteFields("b").find(f => f.key === "pending").value, "review tomorrow", "custom pending column is not replaced by sync metadata");
  assert.equal(w.cosineSheets.hasContent("missing-row"), false, "column names never read inherited object properties");

  // Cancel an in-flight export when navigation/account changes; never publish
  // a partial document or leave a loading popup behind.
  let resolveFetch, downloaded = 0, closed = false;
  w.fetch = () => new Promise(resolve => {resolveFetch = resolve;});
  w.URL.createObjectURL = () => {downloaded++; return "blob:test";};
  w.open = () => ({closed: false, document: {body: {}}, close() {closed = true; this.closed = true;}});
  api.setSource({...selected, complete: false, url: "/api/search?q=dp", total: 3});
  const running = api.start("print");
  api.invalidate();
  resolveFetch({ok: true, json: async () => ({hits, total: 3})});
  await running;
  assert.equal(closed, true);
  assert.equal(downloaded, 0);
  assert.equal(doc.getElementById("notes-export").hidden, true);
  api.setSource({...selected, hits: [hits[2]]});
  await api.start("markdown");
  assert.match(doc.getElementById("notes-export-status").textContent, /No notes or custom-column content/);
  assert.equal(downloaded, 0);
  w.open = () => null;
  api.setSource(selected);
  await api.start("print");
  assert.match(doc.getElementById("notes-export-status").textContent, /Allow pop-ups/);
  let printed = "", completedClosed = false;
  w.cosineSheets.saveNote("a", "$\\pi$ and **an invariant**");
  w.open = () => ({closed: false, document: {body: {}, open() {}, write(value) {printed = value;}, close() {}},
    close() {completedClosed = true;}});
  await api.start("print");
  assert.match(printed, /<math/);
  assert.match(doc.getElementById("notes-export-status").textContent, /2 problems exported/);
  api.invalidate();
  assert.equal(completedClosed, false, "completed previews stay open when browsing continues");
  w.HTMLAnchorElement.prototype.click = function () {assert.match(this.download, /\.md$/);};
  api.setSource(selected);
  doc.getElementById("export-empty").checked = true;
  await api.start("markdown");
  assert.equal(downloaded, 1);
  assert.match(doc.getElementById("notes-export-status").textContent, /3 problems exported · 0 empty/);
  api.setSource({...selected, userId: null});
  assert.equal(doc.getElementById("notes-export").hidden, true);
  await settle(); dom.window.close();
  console.log("notes export passed: ordering, full selection, math, custom columns, empty notes, cache, safety, cancellation");
})().catch(err => {console.error(err); process.exitCode = 1;});
