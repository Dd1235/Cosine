#!/usr/bin/env python3
"""
Fetch Codeforces statements through Tavily, for problems the dataset doesn't
have yet.

Why this exists: codeforces.com answers a script with 403, and the official
mirrors (m1/m3) answer 200 with a JavaScript challenge page rather than a
statement — so `ingest_contest.py` has been sourcing statements from the
open-r1 dataset, which lags live contests by weeks. 27 problems from four
August rounds were sitting in data/pending_contests.json waiting on it.

Tavily's extract endpoint gets through. It needs `extract_depth: "advanced"`:
the basic depth returns navigation chrome and stops before the statement.

This does NOT replace the open-r1 path — that one is free and works fine for
anything old enough. This is the way to not wait.

  python3 scripts/fetch_statements.py --dry-run       # what is missing
  python3 scripts/fetch_statements.py                 # drain the pending queue
  python3 scripts/fetch_statements.py --ids codeforces-2253-f codeforces-2254-g

The key comes from TAVILY in .env. Statements are MERGED into the cache that
every other script reads; the two standalone fetchers truncate that file and
must never be used for a partial top-up.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from ingest_contest import CF_STATEMENTS, PENDING, merge_statements, read_json  # noqa: E402

TAVILY_EXTRACT = "https://api.tavily.com/extract"
# Tavily bills per five URLs, so five is the batch size — a smaller batch costs
# the same as a full one.
BATCH = 5
# Where the page stops being Codeforces chrome and starts being the problem.
STATEMENT_MARKER = "time limit per test"
MIN_STATEMENT = 200   # shorter than this and we got a challenge page, not a problem


def env_key() -> str:
    key = os.environ.get("TAVILY") or os.environ.get("TAVILY_API_KEY")
    if not key:
        env = ROOT / ".env"
        if env.exists():
            for line in env.read_text().splitlines():
                m = re.match(r"\s*(TAVILY|TAVILY_API_KEY)\s*=\s*(.+)", line)
                if m:
                    key = m.group(2).strip().strip("\"'")
                    break
    if not key:
        sys.exit("TAVILY is not set (put it in .env)")
    return key


def problem_url(pid: str) -> str | None:
    m = re.match(r"^codeforces-(\d+)-([a-z0-9]+)$", pid)
    if not m:
        return None
    return f"https://codeforces.com/problemset/problem/{m.group(1)}/{m.group(2).upper()}"


def tavily_extract(urls: list[str], key: str) -> dict[str, str]:
    body = json.dumps({"urls": urls, "extract_depth": "advanced"}).encode()
    req = Request(
        TAVILY_EXTRACT,
        data=body,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    with urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read().decode())
    out: dict[str, str] = {}
    for r in data.get("results", []):
        out[r.get("url", "")] = r.get("raw_content") or ""
    for r in data.get("failed_results", []):
        print(f"    tavily could not read {r.get('url')}: {str(r.get('error'))[:60]}", file=sys.stderr)
    return out


def clean_statement(raw: str) -> str:
    """The problem, without the site around it.

    Everything before `time limit per test` is the navigation bar, the contest
    header and the tag box; everything after the footer is copyright. The
    middle keeps its LaTeX — the annotator reads it fine and cutting it would
    lose the constraints, which is most of what distinguishes a D from an F.
    """
    i = raw.find(STATEMENT_MARKER)
    body = raw[i:] if i >= 0 else raw
    for stop in ("Codeforces (c) Copyright", "The time is now", "Supported by"):
        j = body.find(stop)
        if j > MIN_STATEMENT:
            body = body[:j]
    body = re.sub(r"\n{3,}", "\n\n", body)
    return body.strip()


def pending_names() -> dict[str, str]:
    """The real problem names, which the queue already knows.

    The Codeforces problemset cache predates these contests, so without this
    the annotator falls back to whatever `title` the statement record carries —
    and 27 problems went in called `codeforces-2248-e`.
    """
    pend = read_json(PENDING, {"problems": []})
    return {p["id"]: p.get("name") or p["id"] for p in pend.get("problems", [])}


def wanted_ids(args: argparse.Namespace) -> list[str]:
    if args.ids:
        return list(args.ids)
    pending = read_json(PENDING, {"problems": []})
    return [p["id"] for p in pending.get("problems", [])]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ids", nargs="*", help="problem ids; defaults to the pending queue")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--limit", type=int, default=0, help="stop after N problems")
    args = ap.parse_args()

    cache = read_json(CF_STATEMENTS, {})
    ids = [i for i in wanted_ids(args) if i not in cache]
    if args.limit:
        ids = ids[: args.limit]
    already = len(wanted_ids(args)) - len(ids)
    print(f"{len(ids)} statement(s) to fetch" + (f", {already} already cached" if already else ""))
    if not ids:
        return 0
    if args.dry_run:
        for pid in ids:
            print(f"  would fetch {pid}  {problem_url(pid)}")
        print(f"\n~{-(-len(ids) // BATCH) * 2} tavily credits")
        return 0

    key = env_key()
    names = pending_names()
    by_url = {problem_url(i): i for i in ids if problem_url(i)}
    urls = list(by_url)
    found: dict[str, dict[str, Any]] = {}
    for start in range(0, len(urls), BATCH):
        chunk = urls[start : start + BATCH]
        print(f"  extracting {start + 1}-{start + len(chunk)} of {len(urls)}…")
        try:
            pages = tavily_extract(chunk, key)
        except (HTTPError, URLError, TimeoutError) as exc:
            print(f"    batch failed: {exc}", file=sys.stderr)
            continue
        for url, raw in pages.items():
            pid = by_url.get(url) or by_url.get(url.rstrip("/"))
            if not pid:
                continue
            body = clean_statement(raw)
            if len(body) < MIN_STATEMENT:
                print(f"    {pid}: only {len(body)} chars — looks like a challenge page, skipping")
                continue
            cid, index = pid.split("-")[1], pid.split("-")[2].upper()
            found[pid] = {
                "id": pid,
                "contest_id": int(cid),
                "index": index,
                "title": names.get(pid, pid),
                "rating": None,
                "tags": [],
                "statement": body[:6000],
                "url": url,
                "source": "tavily",
            }
            print(f"    {pid}: {len(body)} chars")
        time.sleep(1)   # be polite between batches

    added = merge_statements(found)
    print(f"\nmerged {added} new statement(s); cache now {len(read_json(CF_STATEMENTS, {}))}")
    missing = [i for i in ids if i not in found]
    if missing:
        print(f"still missing ({len(missing)}): {', '.join(missing)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
