$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$env:PIP_CACHE_DIR = Join-Path $PSScriptRoot '.cache\pip'
if (-not (Test-Path requirements-win-py312.lock)) { throw 'A tested dependency lock is required.' }
& .\.venv\Scripts\python.exe -m pip download --only-binary=:all: --dest wheelhouse -r requirements-win-py312.lock
if ($LASTEXITCODE -ne 0) { throw 'Wheel preparation failed. Do not call the bundle offline-ready.' }
& .\Prepare.ps1
Write-Host 'Bring code, wheelhouse/, models/, .cache/tiktoken/, and a Python 3.12 x64 installer into the intranet. Run Setup.ps1 -Offline on the destination.'
