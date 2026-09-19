"""Create source and offline-resource archives using explicit allowlists; never include secrets/data."""
from pathlib import Path
import hashlib
import json
import zipfile

root = Path(__file__).resolve().parents[1]
out = root / "dist"
out.mkdir(exist_ok=True)
top = ["run.py", "config.example.json", "requirements.in", "requirements-win-py312.lock",
       "Setup.ps1", "Start.ps1", "Start.cmd", "Stop.cmd", "Prepare.ps1", "Prepare-Offline.ps1",
       "README.md", "VERIFICATION.md", ".gitignore"]
code = [root / name for name in top]
for directory in ("demo", "web", "tools", "tests", "samples"):
    code.extend(p for p in (root / directory).rglob("*") if p.is_file()
                and "__pycache__" not in p.parts and p.suffix != ".pyc")
resources = []
for directory in ("wheelhouse", "models", ".cache/tiktoken"):
    resources.extend(p for p in (root / directory).rglob("*") if p.is_file())

results = []
for name, files, compression in (("myRAG-source.zip", code, zipfile.ZIP_DEFLATED),
                                  ("myRAG-offline-resources.zip", resources, zipfile.ZIP_STORED)):
    target = out / name
    with zipfile.ZipFile(target, "w", compression=compression, allowZip64=True) as archive:
        for path in sorted(files):
            archive.write(path, path.relative_to(root).as_posix())
    digest = hashlib.file_digest(target.open("rb"), "sha256").hexdigest()
    results.append({"file": name, "bytes": target.stat().st_size, "sha256": digest, "entries": len(files)})
    print(name, target.stat().st_size, "bytes", flush=True)
(out / "manifest.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
print("Archives contain no config.json, data/, logs/, or virtual environments.")
