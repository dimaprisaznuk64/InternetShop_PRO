#!/bin/bash
set -euo pipefail

echo "============================================="
echo "  InternetShop PRO — Full Health Check"
echo "============================================="

HEALTHY=true

check() {
    local name="$1"
    local result="$2"
    if [ "$result" = "ok" ]; then
        echo "  ✅ $name: OK"
    else
        echo "  ❌ $name: $result"
        HEALTHY=false
    fi
}

echo ""
echo "=== [1/7] Backend API ==="
API_URL="${API_URL:-http://localhost:8000}"
API_STATUS=$(curl -o /dev/null -s -w "%{http_code}" --max-time 5 "${API_URL}/health" 2>/dev/null || echo "000")
if [ "$API_STATUS" = "200" ]; then
    check "Backend API" "ok"
else
    check "Backend API" "HTTP $API_STATUS"
fi

echo ""
echo "=== [2/7] PostgreSQL ==="
COMPOSE_FILE="docker-compose.yml"
COMPOSE_PROD="docker-compose.prod.yml"
PG_PING=$(docker compose -f "$COMPOSE_FILE" -f "$COMPOSE_PROD" exec -T postgres \
    pg_isready -U postgres 2>/dev/null && echo "ok" || echo "unreachable")
check "PostgreSQL" "$PG_PING"

echo ""
echo "=== [3/7] Redis ==="
REDIS_PING=$(docker compose -f "$COMPOSE_FILE" -f "$COMPOSE_PROD" exec -T redis \
    redis-cli ping 2>/dev/null | tr -d '\r' || echo "unreachable")
if [ "$REDIS_PING" = "PONG" ]; then
    check "Redis" "ok"
else
    check "Redis" "$REDIS_PING"
fi

echo ""
echo "=== [4/7] Frontend ==="
FRONTEND_URL="${FRONTEND_URL:-http://localhost:80}"
FRONTEND_STATUS=$(curl -o /dev/null -s -w "%{http_code}" --max-time 5 "$FRONTEND_URL" 2>/dev/null || echo "000")
if [ "$FRONTEND_STATUS" = "200" ] || [ "$FRONTEND_STATUS" = "301" ] || [ "$FRONTEND_STATUS" = "302" ]; then
    check "Frontend" "ok"
else
    check "Frontend" "HTTP $FRONTEND_STATUS"
fi

echo ""
echo "=== [5/7] Nginx ==="
NGINX_STATUS=$(docker compose -f "$COMPOSE_FILE" -f "$COMPOSE_PROD" ps nginx --format json 2>/dev/null | python3 -c "
import sys, json
try:
    data = json.loads(sys.stdin.read())
    state = data.get('State', 'unknown')
    if state == 'running':
        print('ok')
    else:
        print(state)
except:
    print('unreachable')
" 2>/dev/null || echo "unreachable")
check "Nginx" "$NGINX_STATUS"

echo ""
echo "=== [6/7] Docker containers ==="
ALL_RUNNING=true
for svc in postgres redis backend frontend nginx; do
    STATUS=$(docker compose -f "$COMPOSE_FILE" -f "$COMPOSE_PROD" ps "$svc" --format json 2>/dev/null | python3 -c "
import sys, json
try:
    data = json.loads(sys.stdin.read())
    print(data.get('State', 'unknown'))
except:
    print('unreachable')
" 2>/dev/null || echo "unreachable")
    if [ "$STATUS" != "running" ]; then
        echo "  ⚠ $svc: $STATUS"
        ALL_RUNNING=false
    fi
done
if [ "$ALL_RUNNING" = true ]; then
    check "Docker containers" "ok"
else
    check "Docker containers" "some not running"
fi

echo ""
echo "=== [7/7] Disk space ==="
DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | tr -d '%')
echo "  Disk usage: ${DISK_USAGE}%"
if [ "$DISK_USAGE" -gt 90 ]; then
    check "Disk space" "CRITICAL ${DISK_USAGE}%"
elif [ "$DISK_USAGE" -gt 80 ]; then
    echo "  ⚠ WARNING: Disk usage above 80%"
    check "Disk space" "ok"
else
    check "Disk space" "ok"
fi

echo ""
echo "============================================="
if [ "$HEALTHY" = true ]; then
    echo "  ✅ All health checks passed!"
else
    echo "  ❌ Some checks failed"
    exit 1
fi
echo "============================================="
