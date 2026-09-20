@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
 echo Please run: uv sync --group capture
 pause
 exit /b 1
)
"%SystemRoot%\System32\conhost.exe" "%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoLogo -NoProfile -NoExit -ExecutionPolicy Bypass -File "%~dp0capture_terminal.ps1" -PythonPath "%~dp0.venv\Scripts\python.exe"
