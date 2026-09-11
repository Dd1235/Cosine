// Real-model regression: run explicitly with the pinned model cached locally.
// node server/search/embedding.invariance.test.js
const assert = require("node:assert/strict");
const { loadProblems } = require("../data");
const { createEmbedder, problemText, DIMS, embeddingRecipe, matchesEmbeddingRecipe } = require("./embedding");

(async () => {
  const problems = loadProblems();
  const short = problemText(problems.find((p) => p.id === "leetcode-two-sum"));
  const long = problems.map(problemText).reduce((a, b) => a.length > b.length ? a : b);
  const unrelated = "Find a minimum spanning tree of a weighted connected graph.";
  const embed = await createEmbedder();
  const reference = await embed([short]);
  for (const texts of [[short, long], [long, short], [unrelated, short, long], [short]]) {
    const vectors = await embed(texts);
    const row = texts.indexOf(short);
    assert.deepEqual(vectors.slice(row * DIMS, (row + 1) * DIMS), reference,
      "document vector changed after insertion/removal/reordering of other documents");
  }
  assert.equal((await embed([])).length, 0);
  assert.ok(Math.abs(Math.hypot(...reference) - 1) < 1e-3);
  assert.ok(matchesEmbeddingRecipe(embeddingRecipe()));
  assert.ok(!matchesEmbeddingRecipe(undefined));
  for (const key of Object.keys(embeddingRecipe())) {
    assert.ok(!matchesEmbeddingRecipe({ ...embeddingRecipe(), [key]: "different" }), key);
  }
  console.log("real embedding invariance passed: insertion, removal, ordering, singleton repeat, recipe");
})().catch((err) => { console.error(err); process.exitCode = 1; });
