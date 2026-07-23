#!/usr/bin/env bash
# ==============================================================
# 制造业设备维修平台 - 数据备份脚本
# 备份内容：PostgreSQL（应用配置+对话记录）+ Weaviate 数据卷
#
# 用法：
#   bash backup.sh              # 备份到默认目录 ./backups/
#   bash backup.sh /data/backup # 备份到指定目录
#
# 建议：加入 crontab 每天自动执行
#   0 2 * * * cd /path/to/homework && bash src/scripts/backup.sh >> backup.log 2>&1
# ==============================================================

set -euo pipefail

BACKUP_ROOT="${1:-$(dirname "$0")/../../backups}"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="$BACKUP_ROOT/$DATE"
DOCKER_DIR="$(dirname "$0")/../../dify/docker"

mkdir -p "$BACKUP_DIR"
echo "[$(date)] 备份开始 → $BACKUP_DIR"

# ---- 1. PostgreSQL 备份 ----
echo "[1/3] 备份 PostgreSQL..."
docker exec docker-db_postgres-1 pg_dump \
  -U postgres \
  --format=custom \
  --compress=9 \
  dify > "$BACKUP_DIR/postgres_dify.dump"
echo "      大小: $(du -sh "$BACKUP_DIR/postgres_dify.dump" | cut -f1)"

# ---- 2. Weaviate 数据卷备份 ----
echo "[2/3] 备份 Weaviate 向量数据..."
WEAVIATE_VOL=$(docker inspect docker-weaviate-1 \
  --format '{{range .Mounts}}{{if eq .Destination "/var/lib/weaviate"}}{{.Source}}{{end}}{{end}}' 2>/dev/null || echo "")

if [ -n "$WEAVIATE_VOL" ]; then
  tar -czf "$BACKUP_DIR/weaviate_data.tar.gz" -C "$WEAVIATE_VOL" . 2>/dev/null
  echo "      大小: $(du -sh "$BACKUP_DIR/weaviate_data.tar.gz" | cut -f1)"
else
  # fallback: 直接打包 volumes/weaviate 目录
  WEAVIATE_DIR="$DOCKER_DIR/volumes/weaviate"
  if [ -d "$WEAVIATE_DIR" ]; then
    tar -czf "$BACKUP_DIR/weaviate_data.tar.gz" -C "$WEAVIATE_DIR" . 2>/dev/null
    echo "      大小: $(du -sh "$BACKUP_DIR/weaviate_data.tar.gz" | cut -f1)"
  else
    echo "      [警告] 未找到 Weaviate 数据目录，跳过"
  fi
fi

# ---- 3. 应用配置快照 ----
echo "[3/3] 备份应用配置..."
mkdir -p "$BACKUP_DIR/config"
# .env 中 API Key 敏感，仅备份变量名（不备份值）
grep -E "^[A-Z_]+=?" "$DOCKER_DIR/.env" | sed 's/=.*/=<REDACTED>/' \
  > "$BACKUP_DIR/config/env_keys_only.txt" 2>/dev/null || true
cp "$DOCKER_DIR/docker-compose.override.yaml" "$BACKUP_DIR/config/" 2>/dev/null || true
cp -r "$DOCKER_DIR/nginx/conf.d" "$BACKUP_DIR/config/nginx_conf.d" 2>/dev/null || true
echo "      配置文件已备份（API Key 已脱敏）"

# ---- 汇总 ----
TOTAL=$(du -sh "$BACKUP_DIR" | cut -f1)
echo ""
echo "[$(date)] 备份完成"
echo "  位置: $BACKUP_DIR"
echo "  总大小: $TOTAL"
echo ""

# ---- 清理旧备份（保留最近 7 份）----
if [ -d "$BACKUP_ROOT" ]; then
  OLD_COUNT=$(ls -1d "$BACKUP_ROOT"/2* 2>/dev/null | wc -l)
  if [ "$OLD_COUNT" -gt 7 ]; then
    ls -1d "$BACKUP_ROOT"/2* | head -n $((OLD_COUNT - 7)) | xargs rm -rf
    echo "  已清理旧备份（保留最近 7 份）"
  fi
fi
