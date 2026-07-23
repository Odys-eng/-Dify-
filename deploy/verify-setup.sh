#!/usr/bin/env bash
# ============================================================
# verify-setup.sh
# ============================================================
# 文件路径：deploy/verify-setup.sh
# 用途：验证 Dify 环境搭建是否正确
# 检查项：
#   1. Docker 容器运行状态
#   2. Dify API 可访问性
#   3. DeepSeek API Key 有效性
#   4. Tavily API Key 有效性
#
# 使用方式：
#   chmod +x deploy/verify-setup.sh
#   ./deploy/verify-setup.sh
#
# 与 PRD 7.5 节对照：
#   ✅ 验证 Dify 内部配置的前置条件
# ============================================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 路径定义
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DIFY_DOCKER_DIR="$PROJECT_ROOT/dify/docker"
ENV_FILE="$DIFY_DOCKER_DIR/.env"

PASS=0
FAIL=0
WARN=0

echo -e "${BLUE}============================================================${NC}"
echo -e "${BLUE}  环境验证脚本 - 制造业设备维修知识库平台${NC}"
echo -e "${BLUE}============================================================${NC}"

# ------------------------------------------------------------
# 检查 1：Docker 容器运行状态
# ------------------------------------------------------------
echo -e "\n${BLUE}[1/4] 检查 Docker 容器运行状态...${NC}"

if [ ! -d "$DIFY_DOCKER_DIR" ]; then
    echo -e "${RED}✗ Dify 目录不存在：$DIFY_DOCKER_DIR${NC}"
    echo -e "${YELLOW}  请先运行 ./deploy/startup.sh${NC}"
    exit 1
fi

cd "$DIFY_DOCKER_DIR"

# 检查关键容器
# service 名对应 dify/docker/docker-compose.yaml 中的 service key（不是容器名）
REQUIRED_CONTAINERS=("api" "worker" "web" "weaviate" "db_postgres" "redis" "nginx")

for container in "${REQUIRED_CONTAINERS[@]}"; do
    status=$(docker compose ps -q "$container" 2>/dev/null | xargs -I{} docker inspect --format '{{.State.Status}}' {} 2>/dev/null || echo "missing")
    if [ "$status" = "running" ]; then
        echo -e "${GREEN}  ✓ $container: running${NC}"
        PASS=$((PASS + 1))
    elif [ "$status" = "missing" ]; then
        echo -e "${RED}  ✗ $container: 不存在${NC}"
        FAIL=$((FAIL + 1))
    else
        echo -e "${RED}  ✗ $container: $status${NC}"
        FAIL=$((FAIL + 1))
    fi
done

# ------------------------------------------------------------
# 检查 2：Dify API 可访问性
# ------------------------------------------------------------
echo -e "\n${BLUE}[2/4] 检查 Dify API 可访问性...${NC}"

DIFY_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/apps 2>/dev/null || echo "000")

if [ "$DIFY_HEALTH" = "200" ] || [ "$DIFY_HEALTH" = "301" ] || [ "$DIFY_HEALTH" = "302" ]; then
    echo -e "${GREEN}  ✓ Dify Web UI 可访问（HTTP $DIFY_HEALTH）${NC}"
    PASS=$((PASS + 1))
else
    echo -e "${RED}  ✗ Dify Web UI 不可访问（HTTP $DIFY_HEALTH）${NC}"
    echo -e "${YELLOW}  可能原因：${NC}"
    echo -e "${YELLOW}    1. 服务还在启动中（等待 30 秒后重试）${NC}"
    echo -e "${YELLOW}    2. 端口 80 被占用（检查 EXPOSE_NGINX_PORT 配置）${NC}"
    echo -e "${YELLOW}    3. 查看日志：docker compose logs nginx${NC}"
    FAIL=$((FAIL + 1))
fi

# 检查 API 端点
API_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/console/api/setup 2>/dev/null || echo "000")
if [ "$API_HEALTH" = "200" ] || [ "$API_HEALTH" = "404" ]; then
    echo -e "${GREEN}  ✓ Dify API 端点响应正常（HTTP $API_HEALTH）${NC}"
    PASS=$((PASS + 1))
else
    echo -e "${YELLOW}  ⚠ Dify API 端点响应异常（HTTP $API_HEALTH）${NC}"
    WARN=$((WARN + 1))
fi

# ------------------------------------------------------------
# 检查 3：DeepSeek API Key 有效性
# ------------------------------------------------------------
echo -e "\n${BLUE}[3/4] 检查 DeepSeek API Key 有效性...${NC}"

if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}  ✗ .env 文件不存在：$ENV_FILE${NC}"
    FAIL=$((FAIL + 1))
