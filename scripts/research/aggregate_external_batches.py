#!/usr/bin/env python3
"""One aggregated publish for batches B, D, E (and the kindergarten2 retry if approved).

For each batch: read data/analysis/external-batches/<X>/*.json proposals + skeptic*.json reviews,
append proposals to external-proposals.json, write review entries (keep + add ->
patterns) to external-review.json, copy approved verify scripts into
scripts/research/, then run publish_external.py --batch <X> --write. Finally splice
scratchpad/contests-draft.json into data/contests.json. Idempotent.
Run from the repo root:  python3 scripts/research/aggregate_external_batches.py [--dry-run] [--collections=id,id]
"""
import json, shutil, subprocess, sys, glob
from pathlib import Path
SC = Path(__file__).resolve().parents[2] / "data" / "analysis" / "external-batches"
DRY = "--dry-run" in sys.argv
ROOT = Path.cwd()
canon = set(json.loads((ROOT/"data/pattern_taxonomy.json").read_text())["canonical"])
P = ROOT/"data/analysis/external-proposals.json"; props = json.loads(P.read_text())
R = ROOT/"data/analysis/external-review.json"; rev = json.loads(R.read_text())
pby = {p["id"]: p for p in props["problems"]}
summary = {}
for batch in ("A", "B", "D", "E", "A2", "F", "G", "H", "I", "J"):   # C already published (2247a85); F–J = Hanoi 18, HCMC 17, Nha Trang 16, Hong Kong 16, Singapore 15
    bdir = SC/batch   # data/analysis/external-batches/<A|B|C|D|E|A2>/
    if not bdir.exists(): continue
    reviews = {}
    for f in sorted(bdir.glob("skeptic*.json")):
        for r in json.loads(f.read_text())["reviews"]: reviews[r["id"]] = (r, json.loads(f.read_text()))
    solved = {}
    for f in sorted(bdir.glob("*.json")):
        if f.stem.startswith("skeptic"): continue
        d = json.loads(f.read_text())
        if d.get("status") == "solved": solved[d["id"]] = d
    tag = "A" if batch == "A2" else batch
    st = {"solved": len(solved), "reviewed": 0, "approved": 0, "unreviewed": [], "not_approved": []}
    for pid, d in solved.items():
        if pid not in pby:
            props["problems"].append({"id": pid, "batch": tag, "patterns": d["patterns"], "pattern_confidence": d.get("pattern_confidence", {}),
                "tags": d.get("tags", []), "solution": d["solution"], "statement_summary": d["statement_summary"],
                "source_text_sha256": d["source_text_sha256"], "proposer": "opus-solver",
                "verify_script": f"scripts/research/verify_{pid.split('-',1)[1]}.py"}); pby[pid] = props["problems"][-1]
        if pid not in reviews: st["unreviewed"].append(pid); continue
        r, skfile = reviews[pid]; st["reviewed"] += 1
        pats = list(dict.fromkeys(r["keep"] + [a["label"] for a in r.get("add", [])]))
        bad = [x for x in pats if x not in canon]
        if bad: print(f"  !! {pid}: off-vocabulary from skeptic {bad} — dropping them"); pats = [x for x in pats if x in canon]
        rev["problems"] = [e for e in rev["problems"] if e["id"] != pid]
        rev["problems"].append({"id": pid, "batch": tag, "patterns": pats, "solution": d["solution"], "statement_summary": d["statement_summary"],
            "independent_band": r.get("independent_band"), "review_rationale": r.get("review_rationale", ""), "status": r["status"],
            "issues": r.get("issues", []), "source_text_sha256": r["source_text_sha256"], "reviewer": skfile.get("reviewer", "independent-skeptic"),
            "reviewed_at": skfile.get("reviewed_at")})
        if r["status"] == "approved":
            st["approved"] += 1
            src = bdir/f"verify_{pid.split('-',1)[1]}.py"; dst = ROOT/"scripts/research"/src.name
            if src.exists() and not dst.exists() and not DRY: shutil.copy(src, dst)
        else: st["not_approved"].append(f"{pid}:{r['status']}")
    summary[batch] = st
if not DRY:
    P.write_text(json.dumps(props, indent=2, ensure_ascii=False) + "\n"); R.write_text(json.dumps(rev, indent=2, ensure_ascii=False) + "\n")
for batch, st in summary.items():
    print(f"batch {batch}: solved {st['solved']}, reviewed {st['reviewed']}, approved {st['approved']}"
          + (f", unreviewed {st['unreviewed']}" if st['unreviewed'] else "") + (f", not approved {st['not_approved']}" if st['not_approved'] else ""))
for batch in [b for b in summary if summary[b]["approved"]]:
    tag = "A" if batch == "A2" else batch
    out = subprocess.run([sys.executable, "scripts/publish_external.py", "--batch", tag] + ([] if DRY else ["--write"]), capture_output=True, text=True)
    print(f"--- publish {tag} ---"); print("\n".join(l for l in out.stdout.splitlines() if "publishable" in l or "skip" in l.lower() or "wrote" in l))
# registry: splice the drafted collections (idempotent by id)
C = ROOT/"data/contests.json"; reg = json.loads(C.read_text()); draft = json.loads((SC/"_tooling"/"contests-draft.json").read_text())
have = {c["id"] for c in reg["collections"]}
# --collections a,b restricts which drafted collections are spliced this round —
# a collection with zero searchable members reads as sparseness, so Asia
# regionals wait until their batch publishes.
only = next((a.split("=",1)[1].split(",") for a in sys.argv if a.startswith("--collections=")), None)
new = [c for c in draft if c["id"] not in have and (only is None or c["id"] in only)]
if new and not DRY: reg["collections"] += new; C.write_text(json.dumps(reg, indent=2, ensure_ascii=False) + "\n")
print(f"registry: +{len(new)} collections ({', '.join(c['id'] for c in new)})")
print("\nnext: npm run embed && npm run validate && npm run bench && npm run test:search, then commit")
