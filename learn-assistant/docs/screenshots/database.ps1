$Host.UI.RawUI.WindowTitle='Coursework - Database'
$env:PYTHONIOENCODING='utf-8'
Set-Location D:/Codex/2026-10-20/learn-assistant/backend-fastapi
$env:PYTHONPATH=(Get-Location).Path
Clear-Host
Write-Host 'PS> .venv/Scripts/python.exe scripts/show_database.py' -ForegroundColor Yellow
& ./.venv/Scripts/python.exe scripts/show_database.py
