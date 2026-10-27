$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
$env:PYTHONIOENCODING = 'utf-8'
$env:UV_CACHE_DIR = 'D:/Codex/cache/uv'
if (-not (Test-Path '.venv/Scripts/python.exe')) {
    uv sync --frozen
}
& '.venv/Scripts/python.exe' -m app.evaluation
& '.venv/Scripts/python.exe' -m uvicorn app.main:app --host 127.0.0.1 --port 8017
