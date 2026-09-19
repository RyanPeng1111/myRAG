$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$env:PYTHONUTF8='1'
$env:PYTHONIOENCODING='utf-8'
if (-not (Test-Path '.venv\Scripts\python.exe')) { throw 'Run Setup.ps1 first.' }
& .\.venv\Scripts\python.exe tools\doctor.py
if ($LASTEXITCODE -ne 0) { throw 'Environment check failed. See the messages above.' }
& .\.venv\Scripts\python.exe run.py
if ($LASTEXITCODE -ne 0) { throw 'Server exited with an error. See logs/.' }
