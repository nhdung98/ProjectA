"""Transactional, resumable orchestration around the unchanged Protocol 2.0 search."""
from contextlib import contextmanager
from datetime import datetime, timezone
import json
import errno
import shutil
import os
from pathlib import Path
import time
import uuid
import warnings

import pandas as pd
from threadpoolctl import threadpool_limits

from . import common, svm
from .metrics import summarize
from .pipeline import feature_details
from .validation import fold_indices
from .workflow_checks import (REQUIRED, WORKFLOW_VERSION, now, read_json, require,
                              same_identity, validate_block, validate_run)

PREDICTION_COLUMNS = ['configuration', 'repeat', 'fold', 'Sample ID', 'Patient ID',
                      'true_subtype', 'predicted_subtype']


def atomic_bytes(path, payload):
    """Replace a projection atomically; originals and immutable checkpoints never use this."""
    path = Path(path)
    temporary = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    try:
        with temporary.open('xb') as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def publish_new(source, destination):
    """Publish closed bytes without overwriting, including filesystems without links.

    All publishers reserve the destination. A crash may leave this reservation;
    it is never stolen automatically. Copy fallback uses a same-directory staged
    file and atomic rename while holding the reservation.
    """
    source, destination = Path(source), Path(destination)
    reservation = destination.with_name(destination.name + '.publish-lock')
    reservation.mkdir()  # Exclusive across cooperating publishers, on Windows too.
    temporary = destination.with_name(destination.name + '.' + uuid.uuid4().hex + '.tmp')
    try:
        if destination.exists() or destination.is_symlink():
            raise FileExistsError(f'Publication target exists: {destination}')
        try:
            os.link(source, destination)
        except OSError as error:
            if error.errno not in {errno.EXDEV, errno.EPERM, errno.EACCES,
                                   errno.ENOSYS, errno.ENOTSUP, errno.EOPNOTSUPP}:
                raise
            with source.open('rb') as incoming, temporary.open('xb') as outgoing:
                shutil.copyfileobj(incoming, outgoing)
                outgoing.flush()
                os.fsync(outgoing.fileno())
            if destination.exists() or destination.is_symlink():
                raise FileExistsError(f'Publication target exists: {destination}')
            os.rename(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)
        reservation.rmdir()


def atomic_json(path, value):
    atomic_bytes(path, (json.dumps(value, indent=2, allow_nan=False) + '\n').encode('utf-8'))


@contextmanager
def writer_lock(batch):
    """An exclusive reservation prevents two processes from resuming the same batch."""
    path = Path(batch) / '.writer.lock'
    try:
        with path.open('x', encoding='utf-8') as stream:
            json.dump(dict(pid=os.getpid(), created_utc=now()), stream)
    except FileExistsError as error:
        raise ValueError(f'Writer lock exists: {path}. Confirm its process has stopped, then use unlock --batch PATH --pid PID.') from error
    try:
        yield
    finally:
        path.unlink(missing_ok=True)


def unlock(batch, pid):
    path = Path(batch) / '.writer.lock'
    record = read_json(path)
    require(record['pid'] == pid, 'Lock PID does not match')
    # Windows os.kill(pid, 0) can terminate a process instead of probing it.
    # Keep stale-lock recovery explicit there; normal lock release works on every platform.
    if os.name == 'nt':
        raise ValueError('On Windows, verify the writer has stopped in Task Manager, then remove only .writer.lock manually. No process was signalled.')
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        path.unlink()
    except PermissionError as error:
        raise ValueError('Cannot establish that the writer stopped; lock retained') from error
    else:
        raise ValueError('Writer process is still alive; lock retained')


def create_batch(path, configurations, settings, proof, preflight, smoke=False):
    path = Path(path)
    # New batches may only be created in the designated generated-results namespaces.
    namespace = common.ROOT / 'results' / ('protocol2-smoke' if smoke else 'protocol2')
    require(path.resolve().is_relative_to(namespace.resolve()), f'New batches must be below {namespace}')
    path.mkdir(parents=True, exist_ok=False)
    manifest = dict(workflow_version=WORKFLOW_VERSION, protocol_version=settings['protocol_version'],
                    batch_id=path.name, created_utc=now(), updated_utc=now(), status='created',
                    mode='smoke' if smoke else 'official', evidence_origin='new_experiment',
                    provenance=proof, configurations=[c['id'] for c in configurations], runs={},
                    peer_review='pending', settings=settings)
    atomic_json(path / 'experiment_manifest.json', manifest)
    atomic_json(path / 'preflight_report.json', preflight)
    atomic_json(path / 'data_checksums.json', preflight['data_checksums'])
    atomic_json(path / 'split_checksums.json', preflight['split_checksums'])
    env = dict(python=proof['python'], operating_system=proof['operating_system'],
               machine=proof['machine'], packages=proof['packages'],
               environment_packages=proof['environment_packages'], numeric_libraries=proof['numeric_libraries'])
    atomic_bytes(path / 'environment.txt', (json.dumps(env, indent=2) + '\n').encode())
    return manifest


