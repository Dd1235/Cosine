import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from external_judges import metadata, kattis_body


class ExternalAdapters(unittest.TestCase):
    def test_codechef_components_override_editor_template(self):
        data = {'problem_name': 'Actual problem', 'body': 'editor template',
                'problemComponents': {'statement': 'Find the sum of the array. ' * 8,
                                      'inputFormat': 'N and N integers',
                                      'outputFormat': 'The sum',
                                      'constraints': 'N <= 100000'}}
        with patch('annotate_problem_urls.request_json', return_value=data):
            p = metadata('https://www.codechef.com/problems/TEST', 'Verified collection')
        self.assertNotIn('editor template', p['source_text'])
        self.assertIn('100000', p['source_text'])
        self.assertIsNone(p['difficulty'])

    def test_kattis_nested_body_excludes_user_metadata(self):
        page = '<div class="problembody"><p>Statement</p><div>Input<div>nested</div></div>Output</div><div>user email</div>'
        self.assertEqual(kattis_body(page), '<p>Statement</p><div>Input<div>nested</div></div>Output')

    def test_truncated_and_gated_pages_fail(self):
        with self.assertRaises(ValueError):
            kattis_body('<div class="problembody">incomplete')
        with patch('annotate_problem_urls.request_json', return_value={'problem_name': 'Gated'}):
            with self.assertRaises(ValueError):
                metadata('https://www.codechef.com/problems/TEST', 'Collection')

    def test_host_is_exact(self):
        with self.assertRaises(ValueError):
            metadata('https://codechef.com.example.org/problems/TEST', 'Collection')


if __name__ == '__main__':
    unittest.main()
