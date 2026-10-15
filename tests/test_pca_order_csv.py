"""Single-CSV validation, interrupted runs and overwrite protection."""
import contextlib
import copy
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import numpy as np
import pandas as pd
from src.experiments import pca_order_csv as experiment
from src.experiments.pipeline import build_pipeline
from src.experiments.svm import generate_inner
from src.experiments.validation import generate_splits


class PCAOrderTests(unittest.TestCase):
    def setUp(self):
        self.s = experiment.settings()
        self.s['labels'] = ['a', 'b', 'c']
        self.s['search'] = dict(self.s['search'], C=[1], gamma=['scale'])
        self.s['configurations'] = [dict(c, k=c['k'] // 50 + 1) for c in self.s['configurations']]
        self.data = pd.DataFrame({'Sample ID': [f's{i}' for i in range(60)], 'Patient ID': [f'p{i}' for i in range(60)], 'subtype': ['a', 'b', 'c'] * 20})
        rng = np.random.default_rng(42)
        for i in range(8): self.data[f'gene__{i}'] = rng.uniform(0, 30, 60)
        self.outer = generate_splits(self.data, self.s['validation'])
        self.proof = {key: key + '-test' for key in experiment.IDENTITY}
        self.temp = tempfile.TemporaryDirectory(); self.root = Path(self.temp.name)
        self.addCleanup(self.temp.cleanup)

    def fixture(self, member):
        records = []
        for c in self.s['configurations']:
            if c['member'] != member: continue
            for repeat, fold, sample, patient, label in self.outer.itertuples(index=False, name=None):
                records.append(dict(self.proof, configuration=c['id'], repeat=repeat, fold=fold, member=member,
                    scaler=c['scaler'], kernel=c['kernel'], components=c['k'], order=c['order'],
                    **{'Sample ID': sample, 'Patient ID': patient, 'true_subtype': label, 'predicted_subtype': label},
                    C=1, gamma='scale' if c['kernel'] == 'rbf' else 'NA', best_inner_macro_f1=.5,
                    train_samples=48, test_samples=12, retained_genes=8, runtime_seconds=1,
                    pca_explained_variance=.5, run_id=f'run-{member}', started_utc='2026-10-15T00:00:00+00:00', run_state='complete'))
        path = self.root / f'member{member}_results.csv'
        experiment.checkpoint(path, records, 'complete')
        return path

    def edit(self, path, change, rehash=True):
        table = change(experiment.read_csv(path))
        if rehash: table['payload_sha256'] = experiment.payload_hash(table)
        table.to_csv(path, index=False, lineterminator='\n')

    def test_assignments_and_pipeline_orders(self):
        s = experiment.settings()
        self.assertEqual(len(s['configurations']), 24)
        for member in range(1, 5):
            configs = [c for c in s['configurations'] if c['member'] == member]
            self.assertEqual({(c['k'], c['order']) for c in configs}, {(k, o) for k in [50, 100, 150] for o in ['scale_pca', 'pca_scale']})
        c = self.s['configurations'][0]
        for order, names in [('scale_pca', ['log', 'variance', 'scale', 'reduction', 'model']), ('pca_scale', ['log', 'variance', 'reduction', 'scale', 'model'])]:
            self.assertEqual(list(build_pipeline(dict(c, order=order), self.s).named_steps), names)

    def test_collect_recalculates_all_metrics_from_four_csvs(self):
        files = [self.fixture(i) for i in range(1, 5)]
        with contextlib.redirect_stdout(io.StringIO()):
            out = experiment.collect(files, self.root / 'combined', self.s, self.data, self.outer, self.proof)
        for name, count in [('team_summary.csv', 24), ('paired_order_comparison.csv', 12), ('team_repeat_scores.csv', 72), ('team_subtypes.csv', 216), ('team_confusions.csv', 648)]:
            self.assertEqual(len(out[name]), count)
        self.assertTrue((out['team_summary.csv'].macro_f1_mean == 1).all())
        self.assertEqual(len(list(self.root.glob('member*'))), 4)

    def test_missing_duplicate_wrong_fold_label_order_patient(self):
        for problem in ['missing', 'duplicate', 'fold', 'true_subtype', 'order', 'Patient ID']:
            with self.subTest(problem=problem):
                path = self.fixture(1)
                def change(t):
                    if problem == 'missing': return t.iloc[1:]
                    if problem == 'duplicate': return pd.concat([t, t.iloc[:1]])
                    t.loc[0, problem] = '99' if problem == 'fold' else 'wrong'
                    return t
                self.edit(path, change)
                with self.assertRaises((ValueError, AssertionError)):
                    experiment.validate(path, self.s, self.data, self.outer, self.proof, 1)

    def test_checksum_incomplete_release_and_parameters(self):
        for key, value, rehash in [('predicted_subtype', 'b', False), ('run_state', 'partial', True), ('git_commit', 'different', True), ('C', '999', True), ('runtime_seconds', '-1', True)]:
            with self.subTest(key=key):
                path = self.fixture(1)
                def change(t):
                    t.loc[0, key] = value
                    return t
                self.edit(path, change, rehash)
                with self.assertRaises((ValueError, AssertionError)):
                    experiment.validate(path, self.s, self.data, self.outer, self.proof, 1)

    def test_duplicate_member_and_partial_filename(self):
        path = self.fixture(1)
        with self.assertRaisesRegex(ValueError, 'duplicate member'):
            experiment.collect([path] * 4, self.root / 'combined', self.s, self.data, self.outer, self.proof)
        renamed = path.with_name('member1_results.partial.csv'); path.rename(renamed)
        with self.assertRaisesRegex(ValueError, 'partial'):
            experiment.validate(renamed, self.s, self.data, self.outer, self.proof, 1)

    def test_publication_refuses_existing_destination(self):
        partial = self.root / 'partial.csv'; final = self.root / 'final.csv'
        partial.write_text('new'); final.write_text('old')
        with self.assertRaises(FileExistsError): experiment.publish(partial, final)
        self.assertEqual(final.read_text(), 'old'); self.assertEqual(partial.read_text(), 'new')

    def test_real_both_order_training_leaves_one_csv_and_refuses_overwrite(self):
        s = copy.deepcopy(self.s); s['configurations'] = s['configurations'][:2]
        inner = generate_inner(self.data, self.outer, s)
        features = [c for c in self.data if c.startswith('gene__')]
        with patch.object(experiment, 'ROOT', self.root), contextlib.redirect_stdout(io.StringIO()):
            final = experiment.run(1, s, self.data, features, self.data[features].to_numpy(), self.outer, inner, self.proof)
            before = final.read_bytes()
            with self.assertRaisesRegex(ValueError, 'will not be overwritten'):
                experiment.run(1, s, self.data, features, self.data[features].to_numpy(), self.outer, inner, self.proof)
        self.assertEqual(list(final.parent.iterdir()), [final])
        self.assertEqual(len(experiment.read_csv(final)), 360)
        self.assertEqual(final.read_bytes(), before)
        experiment.validate(final, s, self.data, self.outer, self.proof, 1)

    def test_interruption_retains_partial_and_blocks_retry(self):
        features = [c for c in self.data if c.startswith('gene__')]
        inner = generate_inner(self.data, self.outer, self.s)
        with patch.object(experiment, 'ROOT', self.root), patch.object(experiment, 'fit_search', side_effect=KeyboardInterrupt()), contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises(KeyboardInterrupt):
                experiment.run(1, self.s, self.data, features, self.data[features].to_numpy(), self.outer, inner, self.proof)
            final, partial = experiment.result_paths(1)
            self.assertFalse(final.exists()); self.assertTrue(partial.exists())
            self.assertEqual(list(partial.parent.iterdir()), [partial])
            with self.assertRaisesRegex(ValueError, 'Partial run exists'):
                experiment.run(1, self.s, self.data, features, self.data[features].to_numpy(), self.outer, inner, self.proof)


if __name__ == '__main__': unittest.main()
