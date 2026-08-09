# Solution analyses for hard problems

What an audit **worked out**, kept so the next one doesn't have to work it out
again.

When an agent labels a hard problem it does the expensive part first: read the
statement, derive the solution, and usually verify the derivation against the
samples or a brute force. Until now only the labels survived that — three or
four words out of twenty minutes of reasoning. So the next time the vocabulary
grows, or someone asks "which problems here are actually hitting-set problems",
the whole derivation has to happen again.

One file per problem, `<problem-id>.json`:

```json
{
  "id": "codeforces-2252-f",
  "title": "Spectral Components",
  "approach": "one or two sentences: what the solution actually is",
  "techniques": [{ "label": "tree-centroid", "confidence": 0.8, "why": "…" }],
  "verified": "how the derivation was checked — samples, brute force, or not at all",
  "reviewed_by": "claude-agent",
  "reviewed_at": "2026-08-09"
}
```

**This is not searchable and must never be.** `server/search/*` builds its text
from title + statement + tags + patterns; an `approach` field is a spoiler, and
nobody wants the solution in the search results for the problem. It exists for
maintenance: re-labelling, checking a new label against problems that might
carry it, and auditing the auditor.

`techniques` may name labels that were rejected at merge time (over the
12-label cap, or too speculative). Keeping them is the point — a rejected
candidate with a reason is exactly what a later pass wants to reconsider.
