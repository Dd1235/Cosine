const assert = require("node:assert/strict");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const { tryCreateDenseIndex } = require("./dense");
const { MODEL_ID, DTYPE, DIMS, embeddingRecipe, corpusHash } = require("./embedding");

(async () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "algolens-recipe-"));
  const problems = [{ id: "sample", title: "Sample" }];
  const matrix = new Float32Array(DIMS); matrix[0] = 1;
  const manifest = { model: MODEL_ID, dtype: DTYPE, dims: DIMS, count: 1,
    ids: ["sample"], corpusHash: corpusHash(problems), recipe: embeddingRecipe() };
  const embed = async () => matrix;
  const write = (value) => fs.writeFileSync(path.join(dir, "manifest.json"), JSON.stringify(value));
  try {
    fs.writeFileSync(path.join(dir, "corpus.f32"), Buffer.from(matrix.buffer));
    write(manifest);
    assert.ok(await tryCreateDenseIndex(problems, { artifactDir: dir, embed }));
    write({ ...manifest, recipe: undefined });
    assert.equal(await tryCreateDenseIndex(problems, { artifactDir: dir, embed }), null);
    write({ ...manifest, recipe: { ...manifest.recipe, inferenceBatchSize: 32 } });
    assert.equal(await tryCreateDenseIndex(problems, { artifactDir: dir, embed }), null);
    write({ ...manifest, recipe: { ...manifest.recipe, package: "different" } });
    assert.equal(await tryCreateDenseIndex(problems, { artifactDir: dir, embed }), null);
    console.log("embedding recipe boot tests passed");
  } finally { fs.rmSync(dir, { recursive: true, force: true }); }
})().catch((err) => { console.error(err); process.exitCode = 1; });
