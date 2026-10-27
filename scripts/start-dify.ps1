$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
Set-Location $projectRoot
docker info --format '{{.ServerVersion}}'
if ($LASTEXITCODE -ne 0) { throw 'Docker 引擎未就绪，请先修复 Docker Desktop。诊断见 docs/verification.md' }
if (!(Test-Path vendor/dify/docker/docker-compose.yaml)) {
 git clone --depth 1 --branch 1.18.0 https://github.com/langgenius/dify.git vendor/dify
 if ($LASTEXITCODE -ne 0) { throw 'Dify 官方源码下载失败' }
}
Set-Location vendor/dify/docker
if (!(Test-Path .env)) { Copy-Item .env.example .env; Add-Content .env "`nEXPOSE_NGINX_PORT=8080`nEXPOSE_NGINX_SSL_PORT=8443" }
if (!(Select-String -Path .env -Pattern '^SSRF_PROXY_ALLOW_PRIVATE_DOMAINS=' -Quiet)) { Add-Content .env 'SSRF_PROXY_ALLOW_PRIVATE_DOMAINS=host.docker.internal,senyu' }
docker compose up -d
if ($LASTEXITCODE -ne 0) { throw 'Dify 容器启动失败，执行 docker compose logs --tail=100 查看原因' }
Write-Host '访问 http://localhost:8080/install 完成初始化，然后按 docs/dify.md 导入工作流'
