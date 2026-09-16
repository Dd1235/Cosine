// Hidden labels, tested on the thing that matters: what is in the document.
//
// The whole design rests on "hidden" meaning withheld rather than styled out.
// A blurred chip is still selectable, copyable, findable with ctrl-F and read
// aloud, so the assertion that earns its keep is that NO node carrying a
// data-pattern exists anywhere in the produced tree while labels are hidden —
// not that some class was applied.
//
// app.js needs a DOM, so this lifts the two pure-ish renderers out of it and
// runs them against a DOM thin enough to answer the question, in the style of
// practice.test.js. The fake parses exactly the markup these two functions
// emit (buttons with attributes) and nothing else.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

const source = fs.readFileSync(`${__dirname}/app.js`, 'utf8');
const slice = source.slice(
  source.indexOf('function visibleMatchedTerms('),
  source.indexOf('function renderHitsList(')
);
assert.ok(slice.includes('renderPatternsInto'), 'could not slice the label renderers out of app.js');

// ── a DOM thin enough ───────────────────────────────────────────────────────
function makeNode(attrs, text) {
  const dataset = {};
  for (const [k, v] of Object.entries(attrs)) {
    if (k.startsWith('data-')) {
      dataset[k.slice(5).replace(/-([a-z])/g, (_m, c) => c.toUpperCase())] = v;
    }
  }
  return {
    attrs,
    dataset,
    className: attrs.class || '',
    textContent: text.replace(/<[^>]*>/g, ''),
    listeners: {},
    matches(sel) { return this.className.split(/\s+/).includes(sel.replace(/^\./, '')); },
    addEventListener(name, fn) { (this.listeners[name] = this.listeners[name] || []).push(fn); },
    click(event) { for (const fn of this.listeners.click || []) fn(event); },
  };
}

function parseButtons(html) {
  const nodes = [];
  for (const m of html.matchAll(/<button\b([^>]*)>([\s\S]*?)<\/button>/g)) {
    const attrs = {};
    for (const a of m[1].matchAll(/([a-zA-Z-]+)="([^"]*)"/g)) attrs[a[1]] = a[2];
    nodes.push(makeNode(attrs, m[2]));
  }
  return nodes;
}

function fakeEl() {
  return {
    _html: '',
    hidden: false,
    children: [],
    get innerHTML() { return this._html; },
    set innerHTML(v) { this._html = v; this.children = parseButtons(v); },
    querySelector(sel) { return this.children.find((n) => n.matches(sel)) || null; },
    querySelectorAll(sel) { return this.children.filter((n) => n.matches(sel)); },
    // "anywhere in the produced tree", read off the markup rather than the
    // parsed buttons, so a data-pattern smuggled onto any other element counts.
    hasDataPattern() { return /data-pattern\s*=/.test(this._html); },
  };
}