def load_checkpoints(folder, configuration, settings, context):
    data, features, values, outer, _, _ = context
    manifest = read_json(folder / 'run_manifest.json')
    blocks = []
    for path in sorted((folder / '.checkpoints').glob('*.json')):
        envelope = read_json(path)
        content = json.dumps(envelope['block'], sort_keys=True, allow_nan=False).encode()
        import hashlib
        require(hashlib.sha256(content).hexdigest() == envelope['sha256'], 'Checkpoint checksum mismatch')
        require(envelope['run_id'] == manifest['run_id'], 'Checkpoint run ID mismatch')
        block = envelope['block']
        require(path.name == f"r{block['fold']['repeat']}-f{block['fold']['fold']}.json", 'Checkpoint filename mismatch')
        validate_block(block, configuration, settings, data, features, values, outer)
        blocks.append(block)
    require(len({(b['fold']['repeat'], b['fold']['fold']) for b in blocks}) == len(blocks), 'Duplicate checkpoints')
    return blocks


def save_checkpoint(folder, block, run_id):
    import hashlib
    path = folder / '.checkpoints' / f"r{block['fold']['repeat']}-f{block['fold']['fold']}.json"
    content = json.dumps(block, sort_keys=True, allow_nan=False).encode()
    envelope = dict(run_id=run_id, sha256=hashlib.sha256(content).hexdigest(), block=block)
    temporary = path.with_suffix('.tmp')
    try:
        atomic_json(temporary, envelope)
        publish_new(temporary, path)  # Immutable commit point, refuses replacement.
    finally:
        temporary.unlink(missing_ok=True)


def submission(configuration, manifest):
    return (f"# Protocol 2.0 submission draft\n\nConfiguration: {configuration['id']}\n\n"
            f"Run ID: {manifest['run_id']}\n\nCode commit: {manifest['git_commit']}\n\n"
            f"Execution mode: {manifest['mode']}\n\nStatus: see sealed run_manifest.json.\n\n"
            f"Completed fold runtime: {manifest.get('total_fold_runtime_seconds', 0):.6f} seconds.\n\n"
            f"Experiment owner: {configuration['owner']}; execution operator: Vy (Vỹ).\n\n"
            "New experiment evidence; no historical run is replaced.\n\n"
            "Automated validation is distinct from human review. Peer approval: pending.\n")


def project(folder, configuration, settings, manifest, blocks):
    """Rebuild the legacy-compatible files from committed fold transactions."""
    blocks = sorted(blocks, key=lambda b: (b['fold']['repeat'], b['fold']['fold']))
    manifest['folds'] = [b['fold'] for b in blocks]
    manifest['updated_utc'] = now()
    predictions = [row for b in blocks for row in b['predictions']]
    atomic_json(folder / 'feature_details.json', [b['details'] for b in blocks])
    atomic_json(folder / 'search_results.json', [r for b in blocks for r in b['search']])
    table = pd.DataFrame(predictions, columns=PREDICTION_COLUMNS)
    atomic_bytes(folder / 'predictions.csv', table.to_csv(index=False, lineterminator='\n').encode())
    atomic_json(folder / 'metrics.json', {'status': manifest['status']} if manifest['status'] not in ('complete', 'finalizing')
                else summarize(table, settings['labels'], table['Sample ID'].drop_duplicates(), settings['validation']['n_repeats']))
    atomic_bytes(folder / 'submission.md', submission(configuration, manifest).encode('utf-8'))
    atomic_json(folder / 'run_manifest.json', manifest)


