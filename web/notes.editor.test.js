// Real DOM interaction tests, no network or production account required.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const { JSDOM } = require("jsdom");

async function main() {
  const dom = new JSDOM(fs.readFileSync(`${__dirname}/index.html`, "utf8"), {
    url: "http://localhost:3100", runScripts: "outside-only",
  });
  const w = dom.window;
  const style = w.document.createElement("style");
  style.textContent = fs.readFileSync(`${__dirname}/styles.css`, "utf8");
  w.document.head.appendChild(style);
  // Run the exact browser build, not a mock of the math API.
  w.eval(fs.readFileSync(require.resolve("katex"), "utf8"));
  w.eval(fs.readFileSync(`${__dirname}/sheets.js`, "utf8") + "\nwindow.cosineSheets = cosineSheets;");
  const src = fs.readFileSync(`${__dirname}/app.js`, "utf8");
  w.eval(`function track() {} function markSheetDirty() {} function setStatus() {} function refreshNoteOnCard() {}\n`
    + src.slice(src.indexOf("let noteTarget = null;"), src.indexOf("function formatRelative(")));
  w.eval('cosineSheets.init({clientId: "", userId: "local-test"})');
  const ta = w.document.getElementById("note-text");
  const preview = w.document.getElementById("note-preview");
  const dialog = w.document.getElementById("note-dialog");
  const hit = {problem: {id: "cses-2072", title: "Cut and Paste"}};
  w.openNoteEditor(hit);
  ta.value = "invariant";
  ta.select();
  w.document.querySelector('[data-wrap="**"]').click();
  assert.equal(ta.value, "**invariant**");
  ta.value = "a\nb\nc";
  ta.setSelectionRange(0, 4);
  ta.dispatchEvent(new w.KeyboardEvent("keydown", {key: "]", ctrlKey: true, cancelable: true}));
  assert.equal(ta.value, "  a\n  b\nc", "indent all selected lines without deleting code");
  ta.dispatchEvent(new w.KeyboardEvent("keydown", {key: "[", ctrlKey: true, cancelable: true}));
  assert.equal(ta.value, "a\nb\nc", "unindent restores text");
  const tab = new w.KeyboardEvent("keydown", {key: "Tab", cancelable: true});
  ta.dispatchEvent(tab);
  assert.equal(tab.defaultPrevented, false, "Tab can leave the editor");

  // jsdom has no layout engine. Explicitly model browser scrolling caused by
  // focus, edits and selection changes, then check our restoration boundary.
  const nativeFocus = ta.focus.bind(ta);
  const nativeSelection = ta.setSelectionRange.bind(ta);
  ta.focus = options => {
    if (!options?.preventScroll) { ta.scrollTop = 0; dialog.scrollTop = 0; }
    nativeFocus(options);
  };
  ta.setSelectionRange = (...args) => {
    nativeSelection(...args);
    ta.scrollTop = 0; ta.scrollLeft = 0; dialog.scrollTop = 0;
  };
  const longNote = "line with code and explanation\n".repeat(100) + "target\n" + "more detail\n".repeat(100);
  const at = longNote.indexOf("target");
  const replacements = [];
  for (const nativeEditing of [false, true]) {
    w.document.execCommand = nativeEditing ? (command, _ui, replacement) => {
      assert.equal(command, "insertText");
      replacements.push([ta.selectionEnd - ta.selectionStart, replacement.length]);
      ta.setRangeText(replacement, ta.selectionStart, ta.selectionEnd, "end");
      ta.scrollTop = 0; dialog.scrollTop = 0;
      return true;
    } : undefined;
    for (const dataset of [{wrap: "**"}, {insert: "π"}, {block: "```", language: "cpp"}, {prefix: "- "}, {template: "cp"}]) {
      ta.value = longNote;
      ta.setSelectionRange(at, at + 6);
      ta.scrollTop = 900; ta.scrollLeft = 25; dialog.scrollTop = 120;
      w.applyNoteTool({dataset});
      assert.equal(ta.scrollTop, 900, "formatting preserves the long-note viewport");
      assert.equal(ta.scrollLeft, 25, "formatting preserves horizontal code scroll");
      assert.equal(dialog.scrollTop, 120, "formatting does not jump the modal");
      assert.ok(ta.selectionStart >= at, "caret stays near the edit");
    }
    ta.value = longNote;
    ta.setSelectionRange(at, at + 6);
    ta.scrollTop = 900; dialog.scrollTop = 120;
    w.indentNote(false);
    assert.equal(ta.scrollTop, 900, "keyboard indentation preserves the viewport too");
    assert.equal(dialog.scrollTop, 120);
  }
  assert.ok(replacements.every(([removed, added]) => removed < 200 && added < 300), "native undo edits only the affected range, not the whole note");
  ta.focus = nativeFocus;
  ta.setSelectionRange = nativeSelection;
  delete w.document.execCommand;

  // Hiding/rebuilding a pane can reset its DOM scroll offset. Each mode keeps
  // its own remembered position and restores it after being made visible.
  ta.scrollTop = 900; ta.scrollLeft = 25;
  w.setNoteMode("preview");
  preview.scrollTop = 600; preview.scrollLeft = 15;
  w.setNoteMode("write");
  assert.equal(ta.scrollTop, 900);
  assert.equal(ta.scrollLeft, 25);
  preview.scrollTop = preview.scrollLeft = 0;
  w.setNoteMode("preview");
  assert.equal(preview.scrollTop, 600, "returning to preview keeps the reading position");
  assert.equal(preview.scrollLeft, 15);
  w.openNoteEditor(hit);
  w.setNoteMode("preview");
  assert.equal(preview.scrollTop, 0, "reopening a note does not inherit another editing session's preview scroll");
  w.setNoteMode("write");

  ta.value = "return a < b;";
  ta.select();
  w.document.querySelector('[data-block="```"]').click();
  assert.equal(ta.value, "```cpp\nreturn a < b;\n```\n");
  w.document.querySelector('[data-note-mode="preview"]').click();
  assert.equal(preview.hidden, false);
  assert.equal(w.getComputedStyle(w.document.getElementById("note-tools")).display, "none");
  assert.equal(preview.querySelector("pre").textContent, "return a < b;");
  assert.equal(preview.querySelector("pre").dataset.lang, "cpp");

  // Every shipped formula snippet must produce accessible math, not an error.
  for (const btn of w.document.querySelectorAll('[aria-label="LaTeX formula snippets"] button')) {
    w.setNoteMode("write");
    ta.value = "";
    btn.click();
    assert.equal(ta.value, btn.dataset.insert);
    w.setNoteMode("preview");
    await new Promise(setImmediate);
    assert.ok(preview.querySelector(".katex math"), `${btn.textContent} rendered with MathML`);
    assert.equal(preview.querySelector(".note-math-error"), null);
  }
  ta.value = '## Recurrence\n$$\n\\sum_{i=1}^{n} \\frac{a_i}{2^i}\n$$\n- **Invariant**\n1. compress\n2. transition\n`$not math$`\n<script>alert(1)</script>\n$\\href{javascript:alert(1)}{click}$';
  w.setNoteMode("preview");
  await new Promise(setImmediate);
  assert.ok(preview.querySelector(".katex-display"));
  assert.equal(preview.querySelectorAll("li").length, 3);
  assert.equal(preview.querySelector("code").textContent, "$not math$");
  assert.equal(preview.querySelector("script, a, img"), null, "untrusted note cannot create active content");
  assert.ok(preview.textContent.includes("<script>"));
  ta.value = "$\\unknowncommand{x}$";
  w.setNoteMode("preview");
  await new Promise(setImmediate);
  assert.ok(preview.querySelector(".note-math-error"));
  assert.equal(preview.textContent, ta.value, "invalid math remains readable");

  w.setNoteMode("write");
  ta.value = "saved ∑ note $\\pi$";
  ta.dispatchEvent(new w.KeyboardEvent("keydown", {key: "Enter", ctrlKey: true, cancelable: true}));
  w.openNoteEditor(hit);
  assert.equal(ta.value, "saved ∑ note $\\pi$", "save and reopen preserves the exact sheet text");
  ta.value += " draft";
  w.confirm = () => false;
  dialog.dispatchEvent(new w.Event("cancel", {cancelable: true}));
  assert.ok(dialog.open, "declining discard keeps unsaved changes open");
  // Storage is tested more thoroughly in notes.test; the editor must also
  // keep the user's text visible on any save failure.
  w.eval('cosineSheets.saveNote = () => { throw new Error("quota") }');
  w.saveNoteEditor();
  assert.ok(dialog.open);
  assert.match(w.document.getElementById("note-state").textContent, /Could not save/);
  assert.ok(ta.value.endsWith("draft"));

  // Offline fallback, single in-flight download, and a later retry.
  const math = w.katex;
  delete w.katex;
  const one = w.renderNoteMath("x^2", false);
  const two = w.renderNoteMath("n!", false);
  assert.equal(one.textContent, "$x^2$");
  assert.equal(w.document.querySelectorAll('script[src="/vendor/katex/katex.min.js"]').length, 1);
  const script = w.document.querySelector('script[src="/vendor/katex/katex.min.js"]');
  script.onerror();
  await new Promise(setImmediate);
  assert.equal(two.textContent, "$n!$");
  assert.match(one.title, /unavailable/);
  const retry = w.renderNoteMath("n!", false);
  w.katex = math;
  w.document.querySelector('script[src="/vendor/katex/katex.min.js"]').onload();
  await new Promise(setImmediate);
  assert.ok(retry.querySelector("math"));
  assert.equal(w.document.querySelectorAll("#note-math-css").length, 1);
  dom.window.close();
  console.log("note editor DOM tests passed (formatting, math, security, keyboard, persistence)");
}
main().catch(error => { console.error(error); process.exitCode = 1; });
