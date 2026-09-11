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
def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--output', type=Path, default=ROOT/'data/cses'); args=ap.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
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
