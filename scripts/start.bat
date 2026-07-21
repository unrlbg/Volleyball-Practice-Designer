@echo off
cd /d "%~dp0.."
set "PYTHON=python"
where python >nul 2>nul
if errorlevel 1 (
  set "PYTHON=py"
  where py >nul 2>nul
  if errorlevel 1 set "PYTHON=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
)
if not exist .venv "%PYTHON%" -m venv .venv
call .venv\Scripts\activate.bat
python -m pip install -r requirements.txt
python -m app.main
