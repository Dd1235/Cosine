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
  source.indexOf('function collectionOptionLabel('),
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

// The panel sentence flips with the view, not with when the panel was built.
assert.match(ctx.collectionNote(null), /^Verified collection membership/);
assert.match(ctx.collectionNote({ id: 'codeforces-1-a' }), /^Related practice/);
ctx.currentSimilar = { id: 'codeforces-1-a' };
assert.match(ctx.collectionNote(), /^Related practice/, 'defaults to the live view');

console.log('collection picker copy tests passed');
