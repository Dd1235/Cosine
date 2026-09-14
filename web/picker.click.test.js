// Clicking a competition in the picker must add it.
//
// This shipped broken. Every existing picker test asserted wording or keyboard
// movement, so nothing exercised a mouse click, and the control worked with the
// keyboard while doing nothing at all with the mouse in Safari.
//
// The mechanism: openCollectionPicker() focuses the first option. Chrome and
// Firefox focus a <button> on mousedown, so clicking a different option moved
// focus within the listbox and the focusout handler saw a relatedTarget inside
// the picker and left it open. Safari does not focus buttons on mousedown, so
// focus fell to the body, focusout fired with relatedTarget null, the handler
// hid the picker, and the option was display:none before the click could land.
//
// The two guards are asserted here: options preventDefault on mousedown so
// focus never leaves, and focusout defers its close so a null relatedTarget
// mid-click cannot destroy the option.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

const source = fs.readFileSync(`${__dirname}/app.js`, 'utf8');

// Enough of a DOM to carry listeners, containment and focus.
function makeDom() {
  const doc = { activeElement: null };
  function node(tag = 'div') {
    const n = {
      tag, hidden: false, children: [], listeners: {}, dataset: {}, attrs: {},
      textContent: '', type: '', className: '',
      classList: {
        _s: new Set(),
        add(c) { this._s.add(c); }, remove(c) { this._s.delete(c); },
        contains(c) { return this._s.has(c); },
        toggle(c, on) { if (on === undefined) on = !this._s.has(c); on ? this._s.add(c) : this._s.delete(c); },
      },
      setAttribute(k, v) { this.attrs[k] = v; },
      getAttribute(k) { return this.attrs[k]; },
      appendChild(c) { this.children.push(c); c.parent = n; return c; },
      addEventListener(name, fn) { (this.listeners[name] = this.listeners[name] || []).push(fn); },
      contains(other) {
        for (let p = other; p; p = p.parent) if (p === n) return true;
        return false;
      },
      focus() { doc.activeElement = n; },
      querySelectorAll(sel) {
        const want = sel.replace('.', '');
        return this.children.filter((c) => c.classList.contains(want) || c.className === want);
      },
      set innerHTML(v) { if (v === '') this.children = []; },
      get innerHTML() { return ''; },
      dispatch(name, ev = {}) {
        let prevented = false;
        const event = { type: name, preventDefault() { prevented = true; }, ...ev };
        for (const fn of this.listeners[name] || []) fn(event);
        // bubble to ancestors
        for (let p = n.parent; p; p = p.parent) for (const fn of (p.listeners[name] || [])) fn(event);
        return { prevented };
      },
    };
    return n;
  }
  return { doc, node };
}

const { doc, node } = makeDom();
const picker = node('div');
const add = node('button');
picker.className = 'picker';

const added = [];
const timers = [];

const ctx = vm.createContext({
  document: {
    getElementById: (id) => (id === 'collection-picker' ? picker : id === 'collection-add' ? add : null),
    createElement: (t) => node(t),
    addEventListener() {},
    get activeElement() { return doc.activeElement; },
  },
  setTimeout: (fn) => { timers.push(fn); },
  collectionsLoaded: true,
  activeCollections: new Set(),
  collectionSpoilers: false,
  currentOffset: 0,
  inactiveCollections: () => ([
    { id: 'icpc-world-finals-2024', name: 'ICPC World Finals 2024', count: 10 },
    { id: 'icpc-asia-danang-2019', name: 'ICPC Asia Danang Regional 2019', count: 9 },
  ]),
  collectionOptionLabel: (c) => `${c.name} · ${c.count} problems`,
  renderCollectionControls: () => {},
  syncUrl: () => {},
  reissueCurrentView: () => {},
  addCollection: (id) => { added.push(id); },
});

// The picker functions, plus the listener block that wires the container.
const fns = source.slice(
  source.indexOf('function renderCollectionPicker('),
  source.indexOf('function addCollection(')
);
vm.runInContext(fns, ctx);

const wiring = source.slice(
  source.indexOf("const collectionPickerEl = document.getElementById('collection-picker');"),
  source.indexOf('function syncCsesLevelControl()')
);
vm.runInContext(`const collectionAddBtn = document.getElementById('collection-add');\n${wiring}`, ctx);

ctx.renderCollectionPicker(true);
assert.equal(picker.children.length, 2, 'both inactive collections are offered');

ctx.openCollectionPicker();
assert.equal(picker.hidden, false, 'picker opens');
assert.equal(doc.activeElement, picker.children[0], 'first option takes focus');

// --- the Safari sequence, on an option that is NOT the focused one ---
const target = picker.children[1];

const md = target.dispatch('mousedown');
assert.equal(md.prevented, true, 'mousedown is prevented so focus never leaves the listbox');

// Even if focus did escape, focusout must not tear the option down synchronously.
picker.dispatch('focusout', { relatedTarget: null });
assert.equal(picker.hidden, false, 'a null relatedTarget does not close the picker synchronously');

target.dispatch('click');
assert.deepEqual(added, ['icpc-asia-danang-2019'], 'the clicked competition is the one added');
assert.equal(picker.hidden, true, 'picker closes once the choice is made');

// --- a genuine tab-out still closes, once the deferred check runs ---
added.length = 0;
timers.length = 0;
ctx.renderCollectionPicker(true);
ctx.openCollectionPicker();
assert.equal(picker.hidden, false);
doc.activeElement = node('input'); // focus really did leave
picker.dispatch('focusout', { relatedTarget: null });
assert.equal(timers.length, 1, 'the close is deferred, not dropped');
timers.forEach((fn) => fn());
assert.equal(picker.hidden, true, 'leaving the listbox for good closes it');
assert.deepEqual(added, [], 'and adds nothing');

console.log('collection picker mouse-click tests passed');
