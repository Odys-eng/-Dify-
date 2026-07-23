# ============================================================
# startup.ps1
# ============================================================
# 文件路径：deploy/startup.ps1
# 用途：一键启动 Dify 社区版（Windows PowerShell 原生）
# 功能：检查 Docker → 检查 .env → 克隆 Dify → 复制配置 → 启动 → 健康检查
#
# 使用方式：
#   .\deploy\startup.ps1
#
# 与 PRD 7.4 节对照：
#   ✅ 克隆 Dify → 复制 .env → docker compose up -d
#   ✅ 健康检查
# ============================================================

$ErrorActionPreference = "Stop"

# 路径定义
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$DifyDir = Join-Path $ProjectRoot "dify"
$DifyDockerDir = Join-Path $DifyDir "docker"

Write-Host "============================================================" -ForegroundColor Blue
Write-Host "  制造业设备维修知识库智能问答平台 - 环境启动" -ForegroundColor Blue
Write-Host "============================================================" -ForegroundColor Blue

# ------------------------------------------------------------
# 步骤 1：检查 Docker 状态
# ------------------------------------------------------------
Write-Host "`n[1/6] 检查 Docker 环境..." -ForegroundColor Blue

try {
    $dockerVersion = docker version --format '{{.Server.Version}}' 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Docker 守护进程未运行"
    }
    Write-Host "✓ Docker $dockerVersion 运行正常" -ForegroundColor Green
} catch {
    Write-Host "✗ Docker 未安装或未运行，请先启动 Docker Desktop" -ForegroundColor Red
    Write-Host "  下载地址：https://www.docker.com/products/docker-desktop" -ForegroundColor Yellow
    exit 1
}

try {
    $composeVersion = docker compose version --short 2>&1
    Write-Host "✓ Docker Compose $composeVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Docker Compose v2 未安装" -ForegroundColor Red
    exit 1
}

# ------------------------------------------------------------
# 步骤 2：克隆 Dify 社区版（如不存在）
# ------------------------------------------------------------
Write-Host "`n[2/6] 检查 Dify 源码..." -ForegroundColor Blue

if (-not (Test-Path $DifyDir)) {
    Write-Host "  Dify 不存在，开始克隆官方仓库..." -ForegroundColor Yellow
    git clone https://github.com/langgenius/dify.git $DifyDir
    Write-Host "✓ Dify 克隆完成" -ForegroundColor Green
} else {
    Write-Host "✓ Dify 已存在于 $DifyDir" -ForegroundColor Green
}

if (-not (Test-Path (Join-Path $DifyDockerDir "docker-compose.yaml"))) {
    Write-Host "✗ 未找到 $DifyDockerDir\docker-compose.yaml" -ForegroundColor Red
    exit 1
}

# ------------------------------------------------------------
# 步骤 3：检查并复制 .env 文件
# ------------------------------------------------------------
Write-Host "`n[3/6] 检查环境变量配置..." -ForegroundColor Blue

$EnvFile = Join-Path $DifyDockerDir ".env"
$TemplateFile = Join-Path $ScriptDir ".env.template"

if (-not (Test-Path $EnvFile)) {
    if (-not (Test-Path $TemplateFile)) {
        Write-Host "✗ 模板文件不存在：$TemplateFile" -ForegroundColor Red
        exit 1
    }
    Copy-Item $TemplateFile $EnvFile
    Write-Host "  已从模板创建 .env 文件" -ForegroundColor Yellow
    Write-Host "  ⚠️ 请编辑 $EnvFile 填入实际 API Key 后重新运行此脚本" -ForegroundColor Yellow
    Write-Host "  必填项：" -ForegroundColor Yellow
    Write-Host "    - DEEPSEEK_API_KEY（获取：https://platform.deepseek.com）" -ForegroundColor Yellow
    Write-Host "    - TAVILY_API_KEY（获取：https://tavily.com）" -ForegroundColor Yellow
    exit 0
}

# 检查是否还有占位符
$envContent = Get-Content $EnvFile -Raw
if ($envContent -match "your_deepseek_api_key_here|your_tavily_api_key_here") {
    Write-Host "✗ .env 文件中仍有未填写的 API Key 占位符" -ForegroundColor Red
    Write-Host "  请编辑 $EnvFile 填入实际值" -ForegroundColor Yellow
    exit 1
}

Write-Host "✓ .env 配置完整" -ForegroundColor Green

# ------------------------------------------------------------
# 步骤 4：复制 docker-compose.override.yaml
# ------------------------------------------------------------
Write-Host "`n[4/6] 复制 override 配置..." -ForegroundColor Blue

$OverrideSrc = Join-Path $ScriptDir "docker-compose.override.yaml"
$OverrideDst = Join-Path $DifyDockerDir "docker-compose.override.yaml"

if (Test-Path $OverrideSrc) {
    Copy-Item $OverrideSrc $OverrideDst -Force
    Write-Host "✓ docker-compose.override.yaml 已复制" -ForegroundColor Green
} else {
    Write-Host "  override 文件不存在，跳过" -ForegroundColor Yellow
}

# ------------------------------------------------------------
# 步骤 5：启动 Docker Compose
# ------------------------------------------------------------
Write-Host "`n[5/6] 启动 Docker Compose 服务..." -ForegroundColor Blue

Set-Location $DifyDockerDir
docker compose up -d
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Docker Compose 启动失败" -ForegroundColor Red
    exit 1
}

Write-Host "✓ Docker Compose 服务已启动" -ForegroundColor Green

# ------------------------------------------------------------
# 步骤 6：健康检查
# ------------------------------------------------------------
Write-Host "`n[6/6] 健康检查（等待服务就绪，最多 60 秒）..." -ForegroundColor Blue

$maxWait = 60
$waited = 0
$healthOk = $false

while ($waited -lt $maxWait) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost/apps" -UseBasicParsing -ErrorAction Stop
        if ($response.StatusCode -in @(200, 301, 302)) {
            $healthOk = $true
            break
        }
    } catch {
        # 继续等待
    }
    Start-Sleep -Seconds 3
    $waited += 3
    Write-Host "  等待中... ${waited}s" -ForegroundColor Yellow
}

if ($healthOk) {
    Write-Host "✓ Dify 服务已就绪" -ForegroundColor Green
} else {
    Write-Host "  ⚠️ 服务可能还在启动中，请稍后手动检查" -ForegroundColor Yellow
    Write-Host "  检查命令：docker compose ps" -ForegroundColor Yellow
}

# ------------------------------------------------------------
# 输出访问信息
# ------------------------------------------------------------
Write-Host "`n============================================================" -ForegroundColor Blue
Write-Host "  启动完成！" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Blue

Write-Host "`n访问地址： http://localhost" -ForegroundColor Green
Write-Host "首次访问： 需创建管理员账号（邮箱 + 密码）" -ForegroundColor Green

Write-Host "`n下一步（参考 docs\部署检查清单.md）：" -ForegroundColor Yellow
Write-Host "  1. 配置 DeepSeek 模型供应商（模型名填 deepseek-v4-flash）"
Write-Host "  2. 创建知识库并上传手册 PDF"
Write-Host "  3. 配置 Tavily 自定义工具"
Write-Host "  4. 创建 Workflow 应用"

Write-Host "`n常用命令：" -ForegroundColor Blue
Write-Host "  查看容器状态：cd dify\docker; docker compose ps"
Write-Host "  查看日志：    cd dify\docker; docker compose logs -f api"
Write-Host "  停止服务：    cd dify\docker; docker compose down"
Write-Host "  验证环境：    .\deploy\verify-setup.sh（需 WSL 或 Git Bash）"
