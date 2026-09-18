const assert = require("node:assert/strict");
const express = require("express");
process.env.HANDLE_KEY = "profile-cache-test-only-key-not-production";
let cached, next, calls = 0;
const dbPath = require.resolve("../db");
require.cache[dbPath] = {id: dbPath, filename: dbPath, loaded: true, exports: {query: async (sql, params) => {
  if (sql.includes("user_platform_handles")) return {rows: [{platform: "atcoder", handle: "test"}]};
  if (sql.startsWith("INSERT INTO user_platform_stats")) {
    cached = {platform: "atcoder", payload: JSON.parse(params[2]), fetched_at: new Date().toISOString()};
    return {rows: []};
  }
  if (sql.includes("user_platform_stats")) return {rows: cached ? [cached] : []};
  return {rows: []};
}}};
const {createProfileRouter} = require("./profile");
const app = express();
app.use((req, _res, done) => {req.user = {id: "test"}; done();});
app.use(createProfileRouter({fetchStats: async () => {calls++; return structuredClone(next);}}));
const server = app.listen(0, "127.0.0.1");
(async () => {
  await new Promise(resolve => server.once("listening", resolve));
  const base = `http://127.0.0.1:${server.address().port}`;
  const get = async () => {
    const res = await fetch(base + "/profile");
    assert.equal(res.status, 200);
    return (await res.json()).platforms.atcoder;
  };
  const old = new Date(Date.now() - 20 * 60 * 1000).toISOString();
  cached = {platform: "atcoder", fetched_at: old, payload: {rating: null, solved: 5, calendar: {"86400": 2}}};
  next = {rating: 1400, ratingState: "rated", solved: null, calendar: {}, partial: true};
  let stats = await get();
  assert.equal(calls, 1, "legacy missing rating retries after ten minutes, not twelve hours");
  assert.equal(stats.rating, 1400);
  assert.equal(stats.solved, 5, "failed submissions source keeps prior stats");
  assert.deepEqual(stats.calendar, {"86400": 2});
  assert.equal(stats.activityFetchedAt, old);
  await get();
  assert.equal(calls, 1, "partial refresh still respects retry floor");

  cached.fetched_at = old;
  next = {rating: null, ratingState: "unavailable", solved: 8, calendar: {}, partial: true};
  stats = await get();
  assert.equal(calls, 2);
  assert.equal(stats.rating, 1400, "failed rating source keeps prior rating");
  assert.equal(stats.ratingFetchedAt, old);
  assert.equal(stats.solved, 8);
  const level = await (await fetch(base + "/level")).json();
  assert.equal(level.signals.atcoder.fetchedAt, old, "cached rating retains its real timestamp");

  cached = {platform: "atcoder", fetched_at: old, payload: {rating: null, ratingState: "unrated", solved: 5, calendar: {}}};
  await get();
  assert.equal(calls, 2, "genuinely unrated history is a successful cache entry");
  console.log("profile partial-source caching and retry tests passed");
})().catch(err => {console.error(err); process.exitCode = 1;}).finally(() => server.close());
