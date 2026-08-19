#!/usr/bin/env python3
"""
Find LeetCode problems in the corpus that aren't algorithm problems.

`Analyze Organization Hierarchy` was sitting in the corpus labelled `tree-dp`,
`dfs`, `topological-sort` — none of which anyone writes for it, because the
answer is a recursive CTE. It is a SQL problem. So are 21 others, and two more
are Shell problems.

LeetCode says so itself: every question carries a `categoryTitle`, one of
Algorithms / Database / Shell / Concurrency / JavaScript / pandas. Nothing in
the pipeline had ever looked at it.

  python3 scripts/audit_leetcode_category.py            # report
  python3 scripts/audit_leetcode_category.py --write    # delete the non-algorithm ones

The category is cached in data/cache/leetcode_categories.json, so the 25-minute
sweep happens once. `--refresh` re-checks anything already cached.

This sweeps EVERY LeetCode record, not just the ones whose `source_tags` say
`database` — those tags are only as complete as the annotate run that captured
them, and the category is authoritative.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent.parent
CORPUS = ROOT / "data" / "problemset_llm" / "leetcode"
CACHE = ROOT / "data" / "cache" / "leetcode_categories.json"
REMOVALS = ROOT / "data" / "analysis" / "_leetcode-category-removal.json"
SEEDS = ROOT / "Problems"
GRAPHQL = "https://leetcode.com/graphql"
KEEP = "Algorithms"
PAUSE = 1.0   # LeetCode is fine with this and unfriendly to much less
RETRIES = 3   # 403s come in short bursts; backing off clears them


def read_json(path: Path, default):
    try:
        return json.loads(path.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def category_of(slug: str, attempt: int = 1) -> str | None:
    payload = json.dumps({
        "query": "query q($s:String!){question(titleSlug:$s){categoryTitle}}",
        "variables": {"s": slug},
    }).encode()
    req = Request(GRAPHQL, data=payload, headers={
        "Content-Type": "application/json", "User-Agent": "Mozilla/5.0"})
    try:
        with urlopen(req, timeout=45) as resp:
            data = json.loads(resp.read().decode())
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        # A failure is not an answer. Nothing is cached for this slug, so the
        # record simply keeps its place in the corpus and the next run retries
        # it — but a run that quietly leaves 40 slugs unchecked looks exactly
        # like a run that found nothing wrong with them, so retry here and
        # report what is still unknown at the end.
        if attempt < RETRIES:
            time.sleep(PAUSE * 4 * attempt)
            return category_of(slug, attempt + 1)
        print(f"    {slug}: {str(exc)[:60]}", file=sys.stderr)
        return None
    q = (data.get("data") or {}).get("question")
    return (q or {}).get("categoryTitle")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true", help="delete the non-algorithm records")
    ap.add_argument("--refresh", action="store_true", help="re-check slugs already cached")
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    records = {}
    for path in sorted(CORPUS.glob("*.json")):
        d = json.loads(path.read_text())
        slug = d.get("slug") or re.sub(r"^leetcode-", "", d["id"])
        records[d["id"]] = (path, d, slug)

    cache = read_json(CACHE, {})
    todo = [i for i in records if args.refresh or records[i][2] not in cache]
    if args.limit:
        todo = todo[: args.limit]
    print(f"{len(records)} leetcode records; {len(cache)} cached; {len(todo)} to check")

    for n, pid in enumerate(todo, start=1):
        slug = records[pid][2]
        cat = category_of(slug)
        if cat:
            cache[slug] = cat
        if n % 50 == 0 or n == len(todo):
            print(f"  checked {n}/{len(todo)}")
            CACHE.write_text(json.dumps(cache, indent=0, sort_keys=True) + "\n")
        time.sleep(PAUSE)
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(cache, indent=0, sort_keys=True) + "\n")

    offenders = []
    unknown = []
    for pid, (path, d, slug) in sorted(records.items()):
        cat = cache.get(slug)
        if cat is None:
            unknown.append(pid)
        elif cat != KEEP:
            offenders.append((pid, cat, d.get("title", ""), d.get("source_url", "")))

    print(f"\n{len(offenders)} record(s) are not {KEEP}:")
    for pid, cat, title, _ in offenders:
        print(f"  {cat:12} {pid:52} {title[:40]}")
    if unknown:
        print(f"\n{len(unknown)} record(s) have no category yet (network?): {unknown[:5]}")

    if not args.write:
        if offenders:
            print("\nre-run with --write to remove them")
        return 0

    # The seed file matters as much as the record: leaving the URL there means
    # the next `annotate_problem_urls.py --urls Problems/urls.txt` puts the
    # problem straight back.
    urls = {o[3].rstrip("/") for o in offenders if o[3]}
    seeds_cleaned = {}
    for seed in sorted(SEEDS.glob("urls*.txt")):
        lines = seed.read_text().splitlines()
        kept = [l for l in lines if l.strip().rstrip("/") not in urls]
        if len(kept) != len(lines):
            seed.write_text("\n".join(kept) + "\n")
            seeds_cleaned[seed.name] = len(lines) - len(kept)

    for pid, _cat, _t, _u in offenders:
        records[pid][0].unlink()

    REMOVALS.parent.mkdir(parents=True, exist_ok=True)
    REMOVALS.write_text(json.dumps({
        "why": "LeetCode's own categoryTitle says these are not Algorithms problems. "
               "A SQL problem in a DSA corpus answers searches it has nothing to do "
               "with, and drags SQL vocabulary (order-by, window-functions, join) "
               "into the technique index.",
        "reviewed_at": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "removed": [{"id": p, "category": c, "title": t, "url": u} for p, c, t, u in offenders],
    }, ensure_ascii=False, indent=1) + "\n")

    print(f"\nremoved {len(offenders)} record(s); cleaned {seeds_cleaned or 'no seed files'}")
    print(f"recorded in {REMOVALS.relative_to(ROOT)}")
    print("\nnext: npm run embed && npm run validate")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
