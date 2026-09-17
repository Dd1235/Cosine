// The competition picker's wording, without a DOM.
//
// These three strings are the whole user-visible contract of the control: what
// an option in the listbox says, what a resource link says about its
// availability, and which of the two sentences the resources panel carries.
// Each one was wrong at some point (0-problem shells read "0 problems", every
// public link read "· public", and the panel's sentence was written once when
// the panel was built and then went stale when the view became a similarity
// view), so they are sliced out of app.js and asserted directly.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

const source = fs.readFileSync(`${__dirname}/app.js`, 'utf8');
const helpers = source.slice(
  source.indexOf('function collectionCountPhrase('),
  source.indexOf('function renderCollectionControls(')
);
const ctx = vm.createContext({ currentSimilar: null });
vm.runInContext(helpers, ctx);

// Option labels.
assert.equal(
  ctx.collectionOptionLabel({ name: 'ICPC World Finals 2024', count: 12 }),
  'ICPC World Finals 2024 · 12 problems'
);
assert.equal(
  ctx.collectionOptionLabel({ name: 'IICPC Quantfest 2025 Prelims', count: 0 }),
  'IICPC Quantfest 2025 Prelims · resources only',
  'a collection with nothing indexed offers its resources, not "0 problems"'
);
assert.equal(
  ctx.collectionOptionLabel({ name: 'One', count: 1 }),
  'One · 1 problem',
  'singular'
);
assert.equal(
  ctx.collectionOptionLabel({ name: 'ICPC India Prelims 2025–26', count: 5, unavailableCount: 1 }),
  'ICPC India Prelims 2025–26 · 5 problems · 1 not yet indexed'
);
assert.equal(
  ctx.collectionOptionLabel({ name: 'ICPC World Finals archive', count: 0, unavailableCount: 3 }),
  'ICPC World Finals archive · resources only · 3 not yet indexed'
);

// Resource availability. The registry vocabulary is public | inaccessible |
// not-verified — "public" is the ordinary case and says nothing.
assert.equal(ctx.resourceAvailabilityNote('public'), '', 'a public link is not annotated');
assert.equal(ctx.resourceAvailabilityNote('inaccessible'), ' · inaccessible');
assert.equal(ctx.resourceAvailabilityNote('not-verified'), ' · not verified');
assert.equal(ctx.resourceAvailabilityNote(undefined), '');

// Only the similarity view carries a sentence, and which view it is has to be
// read at render time rather than when the panel was built. A plain collection
// view says nothing: the chip already names the competition.
assert.equal(ctx.collectionNote(null), '', 'a collection view needs no caveat');
assert.match(ctx.collectionNote({ id: 'codeforces-1-a' }), /^Related practice/);
ctx.currentSimilar = { id: 'codeforces-1-a' };
assert.match(ctx.collectionNote(), /^Related practice/, 'defaults to the live view');

// The picker option and the resources panel now share one count phrase, so
// the panel can no longer say "0 searchable problems" about a collection the
// picker calls "resources only".
assert.equal(ctx.collectionCountPhrase({ count: 0 }), 'resources only');
assert.equal(ctx.collectionCountPhrase({ count: 1 }), '1 problem');
assert.equal(ctx.collectionCountPhrase({ count: 12, unavailableCount: 2 }), '12 problems · 2 not yet indexed');
assert.equal(ctx.collectionOptionLabel({ name: 'Q', count: 0 }), `Q · ${ctx.collectionCountPhrase({ count: 0 })}`);

// The competition tag shows every membership up to two, because a problem can
// really be in two contests (Luxor ran WF 2022 and WF 2023 together).
const tagSrc = source.slice(source.indexOf('function competitionTag('), source.indexOf('function renderHitsList('));
const tagCtx = vm.createContext({ escapeHtml: (x) => String(x) });
vm.runInContext(tagSrc, tagCtx);
const two = tagCtx.competitionTag([{ id: 'wf22', name: 'WF 2022', short: 'WF 2022' }, { id: 'wf23', name: 'WF 2023', short: 'WF 2023' }]);
assert.equal((two.match(/data-collection="/g) || []).length, 2, 'both memberships are chips');
assert.ok(two.includes('data-collection="wf22"') && two.includes('data-collection="wf23"'));
assert.ok(!two.includes('+1'), 'no "+1" when both fit');
const three = tagCtx.competitionTag([{ id: 'a', name: 'A' }, { id: 'b', name: 'B' }, { id: 'c', name: 'C' }]);
assert.equal((three.match(/data-collection="/g) || []).length, 2);
assert.ok(three.includes('+1'), 'past two it compresses');
assert.equal(tagCtx.competitionTag([]), '');

console.log('collection picker copy tests passed');
