#!/usr/bin/env bash
# ==============================================================
# 恢复完整环境快照（方式B：开箱即用）
# 把 交付方 导出的 PostgreSQL + Weaviate 快照恢复到本地 Dify，
# 恢复后知识库(97文档)、工作流、模型/Tavily key 全部就位，直接可用。
#
# 前置：先跑过 deploy/startup.sh 让 Dify 容器起来（哪怕是空的）
#
# 用法：
#   bash deploy/restore-snapshot.sh <快照目录>
#   例：bash deploy/restore-snapshot.sh snapshot/
# ==============================================================
set -euo pipefail

SNAP="${1:-}"
if [ -z "$SNAP" ] || [ ! -d "$SNAP" ]; then
  echo "用法: bash deploy/restore-snapshot.sh <快照目录>"
  echo "快照目录里应有 postgres_dify.dump 和 weaviate_data.tar.gz"
  exit 1
fi

DUMP="$SNAP/postgres_dify.dump"
WEAVIATE_TAR="$SNAP/weaviate_data.tar.gz"
DOCKER_DIR="$(dirname "$0")/../dify/docker"

[ -f "$DUMP" ] || { echo "缺少 $DUMP"; exit 1; }
[ -f "$WEAVIATE_TAR" ] || { echo "缺少 $WEAVIATE_TAR"; exit 1; }

echo "==============================================="
echo "  恢复环境快照"
echo "==============================================="

# 确认容器在跑
if ! docker ps --format '{{.Names}}' | grep -q docker-db_postgres-1; then
  echo "❌ Dify 容器未运行。请先执行： bash deploy/startup.sh"
  exit 1
fi

# ---- 0. 就位 .env（含 SECRET_KEY，解密模型密钥必需）----
if [ -f "$SNAP/env.backup" ]; then
  echo "[0/3] 就位 .env（SECRET_KEY 必须与源一致，否则模型密钥解不开）..."
  cp "$SNAP/env.backup" "$DOCKER_DIR/.env"
  echo "      ✓ .env 已就位，重启容器加载新 SECRET_KEY..."
  ( cd "$DOCKER_DIR" && docker compose up -d >/dev/null 2>&1 )
  sleep 5
fi

# ---- 1. 恢复 PostgreSQL ----
echo "[1/3] 恢复 PostgreSQL（应用/工作流/知识库元数据/密钥）..."
# 停 api/worker，避免恢复期间写入
( cd "$DOCKER_DIR" && docker compose stop api worker worker_beat >/dev/null 2>&1 || true )
# 断开活动连接并重建 dify 库
docker exec docker-db_postgres-1 psql -U postgres -d postgres -c \
  "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='dify' AND pid<>pg_backend_pid();" >/dev/null 2>&1 || true
docker exec docker-db_postgres-1 psql -U postgres -d postgres -c "DROP DATABASE IF EXISTS dify;" >/dev/null 2>&1 || true
docker exec docker-db_postgres-1 psql -U postgres -d postgres -c "CREATE DATABASE dify;" >/dev/null 2>&1
# 导入 dump
docker exec -i docker-db_postgres-1 pg_restore -U postgres -d dify --no-owner < "$DUMP" 2>/dev/null || true
echo "      ✓ PostgreSQL 已恢复"

# ---- 2. 恢复 Weaviate 向量 ----
echo "[2/3] 恢复 Weaviate 向量数据..."
WEAVIATE_DIR="$DOCKER_DIR/volumes/weaviate"
( cd "$DOCKER_DIR" && docker compose stop weaviate >/dev/null 2>&1 || true )
mkdir -p "$WEAVIATE_DIR"
rm -rf "${WEAVIATE_DIR:?}/"* 2>/dev/null || true
tar -xzf "$WEAVIATE_TAR" -C "$WEAVIATE_DIR"
echo "      ✓ Weaviate 已恢复"

# ---- 3. 重启全部 ----
echo "[3/3] 重启服务..."
( cd "$DOCKER_DIR" && docker compose up -d >/dev/null 2>&1 )
echo "      ✓ 服务已重启"

echo ""
echo "==============================================="
echo "  恢复完成！等待约 30 秒服务就绪后访问："
echo "    http://localhost"
echo ""
echo "  验证：知识库应有 97 个文档；工作流「制造业设备维修智能问答」可直接对话"
echo "==============================================="
