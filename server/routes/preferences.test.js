// Isolated route regression, no external DB or migrations.
const assert = require("node:assert/strict");
const dbPath = require.resolve("../db");
const bands = new Map();
require.cache[dbPath] = { id: dbPath, filename: dbPath, loaded: true, exports: {
  query: async (sql, params) => {
    if (sql.includes("INSERT INTO user_preferences")) { bands.set(params[0], params[1]); return { rows: [] }; }
    if (sql.includes("FROM user_preferences")) return { rows: bands.has(params[0]) ? [{ cses_band: bands.get(params[0]) }] : [] };
    return { rows: [] };
  },
} };
const express = require("express");
const { createProfileRouter } = require("./profile");
const app = express();
app.use(express.json());
app.use((req, _res, next) => { if (req.headers["x-test-user"]) req.user = { id: req.headers["x-test-user"] }; next(); });
app.use("/api", createProfileRouter({ fetchStats: async () => ({}), problems: [
  { platform: "cses", cses_difficulty: { band: 3 } },
] }));
const server = app.listen(0, "127.0.0.1");
(async () => {
  await new Promise((resolve) => server.once("listening", resolve));
  const base = `http://127.0.0.1:${server.address().port}/api`;
  const request = (path, user = "a", body) => fetch(base + path, { method: body === undefined ? "GET" : "PUT",
    headers: { "content-type": "application/json", ...(user ? { "x-test-user": user } : {}) },
    ...(body === undefined ? {} : { body: JSON.stringify(body) }) });
  assert.equal((await request("/preferences/cses-level", null)).status, 401);
  assert.equal((await request("/preferences/cses-level", null, { band: 3 })).status, 401);
  assert.deepEqual(await (await request("/preferences/cses-level")).json(), { band: null });
  for (const band of [0, 6, "3", 2.5]) assert.equal((await request("/preferences/cses-level", "a", { band })).status, 400);
  assert.equal((await request("/preferences/cses-level", "a", {})).status, 400);
  assert.deepEqual(await (await request("/preferences/cses-level", "a", { band: 3 })).json(), { band: 3 });
  assert.deepEqual(await (await request("/preferences/cses-level", "a")).json(), { band: 3 });
  assert.deepEqual(await (await request("/preferences/cses-level", "b")).json(), { band: null });
  const level = await request("/level");
  assert.equal(level.headers.get("cache-control"), "no-store");
  assert.equal((await level.json()).suggest.cses.difficulty, "cses-intermediate");
  await request("/preferences/cses-level", "a", { band: null });
  assert.deepEqual((await (await request("/level")).json()).suggest, {});
  console.log("CSES preference auth, validation, persistence, isolation, clear and level passed");
})().catch((err) => { console.error(err); process.exitCode = 1; }).finally(() => server.close());
