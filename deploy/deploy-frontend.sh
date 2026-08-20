#!/bin/bash
set -euo pipefail

echo "=== InternetShop PRO — Frontend Deploy ==="

APP_DIR="/opt/internetshop"
FRONTEND_DIR="$APP_DIR/frontend"
NGINX_HTML="/var/www/internetshop"
COMPOSE_FILE="docker-compose.yml"
COMPOSE_PROD="docker-compose.prod.yml"

cd "$APP_DIR"

echo "[1/6] Pull latest code..."
git pull origin master

echo "[2/6] Build frontend image..."
docker compose -f "$COMPOSE_FILE" -f "$COMPOSE_PROD" build frontend

echo "[3/6] Build frontend static files..."
docker compose -f "$COMPOSE_FILE" -f "$COMPOSE_PROD" run --rm frontend \
    npm run build

echo "[4/6] Copy build output to nginx..."
mkdir -p "$NGINX_HTML"
docker compose -f "$COMPOSE_FILE" -f "$COMPOSE_PROD" run --rm frontend \
    sh -c "cp -r /app/dist/* /var/www/internetshop/"

echo "[5/6] Copy nginx config..."
cp "$APP_DIR/deploy/nginx/internetshop.conf" /etc/nginx/conf.d/internetshop.conf
nginx -t

echo "[6/6] Restart nginx..."
systemctl reload nginx

echo "=== Frontend deployed successfully! ==="
echo "Static files: $NGINX_HTML"
echo "Nginx config: /etc/nginx/conf.d/internetshop.conf"
