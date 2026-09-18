const assert = require("node:assert/strict");
const {validateLevels, practiceLevels} = require("../search/practice_levels");
const problems = [
  {platform: "codeforces", difficulty: 1500}, {platform: "codeforces", difficulty: 1700},
  {platform: "atcoder", difficulty: 800}, {platform: "leetcode", difficulty: "Medium", acceptance_rate: 40},
  {platform: "leetcode", difficulty: "Hard", acceptance_rate: 30}, {platform: "cses", cses_difficulty: {band: 3}},
];
for (const bad of [null, [], {github: {}}, {cses: {band: 3}}, {leetcode: {tier: "expert"}},
  {codeforces: {min: "1000", max: 1200}}, {atcoder: {min: 1200, max: 1000}}, {codeforces: {min: -1, max: 1000}}]) {
  assert.equal(validateLevels(bad), false, JSON.stringify(bad));
}
const signals = {codeforces: {rating: 1500}, atcoder: {rating: 800}, cses: {band: 3}};
const result = practiceLevels(signals, {codeforces: {min: 1700, max: 1700}, leetcode: {tier: "hard"}}, problems);
assert.equal(result.suggest.codeforces.difficulty, "cf:1700-1700");
assert.equal(result.suggest.codeforces.count, 1);
assert.equal(result.suggest.codeforces.source, "manual");
assert.equal(result.suggest.atcoder.source, "profile");
assert.equal(result.suggest.leetcode.count, 1);
assert.equal(result.automatic.cses, undefined);
assert.equal(result.suggest.cses.source, "manual");
assert.equal(practiceLevels({codeforces: {rating: 2000}}, {}, problems).suggest.cses, undefined, "no cross-judge CSES inference");

const prefs = new Map(); let missingColumn = false, writes = 0;
const dbPath = require.resolve("../db");
require.cache[dbPath] = {id: dbPath, filename: dbPath, loaded: true, exports: {
  query: async (sql, params) => {
    if (missingColumn && sql.includes("practice_levels")) throw Object.assign(new Error("missing"), {code: "42703"});
    if (sql.startsWith("INSERT")) {
      writes++; prefs.set(params[0], {practice_levels: JSON.parse(params[1]), cses_band: params[2]});
      return {rows: []};
    }
    if (sql.includes("user_preferences")) return {rows: prefs.has(params[0]) ? [prefs.get(params[0])] : []};
    if (sql.includes("user_platform_handles")) return {rows: [{platform: "atcoder"}, {platform: "codeforces"}]};
    return {rows: [{platform: "codeforces", payload: {rating: 1500}, fetched_at: "2026-09-18T00:00:00Z"},
      {platform: "atcoder", payload: {rating: null, ratingState: "unavailable"}, fetched_at: "2026-09-18T00:00:00Z"}]};
  },
}};
const express = require("express");
const {createProfileRouter} = require("./profile");
const app = express(); app.use(express.json());
app.use((req, _res, next) => { if (req.headers["x-test-user"]) req.user = {id: req.headers["x-test-user"]}; next(); });
app.use(createProfileRouter({problems}));
const server = app.listen(0, "127.0.0.1");
(async () => {
  await new Promise(resolve => server.once("listening", resolve));
  const base = `http://127.0.0.1:${server.address().port}`;
  const request = (user, body) => fetch(base + (body === undefined ? "/level" : "/preferences/practice-levels"), {
    method: body === undefined ? "GET" : "PUT", headers: {"content-type": "application/json", ...(user ? {"x-test-user": user} : {})},
    ...(body === undefined ? {} : {body: JSON.stringify(body)}),
  });
  assert.equal((await request(null, {levels: {}, csesBand: null})).status, 401);
  assert.equal((await request("a", {levels: {kattis: {min: 1, max: 3}}, csesBand: null})).status, 400);
  assert.equal((await request("a", {levels: {}, csesBand: 6})).status, 400);
  const custom = {levels: {codeforces: {min: 1700, max: 1700}}, csesBand: 3};
  assert.equal((await request("a", custom)).status, 200);
  const saved = await (await request("a")).json();
  assert.deepEqual(saved.preferences, custom);
  assert.ok(saved.linkedPlatforms.includes("atcoder"));
  assert.equal(saved.signals.atcoder.ratingState, "unavailable");
  assert.equal(saved.automatic.atcoder, undefined, "missing ratings never produce a fabricated suggestion");
  assert.equal(saved.suggest.codeforces.difficulty, "cf:1700-1700");
  assert.equal(saved.suggest.cses.difficulty, "cses-intermediate");
  assert.deepEqual((await (await request("b")).json()).preferences, {levels: {}, csesBand: null});
  assert.equal((await request("a", {levels: {}, csesBand: null})).status, 200);
  assert.equal((await (await request("a")).json()).suggest.codeforces.source, "profile");
  assert.equal(writes, 2, "invalid/unauthenticated requests never write");
  missingColumn = true;
  const legacy = await request("a");
  assert.equal(legacy.status, 200);
  assert.equal((await legacy.json()).preferencesReady, false);
  assert.equal((await request("a", custom)).status, 503);
  console.log("practice level validation, override precedence, auth, isolation, reset and migration fallback passed");
})().catch(error => {console.error(error); process.exitCode = 1;}).finally(() => server.close());
