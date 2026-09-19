@echo off
cd /d "%~dp0"
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
if not exist ".venv\Scripts\python.exe" (
  echo Run Bootstrap.cmd with Python 3.12 first. See README.md.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" tools\doctor.py
if errorlevel 1 (
  pause
  exit /b 1
)
".venv\Scripts\python.exe" run.py
pause
