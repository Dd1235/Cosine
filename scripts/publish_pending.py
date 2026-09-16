#!/usr/bin/env python3
"""Publish staged CodeChef statements as searchable, labels-pending records.

    python3 scripts/publish_pending.py                # dry run: what would be written
    python3 scripts/publish_pending.py --write
    python3 scripts/publish_pending.py --contest AMR17ROL --write

This is tier one of a two-tier ingest. A record written here carries the
problem's own statement (an extractive lead, never an LLM summary) and the
judge's own tags, and NOTHING of ours: `patterns` is empty and
`review_status` is "labels-pending". That is the honest claim — nobody here
has solved the problem — and it has a useful side effect: with no patterns the
record can never match a technique filter, so it cannot pollute exactly the
queries this corpus exists to answer. It still ranks on its words.

Tier two (`scripts/publish_external.py`) later replaces the lead and the empty
patterns in place, after a derived solution and an independent skeptic review,
and drops `review_status`. This script never touches a record that already
exists, so a reviewed record cannot be downgraded by re-running it.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
STAGING = ROOT / "data" / "analysis" / "external-staging"
CORPUS = ROOT / "data" / "problemset_llm"

ANNOTATION_VERSION = "problem-patterns-v1"
ANNOTATION_MODEL = "codechef-judge-tags"
REVIEW_STATUS = "labels-pending"
MAX_STATEMENT_CHARS = 600   # scripts/validate_corpus.js warns above this
MAX_LABELS = 12
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SENTENCE_END = re.compile(r"(?<=[.!?])\s+")


def plain(text: str) -> str:
    """Whitespace-collapsed statement text with inline math delimiters dropped."""
    t = re.sub(r"\$([^$\n]{1,60})\$", r"\1", text or "")
    t = re.sub(r"\s+", " ", t).strip()
    return t


def extractive_lead(text: str, limit: int = MAX_STATEMENT_CHARS) -> str:
    """The first sentences of the statement, at least two when there are two,
    cut at a sentence boundary under `limit`. Deterministic; no model."""
    t = plain(text)
    if not t:
        return ""
    sentences = [s for s in SENTENCE_END.split(t) if s]
    out: list[str] = []
    for s in sentences:
        candidate = " ".join(out + [s])
        if out and len(out) >= 2 and len(candidate) > limit:
            break
        if len(candidate) > limit:
            if out:
                break
            # A single opening sentence longer than the limit: cut at a word.
            cut = candidate[: limit - 1]
            cut = cut[: cut.rfind(" ")] if " " in cut else cut
            return cut.rstrip(",;: ") + "…"
        out.append(s)
    return " ".join(out)


def judge_tags(staged: dict[str, Any]) -> list[str]:
    seen: list[str] = []
    for tag in staged.get("judge_tags") or []:
        tag = str(tag).strip().lower()
        if SLUG_RE.match(tag) and tag not in seen:
            seen.append(tag)
        if len(seen) >= MAX_LABELS:
            break
    return seen


def build_pending_record(staged: dict[str, Any], now: int | None = None) -> dict[str, Any]:
    pid = staged["id"]
    code = ((staged.get("contest_source") or {}).get("problem_code")
            or pid.split("-", 1)[-1].upper())
    return {
        "id": pid,
        "title": staged.get("title") or "",
        "slug": staged.get("slug") or pid.split("-", 1)[-1],
        "platform": staged.get("platform") or "codechef",
        "source_url": staged.get("source_url") or f"https://www.codechef.com/problems/{code}",
        "source_topic": staged.get("source_topic") or "",
        "source_tags": staged.get("source_tags") or [],
        "statement": extractive_lead(staged.get("source_text") or ""),
        "tags": judge_tags(staged),
        "patterns": [],
        "review_status": REVIEW_STATUS,
        "annotation": {
            "version": ANNOTATION_VERSION,
            "model": ANNOTATION_MODEL,
            "generated_at_unix": int(now if now is not None else time.time()),
            "pattern_confidence": {},
            "reviewed_by": None,
            "evidence": f"https://www.codechef.com/api/contests/PRACTICE/problems/{code}",
        },
        # No comparable rating exists for these; a guessed tier would be
        # indistinguishable from a measured one.
        "difficulty": None,
        "contest_source": staged.get("contest_source") or {},
    }


def eligible(staged: dict[str, Any]) -> tuple[bool, str]:
    cs = staged.get("contest_source") or {}
    if cs.get("host") != "codechef.com":
        return False, "not a CodeChef contest record"
    if len(plain(staged.get("source_text") or "")) < 150:
        return False, "statement too short"
    if not judge_tags(staged):
        return False, "no judge tags (nothing indexable beyond the statement)"
    return True, ""


def run(write: bool, contest: str | None, root: Path = ROOT) -> dict[str, int]:
    staging, corpus = root / "data" / "analysis" / "external-staging", root / "data" / "problemset_llm"
    stats = {"written": 0, "exists": 0, "skipped": 0}
    for path in sorted(staging.glob("codechef-*.json")):
        staged = json.loads(path.read_text())
        cs = staged.get("contest_source") or {}
        if contest and cs.get("name") != contest:
            continue
        ok, why = eligible(staged)
        if not ok:
            stats["skipped"] += 1
            print(f"  skip  {staged.get('id')}: {why}")
            continue
        out = corpus / "codechef" / f"{staged['id']}.json"
        if out.exists():
            stats["exists"] += 1
            print(f"  have  {staged['id']}  (never overwritten)")
            continue
        record = build_pending_record(staged)
        stats["written"] += 1
        print(f"  {'wrote' if write else 'would write'} {out.relative_to(root)}  "
              f"[{len(record['statement'])} chars, tags: {', '.join(record['tags'])}]")
        if write:
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n")
    print(f"{stats['written']} {'written' if write else 'publishable'}, {stats['exists']} already present, "
          f"{stats['skipped']} skipped" + ("" if write else "  (dry run — nothing written)"))
    if stats["written"] and write:
        print("next: npm run embed && npm run validate && npm run bench && npm run test:search")
    return stats


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--write", action="store_true", help="write records (default: dry run)")
    ap.add_argument("--contest", help="only this CodeChef contest code, e.g. AMR17ROL")
    args = ap.parse_args(argv)
    run(args.write, args.contest)
    return 0


if __name__ == "__main__":
    sys.exit(main())
