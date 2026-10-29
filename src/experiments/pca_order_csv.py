"""Single-CSV PCA-order runner and independent prediction-based collection."""
import argparse
from contextlib import contextmanager
import tempfile
from datetime import datetime, timezone
import hashlib
import json
import os
import platform
from importlib.metadata import version
from pathlib import Path
import subprocess
import time
import uuid
import warnings
import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits
from .common import ROOT, load_dataset, sha256, shared_splits, verify_environment
from .metrics import summarize
from .svm import candidates, fit_search, inner_indices, shared_inner
from .validation import fold_indices

PREDICTIONS = ['configuration', 'repeat', 'fold', 'Sample ID', 'Patient ID', 'true_subtype', 'predicted_subtype']
IDENTITY = ['protocol', 'git_commit', 'code_sha256', 'packages', 'dataset_sha256', 'outer_sha256', 'inner_sha256']
EVIDENCE = ['C', 'gamma', 'best_inner_macro_f1', 'train_samples', 'test_samples', 'retained_genes', 'runtime_seconds', 'pca_explained_variance']
COLUMNS = PREDICTIONS + ['member', 'scaler', 'kernel', 'components', 'order'] + EVIDENCE + IDENTITY + ['run_id', 'started_utc', 'run_state', 'payload_sha256']
SUMMARY = ['configuration', 'member', 'scaler', 'kernel', 'components', 'order', 'macro_f1_mean', 'macro_f1_sd', 'balanced_accuracy_mean', 'balanced_accuracy_sd']


def require(condition, message):
    if not condition:
        raise ValueError(message)


def settings():
    return json.loads((ROOT / 'configs/pca_order.json').read_text(encoding='utf-8'))


def git(*args):
    installed = Path(r'C:\Program Files\Git\cmd\git.exe')
    return subprocess.check_output([str(installed) if installed.exists() else 'git', *args], cwd=ROOT, text=True, timeout=30).strip()


def provenance(s, packages):
    paths = ['configs/pca_order.json', 'configs/data.yaml', 'requirements.txt', 'requirements-experiments.txt', 'requirements-protocol2-lock.txt']
    paths += ['src/experiments/' + n for n in ['__init__.py', 'pca_order.py', 'pca_order_csv.py', 'pipeline.py', 'svm.py', 'common.py', 'metrics.py', 'validation.py']]
    code = ''.join(p + ':' + hashlib.sha256((ROOT / p).read_bytes().replace(b'\r\n', b'\n')).hexdigest() for p in paths)
    return dict(protocol=s['round'], git_commit=git('rev-parse', 'HEAD'), code_sha256=hashlib.sha256(code.encode()).hexdigest(),
                packages=json.dumps(packages, sort_keys=True), dataset_sha256=sha256(ROOT / s['dataset']),
                outer_sha256=sha256(ROOT / 'results/splits/outer.csv'), inner_sha256=sha256(ROOT / 'results/splits/inner.csv'))


def scalar(value):
    if isinstance(value, (float, np.floating)):
        require(np.isfinite(value), 'Nonfinite numeric result')
        return format(float(value), '.17g')
    return str(value)


def read_csv(path):
    return pd.read_csv(path, dtype=str, keep_default_na=False)


def payload_hash(table):
    return hashlib.sha256(table.drop(columns='payload_sha256').to_csv(index=False, lineterminator='\n').encode('utf-8')).hexdigest()


