"""Explicit synthetic aggregate fixtures, never historical or official experiment evidence."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.reporting.dashboard_inputs import CONFIGS, LABELS, COUNTS, REFERENCE, SCHEMAS


def make_fixture(destination, count=24):
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=False)
    (destination / 'reports').mkdir()
    ids = list(CONFIGS)[:count]
    rng = np.random.default_rng(12345)
    manifest = dict(protocol_version='2.0', batch_id='SYNTHETIC-DEVELOPMENT-ONLY', mode='synthetic',
                    evidence_origin='synthetic_demo', status='complete', configurations=ids,
                    settings=dict(labels=LABELS, class_counts=dict(zip(LABELS, COUNTS))),
                    provenance=dict(git_commit='SYNTHETIC-NOT-A-RELEASE', git_dirty=False,
                                    python_executable='/Users/PRIVATE_FIXTURE/person/python'))
    tables = {name: [] for name in SCHEMAS}
    audits = {}
    for index, identifier in enumerate(ids):
        scale, reduction, k, kernel = CONFIGS[identifier]
        scores = []
        for repeat in (1, 2, 3):
            matrix = np.zeros((6, 6), dtype=int)
            for i, support in enumerate(COUNTS):
                probability = .54 + .012 * index + .015 * (repeat - 2)
                probabilities = np.full(6, (1 - probability) / 5)
                probabilities[i] = probability
                matrix[i] = rng.multinomial(support, probabilities)
            precision = np.divide(matrix.diagonal(), matrix.sum(axis=0), out=np.zeros(6), where=matrix.sum(axis=0) != 0)
            recall = matrix.diagonal() / np.array(COUNTS)
            f1 = np.divide(2 * precision * recall, precision + recall, out=np.zeros(6), where=(precision + recall) != 0)
            scores.append((f1.mean(), recall.mean()))
            tables['reports/repeat_scores.csv'].append(dict(configuration=identifier, repeat=repeat, macro_f1=f1.mean(), balanced_accuracy=recall.mean()))
            for i, label in enumerate(LABELS):
                tables['reports/subtype_analysis.csv'].append(dict(configuration=identifier, repeat=repeat, subtype=label,
                    precision=precision[i], recall=recall[i], f1=f1[i], support=COUNTS[i]))
                for j, predicted in enumerate(LABELS):
                    tables['reports/confusion_matrices.csv'].append(dict(configuration=identifier, repeat=repeat,
                        true_subtype=label, predicted_subtype=predicted, count=int(matrix[i,j])))
        scores = np.array(scores)
        tables['summary.csv'].append(dict(configuration=identifier, scaler='minmax' if scale == 'MM' else 'standard',
            reduction=reduction.lower(), components_or_genes=k, kernel=kernel.lower(), run_id=f'SYNTHETIC-RUN-{index}',
            macro_f1_mean=scores[:,0].mean(), macro_f1_sd=scores[:,0].std(ddof=1),
            balanced_accuracy_mean=scores[:,1].mean(), balanced_accuracy_sd=scores[:,1].std(ddof=1),
            runtime_seconds=25 + index * 7, validation_status='passed', git_commit='SYNTHETIC-NOT-A-RELEASE', peer_review='synthetic_fixture'))
        audits[identifier] = dict(status='passed', configuration=identifier, run_id=f'SYNTHETIC-RUN-{index}',
            fits=15, predictions=762, metrics_independently_recomputed=True, inner_search_checked=True,
            warning_log_empty=True, synthetic_fixture=True)
    ref = next((r for r in tables['summary.csv'] if r['configuration'] == REFERENCE), None)
    for row in tables['summary.csv']:
        tables['comparison.csv'].append(dict(configuration=row['configuration'], reference=REFERENCE,
            reference_available=ref is not None, macro_f1_delta=None if ref is None else row['macro_f1_mean']-ref['macro_f1_mean'],
            balanced_accuracy_delta=None if ref is None else row['balanced_accuracy_mean']-ref['balanced_accuracy_mean'],
            comparison_type='exploratory_descriptive'))
    for name, columns in SCHEMAS.items():
        pd.DataFrame(tables[name], columns=columns).to_csv(destination/name, index=False, lineterminator='\n')
    (destination/'experiment_manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    validation = dict(status='passed', full_24_comparison=count == 24, configurations=count, runs=audits,
                      synthetic_fixture=True, export_files={name: hashlib.sha256((destination/name).read_bytes()).hexdigest()
                          for name in ['experiment_manifest.json', *SCHEMAS]})
    (destination/'validation_summary.json').write_text(json.dumps(validation, indent=2), encoding='utf-8')
    return destination


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    make_fixture(args.output)
    print('Created SYNTHETIC aggregate fixtures, not experiment results:', args.output)
