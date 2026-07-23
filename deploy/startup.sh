#!/usr/bin/env bash
# ============================================================
# startup.sh
# ============================================================
# 文件路径：deploy/startup.sh
# 用途：一键启动 Dify 社区版（Linux/Mac/WSL2）
# 功能：检查 Docker → 检查 .env → 克隆 Dify → 复制配置 → 启动 → 健康检查
#
# 使用方式：
#   chmod +x deploy/startup.sh
#   ./deploy/startup.sh
#
# 与 PRD 7.4 节对照：
#   ✅ 克隆 Dify → 复制 .env → docker compose up -d
#   ✅ 健康检查
# ============================================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 路径定义
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DIFY_DIR="$PROJECT_ROOT/dify"
DIFY_DOCKER_DIR="$DIFY_DIR/docker"

echo -e "${BLUE}============================================================${NC}"
echo -e "${BLUE}  制造业设备维修知识库智能问答平台 - 环境启动${NC}"
echo -e "${BLUE}============================================================${NC}"

# ------------------------------------------------------------
# 步骤 1：检查 Docker 状态
# ------------------------------------------------------------
echo -e "\n${BLUE}[1/6] 检查 Docker 环境...${NC}"

if ! command -v docker &> /dev/null; then
    echo -e "${RED}✗ Docker 未安装，请先安装 Docker Engine${NC}"
    echo -e "  安装指南：https://docs.docker.com/engine/install/"
    exit 1
fi

if ! docker info &> /dev/null; then
    echo -e "${RED}✗ Docker 守护进程未运行，请启动 Docker${NC}"
    exit 1
fi

if ! docker compose version &> /dev/null; then
    echo -e "${RED}✗ Docker Compose v2 未安装${NC}"
    echo -e "  安装指南：https://docs.docker.com/compose/install/"
    exit 1
fi

echo -e "${GREEN}✓ Docker $(docker version --format '{{.Server.Version}}') 运行正常${NC}"
echo -e "${GREEN}✓ Docker Compose $(docker compose version --short)${NC}"

# ------------------------------------------------------------
# 步骤 2：克隆 Dify 社区版（如不存在）
# ------------------------------------------------------------
echo -e "\n${BLUE}[2/6] 检查 Dify 源码...${NC}"

if [ ! -d "$DIFY_DIR" ]; then
    echo -e "${YELLOW}  Dify 不存在，开始克隆官方仓库...${NC}"
    git clone https://github.com/langgenius/dify.git "$DIFY_DIR"
    echo -e "${GREEN}✓ Dify 克隆完成${NC}"
else
    echo -e "${GREEN}✓ Dify 已存在于 $DIFY_DIR${NC}"
fi

if [ ! -f "$DIFY_DOCKER_DIR/docker-compose.yaml" ]; then
    echo -e "${RED}✗ 未找到 $DIFY_DOCKER_DIR/docker-compose.yaml${NC}"
    exit 1
fi

# ------------------------------------------------------------
# 步骤 3：检查并复制 .env 文件
# ------------------------------------------------------------
echo -e "\n${BLUE}[3/6] 检查环境变量配置...${NC}"

ENV_FILE="$DIFY_DOCKER_DIR/.env"
TEMPLATE_FILE="$SCRIPT_DIR/.env.template"

if [ ! -f "$ENV_FILE" ]; then
    if [ ! -f "$TEMPLATE_FILE" ]; then
        echo -e "${RED}✗ 模板文件不存在：$TEMPLATE_FILE${NC}"
        exit 1
    fi
    cp "$TEMPLATE_FILE" "$ENV_FILE"
    echo -e "${YELLOW}  已从模板创建 .env 文件${NC}"
    echo -e "${YELLOW}  ⚠️ 请编辑 $ENV_FILE 填入实际 API Key 后重新运行此脚本${NC}"
    echo -e "${YELLOW}  必填项：${NC}"
    echo -e "${YELLOW}    - TAVILY_API_KEY（获取：https://tavily.com）${NC}"
    echo -e "${YELLOW}  （SiliconFlow 模型密钥不填这里，稍后在 Dify Web UI 配置）${NC}"
    exit 0
