"""Strict aggregate-only Protocol 2.0 input checks. Never import or execute ML code."""
from dataclasses import dataclass
from pathlib import Path
import hashlib
import io
import json
import re
import zipfile

import numpy as np
import pandas as pd

LABELS = ['LMS', 'DDLPS', 'UPS', 'MFS', 'SS', 'MPNST']
COUNTS = [104, 57, 49, 25, 10, 9]
CONFIGS = {f'SVM-{scale}-{reduction}-{k}-{kernel}': (scale, reduction, k, kernel)
           for scale in ('MM', 'STD') for reduction in ('ANOVA', 'PCA')
           for k in (50, 100, 150) for kernel in ('LINEAR', 'RBF')}
REFERENCE = 'SVM-STD-ANOVA-150-LINEAR'
SCHEMAS = {
    'summary.csv': ['configuration', 'scaler', 'reduction', 'components_or_genes', 'kernel', 'run_id',
                    'macro_f1_mean', 'macro_f1_sd', 'balanced_accuracy_mean', 'balanced_accuracy_sd',
                    'runtime_seconds', 'validation_status', 'git_commit', 'peer_review'],
    'comparison.csv': ['configuration', 'reference', 'reference_available', 'macro_f1_delta',
                       'balanced_accuracy_delta', 'comparison_type'],
    'reports/repeat_scores.csv': ['configuration', 'repeat', 'macro_f1', 'balanced_accuracy'],
    'reports/subtype_analysis.csv': ['configuration', 'repeat', 'subtype', 'precision', 'recall', 'f1', 'support'],
    'reports/confusion_matrices.csv': ['configuration', 'repeat', 'true_subtype', 'predicted_subtype', 'count'],
}
INPUTS = ['experiment_manifest.json', 'validation_summary.json', *SCHEMAS]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(payload):
    return hashlib.sha256(payload).hexdigest()


def safe_label(value):
    """Do not propagate user-controlled identifiers, paths or patient IDs to exports."""
    value = str(value)
    if re.fullmatch(r'[A-Za-z0-9_.-]{1,100}', value) and 'TCGA-' not in value.upper():
        return value
    return 'redacted-batch-label'


@dataclass
class Batch:
    source: Path
    batch_id: str
    commit: str
    synthetic: bool
    status: str
    overview: pd.DataFrame
    tables: dict
    hashes: dict
    warnings: list

    @property
    def valid(self):
        return self.overview.loc[self.overview.status.eq('VALIDATED'), 'configuration'].tolist()


def read_payloads(source):
    """Only read the seven aggregate inputs; ZIP verification never extracts files."""
    source = Path(source).resolve()
    if source.is_dir():
        result = {}
        for name in INPUTS:
            path = source / name
            if path.exists():
                require(not path.is_symlink() and path.resolve().is_relative_to(source), 'Linked aggregate input refused')
                result[name] = path.read_bytes()
        return result, None
    require(source.suffix.lower() == '.zip', 'Input must be a batch directory or evidence ZIP')
    with zipfile.ZipFile(source) as archive:
        names = archive.namelist()
        require(len(names) == len(set(names)), 'Duplicate ZIP entries')
        require('EXPORT_CHECKSUMS.json' in names, 'Missing export checksum inventory')
        index = json.loads(archive.read('EXPORT_CHECKSUMS.json'))
        require(index.get('schema_version') == 1, 'Unsupported export checksum schema')
        hashes = index.get('entry_sha256', {})
        require(set(hashes) == set(names) - {'EXPORT_CHECKSUMS.json'}, 'ZIP entry inventory mismatch')
        require(sum(x.file_size for x in archive.infolist()) <= 200_000_000, 'ZIP too large for aggregate reporting')
        for name, expected in hashes.items():
            require(not name.startswith(('/', '\\')) and '\\' not in name and ':' not in name
                    and '..' not in name.split('/'), 'Unsafe ZIP entry')
            require(digest(archive.read(name)) == expected, 'ZIP entry checksum mismatch')
        return {name: archive.read(name) for name in INPUTS if name in names}, hashes


def close(actual, expected):
    require(np.allclose(actual, expected, rtol=0, atol=1e-10), 'Aggregate metric inconsistency')