def run_configuration(folder, configuration, settings, context, proof, smoke=False):
    data, features, values, outer, inner, _ = context
    if not folder.exists():
        folder.mkdir(parents=True)
        (folder / '.checkpoints').mkdir()
        manifest = dict(proof, run_id=folder.name, configuration=configuration['id'],
                        created_utc=now(), updated_utc=now(), status='running', smoke=smoke,
                        mode='smoke' if smoke else 'official', evidence_origin='new_experiment',
                        folds=[], validation_status='pending',
                        random_seeds=dict(outer=settings['validation']['random_state'],
                                          inner=settings['inner_validation']['random_state'],
                                          pca=settings['pca']['random_state']),
                        warnings=[], attempts=[])
        atomic_json(folder / 'config.json', dict(shared=settings, configuration=configuration, smoke=smoke))
        atomic_json(folder / 'validation.json', dict(status='not_run', peer_review='pending'))
        atomic_bytes(folder / 'warnings.log', b'')
        project(folder, configuration, settings, manifest, [])
    manifest = read_json(folder / 'run_manifest.json')
    same_identity(manifest, proof)
    require(manifest['mode'] == ('smoke' if smoke else 'official'), 'Cannot mix smoke and official runs')
    require(read_json(folder / 'config.json') == dict(shared=settings, configuration=configuration, smoke=smoke), 'Run configuration changed')
    require(not manifest.get('warnings') and (folder / 'warnings.log').stat().st_size == 0,
            'Warning-bearing run requires review; resume will not erase warnings')
    if manifest['status'] == 'complete':
        validate_run(folder, settings, data, outer, proof)
        return
    require(manifest['status'] != 'smoke_only', 'Completed smoke cannot become official')
    blocks = load_checkpoints(folder, configuration, settings, context)
    done = {(b['fold']['repeat'], b['fold']['fold']) for b in blocks}
    manifest['attempts'].append(dict(started_utc=now(), reused_folds=len(done)))
    attempt_started = time.perf_counter()
    if manifest['status'] == 'finalizing':
        expected = {(r, f) for r, f, _, _ in fold_indices(outer, data)}
        require(done == expected, 'Finalizing run is missing committed checkpoints; investigate without refitting')
    else:
        manifest['status'] = 'running'
    project(folder, configuration, settings, manifest, blocks)
    try:
        for repeat, fold, train, test in fold_indices(outer, data):
            if (repeat, fold) in done:
                continue
            started = time.perf_counter()
            caught = []
            try:
                cv = svm.inner_indices(data.iloc[train], inner, repeat, fold)
                with threadpool_limits(limits=settings['blas_threads']), warnings.catch_warnings(record=True) as caught:
                    warnings.simplefilter('always')
                    search = svm.fit_search(configuration, settings, values[train], data.iloc[train].subtype, cv)
                    predicted = search.predict(values[test])
                require(not caught, 'Search/prediction warnings require review')
            finally:
                if caught:
                    manifest['warnings'].extend(f'{w.category.__name__}: {w.message}' for w in caught)
                    atomic_bytes(folder / 'warnings.log', ('\n'.join(manifest['warnings']) + '\n').encode())
            record = dict(repeat=repeat, fold=fold, status='complete', train_samples=len(train), test_samples=len(test),
                          best_params=search.best_params_, best_inner_score=float(search.best_score_),
                          search_candidates=len(search.cv_results_['params']), inner_folds=len(cv),
                          runtime_seconds=time.perf_counter() - started)
            details = dict(repeat=repeat, fold=fold, **feature_details(search.best_estimator_, features))
            tuning = [dict(repeat=repeat, fold=fold, candidate=i, params=params,
                           scores=[float(search.cv_results_[f'split{j}_test_score'][i]) for j in range(len(cv))],
                           mean_score=float(search.cv_results_['mean_test_score'][i]))
                      for i, params in enumerate(search.cv_results_['params'])]
            predictions = [dict(configuration=configuration['id'], repeat=repeat, fold=fold,
                                **{'Sample ID': data.iloc[i]['Sample ID'], 'Patient ID': data.iloc[i]['Patient ID'],
                                   'true_subtype': data.iloc[i].subtype, 'predicted_subtype': label})
                           for i, label in zip(test, predicted)]
            block = dict(fold=record, details=details, search=tuning, predictions=predictions)
            validate_block(block, configuration, settings, data, features, values, outer)
            save_checkpoint(folder, block, manifest['run_id'])
            blocks.append(block)
            project(folder, configuration, settings, manifest, blocks)
            print(f"{configuration['id']} repeat={repeat} fold={fold}: complete ({len(blocks)}/15)", flush=True)
            if smoke:
                break
        manifest['status'] = 'smoke_only' if smoke else 'finalizing'
        manifest['completed_utc'] = now()
        manifest['attempts'][-1].update(completed_utc=now(), elapsed_seconds=time.perf_counter() - attempt_started)
        manifest['total_fold_runtime_seconds'] = sum(b['fold']['runtime_seconds'] for b in blocks)
        atomic_json(folder / 'run_manifest.json', manifest)
        project(folder, configuration, settings, manifest, blocks)
        if smoke:
            report = dict(status='smoke_only', official_valid=False, completed_folds=len(blocks),
                          predictions=sum(len(b['predictions']) for b in blocks),
                          checkpoint_checks='passed', limitation='One outer fold only; no official performance claim.')
        else:
            _, _, report = validate_run(folder, settings, data, outer, proof, finalizing=True)
        manifest['validation_status'] = report['status']
        atomic_json(folder / 'validation.json', report)
        manifest['artifact_sha256'] = {name: common.sha256(folder / name) for name in REQUIRED
                                      if name != 'run_manifest.json'}
        manifest['status'] = 'smoke_only' if smoke else 'complete'
        atomic_json(folder / 'run_manifest.json', manifest)
    except (Exception, KeyboardInterrupt) as error:
        persisted = read_json(folder / 'run_manifest.json')
        if persisted.get('status') == 'complete':
            raise
        manifest['status'] = ('finalizing' if persisted.get('status') == 'finalizing'
                              or manifest['status'] == 'finalizing' else 'incomplete')
        manifest['validation_status'] = 'failed' if not isinstance(error, KeyboardInterrupt) else 'not_run'
        manifest['attempts'][-1].update(stopped_utc=now(), elapsed_seconds=time.perf_counter() - attempt_started,
                                        error=f'{type(error).__name__}: {error}')
        project(folder, configuration, settings, manifest, blocks)
        atomic_json(folder / 'validation.json', dict(status='incomplete', official_valid=False,
                                                    error=f'{type(error).__name__}: {error}'))
        raise


