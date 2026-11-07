import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from zipfile import ZipFile

from src.p3.submission import member_submission


class SubmissionChecks(unittest.TestCase):
    def test_packages_current_results_without_modifying_them(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            pipeline = root / 'P06'
            pipeline.mkdir()
            manifest = '{"status": "complete"}'
            (pipeline / 'manifest.json').write_text(manifest, encoding='utf-8')
            (pipeline / 'search_results.csv').write_text('inner_1\n0.8\n', encoding='utf-8')
            with contextlib.redirect_stdout(io.StringIO()):
                with member_submission(root / 'out', 'A', 2, ['P06']) as outputs:
                    outputs.append(pipeline)
            files = list((root / 'out').glob('*.zip'))
            self.assertEqual(len(files), 1)
            with ZipFile(files[0]) as archive:
                summary = json.loads(archive.read('submission_summary.json'))
                self.assertEqual(summary['status'], 'complete')
                self.assertEqual(archive.read('P06/manifest.json').decode(), manifest)
                self.assertIn('P06/search_results.csv', archive.namelist())
            self.assertEqual((pipeline / 'manifest.json').read_text(encoding='utf-8'), manifest)

    def test_failure_still_produces_diagnostic_archive_and_raises(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaisesRegex(ValueError, 'bad environment'):
                    with member_submission(root, 'A', 2, ['P06']):
                        raise ValueError('bad environment')
            with ZipFile(next(root.glob('*.zip'))) as archive:
                summary = json.loads(archive.read('submission_summary.json'))
                self.assertEqual(summary['status'], 'failed')
                self.assertIn('bad environment', summary['error'])
                self.assertEqual(summary['pipelines'], [])