fi

# 检查 Tavily 占位符是否已填（LLM 走 SiliconFlow，在 Web UI 配，不在 .env 校验）
if grep -q "your_tavily_api_key_here" "$ENV_FILE"; then
    echo -e "${RED}✗ .env 中的 TAVILY_API_KEY 还是占位符${NC}"
    echo -e "${YELLOW}  请编辑 $ENV_FILE 填入真实 Tavily 密钥${NC}"
    exit 1
fi

echo -e "${GREEN}✓ .env 配置完整${NC}"

# ------------------------------------------------------------
# 步骤 4：复制 docker-compose.override.yaml
# ------------------------------------------------------------
echo -e "\n${BLUE}[4/6] 复制 override 配置...${NC}"

OVERRIDE_SRC="$SCRIPT_DIR/docker-compose.override.yaml"
OVERRIDE_DST="$DIFY_DOCKER_DIR/docker-compose.override.yaml"

if [ -f "$OVERRIDE_SRC" ]; then
    cp "$OVERRIDE_SRC" "$OVERRIDE_DST"
    echo -e "${GREEN}✓ docker-compose.override.yaml 已复制${NC}"
else
    echo -e "${YELLOW}  override 文件不存在，跳过${NC}"
fi

# ------------------------------------------------------------
# 步骤 5：启动 Docker Compose
# ------------------------------------------------------------
echo -e "\n${BLUE}[5/6] 启动 Docker Compose 服务...${NC}"

cd "$DIFY_DOCKER_DIR"
docker compose up -d

echo -e "${GREEN}✓ Docker Compose 服务已启动${NC}"

# ------------------------------------------------------------
# 步骤 6：健康检查
# ------------------------------------------------------------
echo -e "\n${BLUE}[6/6] 健康检查（等待服务就绪，最多 60 秒）...${NC}"

MAX_WAIT=60
WAITED=0
HEALTH_OK=false

while [ $WAITED -lt $MAX_WAIT ]; do
    if curl -s -o /dev/null -w "%{http_code}" http://localhost/apps | grep -q "200\|301\|302"; then
        HEALTH_OK=true
        break
    fi
    sleep 3
    WAITED=$((WAITED + 3))
    echo -e "${YELLOW}  等待中... ${WAITED}s${NC}"
done

if [ "$HEALTH_OK" = true ]; then
    echo -e "${GREEN}✓ Dify 服务已就绪${NC}"
else
    echo -e "${YELLOW}  ⚠️ 服务可能还在启动中，请稍后手动检查${NC}"
    echo -e "${YELLOW}  检查命令：docker compose ps${NC}"
fi

# ------------------------------------------------------------
# 输出访问信息
# ------------------------------------------------------------
echo -e "\n${BLUE}============================================================${NC}"
echo -e "${GREEN}  启动完成！${NC}"
echo -e "${BLUE}============================================================${NC}"
echo -e "\n${GREEN}访问地址：${NC} http://localhost"
echo -e "${GREEN}首次访问：${NC} 需创建管理员账号（邮箱 + 密码）"
echo -e "\n${YELLOW}下一步（参考 README 第 4 节）：${NC}"
echo -e "  1. 配置 SiliconFlow 模型供应商（推理 deepseek-ai/DeepSeek-V4-Pro + Embedding BAAI/bge-large-zh-v1.5）"
echo -e "  2. 创建知识库并上传手册"
echo -e "  3. 导入 Workflow（src/workflow/chatflow-dsl.yml）并填 Tavily Key"
echo -e "  4. （可选）bash deploy/setup-hardening.sh 加 HTTPS + Basic Auth"
echo -e "\n${BLUE}常用命令：${NC}"
echo -e "  查看容器状态：cd dify/docker && docker compose ps"
echo -e "  查看日志：    cd dify/docker && docker compose logs -f api"
echo -e "  停止服务：    cd dify/docker && docker compose down"
echo -e "  验证环境：    ./deploy/verify-setup.sh"
