#!/usr/bin/env python3
"""Print a collection's members as member objects, from the staged statements.

    python3 scripts/print_registry_members.py icpc-world-finals-2024
    python3 scripts/print_registry_members.py --all

data/contests.json lists members as bare ids; the title, the judge link and the
Kattis difficulty live in data/analysis/external-staging/<id>.json. This joins
the two so a member list can be reviewed (or pasted back as member objects)
without opening one file per problem, and says `"missing": true` for an id with
no staging file rather than inventing a title for it.

Read-only by construction: it prints, and writes nothing.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
CONTESTS = ROOT / "data" / "contests.json"
STAGING = ROOT / "data" / "analysis" / "external-staging"


def member_id(member: Any) -> str:
    """Members are ids today and may be objects tomorrow; accept both."""
    return member.get("id", "") if isinstance(member, dict) else str(member)


def member_object(problem_id: str) -> dict[str, Any]:
    path = STAGING / f"{problem_id}.json"
    try:
        staged = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return {"id": problem_id, "missing": True}
    return {"id": problem_id,
            "title": staged.get("title"),
            "url": staged.get("source_url"),
            "kattis_difficulty": staged.get("kattis_difficulty")}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("collection", nargs="?", help="a data/contests.json collection id")
    ap.add_argument("--all", action="store_true", help="every collection in the registry")
    args = ap.parse_args()
    if not args.collection and not args.all:
        ap.error("give a collection id or --all")

    registry = json.loads(CONTESTS.read_text())
    collections = registry.get("collections") or []
    if not args.all:
        collections = [c for c in collections if c.get("id") == args.collection]
        if not collections:
            print(f"no collection {args.collection!r} in {CONTESTS.relative_to(ROOT)}",
                  file=sys.stderr)
            return 1

    for collection in collections:
        members = [member_object(member_id(m)) for m in collection.get("problems") or []]
        absent = sum(1 for m in members if m.get("missing"))
        print(f"# {collection.get('id')}  ({len(members)} members"
              + (f", {absent} without a staging file" if absent else "") + ")")
        print(json.dumps(members, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
