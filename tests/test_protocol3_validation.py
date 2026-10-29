"""Submission rejection tests; no real cohort training is performed."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np

from test_protocol3 import CONFIG, cohort, fake_run
from src.p3.inputs import split_settings
from src.p3.results import load_runs
from src.p3.validation import validate_evidence


class EvidenceChecks(unittest.TestCase):
    def test_accepts_complete_evidence_and_rejects_corruptions(self):
        data, outer, labels = cohort()
        config = copy.deepcopy(CONFIG)
        spec = next(s for s in config['pipelines'] if s['id'] == 'P06')
        config['pipelines'] = [spec]
        inputs = dict(data=data, outer=outer, labels=labels, settings=split_settings(CONFIG))
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            fake_run(folder, spec, 'B', data, outer, labels, np.random.default_rng(42))
            good = load_runs([folder], 'B')
            validate_evidence(config, good, inputs)
            mutations = {
                'missing repeat': lambda r: r.update(predictions=r['predictions'].query('repeat != 3')),
                'duplicate patient': lambda r: r.update(predictions=r['predictions'].assign(**{'Sample ID': 'same'})),
                'wrong patient ID': lambda r: r.update(predictions=r['predictions'].assign(**{'Patient ID': 'wrong'})),
                'wrong true label': lambda r: r.update(predictions=r['predictions'].assign(true_subtype='FAKE')),
                'wrong fold': lambda r: r.update(predictions=r['predictions'].assign(fold=1)),
                'unknown prediction': lambda r: r.update(predictions=r['predictions'].assign(predicted_subtype='FAKE')),
                'wrong config': lambda r: r['manifest'].update(config_sha256='wrong'),
                'wrong code or split hash': lambda r: r['manifest'].update(code_sha256={}),
                'wrong packages': lambda r: r['manifest'].update(packages={}),
                'wrong owner': lambda r: r['manifest'].update(member=99),
                'dirty source': lambda r: r['manifest'].update(git_dirty_code=True),
                'wrong spec': lambda r: r['manifest'].update(spec={}),
                'missing inner candidate': lambda r: r.update(search=r['search'].iloc[1:]),
                'invalid inner score': lambda r: r.update(search=r['search'].assign(inner_1=np.nan)),
                'wrong mean': lambda r: r.update(search=r['search'].assign(mean_inner=0.0)),
                'wrong selected flags': lambda r: r.update(search=r['search'].assign(selected=False)),
                'wrong manifest winner': lambda r: r['manifest']['folds'][0].update(best_params={}),
                'wrong sample count': lambda r: r['manifest']['folds'][0].update(test_samples=999),
                'missing details': lambda r: r.update(details=[]),
            }
            for name, mutate in mutations.items():
                with self.subTest(name=name):
                    bad = copy.deepcopy(good)
                    mutate(bad['P06'])
                    with self.assertRaises(ValueError):
                        validate_evidence(config, bad, inputs)
            manifest_path = folder / 'P06/manifest.json'
            manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
            manifest['outputs'].pop('search_results.csv')
            manifest_path.write_text(json.dumps(manifest), encoding='utf-8')
            with self.assertRaises(ValueError):
                load_runs([folder], 'B')
