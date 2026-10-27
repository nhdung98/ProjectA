"""Prediction-based descriptive reports and explicit team/external evidence exports."""
import json
import hashlib
import re
from pathlib import Path
import uuid
import zipfile

import pandas as pd

from . import common
from .workflow_checks import (REQUIRED, REFERENCE, WORKFLOW_VERSION, now, read_json,
                              require, same_identity, validate_run)
from .workflow_run import atomic_bytes, atomic_json, publish_new

AGGREGATES = ('summary.csv', 'comparison.csv', 'experiment_manifest.json', 'environment.txt',
              'data_checksums.json', 'split_checksums.json', 'preflight_report.json',
              'validation_summary.json', 'run_register.csv', 'reports/model_comparison.md',
              'reports/subtype_analysis.csv', 'reports/confusion_matrices.csv',
              'reports/repeat_scores.csv')


def validate_batch(batch, settings, context, proof):
    batch = Path(batch)
    manifest = read_json(batch / 'experiment_manifest.json')
    require(manifest.get('workflow_version') == WORKFLOW_VERSION, 'Unsupported batch')
    require(manifest['mode'] == 'official' and manifest['status'] == 'complete', 'Incomplete/smoke batch is not official evidence')
    require(manifest['settings'] == settings, 'Batch configuration changed')
    same_identity(manifest['provenance'], proof)
    selected = manifest['configurations']
    require(len(selected) == len(set(selected)) and set(manifest['runs']) == set(selected), 'Missing/duplicate selected runs')
    require(set(selected).issubset({c['id'] for c in settings['configurations']}), 'Unknown configuration')
    actual = {p.parent.resolve() for p in (batch / 'runs').glob('*/*/run_manifest.json')}
    expected = {(batch / p).resolve() for p in manifest['runs'].values()}
    require(all(all((folder / name).is_file() for name in REQUIRED) for folder in expected),
            'Missing required Protocol 2.0 artifacts')
    require(len(expected) == len(selected) and actual == expected, 'Unregistered/duplicate run folders')
    identifiers, results = set(), {}
    for identifier in selected:
        folder = (batch / manifest['runs'][identifier]).resolve()
        require(folder.is_relative_to(batch.resolve()) and folder.is_relative_to((batch / 'runs').resolve()), 'Run path escapes batch')
        run = read_json(folder / 'run_manifest.json')
        require(run['configuration'] == identifier and run['run_id'] not in identifiers, 'Duplicate run ID/configuration')
        identifiers.add(run['run_id'])
        results[identifier] = validate_run(folder, settings, context[0], context[3], proof)
    return manifest, results


def csv_output(path, rows, columns):
    frame = pd.DataFrame(rows, columns=columns)
    atomic_bytes(path, frame.to_csv(index=False, lineterminator='\n').encode('utf-8'))
    return frame


