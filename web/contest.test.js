// The contest page's data layer, sliced out of app.js and run in a vm — the
// same trick web/urlstate.test.js and web/practice.test.js use.
//
// What is worth guarding here is everything the page claims that the search
// index cannot: the order the problems ran in, the problems that are missing
// from the corpus entirely, and how many of the SET (not of the searchable
// part of it) you have finished. Each of those is a sentence a reader will
// believe, and each of them is derived rather than fetched.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const difficulty = require('./difficulty.js');

const source = fs.readFileSync(`${__dirname}/app.js`, 'utf8');
const block = source.slice(
  source.indexOf('function contestLetterRank('),
  source.indexOf('function renderContestList(')
);
const helpers = source.slice(
  source.indexOf('function safeResourceUrl('),
  source.indexOf('// Collections are a facet')
) + source.slice(
  source.indexOf('function resourceAvailabilityNote('),
  source.indexOf('// Only the similarity view needs a caveat')
);

function context(extra = {}) {
  const ctx = vm.createContext({
    cosineDifficulty: difficulty,
    escapeHtml: (x) => String(x).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/"/g, '&quot;'),
    URL, Map, Set, Number, ...extra,
  });
  vm.runInContext(helpers + block, ctx);
  return ctx;
}
const ctx = context();
const hit = (id, patterns = []) => ({ problem: { id, title: id, platform: 'kattis', patterns } });

// ── the unindexed row ────────────────────────────────────────────────────────
// This row is the whole reason the view exists. The members we could not index
// are not a random remainder: on Kattis's own 1-10 scale they are 9.2, 9.1 and
// 8.4, so "3 not yet indexed" was hiding the hard end of every set.
{
  const row = ctx.renderContestUnindexedRow({
    id: 'kattis-div2mul2mul3',
    title: 'Div 2, Mul 2, Mul 3',
    url: 'https://open.kattis.com/problems/div2mul2mul3',
    kattis_difficulty: { score: 9.2, label: 'hard' },
  });
  assert.match(row, /Div 2, Mul 2, Mul 3/);
  assert.match(row, /9\.2 · Kattis/, "the judge's own number, named as theirs");
  assert.match(row, /class="difficulty hard"/);
  assert.match(row, /href="https:\/\/open\.kattis\.com\/problems\/div2mul2mul3"/);
  assert.match(row, /rel="noopener"/);
  assert.match(row, /not yet labelled/);
}
// Kattis publishes no score for every problem, and a bordered chip standing in
// for nothing is furniture.
{
  const row = ctx.renderContestUnindexedRow({
    id: 'kattis-kindergarten2',
    title: 'Kindergarten',
    url: 'https://icpc.kattis.com/problems/kindergarten2',
  });
  assert.match(row, /Kindergarten/);
  assert.ok(!row.includes('class="difficulty'), 'no difficulty chip without a difficulty');
  assert.match(row, /not yet labelled/);
}
// No url, no link — and never a link to something that is not http(s).
{
  const bare = ctx.renderContestUnindexedRow({ id: 'kattis-x' });
  assert.ok(!bare.includes('<a '), 'nothing to open');
  assert.match(bare, /kattis-x/, 'the id stands in for a title we never learned');
  const hostile = ctx.renderContestUnindexedRow({ id: 'x', url: 'javascript:alert(1)' });
  assert.ok(!hostile.includes('<a '), 'safeResourceUrl gates the member url like any other');
}

// ── merge and order ──────────────────────────────────────────────────────────
{
  const members = [{ id: 'a' }, { id: 'b' }, { id: 'c' }];
  const rows = ctx.contestRows(members, [hit('c'), hit('a')]);
  assert.deepEqual(rows.map((r) => r.member.id), ['a', 'b', 'c'],
    'with nothing to order by, the registry order is the order');
  assert.deepEqual(rows.map((r) => !!r.hit), [true, false, true],
    'a member with no hit is still a row');
  assert.equal(rows[0].hit.problem.id, 'a', 'hits merge by id, not by position');
}
// An explicit order beats the position the registry put it in.
{
  const rows = ctx.contestRows([{ id: 'a', order: 3 }, { id: 'b', order: 1 }, { id: 'c', order: 2 }], []);
  assert.deepEqual(rows.map((r) => r.member.id), ['b', 'c', 'a']);
}
// A member without one falls back to its registry position, which is 1-based
// so it interleaves with `order` rather than sorting to the end.
{
  const rows = ctx.contestRows([{ id: 'a', order: 3 }, { id: 'b' }, { id: 'c', order: 1 }], []);
  assert.deepEqual(rows.map((r) => r.member.id), ['c', 'b', 'a']);
}
// Letters sort as letters, not as strings, and not as registry position.
{
  const rows = ctx.contestRows([{ id: 'f', letter: 'F' }, { id: 'a', letter: 'A' }, { id: 'b', letter: 'B' }], []);
  assert.deepEqual(rows.map((r) => r.member.id), ['a', 'b', 'f']);
  const split = ctx.contestRows([{ id: 'b2', letter: 'B2' }, { id: 'c', letter: 'C' }, { id: 'b', letter: 'B' }], []);
  assert.deepEqual(split.map((r) => r.member.id), ['b', 'b2', 'c'], 'B2 is part of B, so it sits inside it');
}

