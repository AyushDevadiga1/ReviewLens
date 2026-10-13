@echo off
REM start.bat — the one-liner for the complete ReviewLens project.
REM Usage:  start.bat [--seed N] [--no-seed] [--port 8000] [--ui-port 8501]
REM First run creates .venv, installs dependencies and downloads the
REM spacy model (slow, once). Every later run goes straight to the app.
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo [setup] creating virtual environment...
  python -m venv .venv
  echo [setup] installing dependencies ^(one time, several minutes^)...
  .\.venv\Scripts\python.exe -m pip install -r requirements.txt
  .\.venv\Scripts\python.exe -m spacy download en_core_web_sm
)
.\.venv\Scripts\python.exe demo.py %*
