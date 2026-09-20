param([string]$PythonPath)
$ErrorActionPreference = 'Stop'
$env:PYTHONIOENCODING = 'utf-8'
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
$Host.UI.RawUI.WindowTitle = 'LangChain + Qwen - 在线运行'
Set-Location -LiteralPath $PSScriptRoot
if (-not $PythonPath) {
    $PythonPath = Join-Path $PSScriptRoot '.venv/Scripts/python.exe'
}
if (-not (Test-Path -LiteralPath $PythonPath)) { throw '请先执行 uv sync，或传入 -PythonPath。' }
$log = Join-Path $PSScriptRoot 'runs/online/PowerShell实际运行记录.txt'
Start-Transcript -Path $log -Force
try {
    foreach ($script in @('class1.py','class2_temperature.py','class3_memory.py','06_langchain_chain.py','07_langchain_long_chain.py','class5_calc_tool.py','class6_time_tool.py')) {
        Write-Host "`nPS $PSScriptRoot> python .\examples\$script" -ForegroundColor Yellow
        & $PythonPath -u (Join-Path $PSScriptRoot "examples/$script")
        if ($LASTEXITCODE -ne 0) { throw "$script 运行失败，退出码 $LASTEXITCODE" }
    }
    Write-Host "`n全部 7 个示例在线运行完成。可向上滚动查看完整过程。" -ForegroundColor Green
} finally {
    Stop-Transcript
}
