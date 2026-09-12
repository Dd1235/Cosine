#!/usr/bin/env python3
"""
Publish reviewed external-judge problems from staging into the served corpus.

    python3 scripts/publish_external.py --batch wf-2024            # dry run
    python3 scripts/publish_external.py --batch wf-2024 --write
    python3 scripts/publish_external.py --list                     # known batches

This mechanises what experiments/18-reviewed-corpus-refresh.md did by hand.
Kattis and CodeChef problems arrive with no rating, no tags and no editorial, so
their labels come from a human solving the problem (data/analysis/external-
proposals.json) and an independent skeptic checking that solution
(data/analysis/external-review.json). Only after both does a record become
searchable.

WHAT THIS SCRIPT IS ACTUALLY FOR

It is a gate, not a copier. Doing this by hand is five checks per problem, and
the expensive failure is the quiet one: a record that looks published, is
indexed, and is wrong — a solution nobody reviewed, a label outside the
vocabulary that no query will ever match, or a statement that drifted from the
statement the reviewer read. Each check below exists because skipping it
produces exactly that.

  staged file exists       — the statement is the bulk of the indexed document.
  sha256 matches review    — the reviewer approved ONE text. If staging has been
                             re-fetched since (Kattis edits statements), the
                             approval no longer covers what would be published.
  review status approved   — an unreviewed or rejected proposal is not evidence.
  patterns in the taxonomy — an off-vocabulary label is invisible to search, so
                             publishing one is worse than publishing no label:
                             the problem looks annotated and is unfindable.
  non-empty solution       — the review's whole subject. No solution, no review.
  no canary in the summary — third-party statements carry sentences aimed at
                             language models (see fetch_statements.AGENT_CANARY).
                             One that survived into a summary would be stored in
                             the corpus and re-read by the next annotator.

Anything that fails is REPORTED AND SKIPPED, never partially written. It stays
in staging, which is also how the site already describes it: a collection
problem with no record shows in `unavailableCount`. A half-published batch is a
worse state than an unpublished one, and "it was mostly fine" is not a review.

WHY THE REVIEW'S TEXT WINS

Where the review restates `patterns`, `solution` or `statement_summary`, those
are what get published — the skeptic pass exists to correct the proposal, and
publishing the proposal's version would discard the correction it was run to
find. Every check runs against the values actually being written.

Families are applied with annotate_problem_urls.with_families: a specific label
implies its family, because "dp-with-state" and "dynamic-programming" are both
real queries and only one of them was being indexed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from annotate_problem_urls import canonical_label, with_families  # noqa: E402
from cache_io import atomic_write_json  # noqa: E402
from fetch_statements import AGENT_CANARY  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
PROPOSALS = ROOT / "data" / "analysis" / "external-proposals.json"

ANNOTATION_VERSION = "problem-patterns-v1"
ANNOTATION_MODEL = "opus-solution-review"
REVIEWED_BY = "independent Opus skeptic"
EVIDENCE = "data/analysis/external-review.json"
MAX_LABELS = 12  # mirrors scripts/validate_corpus.js
REVIEWED_CONFIDENCE = 0.9
# A family label is an implication of a reviewed label, not an independently
# reviewed judgement, and the confidence should not claim otherwise.
FAMILY_CONFIDENCE = 0.7


def read_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return default


def by_id(document: Any) -> dict[str, dict[str, Any]]:
    problems = (document or {}).get("problems") or []
    return {p["id"]: p for p in problems if isinstance(p, dict) and p.get("id")}


def batch_of(proposal: dict[str, Any], document: dict[str, Any]) -> str | None:
    """A proposal's batch, or the file-level one. The early hand-run batches
    predate the field, so a whole file can name itself instead."""
    return proposal.get("batch") or (document or {}).get("batch")


def platform_of(problem_id: str) -> str:
    return problem_id.split("-", 1)[0]


def check(record: dict[str, Any], review: dict[str, Any], staged: dict[str, Any] | None,
          canonical: set[str], aliases: dict[str, str]) -> tuple[list[str], list[str]]:
    """Returns (reasons to skip, canonical patterns). Collects every failure
    rather than stopping at the first: one run should say everything that is
    wrong with a batch."""
    reasons: list[str] = []
    if staged is None:
        reasons.append("no staging file")
    if not review:
        reasons.append("no review entry")
    elif review.get("status") != "approved":
        reasons.append(f"review status is {review.get('status')!r}, not 'approved'")

    if staged is not None and review:
        text = staged.get("source_text") or ""
        digest = hashlib.sha256(text.encode("utf8")).hexdigest()
        expected = review.get("source_text_sha256")
        if not expected:
            reasons.append("review records no source_text_sha256")
        elif digest != expected:
            reasons.append(f"staged statement sha256 {digest[:12]}… != reviewed {expected[:12]}…")

    if not (record.get("solution") or "").strip():
        reasons.append("empty solution")

    summary = (record.get("statement_summary") or "").strip()
    if not summary:
        reasons.append("empty statement_summary")
    elif AGENT_CANARY.search(summary):
        reasons.append("statement_summary contains an agent-directed sentence")

    patterns: list[str] = []
    raw = record.get("patterns")
    if not isinstance(raw, list) or not raw:
        reasons.append("no patterns")
    else:
        for label in raw:
            folded = aliases.get(canonical_label(str(label)), canonical_label(str(label)))
            if folded not in canonical:
                reasons.append(f"pattern {label!r} is not in the taxonomy")
            elif folded not in patterns:
                patterns.append(folded)
    return reasons, patterns


def build_record(problem_id: str, staged: dict[str, Any], summary: str,
                 patterns: list[str]) -> dict[str, Any]:
    reviewed = set(patterns)
    labels = with_families(patterns, MAX_LABELS)
    record: dict[str, Any] = {
        "id": problem_id,
        "title": staged.get("title") or "",
        "slug": staged.get("slug") or problem_id.split("-", 1)[-1],
        "platform": staged.get("platform") or platform_of(problem_id),
        "source_url": staged.get("source_url") or "",
        "source_topic": staged.get("source_topic") or "",
        "source_tags": staged.get("source_tags") or [],
        "statement": summary,
        "tags": [],
        "patterns": labels,
        "annotation": {
            "version": ANNOTATION_VERSION,
            "model": ANNOTATION_MODEL,
            "generated_at_unix": int(time.time()),
            "pattern_confidence": {
                label: (REVIEWED_CONFIDENCE if label in reviewed else FAMILY_CONFIDENCE)
                for label in labels
            },
            "reviewed_by": REVIEWED_BY,
            "evidence": EVIDENCE,
        },
        # Kattis and CodeChef expose no comparable rating. `null` says unknown;
        # a guessed tier would be indistinguishable from a measured one.
        "difficulty": None,
    }
    if isinstance(staged.get("kattis_difficulty"), dict):
        record["kattis_difficulty"] = staged["kattis_difficulty"]
    return record


def publish(batch: str, write: bool, root: Path = ROOT) -> dict[str, int]:
    proposals_doc = read_json(root / "data" / "analysis" / "external-proposals.json", {}) or {}
    review_doc = read_json(root / "data" / "analysis" / "external-review.json", {}) or {}
    staging = root / "data" / "analysis" / "external-staging"
    corpus = root / "data" / "problemset_llm"
    taxonomy = read_json(root / "data" / "pattern_taxonomy.json", {}) or {}
    canonical = set(taxonomy.get("canonical") or {})
    aliases = taxonomy.get("aliases") or {}

    reviews = by_id(review_doc)
    wanted = [p for p in (proposals_doc.get("problems") or [])
              if batch_of(p, proposals_doc) == batch]
    if not wanted:
        known = sorted({b for p in (proposals_doc.get("problems") or [])
                        if (b := batch_of(p, proposals_doc))})
        print(f"no proposals in batch {batch!r}" +
              (f"; known batches: {', '.join(known)}" if known else "; no batch is named yet"))
        return {"published": 0, "skipped": 0}

    stats = {"published": 0, "skipped": 0}
    written: list[Path] = []
    for proposal in wanted:
        problem_id = proposal["id"]
        review = reviews.get(problem_id) or {}
        # The skeptic's corrections are the point of the review pass.
        record = {**proposal, **{k: v for k, v in review.items() if v not in (None, "", [])}}
        staged = read_json(staging / f"{problem_id}.json", None)
        reasons, patterns = check(record, review, staged, canonical, aliases)
        if reasons:
            stats["skipped"] += 1
            print(f"  skip {problem_id}: {'; '.join(reasons)}")
            continue

        platform = staged.get("platform") or platform_of(problem_id)
        out = corpus / platform / f"{problem_id}.json"
        built = build_record(problem_id, staged, record["statement_summary"].strip(), patterns)
        stats["published"] += 1
        verb = "write" if write else "would write"
        print(f"  {verb} {out.relative_to(root)}  patterns={','.join(built['patterns'])}")
        if write:
            atomic_write_json(out, built)
            written.append(out)

    print(f"\n{stats['published']} publishable, {stats['skipped']} skipped "
          f"(skipped stay staged and keep counting as unavailable)")
    if not write:
        print("(dry run — nothing written; re-run with --write)")
    elif written:
        print("\nnext:\n  npm run embed && npm run validate"
              "   # embed FIRST: validate checks corpusHash")
    return stats


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--batch", help="publish the proposals carrying this batch name")
    ap.add_argument("--write", action="store_true",
                    help="actually write records; without it this is a dry run")
    ap.add_argument("--list", action="store_true", help="list the batch names in the proposals file")
    args = ap.parse_args()

    if args.list:
        doc = read_json(PROPOSALS, {}) or {}
        counts: dict[str, int] = {}
        for proposal in doc.get("problems") or []:
            counts[batch_of(proposal, doc) or "(no batch)"] = \
                counts.get(batch_of(proposal, doc) or "(no batch)", 0) + 1
        for name, n in sorted(counts.items()):
            print(f"  {name}  ({n} proposal(s))")
        return 0
    if not args.batch:
        ap.error("give --batch <name>, or --list")

    publish(args.batch, args.write)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
