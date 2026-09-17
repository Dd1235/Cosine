const registry = require('../data/contests.json');

// A membership is either a bare id or an object carrying what the corpus does
// not know about that problem yet — its letter in the original set, its title,
// where to read it, what the judge says it is worth. The contest page is the
// reason: a problem we could not index is still a problem that ran, and a row
// reading "not yet indexed" and nothing else is not a listing of a contest.
const MEMBER_KEYS = new Set(['id', 'letter', 'order', 'title', 'url', 'kattis_difficulty', 'solves', 'code']);
const SOLVE_SOURCES = ['kattis-source-page', 'codechef-replay', 'icpc-standings'];
const memberId = p => (p && typeof p === 'object' ? p.id : p);

function validateRegistry(data, problems) {
  const errors = [], ids = new Set(), problemIds = new Set(problems.map(p => p.id));
  const url = value => { try { return ['https:', 'http:'].includes(new URL(value).protocol); } catch { return false; } };
  const date = value => /^\d{4}-\d{2}-\d{2}$/.test(value || '');
  const str = value => typeof value === 'string' && !!value.trim();
  // Only the keys named above, and only the shapes named here. A member is
  // hand-written against a judge page, so a typo'd key would otherwise sit in
  // the registry rendering nothing and reading as a missing feature.
  function memberErrors(c, member, orders) {
    const out = [];
    const where = `${c.id}/${member.id || '?'}`;
    for (const key of Object.keys(member)) {
      if (!MEMBER_KEYS.has(key)) out.push(`${where}: unknown member field ${key}`);
    }
    if (!str(member.id)) out.push(`${where}: member needs an id`);
    if (member.letter !== undefined && !/^[A-Z][0-9]?$/.test(member.letter)) out.push(`${where}: invalid letter`);
    if (member.order !== undefined) {
      if (!Number.isInteger(member.order) || member.order < 1) out.push(`${where}: invalid order`);
      else if (orders.has(member.order)) out.push(`${where}: duplicate order ${member.order}`);
      else orders.add(member.order);
    }
    if (member.title !== undefined && !str(member.title)) out.push(`${where}: invalid title`);
    if (member.url !== undefined && !url(member.url)) out.push(`${where}: invalid url`);
    if (member.code !== undefined && !str(member.code)) out.push(`${where}: invalid code`);
    const k = member.kattis_difficulty;
    if (k !== undefined) {
      if (!k || typeof k !== 'object' || Object.keys(k).some(key => !['score', 'label'].includes(key))) out.push(`${where}: invalid kattis difficulty`);
      else if (typeof k.score !== 'number' || !Number.isFinite(k.score) || k.score < 0 || k.score > 10) out.push(`${where}: invalid kattis score`);
      else if (k.label !== undefined && !str(k.label)) out.push(`${where}: invalid kattis label`);
    }
    const s = member.solves;
    if (s !== undefined) {
      if (!s || typeof s !== 'object' || Object.keys(s).some(key => !['full', 'source', 'observed_at'].includes(key))) out.push(`${where}: invalid solves`);
      else if (!Number.isInteger(s.full) || s.full < 0) out.push(`${where}: invalid solve count`);
      // A solve count with no named source is a number nobody can check.
      else if (!SOLVE_SOURCES.includes(s.source)) out.push(`${where}: invalid solves source`);
      else if (s.observed_at !== undefined && !date(s.observed_at)) out.push(`${where}: invalid solves date`);
    }
    return out;
  }
  for (const c of data.collections || []) {
    if (!/^[a-z0-9-]+$/.test(c.id) || ids.has(c.id)) errors.push(`invalid/duplicate collection id: ${c.id}`);
    ids.add(c.id);
    for (const field of ['name','family','organizer','stage']) if (!c[field]) errors.push(`${c.id}: missing ${field}`);
    // Optional chip label. It replaces the name on a card and in the judge row,
    // where anything longer than a judge chip stops reading as a chip.
    if (c.short !== undefined && (typeof c.short !== 'string' || !c.short.trim() || c.short.length > 16)) errors.push(`${c.id}: invalid short label`);
    // Dedupe on ids, not on the members themselves: two object members naming
    // the same problem are two distinct objects, so the old Set over c.problems
    // compared identities and waved every object duplicate straight through.
    if (!Array.isArray(c.problems) || new Set(c.problems.map(memberId)).size !== c.problems.length) errors.push(`${c.id}: invalid ordered memberships`);
    else {
      const orders = new Set();
      for (const p of c.problems) {
        if (typeof p === 'string') { if (!p.trim()) errors.push(`${c.id}: empty membership`); continue; }
        if (!p || typeof p !== 'object') { errors.push(`${c.id}: invalid membership`); continue; }
        errors.push(...memberErrors(c, p, orders));
      }
    }
    if (!c.evidence?.length || !c.evidence.every(url)) errors.push(`${c.id}: invalid evidence`);
    if (c.held_date !== null && !/^\d{4}-\d{2}-\d{2}$/.test(c.held_date || '')) errors.push(`${c.id}: invalid held date`);
    for (const r of c.resources || []) if (!r.title || !r.kind || !url(r.url) || !['public','inaccessible','not-verified'].includes(r.availability)) errors.push(`${c.id}: invalid resource`);
  }
  for (const [alias, target] of Object.entries(data.aliases || {})) {
    if (alias === target || !problemIds.has(target) || problemIds.has(alias)) errors.push(`alias must point to an existing state-owning id without a duplicate record: ${alias}`);
  }
  return errors;
}