// ── how much of the SET is done ──────────────────────────────────────────────
// The denominator is every member, including the ones with no statement here.
// Counting only indexed members would report a contest finished while three of
// its problems had never been shown to anybody.
{
  const ids = ['a', 'b', 'c', 'd'];
  assert.equal(ctx.contestDoneCount(ids, new Set(['a', 'c', 'zzz'])), 2);
  assert.equal(ctx.contestDoneCount(ids, ['a']), 1, 'an array works as well as a Set');
  assert.equal(ctx.contestDoneCount(ids, new Set()), 0);
  assert.equal(ctx.contestDoneCount([], new Set(['a'])), 0);
}

// ── the order caveat ─────────────────────────────────────────────────────────
// Seven collections came from Kattis source pages, which list problems
// alphabetically and print no letters. Saying so is the honest alternative to
// making letters up.
{
  assert.equal(ctx.contestOrderUnverified([{ id: 'kattis-a' }, { id: 'kattis-b' }]), true);
  assert.equal(ctx.contestOrderUnverified([{ id: 'kattis-a', letter: 'A' }, { id: 'kattis-b' }]), false,
    'one real letter is enough to stop claiming the order is unknown');
  assert.equal(ctx.contestOrderUnverified([{ id: 'kattis-a', order: 1 }]), false);
  // A gym id ends in the problem's actual letter, so that set IS ordered.
  assert.equal(ctx.contestOrderUnverified(
    ['a', 'b', 'c', 'd', 'e', 'f'].map((l) => ({ id: `codeforces-106179-${l}` }))), false);
  assert.equal(ctx.contestOrderUnverified([]), false, 'an empty set has no order to doubt');
}

// ── the topic tally ──────────────────────────────────────────────────────────
{
  const tally = ctx.contestTopicTally([
    hit('a', ['dp', 'greedy']),
    hit('b', ['dp', 'geometry']),
    hit('c', ['dp']),
    hit('d', []),
  ]);
  // JSON rather than deepEqual: vm arrays are from another realm, so their
  // prototypes never compare strictly equal.
  assert.equal(JSON.stringify(tally), JSON.stringify([['dp', 3], ['geometry', 1], ['greedy', 1]]),
    'descending by count, then alphabetical so the order is stable');
  assert.equal(ctx.contestTopicTally([]).length, 0);
}

