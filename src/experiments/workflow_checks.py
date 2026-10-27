"""Protocol 2.0 gates for the standardized workflow; never prepare data or splits."""
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from importlib.metadata import PackageNotFoundError, distributions, version
from pathlib import Path

import numpy as np
import pandas as pd
from threadpoolctl import threadpool_info

from . import common, svm
from .validate_svm import audit_run, require

REQUIRED = ('config.json', 'run_manifest.json', 'predictions.csv', 'metrics.json',
            'feature_details.json', 'search_results.json', 'warnings.log',
            'validation.json', 'submission.md')
REFERENCE = 'SVM-STD-ANOVA-150-LINEAR'
WORKFLOW_VERSION = 2


def now():
    return datetime.now(timezone.utc).isoformat()


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def environment(settings):
    packages = {}
    for name in settings['packages']:
        try:
            packages[name] = version(name)
        except PackageNotFoundError:
            packages[name] = None
    return dict(python=sys.version, python_executable=sys.executable,
                operating_system=platform.platform(), machine=platform.machine(), packages=packages,
                environment_packages={d.metadata['Name']: d.version for d in distributions()},
                numeric_libraries=[{k: row[k] for k in ('internal_api', 'version', 'architecture', 'threading_layer') if k in row}
                                   for row in threadpool_info()])


def code_hashes():
    paths = list((common.ROOT / 'src/experiments').glob('*.py'))
    paths += list((common.ROOT / 'src/data').glob('*.py'))
    paths += [common.ROOT / p for p in ('configs/svm.json', 'configs/data.yaml',
                                      'requirements.txt', 'requirements-experiments.txt', 'requirements-protocol2-lock.txt')]
    return {p.relative_to(common.ROOT).as_posix(): common.sha256(p) for p in sorted(paths)}


def identity(settings, packages):
    proof = svm.provenance(settings, packages)
    proof.update(environment(settings), code_sha256=code_hashes(),
                 workflow_version=WORKFLOW_VERSION)
    return proof


def preflight(settings, official=False):
    """Return all failures and, on success, verified in-memory training inputs."""
    report = dict(checked_utc=now(), protocol_version=settings['protocol_version'],
                  environment=environment(settings), checks={}, errors=[],
                  data_checksums={}, split_checksums={})
    context = None
    def check(name, action):
        try:
            result = action()
            report['checks'][name] = 'passed'
            return result
        except (ValueError, AssertionError, OSError, KeyError, PackageNotFoundError,
                subprocess.SubprocessError) as error:
            report['checks'][name] = 'failed'
            report['errors'].append(f'{name}: {type(error).__name__}: {error}')
            return None
    packages = check('environment', lambda: common.verify_environment(settings))
    def transitive_versions():
        for line in (common.ROOT / 'requirements-protocol2-lock.txt').read_text().splitlines():
            if '==' in line and not line.startswith('#'):
                name, expected = line.strip().split('==')
                require(version(name) == expected, f'Locked transitive package mismatch: {name}')
    check('transitive_environment', transitive_versions)
    for relative, expected in settings['source_sha256'].items():
        def raw(path=relative, digest=expected):
            actual = common.sha256(common.ROOT / path)
            report['data_checksums'][path] = actual
            require(actual == digest, f'Input hash mismatch: {path}')
        check(relative, raw)
    def dataset_hash():
        path = common.ROOT / settings['dataset']
        actual = common.sha256(path)
        report['data_checksums'][settings['dataset']] = actual
        expected = read_json(common.SPLIT_MANIFEST)['dataset_sha256']
        require(actual == expected, 'Canonical dataset hash mismatch. Investigate serialization; do not change manifests.')
    check('canonical_dataset_hash', dataset_hash)
    for relative, manifest, field in (
        ('results/splits/outer.csv', common.SPLIT_MANIFEST, 'split_sha256'),
        ('results/splits/inner.csv', svm.INNER_MANIFEST, 'inner_sha256'),
    ):
        def split(path=relative, metadata=manifest, key=field):
            actual = common.sha256(common.ROOT / path)
            report['split_checksums'][path] = actual
            require(actual == read_json(metadata)[key], f'Split hash mismatch: {path}')
        check(relative, split)
    loaded = check('dataset_values_and_labels', lambda: common.load_dataset(settings))
    if loaded is not None and packages is not None:
        data, features, values = loaded
        outer = check('outer_assignments', lambda: common.shared_splits(data, settings))
        inner = check('inner_assignments', lambda: svm.shared_inner(data, outer, settings)) if outer is not None else None
        if inner is not None:
            context = (data, features, values, outer, inner, packages)
            report.update(patients=len(data), gene_records=len(features),
                          outer_assignments=len(outer), inner_assignments=len(inner))
    def release():
        result = subprocess.run(['git', 'status', '--porcelain'], cwd=common.ROOT,
                                check=True, capture_output=True, text=True)
        commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=common.ROOT, text=True).strip()
        report['git_commit'] = commit
        report['git_dirty'] = bool(result.stdout.strip())
        if official:
            require(not report['git_dirty'], 'Official execution requires a reviewed, committed, clean checkout.')
    check('git_release', release)
    report['status'] = 'passed' if not report['errors'] else 'failed'
    return report, context