function createCollections(problems, data = registry) {
  const byId = new Map(problems.map(p => [p.id, p]));
  const aliases = data.aliases || {};
  function canonical(id) {
    const seen = new Set();
    while (aliases[id] && !seen.has(id)) { seen.add(id); id = aliases[id]; }
    return id;
  }
  // `problems` stays the flat canonical id list every other consumer reads.
  // `members` is the same list with whatever the registry knows about each
  // entry still attached, in the same order — the contest page needs the
  // metadata, and nothing else should have to learn a second shape.
  const collections = (data.collections || []).map(c => {
    const members = [], seen = new Set();
    for (const p of c.problems) {
      const raw = typeof p === 'string' ? { id: p } : { ...p };
      const id = canonical(raw.id);
      if (seen.has(id)) continue;
      seen.add(id);
      members.push({ ...raw, id });
    }
    return { ...c, members, problems: members.map(m => m.id) };
  });
  const known = new Map(collections.map(c => [c.id, c]));
  const memberships = new Map();
  // What a card says about where a problem came from. Registry order, so a
  // problem in two collections always names them in the same order.
  for (const c of collections) for (const id of c.problems) {
    if (!memberships.has(id)) memberships.set(id, []);
    memberships.get(id).push({ id: c.id, name: c.name, ...(c.short ? { short: c.short } : {}) });
  }
  function parse(raw) {
    // Preserve unknown selections as empty matches, never silently broaden.
    return new Set(String(raw || '').split(',').map(s => s.trim()).filter(Boolean));
  }
  function passes(p, selected) {
    return !selected.size || (memberships.get(canonical(p.id)) || []).some(c => selected.has(c.id));
  }
  function payload() {
    return { version: data.version, collections: collections.map(c => ({ ...c,
      count: c.problems.filter(id => byId.has(id)).length,
      unavailableCount: c.problems.filter(id => !byId.has(id)).length,
    })) };
  }
  function order(items, selected, get = x => x) {
    const order = new Map();
    for (const id of selected) for (const pid of known.get(id)?.problems || []) {
      if (!order.has(pid)) order.set(pid, order.size);
    }
    return [...items].sort((a,b) => (order.get(canonical(get(a).id)) ?? Infinity) - (order.get(canonical(get(b).id)) ?? Infinity));
  }
  return { canonical, parse, passes, payload, order, memberships };
}
module.exports = { createCollections, validateRegistry };
