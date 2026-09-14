#!/usr/bin/env python3
"""Fail-closed CSES pilot evaluation. Never manufactures reviews or release dates."""
import argparse, hashlib, json, math, statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
VARIANTS=('review_only','completion','volume','combined')
def read(path): return json.loads(Path(path).read_text())
def digest(value): return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def percentile(values, value):
    return (sum(x<value for x in values)+0.5*sum(x==value for x in values))/len(values)
def predictions(snapshot, reviews, variant):
    ps=snapshot['problems']; by={p['id']:p for p in ps}
    verified=snapshot.get('verified_count_semantics')=='distinct_solvers_over_distinct_attempting_users'
    mu=sum(p['public_count_first'] for p in ps)/max(1,sum(p['public_count_second'] for p in ps))
    ratios={p['id']:(p['public_count_first']+100*mu)/(p['public_count_second']+100) for p in ps}
    out={}
    for ident,(r1,r2) in reviews.items():
        p=by[ident]; base=(r1['band']+r2['band'])/2; adjustment=0.
        if verified and variant!='review_only':
            completion=1-percentile(list(ratios.values()),ratios[ident])
            cohort=p.get('release_cohort'); peers=[x for x in ps if cohort and x.get('release_cohort')==cohort]
            volume=None
            if len(peers)>=10: volume=1-percentile([math.log1p(x['public_count_second']) for x in peers],math.log1p(p['public_count_second']))
            signals={'completion':[completion],'volume':[] if volume is None else [volume],'combined':[] if volume is None else [completion,volume]}[variant]
            # Missing cohort disables volume contribution, never imputes age.
            if signals:
                reliability=p['public_count_second']/(p['public_count_second']+100)
                if p.get('age_days') is not None: reliability*=min(1,max(0,p['age_days'])/180)
                adjustment=(statistics.mean(signals)-0.5)*reliability
        out[ident]={'continuous':base+adjustment,'band':max(1,min(5,math.floor(base+adjustment+0.5))),'adjustment':adjustment}
    return out

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--evidence',type=Path,default=ROOT/'data/cses');ap.add_argument('--phase',choices=['freeze','evaluate'],required=True);a=ap.parse_args();d=a.evidence
    snapshot=read(d/'public_counts.json'); pilot=read(d/'pilot.json')
    a1=read(d/'reviews_a.json');a2=read(d/'reviews_b.json')
    verifications=read(d/'solution_verifications.json') if (d/'solution_verifications.json').exists() else {'reviews':[]}
    verified_solutions={r['id']:r for r in verifications['reviews'] if r.get('resolved') and r.get('solution_rationale') and r.get('complexity')}
    if a1['reviewer_id']==a2['reviewer_id']: raise SystemExit('Independent reviewers required')
    left={x['id']:x for x in a1['reviews']};right={x['id']:x for x in a2['reviews']}
    ids=pilot['development']+pilot['held_out']
    if len(pilot['development'])!=30 or len(pilot['held_out'])!=30 or len(set(ids))!=60: raise SystemExit('Pilot requires disjoint 30/30 split')
    for ident in ids:
        for review in (left.get(ident),right.get(ident)):
            if not review or (review.get('status')=='specialist_verification_required' and ident not in verified_solutions) or not isinstance(review.get('band'),int) or not 1<=review['band']<=5 or not review.get('solution_rationale') or not review.get('complexity'): raise SystemExit('Missing grounded review: '+ident)
    paired={i:(left[i],right[i]) for i in ids}
    preds={v:predictions(snapshot,paired,v) for v in VARIANTS}
    def metrics(variant, subset, labels):
        for ident in subset:
            if ident not in labels or labels[ident].get('unresolved') or not isinstance(labels[ident].get('band'),int) or not 1<=labels[ident]['band']<=5: raise SystemExit('Missing independent evaluation: '+ident)
        errors=[abs(preds[variant][i]['band']-labels[i]['band']) for i in subset]
        return dict(mae=statistics.mean(errors),within_one=sum(e<=1 for e in errors)/len(errors),two_band_errors=[i for i,e in zip(subset,errors) if e>=2])
    inputs_hash=digest([snapshot,pilot,a1,a2,verifications])
    if a.phase=='freeze':
        evaluation=read(d/'evaluation_development.json');labels={x['id']:x for x in evaluation['reviews']}
        if evaluation['reviewer_id'] in {a1['reviewer_id'],a2['reviewer_id']}: raise SystemExit('Evaluation reviewer must be independent')
        scores={v:metrics(v,pilot['development'],labels) for v in VARIANTS}
        selected=min(VARIANTS,key=lambda v:(scores[v]['mae'],VARIANTS.index(v)))
        target=d/'frozen_model.json'
        if target.exists(): raise SystemExit('Frozen model exists: do not overwrite after seeing held-out judgments')
        target.write_text(json.dumps(dict(version='cses-reviewed-hybrid-v1',selected=selected,inputs_hash=inputs_hash,development_hash=digest(evaluation),scores=scores),indent=2)+'\n')
    else:
        frozen=read(d/'frozen_model.json')
        if frozen['inputs_hash']!=inputs_hash: raise SystemExit('Inputs changed after freeze')
        evaluation=read(d/'evaluation_held_out.json')
        if evaluation['reviewer_id'] in {a1['reviewer_id'],a2['reviewer_id']}: raise SystemExit('Evaluation reviewer must be independent')
        labels={x['id']:x for x in evaluation['reviews']};selected=frozen['selected'];result=metrics(selected,pilot['held_out'],labels);baseline=metrics('review_only',pilot['held_out'],labels)
        adjudicated=set(read(d/'adjudications.json').get('resolved_ids',[])) if (d/'adjudications.json').exists() else set()
        unresolved=[i for i in result['two_band_errors'] if i not in adjudicated]
        benefit=selected=='review_only' or result['mae']<baseline['mae']
        cohorts={x.get('release_cohort') for x in snapshot['problems'] if x['id'] in ids and x.get('release_cohort')}
        report=dict(selected=selected,held_out=result,baseline=baseline,statistics_benefit=selected!='review_only' and benefit,unresolved_two_band_errors=unresolved,cross_cohort_status='pending: no verified release cohorts' if len(cohorts)<2 else 'requires separate cohort evaluation',publication_ready=False,pilot_numerical_gate=result['within_one']>=.85 and not unresolved and benefit,note='Full 400-task independent review, cohort check, and adjudication are separate required publication gates.')
        (d/'pilot_report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