def atomic_write(path, payload):
    """Unique same-directory temporary; a crash leaves the last committed CSV intact."""
    fd, temporary = tempfile.mkstemp(prefix=path.name + '.', suffix='.tmp', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def checkpoint(path, records, state):
    table = pd.DataFrame([{k: scalar(row[k]) for k in COLUMNS[:-1]} for row in records], columns=COLUMNS[:-1])
    table['run_state'] = state
    table['payload_sha256'] = ''
    table['payload_sha256'] = payload_hash(table)
    atomic_write(path, table.to_csv(index=False, lineterminator='\n').encode('utf-8'))


@contextmanager
def member_lock(final):
    """OS-held lock, released on process exit. Keep the lock inode; never unlink it."""
    path = final.with_suffix('.lock')
    with path.open('a+b') as stream:
        if stream.seek(0, os.SEEK_END) == 0:
            stream.write(b'0'); stream.flush()
        stream.seek(0)
        try:
            if os.name == 'nt':
                import msvcrt
                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as error:
            raise ValueError('Another process holds this member lock; do not remove the lock file') from error
        try:
            yield
        finally:
            stream.seek(0)
            if os.name == 'nt':
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


def activity(path, event, common, completed):
    record = dict(event=event, utc=datetime.now(timezone.utc).isoformat(),
                  run_id=common['run_id'], completed_evaluations=len(completed))
    with path.open('a', encoding='utf-8') as stream:
        stream.write(json.dumps(record, sort_keys=True) + '\n')
        stream.flush(); os.fsync(stream.fileno())


def metrics_tables(table, configs, s, data):
    predictions = table[PREDICTIONS].copy()
    predictions[['repeat', 'fold']] = predictions[['repeat', 'fold']].astype(int)
    summary, repeats, subtypes, confusions = [], [], [], []
    for config in configs:
        result = summarize(predictions[predictions.configuration == config['id']], s['labels'], data['Sample ID'], s['validation']['n_repeats'])
        summary.append([config['id'], config['member'], config['scaler'], config['kernel'], config['k'], config['order'],
                        result['summary']['macro_f1']['mean'], result['summary']['macro_f1']['sample_std'],
                        result['summary']['balanced_accuracy']['mean'], result['summary']['balanced_accuracy']['sample_std']])
        for repeat in result['repeats']:
            repeats.append([config['id'], repeat['repeat'], repeat['macro_f1'], repeat['balanced_accuracy']])
            for label, values in repeat['per_class'].items():
                subtypes.append([config['id'], repeat['repeat'], label, values['precision'], values['recall'], values['f1'], values['support']])
            for i, actual in enumerate(s['labels']):
                for j, predicted in enumerate(s['labels']):
                    confusions.append([config['id'], repeat['repeat'], actual, predicted, repeat['confusion_matrix'][i][j]])
    return {'team_summary.csv': pd.DataFrame(summary, columns=SUMMARY),
            'team_repeat_scores.csv': pd.DataFrame(repeats, columns=['configuration', 'repeat', 'macro_f1', 'balanced_accuracy']),
            'team_subtypes.csv': pd.DataFrame(subtypes, columns=['configuration', 'repeat', 'subtype', 'precision', 'recall', 'f1', 'support']),
            'team_confusions.csv': pd.DataFrame(confusions, columns=['configuration', 'repeat', 'true_subtype', 'predicted_subtype', 'count'])}


def validate(path, s, data, outer, proof, member, partial=False, checkpoint_mode=False):
    path = Path(path)
    require(partial or path.name == f'member{member}_results.csv', 'Use completed memberN_results.csv; partial or renamed files are not accepted')
    table = read_csv(path)
    require(list(table.columns) == COLUMNS, 'Unexpected CSV columns')
    require(not table.empty, 'Empty checkpoint has no verifiable record checksum; preserve the bundle and request a reviewed fresh run')
    states = set(table.run_state)
    require(len(table) > 0 and (states in ({'partial'}, {'complete'}) if checkpoint_mode else states == {'complete'}), 'Result is incomplete or has mixed states')
    require(set(table.payload_sha256) == {payload_hash(table)}, 'CSV checksum mismatch')
    for key in IDENTITY:
        require(key in proof and set(table[key]) == {str(proof[key])}, f'Mismatched {key}; use the same release, data and environment')
    for key in ['run_id', 'started_utc']:
        require(table[key].nunique() == 1 and table[key].iloc[0] != '', f'Missing or mixed {key}')
    require(set(table.member) == {str(member)}, 'Wrong member assignment')
    configs = [c for c in s['configurations'] if c['member'] == member]
    planned = {c['id'] for c in configs}
    require(set(table.configuration).issubset(planned) if checkpoint_mode else set(table.configuration) == planned, 'Unexpected or missing configurations')
    parsed = table.copy()
    integers = ['repeat', 'fold', 'member', 'components', 'train_samples', 'test_samples', 'retained_genes']
    for key in list(dict.fromkeys(integers + [c for c in EVIDENCE if c != 'gamma'])):
        parsed[key] = pd.to_numeric(parsed[key], errors='raise')
        require(np.isfinite(parsed[key]).all(), f'Invalid numeric field: {key}')
        if key in integers:
            require((parsed[key] % 1 == 0).all(), f'Noninteger field: {key}')
            parsed[key] = parsed[key].astype(int)
    keys = ['repeat', 'fold', 'Sample ID', 'Patient ID', 'true_subtype']
    reference = outer.rename(columns={'subtype': 'true_subtype'})[keys].sort_values(['repeat', 'Sample ID']).reset_index(drop=True)
    completed = set()
    allowed_folds = set(zip(outer['repeat'], outer['fold']))
    for config in configs:
        block = parsed[parsed.configuration == config['id']]
        if checkpoint_mode and block.empty:
            continue
        pairs = set(zip(block['repeat'], block['fold']))
        require(pairs.issubset(allowed_folds), 'Unexpected repeat/fold')
        expected_rows = reference
        if checkpoint_mode:
            expected_rows = reference.loc[[pair in pairs for pair in zip(reference['repeat'], reference['fold'])]].reset_index(drop=True)
        for key, expected in [('scaler', config['scaler']), ('kernel', config['kernel']), ('components', config['k']), ('order', config['order'])]:
            require(set(block[key]) == {expected}, f'Wrong configuration field: {key}')
        actual = block[keys].sort_values(['repeat', 'Sample ID']).reset_index(drop=True)
        pd.testing.assert_frame_equal(actual, expected_rows, check_dtype=False)
        require(set(block.predicted_subtype).issubset(s['labels']), 'Unknown predicted label')
        require(block.best_inner_macro_f1.between(0, 1).all(), 'Invalid inner score')
        require((block.runtime_seconds >= 0).all(), 'Invalid runtime')
        require(block.pca_explained_variance.between(0, 1 + 1e-10).all(), 'Invalid PCA variance')
        require(block.retained_genes.between(config['k'], len([c for c in data if c.startswith('gene__')])).all(), 'Invalid feature count')
        allowed = {(float(p['model__C']), str(p.get('model__gamma', 'NA'))) for p in candidates(config, s)}
        for (repeat, fold), group in block.groupby(['repeat', 'fold']):
            require(all(group[c].nunique() == 1 for c in EVIDENCE), 'Mixed parameters/evidence within an outer fold')
            row = group.iloc[0]
            require((float(row.C), str(row.gamma)) in allowed, 'Selected C/gamma outside the agreed grid')
            count = len(outer[(outer['repeat'] == repeat) & (outer['fold'] == fold)])
            require(row.test_samples == count and row.train_samples == len(data) - count, 'Wrong train/test counts')
            completed.add((config['id'], int(repeat), int(fold)))
    if checkpoint_mode:
        return table, completed
    return table, metrics_tables(table, configs, s, data)


def result_paths(member):
    folder = ROOT / 'results/pca_order'
    return folder / f'member{member}_results.csv', folder / f'member{member}_results.partial.csv'


def publish(partial, final):
    # Same-filesystem hard link is atomic and refuses an existing destination.
    os.link(partial, final)
    partial.unlink()


def evaluate_fold(config, s, data, features, values, train, test, cv, started):
    """Unchanged scientific computation; called only for an uncommitted outer fold."""
    with threadpool_limits(limits=s['blas_threads']), warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        search = fit_search(config, s, values[train], data.iloc[train].subtype, cv)
        labels = search.predict(values[test])
    require(not caught, 'Training/prediction warning: ' + '; '.join(str(w.message) for w in caught))
    pipeline = search.best_estimator_
    evidence = dict(C=search.best_params_['model__C'], gamma=search.best_params_.get('model__gamma', 'NA'),
                    best_inner_macro_f1=search.best_score_, train_samples=len(train), test_samples=len(test),
                    retained_genes=int(pipeline.named_steps['variance'].get_support().sum()),
                    runtime_seconds=time.perf_counter() - started,
                    pca_explained_variance=float(pipeline.named_steps['reduction'].explained_variance_ratio_.sum()))
    return labels, evidence


def run(member, s, data, features, values, outer, inner, proof, *, resume=False, evaluate=None):
    final, partial = result_paths(member)
    final.parent.mkdir(parents=True, exist_ok=True)
    context_path = final.with_suffix('.context.json')
    log_path = final.with_suffix('.activity.jsonl')
    evaluate = evaluate or evaluate_fold
    execution = dict(python=platform.python_version(), system=platform.system(), machine=platform.machine(),
                     dependencies={name: version(name) for name in ('numpy', 'pandas', 'scikit-learn', 'scipy', 'joblib', 'threadpoolctl', 'python-dateutil', 'six', 'tzdata')})
    expected_context = dict(schema_version=1, member=member, settings=s, proof=proof, execution=execution)
    with member_lock(final):
        require(not final.exists(), f'Result exists: {final}. It will not be overwritten.')
        if resume:
            require(partial.exists() and context_path.exists(), 'Resume requires the original partial CSV and context; legacy/incomplete bundles require review')
            context = json.loads(context_path.read_text(encoding='utf-8'))
            require({k: context.get(k) for k in expected_context} == expected_context, 'Checkpoint context differs: release/configuration/data/splits/environment')
            common = context.get('common', {})
            require(set(common) == set(proof) | {'member', 'run_id', 'started_utc', 'run_state'}, 'Invalid checkpoint run identity')
            require(all(common.get(k) == v for k, v in proof.items()) and common['member'] == member
                    and common['run_state'] == 'partial' and bool(common['run_id']) and bool(common['started_utc']), 'Invalid checkpoint provenance')
            table, completed = validate(partial, s, data, outer, proof, member, partial=True, checkpoint_mode=True)
            if len(table):
                for key in ('run_id', 'started_utc'):
                    require(set(table[key]) == {common[key]}, 'Checkpoint/context run identity mismatch')
            records = table.drop(columns='payload_sha256').to_dict('records')
            activity(log_path, 'resume', common, completed)
        else:
            require(not partial.exists() and not context_path.exists() and not log_path.exists(), 'Partial run or context exists; use --resume or preserve the entire bundle before an approved fresh run')
            common = dict(proof, member=member, run_id=uuid.uuid4().hex,
                          started_utc=datetime.now(timezone.utc).isoformat(), run_state='partial')
            # Immutable identity first. A crash before the initial CSV fails closed on resume.
            with context_path.open('x', encoding='utf-8') as stream:
                json.dump(dict(expected_context, common=common), stream, indent=2, allow_nan=False)
                stream.flush(); os.fsync(stream.fileno())
            records, completed = [], set()
            checkpoint(partial, records, 'partial')
            activity(log_path, 'start', common, completed)
        print(f'Member {member}: {len(completed)} verified evaluations retained', flush=True)
        try:
            for config in [c for c in s['configurations'] if c['member'] == member]:
                for repeat, fold, train, test in fold_indices(outer, data):
                    key = (config['id'], repeat, fold)
                    if key in completed:
                        continue
                    started = time.perf_counter()
                    cv = inner_indices(data.iloc[train][['Sample ID', 'Patient ID', 'subtype']], inner, repeat, fold)
                    labels, evidence = evaluate(config, s, data, features, values, train, test, cv, started)
                    require(len(labels) == len(test), 'Prediction count differs from outer test size')
                    block = []
                    for index, label in zip(test, labels):
                        row = data.iloc[index]
                        block.append(dict(common, **evidence, configuration=config['id'], scaler=config['scaler'], kernel=config['kernel'],
                                          components=config['k'], order=config['order'], repeat=repeat, fold=fold,
                                          **{'Sample ID': row['Sample ID'], 'Patient ID': row['Patient ID'], 'true_subtype': row.subtype, 'predicted_subtype': label}))
                    # Commit complete folds only; never save records from an interrupted evaluation.
                    checkpoint(partial, records + block, 'partial')
                    records.extend(block)
                    completed.add(key)
                    print(f'{config["id"]}: repeat {repeat}, fold {fold} committed', flush=True)
            checkpoint(partial, records, 'complete')
            validate(partial, s, data, outer, proof, member, partial=True)
            activity(log_path, 'validated_for_publication', common, completed)
            publish(partial, final)
            print(f'COMPLETE: {final}. Keep context/activity private alongside the CSV.', flush=True)
            return final
        except BaseException:
            # Never rewrite durable checkpoint from stale/incomplete in-memory state.
            print(f'INCOMPLETE: preserve {partial} and its context/activity. Use explicit --resume after review.', flush=True)
            raise


def collect(files, destination, s, data, outer, proof):
    require(len(files) == 4, 'Supply exactly one CSV for each of the 4 members')
    tables, members, sources = [], set(), []
    for filename in files:
        table = read_csv(filename)
        require('member' in table and len(table) > 0 and table.member.nunique() == 1, 'Missing or mixed member identity')
        member = int(table.member.iloc[0])
        require(member in range(1, 5) and member not in members, 'Invalid or duplicate member submission')
        members.add(member)
        table, _ = validate(filename, s, data, outer, proof, member)
        tables.append(table)
        sources.append([member, str(Path(filename).resolve()), sha256(filename), table.run_id.iloc[0]])
    outputs = metrics_tables(pd.concat(tables, ignore_index=True), s['configurations'], s, data)
    combined = outputs['team_summary.csv']
    keys = ['member', 'scaler', 'kernel', 'components']
    before = combined[combined.order == 'scale_pca'].set_index(keys)
    after = combined[combined.order == 'pca_scale'].set_index(keys)
    require(not before.index.has_duplicates and not after.index.has_duplicates and set(before.index) == set(after.index), 'Missing or duplicate order pairs')
    paired = before[['macro_f1_mean', 'balanced_accuracy_mean']].join(after[['macro_f1_mean', 'balanced_accuracy_mean']], lsuffix='_scale_first', rsuffix='_pca_first')
    for metric in ['macro_f1', 'balanced_accuracy']:
        paired[metric + '_delta_pca_first'] = paired[metric + '_mean_pca_first'] - paired[metric + '_mean_scale_first']
    outputs['paired_order_comparison.csv'] = paired.reset_index()
    outputs['sources.csv'] = pd.DataFrame(sources, columns=['member', 'file', 'sha256', 'run_id'])
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=False)
    for name, table in outputs.items():
        table.to_csv(destination / name, index=False, lineterminator='\n')
    print(f'All 4 CSVs passed validation. Recalculated comparison: {destination}', flush=True)
    return outputs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('check')
    command = sub.add_parser('run')
    command.add_argument('--member', type=int, choices=range(1, 5), required=True)
    command.add_argument('--resume', action='store_true', help='Validate and reuse completed outer evaluations; never resume an inner fit')
    command = sub.add_parser('validate')
    command.add_argument('--member', type=int, choices=range(1, 5), required=True)
    command = sub.add_parser('collect')
    command.add_argument('files', nargs=4)
    command.add_argument('--output', required=True)
    args = parser.parse_args()
    s = settings()
    print('Checking pinned environment, source data and expression values...', flush=True)
    packages = verify_environment(s)
    data, features, values = load_dataset(s)
    print('Checking saved splits and release identities...', flush=True)
    outer = shared_splits(data, s)
    inner = shared_inner(data[['Sample ID', 'Patient ID', 'subtype']], outer, s)
    proof = provenance(s, packages)
    require(not git('status', '--porcelain'), 'Official operations require a clean committed checkout of the shared release')
    if args.command == 'run':
        run(args.member, s, data, features, values, outer, inner, proof, resume=args.resume)
    elif args.command == 'validate':
        validate(result_paths(args.member)[0], s, data, outer, proof, args.member)
        print('Completed member CSV passed validation. No models trained.')
    elif args.command == 'collect':
        collect(args.files, args.output, s, data, outer, proof)
    else:
        print('Data, environment and saved splits verified. No models trained.')