def report_batch(batch, settings, context, proof):
    batch = Path(batch)
    manifest, validated = validate_batch(batch, settings, context, proof)
    (batch / 'reports').mkdir(exist_ok=True)
    summary, repeats, subtypes, confusions, register = [], [], [], [], []
    reports = {}
    for configuration in settings['configurations']:
        identifier = configuration['id']
        if identifier not in validated:
            continue
        _, metrics, audit = validated[identifier]
        reports[identifier] = audit
        folder = batch / manifest['runs'][identifier]
        run = read_json(folder / 'run_manifest.json')
        row = dict(configuration=identifier, scaler=configuration['scaler'], reduction=configuration['reduction'],
                   components_or_genes=configuration['k'], kernel=configuration['kernel'], run_id=run['run_id'],
                   runtime_seconds=sum(f['runtime_seconds'] for f in run['folds']), validation_status='passed',
                   git_commit=run['git_commit'], peer_review='pending')
        for metric in ('macro_f1', 'balanced_accuracy'):
            row[metric + '_mean'] = metrics['summary'][metric]['mean']
            row[metric + '_sd'] = metrics['summary'][metric]['sample_std']
        summary.append(row)
        register.append(dict(configuration=identifier, run_id=run['run_id'], code_commit=run['git_commit'],
                             status='pending_review', automated_validation='passed', path=manifest['runs'][identifier],
                             evidence_origin='new_experiment'))
        for repeat in metrics['repeats']:
            repeats.append(dict(configuration=identifier, repeat=repeat['repeat'], macro_f1=repeat['macro_f1'],
                                balanced_accuracy=repeat['balanced_accuracy']))
            for label, values in repeat['per_class'].items():
                subtypes.append(dict(configuration=identifier, repeat=repeat['repeat'], subtype=label, **values))
            for i, true in enumerate(settings['labels']):
                for j, predicted in enumerate(settings['labels']):
                    confusions.append(dict(configuration=identifier, repeat=repeat['repeat'], true_subtype=true,
                                           predicted_subtype=predicted, count=repeat['confusion_matrix'][i][j]))
    columns = ['configuration', 'scaler', 'reduction', 'components_or_genes', 'kernel', 'run_id',
               'macro_f1_mean', 'macro_f1_sd', 'balanced_accuracy_mean', 'balanced_accuracy_sd',
               'runtime_seconds', 'validation_status', 'git_commit', 'peer_review']
    scores = csv_output(batch / 'summary.csv', summary, columns)
    comparisons = []
    reference = next((row for row in summary if row['configuration'] == REFERENCE), None)
    for row in summary:
        comparisons.append(dict(configuration=row['configuration'], reference=REFERENCE,
                                reference_available=reference is not None,
                                macro_f1_delta=None if reference is None else row['macro_f1_mean'] - reference['macro_f1_mean'],
                                balanced_accuracy_delta=None if reference is None else row['balanced_accuracy_mean'] - reference['balanced_accuracy_mean'],
                                comparison_type='exploratory_descriptive'))
    csv_output(batch / 'comparison.csv', comparisons, ['configuration', 'reference', 'reference_available',
               'macro_f1_delta', 'balanced_accuracy_delta', 'comparison_type'])
    csv_output(batch / 'run_register.csv', register, ['configuration', 'run_id', 'code_commit', 'status',
               'automated_validation', 'path', 'evidence_origin'])
    csv_output(batch / 'reports/subtype_analysis.csv', subtypes,
               ['configuration', 'repeat', 'subtype', 'precision', 'recall', 'f1', 'support'])
    csv_output(batch / 'reports/confusion_matrices.csv', confusions,
               ['configuration', 'repeat', 'true_subtype', 'predicted_subtype', 'count'])
    csv_output(batch / 'reports/repeat_scores.csv', repeats,
               ['configuration', 'repeat', 'macro_f1', 'balanced_accuracy'])
    lines = ['# Protocol 2.0 descriptive model comparison', '',
             f'Validated configurations: {len(validated)}/24. Human peer review: pending.', '',
             f'Reference: {REFERENCE}. ' + ('Available in this batch.' if reference else
             'Not in this subset; differences are left empty. Historical scores are not substituted.'), '',
             'Macro-F1 is primary. SD is sample SD across three complete repeat scores. '
             'Repeats reuse the same 254 patients and overlapping training sets; folds and repeats '
             'are not independent observations. SD is not a confidence interval. No t-tests, '
             'significance claims or preregistered statistical tests are performed.', '',
             'This is an exploratory comparison. Selecting a winner from these outer scores '
             'does not give an unbiased estimate of the selected model. Read subtype and confusion '
             'tables, especially MFS/UPS errors and SS/MPNST with only 10/9 patients. '
             'Keep this round separate from later Protocol 3.0 analyses.', '',
             '| Configuration | Macro-F1 mean | SD | Balanced accuracy |',
             '| --- | ---: | ---: | ---: |']
    for row in scores.sort_values('macro_f1_mean', ascending=False).to_dict('records'):
        lines.append(f"| {row['configuration']} | {row['macro_f1_mean']:.6f} | {row['macro_f1_sd']:.6f} | {row['balanced_accuracy_mean']:.6f} |")
    lines += ['', 'See subtype_analysis.csv, confusion_matrices.csv and repeat_scores.csv. '
              'Runtime reflects this machine and local execution conditions.', '',
              'evidence_bundle.zip is for external review and contains aggregate evidence only. '
              'It omits patient-level predictions, fold checkpoints and run artifacts. '
              'The local runs/ tree holds all nine original artifacts. '
              'An explicit team export includes original Protocol-required identifiers and must stay in the approved team channel.']
    atomic_bytes(batch / 'reports/model_comparison.md', ('\n'.join(lines) + '\n').encode())
    files = {name: common.sha256(batch / name) for name in AGGREGATES if name != 'validation_summary.json'}
    for relative in manifest['runs'].values():
        files.update({f'{relative}/{name}': common.sha256(batch / relative / name) for name in REQUIRED})
    atomic_json(batch / 'validation_summary.json', dict(status='passed', checked_utc=now(),
                configurations=len(validated), full_24_comparison=len(validated) == 24,
                peer_review='pending', runs=reports, export_files=files))
    return scores


def external_copy(value):
    """Sanitize copies only; no local paths are necessary for aggregate review."""
    if isinstance(value, dict):
        return {key: external_copy(item) for key, item in value.items()
                if key != 'python_executable'}
    if isinstance(value, list):
        return [external_copy(item) for item in value]
    if isinstance(value, str) and (value.startswith(('/', '\\')) or re.match(r'^[A-Za-z]:[\\/]', value)):
        return '<redacted-local-path>'
    return value


