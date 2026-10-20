$Host.UI.RawUI.WindowTitle='Coursework - Backend'
$env:PYTHONIOENCODING='utf-8'
Set-Location D:/Codex/2026-10-20/learn-assistant/backend-fastapi
Clear-Host
Write-Host 'Backend verification instance: port 8001 (main service: 8000)' -ForegroundColor Cyan
Write-Host 'PS> .venv/Scripts/python.exe -m uvicorn app.main:app --port 8001' -ForegroundColor Yellow
& ./.venv/Scripts/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8001
