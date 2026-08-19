#!/usr/bin/env node
// Give every problem the broad label its own specific labels imply.
//
// A problem labelled `digit-dp` is dynamic programming; one labelled
// `modular-arithmetic` is number theory. The specific name and the family name
// are both things people type, and only the specific one was indexed.
//
// The rules live in data/pattern_taxonomy.json under `families` and are shared
// with the ingest path (scripts/annotate_problem_urls.py applies them to new
// annotations). They started out as regexes inside that script, which meant
// they only ever ran on new problems — 1,029 of 3,468 were missing a family
// label their own labels implied, and `number-theory` was on 40 problems while
// 394 carried a number-theory technique.
//
//   node scripts/apply_families.js           report
//   node scripts/apply_families.js --write   apply
//
// Adding a label to hundreds of problems changes its IDF, so run `npm run
// bench` after this and not just `npm run validate` — the point is recall, and
// the cost is paid by whoever was already ranking first for the family term.
//
// Append-only: nothing is ever removed, and the 12-label cap is respected.

const fs = require("fs");
const path = require("path");

const ROOT = path.join(__dirname, "..");
const CORPUS_ROOT = path.join(ROOT, "data", "problemset_llm");
const MAX_LABELS = 12;

const taxonomy = JSON.parse(fs.readFileSync(path.join(ROOT, "data", "pattern_taxonomy.json"), "utf8"));
const FAMILIES = (taxonomy.families || []).map((f) => ({ re: new RegExp(f.match), family: f.family }));

function problemFiles() {
  return fs.readdirSync(CORPUS_ROOT)
    .flatMap((platform) => {
      const dir = path.join(CORPUS_ROOT, platform);
      if (!fs.statSync(dir).isDirectory()) return [];
      return fs.readdirSync(dir).filter((f) => f.endsWith(".json")).map((f) => path.join(dir, f));
    })
    .sort();
}

function main() {
  const write = process.argv.includes("--write");
  if (!FAMILIES.length) {
    console.error("no `families` in data/pattern_taxonomy.json — nothing to do");
    process.exitCode = 1;
    return;
  }

  const added = new Map();
  const capped = [];
  let touched = 0;

  for (const file of problemFiles()) {
    const problem = JSON.parse(fs.readFileSync(file, "utf8"));
    const patterns = problem.patterns || [];
    const have = new Set(patterns);
    const want = [];
    for (const label of patterns) {
      for (const { re, family } of FAMILIES) {
        if (have.has(family) || want.includes(family) || !re.test(label)) continue;
        want.push(family);
      }
    }
    if (!want.length) continue;

    // The cap is a real constraint, not a formality — a problem already at 12
    // labels loses the family silently otherwise, and silently is the failure
    // mode this whole pass exists to fix.
    const room = MAX_LABELS - patterns.length;
    const fits = want.slice(0, Math.max(0, room));
    if (fits.length < want.length) capped.push(`${problem.id}: no room for ${want.slice(fits.length).join(", ")}`);
    if (!fits.length) continue;

    touched += 1;
    for (const f of fits) added.set(f, (added.get(f) || 0) + 1);
    if (write) {
      problem.patterns = patterns.concat(fits);
      fs.writeFileSync(file, JSON.stringify(problem, null, 2) + "\n");
    }
  }

  const verb = write ? "added" : "would add";
  const total = [...added.values()].reduce((a, b) => a + b, 0);
  console.log(`${verb} ${total} label(s) across ${touched} problem(s)`);
  for (const [family, n] of [...added].sort((a, b) => b[1] - a[1])) console.log(`  ${family.padEnd(22)} ${n}`);
  for (const line of capped) console.log(`  cap: ${line}`);
  if (write) console.log("\ncorpus text changed — run: npm run embed && npm run validate && npm run bench");
  else if (total) console.log("\nre-run with --write");
}

main();
