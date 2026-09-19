@echo off
cd /d "%~dp0"
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
if "%~1"=="" (
  py -3.12 tools\bootstrap.py
) else (
  "%~1" tools\bootstrap.py
)
if errorlevel 1 (
  echo Installation failed. See the error above.
  pause
  exit /b 1
)
echo Ready. Run Start.cmd, then Load-Samples.cmd to import the included demo files.
pause