def check_configuration(identifier, tables, audit, commit):
    """Independently check aggregate arithmetic; no predictions are read/recomputed."""
    summary = tables['summary.csv']
    row = summary[summary.configuration.eq(identifier)]
    require(len(row) == 1, 'Missing or duplicated summary row')
    row = row.iloc[0]
    require(row.validation_status == 'passed' and audit.get('status') == 'passed', 'Run validation did not pass')
    require(audit.get('configuration') == identifier and audit.get('run_id') == row.run_id,
            'Run validation identity mismatch')
    require(audit.get('fits') == 15 and audit.get('predictions') == 762, 'Incomplete audit counts')
    require(audit.get('metrics_independently_recomputed') is True and audit.get('inner_search_checked') is True
            and audit.get('warning_log_empty') is True, 'Incomplete validation attestations')
    require(row.git_commit == commit, 'Source commit mismatch')
    scale, reduction, k, kernel = CONFIGS[identifier]
    require((row.scaler, row.reduction, row.components_or_genes, row.kernel) ==
            ('minmax' if scale == 'MM' else 'standard', reduction.lower(), k, kernel.lower()), 'Configuration metadata mismatch')
    require(np.isfinite(float(row.runtime_seconds)) and float(row.runtime_seconds) >= 0, 'Invalid runtime')
    repeats = tables['reports/repeat_scores.csv'].query('configuration == @identifier').sort_values('repeat')
    subtypes = tables['reports/subtype_analysis.csv'].query('configuration == @identifier')
    confusions = tables['reports/confusion_matrices.csv'].query('configuration == @identifier')
    require(repeats['repeat'].tolist() == [1, 2, 3], 'Missing or duplicated repeat scores')
    require(len(subtypes) == 18 and len(confusions) == 108, 'Incomplete subtype/confusion evidence')
    for repeat in (1, 2, 3):
        cells = confusions[confusions['repeat'].eq(repeat)]
        require(len(cells) == 36 and not cells.duplicated(['true_subtype', 'predicted_subtype']).any(), 'Invalid confusion cells')
        require(set(cells.true_subtype) == set(LABELS) and set(cells.predicted_subtype) == set(LABELS), 'Confusion labels mismatch')
        matrix = cells.pivot(index='true_subtype', columns='predicted_subtype', values='count').loc[LABELS, LABELS].to_numpy(float)
        require(np.isfinite(matrix).all() and (matrix >= 0).all() and (matrix == np.floor(matrix)).all(), 'Invalid confusion counts')
        require(np.array_equal(matrix.sum(axis=1), COUNTS), 'Confusion denominator mismatch')
        diagonal = matrix.diagonal()
        precision = np.divide(diagonal, matrix.sum(axis=0), out=np.zeros(6), where=matrix.sum(axis=0) != 0)
        recall = diagonal / np.array(COUNTS)
        f1 = np.divide(2 * precision * recall, precision + recall, out=np.zeros(6), where=(precision + recall) != 0)
        detail = subtypes[subtypes['repeat'].eq(repeat)]
        require(len(detail) == 6 and not detail.subtype.duplicated().any() and set(detail.subtype) == set(LABELS), 'Invalid subtype rows')
        detail = detail.set_index('subtype').loc[LABELS]
        close(detail[['precision', 'recall', 'f1', 'support']].to_numpy(float), np.array([precision, recall, f1, COUNTS]).T)
        scores = repeats[repeats['repeat'].eq(repeat)].iloc[0]
        close([scores.macro_f1, scores.balanced_accuracy], [f1.mean(), recall.mean()])
    for metric in ('macro_f1', 'balanced_accuracy'):
        values = repeats[metric].to_numpy(float)
        close([row[metric + '_mean'], row[metric + '_sd']], [values.mean(), values.std(ddof=1)])
    comparison = tables['comparison.csv'].query('configuration == @identifier')
    require(len(comparison) == 1, 'Missing or duplicated comparison row')
    comparison = comparison.iloc[0]
    require(comparison.reference == REFERENCE and comparison.comparison_type == 'exploratory_descriptive', 'Invalid comparison metadata')
    reference = summary[summary.configuration.eq(REFERENCE)]
    available = len(reference) == 1
    require(str(comparison.reference_available).lower() == str(available).lower(), 'Reference availability mismatch')
    if available:
        close([comparison.macro_f1_delta, comparison.balanced_accuracy_delta],
              [row.macro_f1_mean - reference.iloc[0].macro_f1_mean,
               row.balanced_accuracy_mean - reference.iloc[0].balanced_accuracy_mean])
    else:
        require(pd.isna(comparison.macro_f1_delta) and pd.isna(comparison.balanced_accuracy_delta), 'Invented comparison baseline')