def same_identity(recorded, current):
    # Resume never combines a new release, dataset, Python build or BLAS host with an old run.
    for key in ('git_commit', 'git_dirty', 'packages', 'python', 'operating_system', 'machine',
                'source_sha256', 'dataset_sha256', 'split_sha256', 'inner_split_sha256',
                'code_sha256', 'workflow_version', 'environment_packages', 'numeric_libraries'):
        require(recorded.get(key) == current.get(key), f'Resume/provenance mismatch: {key}')


def validate_block(block, configuration, settings, data, features, values, outer):
    """Check one saved fold transaction before reuse; this function performs no fitting."""
    fold = block['fold']
    repeat, number = fold['repeat'], fold['fold']
    require(type(repeat) is int and type(number) is int, 'Noninteger fold identity')
    test = outer[(outer['repeat'] == repeat) & (outer['fold'] == number)]
    require(len(test) > 0 and fold['status'] == 'complete', 'Invalid/incomplete checkpoint fold')
    require(fold['train_samples'] == len(data) - len(test) and fold['test_samples'] == len(test), 'Fold sample counts mismatch')
    require(np.isfinite(fold['runtime_seconds']) and fold['runtime_seconds'] >= 0, 'Invalid fold runtime')
    predictions = pd.DataFrame(block['predictions'])
    keys = ['Sample ID', 'Patient ID', 'subtype']
    actual = predictions.rename(columns={'true_subtype': 'subtype'})
    require(len(actual) == len(test) and not actual['Sample ID'].duplicated().any(), 'Checkpoint predictions incomplete/duplicated')
    pd.testing.assert_frame_equal(actual[keys].sort_values('Sample ID').reset_index(drop=True),
                                  test[keys].sort_values('Sample ID').reset_index(drop=True), check_dtype=False)
    require(predictions['configuration'].eq(configuration['id']).all(), 'Checkpoint configuration mismatch')
    require(predictions['repeat'].eq(repeat).all() and predictions['fold'].eq(number).all(), 'Checkpoint fold mismatch')
    require(set(predictions['predicted_subtype']).issubset(settings['labels']), 'Unknown prediction label')
    records, grid = block['search'], svm.candidates(configuration, settings)
    require(len(records) == len(grid), 'Missing search candidates')
    for i, (record, candidate) in enumerate(zip(records, grid)):
        require(record['repeat'] == repeat and record['fold'] == number and record['candidate'] == i
                and record['params'] == candidate, 'Search candidate identity/order mismatch')
        scores = np.asarray(record['scores'], dtype=float)
        require(scores.shape == (settings['inner_validation']['n_splits'],)
                and np.isfinite(scores).all() and ((scores >= 0) & (scores <= 1)).all(), 'Invalid inner scores')
        np.testing.assert_allclose(scores.mean(), record['mean_score'], rtol=0, atol=1e-12)
    winner = records[int(np.argmax([r['mean_score'] for r in records]))]
    require(winner['params'] == fold['best_params'], 'Incorrect search winner')
    np.testing.assert_allclose(winner['mean_score'], fold['best_inner_score'], rtol=0, atol=1e-12)
    require(fold['inner_folds'] == settings['inner_validation']['n_splits'] and fold['search_candidates'] == len(grid), 'Search workload mismatch')
    detail = block['details']
    require(detail['repeat'] == repeat and detail['fold'] == number, 'Feature-detail fold mismatch')
    train = ~data['Sample ID'].isin(test['Sample ID']).to_numpy()
    retained = np.asarray(features)[np.ptp(np.log2(values[train] + 1), axis=0) > 0].tolist()
    require(detail['retained_after_variance'] == retained, 'Training-only retained features mismatch')
    if configuration['reduction'] == 'anova':
        selected = detail['selected_genes']
        require(len(selected) == configuration['k'] and len(set(selected)) == len(selected)
                and set(selected).issubset(retained), 'Invalid selected genes')
    else:
        pca = detail['pca']
        ratios = np.asarray(pca['explained_variance_ratio'], dtype=float)
        require(pca['n_components'] == configuration['k'] and ratios.shape == (configuration['k'],)
                and np.isfinite(ratios).all() and (ratios >= 0).all() and ratios.sum() <= 1 + 1e-12,
                'Invalid PCA details')
        np.testing.assert_allclose(ratios.sum(), pca['total_explained_variance_ratio'], rtol=0, atol=1e-12)


