# ==============================================================
# 恢复完整环境快照（方式B：开箱即用）- Windows PowerShell 版
#
# 前置：先跑过 deploy/startup.ps1 让 Dify 容器起来
# 用法：  .\deploy\restore-snapshot.ps1 -Snapshot .\snapshot
# ==============================================================
param(
    [Parameter(Mandatory=$true)]
    [string]$Snapshot
)
$ErrorActionPreference = "Stop"

$Dump = Join-Path $Snapshot "postgres_dify.dump"
$WeaviateTar = Join-Path $Snapshot "weaviate_data.tar.gz"
$DockerDir = Join-Path $PSScriptRoot "..\dify\docker"

if (-not (Test-Path $Dump)) { Write-Error "缺少 $Dump"; exit 1 }
if (-not (Test-Path $WeaviateTar)) { Write-Error "缺少 $WeaviateTar"; exit 1 }

Write-Host "==============================================="
Write-Host "  恢复环境快照"
Write-Host "==============================================="

$running = docker ps --format '{{.Names}}'
if ($running -notmatch 'docker-db_postgres-1') {
    Write-Error "Dify 容器未运行。请先执行： .\deploy\startup.ps1"
    exit 1
}

# 0. 就位 .env（含 SECRET_KEY，解密模型密钥必需）
$EnvBackup = Join-Path $Snapshot "env.backup"
if (Test-Path $EnvBackup) {
    Write-Host "[0/3] 就位 .env（SECRET_KEY 必须与源一致）..."
    Copy-Item $EnvBackup (Join-Path $DockerDir ".env") -Force
    Push-Location $DockerDir
    docker compose up -d | Out-Null
    Pop-Location
    Start-Sleep -Seconds 5
    Write-Host "      OK .env 已就位"
}

# 1. 恢复 PostgreSQL
Write-Host "[1/3] 恢复 PostgreSQL（应用/工作流/知识库元数据/密钥）..."
Push-Location $DockerDir
docker compose stop api worker worker_beat 2>$null | Out-Null
Pop-Location
docker exec docker-db_postgres-1 psql -U postgres -d postgres -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='dify' AND pid<>pg_backend_pid();" 2>$null | Out-Null
docker exec docker-db_postgres-1 psql -U postgres -d postgres -c "DROP DATABASE IF EXISTS dify;" 2>$null | Out-Null
docker exec docker-db_postgres-1 psql -U postgres -d postgres -c "CREATE DATABASE dify;" 2>$null | Out-Null
Get-Content $Dump -Raw -Encoding Byte | docker exec -i docker-db_postgres-1 pg_restore -U postgres -d dify --no-owner 2>$null
Write-Host "      OK PostgreSQL 已恢复"

# 2. 恢复 Weaviate
Write-Host "[2/3] 恢复 Weaviate 向量数据..."
$WeaviateDir = Join-Path $DockerDir "volumes\weaviate"
Push-Location $DockerDir
docker compose stop weaviate 2>$null | Out-Null
Pop-Location
if (-not (Test-Path $WeaviateDir)) { New-Item -ItemType Directory -Path $WeaviateDir -Force | Out-Null }
Get-ChildItem -Path $WeaviateDir -Recurse | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
tar -xzf $WeaviateTar -C $WeaviateDir
Write-Host "      OK Weaviate 已恢复"

# 3. 重启
Write-Host "[3/3] 重启服务..."
Push-Location $DockerDir
docker compose up -d | Out-Null
Pop-Location
Write-Host "      OK 服务已重启"

Write-Host ""
Write-Host "==============================================="
Write-Host "  恢复完成！等待约 30 秒后访问 http://localhost"
Write-Host "  验证：知识库应有 97 个文档；工作流可直接对话"
Write-Host "==============================================="
