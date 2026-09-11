import importlib.util
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location('cses_experiment',Path(__file__).resolve().parents[1]/'scripts/evaluate_cses_difficulty.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class CsesExperimentTest(unittest.TestCase):
    def snapshot(self,verified=False,cohort=None):
        s={'problems':[{'id':str(i),'public_count_first':i+1,'public_count_second':100+i*10,'release_cohort':cohort} for i in range(12)]}
        if verified:s['verified_count_semantics']='distinct_solvers_over_distinct_attempting_users'
        return s
    def reviews(self):return {str(i):({'band':3},{'band':4}) for i in range(12)}
    def test_unverified_counts_never_adjust(self):
        for variant in m.VARIANTS:
            p=m.predictions(self.snapshot(),self.reviews(),variant)
            self.assertTrue(all(r['adjustment']==0 for r in p.values()))
    def test_unknown_cohort_disables_volume(self):
        for variant in ['volume','combined']:
            p=m.predictions(self.snapshot(True),self.reviews(),variant)
            self.assertTrue(all(r['adjustment']==0 for r in p.values()))
    def test_verified_adjustments_are_bounded(self):
        for variant in m.VARIANTS:
            p=m.predictions(self.snapshot(True,'verified-cohort'),self.reviews(),variant)
            self.assertTrue(all(abs(r['adjustment'])<=.5 and 1<=r['band']<=5 for r in p.values()))
    def test_newness_only_attenuates(self):
        s=self.snapshot(True,'verified-cohort')
        old=m.predictions(s,self.reviews(),'completion')
        for x in s['problems']:x['age_days']=0
        recent=m.predictions(s,self.reviews(),'completion')
        self.assertTrue(any(r['adjustment']!=0 for r in old.values()))
        self.assertTrue(all(r['adjustment']==0 for r in recent.values()))
    def test_snapshot_and_review_coverage(self):
        root=Path(__file__).resolve().parents[1]/'data/cses'
        snapshot=m.read(root/'public_counts.json');reviews=m.read(root/'reviews_a.json')
        self.assertEqual(400,len(snapshot['problems']))
        self.assertEqual({p['id'] for p in snapshot['problems']},{r['id'] for r in reviews['reviews']})
        for r in reviews['reviews']:
            statement=m.read(root/'statements'/(r['id']+'.json'))
            self.assertEqual(r['statement_sha256'],statement['statement_sha256'])
            self.assertTrue(r['solution_rationale'] and r['complexity'])
if __name__=='__main__':unittest.main()
