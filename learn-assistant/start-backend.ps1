$ErrorActionPreference = 'Stop'
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:UV_CACHE_DIR = 'D:/Codex/cache/uv'
$env:TEMP = 'D:/Codex/temp'
$env:TMP = $env:TEMP
Set-Location (Join-Path $PSScriptRoot 'backend-fastapi')
& ./.venv/Scripts/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
