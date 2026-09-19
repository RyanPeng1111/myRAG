param([string]$Python = "", [switch]$Offline)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$env:PIP_CACHE_DIR = Join-Path $PSScriptRoot '.cache\pip'
if (-not (Test-Path '.venv\Scripts\python.exe')) {
    if ($Python) {
        & $Python -c "import sys; assert sys.version_info[:2] == (3,12), 'Python 3.12 required'"
        if ($LASTEXITCODE -ne 0) { throw 'Please supply Python 3.12 using -Python C:\path\python.exe' }
        & $Python -m venv .venv
    } else {
        & py -3.12 -m venv .venv
    }
    if ($LASTEXITCODE -ne 0) { throw 'Install Python 3.12 x64, then rerun Setup.ps1. No administrator privileges are required for a per-user Python install.' }
}
$requirements = if (Test-Path requirements-win-py312.lock) { 'requirements-win-py312.lock' } else { 'requirements.in' }
if ($Offline) {
    & .\.venv\Scripts\python.exe -m pip install --no-index --find-links wheelhouse -r $requirements
} else {
    & .\.venv\Scripts\python.exe -m pip install --disable-pip-version-check -r $requirements
}
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed. See the preceding error.' }
if (-not (Test-Path config.json)) { Copy-Item config.example.json config.json }
Write-Host 'Installed. Run Prepare.ps1 online once, or copy the offline model/cache folders. Then run Start.ps1.'
