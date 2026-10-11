param([string]$Python = 'python')
$ErrorActionPreference = 'Stop'
& $Python -X utf8 (Join-Path $PSScriptRoot 'plot_figure3c.py')
if ($LASTEXITCODE -ne 0) { throw 'Figure3c 绘制或标记核验失败。' }
