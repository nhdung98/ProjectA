"""Synthetic execution tests: real searches, independent audits, corruption and restart gates."""
from contextlib import contextmanager, ExitStack, redirect_stdout
import copy
import io
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
import warnings
import zipfile

import numpy as np
import pandas as pd

from src.experiments import common, svm, validate_svm
from src.experiments import workflow, workflow_checks as checks, workflow_run as runner
from src.experiments import workflow_report as reporting
from src.experiments.metrics import summarize


class WorkflowTests(unittest.TestCase):
    @contextmanager
    def fixture(self, both=False):
        """254 artificial patients, eight artificial features; never official evidence."""
        settings = copy.deepcopy(svm.load_settings())
        configurations = [dict(settings['configurations'][0], k=3),
                          dict(settings['configurations'][12], k=3)]
        settings['configurations'] = configurations
        settings['expected_features'] = 8
        settings['search']['C'] = [0.1, 1]
        labels = sum(([label] * count for label, count in settings['class_counts'].items()), [])
        data = pd.DataFrame({'Sample ID': [f'SYNTHETIC-S{i}' for i in range(254)],
                             'Patient ID': [f'SYNTHETIC-P{i}' for i in range(254)], 'subtype': labels})
        values = np.random.default_rng(42).uniform(0, 30, size=(254, 8))
        values[:, 0] = 0
        features = [f'gene__synthetic{i}' for i in range(8)]
        for i, feature in enumerate(features):
            data[feature] = values[:, i]
        with tempfile.TemporaryDirectory() as temporary, ExitStack() as stack:
            root = Path(temporary)
            shutil.copytree(common.ROOT / 'src', root / 'src', ignore=shutil.ignore_patterns('__pycache__'))
            (root / 'configs').mkdir()
            for name in ('data.yaml',):
                shutil.copy2(common.ROOT / 'configs' / name, root / 'configs' / name)
            for name in ('requirements.txt', 'requirements-experiments.txt', 'requirements-protocol2-lock.txt'):
                shutil.copy2(common.ROOT / name, root / name)
            (root / 'configs/svm.json').write_text(json.dumps(settings))
            (root / 'data/processed').mkdir(parents=True)
            data.to_csv(root / settings['dataset'], index=False, sep='\t')
            (root / 'results/splits').mkdir(parents=True)
            for module in (common, svm, validate_svm):
                stack.enter_context(patch.object(module, 'ROOT', root))
            stack.enter_context(patch.object(common, 'SPLIT_PATH', root / 'results/splits/outer.csv'))
            stack.enter_context(patch.object(common, 'SPLIT_MANIFEST', root / 'results/splits/outer_manifest.json'))
            stack.enter_context(patch.object(svm, 'INNER', root / 'results/splits/inner.csv'))
            stack.enter_context(patch.object(svm, 'INNER_MANIFEST', root / 'results/splits/inner_manifest.json'))
            stack.enter_context(patch.object(validate_svm, 'INNER', svm.INNER))
            outer = common.shared_splits(data, settings, create=True)
            inner = svm.shared_inner(data, outer, settings, create=True)
            env = checks.environment(settings)
            proof = dict(env, git_commit='synthetic-test-fixture-only', git_dirty=False,
                         source_sha256=settings['source_sha256'], dataset_sha256=common.sha256(root / settings['dataset']),
                         split_sha256=common.sha256(common.SPLIT_PATH), inner_split_sha256=common.sha256(svm.INNER),
                         code_sha256=checks.code_hashes(), workflow_version=checks.WORKFLOW_VERSION)
            context = (data, features, values, outer, inner, settings['packages'])
            preflight = dict(status='passed', data_checksums={}, split_checksums={}, synthetic_fixture=True)
            batch = root / 'results/protocol2/synthetic-tests'
            runner.create_batch(batch, configurations if both else configurations[:1], settings, proof, preflight)
            with redirect_stdout(io.StringIO()):
                yield batch, settings, context, proof

    def test_real_synthetic_searches_audit_reports_and_privacy_exports(self):
        with self.fixture(both=True) as (batch, settings, context, proof):
            runner.execute(batch, settings, context, proof)
            manifest, validated = reporting.validate_batch(batch, settings, context, proof)
            self.assertEqual(len(validated), 2)
            for identifier, relative in manifest['runs'].items():
                folder = batch / relative
                self.assertTrue(all((folder / name).is_file() for name in checks.REQUIRED))
                self.assertEqual(len(pd.read_csv(folder / 'predictions.csv')), 762)
                self.assertEqual(len(checks.read_json(folder / 'run_manifest.json')['folds']), 15)
                self.assertEqual(checks.read_json(folder / 'validation.json')['status'], 'passed')
            scores = reporting.report_batch(batch, settings, context, proof)
            self.assertEqual(len(scores), 2)
            self.assertEqual(len(pd.read_csv(batch / 'reports/confusion_matrices.csv')), 216)
            self.assertTrue(pd.read_csv(batch / 'comparison.csv').macro_f1_delta.isna().all())
            external = reporting.export_bundle(batch)
            with zipfile.ZipFile(external) as z:
                self.assertFalse(any('predictions.csv' in p or '.checkpoints' in p or p.startswith('runs/') for p in z.namelist()))
                self.assertFalse(any(b'SYNTHETIC-S' in z.read(p) or b'SYNTHETIC-P' in z.read(p) for p in z.namelist()))
            team = reporting.export_bundle(batch, audience='team')
            with zipfile.ZipFile(team) as z:
                self.assertEqual(sum(p.endswith('predictions.csv') for p in z.namelist()), 2)
                self.assertFalse(any('data/raw/' in p or 'sarc_merged' in p for p in z.namelist()))
            with self.assertRaisesRegex(ValueError, 'already exists'):
                reporting.export_bundle(batch)

    def test_resume_reuses_only_committed_verified_folds(self):
        with self.fixture() as (batch, settings, context, proof):
            original = svm.fit_search
            count = 0
            def interrupted(*args, **kwargs):
                nonlocal count
                count += 1
                if count == 2:
                    raise KeyboardInterrupt()
                return original(*args, **kwargs)
            with patch.object(svm, 'fit_search', side_effect=interrupted):
                with self.assertRaises(KeyboardInterrupt):
                    runner.execute(batch, settings, context, proof)
            manifest = checks.read_json(batch / 'experiment_manifest.json')
            folder = batch / next(iter(manifest['runs'].values()))
            checkpoint = folder / '.checkpoints/r1-f1.json'
            before = checkpoint.read_bytes()
            self.assertEqual(runner.status(batch)['configurations'][0]['committed_folds'], 1)
            with patch.object(svm, 'fit_search', wraps=original) as search:
                runner.execute(batch, settings, context, proof, resume=True)
                self.assertEqual(search.call_count, 14)
            self.assertEqual(checkpoint.read_bytes(), before)
            reporting.validate_batch(batch, settings, context, proof)
            with patch.object(svm, 'fit_search', side_effect=AssertionError('No repeat fitting')):
                runner.execute(batch, settings, context, proof, resume=True)

    def test_corrupt_checkpoint_rejected_before_any_resume_fit(self):
        with self.fixture() as (batch, settings, context, proof):
            original = svm.fit_search
            calls = 0
            def interrupted(*args):
                nonlocal calls
                calls += 1
                if calls > 1:
                    raise KeyboardInterrupt()
                return original(*args)
            with patch.object(svm, 'fit_search', side_effect=interrupted), self.assertRaises(KeyboardInterrupt):
                runner.execute(batch, settings, context, proof)
            manifest = checks.read_json(batch / 'experiment_manifest.json')
            folder = batch / next(iter(manifest['runs'].values()))
            path = folder / '.checkpoints/r1-f1.json'
            envelope = checks.read_json(path)
            envelope['block']['predictions'][0]['predicted_subtype'] = 'NOT_A_LABEL'
            path.write_text(json.dumps(envelope))
            with patch.object(svm, 'fit_search', side_effect=AssertionError('Must not fit')), self.assertRaisesRegex(ValueError, 'checksum'):
                runner.execute(batch, settings, context, proof, resume=True)
            envelope['sha256'] = hashlib.sha256(json.dumps(envelope['block'], sort_keys=True, allow_nan=False).encode()).hexdigest()
            path.write_text(json.dumps(envelope))
            with patch.object(svm, 'fit_search', side_effect=AssertionError('Must not fit')), self.assertRaisesRegex(ValueError, 'Unknown prediction'):
                runner.execute(batch, settings, context, proof, resume=True)

    def test_artifact_corruption_missing_files_and_duplicate_runs_rejected(self):
        with self.fixture() as (batch, settings, context, proof):
            runner.execute(batch, settings, context, proof)
            manifest = checks.read_json(batch / 'experiment_manifest.json')
            folder = batch / next(iter(manifest['runs'].values()))
            for name in checks.REQUIRED:
                path = folder / name
                before = path.read_bytes()
                path.unlink()
                with self.subTest(missing=name), self.assertRaisesRegex(ValueError, 'Missing required'):
                    reporting.validate_batch(batch, settings, context, proof)
                path.write_bytes(before)
            for name in ['predictions.csv', 'metrics.json', 'feature_details.json', 'search_results.json', 'warnings.log', 'config.json']:
                path = folder / name; before = path.read_bytes(); path.write_bytes(before + b' ')
                with self.subTest(corruption=name), self.assertRaisesRegex(ValueError, 'checksum'):
                    reporting.validate_batch(batch, settings, context, proof)
                path.write_bytes(before)
            # Recomputed hashes do not excuse inconsistent evidence.
            path = folder / 'predictions.csv'; before = path.read_bytes()
            run_path = folder / 'run_manifest.json'; manifest_bytes = run_path.read_bytes()
            predictions = pd.read_csv(path)
            current = predictions.loc[0, 'predicted_subtype']
            predictions.loc[0, 'predicted_subtype'] = next(x for x in settings['labels'] if x != current)
            predictions.to_csv(path, index=False)
            run = checks.read_json(run_path); run['artifact_sha256']['predictions.csv'] = common.sha256(path)
            run_path.write_text(json.dumps(run))
            with self.assertRaises(AssertionError):
                reporting.validate_batch(batch, settings, context, proof)
            path.write_bytes(before); run_path.write_bytes(manifest_bytes)
            source = common.ROOT / 'src/experiments/pipeline.py'; source_bytes = source.read_bytes()
            source.write_bytes(source_bytes + b'\n# synthetic corruption fixture\n')
            with self.assertRaisesRegex(ValueError, 'Source code'):
                reporting.validate_batch(batch, settings, context, proof)
            source.write_bytes(source_bytes)
            extra = folder.parent / 'unregistered-run'
            shutil.copytree(folder, extra)
            with self.assertRaisesRegex(ValueError, 'duplicate run'):
                reporting.validate_batch(batch, settings, context, proof)

    def test_warning_persists_and_blocks_resume(self):
        with self.fixture() as (batch, settings, context, proof):
            original = svm.fit_search
            def warned(*args):
                result = original(*args)
                warnings.warn('Synthetic warning to exercise acceptance gate', RuntimeWarning)
                return result
            with patch.object(svm, 'fit_search', side_effect=warned), self.assertRaisesRegex(ValueError, 'warnings'):
                runner.execute(batch, settings, context, proof)
            with self.assertRaisesRegex(ValueError, 'Warning-bearing'):
                runner.execute(batch, settings, context, proof, resume=True)
            folder = batch / next(iter(checks.read_json(batch / 'experiment_manifest.json')['runs'].values()))
            self.assertIn('Synthetic warning', (folder / 'warnings.log').read_text())
            self.assertEqual(checks.read_json(folder / 'validation.json')['status'], 'incomplete')

    def test_release_changes_incomplete_batches_and_lock_rejected(self):
        with self.fixture() as (batch, settings, context, proof):
            changed = dict(proof, git_commit='another-commit')
            with self.assertRaisesRegex(ValueError, 'git_commit'):
                runner.execute(batch, settings, context, changed)
            with self.assertRaisesRegex(ValueError, 'Incomplete/smoke'):
                reporting.validate_batch(batch, settings, context, proof)
            with runner.writer_lock(batch):
                with self.assertRaisesRegex(ValueError, 'Writer lock exists'):
                    with runner.writer_lock(batch):
                        pass
                with self.assertRaisesRegex(ValueError, 'On Windows' if os.name == 'nt' else 'still alive'):
                    runner.unlock(batch, os.getpid())

    def test_preflight_failure_is_reported_without_training_or_preparation(self):
        settings = svm.load_settings()
        settings['dataset'] = 'data/processed/INTENTIONALLY_MISSING_TEST.tsv'
        with patch.object(svm, 'fit_search', side_effect=AssertionError('No fitting')):
            report, context = checks.preflight(settings)
        self.assertEqual(report['status'], 'failed')
        self.assertIsNone(context)
        self.assertEqual(report['checks']['canonical_dataset_hash'], 'failed')

    def test_selection_preserves_exact_protocol_grid(self):
        from argparse import Namespace
        settings = svm.load_settings()
        self.assertEqual(len(workflow.selection(Namespace(configuration=None, branch=None), settings)), 24)
        for branch in workflow.BRANCHES:
            self.assertEqual(len(workflow.selection(Namespace(configuration=None, branch=branch), settings)), 6)
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            workflow.selection(Namespace(configuration=['x', 'x']), settings)

    def test_resume_rejects_traversal_without_touching_target(self):
        with self.fixture() as (batch, settings, context, proof):
            path = batch / 'experiment_manifest.json'
            manifest = checks.read_json(path)
            manifest['runs'][manifest['configurations'][0]] = '../../../archive/week01/submissions/member3'
            path.write_text(json.dumps(manifest))
            with patch.object(svm, 'fit_search', side_effect=AssertionError('Must not fit')), self.assertRaisesRegex(ValueError, 'escapes'):
                runner.execute(batch, settings, context, proof, resume=True)

    def test_full_24_report_shape_with_mock_validated_fixtures_only(self):
        """Test rendering, not 24 model executions; mock data never leave the temporary directory."""
        settings = copy.deepcopy(svm.load_settings())
        with tempfile.TemporaryDirectory() as temporary:
            batch = Path(temporary)
            predictions = pd.DataFrame({'Sample ID': [f'ARTIFICIAL-{i}' for i in range(12)],
                                         'true_subtype': settings['labels'] * 2,
                                         'predicted_subtype': settings['labels'] * 2})
            repeated = pd.concat([predictions.assign(repeat=r) for r in (1, 2, 3)], ignore_index=True)
            metrics = summarize(repeated, settings['labels'], predictions['Sample ID'], 3)
            manifest = dict(status='complete', mode='official', runs={})
            validated = {}
            for config in settings['configurations']:
                identifier = config['id']; relative = f'runs/{identifier}/ARTIFICIAL-REPORT-FIXTURE'
                folder = batch / relative; folder.mkdir(parents=True)
                for name in checks.REQUIRED:
                    (folder / name).write_text('{}')
                (folder / 'run_manifest.json').write_text(json.dumps(dict(run_id=identifier, git_commit='ARTIFICIAL-FIXTURE',
                    folds=[dict(runtime_seconds=1)])))
                manifest['runs'][identifier] = relative
                validated[identifier] = (repeated, metrics, dict(status='mock_fixture_only'))
            (batch / 'experiment_manifest.json').write_text(json.dumps(manifest))
            for name in ('environment.txt', 'data_checksums.json', 'split_checksums.json', 'preflight_report.json'):
                (batch / name).write_text('{}')
            with patch.object(reporting, 'validate_batch', return_value=(manifest, validated)):
                reporting.report_batch(batch, settings, None, None)
            self.assertEqual(len(pd.read_csv(batch / 'summary.csv')), 24)
            self.assertEqual(len(pd.read_csv(batch / 'comparison.csv')), 24)
            self.assertEqual(len(pd.read_csv(batch / 'reports/subtype_analysis.csv')), 432)
            self.assertEqual(len(pd.read_csv(batch / 'reports/confusion_matrices.csv')), 2592)
            self.assertTrue(pd.read_csv(batch / 'comparison.csv').macro_f1_delta.eq(0).all())

    def test_finalization_crash_boundaries_resume_without_fitting(self):
        class PowerLoss(BaseException):
            pass
        with self.fixture() as (batch, settings, context, proof), tempfile.TemporaryDirectory() as tmp:
            runner.execute(batch, settings, context, proof)
            relative = next(iter(checks.read_json(batch / 'experiment_manifest.json')['runs'].values()))
            folder = batch / relative
            original_run = checks.read_json(folder / 'run_manifest.json')
            original_id = original_run['run_id']
            checkpoint_hashes = {p.name: common.sha256(p) for p in (folder / '.checkpoints').glob('*.json')}
            original_run.update(status='running', validation_status='pending')
            original_run.pop('artifact_sha256')
            runner.atomic_json(folder / 'run_manifest.json', original_run)
            snapshot = Path(tmp) / 'snapshot'
            shutil.copytree(batch, snapshot)
            original_write = runner.atomic_bytes
            events = []
            def track(path, payload):
                if Path(path).parent == folder:
                    events.append(Path(path).name)
                original_write(path, payload)
            with patch.object(svm, 'fit_search', side_effect=AssertionError('Must not refit')), patch.object(runner, 'atomic_bytes', side_effect=track):
                runner.execute(batch, settings, context, proof, resume=True)
            self.assertIn('validation.json', events)
            self.assertIn('run_manifest.json', events)
            for index in range(len(events)):
                for after in (False, True):
                    with self.subTest(write=index, filename=events[index], after=after):
                        shutil.rmtree(batch)
                        shutil.copytree(snapshot, batch)
                        counter = 0
                        def crash(path, payload):
                            nonlocal counter
                            selected = Path(path).parent == folder
                            hit = selected and counter == index
                            if selected:
                                counter += 1
                            if hit and not after:
                                raise PowerLoss()
                            original_write(path, payload)
                            if hit:
                                raise PowerLoss()
                        with patch.object(svm, 'fit_search', side_effect=AssertionError('Must not refit')) as fit:
                            with patch.object(runner, 'atomic_bytes', side_effect=crash), self.assertRaises(PowerLoss):
                                runner.execute(batch, settings, context, proof, resume=True)
                            persisted = checks.read_json(folder / 'run_manifest.json')
                            if persisted['status'] == 'complete':
                                checks.validate_run(folder, settings, context[0], context[3], proof)
                            runner.execute(batch, settings, context, proof, resume=True)
                            fit.assert_not_called()
                        reporting.validate_batch(batch, settings, context, proof)
                        self.assertEqual(checks.read_json(folder / 'run_manifest.json')['run_id'], original_id)
                        self.assertEqual(checkpoint_hashes, {p.name: common.sha256(p) for p in (folder / '.checkpoints').glob('*.json')})
                        sealed = {name: (folder / name).read_bytes() for name in checks.REQUIRED}
                        with patch.object(svm, 'fit_search', side_effect=AssertionError('Must not refit')):
                            runner.execute(batch, settings, context, proof, resume=True)
                        self.assertEqual(sealed, {name: (folder / name).read_bytes() for name in checks.REQUIRED})
            self.assertEqual(len(events), 15)  # 30 before/after abrupt-interruption cases.

    def test_finalizing_missing_checkpoint_is_not_refitted(self):
        with self.fixture() as (batch, settings, context, proof):
            runner.execute(batch, settings, context, proof)
            folder = batch / next(iter(checks.read_json(batch / 'experiment_manifest.json')['runs'].values()))
            manifest = checks.read_json(folder / 'run_manifest.json')
            manifest['status'] = 'finalizing'
            runner.atomic_json(folder / 'run_manifest.json', manifest)
            (folder / '.checkpoints/r1-f1.json').unlink()
            with patch.object(svm, 'fit_search', side_effect=AssertionError('Must not refit')), self.assertRaisesRegex(ValueError, 'missing committed'):
                runner.execute(batch, settings, context, proof, resume=True)

    def test_exact_zip_checksums_tampering_and_private_paths(self):
        with self.fixture() as (batch, settings, context, proof):
            # Private metadata must survive internally and disappear only in external copies.
            proof['python_executable'] = r'C:\Users\PRIVATE_OPERATOR\ProjectA\.venv\Scripts\python.exe'
            manifest = checks.read_json(batch / 'experiment_manifest.json')
            manifest['provenance'] = proof
            runner.atomic_json(batch / 'experiment_manifest.json', manifest)
            report = checks.read_json(batch / 'preflight_report.json')
            report['environment'] = dict(python_executable='/Users/PRIVATE_OPERATOR/project/.venv/bin/python')
            runner.atomic_json(batch / 'preflight_report.json', report)
            runner.execute(batch, settings, context, proof)
            reporting.report_batch(batch, settings, context, proof)
            before = {p.relative_to(batch).as_posix(): p.read_bytes() for p in batch.rglob('*') if p.is_file()}
            for audience in ('external', 'team'):
                path = reporting.export_bundle(batch, audience)
                self.assertEqual(reporting.verify_bundle(path)['status'], 'passed')
                with patch.object(svm, 'load_settings', side_effect=AssertionError('ZIP verification must not need local experiment settings')):
                    workflow.main(['verify-export', '--zip', str(path)])
                with zipfile.ZipFile(path) as archive:
                    entries = {n: archive.read(n) for n in archive.namelist()}
                inventory = json.loads(entries['EXPORT_CHECKSUMS.json'])
                self.assertEqual(set(inventory['entry_sha256']), set(entries) - {'EXPORT_CHECKSUMS.json'})
                for name, digest in inventory['entry_sha256'].items():
                    self.assertEqual(hashlib.sha256(entries[name]).hexdigest(), digest)
                if audience == 'external':
                    for payload in entries.values():
                        for forbidden in (b'PRIVATE_OPERATOR', b'/Users/', b'C:\\Users', b'SYNTHETIC-S', b'SYNTHETIC-P'):
                            self.assertNotIn(forbidden, payload)
                    self.assertNotEqual(inventory['source_artifact_sha256']['experiment_manifest.json'], inventory['entry_sha256']['experiment_manifest.json'])
                else:
                    self.assertIn(b'PRIVATE_OPERATOR', entries['experiment_manifest.json'])
                    for name in entries:
                        if name.startswith('runs/'):
                            self.assertEqual(entries[name], (batch / name).read_bytes())
                self.assertFalse(any(n.startswith('data/') for n in entries))
                for corruption in ('modified', 'missing', 'extra', 'duplicate', 'invalid_zip'):
                    broken = batch / f'{audience}-{corruption}.zip'
                    if corruption == 'invalid_zip':
                        broken.write_bytes(b'not a zip')
                    else:
                        with zipfile.ZipFile(broken, 'w') as archive:
                            for name, payload in entries.items():
                                if corruption == 'missing' and name == 'summary.csv':
                                    continue
                                archive.writestr(name, payload + b'changed' if corruption == 'modified' and name == 'summary.csv' else payload)
                            if corruption == 'extra':
                                archive.writestr('extra.txt', b'extra')
                            if corruption == 'duplicate':
                                with warnings.catch_warnings():
                                    warnings.simplefilter('ignore')
                                    archive.writestr('summary.csv', entries['summary.csv'])
                    with self.subTest(audience=audience, corruption=corruption), self.assertRaises(ValueError):
                        reporting.verify_bundle(broken)
            for name, payload in before.items():
                self.assertEqual((batch / name).read_bytes(), payload)

    def test_publication_copy_fallback_is_atomic_and_exclusive(self):
        import errno
        with tempfile.TemporaryDirectory(prefix='space and unicode-ỹ-') as tmp:
            source, target = Path(tmp) / 'source', Path(tmp) / 'target'
            payload = b'canonical\r\nbytes\x00'
            source.write_bytes(payload)
            with patch.object(runner.os, 'link', side_effect=OSError(errno.ENOTSUP, 'no links')):
                runner.publish_new(source, target)
                self.assertEqual(target.read_bytes(), payload)
                with self.assertRaises(FileExistsError):
                    runner.publish_new(source, target)
                target.unlink()
                with patch.object(runner.os, 'rename', side_effect=PermissionError('Windows sharing violation')):
                    with self.assertRaises(PermissionError):
                        runner.publish_new(source, target)
                self.assertFalse(target.exists())
                self.assertEqual(sorted(p.name for p in Path(tmp).iterdir()), ['source'])
                runner.publish_new(source, target)
            self.assertEqual(target.read_bytes(), payload)

    def test_windows_identity_is_new_batch_not_cross_platform_resume(self):
        with self.fixture() as (_, settings, _, proof):
            windows = dict(proof, operating_system='Windows-11', machine='AMD64', python='3.12 Windows build')
            checks.same_identity(windows, dict(windows))
            with self.assertRaisesRegex(ValueError, 'provenance mismatch'):
                checks.same_identity(proof, windows)
            for field in ('git_commit', 'dataset_sha256', 'split_sha256', 'inner_split_sha256', 'code_sha256', 'packages'):
                changed = dict(windows, **{field: 'changed'})
                with self.subTest(field=field), self.assertRaises(ValueError):
                    checks.same_identity(windows, changed)


if __name__ == '__main__':
    unittest.main()
