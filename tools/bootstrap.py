"""Offline Windows bootstrap. Only Python standard library is needed initially."""
import hashlib
import json
from pathlib import Path, PurePosixPath
import platform
import shutil
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def bootstrap(root=ROOT):
    if sys.version_info[:2] != (3, 12) or sys.platform != 'win32' or platform.machine().lower() not in ('amd64', 'x86_64'):
        raise SystemExit('Use Windows x64 and Python 3.12 x64.')
    resource_dir = root / 'offline'
    manifest = json.loads((resource_dir / 'manifest.json').read_text(encoding='utf-8'))
    temp = root / '.cache/bootstrap'
    temp.mkdir(parents=True, exist_ok=True)
    archive_path = temp / 'resources.zip'
    digest = hashlib.sha256()
    print('Verifying offline resource parts...', flush=True)
    with archive_path.open('wb') as output:
        for part in manifest['parts']:
            name = part['file']
            if Path(name).name != name:
                raise ValueError('Invalid manifest filename')
            data = (resource_dir / name).read_bytes()
            if len(data) != part['bytes'] or hashlib.sha256(data).hexdigest() != part['sha256']:
                raise ValueError(f'Corrupted or incomplete resource: {name}. Fetch it again from Git.')
            output.write(data)
            digest.update(data)
    if digest.hexdigest() != manifest['sha256']:
        raise ValueError('Combined resource hash does not match')
    with zipfile.ZipFile(archive_path) as archive:
        for entry in archive.infolist():
            p = PurePosixPath(entry.filename)
            if p.is_absolute() or '..' in p.parts or '\\' in entry.filename or ':' in entry.filename:
                raise ValueError('Unsafe archive path')
            if not (p.parts[0] in ('models', 'wheelhouse') or p.parts[:2] == ('.cache', 'tiktoken')):
                raise ValueError('Unexpected resource directory')
        archive.extractall(root)
    archive_path.unlink()
    python = root / '.venv/Scripts/python.exe'
    if not python.exists():
        subprocess.run([sys.executable, '-m', 'venv', str(root / '.venv')], check=True)
    subprocess.run([str(python), '-c', "import sys; assert sys.version_info[:2] == (3,12), 'Existing venv must use Python 3.12'"], check=True)
    subprocess.run([str(python), '-m', 'pip', 'install', '--disable-pip-version-check', '--no-index', '--find-links', str(root / 'wheelhouse'), '-r', str(root / 'requirements-win-py312.lock')], check=True, cwd=root)
    subprocess.run([str(python), '-m', 'pip', 'check'], check=True, cwd=root)
    if not (root / 'config.json').exists():
        shutil.copyfile(root / 'config.example.json', root / 'config.json')
    subprocess.run([str(python), str(root / 'tools/doctor.py')], check=True, cwd=root)
    print('Offline install complete. Existing config and documents were preserved.', flush=True)


if __name__ == '__main__':
    bootstrap()
