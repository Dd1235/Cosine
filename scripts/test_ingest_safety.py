"""Offline regressions for shared cache safety and read-only discovery."""
import json
import multiprocessing
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import cache_io
import ingest_contest as ingest
from annotate_problem_urls import codeforces_problem_key


def merge_worker(path, key):
    cache_io.merge_json_map(Path(path), {key: {'statement': key}})


class IngestionSafetyTests(unittest.TestCase):
    def test_parallel_merges_keep_every_entry(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'cache.json'
            path.write_text('{"original": {"statement": "original"}}')
            workers = [multiprocessing.Process(target=merge_worker, args=(str(path), str(i))) for i in range(6)]
            for worker in workers:
                worker.start()
            for worker in workers:
                worker.join(10)
                self.assertEqual(worker.exitcode, 0)
            self.assertEqual(set(json.loads(path.read_text())), {'original', *map(str, range(6))})

    def test_bad_cache_is_not_replaced(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'cache.json'
            path.write_text('{broken')
            with self.assertRaises(json.JSONDecodeError):
                cache_io.merge_json_map(path, {'new': {}})
            self.assertEqual(path.read_text(), '{broken')

    def test_expired_index_dry_run_does_not_write(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'index.json'
            path.write_text('{"fetched_at":"2000-01-01T00:00:00+00:00","keys":{}}')
            before = path.read_bytes()
            with patch.object(ingest, 'HF_INDEX', path), patch.object(ingest, 'request_json', return_value={'num_rows_total': 0}):
                self.assertEqual(ingest.hf_lookup({'codeforces-1-a'}, write=False), {})
            self.assertEqual(path.read_bytes(), before)
            self.assertEqual(len(list(Path(directory).iterdir())), 1)

    def test_staging_dry_run_reads_cached_gym_without_writes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            cache = root / 'statements.json'
            key = 'codeforces-106179-a'
            entry = {'id': key, 'statement': 'a' * 100, 'title': 'A', 'url': 'https://codeforces.com/gym/106179/problem/A'}
            cache.write_text(json.dumps({key: entry}))
            with patch.object(ingest, 'CF_STATEMENTS', cache), patch.object(ingest, 'CORPUS', root / 'corpus'), patch.object(ingest, 'hf_lookup', return_value={}) as lookup, patch.object(ingest, 'merge_statements') as merge, patch.object(ingest, 'append_seed_block') as append:
                result = ingest.stage_codeforces([{'index': 'A'}], 106179, 'Gym', dry_run=True)
                self.assertEqual(result['staged'], 1)
                lookup.assert_called_once_with(set(), write=False)
                merge.assert_not_called()
                append.assert_not_called()
            self.assertEqual(len(list(root.iterdir())), 1)

    def test_gym_identity_and_links(self):
        self.assertEqual(ingest.parse_contest_url('https://codeforces.com/gym/106179'), ('codeforces', 106179))
        self.assertEqual(codeforces_problem_key('https://codeforces.com/gym/106179/problem/A'), (106179, 'A'))
        self.assertEqual(codeforces_problem_key('https://codeforces.com/contest/2259/problem/B'), (2259, 'B'))
        _, entry = ingest.row_to_entry({'contest_id': 106179, 'index': 'A', 'description': 'x' * 100})
        self.assertEqual(entry['url'], 'https://codeforces.com/gym/106179/problem/A')


if __name__ == '__main__':
    unittest.main()
