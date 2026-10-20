$Host.UI.RawUI.WindowTitle='Coursework - Environment'
Set-Location D:/Codex/2026-10-20/learn-assistant
Clear-Host
Write-Host 'PS> node --version' -ForegroundColor Yellow
node --version
Write-Host 'PS> pnpm --version' -ForegroundColor Yellow
pnpm --version
Write-Host 'PS> backend-fastapi/.venv/Scripts/python.exe --version' -ForegroundColor Yellow
& ./backend-fastapi/.venv/Scripts/python.exe --version
Write-Host 'PS> D:/Codex/tools/bin/uv.exe --version' -ForegroundColor Yellow
& D:/Codex/tools/bin/uv.exe --version
Write-Host 'PS> mysql --version' -ForegroundColor Yellow
mysql --version
