"""Small source/processed fixtures exercise real identity checks without patient data."""
from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import pandas as pd

from src.experiments import common


class SourceIdentityTests(unittest.TestCase):
    @contextmanager
    def fixture(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'configs').mkdir()
            (root / 'data/raw').mkdir(parents=True)
            (root / 'data/processed').mkdir()
            clinical = pd.DataFrame({'Sample ID': [f'S{i}' for i in range(6)],
                                     'Patient ID': [f'P{i}' for i in range(6)],
                                     'Cancer Type Detailed': ['Class A'] * 3 + ['Class B'] * 3})
            expression = pd.DataFrame({'Hugo_Symbol': ['G1', 'G2'], 'Entrez_Gene_Id': ['1', '2'],
                                       **{f'S{i}': [i, i + 1] for i in range(6)}})
            cp, ep = root / 'data/raw/clinical.tsv', root / 'data/raw/expression.tsv'
            clinical.to_csv(cp, sep='\t', index=False)
            expression.to_csv(ep, sep='\t', index=False)
            source = dict(clinical_file='data/raw/clinical.tsv', expression_file='data/raw/expression.tsv',
                          label_column='Cancer Type Detailed', target_subtypes={'Class A': 'A', 'Class B': 'B'})
            (root / 'configs/data.yaml').write_text(json.dumps(source))
            data = clinical.copy()
            data['subtype'] = ['A'] * 3 + ['B'] * 3
            data['gene__G1__1__row1'] = list(range(6))
            data['gene__G2__2__row2'] = list(range(1, 7))
            dataset = root / 'data/processed/cohort.tsv'
            data.to_csv(dataset, sep='\t', index=False)
            settings = dict(dataset='data/processed/cohort.tsv', expected_samples=6, expected_features=2,
                            class_counts={'A': 3, 'B': 3},
                            source_sha256={p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in (cp, ep)})
            with patch.object(common, 'ROOT', root):
                yield root, data, settings, dataset

    def test_identity_and_gene_only_inputs(self):
        with self.fixture() as (_, data, settings, _):
            actual, features, values = common.load_dataset(settings)
            self.assertEqual(len(actual), 6)
            self.assertEqual(features, ['gene__G1__1__row1', 'gene__G2__2__row2'])
            self.assertEqual(values.shape, (6, 2))

    def test_edited_processed_values_labels_ids_and_dimensions_rejected(self):
        with self.fixture() as (_, data, settings, dataset):
            for corruption in ('expression', 'labels', 'patient', 'missing', 'nonfinite'):
                changed = data.copy()
                if corruption == 'expression':
                    changed.loc[0, 'gene__G1__1__row1'] = 999
                elif corruption == 'labels':
                    changed.loc[[0, 3], 'subtype'] = ['B', 'A']  # Keep class counts unchanged.
                elif corruption == 'patient':
                    changed.loc[0, 'Patient ID'] = changed.loc[1, 'Patient ID']
                elif corruption == 'missing':
                    changed = changed.iloc[:-1]
                else:
                    changed['gene__G1__1__row1'] = changed['gene__G1__1__row1'].astype(float)
                    changed.loc[0, 'gene__G1__1__row1'] = float('inf')
                changed.to_csv(dataset, sep='\t', index=False)
                with self.subTest(corruption=corruption), self.assertRaises(ValueError):
                    common.load_dataset(settings)

    def test_changed_raw_bytes_rejected(self):
        with self.fixture() as (root, _, settings, _):
            path = root / 'data/raw/expression.tsv'
            path.write_bytes(path.read_bytes() + b'\n')
            with self.assertRaisesRegex(ValueError, 'Changed source'):
                common.load_dataset(settings)


if __name__ == '__main__':
    unittest.main()
