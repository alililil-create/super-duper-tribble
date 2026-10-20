$ErrorActionPreference = 'Stop'
$env:TEMP = 'D:/Codex/temp'
$env:TMP = $env:TEMP
Set-Location (Join-Path $PSScriptRoot 'frontend')
pnpm dev
