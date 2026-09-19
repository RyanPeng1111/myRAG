"""Split the explicit offline resource archive into regular Git blobs below 50 MiB."""
import hashlib
import json
from pathlib import Path
root = Path(__file__).resolve().parents[1]
folder = root / 'offline'
folder.mkdir(exist_ok=True)
parts = []
digest = hashlib.sha256()
with (root / 'dist/myRAG-offline-resources.zip').open('rb') as stream:
    while data := stream.read(45 * 1024 * 1024):
        name = f'resources.part{len(parts)+1:03d}'
        (folder / name).write_bytes(data)
        digest.update(data)
        parts.append({'file': name, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()})
(folder / 'manifest.json').write_text(json.dumps({'sha256': digest.hexdigest(), 'parts': parts}, indent=2), encoding='utf-8')
print(f'{len(parts)} resource parts prepared for ordinary Git; no LFS required.')
