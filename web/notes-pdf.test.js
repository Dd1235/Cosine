const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const {JSDOM} = require("jsdom");

(async () => {
  const dom = new JSDOM("<!doctype html>", {runScripts: "outside-only", url: "http://localhost:3100"});
  const w = dom.window;
  for (const file of [require.resolve("katex"), path.join(__dirname, "notes-export.js"), path.join(__dirname, "notes-pdf.js")]) w.eval(fs.readFileSync(file, "utf8"));
  const app = fs.readFileSync(path.join(__dirname, "app.js"), "utf8");
  w.eval(app.slice(app.indexOf("function renderNoteMarkdown("), app.indexOf("function formatRelative(")));
  w.MathJax = {startup: {typeset: false}, svg: {fontCache: "none"}};
  w.eval(fs.readFileSync(require.resolve("mathjax-full/es5/mml-svg.js"), "utf8"));
  await w.MathJax.startup.promise;
  const plan = {context: "Bookmarks · oldest first", viewUrl: "https://onebysec.com/?q=:bookmarks", skipped: 1, createdAt: "2026-09-18T12:00:00Z", rows: [
    {problem: {id: "cf:1", title: "Prefix sums and invariants", platform: "codeforces", url: "https://codeforces.com/problemset/problem/1/A"}, difficulty: "1400", fields: [
      {label: "Notes", value: "# Approach\n**Keep the invariant** and *prove it* before writing `lower_bound`.\n- Build prefix sums\n- Answer each query\n$$\n\\sum_{i=1}^{n} i = \\frac{n(n+1)}{2}\n$$\nCost $O(n \\log n)$ with $\\pi \\approx 3.14159$.\n```cpp\n" + Array.from({length: 80}, (_, i) => `    dp[${i}] = dp[${i - 1}] + cost; // transition`).join("\n") + "\n```"},
      {label: "Proof (custom column)", value: "1. Base case\n2. Induction step\nA very long identifier: " + "long_identifier_".repeat(25)},
      {label: "Attempts", value: "0\nPlain symbols: → ∈ ∅ ⌊x⌋ ∑ π ∞ ≤ ≥ ≠ Θ α β"},
    ]},
    {problem: {id: "cses:2", title: "Empty note included explicitly", platform: "cses"}, fields: []},
  ]};
  const html = w.cosineNotesExport.html(plan, w.renderNoteMarkdown, w.katex);
  const result = w.cosineNotesPdf.definition(html.text, mml => w.MathJax.mathml2svg(mml).querySelector("svg"));
  assert.equal(result.formulasAsText, 0);
  const serialized = JSON.stringify(result.document);
  assert.match(serialized, /Proof \(custom column\)/);
  assert.match(serialized, /No notes or custom-column content/);
  assert.match(serialized, /"svg"/);
  assert.ok(serialized.indexOf("Prefix sums") < serialized.indexOf("Empty note"));
  assert.ok(!serialized.includes("Print / Save as PDF"));
  assert.equal(w.cosineNotesPdf.definition(html.text, () => {throw new Error("bad math");}).formulasAsText, 3);
  const pdf = require("pdfmake/build/pdfmake.js");
  pdf.addVirtualFileSystem(require("pdfmake/build/vfs_fonts.js"));
  pdf.addVirtualFileSystem({"mono.woff": fs.readFileSync(require.resolve("@fontsource/roboto-mono/files/roboto-mono-latin-400-normal.woff")).toString("base64")});
  pdf.addFonts({Mono: {normal: "mono.woff", bold: "mono.woff", italics: "mono.woff", bolditalics: "mono.woff"}});
  pdf.addVirtualFileSystem({"symbols.woff": fs.readFileSync(require.resolve("@fontsource/noto-sans-math/files/noto-sans-math-latin-400-normal.woff")).toString("base64")});
  pdf.addFonts({Symbols: {normal: "symbols.woff", bold: "symbols.woff", italics: "symbols.woff", bolditalics: "symbols.woff"}});
  const bytes = await pdf.createPdf(result.document).getBuffer();
  assert.equal(bytes.subarray(0, 5).toString(), "%PDF-");
  assert.ok(bytes.length > 10000);
  if (process.env.PDF_QA_PATH) fs.writeFileSync(process.env.PDF_QA_PATH, bytes);
  dom.window.close();
  // Optional integration against the running app: use the actual lazy loader,
  // minified bundle, static routes, and fetched WOFF fonts. No account needed.
  if (process.env.PDF_TEST_ORIGIN) {
    const live = new JSDOM("<!doctype html>", {url: process.env.PDF_TEST_ORIGIN, runScripts: "dangerously", resources: "usable",
      beforeParse(window) {
        window.TextEncoder = TextEncoder; window.TextDecoder = TextDecoder;
        window.fetch = async (...args) => {
          const response = await fetch(...args);
          return {ok: response.ok, status: response.status,
            arrayBuffer: async () => window.Uint8Array.from(new Uint8Array(await response.arrayBuffer())).buffer};
        };
      }});
    try {
      live.window.eval(fs.readFileSync(path.join(__dirname, "notes-pdf.js"), "utf8"));
      const downloaded = await live.window.cosineNotesPdf.create(html.text);
      assert.ok(downloaded.bytes.length > 10000);
      assert.equal(downloaded.formulasAsText, 0);
    } finally { live.window.close(); }
  }
  console.log("notes PDF passed: real browser bundles, vector formulas, code pagination, custom columns, empty notes, fallback");
})().catch(error => { console.error(error); process.exitCode = 1; });
