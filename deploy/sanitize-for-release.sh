#!/usr/bin/env bash
# ============================================================
# sanitize-for-release.sh
# 分发前清理：把含真实密钥/密码的文件重置为占位符，
# 避免把私钥、API Key、密码随 DifiProject.rar 或仓库发出去。
#
# 用法：
#   bash deploy/sanitize-for-release.sh            # 仅扫描并报告（默认，安全）
#   bash deploy/sanitize-for-release.sh --apply    # 实际清理（会先备份为 *.release-bak）
#
# 注意：--apply 会修改你本地的 .env / htpasswd / 证书，
#       导致本地 Dify 实例需要重新填 Key 才能跑。
#       建议只在“准备对外分发的副本”上执行。
# ============================================================
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

APPLY=0
[ "${1:-}" = "--apply" ] && APPLY=1

# 需要处理的敏感文件（路径:处理方式）
ENV_FILE="dify/docker/.env"
HTPASSWD="dify/docker/nginx/conf.d/.htpasswd"
HTPASSWD_TXT="dify/docker/nginx/conf.d/.htpasswd_plaintext"
SSL_KEY="dify/docker/nginx/ssl/dify.key"
SSL_CRT="dify/docker/nginx/ssl/dify.crt"
KEY_TXT="key.txt"

# .env 中需要清空/占位的键
SECRET_KEYS=(
  DEEPSEEK_API_KEY TAVILY_API_KEY SILICONFLOW_API_KEY
  SECRET_KEY INIT_PASSWORD
  DB_PASSWORD REDIS_PASSWORD WEAVIATE_API_KEY
  CODE_EXECUTION_API_KEY SANDBOX_API_KEY
  PLUGIN_DIFY_INNER_API_KEY DIFY_AGENT_SERVER_SECRET_KEY
)

hr() { printf '%s\n' "------------------------------------------------------------"; }
found=0

echo "分发前敏感文件扫描  (模式: $([ $APPLY -eq 1 ] && echo 清理APPLY || echo 仅扫描DRY-RUN))"
hr

# 1) .env
if [ -f "$ENV_FILE" ]; then
  for k in "${SECRET_KEYS[@]}"; do
    line="$(grep -E "^${k}=" "$ENV_FILE" 2>/dev/null || true)"
    val="${line#*=}"
    if [ -n "$line" ] && [ -n "$val" ]; then
      echo "  [.env] $k 含真实值 → 需清空"
      found=1
    fi
  done
else
  echo "  [.env] 不存在（跳过）"
fi

# 2) 明文密码 / 私钥 / key.txt
for f in "$HTPASSWD_TXT" "$SSL_KEY" "$KEY_TXT"; do
  [ -f "$f" ] && { echo "  [敏感文件] $f 存在 → 需移除"; found=1; }
done

hr
if [ "$found" -eq 0 ]; then
  echo "✓ 未发现需要清理的真实密钥/密码，可安全打包分发。"
  exit 0
fi

if [ "$APPLY" -eq 0 ]; then
  echo "以上为待清理项。确认无误后执行：  bash deploy/sanitize-for-release.sh --apply"
  exit 0
fi

echo "开始清理（原文件备份为 *.release-bak）..."
hr

# --- 清空 .env 中的密钥值 ---
if [ -f "$ENV_FILE" ]; then
  cp "$ENV_FILE" "${ENV_FILE}.release-bak"
  for k in "${SECRET_KEYS[@]}"; do
    # 保留键名，清空值
    sed -i -E "s|^(${k}=).*|\1|" "$ENV_FILE"
  done
  echo "  ✓ 已清空 $ENV_FILE 中的密钥值（备份: ${ENV_FILE}.release-bak）"
fi

# --- 移除明文密码 / 私钥 / key.txt（备份后删除）---
for f in "$HTPASSWD_TXT" "$SSL_KEY" "$KEY_TXT"; do
  if [ -f "$f" ]; then
    mv "$f" "${f}.release-bak"
    echo "  ✓ 已移除 $f（备份: ${f}.release-bak）"
  fi
done

hr
echo "清理完成。分发提示："
echo "  - htpasswd(.htpasswd) 与证书(dify.crt) 仍在，接收方可直接用或重新生成"
echo "  - 接收方需按 README 重新填 .env 密钥、重新生成 Basic Auth 密码与 SSL 证书"
echo "  - 本地要恢复运行：把 *.release-bak 改回原名即可"
