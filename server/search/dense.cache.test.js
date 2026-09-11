const assert = require("node:assert/strict");
const { DenseIndex } = require("./dense");
(async () => {
  const calls = [];
  let failing = true;
  const options = { matrix: new Float32Array([1]), dims: 1, queryCacheSize: 2,
    embed: async ([q]) => { calls.push(q); if (q === "fail" && failing) throw new Error("temporary"); return new Float32Array([1]); } };
  const index = new DenseIndex([{ id: "a" }], options);
  await Promise.all([index.search("A"), index.search("A")]);
  assert.deepEqual(calls, ["A"]);
  await index.search("a"); // Exact embedding input; no case/space folding.
  await index.search(" A");
  await index.search("A"); // Evicted LRU.
  assert.deepEqual(calls, ["A", "a", " A", "A"]);
  await assert.rejects(index.search("fail"));
  failing = false;
  await index.search("fail");
  assert.equal(calls.filter((q) => q === "fail").length, 2);
  const other = new DenseIndex([{ id: "a" }], options);
  await other.search("A"); // New model/index never reuses old cache.
  assert.equal(calls.filter((q) => q === "A").length, 3);
  assert.ok(index.queryCache.size <= 2);
  console.log("dense query cache coalescing, exact keys, eviction, retry and isolation passed");
})().catch((err) => { console.error(err); process.exitCode = 1; });
