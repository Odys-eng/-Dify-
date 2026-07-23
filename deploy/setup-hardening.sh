#!/usr/bin/env bash
# ============================================================
# setup-hardening.sh
# 一键给 Dify 加上 HTTPS + 限流 + Basic Auth。
# 自动完成：
#   1. 生成自签 SSL 证书（localhost + 127.0.0.1）
#   2. 生成 Basic Auth 账号密码（随机密码，保存到明文文件方便你记）
#   3. 复制 nginx 配置模板到位
#   4. 重启 nginx 生效
#
# 前置：已完成 3.3「docker compose up -d」，且 dify/ 目录存在。
# 运行：bash deploy/setup-hardening.sh          （Windows 用 Git Bash / WSL）
#
# 需要命令：openssl、htpasswd（或 docker）。若无 htpasswd，脚本会用 openssl 兜底。
# ============================================================
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

NGINX_DIR="dify/docker/nginx"
CONF_DIR="$NGINX_DIR/conf.d"
SSL_DIR="$NGINX_DIR/ssl"
TEMPLATE="deploy/nginx/rate_limit.conf.template"
AUTH_USER="admin"

if [ ! -d "dify/docker" ]; then
  echo "错误：找不到 dify/docker 目录。请先完成 README 第 3 步获取并启动 Dify。"
  exit 1
fi

mkdir -p "$CONF_DIR" "$SSL_DIR"

echo "[1/4] 生成自签 SSL 证书..."
if [ -f "$SSL_DIR/dify.crt" ] && [ -f "$SSL_DIR/dify.key" ]; then
  echo "      已存在证书，跳过。"
else
  openssl req -x509 -nodes -days 825 -newkey rsa:2048 \
    -keyout "$SSL_DIR/dify.key" -out "$SSL_DIR/dify.crt" \
    -subj "/C=CN/O=EquipMaint/CN=localhost" \
    -addext "subjectAltName=DNS:localhost,IP:127.0.0.1" 2>/dev/null
  echo "      已生成 $SSL_DIR/dify.{crt,key}"
fi

echo "[2/4] 生成 Basic Auth 账号密码..."
if [ -f "$CONF_DIR/.htpasswd" ]; then
  echo "      已存在 .htpasswd，跳过（如需重置请先删除该文件）。"
else
  PASS="$(openssl rand -base64 12 | tr -dc 'A-Za-z0-9' | head -c 16)"
  if command -v htpasswd >/dev/null 2>&1; then
    htpasswd -bc "$CONF_DIR/.htpasswd" "$AUTH_USER" "$PASS" >/dev/null 2>&1
  else
    # 无 htpasswd 时用 openssl 生成 APR1 兼容不了，改用 nginx 支持的 {SHA}
    HASH="$(printf '%s' "$PASS" | openssl passwd -apr1 -stdin 2>/dev/null || printf '%s' "$PASS" | openssl passwd -6 -stdin)"
    printf '%s:%s\n' "$AUTH_USER" "$HASH" > "$CONF_DIR/.htpasswd"
  fi
  printf '%s / %s\n' "$AUTH_USER" "$PASS" > "$CONF_DIR/.htpasswd_plaintext"
  echo "      账号：$AUTH_USER   密码：$PASS"
  echo "      已保存到 $CONF_DIR/.htpasswd_plaintext（请妥善保管，勿提交仓库）"
fi

echo "[3/4] 复制 nginx 配置..."
cp "$TEMPLATE" "$CONF_DIR/rate_limit.conf"
# 关闭上游默认 80 配置，避免与本配置冲突绕过鉴权
[ -f "$CONF_DIR/default.conf" ] && mv "$CONF_DIR/default.conf" "$CONF_DIR/default.conf.disabled" && echo "      已禁用 default.conf（避免鉴权旁路）"
echo "      已复制 rate_limit.conf"

echo "[4/4] 重启 nginx..."
( cd dify/docker && docker compose restart nginx >/dev/null 2>&1 ) && echo "      nginx 已重启" || echo "      ⚠️ 重启失败，请手动：cd dify/docker && docker compose restart nginx"

echo
echo "完成！现在通过  https://localhost  访问（浏览器会提示自签证书不安全，选择继续即可）。"
echo "登录 Basic Auth 用 $CONF_DIR/.htpasswd_plaintext 里的账号密码。"
