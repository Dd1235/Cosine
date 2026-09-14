#!/usr/bin/env python3
"""Publish solution-reviewed CSES estimates only after evidence gates; dry-run default."""
import argparse, hashlib, json, math
from pathlib import Path
from evaluate_cses_difficulty import digest
ROOT=Path(__file__).resolve().parents[1]
D=ROOT/'data/cses'
def read(name): return json.loads((D/name).read_text())
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--write',action='store_true')
 # The scope names what the bands are being published *as*; the default keeps
 # the pre-review-decision label, so a bare re-run can never promote them.
 ap.add_argument('--scope',default='local-review-candidate')
 args=ap.parse_args()
 report=read('pilot_report.json');frozen=read('frozen_model.json')
 if digest([read('public_counts.json'),read('pilot.json'),read('reviews_a.json'),read('reviews_b.json'),read('solution_verifications.json')]) != frozen['inputs_hash']:
  raise SystemExit('Research inputs changed after formula freeze')
 if not report['pilot_numerical_gate'] or frozen['selected']!='review_only':
  raise SystemExit('This publisher supports only the gated review-only fallback')
 a={r['id']:r for r in read('reviews_a.json')['reviews']};b={r['id']:r for r in read('reviews_b.json')['reviews']}
 if read('reviews_a.json')['reviewer_id']==read('reviews_b.json')['reviewer_id']:raise SystemExit('Independent assessors required')
 specialists={r['id']:(r,f) for f in ['specialist_a.json','specialist_b.json'] for r in read(f)['reviews']}
 verified={r['id'] for r in read('solution_verifications.json')['reviews'] if r.get('resolved')}
 files=sorted((ROOT/'data/problemset_llm/cses').glob('*.json')); expected={p.stem for p in files}
 if len(expected)!=400 or set(a)!=expected or set(b)!=expected:raise SystemExit('Complete 400-task double review required')
 result=[]
 for path in files:
  p=json.loads(path.read_text());ident=p['id'];s=read('statements/'+ident+'.json')
  sha=hashlib.sha256(s['statement'].encode()).hexdigest()
  for r in [a[ident],b[ident]]:
   if r['statement_sha256']!=sha or not r.get('solution_rationale') or not r.get('complexity'):raise SystemExit('Missing grounded review '+ident)
  if abs(a[ident]['band']-b[ident]['band'])>=2 and ident not in specialists:raise SystemExit('Unadjudicated two-band disagreement '+ident)
  if a[ident].get('status')=='specialist_verification_required' and ident not in verified:raise SystemExit('Unresolved specialist '+ident)
  band=math.floor((a[ident]['band']+b[ident]['band'])/2+.5)
  confidence='high' if a[ident]['band']==b[ident]['band'] else 'medium'
  evidence=[s['source_url'],'data/cses/reviews_a.json','data/cses/reviews_b.json']
  override=None
  if ident in specialists:
   r,f=specialists[ident]
   if not r['status'].startswith('resolved'):raise SystemExit('Unresolved specialist '+ident)
   override=dict(original_band=band,reason='Completed specialist solution and proof review',evidence='data/cses/'+f)
   band=r['band'];confidence='medium';evidence.append('data/cses/'+f)
   if 'computational' in r['status']:confidence='low'
  metadata=dict(band=band,confidence=confidence,method='cses-reviewed-v1',evidence=evidence,statement_sha256=sha,statistics_adjustment=0,reviewed_at='2026-09-11')
  if override:metadata['override']=override
  p['cses_difficulty']=metadata
  if args.write:path.write_text(json.dumps(p,ensure_ascii=False,indent=2)+'\n')
  result.append(dict(id=ident,**metadata))
 if args.write:
  (D/'published_bands.json').write_text(json.dumps(dict(method='cses-reviewed-v1',scope=args.scope,statistical_model='disabled: count semantics and release cohorts unverified',problems=result),indent=2)+'\n')
 print(('Published' if args.write else 'Would publish'),len(result),'reviewed bands')
if __name__=='__main__':main()