def execute(batch, settings, context, proof, resume=False):
    batch = Path(batch)
    initial = read_json(batch / 'experiment_manifest.json')
    require(initial.get('workflow_version') == WORKFLOW_VERSION and initial.get('evidence_origin') == 'new_experiment',
            'Not a managed new experiment batch')
    selected = initial['configurations']
    known = {c['id'] for c in settings['configurations']}
    require(selected and len(selected) == len(set(selected)) and set(selected).issubset(known), 'Invalid/duplicate configuration plan')
    require(set(initial['runs']).issubset(selected) and len(set(initial['runs'].values())) == len(initial['runs']),
            'Invalid/duplicate run mapping')
    for identifier, relative in initial['runs'].items():
        path = Path(relative)
        require(len(path.parts) == 3 and path.parts[:2] == ('runs', identifier)
                and (batch / path).resolve().is_relative_to((batch / 'runs').resolve())
                and (batch / path).resolve().is_relative_to(batch.resolve()), 'Run path escapes batch')
    registered = {(batch / relative).resolve() for relative in initial['runs'].values()}
    require(all(p.resolve() in registered for p in (batch / 'runs').glob('*/*') if p.is_dir()), 'Unregistered run folder; investigate before resume')
    with writer_lock(batch):
        manifest = read_json(batch / 'experiment_manifest.json')
        require(manifest['settings'] == settings, 'Batch settings differ from Protocol 2.0')
        same_identity(manifest['provenance'], proof)
        require(resume or manifest['status'] == 'created', 'Batch exists; use resume')
        manifest['status'] = 'running'
        atomic_json(batch / 'experiment_manifest.json', manifest)
        try:
            for identifier in manifest['configurations']:
                configuration = next(c for c in settings['configurations'] if c['id'] == identifier)
                if identifier not in manifest['runs']:
                    run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex[:12]
                    manifest['runs'][identifier] = f'runs/{identifier}/{run_id}'
                    atomic_json(batch / 'experiment_manifest.json', manifest)
                run_configuration(batch / manifest['runs'][identifier], configuration, settings, context, proof,
                                  smoke=manifest['mode'] == 'smoke')
            manifest['status'] = 'smoke_only' if manifest['mode'] == 'smoke' else 'complete'
        except BaseException:
            manifest['status'] = 'incomplete'
            raise
        finally:
            manifest['updated_utc'] = now()
            atomic_json(batch / 'experiment_manifest.json', manifest)


def status(batch):
    manifest = read_json(Path(batch) / 'experiment_manifest.json')
    rows = []
    for identifier in manifest['configurations']:
        relative = manifest['runs'].get(identifier)
        path = Path(batch) / relative / 'run_manifest.json' if relative else None
        run = read_json(path) if path and path.exists() else {}
        rows.append(dict(configuration=identifier, run_id=run.get('run_id'), status=run.get('status', 'not_started'),
                         committed_folds=len(list(path.parent.glob('.checkpoints/*.json'))) if path and path.exists() else 0,
                         validation_status=run.get('validation_status', 'not_run')))
    return dict(batch=str(batch), status=manifest['status'], mode=manifest['mode'],
                writer_lock=(Path(batch) / '.writer.lock').exists(), configurations=rows)
