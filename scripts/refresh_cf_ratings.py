#!/usr/bin/env python3
"""
Fill in Codeforces ratings that didn't exist when the problem was ingested.

A contest reports `rating: null` for its problems for days or weeks after it
runs — the value is derived from how many people solved what. So a problem
ingested the day it appeared has no difficulty, which means every difficulty
filter and every sort is blind to it, and `my level` can't reach it either.

Nothing else in the pipeline goes back for it. This does:

  python3 scripts/refresh_cf_ratings.py            # report what is missing
  python3 scripts/refresh_cf_ratings.py --write    # fill in what has landed

Safe to run any time — it only ever fills a rating that is currently absent,
and never overwrites one. Judge tags get the same treatment, since they arrive
on the same schedule and `apply_source_tags.py` needs them.

`difficulty` is metadata: `corpusHash` covers title/statement/tags/patterns, so
a rating alone needs no re-embed. Filling `source_tags` does not either — but
running `apply_source_tags.py` afterwards moves tags into the indexed text and
that does.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CORPUS = ROOT / "data" / "problemset_llm" / "codeforces"
API = "https://codeforces.com/api/problemset.problems"


def live_problems() -> dict[tuple[int, str], dict]:
    req = urllib.request.Request(API, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=90) as resp:
        payload = json.loads(resp.read().decode())
    if payload.get("status") != "OK":
        sys.exit(f"codeforces api: {payload.get('comment')}")
    return {(p["contestId"], p["index"].upper()): p for p in payload["result"]["problems"]}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    live = live_problems()
    filled_rating: list[str] = []
    filled_titles: list[str] = []
    filled_tags: list[str] = []
    still_missing: list[str] = []

    for path in sorted(CORPUS.glob("*.json")):
        d = json.loads(path.read_text())
        m = re.match(r"codeforces-(\d+)-([a-z0-9]+)$", d.get("id", ""))
        if not m:
            continue
        needs_title = d.get("title") == d.get("id")
        if d.get("difficulty") is not None and d.get("source_tags") and not needs_title:
            continue
        p = live.get((int(m.group(1)), m.group(2).upper()))
        if not p:
            continue

        changed = False
        # A record whose title is its own id came from a statement fetched
        # before the name was known. The API has it.
        if needs_title and p.get("name"):
            d["title"] = p["name"]
            filled_titles.append(f"{d['id']} -> {p['name']}")
            changed = True
        if d.get("difficulty") is None:
            if p.get("rating"):
                d["difficulty"] = p["rating"]
                filled_rating.append(f"{d['id']} -> {p['rating']}")
                changed = True
            else:
                still_missing.append(d["id"])
        if not d.get("source_tags") and p.get("tags"):
            d["source_tags"] = p["tags"]
            filled_tags.append(d["id"])
            changed = True
        if changed and args.write:
            path.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n")

    verb = "filled" if args.write else "would fill"
    print(f"{verb} {len(filled_rating)} rating(s), {len(filled_tags)} tag set(s), {len(filled_titles)} title(s)")
    for line in filled_titles[:10]:
        print(f"  {line}")
    for line in filled_rating[:20]:
        print(f"  {line}")
    if still_missing:
        print(f"{len(still_missing)} still unrated by codeforces — run this again in a week")
    if args.write and filled_tags:
        print("\nnext: python3 scripts/apply_source_tags.py --write && npm run embed && npm run validate")
    elif not args.write and (filled_rating or filled_tags):
        print("\nre-run with --write")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
