import importlib.util
import json
import tempfile
from pathlib import Path
import unittest

def load(name,relative):
    spec=importlib.util.spec_from_file_location(name,Path(__file__).resolve().parents[1]/relative)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

m=load('cses_experiment','scripts/evaluate_cses_difficulty.py')
collect=load('cses_collect','scripts/collect_cses_evidence.py')

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

class PublishedScopeTest(unittest.TestCase):
    def test_published_bands_say_what_they_are(self):
        root=Path(__file__).resolve().parents[1]/'data/cses'
        bands=m.read(root/'published_bands.json');status=m.read(root/'research_status.json')
        self.assertEqual('published-estimate-v1',bands['scope'])
        self.assertTrue(bands['statistical_model'].startswith('disabled'))
        self.assertTrue(status['publication_ready'])
        self.assertTrue(status['production_changes'])
        self.assertIn('statistical adjustment disabled',status['scope'])
        self.assertTrue(status['statistics_arm'].startswith('disabled'))
        self.assertEqual(400,len(bands['problems']))
        self.assertTrue(all(p['confidence'] in {'low','medium','high'} for p in bands['problems']))

class CountSemanticsGateTest(unittest.TestCase):
    # The public counts stay unlabelled until a logged-in human checks them. The
    # only way that claim can appear in the snapshot is through a check file, so
    # the refusal is the feature worth testing.
    VALUE='distinct_solvers_over_distinct_attempting_users'
    def test_refuses_without_check_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp);(out/'public_counts.json').write_text(json.dumps({'problems':[]}))
            missing=Path(tmp)/'count_semantics_check.json'
            original=collect.CHECK;collect.CHECK=missing
            try:
                with self.assertRaises(SystemExit) as raised:collect.set_semantics(self.VALUE,out)
            finally:collect.CHECK=original
            self.assertIn('does not exist',str(raised.exception))
            self.assertNotIn('verified_count_semantics',json.loads((out/'public_counts.json').read_text()))
    def test_refuses_when_the_check_concluded_otherwise(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp);(out/'public_counts.json').write_text(json.dumps({'problems':[]}))
            check=out/'count_semantics_check.json'
            check.write_text(json.dumps({'conclusion':'public counters are not solver/attempt counts'}))
            original=collect.CHECK;collect.CHECK=check
            try:
                with self.assertRaises(SystemExit) as raised:collect.set_semantics(self.VALUE,out)
            finally:collect.CHECK=original
            self.assertIn('concludes',str(raised.exception))
            self.assertNotIn('verified_count_semantics',json.loads((out/'public_counts.json').read_text()))
    def test_no_check_file_is_committed(self):
        self.assertFalse((Path(__file__).resolve().parents[1]/'data/cses/count_semantics_check.json').exists())
        self.assertNotIn('verified_count_semantics',m.read(Path(__file__).resolve().parents[1]/'data/cses/public_counts.json'))

if __name__=='__main__':unittest.main()