def verify_bundle(path):
    """Read-only ZIP verification, independent of the executing machine/environment.

    The inventory covers every entry except itself (no circular hash). This is
    corruption detection, not a signature or proof of execution authenticity.
    """
    try:
        with zipfile.ZipFile(path) as archive:
            names = archive.namelist()
            require(len(names) == len(set(names)), 'Duplicate ZIP entries')
            require('EXPORT_CHECKSUMS.json' in names, 'Missing ZIP checksum inventory')
            inventory = json.loads(archive.read('EXPORT_CHECKSUMS.json'))
            require(inventory.get('schema_version') == 1 and inventory.get('audience') in ('external', 'team'),
                    'Unsupported ZIP inventory')
            hashes = inventory['entry_sha256']
            require(set(hashes) == set(names) - {'EXPORT_CHECKSUMS.json'}, 'Missing or unexpected ZIP entries')
            for name, expected in hashes.items():
                require(not name.startswith(('/', '\\')) and '\\' not in name
                        and ':' not in name and '..' not in name.split('/'), 'Unsafe ZIP entry path')
                require(hashlib.sha256(archive.read(name)).hexdigest() == expected,
                        f'ZIP entry checksum mismatch: {name}')
            require(archive.testzip() is None, 'Corrupt ZIP')
        return dict(status='passed', audience=inventory['audience'], verified_entries=len(hashes),
                    zip_sha256=common.sha256(path), limitation='Checksums are not signatures.')
    except (zipfile.BadZipFile, KeyError, json.JSONDecodeError) as error:
        raise ValueError(f'Invalid evidence ZIP: {error}') from error


def export_bundle(batch, audience='external', output=None):
    """Build immutable audience-specific snapshots and hash their exact payloads."""
    batch = Path(batch)
    manifest = read_json(batch / 'experiment_manifest.json')
    validation = read_json(batch / 'validation_summary.json')
    require(manifest['status'] == 'complete' and manifest['mode'] == 'official'
            and validation['status'] == 'passed', 'Only validated official batches can be exported')
    require(audience in ('external', 'team'), 'Unknown evidence audience')
    paths = [Path(name) for name in AGGREGATES]
    if audience == 'team':
        for relative in manifest['runs'].values():
            paths.extend(Path(relative) / name for name in REQUIRED)
    require(all((batch / p).is_file() and not (batch / p).is_symlink()
                and (batch / p).resolve().is_relative_to(batch.resolve()) for p in paths), 'Missing or linked export file')
    source_hashes = validation.get('export_files', {})
    expected_sources = set(AGGREGATES) - {'validation_summary.json'}
    expected_sources.update(f'{relative}/{name}' for relative in manifest['runs'].values() for name in REQUIRED)
    require(set(source_hashes) == expected_sources, 'Incomplete source checksum inventory')
    for relative, digest in source_hashes.items():
        require(common.sha256(batch / relative) == digest, f'Export input changed: {relative}')
    destination = Path(output) if output else batch / ('evidence_bundle.zip' if audience == 'external' else 'team_evidence_bundle.zip')
    require(destination.resolve().parent == batch.resolve() and destination.suffix == '.zip',
            'Export output must be a new .zip directly inside the batch')
    require(not destination.exists(), f'Bundle already exists: {destination}; choose a new --output snapshot')
    payloads = {}
    for relative in paths:
        name = relative.as_posix()
        payload = (batch / relative).read_bytes()
        if name in source_hashes:
            require(hashlib.sha256(payload).hexdigest() == source_hashes[name], f'Export input changed: {name}')
        if audience == 'external' and (name.endswith('.json') or name == 'environment.txt'):
            value = json.loads(payload)
            if name == 'experiment_manifest.json':
                value.pop('runs', None)
            if name == 'validation_summary.json':
                value['source_artifact_sha256'] = value.pop('export_files')
            payload = (json.dumps(external_copy(value), indent=2, allow_nan=False) + '\n').encode('utf-8')
        payloads[name] = payload
    payloads['EXPORT_NOTICE.txt'] = (
        'External aggregate review; patient-level artifacts omitted.\n' if audience == 'external' else
        'PRIVATE TEAM EVIDENCE: includes Protocol 2.0 sample and patient IDs; do not upload to external AI services.\n').encode('utf-8')
    inventory = dict(schema_version=1, audience=audience,
                     source_artifact_sha256={p.as_posix(): common.sha256(batch / p) for p in paths},
                     entry_sha256={name: hashlib.sha256(payload).hexdigest() for name, payload in payloads.items()},
                     exclusions=['EXPORT_CHECKSUMS.json'],
                     note='Source hashes describe original local files; entry hashes describe exact exported bytes. Inventory is not self-hashed or signed.')
    payloads['EXPORT_CHECKSUMS.json'] = (json.dumps(inventory, indent=2) + '\n').encode('utf-8')
    temporary = batch / ('.bundle-' + uuid.uuid4().hex + '.tmp')
    try:
        with zipfile.ZipFile(temporary, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
            for name, payload in payloads.items():
                archive.writestr(name, payload)
        # Flush the closed archive before immutable publication.
        import os
        with temporary.open('r+b') as stream:
            stream.flush()
            os.fsync(stream.fileno())
        verify_bundle(temporary)
        publish_new(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)
    return destination
