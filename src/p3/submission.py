"""One automatic result archive for each member command, including failed runs."""
from contextlib import contextmanager
from datetime import datetime, timezone
import json
import uuid
from zipfile import ZIP_DEFLATED, ZipFile


@contextmanager
def member_submission(folder, round_name, member, requested):
    folder.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex[:8]
    path = folder / f'round{round_name}-member{member}-{stamp}.zip'
    outputs = []
    summary = dict(round=round_name, member=member, requested=requested, status='failed', pipelines=[])
    try:
        yield outputs
        summary['status'] = 'complete'
    except BaseException as error:
        summary['error'] = f'{type(error).__name__}: {error}'
        raise
    finally:
        with ZipFile(path, 'x', compression=ZIP_DEFLATED) as archive:
            for destination in outputs:
                manifest = destination / 'manifest.json'
                status = 'incomplete'
                if manifest.exists():
                    try:
                        status = json.loads(manifest.read_text(encoding='utf-8')).get('status', 'incomplete')
                    except (ValueError, OSError):
                        pass
                summary['pipelines'].append(dict(pipeline=destination.name, status=status))
                if destination.exists():
                    for item in sorted(destination.rglob('*')):
                        if item.is_file():
                            archive.write(item, destination.name + '/' + item.relative_to(destination).as_posix())
            archive.writestr('submission_summary.json', json.dumps(summary, ensure_ascii=False, indent=2))
        print(f'SUBMISSION RESULTS ({summary["status"]}): {path.resolve()}', flush=True)
