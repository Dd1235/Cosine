#!/usr/bin/env python3
"""Snapshot public CSES counts and full statements without inferring count semantics."""
import argparse, concurrent.futures, datetime, hashlib, html, json, re, time, urllib.request
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
def fetch(url):
    for attempt in range(3):
        try:
            with urllib.request.urlopen(url, timeout=40) as r: return r.read().decode()
        except Exception:
            if attempt == 2: raise
            time.sleep(2 ** attempt)
def text(s):
    s = re.sub(r'<(?:script|style)\b.*?</(?:script|style)>', '', s, flags=re.S)
    s = re.sub(r'</(?:p|h1|h2|li|pre|div)>', '\n', s)
    return html.unescape(re.sub('<[^>]+>', '', s)).strip()
CHECK = ROOT/'data/cses/count_semantics_check.json'
def shown(path):
    try: return path.relative_to(ROOT)
    except ValueError: return path
def set_semantics(value, output):
    """Record what the two public counts mean - only ever from a completed check.

    The task statistics page needs a login, so the check is the owner's manual
    procedure (documented in data/cses/README.md), not something this script can
    perform. Without its file, or with a file that concluded something else,
    this refuses: an unverified semantics claim is what every gate here exists
    to prevent."""
    if not CHECK.exists():
        raise SystemExit(f'Refusing: {shown(CHECK)} does not exist. Run the manual logged-in count check first; the procedure is in data/cses/README.md.')
    check = json.loads(CHECK.read_text())
    conclusion = check.get('conclusion')
    if conclusion != value:
        raise SystemExit(f'Refusing: {shown(CHECK)} concludes {conclusion!r}, not {value!r}.')
    snapshot_path = output/'public_counts.json'
    if not snapshot_path.exists():
        raise SystemExit(f'Refusing: no snapshot at {snapshot_path}.')
    snapshot = json.loads(snapshot_path.read_text())
    snapshot['verified_count_semantics'] = value
    snapshot['count_semantics'] = f'verified by manual logged-in task-statistics check: {value}'
    snapshot['count_semantics_evidence'] = 'data/cses/count_semantics_check.json'
    snapshot_path.write_text(json.dumps(snapshot, indent=2)+'\n')
    # Semantics are a frozen input, so this invalidates the freeze on purpose.
    print(f'Recorded verified_count_semantics={value!r}. The frozen input hash no longer verifies; re-freeze before publishing again.')

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--output', type=Path, default=ROOT/'data/cses')
    ap.add_argument('--set-semantics', dest='set_semantics', help='record verified count semantics from data/cses/count_semantics_check.json instead of snapshotting')
    args=ap.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    if args.set_semantics:
        return set_semantics(args.set_semantics, args.output)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
    page=fetch('https://cses.fi/problemset/')
    records=[]
    for section, contents in re.findall(r'<h2>(.*?)</h2>(.*?)(?=<h2>|$)', page, re.S):
        for ident,title,first,second in re.findall(r'<li class="task"><a href="/problemset/task/(\d+)">(.*?)</a><span class="detail">(\d+) / (\d+)</span>',contents):
            records.append(dict(id='cses-'+ident,title=text(title),section=text(section),source_url=f'https://cses.fi/problemset/task/{ident}',public_count_first=int(first),public_count_second=int(second),release_cohort=None))
    assert len(records)==len({x['id'] for x in records}) and records
    snapshot=dict(observed_at=stamp,source_url='https://cses.fi/problemset/',count_semantics='unverified: public list displays two unlabeled counts; task statistics require login',release_cohort_policy='unknown; no age inferred from task ID or local annotation timestamp',problems=records)
    (args.output/'public_counts.json').write_text(json.dumps(snapshot,indent=2)+'\n')
    def get(record):
        out=args.output/'statements'/(record['id']+'.json');out.parent.mkdir(exist_ok=True)
        if out.exists(): return
        page=fetch(record['source_url'])
        content=page.split('<div class="content">',1)[1].split('<div class="nav sidebar">',1)[0]
        statement=text(content)
        if ('Input' not in statement or 'Output' not in statement) and 'Interaction' not in statement: raise ValueError('missing statement '+record['id'])
        result={k:record[k] for k in ['id','title','source_url']};result.update(observed_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),statement=statement,statement_sha256=hashlib.sha256(statement.encode()).hexdigest())
        temp=out.with_suffix('.tmp'); temp.write_text(json.dumps(result,indent=2)+'\n');temp.replace(out)
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool: list(pool.map(get, records))
    print(f'Snapshotted {len(records)} tasks; count semantics and release dates deliberately unverified.')
if __name__=='__main__': main()
