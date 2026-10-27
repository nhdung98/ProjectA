"""Unified Protocol 2.0 interface. Official fitting is an explicit run/resume action."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import tempfile
import uuid

from . import common, svm
from .workflow_checks import (WORKFLOW_VERSION, identity, preflight, read_json, require)
from .workflow_run import (atomic_json, create_batch, execute, status, unlock, writer_lock, publish_new)
from .workflow_report import export_bundle, report_batch, validate_batch, verify_bundle

BRANCHES = {'minmax-anova': ('minmax', 'anova'), 'standard-anova': ('standard', 'anova'),
            'minmax-pca': ('minmax', 'pca'), 'standard-pca': ('standard', 'pca')}


def managed_batch(path):
    path = Path(path).resolve()
    allowed = [common.ROOT / 'results' / name for name in ('protocol2', 'protocol2-smoke')]
    require(any(path.is_relative_to(p.resolve()) and path != p.resolve() for p in allowed),
            'Batch must be in results/protocol2/ or results/protocol2-smoke/; historical folders cannot be modified')
    manifest = read_json(path / 'experiment_manifest.json')
    require(manifest.get('workflow_version') == WORKFLOW_VERSION
            and manifest.get('evidence_origin') == 'new_experiment', 'Not a managed new experiment batch')
    return path


def prepare_data(settings):
    """Explicitly prepare new files, verify frozen bytes first, never rewrite an existing file."""
    from src.data.audit import load_config
    from src.data.prepare import prepare
    common.verify_environment(settings)
    for relative, digest in settings['source_sha256'].items():
        require(common.sha256(common.ROOT / relative) == digest, f'Raw hash mismatch: {relative}')
    config = load_config()
    destination = config['processed_dir']
    target = common.ROOT / settings['dataset']
    expected = read_json(common.SPLIT_MANIFEST)['dataset_sha256']
    if target.exists():
        require(common.sha256(target) == expected, 'Existing dataset hash differs. Preserve and investigate it; no overwrite performed.')
        return dict(status='already_present', dataset_sha256=expected)
    with tempfile.TemporaryDirectory(prefix='protocol2-prepare-', dir=common.ROOT / 'data') as temporary:
        config['processed_dir'] = Path(temporary)
        prepare(config, lineterminator='\r\n')
        source = Path(temporary) / target.name
        actual = common.sha256(source)
        require(actual == expected, f'Prepared bytes differ: {actual}; expected {expected}. Nothing published; splits unchanged.')
        files = list(Path(temporary).iterdir())
        require(all(not (destination / p.name).exists() for p in files), 'Prepared output already exists; no overwrites allowed')
        destination.mkdir(parents=True, exist_ok=True)
        # Publish canonical training data last. A failed ancillary publish cannot create a ready dataset.
        for p in sorted(files, key=lambda p: p.name == target.name):
            publish_new(p, destination / p.name)
    return dict(status='prepared_and_hash_verified', dataset_sha256=actual,
                serialization='Explicit CRLF matches existing frozen Protocol 2.0 dataset checksum; split manifests unchanged')


def selection(args, settings):
    if getattr(args, 'configuration', None):
        require(len(args.configuration) == len(set(args.configuration)), 'Duplicate configuration request')
        lookup = {c['id']: c for c in settings['configurations']}
        require(set(args.configuration).issubset(lookup), 'Unknown configuration ID')
        return [lookup[c] for c in args.configuration]
    if getattr(args, 'branch', None):
        scaler, reduction = BRANCHES[args.branch]
        return [c for c in settings['configurations'] if (c['scaler'], c['reduction']) == (scaler, reduction)]
    return settings['configurations']


def check_context(settings, official):
    report, context = preflight(settings, official=official)
    require(report['status'] == 'passed' and context is not None,
            'Preflight failed:\n' + '\n'.join(report['errors']))
    return report, context, identity(settings, context[-1])


def finish(batch, settings, context, proof, bundle=False, audience='external', output=None):
    with writer_lock(batch):
        report_batch(batch, settings, context, proof)
        if bundle:
            destination = export_bundle(batch, audience=audience, output=output)
            print(f'Evidence ZIP ({audience}): {destination}', flush=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('list')
    command = commands.add_parser('verify-export', help='Read-only ZIP byte-integrity check; no training or local provenance required')
    command.add_argument('--zip', type=Path, required=True)
    commands.add_parser('prepare-data', help='Explicit, no-overwrite preparation with frozen hash verification')
    command = commands.add_parser('preflight', help='Read-only scientific/data checks; optional JSON report')
    command.add_argument('--official', action='store_true', help='Also require a clean committed release')
    command.add_argument('--output', type=Path)
    for name in ('run', 'smoke'):
        command = commands.add_parser(name)
        command.add_argument('--batch', type=Path)
        if name == 'run':
            choice = command.add_mutually_exclusive_group(required=True)
            choice.add_argument('--configuration', action='append')
            choice.add_argument('--branch', choices=BRANCHES)
            choice.add_argument('--all', action='store_true')
        else:
            command.add_argument('--configuration', action='append', default=None)
    for name in ('resume', 'validate', 'report', 'export', 'status', 'unlock'):
        command = commands.add_parser(name)
        command.add_argument('--batch', type=Path, required=True)
        if name == 'export':
            command.add_argument('--audience', choices=('external', 'team'), default='external')
            command.add_argument('--output', type=Path, help='New ZIP snapshot path directly inside the batch')
        if name == 'unlock':
            command.add_argument('--pid', type=int, required=True)
    args = parser.parse_args(argv)
    if args.command == 'verify-export':
        print(json.dumps(verify_bundle(args.zip), indent=2))
        return
    settings = svm.load_settings()
    if args.command == 'list':
        for config in settings['configurations']:
            print(config['id'])
        return
    if args.command == 'prepare-data':
        print(json.dumps(prepare_data(settings), indent=2))
        return
    if args.command == 'preflight':
        report, _ = preflight(settings, official=args.official)
        if args.output:
            path = args.output.resolve()
            require(path.is_relative_to((common.ROOT / 'results').resolve()), 'Preflight reports must be under results/')
            require(not path.exists(), 'Preflight report exists; choose a new path')
            path.parent.mkdir(parents=True, exist_ok=True)
            # Exclusive publication prevents accidental replacement of another report.
            with path.open('x', encoding='utf-8') as stream:
                json.dump(report, stream, indent=2, allow_nan=False)
        print(json.dumps(report, indent=2))
        if report['status'] != 'passed':
            raise SystemExit(1)
        return
    if args.command in ('status', 'unlock'):
        batch = managed_batch(args.batch)
        if args.command == 'unlock':
            unlock(batch, args.pid)
        else:
            print(json.dumps(status(batch), indent=2))
        return
    smoke = args.command == 'smoke'
    if args.command == 'resume':
        batch = managed_batch(args.batch)
        smoke = read_json(batch / 'experiment_manifest.json')['mode'] == 'smoke'
        require(not smoke, 'Smoke runs are diagnostics; start a new smoke rather than resuming as official')
    report, context, proof = check_context(settings, official=not smoke)
    if args.command in ('run', 'smoke'):
        configurations = selection(args, settings)
        if smoke:
            require(not args.configuration or len(configurations) == 1, 'Smoke runs exactly one configuration')
            configurations = configurations[:1]
        timestamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex[:8]
        batch = args.batch or common.ROOT / 'results' / ('protocol2-smoke' if smoke else 'protocol2') / timestamp
        create_batch(batch, configurations, settings, proof, report, smoke=smoke)
        print(f'Batch: {batch}', flush=True)
        execute(batch, settings, context, proof)
        if smoke:
            atomic_json(batch / 'validation_summary.json', dict(status='smoke_only', official_valid=False,
                        limitations='One outer fold; dirty development source allowed and recorded; no full 762-record validation.'))
        else:
            finish(batch, settings, context, proof, bundle=True)
        return
    batch = managed_batch(args.batch)
    if args.command == 'resume':
        execute(batch, settings, context, proof, resume=True)
        finish(batch, settings, context, proof, bundle=not (batch / 'evidence_bundle.zip').exists())
    elif args.command == 'validate':
        _, validated = validate_batch(batch, settings, context, proof)
        print(json.dumps(dict(status='passed', configurations=len(validated), peer_review='pending'), indent=2))
    else:
        finish(batch, settings, context, proof, bundle=args.command == 'export',
               audience=getattr(args, 'audience', 'external'), output=getattr(args, 'output', None))


if __name__ == '__main__':
    try:
        main()
    except (ValueError, AssertionError, OSError, KeyError, subprocess.SubprocessError) as error:
        raise SystemExit(f'Workflow stopped: {type(error).__name__}: {error}') from error
