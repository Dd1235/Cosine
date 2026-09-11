# Singleton embedding baseline — 2026-09-11

Quantized inference now processes each input independently inside the shared
array-in/array-out embedder. Offline progress chunks no longer become inference
batches. The committed manifest records recipe version 2: model/tokenizer
`Xenova/all-MiniLM-L6-v2`, q8, Transformers.js 4.2.0, mean pooling, normalization,
singleton inference, and the existing text composition. Boot and corpus validation
reject an absent or incompatible recipe.

## Controlled comparison

- Before: `bench-2026-09-11T06-51-40-787Z.json`.
- After: `bench-2026-09-11T06-52-47-400Z.json` (new baseline).
- Both: 3,482 documents, 81 queries, expansion enabled, five latency repetitions.
- Corpus text/order SHA-256: `537bf4e8850edafc5732fb4a5d949175f8fdfb68d7825e299efcb31aa3021015`.
- Query-file SHA-256: `3a00dff41b615e12a98c7d3b7277ed03576777a746cbf7e6940a319f346fe858`.
- No corpus text, relevance judgments, or ranking changes between runs.

| Ranker | nDCG@10 before | After | MRR before | After |
|---|---:|---:|---:|---:|
| TF-IDF | .495 | .495 | .570 | .570 |
| BM25 | .603 | .603 | .642 | .642 |
| Dense | .502 | .519 | .550 | .571 |
| Hybrid | .589 | .613 | .629 | .664 |

Dense/hybrid differences establish the new calibration, not evidence for a new
ranking algorithm. Existing corpus-growth comparisons made with batched vectors
remain confounded. Model weights still use the project's cached Hugging Face
model identity; byte-for-byte guarantees apply to the same model/runtime, not
arbitrary future upstream weights or different inference hardware.

## Verification

`node server/search/embedding.invariance.test.js` loads the real model and checks
exact vector equality for Two Sum alone, with the longest corpus statement,
reordered, with another unrelated insertion, and alone again. Also checks empty
input and normalized output. All passed.

`node server/search/embedding.recipe.test.js` verifies that boot accepts the
matching recipe and rejects legacy, batched, or package-mismatched artifacts.
`node server/search/dense.test.js` passed. `npm run validate` passed with zero
errors and the pre-existing open-vocabulary warning. Full singleton corpus
embedding took 10.5 seconds on this local environment.