function run({ showLabels = false, patterns = ['binary-search-answer', 'dp-with-state'] } = {}) {
  const beacons = [];
  const filtered = [];
  const ctx = vm.createContext({
    showLabels,
    revealedCards: new Set(),
    escapeHtml: (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;')
      .replace(/>/g, '&gt;').replace(/"/g, '&quot;'),
    track: (type, props) => beacons.push([type, props]),
    applyPatternFilter: (p) => filtered.push(p),
  });
  vm.runInContext(slice, ctx);
  const el = fakeEl();
  const problem = { id: 'leetcode-minimum-possible-maximum', patterns };
  return { ctx, el, problem, beacons, filtered };
}

// ── (1) hidden: nothing to read ─────────────────────────────────────────────
{
  const { ctx, el, problem } = run();
  ctx.renderPatternsInto(el, problem, false);
  assert.equal(el.hasDataPattern(), false, 'a hidden label must not be in the document at all');
  assert.equal(el.querySelectorAll('.pattern-chip').length, 0);
  const lid = el.querySelector('.reveal-labels');
  assert.ok(lid, 'hidden labels are replaced by one reveal button');
  assert.equal(lid.textContent, '2 technique labels · show');
  assert.equal(lid.dataset.problemId, problem.id);
  // Nor by name anywhere in the markup — the button counts them, never lists them.
  assert.ok(!el.innerHTML.includes('binary-search-answer'), 'the button must not spell the label out');
}

// One label is not "1 technique labels".
{
  const { ctx, el, problem } = run({ patterns: ['greedy'] });
  ctx.renderPatternsInto(el, problem, false);
  assert.equal(el.querySelector('.reveal-labels').textContent, '1 technique label · show');
}

// ── (2) the reveal click ────────────────────────────────────────────────────
{
  const { ctx, el, problem, beacons, filtered } = run();
  ctx.renderPatternsInto(el, problem, false);
  let revealed = 0;
  ctx.renderPatternsInto(el, problem, false, () => { revealed++; });

  let stopped = false;
  el.querySelector('.reveal-labels').click({ stopPropagation: () => { stopped = true; } });

  // The header toggles the card open on click. Revealing a label is not asking
  // to collapse the problem you are reading, so the event must stop here.
  assert.equal(stopped, true, 'the reveal must stopPropagation or it collapses the card');
  const chips = el.querySelectorAll('.pattern-chip');
  assert.deepEqual(chips.map((c) => c.dataset.pattern), ['binary-search-answer', 'dp-with-state']);
  assert.equal(el.querySelector('.reveal-labels'), null, 'the lid is gone once opened');
  assert.deepEqual([...ctx.revealedCards], [problem.id], 'the card is remembered for this session');
  // Cross-realm: the props object is built inside the vm, so compare fields.
  assert.equal(beacons.length, 1);
  assert.equal(beacons[0][0], 'labels_revealed');
  assert.equal(beacons[0][1].problemId, problem.id);
  assert.equal(revealed, 1, 'the card repaints its other label surfaces');

  // The chips it just built are live: the filter binding survived extraction.
  let chipStopped = false;
  chips[1].click({ stopPropagation: () => { chipStopped = true; } });
  assert.deepEqual(filtered, ['dp-with-state']);
  assert.equal(chipStopped, true, 'a chip click must not toggle the card either');
}

// ── (3) the switch is on: chips straight away ───────────────────────────────
{
  const { ctx, el, problem, beacons } = run({ showLabels: true });
  ctx.renderPatternsInto(el, problem, false);
  assert.equal(el.querySelector('.reveal-labels'), null, 'no lid when labels are shown');
  assert.deepEqual(
    el.querySelectorAll('.pattern-chip').map((c) => c.dataset.pattern),
    ['binary-search-answer', 'dp-with-state']
  );
  assert.ok(el.innerHTML.includes('<strong>patterns:</strong>'));
  assert.deepEqual(beacons, [], 'showing labels is not a per-card reveal');
}

// ── (4) nothing to hide, nothing to offer ───────────────────────────────────
for (const shape of [{ patterns: [] }, {}]) {
  for (const showLabels of [false, true]) {
    const { ctx, el } = run({ showLabels });
    ctx.renderPatternsInto(el, { id: 'p0', ...shape }, false);
    assert.equal(el.innerHTML, '', `no patterns renders nothing (showLabels=${showLabels})`);
    assert.equal(el.hidden, true, 'and the paragraph is not left standing empty');
    assert.equal(el.querySelector('.reveal-labels'), null, 'never a "0 technique labels" button');
  }
}

// ── (5) the matched line cannot name what the card is hiding ────────────────
{
  const { ctx } = run();
  const hit = {
    problem: { id: 'p1', patterns: ['binary-search-answer', 'Greedy'] },
    matchedTerms: ['binary-search-answer', 'waiting', 'greedy'],
  };
  // Searching for the label is the obvious way around the switch.
  assert.deepEqual(
    [...ctx.visibleMatchedTerms(hit, false)],
    ['waiting'],
    'a matched term equal to a label is dropped; title words stay'
  );
  assert.deepEqual(
    [...ctx.visibleMatchedTerms(hit, true)],
    ['binary-search-answer', 'waiting', 'greedy'],
    'revealing the card gives the whole line back'
  );
  ctx.showLabels = true;
  assert.deepEqual([...ctx.visibleMatchedTerms(hit, false)], ['binary-search-answer', 'waiting', 'greedy']);
  ctx.showLabels = false;
  // No labels at all: nothing to subtract.
  assert.deepEqual(
    [...ctx.visibleMatchedTerms({ problem: { id: 'p2' }, matchedTerms: ['waiting'] }, false)],
    ['waiting']
  );
  assert.deepEqual([...ctx.visibleMatchedTerms({ problem: { id: 'p3' } }, false)], []);
}

console.log('label hiding passed (withheld not blurred, reveal, switch, empty, matched terms)');
