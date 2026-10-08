"""Optional extraction from a tar archive; bundled inputs need no extraction."""
from pathlib import Path, PurePosixPath
import argparse
import shutil
import tarfile
from .audit import load_config

def extract(archive, config):
    target = config['expression_file']
    if target.exists():
        raise FileExistsError(f'Refusing to overwrite {target}')
    with tarfile.open(archive, 'r:*') as tar:
        candidates = [m for m in tar.getmembers() if m.isfile() and PurePosixPath(m.name).name == target.name]
        if len(candidates) != 1:
            raise ValueError(f'Expected one {target.name} member, found {len(candidates)}')
        member = candidates[0]
        if PurePosixPath(member.name).is_absolute() or '..' in PurePosixPath(member.name).parts:
            raise ValueError('Unsafe archive member path')
        target.parent.mkdir(parents=True, exist_ok=True)
        # Write only to the configured destination; archive paths never determine output paths.
        with tar.extractfile(member) as source, target.open('xb') as output:
            shutil.copyfileobj(source, output)
    return target

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--archive', required=True, type=Path)
    p.add_argument('--config')
    a = p.parse_args()
    print(extract(a.archive, load_config(a.config)))

if __name__ == '__main__':
    main()
