"""The labels-pending tier: what it writes, what it never touches."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import publish_pending as pp  # noqa: E402

LONG = ("Bob has created N convex polygons on a plane, numbered from 1 to N. "
        "He wants Alice to pick a maximum subset such that no two polygons in the subset touch. "
        "Alice thinks this is easy, but the polygons are huge and she has only a second. "
        "Help her find the size of the largest such subset. ") * 3

def staged(**over):
    base = {
        "id": "codechef-polcon", "platform": "codechef", "title": "Polygon Containment",
        "slug": "polcon", "source_url": "https://www.codechef.com/problems/POLCON",
        "source_topic": "ICPC / Amritapuri Regional 2019", "source_text": LONG,
        "source_tags": [], "judge_tags": ["advanced-algorithms", "flow-networks", "Computational Geometry", "flow-networks"],
        "contest_source": {"host": "codechef.com", "name": "AM19MOS", "position": 2, "problem_code": "POLCON",
                           "replay_solves": {"successful": 8, "total": 30, "accuracy": 26.67, "replay_only": True}},
    }
    base.update(over)
    return base


class Lead(unittest.TestCase):
    def test_at_least_two_sentences_under_the_limit(self):
        lead = pp.extractive_lead(LONG)
        self.assertLessEqual(len(lead), 600)
        self.assertGreaterEqual(lead.count(". "), 1, "two sentences means one boundary inside")
        self.assertTrue(lead.endswith("."), "cut at a sentence boundary, not mid-word")

    def test_math_delimiters_are_dropped_and_whitespace_collapsed(self):
        self.assertEqual(pp.extractive_lead("Given $N$ items.\n\nPick   $K$ of them."), "Given N items. Pick K of them.")

    def test_one_giant_sentence_is_cut_at_a_word(self):
        lead = pp.extractive_lead("word " * 300)
        self.assertLessEqual(len(lead), 600)
        self.assertTrue(lead.endswith("…"))


class Record(unittest.TestCase):
    def test_shape(self):
        r = pp.build_pending_record(staged(), now=123)
        self.assertEqual(r["patterns"], [])
        self.assertEqual(r["review_status"], "labels-pending")
        self.assertEqual(r["annotation"]["model"], "codechef-judge-tags")
        self.assertEqual(r["annotation"]["generated_at_unix"], 123)
        self.assertIsNone(r["annotation"]["reviewed_by"])
        self.assertEqual(r["annotation"]["pattern_confidence"], {})
        self.assertIsNone(r["difficulty"])
        self.assertEqual(r["tags"], ["advanced-algorithms", "flow-networks"],
                         "judge tags are deduplicated and only slug-shaped ones survive")
        self.assertEqual(r["contest_source"]["replay_solves"]["replay_only"], True)
        self.assertIn("PRACTICE/problems/POLCON", r["annotation"]["evidence"])

    def test_eligibility(self):
        self.assertEqual(pp.eligible(staged())[0], True)
        self.assertEqual(pp.eligible(staged(contest_source={"host": "open.kattis.com"}))[0], False)
        self.assertEqual(pp.eligible(staged(source_text="short"))[0], False)
        self.assertEqual(pp.eligible(staged(judge_tags=["Not A Slug"]))[0], False)


class Run(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        (self.tmp / "data" / "analysis" / "external-staging").mkdir(parents=True)
        (self.tmp / "data" / "problemset_llm" / "codechef").mkdir(parents=True)
        self.stage(staged())
        self.stage(staged(id="codechef-other", slug="other", contest_source={"host": "codechef.com", "name": "KOL18ROL", "position": 1, "problem_code": "OTHER"}))

    def stage(self, rec):
        (self.tmp / "data" / "analysis" / "external-staging" / f"{rec['id']}.json").write_text(json.dumps(rec))

    def test_dry_run_writes_nothing(self):
        st = pp.run(write=False, contest=None, root=self.tmp)
        self.assertEqual(st["written"], 2)
        self.assertEqual(list((self.tmp / "data" / "problemset_llm" / "codechef").iterdir()), [])

    def test_write_then_never_overwrite(self):
        pp.run(write=True, contest=None, root=self.tmp)
        out = self.tmp / "data" / "problemset_llm" / "codechef" / "codechef-polcon.json"
        self.assertTrue(out.exists())
        # Simulate tier two having reviewed it: labels present, status gone.
        reviewed = json.loads(out.read_text()); reviewed["patterns"] = ["max-flow"]; reviewed.pop("review_status")
        out.write_text(json.dumps(reviewed))
        st = pp.run(write=True, contest=None, root=self.tmp)
        self.assertEqual(st["exists"], 2)
        self.assertEqual(json.loads(out.read_text())["patterns"], ["max-flow"], "a reviewed record is never downgraded")

    def test_contest_filter(self):
        st = pp.run(write=False, contest="KOL18ROL", root=self.tmp)
        self.assertEqual(st["written"], 1)


if __name__ == "__main__":
    unittest.main()
