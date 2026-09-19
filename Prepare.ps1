$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
& .\.venv\Scripts\python.exe tools\prepare.py
if ($LASTEXITCODE -ne 0) { throw 'Model preparation failed.' }
