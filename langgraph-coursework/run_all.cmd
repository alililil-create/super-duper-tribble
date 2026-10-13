@echo off
cd /d "%~dp0"
set "PYTHONIOENCODING=utf-8"
if not exist ".venv\Scripts\python.exe" (
 echo Please run uv sync first.
 pause
 exit /b 1
)
".venv\Scripts\python.exe" -u run_all.py
pause
