#!/bin/bash
set -euo pipefail

echo "=== InternetShop PRO — Backend Deploy ==="

APP_DIR="/opt/internetshop"
COMPOSE_FILE="docker-compose.yml"
COMPOSE_PROD="docker-compose.prod.yml"

cd "$APP_DIR"

echo "[1/6] Pull latest code..."
git pull origin master

echo "[2/6] Copy production environment..."
if [ ! -f .env.docker ]; then
    echo "ERROR: .env.docker not found! Copy from .env.prod.example"
    exit 1
fi

echo "[3/6] Build backend image..."
docker compose -f "$COMPOSE_FILE" -f "$COMPOSE_PROD" build backend

echo "[4/6] Run database migrations..."
docker compose -f "$COMPOSE_FILE" -f "$COMPOSE_PROD" run --rm backend \
    alembic upgrade head

echo "[5/6] Restart services..."
docker compose -f "$COMPOSE_FILE" -f "$COMPOSE_PROD" up -d backend

echo "[6/6] Wait for health check..."
MAX_WAIT=60
ELAPSED=0
while [ $ELAPSED -lt $MAX_WAIT ]; do
    if docker compose -f "$COMPOSE_FILE" -f "$COMPOSE_PROD" ps backend | grep -q "healthy"; then
        echo "Backend is healthy!"
        break
    fi
    sleep 5
    ELAPSED=$((ELAPSED + 5))
    echo "  Waiting... (${ELAPSED}s/${MAX_WAIT}s)"
done

if [ $ELAPSED -ge $MAX_WAIT ]; then
    echo "WARNING: Backend did not become healthy within ${MAX_WAIT}s"
    docker compose -f "$COMPOSE_FILE" -f "$COMPOSE_PROD" logs backend --tail=50
    exit 1
fi

echo "=== Backend deployed successfully! ==="
docker compose -f "$COMPOSE_FILE" -f "$COMPOSE_PROD" ps
