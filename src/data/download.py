"""Optional acquisition of an explicit public URL; bundled inputs need no download."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import tempfile
from urllib.parse import urlparse
from urllib.request import urlopen
from .audit import load_config

def download(url, filename, config, sha256=None):
    if urlparse(url).scheme != 'https':
        raise ValueError('Provide an HTTPS URL')
    if Path(filename).name != filename or filename in ['', '.', '..']:
        raise ValueError('Filename must be a plain file name')
    directory = config['raw_dir']
    directory.mkdir(parents=True, exist_ok=True)
    destination = directory / filename
    if destination.exists():
        raise FileExistsError(f'Refusing to overwrite {destination}')
    digest = hashlib.sha256()
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=directory, delete=False) as target:
            temporary = Path(target.name)
            with urlopen(url, timeout=60) as response:
                while chunk := response.read(1024 * 1024):
                    target.write(chunk)
                    digest.update(chunk)
        actual = digest.hexdigest()
        if sha256 and actual.lower() != sha256.lower():
            raise ValueError('Downloaded SHA-256 does not match expected hash')
        os.replace(temporary, destination)
        metadata = {'url': url, 'filename': filename, 'sha256': actual}
        (directory / (filename + '.source.json')).write_text(json.dumps(metadata, indent=2), encoding='utf-8')
        return metadata
    finally:
        if temporary and temporary.exists():
            temporary.unlink()

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--url', required=True)
    p.add_argument('--filename', required=True)
    p.add_argument('--sha256')
    p.add_argument('--config')
    a = p.parse_args()
    print(json.dumps(download(a.url, a.filename, load_config(a.config), a.sha256), indent=2))

if __name__ == '__main__':
    main()
