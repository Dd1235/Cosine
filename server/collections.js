const registry = require('../data/contests.json');

function validateRegistry(data, problems) {
  const errors = [], ids = new Set(), problemIds = new Set(problems.map(p => p.id));
  const url = value => { try { return ['https:', 'http:'].includes(new URL(value).protocol); } catch { return false; } };
  for (const c of data.collections || []) {
    if (!/^[a-z0-9-]+$/.test(c.id) || ids.has(c.id)) errors.push(`invalid/duplicate collection id: ${c.id}`);
    ids.add(c.id);
    for (const field of ['name','family','organizer','stage']) if (!c[field]) errors.push(`${c.id}: missing ${field}`);
    if (!Array.isArray(c.problems) || new Set(c.problems).size !== c.problems.length) errors.push(`${c.id}: invalid ordered memberships`);
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
  const collections = (data.collections || []).map(c => ({ ...c,
    problems: [...new Set(c.problems.map(p => canonical(typeof p === 'string' ? p : p.id)))],
  }));
  const known = new Map(collections.map(c => [c.id, c]));
  const memberships = new Map();
  for (const c of collections) for (const id of c.problems) {
    if (!memberships.has(id)) memberships.set(id, []);
    memberships.get(id).push({ id: c.id, name: c.name });
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
