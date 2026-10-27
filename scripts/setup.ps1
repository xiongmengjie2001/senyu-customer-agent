$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
python -m pip install --target .runtime -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw 'Python 依赖安装失败' }
if (!(Test-Path .env)) { Copy-Item .env.example .env }
Push-Location frontend
npm.cmd ci
if ($LASTEXITCODE -ne 0) { throw '前端依赖安装失败' }
npm.cmd run build
if ($LASTEXITCODE -ne 0) { throw '前端构建失败' }
Pop-Location
Write-Host '安装完成：python run.py'