def validate_run(folder, settings, data, outer, proof=None, *, finalizing=False):
    """Reuse the independent legacy metric audit, then enforce workflow evidence gates."""
    folder = Path(folder)
    require(all((folder / name).is_file() for name in REQUIRED), 'Missing required Protocol 2.0 artifacts')
    manifest = read_json(folder / 'run_manifest.json')
    require(manifest.get('workflow_version') == WORKFLOW_VERSION, 'Only new workflow runs are accepted here; historical evidence stays separate')
    require(manifest.get('evidence_origin') == 'new_experiment' and manifest.get('mode') == 'official', 'Smoke/historical runs cannot be official evidence')
    require(manifest['git_commit'] and manifest['git_dirty'] is False, 'Official run requires clean commit provenance')
    require(folder.name == manifest['run_id'], 'Run folder/ID mismatch')
    require(manifest['code_sha256'] == code_hashes(), 'Source code or requirements changed')
    if proof is not None:
        same_identity(manifest, proof)
    if not finalizing:
        expected_names = set(REQUIRED) - {'run_manifest.json'}
        require(set(manifest.get('artifact_sha256', {})) == expected_names, 'Incomplete artifact checksum inventory')
        for name, expected in manifest['artifact_sha256'].items():
            require(common.sha256(folder / name) == expected, f'Artifact checksum mismatch: {name}')
        saved = read_json(folder / 'validation.json')
        require(manifest.get('validation_status') == 'passed' and saved.get('status') == 'passed'
                and saved.get('run_id') == manifest['run_id'], 'Missing/mismatched saved automated validation')
    predictions, metrics, report = audit_run(folder, settings, data, outer, finalizing=finalizing)
    details = read_json(folder / 'feature_details.json')
    tuning = read_json(folder / 'search_results.json')
    pairs = {(f['repeat'], f['fold']) for f in manifest['folds']}
    require({(r['repeat'], r['fold']) for r in tuning} == pairs, 'Unexpected search folds')
    require(len(details) == len(pairs), 'Incomplete feature evidence')
    report.update(checked_utc=now(), protocol_version=settings['protocol_version'],
                  validator_sha256=common.sha256(Path(__file__)), run_id=manifest['run_id'],
                  peer_review='pending', evidence_origin='new_experiment')
    return predictions, metrics, report
