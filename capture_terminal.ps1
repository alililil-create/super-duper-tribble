param([string]$PythonPath)
$ErrorActionPreference='Stop'
$env:PYTHONIOENCODING='utf-8'
[Console]::OutputEncoding=[System.Text.UTF8Encoding]::new()
Set-Location -LiteralPath $PSScriptRoot
$Host.UI.RawUI.WindowTitle='LangChain Qwen - Real Terminal'
$Host.UI.RawUI.BackgroundColor='Black'
$Host.UI.RawUI.ForegroundColor='Gray'
Add-Type -AssemblyName System.Drawing
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class TerminalCapture {
 [DllImport("kernel32.dll")] public static extern IntPtr GetConsoleWindow();
 [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h,int n);
 [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
 [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
 [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h,out RECT r);
 public struct RECT {public int Left,Top,Right,Bottom;}
}
"@
$window=[TerminalCapture]::GetConsoleWindow()
if ($window -eq [IntPtr]::Zero) { throw 'No console window available.' }
[TerminalCapture]::ShowWindow($window,3) | Out-Null
$destination=Join-Path $PSScriptRoot 'runs/terminal-screenshots'
New-Item -ItemType Directory -Force -Path $destination | Out-Null
$groups=@(
 @{Name='01_basic';Files=@('class1.py')},
 @{Name='02_temperature';Files=@('class2_temperature.py')},
 @{Name='03_memory';Files=@('class3_memory.py')},
 @{Name='04_chain';Files=@('06_langchain_chain.py','07_langchain_long_chain.py')},
 @{Name='05_calculator';Files=@('class5_calc_tool.py')},
 @{Name='06_time';Files=@('class6_time_tool.py')}
)
foreach ($group in $groups) {
 Clear-Host
 Write-Host '真实千问在线运行 / PowerShell 窗口截图' -ForegroundColor Cyan
 foreach ($file in $group.Files) {
  Write-Host "`nPS> python ./examples/$file" -ForegroundColor Yellow
  & $PythonPath -u (Join-Path $PSScriptRoot "examples/$file") | ForEach-Object { Write-Host $_ }
  if ($LASTEXITCODE -ne 0) { throw "$file failed: $LASTEXITCODE" }
 }
 Write-Host "`n运行完成，正在保存本窗口截图……" -ForegroundColor Green
 [TerminalCapture]::SetForegroundWindow($window) | Out-Null
 Start-Sleep -Milliseconds 900
 if ([TerminalCapture]::GetForegroundWindow() -ne $window) { throw '请保持此终端在前台，然后重新运行；未截取其他窗口。' }
 $rect=New-Object TerminalCapture+RECT
 [TerminalCapture]::GetWindowRect($window,[ref]$rect) | Out-Null
 $bitmap=New-Object System.Drawing.Bitmap(($rect.Right-$rect.Left),($rect.Bottom-$rect.Top))
 $graphics=[System.Drawing.Graphics]::FromImage($bitmap)
 try {
  $graphics.CopyFromScreen($rect.Left,$rect.Top,0,0,$bitmap.Size)
  $bitmap.Save((Join-Path $destination ($group.Name+'.png')),[System.Drawing.Imaging.ImageFormat]::Png)
 } finally { $graphics.Dispose(); $bitmap.Dispose() }
}
Write-Host "`n六组真实终端截图已保存：$destination" -ForegroundColor Green
Write-Host '若长输出超出屏幕，截图只包含当前可见部分；可向上滚动查看。'