else
    # 从 .env 读取 DeepSeek API Key
    DEEPSEEK_API_KEY=$(grep -E "^DEEPSEEK_API_KEY=" "$ENV_FILE" | cut -d'=' -f2- | tr -d '[:space:]')

    if [ -z "$DEEPSEEK_API_KEY" ] || [ "$DEEPSEEK_API_KEY" = "your_deepseek_api_key_here" ]; then
        echo -e "${RED}  ✗ DEEPSEEK_API_KEY 未配置（仍是占位符）${NC}"
        echo -e "${YELLOW}  请编辑 $ENV_FILE 填入实际 Key${NC}"
        FAIL=$((FAIL + 1))
    else
        echo -e "${GREEN}  ✓ DEEPSEEK_API_KEY 已配置（${DEEPSEEK_API_KEY:0:8}...）${NC}"

        # 发送测试请求
        echo -e "${BLUE}  发送测试请求到 DeepSeek API...${NC}"
        TEST_RESPONSE=$(curl -s -w "\n%{http_code}" https://api.deepseek.com/chat/completions \
            -H "Authorization: Bearer $DEEPSEEK_API_KEY" \
            -H "Content-Type: application/json" \
            -d '{
                "model": "deepseek-v4-flash",
                "messages": [{"role": "user", "content": "ping"}],
                "max_tokens": 10,
                "thinking": {"type": "disabled"}
            }' 2>/dev/null || echo "failed")

        HTTP_CODE=$(echo "$TEST_RESPONSE" | tail -1)
        RESPONSE_BODY=$(echo "$TEST_RESPONSE" | head -n -1)

        if [ "$HTTP_CODE" = "200" ]; then
            echo -e "${GREEN}  ✓ DeepSeek API 调用成功（HTTP 200）${NC}"
            echo -e "${GREEN}  ✓ 模型 deepseek-v4-flash 可用${NC}"
            PASS=$((PASS + 1))
        elif [ "$HTTP_CODE" = "401" ]; then
            echo -e "${RED}  ✗ DeepSeek API Key 无效（HTTP 401）${NC}"
            echo -e "${YELLOW}  请检查 Key 是否正确：https://platform.deepseek.com${NC}"
            FAIL=$((FAIL + 1))
        elif [ "$HTTP_CODE" = "404" ]; then
            echo -e "${RED}  ✗ 模型 deepseek-v4-flash 不可用（HTTP 404）${NC}"
            echo -e "${YELLOW}  可能原因：${NC}"
            echo -e "${YELLOW}    1. 模型名错误（确认是 deepseek-v4-flash，不是 deepseek-chat）${NC}"
            echo -e "${YELLOW}    2. DeepSeek 账户无权限${NC}"
            echo -e "${YELLOW}  响应：$RESPONSE_BODY${NC}"
            FAIL=$((FAIL + 1))
        else
            echo -e "${YELLOW}  ⚠ DeepSeek API 响应异常（HTTP $HTTP_CODE）${NC}"
            echo -e "${YELLOW}  响应：$RESPONSE_BODY${NC}"
            WARN=$((WARN + 1))
        fi
    fi
fi

# ------------------------------------------------------------
# 检查 4：Tavily API Key 有效性
# ------------------------------------------------------------
echo -e "\n${BLUE}[4/4] 检查 Tavily API Key 有效性...${NC}"

if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}  ✗ .env 文件不存在${NC}"
    FAIL=$((FAIL + 1))
else
    TAVILY_API_KEY=$(grep -E "^TAVILY_API_KEY=" "$ENV_FILE" | cut -d'=' -f2- | tr -d '[:space:]')

    if [ -z "$TAVILY_API_KEY" ] || [ "$TAVILY_API_KEY" = "your_tavily_api_key_here" ]; then
        echo -e "${RED}  ✗ TAVILY_API_KEY 未配置（仍是占位符）${NC}"
        echo -e "${YELLOW}  请编辑 $ENV_FILE 填入实际 Key${NC}"
        FAIL=$((FAIL + 1))
    else
        echo -e "${GREEN}  ✓ TAVILY_API_KEY 已配置（${TAVILY_API_KEY:0:8}...）${NC}"

        # 发送测试搜索请求
        echo -e "${BLUE}  发送测试搜索请求到 Tavily API...${NC}"
        TEST_RESPONSE=$(curl -s -w "\n%{http_code}" https://api.tavily.com/search \
            -H "Content-Type: application/json" \
            -d "{
                \"api_key\": \"$TAVILY_API_KEY\",
                \"query\": \"CNC machine tool repair\",
                \"max_results\": 1
            }" 2>/dev/null || echo "failed")

        HTTP_CODE=$(echo "$TEST_RESPONSE" | tail -1)
        RESPONSE_BODY=$(echo "$TEST_RESPONSE" | head -n -1)

        if [ "$HTTP_CODE" = "200" ]; then
            echo -e "${GREEN}  ✓ Tavily API 调用成功（HTTP 200）${NC}"
            PASS=$((PASS + 1))
        elif [ "$HTTP_CODE" = "401" ] || [ "$HTTP_CODE" = "403" ]; then
            echo -e "${RED}  ✗ Tavily API Key 无效（HTTP $HTTP_CODE）${NC}"
            echo -e "${YELLOW}  请检查 Key 是否正确：https://tavily.com${NC}"
            FAIL=$((FAIL + 1))
        else
            echo -e "${YELLOW}  ⚠ Tavily API 响应异常（HTTP $HTTP_CODE）${NC}"
            echo -e "${YELLOW}  响应：$RESPONSE_BODY${NC}"
            WARN=$((WARN + 1))
        fi
    fi
fi

# ------------------------------------------------------------
# 汇总
# ------------------------------------------------------------
echo -e "\n${BLUE}============================================================${NC}"
echo -e "${BLUE}  验证结果汇总${NC}"
echo -e "${BLUE}============================================================${NC}"
echo -e "${GREEN}  通过：$PASS${NC}"
echo -e "${RED}  失败：$FAIL${NC}"
echo -e "${YELLOW}  警告：$WARN${NC}"

if [ $FAIL -gt 0 ]; then
    echo -e "\n${RED}✗ 环境验证未通过，请修复上述失败项${NC}"
    exit 1
elif [ $WARN -gt 0 ]; then
    echo -e "\n${YELLOW}⚠ 环境验证通过（有警告），建议检查警告项${NC}"
    exit 0
else
    echo -e "\n${GREEN}✓ 环境验证全部通过，可以开始 Dify 内部配置${NC}"
    echo -e "${YELLOW}  下一步：参考 docs/部署检查清单.md 完成 Dify Web UI 配置${NC}"
    exit 0
fi
