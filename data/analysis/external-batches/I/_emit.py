"""Helper: write a batch-I annotation file with the staging source_text sha256."""
import hashlib
import json
import os
import sys

REPO = "/Users/dedeepya/Cosine"
BATCH = os.path.join(REPO, "data/analysis/external-batches/I")


def emit(doc):
    pid = doc["id"]
    staged = json.load(open(os.path.join(REPO, "data/analysis/external-staging", pid + ".json")))
    doc["source_text_sha256"] = hashlib.sha256(staged["source_text"].encode("utf-8")).hexdigest()
    words = len(doc["statement_summary"].split())
    if not (40 <= words <= 70):
        print("WARNING %s: statement_summary is %d words" % (pid, words), file=sys.stderr)
    out = os.path.join(BATCH, pid + ".json")
    with open(out, "w") as fh:
        json.dump(doc, fh, indent=1, ensure_ascii=False)
        fh.write("\n")
    print("wrote", out, "(%d words)" % words)
