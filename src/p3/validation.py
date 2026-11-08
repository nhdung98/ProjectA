"""Validate submitted evidence without changing training or selection rules."""
import json

import numpy as np
import pandas as pd

from src.experiments.common import ROOT, sha256
from .inputs import code_hashes
from .pipelines import candidates


def require(condition, message):
    if not condition:
        raise ValueError(message)


def validate_evidence(config, runs, inputs):
    """Match all official round-B evidence to this release and verified cohort."""
    specs = {s['id']: s for s in config['pipelines']}
    require(set(runs) == set(specs), 'Expected exactly the configured pipelines')
    reference = inputs['outer'].rename(columns={'subtype': 'true_subtype'})
    keys = ['repeat', 'fold', 'Sample ID', 'Patient ID', 'true_subtype']
    reference = reference[keys].sort_values(['repeat', 'Sample ID']).reset_index(drop=True)
    pairs = sorted(set(zip(reference['repeat'], reference['fold'])))
    identity = code_hashes()
    config_hash = sha256(ROOT / 'configs/protocol3.json')
    for name, run in runs.items():
        m, predictions, search = run['manifest'], run['predictions'], run['search']
        prefix = f'{name}: '
        require(m.get('round') == 'B' and m.get('status') == 'complete'
                and m.get('development') is False and m.get('git_dirty_code') is False,
                prefix + 'not a clean official round-B run')
        require(bool(m.get('git_commit')), prefix + 'missing code commit')
        require(m.get('config_sha256') == config_hash and m.get('code_sha256') == identity
                and m.get('packages') == config['packages'], prefix + 'release/config/splits/packages mismatch')
        spec = specs[name]
        require(m.get('pipeline') == name and m.get('spec') == spec, prefix + 'pipeline specification mismatch')
        owners = [int(i) for i, member in config['members'].items() if name in member['pipelines']]
        require(owners == [m.get('member')], prefix + 'wrong member assignment')
        grid = candidates(spec)
        require(m.get('candidates') == grid, prefix + 'manifest grid mismatch')
        require(predictions is not None and set(keys + ['pipeline', 'predicted_subtype']).issubset(predictions),
                prefix + 'missing prediction columns')
        require(not predictions[keys + ['pipeline', 'predicted_subtype']].isna().any().any(),
                prefix + 'missing prediction values')
        require(predictions['pipeline'].eq(name).all(), prefix + 'wrong prediction pipeline')
        require(not predictions.duplicated(['repeat', 'Sample ID']).any(), prefix + 'duplicate predictions')
        actual = predictions[keys].sort_values(['repeat', 'Sample ID']).reset_index(drop=True)
        require(actual.equals(reference), prefix + 'predictions differ from verified cohort/labels/folds')
        require(set(predictions['predicted_subtype']).issubset(inputs['labels']), prefix + 'unknown prediction label')
        records = m.get('folds', [])
        require([(r['repeat'], r['fold']) for r in records] == pairs, prefix + 'missing/duplicate manifest folds')
        require(len(search) == len(grid) * len(pairs), prefix + 'incomplete inner search')
        require(set(zip(search['repeat'], search['fold'])) == set(pairs), prefix + 'unexpected search folds')
        detail_pairs = [(r['repeat'], r['fold']) for r in run['details']]
        require(sorted(detail_pairs) == pairs, prefix + 'missing/duplicate feature details')
        n_inner = inputs['settings']['inner_validation']['n_splits']
        score_columns = [f'inner_{i + 1}' for i in range(n_inner)]
        require(set(score_columns + ['mean_inner', 'selected', 'params', 'candidate']).issubset(search),
                prefix + 'missing search columns')
        for record in records:
            r, f = record['repeat'], record['fold']
            block = search[(search['repeat'] == r) & (search['fold'] == f)].sort_values('candidate')
            require(block['candidate'].tolist() == list(range(len(grid))), prefix + 'candidate IDs mismatch')
            try:
                params = [json.loads(p) for p in block['params']]
                scores = block[score_columns].to_numpy(dtype=float)
                stored_means = block['mean_inner'].to_numpy(dtype=float)
            except (TypeError, ValueError) as error:
                raise ValueError(prefix + 'invalid search evidence') from error
            require(params == grid, prefix + 'candidate parameters mismatch')
            require(np.isfinite(scores).all() and ((scores >= 0) & (scores <= 1)).all(),
                    prefix + 'invalid inner scores')
            means = scores.mean(axis=1)
            require(np.allclose(means, stored_means, rtol=0, atol=1e-12), prefix + 'inner means mismatch')
            best = int(np.argmax(means))
            require(block['selected'].tolist() == [i == best for i in range(len(grid))],
                    prefix + 'selected flags do not match inner winner')
            test_count = int(((reference['repeat'] == r) & (reference['fold'] == f)).sum())
            require(record.get('status') == 'complete' and record.get('best_candidate') == best
                    and record.get('best_params') == grid[best]
                    and np.isclose(record.get('best_inner', np.nan), means[best], rtol=0, atol=1e-12),
                    prefix + 'manifest winner mismatch')
            require(record.get('test_samples') == test_count
                    and record.get('train_samples') == len(inputs['data']) - test_count
                    and record.get('fits') == len(grid) * n_inner + 1, prefix + 'fit/sample counts mismatch')
