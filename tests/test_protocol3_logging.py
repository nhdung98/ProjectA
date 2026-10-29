import contextlib
import io
from pathlib import Path
import tempfile
import unittest
import warnings

from src.p3.logging import logged_main, member_log_folder


class LoggingChecks(unittest.TestCase):
    def test_each_member_has_a_separate_log_folder(self):
        base = Path('logs')
        for member in range(1, 5):
            expected = base / f'member{member}'
            self.assertEqual(member_log_folder(base, ['run', '--member', str(member)]), expected)
            self.assertEqual(member_log_folder(base, [f'--member={member}']), expected)
        self.assertEqual(member_log_folder(base, ['check']), base)
        self.assertEqual(member_log_folder(base, ['--member', '../outside']), base)

    def test_terminal_warning_and_error_share_one_log(self):
        def command():
            print('training progress')
            warnings.warn('example warning', UserWarning)
            raise ValueError('example failure')

        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            output, errors = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
                with warnings.catch_warnings():
                    warnings.simplefilter('always')
                    with self.assertRaises(SystemExit) as caught:
                        logged_main(command, folder)
            self.assertEqual(caught.exception.code, 1)
            files = list(folder.glob('*.log'))
            self.assertEqual(len(files), 1)
            text = files[0].read_text(encoding='utf-8')
            for expected in ['training progress', 'example warning', 'example failure', 'Traceback']:
                self.assertIn(expected, text)
            self.assertIn('training progress', output.getvalue())
            self.assertIn('example warning', errors.getvalue())