def load_batch(source, *, allow_partial=False, allow_synthetic=False):
    payloads, export_hashes = read_payloads(source)
    require('experiment_manifest.json' in payloads, 'Missing experiment manifest')
    manifest = json.loads(payloads['experiment_manifest.json'])
    synthetic = manifest.get('evidence_origin') == 'synthetic_demo'
    require(not synthetic or allow_synthetic, 'Synthetic fixtures require --allow-synthetic')
    require(synthetic or (manifest.get('mode') == 'official' and manifest.get('evidence_origin') == 'new_experiment'),
            'Smoke/historical/unrecognized batches are not accepted as official evidence')
    require(manifest.get('protocol_version') == '2.0', 'Unsupported scientific protocol')
    settings = manifest.get('settings', {})
    require(settings.get('labels') == LABELS and settings.get('class_counts') == dict(zip(LABELS, COUNTS)), 'Protocol label order or cohort mismatch')
    plan = manifest.get('configurations', [])
    require(len(plan) == len(set(plan)) and set(plan).issubset(CONFIGS), 'Invalid configuration plan')
    require(manifest.get('provenance', {}).get('git_dirty') is False, 'Dirty source provenance refused')
    commit = manifest.get('provenance', {}).get('git_commit', '')
    require((synthetic and commit == 'SYNTHETIC-NOT-A-RELEASE') or re.fullmatch('[0-9a-f]{40}', commit), 'Invalid source commit')
    validation = json.loads(payloads.get('validation_summary.json', b'{}'))
    tables, problems = {}, []
    hashes = {name: digest(payload) for name, payload in payloads.items()}
    recorded_hashes = export_hashes if export_hashes is not None else validation.get('export_files', {})
    for name, columns in SCHEMAS.items():
        if name not in payloads:
            problems.append('Missing aggregate file: ' + name)
            tables[name] = pd.DataFrame(columns=columns)
            continue
        require(recorded_hashes.get(name) == hashes[name], 'Aggregate hash mismatch: ' + name)
        table = pd.read_csv(io.BytesIO(payloads[name]))
        require(list(table.columns) == columns, 'Unexpected columns: ' + name)
        require(table.configuration.isin(CONFIGS).all(), 'Unknown configuration in aggregate table')
        require(set(table.configuration).issubset(plan), 'Unplanned aggregate configuration')
        tables[name] = table
    if export_hashes is None and validation:
        require(recorded_hashes.get('experiment_manifest.json') == hashes['experiment_manifest.json'], 'Manifest hash mismatch')
    overview = []
    for identifier in CONFIGS:
        if identifier not in plan:
            state, reason = 'INCOMPLETE', 'Not included in batch plan'
        elif identifier not in set(tables['summary.csv'].configuration):
            audit = validation.get('runs', {}).get(identifier, {})
            state = 'INVALID' if audit.get('status') in ('failed', 'invalid') else 'INCOMPLETE'
            reason = 'Failed validation; aggregate scores unavailable' if state == 'INVALID' else 'No validated aggregate summary'
        else:
            try:
                require(not problems, 'Required aggregate evidence missing')
                check_configuration(identifier, tables, validation.get('runs', {}).get(identifier, {}), commit)
                state, reason = 'VALIDATED', 'Complete run; aggregate consistency checks passed'
            except (ValueError, TypeError, KeyError, OverflowError):
                state, reason = 'INVALID', 'Validation, identity, completeness or aggregate consistency check failed'
        overview.append(dict(configuration=identifier, status=state, reason=reason))
    full = (all(r['status'] == 'VALIDATED' for r in overview) and manifest.get('status') == 'complete'
            and validation.get('status') == 'passed' and validation.get('full_24_comparison') is True
            and validation.get('configurations') == 24)
    require(full or allow_partial, 'Batch is not fully validated; use --allow-partial for an INCOMPLETE overview')
    if not full:
        problems.append('Batch is INCOMPLETE: only individually validated, consistent runs are plotted; all 24 remain visible in the status overview.')
    problems.append('Original automated validation plus aggregate consistency checks; not a new patient-level audit. Checksums are not signatures. Human peer review is not inferred.')
    return Batch(Path(source).resolve(), safe_label(manifest.get('batch_id', 'unknown')), commit, synthetic,
                 ('SYNTHETIC DEMONSTRATION — NOT RESEARCH RESULTS' + (' · INCOMPLETE' if not full else '')) if synthetic else ('FULLY VALIDATED AGGREGATES' if full else 'INCOMPLETE'),
                 pd.DataFrame(overview), tables, hashes, problems)
