# Codex brief: audit `binary-search-answer`

Paste this whole file to Codex, from a checkout of `Dd1235/Cosine`. It is
self-contained. Expected runtime: **1.5–2.5 hours** for 277 problems.

---

## What you are doing

`cosine` is a search engine over 3,461 competitive-programming problems. Each
problem carries 2–12 technique labels, and search matches those labels — so a
**wrong** label makes a problem appear for a query it has nothing to do with.
That is the worst failure mode here, because nobody notices it: the problem you
wanted is still missing and a stranger is in its place.

A sampled audit (`experiments/16-general-precision-sample.md`) measured 13.6% of
labels as wrong, and found the errors are **not** spread evenly — they cluster
in a handful of *narrow technique names used in their loose English sense*. The
biggest one is `binary-search-answer`, on **277 problems**.

`binary-search-answer` means **binary searching the answer space**: guess a
candidate answer, test feasibility in O(n) or so, and narrow the range. The
tell is monotonicity — if X works, everything above (or below) X works.

It does **not** mean:
- plain binary search in a sorted array (`binary-search`),
- `lower_bound` / `upper_bound` on a container,
- a two-pointer or sliding-window scan,
- "the complexity has a log in it".

## The job

For each of the 277 problems, decide whether `binary-search-answer` is
justified, and produce a file listing the ones where it is not.

```bash
# the carriers, with everything you need to judge them
python3 - <<'PY'
import json, glob
out = []
for f in glob.glob("data/problemset_llm/*/*.json"):
    d = json.loads(open(f).read())
    if "binary-search-answer" in d.get("patterns", []):
        out.append({"id": d["id"], "title": d["title"], "platform": d["platform"],
                    "difficulty": d.get("difficulty"), "patterns": d["patterns"],
                    "source_tags": d.get("source_tags", []), "statement": d["statement"]})
json.dump(out, open("/tmp/bsa.json", "w"), indent=1)
print(len(out), "problems -> /tmp/bsa.json")
PY
```

Judge each one from the statement summary and the title. If you recognise the
problem, use that knowledge and say so. **Codeforces `source_tags` are an
independent second opinion** — CF tags `binary search` itself, which is
evidence but not proof (they tag plain binary search the same way).

Three verdicts only:

- `justified` — a solution really does binary search the answer space.
- `wrong` — it does not. Say in one line what the problem actually does.
- `unsure` — the summary is too thin. **Default to this rather than guessing.**

## Output

Write `data/review_queue/_bsa-audit.json`:

```json
{
  "label": "binary-search-answer",
  "reviewed_by": "codex",
  "reviewed_at": "YYYY-MM-DD",
  "justified": ["problem-id", "..."],
  "unsure": [{"id": "...", "why": "what would settle it"}],
  "remove": [{"id": "...", "why": "one line: what the problem actually does"}]
}
```

Also write a short `experiments/17-bsa-audit.md`: the counts, whether the errors
concentrate anywhere (judge, difficulty, co-label), and anything that surprised
you.

## Rules

1. **Do not edit any file under `data/problemset_llm/`.** You produce a list;
   applying it is a separate, reviewed step. This is the whole reason the review
   queue exists.
2. **`unsure` is a real answer.** A wrong removal costs more than a wrong keep:
   it silently stops a problem answering a search it *should* answer. When the
   evidence is thin, say so.
3. Do not add labels. This pass is about one label being wrong, not about what
   is missing — a separate pass does that.
4. No git commands, no commits.
5. If you find a problem whose **statement summary is factually wrong** (it
   happens — `atcoder-abc159-f` describes a condition the real problem doesn't
   have), note it in the report. That is a retrieval bug in its own right,
   because statements are indexed.

## What good looks like

The audit that produced this brief found that the predictor of a bad
`state-compression` label was not the judge or the difficulty but a **co-label**:
with a bitmask sibling it was usually right, with only generic
`dynamic-programming` it was wrong 10 times out of 10. If you can find a rule
like that for `binary-search-answer`, it is worth more than the 277 individual
verdicts — say it plainly in the report.