// ── the header ───────────────────────────────────────────────────────────────
const kattisCollection = {
  id: 'icpc-asia-can-tho-2020',
  name: 'ICPC Asia Can Tho 2020',
  organizer: 'ICPC',
  location: 'Vietnam',
  held_date: null,
  problems: ['a', 'b'],
  evidence: ['https://open.kattis.com/problem-sources/x'],
  resources: [
    { title: 'Judge', url: 'https://open.kattis.com/contests/x', kind: 'judge', availability: 'public' },
    { title: 'Editorial', url: 'https://example.com/e', kind: 'editorial', availability: 'not-verified' },
  ],
};
{
  const html = ctx.contestHeaderHtml(kattisCollection, [hit('a', ['dp'])], [{ id: 'a' }, { id: 'b' }], null);
  assert.match(html, /ICPC Asia Can Tho 2020/);
  assert.match(html, /Vietnam · ICPC/, 'the dim line omits a null held date rather than printing "null"');
  assert.match(html, /Statements from Kattis; this is the original judge\./);
  assert.match(html, /problem order not verified/);
  assert.ok(!html.includes('done<'), 'signed out there is nothing to intersect, so the line is absent');
  // Editorials and booklets first — the judge link is already on every row.
  assert.ok(html.indexOf('Editorial') < html.indexOf('>Judge<'));
  assert.match(html, /Editorial<\/a> · not verified/);
  assert.match(html, /<details class="contest-topics"><summary>by topic<\/summary>/);
  assert.ok(!html.includes('<details class="contest-topics" open'), 'the tally is NEVER open by default');
  assert.match(html, /data-pattern="dp"[^>]*>dp<\/button> × 1/);
}
// The caveat is about our data, so a set that knows its own letters never says it.
{
  const gym = {
    id: 'icpc-india-prelims-2025-26',
    name: 'ICPC India Prelims',
    organizer: 'ICPC',
    held_date: null,
    problems: ['codeforces-106179-a', 'codeforces-106179-f'],
    evidence: ['https://codeforces.com/gym/106179'],
    resources: [{ title: 'Gym', url: 'https://codeforces.com/gym/106179', kind: 'judge', availability: 'public' }],
  };
  const members = [{ id: 'codeforces-106179-a' }, { id: 'codeforces-106179-f', title: 'Non Unique' }];
  const html = ctx.contestHeaderHtml(gym, [], members, new Set(['codeforces-106179-a']));
  assert.ok(!html.includes('problem order not verified'), 'gym ids carry the real letters');
  assert.match(html, /Statements from the Codeforces gym\./);
  assert.match(html, /1 of 2 done/);
  assert.ok(!html.includes('contest-topics'), 'no indexed hits, so there is nothing to tally');
}

// Hiding labels does not remove the tally, it renames the door. The flag is
// read defensively because it belongs to the labels-hidden toggle, not here.
{
  const hidden = context({ showLabels: false });
  assert.match(
    hidden.contestHeaderHtml(kattisCollection, [hit('a', ['dp'])], [{ id: 'a' }], null),
    /<summary>by topic · reveals labels<\/summary>/
  );
  assert.match(
    context({ showLabels: true }).contestHeaderHtml(kattisCollection, [hit('a', ['dp'])], [{ id: 'a' }], null),
    /<summary>by topic<\/summary>/
  );
}

// ── the list itself ──────────────────────────────────────────────────────────
// A DOM thin enough to answer "what did it build, and which renderer drew each
// row" without pretending to be a browser. The point is that an indexed member
// goes to renderHitsList — the one function that knows how to draw a card —
// and an unindexed one does not, because there is no card to draw.
{
  const node = (tag) => ({
    tag, className: '', innerHTML: '', textContent: '', dataset: {}, children: [],
    appendChild(child) { this.children.push(child); return child; },
    addEventListener() {},
    querySelectorAll: () => [],
    querySelector: () => null,
  });
  const results = node('ul');
  const drawn = [];
  const listCtx = vm.createContext({
    cosineDifficulty: difficulty,
    escapeHtml: (x) => String(x),
    resultsEl: results,
    document: { createElement: node },
    renderHitsList: (container, hits, opts) => drawn.push({ hits, opts }),
    applyPatternFilter() {}, track() {},
    URL, Map, Set, Number,
  });
  vm.runInContext(
    helpers + source.slice(source.indexOf('function contestLetterRank('), source.indexOf('// Done ids come from the same endpoint')),
    listCtx
  );
  const members = [
    { id: 'kattis-alchemy101', letter: 'A' },
    { id: 'kattis-div2mul2mul3', letter: 'B', title: 'Div 2, Mul 2, Mul 3', url: 'https://open.kattis.com/problems/div2mul2mul3' },
  ];
  listCtx.renderContestList(kattisCollection, [hit('kattis-alchemy101', ['dp'])], members, null);
  assert.equal(results.children.length, 3, 'a header and one row per member, indexed or not');
  assert.equal(results.children[0].className, 'contest-header');
  assert.deepEqual(results.children.slice(1).map((c) => c.className), ['result contest-row', 'result contest-row']);
  assert.deepEqual(results.children.slice(1).map((c) => c.children[0].textContent), ['A', 'B'],
    'the letter cell is prefixed to both kinds of row');
  assert.equal(drawn.length, 1, 'only the indexed member is drawn as a card');
  assert.equal(drawn[0].hits[0].problem.id, 'kattis-alchemy101');
  assert.equal(drawn[0].opts.unranked, true, 'a contest is not a ranking, so no score bar');
  const unindexed = results.children[2].children[1];
  assert.match(unindexed.innerHTML, /Div 2, Mul 2, Mul 3/);
  assert.match(unindexed.innerHTML, /not yet labelled/);
}

console.log('contest page order, merge, progress and header tests passed');
